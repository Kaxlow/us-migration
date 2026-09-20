import sys
from pathlib import Path
import json
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.cleaning import normalize_irs, clean_noaa, clean_acs, clean_acs_flows, clean_fema, build_panel, canonical_irs_pairs
from us_migration.acquisition import safe_url


def test_irs_direction_suppression_and_negative_agi():
    raw=pd.DataFrame([['01','001','06','037','CA','Los Angeles','-1','20','-25'],
                      ['01','001','97','000','AL','US total','50','80','-1'],
                      ['01','001','01','001','AL','Nonmigrant','200','400','999']])
    a=normalize_irs(raw,2023,'inflow')
    assert a.loc[0,'origin_fips']=='06037'
    assert a.loc[0,'destination_fips']=='01001'
    assert pd.isna(a.loc[0,'returns'])
    assert a.loc[0,'agi_thousands']==-25
    assert pd.isna(a.loc[1,'agi_thousands'])
    assert list(a.row_type)==['county_pair','domestic_total','nonmigrant']
    b=normalize_irs(raw,2023,'outflow')
    assert b.loc[0,'origin_fips']=='01001'


def test_noaa_state_mapping_and_sentinel(tmp_path):
    path=tmp_path/'climate.txt'
    path.write_text('05001022024'+''.join(f'{x:7.2f}' for x in [32.0]*11+[-99.99])+'\n')
    data=clean_noaa(path,'tmpccy',2009,2026)
    assert set(data.county_fips)=={'08001'} # climate 05 is Colorado, not Arkansas
    assert data.value.notna().sum()==11


def test_noaa_dc_and_actual_temperature_sentinel(tmp_path):
    path=tmp_path/'climate.txt'
    path.write_text('18511022026'+''.join(f'{x:7.2f}' for x in [32.0]*8+[-99.90]*4)+'\n')
    data=clean_noaa(path,'tmpccy',2009,2026)
    assert set(data.county_fips)=={'11001'}
    assert data.value.notna().sum()==8


def test_2009_acs_preserves_foreign_codes(tmp_path):
    p=tmp_path/'flows.txt'
    p.write_text('001001ASI000 text fields 12 21\n')
    data=clean_acs_flows(p,2009)
    assert data.loc[0,'origin_code']=='ASI000'
    assert not data.loc[0,'domestic_pair']


def test_foreign_regions_with_shared_codes_keep_distinct_ids(tmp_path):
    p=tmp_path/'flows.json'
    p.write_text(json.dumps([['GEOID1','GEOID2','FULL2_NAME','MOVEDIN','MOVEDIN_M'],
                            ['01001','AM','Central America','10','20'],
                            ['01001','AM','South America','15','25'],
                            ['01001',' ','Asia','30','40']]))
    data=clean_acs_flows(p,2021,True)
    assert data.origin_id.nunique()==3
    assert pd.isna(data.loc[2,'origin_code'])


def test_acs_missing_codes_zero_denominator_and_moe(tmp_path):
    p=tmp_path/'acs.json'
    p.write_text(json.dumps([['state','county','NAME','B01003_001E','B01003_001M','B19013_001E','B17001_001E','B17001_002E'],
                            ['01','001','Autauga','100','0','-666666666','0','0']]))
    d=clean_acs(p,2020)
    assert d.loc[0,'population_moe']==0
    assert pd.isna(d.loc[0,'median_household_income'])
    assert pd.isna(d.loc[0,'poverty_pct'])
    assert d.loc[0,'period_start']==2016


def test_acs_flow_origin_and_missing_not_zero(tmp_path):
    p=tmp_path/'flows.json'
    p.write_text(json.dumps([['GEOID1','GEOID2','MOVEDIN','MOVEDIN_M'],['01001','06037','0','20'],['01001',None,None,None]]))
    d=clean_acs_flows(p,2020)
    assert d.loc[0,'origin_code']=='06037'
    assert d.loc[0,'movers']==0
    assert pd.isna(d.loc[1,'movers'])
    assert not d.loc[1,'domestic_pair']


def test_fema_statewide_and_unknown_date_retained(tmp_path):
    p=tmp_path/'fema.csv'
    pd.DataFrame({'fipsStateCode':['01','01'],'fipsCountyCode':['000','001'],
        'incidentBeginDate':['2020-01-01',None],'incidentEndDate':['2020-01-02',None],
        'declarationDate':['2020-01-02','2020-02-01'],'disasterNumber':['1','2']}).to_csv(p,index=False)
    d=clean_fema(p,2009,2026)
    assert len(d)==2
    assert not d.loc[0,'county_coded_us']
    assert pd.isna(d.loc[1,'year'])


def test_panel_does_not_fill_missing_migration():
    a=pd.DataFrame({'county_fips':['01001'],'year':[2020],'in_scope_us':[True],'population':[100]})
    i=normalize_irs(pd.DataFrame([['01','003','97','000','AL','total','1','2','3']]),2020,'inflow')
    p=build_panel(a,i,pd.DataFrame(),pd.DataFrame(),2025)
    assert pd.isna(p.loc[0,'inflow_individuals'])


def test_secret_url_redaction():
    assert 'secret' not in safe_url('https://api.census.gov/data?get=NAME&key=secret')
    assert 'NAME' in safe_url('https://api.census.gov/data?get=NAME&key=secret')


def test_duplicate_irs_pairs_do_not_double_count_or_hide_conflicts():
    row=['01','001','06','037','CA','Los Angeles','10','20','100']
    same=normalize_irs(pd.DataFrame([row,row]),2020,'inflow')
    assert len(canonical_irs_pairs(same))==1
    same.loc[1,'individuals']=21
    with pytest.raises(ValueError,match='Conflicting'):
        canonical_irs_pairs(same)
