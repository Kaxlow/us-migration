"""Source parsing and county panel construction."""
import io, json, re, zipfile
import numpy as np
import pandas as pd
from .acquisition import ACS_VARIABLES
from .conventions import US_STATES, NOAA_STATE_FIPS


def code(series, width):
    return series.astype('string').str.strip().str.replace(r'\.0$','',regex=True).str.zfill(width)


def numeric(series):
    return pd.to_numeric(series.astype('string').str.replace(',','',regex=False).str.strip(),errors='coerce').astype(float)


def api_frame(path):
    rows = json.loads(path.read_bytes())
    if not isinstance(rows,list) or len(rows)<2:
        raise ValueError('Expected Census header and data rows')
    return pd.DataFrame(rows[1:],columns=rows[0])


def acs_numeric(series):
    values = numeric(series)
    # All selected ACS measures are nonnegative; negative values are API special codes.
    return values.mask(values < 0)


def acs_identifiers(raw, year):
    frame = pd.DataFrame({'county_fips':code(raw['state'],2)+code(raw.get('county',pd.Series('000',index=raw.index)),3),
        'county_name':raw['NAME'],'year':year,'period_start':year-4,'period_end':year})
    frame['in_scope_us'] = frame.county_fips.str[:2].isin(US_STATES)
    return frame


def acs_estimates(raw, frame):
    for variable,name in ACS_VARIABLES.items():
        for suffix,label in [('E',name),('M',name+'_moe')]:
            values = raw.get(variable+suffix,pd.Series(pd.NA,index=raw.index))
            frame[label] = acs_numeric(values)
            frame[label+'_flag'] = np.where(values.isna(),'not_available',np.where(numeric(values)<0,'special_value',''))
    return frame


def acs_percentages(frame):
    for target,numerator,denominator in [
        ('poverty_pct','below_poverty','poverty_universe'),
        ('unemployment_pct','unemployed','civilian_labor_force'),
        ('vacancy_pct','vacant_units','housing_units'),
        ('homeownership_pct','owner_occupied_units','occupied_units')]:
        frame[target] = 100*frame[numerator]/frame[denominator].where(frame[denominator]>0)
    degree_cols = ['bachelors','masters','professional_degree','doctorate']
    frame['bachelors_plus_pct'] = 100*frame[degree_cols].sum(axis=1,min_count=4)/frame.population_25_plus.where(frame.population_25_plus>0)
    return frame


def clean_acs(path,year):
    raw=api_frame(path)
    frame=acs_identifiers(raw,year)
    frame=acs_estimates(raw,frame)
    from us_migration.historical_acs import restore_historical
    frame=restore_historical(frame,year,'counties' if 'county' in raw else 'states')
    return acs_percentages(frame)


def irs_layout(raw):
    if raw.shape[1] != 9:
        raise ValueError(f'Unexpected IRS width: {raw.shape[1]}')
    raw = raw.copy()
    raw.columns = ['ref_state','ref_county','other_state','other_county','other_state_name','other_name','returns','individuals','agi_thousands']
    # Legacy workbooks contain notes/headers; data rows have numeric geographic codes.
    valid = numeric(raw.ref_state).notna() & numeric(raw.ref_county).notna()
    raw = raw.loc[valid].copy()
    return raw


def irs_geography(raw):
    for col,width in [('ref_state',2),('ref_county',3),('other_state',2),('other_county',3)]:
        raw[col] = code(raw[col],width)
    raw['county_fips'] = raw.ref_state+raw.ref_county
    raw['other_fips'] = raw.other_state+raw.other_county
    return raw


def irs_measures(raw):
    for col in ['returns','individuals','agi_thousands']:
        values = numeric(raw[col])
        # AGI may legitimately be negative; only -1 is the documented numeric suppression marker.
        missing = values.eq(-1) if col=='agi_thousands' else values.lt(0)
        raw[col+'_suppressed_or_missing'] = missing | values.isna()
        raw[col] = values.mask(missing)
    return raw


def irs_classify(raw, year, view):
    domestic = raw.ref_state.isin(US_STATES) & raw.other_state.isin(US_STATES) & raw.ref_county.ne('000') & raw.other_county.ne('000')
    raw['row_type'] = np.select([
        raw.ref_county.eq('000'), domestic & raw.county_fips.eq(raw.other_fips),
        domestic, raw.other_state.eq('97') & raw.other_county.eq('000'),
        raw.other_state.eq('96') & raw.other_county.eq('000'),
    ],['state_summary','nonmigrant','county_pair','domestic_total','all_migration_total'],default='other_or_foreign')
    raw['origin_fips'] = raw.other_fips if view=='inflow' else raw.county_fips
    raw['destination_fips'] = raw.county_fips if view=='inflow' else raw.other_fips
    raw['view'] = view
    raw['year'] = year
    raw['period_start'] = year-1
    raw['methodology_series'] = 'pre_2012' if year<2012 else ('2012_2022' if year<2023 else '2023_onward')
    return raw


