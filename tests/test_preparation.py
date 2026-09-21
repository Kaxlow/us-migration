import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.preparation import (SocioeconomicImputer,finish_fema_dates,annual_climate,
                                     repair_identifiers,map_fema_areas)


def test_irs_reused_97_code_selects_interstate_not_intrastate():
    from us_migration.cleaning import normalize_state_irs
    raw=pd.DataFrame([
        ['02','97','AK','AK Total Migration-US','100','200','500'],
        ['02','97','AK','AK Total Migration-Same State','40','80','100'],
        ['09','97','CT','CT Total Migration-US','300','600','1000'],
        ['09','97','CT','CT Total Migration-Same State','70','140','300']])
    result=normalize_state_irs(raw,2023,'outflow')
    assert result.county_fips.tolist()==['02000','09000']
    assert result.individuals.tolist()==[200,600]
    assert not result.duplicated(['county_fips','year']).any()


def predictors():
    rows=pd.DataFrame({'county_fips':['01001']*3,'year':[2018,2019,2021],'population':[1000]*3,
                       'inflow_individuals':[10,20,np.nan],'outflow_individuals':[5,8,3]})
    for col in SocioeconomicImputer.levels: rows[col]=[100.,np.nan,900.]
    for col in SocioeconomicImputer.counts: rows[col]=[100.,np.nan,100.]
    for col in SocioeconomicImputer.historical_counts: rows[col]=[100.,100.,100.]
    for col in ['bachelors','masters','professional_degree','doctorate']:rows[col]=[10.,10.,10.]
    return rows


def test_imputation_ignores_future_values_and_preserves_outcomes():
    frame=predictors();imputer=SocioeconomicImputer().fit(frame)
    changed=frame.copy();changed.loc[2,imputer.levels]=1e9
    other=SocioeconomicImputer().fit(changed)
    assert imputer.stats==other.stats
    result,_=imputer.transform(frame)
    assert np.isclose(result.loc[1,'median_household_income'],100*imputer.price_index[2019]/imputer.price_index[2018])
    assert result.loc[1,'bachelors_plus_pct']==40
    assert result.loc[1,'median_household_income_imputed']
    assert pd.isna(result.loc[2,'inflow_individuals'])
    assert result.data_split.tolist()==['train','validation','test']


def test_missing_identifier_uses_unique_reference_not_guess():
    ref=pd.DataFrame({'county_fips':['01001','01003','01005'],'county_name':['A','B','B'],'year':[2018]*3})
    source=pd.DataFrame({'county_fips':[None,None],'county_name':['A','B'],'year':[2018]*2})
    out=repair_identifiers(source,ref)
    assert out.county_fips.iloc[0]=='01001'
    assert pd.isna(out.county_fips.iloc[1])


def test_fema_duration_fit_uses_training_and_distinct_declarations():
    start=pd.to_datetime(['2018-01-01','2021-01-01','2022-01-01'],utc=True)
    frame=pd.DataFrame({'disasterNumber':['a','b','c'],'incidentType':['Flood']*3,
                        'incidentBeginDate':start,'incidentEndDate':[start[0]+pd.Timedelta(days=2),start[1]+pd.Timedelta(days=200),pd.NaT]})
    result,report,_=finish_fema_dates(pd.concat([frame,frame.iloc[[2]]],ignore_index=True))
    assert report['missing_end_declarations']==1 and report['declarations']==3
    assert result.loc[result.disasterNumber.eq('c'),'duration_days'].eq(3).all()
    assert result.loc[result.disasterNumber.eq('c'),'incident_end_imputed'].all()


def test_small_fema_missing_fraction_drops_declaration():
    start=pd.Timestamp('2018-01-01',tz='UTC')
    frame=pd.DataFrame({'disasterNumber':[str(i) for i in range(25)],'incidentType':'Flood',
                        'incidentBeginDate':start,'incidentEndDate':start+pd.Timedelta(days=2)})
    frame.loc[24,'incidentEndDate']=pd.NaT
    result,report,_=finish_fema_dates(frame)
    assert len(result)==24 and report['missing_end_pct']==4


def test_partial_current_climate_removed_but_past_gap_audited():
    monthly=pd.DataFrame([(f,year,month,'temperature_f',np.nan if month==12 else 60)
                          for f in ['01001'] for year in [2025,2026] for month in range(1,13)],
                         columns=['county_fips','year','month','variable','value'])
    clean,audit,dropped=annual_climate(monthly,2026)
    assert clean.year.tolist()==[2025] and dropped.year.tolist()==[2026]
    assert audit.incomplete.eq(1).all() and clean.temperature_f.isna().all()


def test_statewide_and_tribal_mapping_preserves_extent():
    events=pd.DataFrame({'id':['a','b'],'year':[2020]*2,'fipsStateCode':['01']*2,
                         'county_fips':['01000']*2,'designatedArea':['Statewide','Example Indian Reservation']})
    geo=pd.DataFrame({'county_fips':['01001','01003'],'county_name':['A, Alabama','B, Alabama'],'year':[2020]*2})
    rel=pd.DataFrame({'GEOID_AIANNH_20':['1234'],'NAMELSAD_AIANNH_20':['Example Reservation'],
                      'GEOID_COUNTY_20':['01003'],'AREALAND_PART':['100']})
    mapped,unresolved=map_fema_areas(events,geo,rel)
    assert len(mapped)==3 and unresolved.empty
    assert set(mapped.loc[mapped.id.eq('a'),'county_fips'])=={'01001','01003'}
    assert mapped.loc[mapped.id.eq('b'),'county_fips'].tolist()==['01003']
