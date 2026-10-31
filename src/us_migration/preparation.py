"""Geographic preparation and training-fitted imputation."""
import re, unicodedata
import numpy as np
import pandas as pd
from .acquisition import ACS_VARIABLES
from .conventions import TRAIN_END, VALIDATION_END, SMALL_MISSING_FRACTION, STATE_UNITS, NOAA_STATE_FIPS
from .cleaning import code


def finish_fema_dates(events, train_end=TRAIN_END):
    """One duration per disaster number; fit duration estimates on training incidents."""
    frame=events.copy()
    groups=frame.groupby('disasterNumber')
    incidents=groups.agg(start=('incidentBeginDate','min'),end=('incidentEndDate','max'),
                         incident_type=('incidentType','first'))
    missing=incidents.end.isna()
    fraction=float(missing.mean())
    # Reconcile repeated area rows using an observed end from the same declaration.
    frame['incident_end_imputed']=False
    frame['incidentEndDate']=frame.disasterNumber.map(incidents.end)
    duration=(incidents.end-incidents.start).dt.total_seconds()/86400
    train=incidents.start.dt.year.le(train_end)&incidents.end.dt.year.le(train_end)&duration.ge(0)
    fitted=duration.loc[train].groupby(incidents.loc[train,'incident_type']).median()
    global_duration=duration.loc[train].median()
    if not np.isfinite(global_duration): raise ValueError('No training incident durations')
    if fraction <= SMALL_MISSING_FRACTION:
        frame=frame.loc[~frame.disasterNumber.isin(incidents.index[missing])].copy()
        action='drop missing-end declarations'
    else:
        estimates=incidents.incident_type.map(fitted).fillna(global_duration).round().clip(lower=0)
        ids=incidents.index[missing & incidents.start.notna()]
        replacement=incidents.loc[ids,'start']+pd.to_timedelta(estimates.loc[ids],unit='D')
        fill=frame.disasterNumber.isin(ids)
        frame.loc[fill,'incidentEndDate']=frame.loc[fill,'disasterNumber'].map(replacement)
        frame.loc[fill,'incident_end_imputed']=True
        action='training incident-type median duration; training global median fallback'
    frame['duration_days']=(frame.incidentEndDate-frame.incidentBeginDate).dt.total_seconds()/86400+1
    frame['invalid_duration']=frame.duration_days.lt(1)
    invalid=frame.incidentBeginDate.isna()|frame.incidentEndDate.isna()|frame.invalid_duration
    rejected=frame.loc[invalid].copy()
    frame=frame.loc[~invalid].copy()
    report={'declarations':len(incidents),'missing_end_declarations':int(missing.sum()),
            'missing_end_pct':100*fraction,'missing_end_area_rows':int(events.incidentEndDate.isna().sum()),
            'small_missing_threshold_pct':100*SMALL_MISSING_FRACTION,'action':action,
            'training_end_year':train_end,'training_declarations':int(train.sum()),
            'global_duration_days':float(global_duration),'duration_days_by_type':fitted.to_dict(),
            'rejected_area_rows':len(rejected)}
    return frame,report,rejected


def area_key(name):
    text=unicodedata.normalize('NFKD',str(name)).encode('ascii','ignore').decode().lower()
    text=re.sub(r'\(also[^)]*\)','',text)
    text=re.sub(r'\b(indian|reservation|off|trust|lands?|tribe|of|the|community|anvsa|anv|tdsa|otsa|county|borough|census area)\b',' ',text)
    return ' '.join(sorted(re.findall(r'[a-z0-9]+',text)))