def normalize_irs(raw,year,view):
    raw=irs_layout(raw)
    raw=irs_geography(raw)
    raw=irs_measures(raw)
    return irs_classify(raw,year,view)


def read_irs(path,year,view=None):
    if view:
        try:
            raw=pd.read_csv(path,dtype=str,encoding='utf-8-sig')
        except UnicodeDecodeError:
            raw=pd.read_csv(path,dtype=str,encoding='cp1252')
        return normalize_irs(raw,year,view)
    frames=[]
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            match = re.search(r'co\d{4}([io])[^/]*\.xls[x]?$',member,re.I)
            if not match:
                continue
            workbook = pd.read_excel(io.BytesIO(archive.read(member)),header=None,sheet_name=None,dtype=str)
            for sheet,raw in workbook.items():
                if raw.empty:
                    continue
                # Data sheets have the nine-column published layout.
                if raw.shape[1]==9:
                    cleaned = normalize_irs(raw,year,'inflow' if match[1].lower()=='i' else 'outflow')
                    cleaned['archive_member'] = member+'::'+sheet
                    frames.append(cleaned)
    if not frames:
        raise ValueError('No recognized legacy IRS data sheets')
    return pd.concat(frames,ignore_index=True)


def canonical_irs_pairs(records):
    """Collapse repeated numeric records, but fail on conflicting published pair values."""
    keys=['year','view','origin_fips','destination_fips']
    pairs=records.loc[records.row_type.eq('county_pair')].copy()
    pairs=pairs.drop_duplicates(keys+['returns','individuals','agi_thousands'])
    if pairs.duplicated(keys).any():
        raise ValueError('Conflicting IRS pair records require investigation; no arbitrary selection made')
    return pairs


def normalize_state_irs(raw, year, view):
    """Code 97 is reused for US interstate and same-state totals; match the label."""
    raw=raw.copy()
    raw.columns=['ref_state','other_state','state_name','name','returns','individuals','agi_thousands']
    expanded=raw.assign(ref_county='000',other_county='000')[['ref_state','ref_county','other_state','other_county','state_name','name','returns','individuals','agi_thousands']]
    values=normalize_irs(expanded,year,view)
    interstate=values.other_name.str.strip().str.fullmatch(r'.*Total Migration\s*-\s*US',case=False,na=False)
    values=values.loc[values.county_fips.isin(['02000','09000'])&values.other_fips.eq('97000')&interstate].copy()
    values['row_type']='domestic_total'
    if values.duplicated(['county_fips','year','view']).any():
        raise ValueError('Duplicate published interstate totals')
    return values


def acs_flow_raw(path, year):
    if year==2009:
        # 2009 ctyxcty_us: 3-digit state/3-digit county pairs in first 12 chars;
        # final two whitespace-separated fields are movers and their 90% MOE.
        records=[]
        with path.open(encoding='latin-1') as source:
            for line in source:
                if not line.strip(): continue
                tail=line.split()[-2:]
                origin_state=line[6:9]
                origin=(origin_state[-2:] if origin_state.isdigit() and int(origin_state)<100 else origin_state)+line[9:12]
                records.append((line[:3].strip().zfill(3)[-2:]+line[3:6],origin,*tail))
        raw=pd.DataFrame(records,columns=['GEOID1','GEOID2','MOVEDIN','MOVEDIN_M'])
    else:
        raw=api_frame(path)
    return raw


def acs_flow_measures(raw, year):
    frame=pd.DataFrame({'destination_fips':raw.GEOID1.astype('string'),
        'origin_code':raw.GEOID2.astype('string').str.strip().replace('',pd.NA),'year':year,'period_start':year-4,'period_end':year,
        'movers':acs_numeric(raw.MOVEDIN),'movers_moe':acs_numeric(raw.MOVEDIN_M)})
    return frame


def acs_flow_origins(raw, frame, state_origin):
    width=2 if state_origin else 5
    frame['origin_geography']=np.where(frame.origin_code.str.fullmatch(r'\d{'+str(width)+'}').fillna(False),'state' if state_origin else 'county','world_region_or_other')
    frame['domestic_pair']=frame.destination_fips.str.fullmatch(r'\d{5}').fillna(False) & frame.origin_code.str.fullmatch(r'\d{'+str(width)+'}').fillna(False) & frame.origin_code.str[:2].isin(US_STATES) & frame.destination_fips.str[:2].isin(US_STATES)
    if not state_origin:
        frame['domestic_pair'] = frame.domestic_pair & frame.origin_code.str[2:].ne('000').fillna(False)
    for source,target in [('FULL1_NAME','destination_name'),('FULL2_NAME','origin_name')]:
        if source in raw: frame[target]=raw[source]
    frame['origin_id']=frame.origin_code
    if 'origin_name' in frame:
        other=frame.origin_geography.eq('world_region_or_other')
        frame.loc[other,'origin_id']='region:'+frame.loc[other,'origin_name'].astype('string').str.strip()
    return frame


def clean_acs_flows(path,year,state_origin=False):
    raw=acs_flow_raw(path,year)
    frame=acs_flow_measures(raw,year)
    return acs_flow_origins(raw,frame,state_origin)


