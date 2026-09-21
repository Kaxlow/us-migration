import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.historical_acs import reconstruct, component_map
from us_migration.preparation import deduplicate_fema_events, SocioeconomicImputer


def test_reconstruction_requires_all_components_and_combines_moes():
    raw=pd.DataFrame({'aE':[10,10], 'bE':[20,-666666666], 'aM':[3,3], 'bM':[4,4]})
    result=reconstruct(raw,{'bachelors':['a','b']})
    assert result.bachelors.iloc[0]==30
    assert result.bachelors_moe.iloc[0]==5
    assert pd.isna(result.bachelors.iloc[1])


def test_education_employment_never_use_median_imputer():
    assert not set(SocioeconomicImputer.historical_counts).intersection(SocioeconomicImputer.counts)


def test_incidents_merge_declarations_but_not_different_incidents_or_counties():
    frame=pd.DataFrame({'county_fips':['01001']*4+['01003'],
        'incidentId':['a','a','b',None,'a'],'disasterNumber':['1','2','3','4','2'],
        'incidentBeginDate':pd.to_datetime(['2019-12-31','2020-01-01','2020-01-01','2020-01-01','2020-01-01'],utc=True),
        'incidentEndDate':pd.to_datetime(['2020-01-02']*5,utc=True),
        'incidentType':['Flood']*5,'id':['r1','r2','r3','r4','r5']})
    result=deduplicate_fema_events(frame)
    assert len(result)==4
    joined=result.loc[result.county_fips.eq('01001') & result.event_id.eq('incident:a')].iloc[0]
    assert joined.declaration_count==2 and joined.year==2019
    assert result.event_id.eq('declaration:4').sum()==1


def test_unresolved_historical_counts_stay_missing_after_imputation():
    frame=pd.DataFrame({'county_fips':['01001','01001'],'year':[2018,2019],
                        'population':[1000.,1000.]})
    for col in SocioeconomicImputer.levels+SocioeconomicImputer.counts+SocioeconomicImputer.historical_counts:
        frame[col]=100.
    for col in ['bachelors','masters','professional_degree','doctorate']:frame[col]=10.
    frame.loc[1,['unemployed','bachelors']]=np.nan
    result,_=SocioeconomicImputer().fit(frame).transform(frame)
    assert pd.isna(result.loc[1,'unemployed']) and pd.isna(result.loc[1,'bachelors'])
    assert pd.isna(result.loc[1,'unemployment_pct']) and pd.isna(result.loc[1,'bachelors_plus_pct'])
    assert not result.loc[1,'unemployed_imputed'] and not result.loc[1,'bachelors_imputed']