def map_fema_areas(events, geography, relationships):
    """Map only explicit statewide areas, known FIPS, or unambiguous reference names."""
    geo=geography[['county_fips','county_name','year']].drop_duplicates().copy()
    geo['state']=geo.county_fips.str[:2]
    geo['key']=geo.county_name.str.split(',').str[0].map(area_key)
    rel=relationships.dropna(subset=['GEOID_AIANNH_20']).copy()
    rel['key']=rel.NAMELSAD_AIANNH_20.map(area_key)
    rel=rel.loc[pd.to_numeric(rel.AREALAND_PART,errors='coerce').gt(0)]
    # Different official entities with the same stripped name are not guessed.
    mappings={}
    for key,g in rel.groupby('key'):
        if g.GEOID_AIANNH_20.str[:4].nunique()==1:
            mappings[key]=sorted(g.GEOID_COUNTY_20.dropna().unique())
    years=sorted(geo.year.unique())
    lookup={year:g for year,g in geo.groupby('year')}
    valid_codes={year:set(g.county_fips) for year,g in lookup.items()}
    state_codes={(year,state):g.county_fips.tolist() for year,ref in lookup.items() for state,g in ref.groupby('state')}
    name_codes={(year,state,key):g.county_fips.unique() for year,ref in lookup.items() for (state,key),g in ref.groupby(['state','key'])}
    rows=[]; unresolved=[]
    for _,record in events.iterrows():
        year=int(record.year)
        reference_year=max((y for y in years if y<=year),default=years[0])
        ref=lookup[reference_year]
        state=str(record.fipsStateCode).zfill(2)
        name=str(record.designatedArea)
        code=str(record.county_fips)
        method=''; targets=[]
        if state in STATE_UNITS:
            targets=[state+'000']; method='state_analysis_unit'
        elif name.strip().lower()=='statewide':
            targets=state_codes.get((reference_year,state),[]); method='statewide_expansion'
        elif code in valid_codes[reference_year]:
            targets=[code];method='published_county_fips'
        else:
            key=area_key(name)
            candidate=name_codes.get((reference_year,state,key),[])
            if len(candidate)==1:
                targets=list(candidate);method='exact_county_name_reference'
            elif key in mappings:
                candidate=mappings[key]
                # Retain all intersecting counties for a cross-state tribal designation.
                if any(c.startswith(state) for c in candidate):
                    valid=valid_codes[reference_year]
                    targets=[c for c in candidate if c in valid]
                    method='tribal_2020_land_overlap'
        if not targets:
            unresolved.append(record.to_dict());continue
        for target in sorted(set(targets)):
            item=record.to_dict();item['source_county_fips']=code
            item['county_fips']=target;item['mapping_method']=method
            item['geography_reference_year']=2020 if method.startswith('tribal') else reference_year
            rows.append(item)
    mapped=pd.DataFrame(rows)
    return mapped,pd.DataFrame(unresolved,columns=events.columns)


def deduplicate_fema_events(mapped):
    """One local exposure per official incident ID, regardless of declaration number."""
    frame=mapped.copy()
    incident=frame['incidentId'].astype('string').str.strip()
    valid=incident.notna() & ~incident.str.lower().isin(['','0','none','nan','null','<na>'])
    frame['event_id']=('incident:'+incident).where(valid,'declaration:'+frame.disasterNumber.astype(str))
    frame['event_key_method']=np.where(valid,'official_incident_id','declaration_fallback')
    # A declaration must not identify two distinct incidents.
    if frame.groupby('disasterNumber').event_id.nunique().gt(1).any():
        raise ValueError('Conflicting incident IDs for a declaration')
    events=frame.groupby(['county_fips','event_id'],as_index=False).agg(
        incidentBeginDate=('incidentBeginDate','min'),
        incidentEndDate=('incidentEndDate','max'),
        incidentType=('incidentType',lambda s:'; '.join(sorted(set(s.dropna().astype(str))))),
        declaration_numbers=('disasterNumber',lambda s:'; '.join(sorted(set(s.astype(str))))),
        declaration_count=('disasterNumber','nunique'),source_record_count=('id','nunique'),
        event_key_method=('event_key_method','first'))
    events['year']=events.incidentBeginDate.dt.year.astype('int64')
    return events