def fema_dates(frame):
    frame=frame.copy()
    required={'fipsStateCode','fipsCountyCode','incidentBeginDate','declarationDate','disasterNumber'}
    if not required.issubset(frame):
        raise ValueError('FEMA schema missing required fields')
    frame['county_fips']=code(frame.fipsStateCode,2)+code(frame.fipsCountyCode,3)
    for col in ['incidentBeginDate','incidentEndDate','declarationDate']:
        frame[col]=pd.to_datetime(frame[col],errors='coerce',utc=True)
    return frame


def fema_scope(frame, start, end):
    frame['year']=frame.incidentBeginDate.dt.year.astype('Int64')
    frame['county_coded_us']=frame.county_fips.str[:2].isin(US_STATES) & frame.county_fips.str[2:].ne('000') & frame.county_fips.str.fullmatch(r'\d{5}').fillna(False)
    frame['duration_days']=(frame.incidentEndDate-frame.incidentBeginDate).dt.total_seconds()/86400+1
    frame['invalid_duration']=frame.duration_days.lt(0)
    # Preserve missing incident dates if the declaration falls in the requested period.
    selected=frame.year.between(start,end) | (frame.year.isna() & frame.declarationDate.dt.year.between(start,end))
    return frame.loc[selected].copy()


def clean_fema(path,start,end):
    frame=pd.read_csv(path,dtype=str)
    return fema_scope(fema_dates(frame),start,end)


def noaa_raw(path, start, end):
    # Filter the text before pandas parsing: full originals retain 1895 onward.
    with path.open() as source:
        lines=[line for line in source if line[7:11].isdigit() and start<=int(line[7:11])<=end]
    columns=['climate_state','county','element','year']+[str(i) for i in range(1,13)]
    raw=pd.read_fwf(io.StringIO(''.join(lines)),widths=[2,3,2,4]+[7]*12,names=columns,dtype=str)
    return raw


def noaa_geography(raw):
    raw=raw.copy()
    raw['climate_state']=code(raw.climate_state,2)
    raw['county_fips']=raw.climate_state.map(NOAA_STATE_FIPS)+code(raw.county,3)
    # NOAA's county crosswalk maps NCDC 18511 to DC's Census code 11001.
    raw.loc[raw.climate_state.eq('18') & code(raw.county,3).eq('511'),'county_fips']='11001'
    if raw.county_fips.isna().any(): raise ValueError('Unmapped NOAA state ID')
    raw['year']=pd.to_numeric(raw.year)
    return raw


def noaa_months(raw):
    result=raw.melt(id_vars=['county_fips','year'],value_vars=[str(i) for i in range(1,13)],var_name='month',value_name='value')
    result['month']=pd.to_numeric(result.month)
    result['value']=numeric(result.value)
    return result


def noaa_values(result, element):
    sentinels=[-9.99] if element=='pcpncy' else [-99.99,-99.90]
    result['missing_sentinel']=result.value.isin(sentinels)
    result['value']=result.value.mask(result.missing_sentinel)
    result['variable']={'pcpncy':'precipitation_inches','tmpccy':'temperature_f','tmaxcy':'tmax_f','tmincy':'tmin_f'}[element]
    return result


def clean_noaa(path,element,start,end):
    raw=noaa_raw(path,start,end)
    raw=noaa_geography(raw)
    result=noaa_months(raw)
    return noaa_values(result,element)


def build_panel(acs,irs,fema,climate,fema_complete_through):
    panel=acs.loc[acs.in_scope_us].copy()
    if not irs.empty:
        totals=irs.loc[irs.row_type.eq('domestic_total')]
        for view in ['inflow','outflow']:
            subset=totals.loc[totals.view.eq(view),['county_fips','year','individuals','returns']].rename(columns={'individuals':view+'_individuals','returns':view+'_returns'})
            panel=panel.merge(subset,on=['county_fips','year'],how='left',validate='one_to_one')
        panel['net_individuals']=panel.inflow_individuals-panel.outflow_individuals
        for col in ['inflow_individuals','outflow_individuals','net_individuals']:
            panel[col+'_per_1000']=1000*panel[col]/panel.population.where(panel.population>0)
    if not fema.empty:
        panel=panel.merge(fema,on=['county_fips','year'],how='left',validate='one_to_one')
        # Zero means no county-coded declaration starting in that year, not no disaster.
        fill=panel.year.le(fema_complete_through)
        panel.loc[fill,'declarations']=panel.loc[fill,'declarations'].fillna(0)
    if not climate.empty:
        panel=panel.merge(climate,on=['county_fips','year'],how='left',validate='one_to_one')
    panel['geography_level']=np.where(panel.county_fips.str.endswith('000'),'state','county')
    panel['geography_caution']=panel.county_fips.str[:2].isin(['02','09']) & panel.geography_level.ne('state')
    panel['irs_methodology_series']=np.select([panel.year<2012,panel.year<2023],['pre_2012','2012_2022'],default='2023_onward')
    return panel
