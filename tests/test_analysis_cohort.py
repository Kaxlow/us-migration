import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.notebook_helpers import build_analysis_cohort, assert_clean_cohort


def frame(n=4):
    records=[]
    for i in range(n):
        records.append(dict(county_fips=f'01{2*i+1:03d}',county_name=f'County {i}',year=2020,
            population=10000,median_age=40,median_household_income=50000,median_home_value=150000,
            median_gross_rent=800,poverty_pct=10,unemployment_pct=5,vacancy_pct=10,
            homeownership_pct=65,bachelors_plus_pct=25,declarations=0,precipitation_inches=40,
            temperature_f=60,inflow_individuals=100,outflow_individuals=80,net_individuals=20,
            inflow_individuals_per_1000=10,outflow_individuals_per_1000=8,net_individuals_per_1000=2,
            geography_caution=False))
    return pd.DataFrame(records)


@pytest.mark.parametrize('bad',[np.nan,np.inf,''])
def test_missing_or_nonfinite_values_are_excluded_not_imputed(bad):
    source=frame().astype({'median_household_income':object})
    source.loc[0,'median_household_income']=bad
    clean,excluded,_,_=build_analysis_cohort(source)
    assert len(clean)==3 and len(excluded)==1
    assert_clean_cohort(clean)
    assert clean.median_household_income.eq(50000).all()


def test_invalid_ranges_duplicates_and_arithmetic_are_audited():
    source=frame(7).astype({'year':float})
    source.loc[0,'poverty_pct']=110
    source.loc[1,'net_individuals']=200
    source.loc[2,'year']=2020.5
    source.loc[3,'county_fips']='99001'
    source.loc[4,'population']=0
    source=pd.concat([source,source.iloc[[5]]],ignore_index=True)
    clean,excluded,_,reasons=build_analysis_cohort(source)
    assert len(clean)==1
    assert reasons.percentage_outside_0_100.iloc[0]
    assert reasons.inconsistent_net_migration.iloc[1]
    assert reasons.invalid_year.iloc[2]
    assert reasons.outside_us_county_scope.iloc[3]
    assert reasons.duplicate_county_year.sum()==2
    assert excluded.reason.str.len().gt(0).all()


def test_valid_statistical_outlier_is_retained_and_flagged():
    source=frame(20)
    source['inflow_individuals']=80; source['net_individuals']=0
    source['inflow_individuals_per_1000']=8; source['net_individuals_per_1000']=0
    source.loc[0,['inflow_individuals','net_individuals','inflow_individuals_per_1000','net_individuals_per_1000']]=[1080,1000,108,100]
    clean,excluded,_,_=build_analysis_cohort(source)
    assert len(clean)==20 and excluded.empty
    assert clean.loc[0,'net_rate_iqr_flag']
    assert clean.loc[0,'net_individuals_per_1000']==100


def test_large_rate_held_for_review_and_discretization_is_complete():
    source=frame()
    source.loc[0,['inflow_individuals','net_individuals','inflow_individuals_per_1000','net_individuals_per_1000']]=[20000,19920,2000,1992]
    source.loc[1,'bachelors_plus_pct']=100
    clean,excluded,_,reasons=build_analysis_cohort(source)
    assert reasons.rate_denominator_review.iloc[0]
    assert len(excluded)==1
    assert clean.education_band.iloc[0]=='40% or more'
    assert clean.log10_population.eq(4).all()