def annual_climate(monthly, as_of_year):
    grouped=monthly.groupby(['county_fips','year','variable']).value
    annual=grouped.agg(['count','mean','sum']).reset_index()
    annual['value']=np.where(annual.variable.eq('precipitation_inches'),annual['sum'],annual['mean'])
    annual.loc[annual['count'].ne(12),'value']=np.nan
    values=annual.pivot(index=['county_fips','year'],columns='variable',values='value')
    counts=annual.pivot(index=['county_fips','year'],columns='variable',values='count').add_suffix('_months')
    full=values.join(counts).reset_index()
    bad=full[counts.columns].ne(12).any(axis=1)
    audit=full.assign(incomplete=bad).groupby('year').agg(observations=('incomplete','size'),incomplete=('incomplete','sum'))
    audit['incomplete_pct']=100*audit.incomplete/audit.observations
    # A partial current year is not an annual observation, regardless of its share.
    drop=bad & full.year.ge(as_of_year)
    return full.loc[~drop].copy(),audit.reset_index(),full.loc[drop].copy()


def clean_state_climate(path, element, start, end):
    rows=[]
    name={'tmpcst':'temperature_f','pcpnst':'precipitation_inches','tmaxst':'tmax_f','tminst':'tmin_f'}[element]
    for line in path.read_text().splitlines():
        state=NOAA_STATE_FIPS.get(line[:3].lstrip('0').zfill(2))
        if state not in STATE_UNITS or line[3:4]!='0': continue
        year=int(line[6:10])
        if not start<=year<=end:continue
        for month in range(1,13):
            value=float(line[10+(month-1)*7:17+(month-1)*7])
            if value in [-9.99,-99.90,-99.99]:value=np.nan
            rows.append((state+'000',year,month,name,value))
    return pd.DataFrame(rows,columns=['county_fips','year','month','variable','value'])


def repair_identifiers(panel, reference):
    """Identifiers are recovered by unique same-year names, never statistical imputation."""
    result=panel.copy()
    ref=reference[['county_name','year','county_fips']].drop_duplicates()
    ref=ref.loc[~ref.duplicated(['county_name','year'],keep=False)]
    names=ref.set_index(['county_name','year']).county_fips
    known=set(reference.county_fips.dropna())
    missing=~result.county_fips.isin(known)
    result['identifier_repaired']=False
    for index in result.index[missing]:
        key=(result.at[index,'county_name'],result.at[index,'year'])
        if key in names:
            result.at[index,'county_fips']=names.loc[key]
            result.at[index,'identifier_repaired']=True
    valid_pairs=set(zip(reference.county_fips,reference.year))
    unresolved=pd.Series([(f,y) not in valid_pairs for f,y in zip(result.county_fips,result.year)],index=result.index)
    result['geography_caution']=result.get('geography_caution',pd.Series(False,index=result.index)) | unresolved
    return result


def recalculate(frame):
    frame = frame.copy()
    ratios = {'poverty_pct':('below_poverty','poverty_universe'),
              'unemployment_pct':('unemployed','civilian_labor_force'),
              'vacancy_pct':('vacant_units','housing_units'),
              'homeownership_pct':('owner_occupied_units','occupied_units')}
    for name,(num,den) in ratios.items():
        frame[name] = 100*frame[num]/frame[den].where(frame[den]>0)
    degree=['bachelors','masters','professional_degree','doctorate']
    frame['bachelors_plus_pct']=100*frame[degree].sum(axis=1,min_count=4)/frame.population_25_plus.where(frame.population_25_plus>0)
    if 'inflow_individuals' in frame:
        frame['net_individuals']=frame.inflow_individuals-frame.outflow_individuals
        for stem in ['inflow_individuals','outflow_individuals','net_individuals']:
            frame[stem+'_per_1000']=1000*frame[stem]/frame.population.where(frame.population>0)
    return frame


class SocioeconomicImputer:
    """Train-only state medians of levels and population-normalized base counts."""
    monetary=['median_household_income','median_home_value','median_gross_rent']
    levels=['median_age','median_household_income','median_home_value','median_gross_rent']
    historical_counts=['civilian_labor_force','unemployed','population_25_plus','bachelors','masters','professional_degree','doctorate']
    counts=[v for v in ACS_VARIABLES.values() if v not in ['population','median_age','median_household_income','median_home_value','median_gross_rent','civilian_labor_force','unemployed','population_25_plus','bachelors','masters','professional_degree','doctorate']]

    def fit(self, panel, train_end=TRAIN_END, price_index=None, base_year=None):
        from us_migration.inflation import annual_price_index, dollar_factors
        self.price_index=annual_price_index() if price_index is None else dict(price_index)
        self.base_year=int(panel.year.max()) if base_year is None else int(base_year)
        dollar_factors(panel.year,self.price_index,self.base_year)
        train=panel.loc[panel.year.le(train_end)&panel.population.gt(0)].copy()
        if train.empty:raise ValueError('No training observations for imputation')
        self.train_end=train_end;self.stats={}
        for col in self.levels+self.counts:
            values=pd.to_numeric(train[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
            values=values.where(values.gt(0) if col in self.levels else values.ge(0))
            if col in self.monetary:values=values*dollar_factors(train.year,self.price_index,self.base_year)
            if col in self.counts:values=values/train.population
            self.stats[col]={'state':values.groupby(train.county_fips.str[:2]).median().dropna().to_dict(),
                             'global':float(values.median())}
            if not np.isfinite(self.stats[col]['global']):raise ValueError('No training values for '+col)
        return self

    def transform(self, panel):
        from us_migration.inflation import dollar_factors
        result=panel.copy();audit=[]
        for col,stats in self.stats.items():
            values=pd.to_numeric(result[col],errors='coerce').replace([np.inf,-np.inf],np.nan)
            missing=values.isna() # Invalid observed values still fail the exclusion rules.
            estimate=result.county_fips.str[:2].map(stats['state']).fillna(stats['global'])
            if col in self.monetary:estimate=estimate/dollar_factors(result.year,self.price_index,self.base_year)
            if col in self.counts:estimate=(estimate*result.population).round()
            result[col]=values.where(~missing,estimate)
            result[col+'_imputed']=missing & result[col].notna()
            audit.append({'variable':col,'imputed_rows':int(result[col+'_imputed'].sum())})
        for col in self.historical_counts:
            result[col+'_imputed']=False
        # Constrain imputed counts to their observed/estimated universes, never change observed counts.
        for num,den in [('below_poverty','poverty_universe'),('unemployed','civilian_labor_force'),
                        ('vacant_units','housing_units'),('occupied_units','housing_units'),
                        ('owner_occupied_units','occupied_units')]:
            mask=result[num+'_imputed']&result[num].gt(result[den])
            result.loc[mask,num]=result.loc[mask,den]
        degree=['bachelors','masters','professional_degree','doctorate']
        total=result[degree].sum(axis=1,min_count=4)
        excess=total.gt(result.population_25_plus)
        for index in result.index[excess]:
            imputed=[c for c in degree if result.at[index,c+'_imputed']]
            observed=sum(result.at[index,c] for c in degree if c not in imputed)
            allowance=max(0,result.at[index,'population_25_plus']-observed)
            denom=sum(result.at[index,c] for c in imputed)
            for col in imputed:
                result.at[index,col]=np.floor(result.at[index,col]*allowance/denom) if denom else 0
        result=recalculate(result)
        result['socioeconomic_imputed']=result[[c+'_imputed' for c in self.stats]].any(axis=1)
        result['data_split']=np.select([result.year.le(self.train_end),result.year.le(VALIDATION_END)],['train','validation'],default='test')
        return result,pd.DataFrame(audit)
