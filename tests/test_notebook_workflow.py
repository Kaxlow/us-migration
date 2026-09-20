"""The notebook is the implementation, not a printed copy of module functions."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from us_migration.notebook_api import definitions
from us_migration.cleaning import normalize_irs


def test_compatibility_exports_are_notebook_definitions():
    assert normalize_irs is definitions()['normalize_irs']
    assert '01_data_cleaning.ipynb' in normalize_irs.__code__.co_filename
    notebook=json.loads((ROOT/'notebooks/01_data_cleaning.ipynb').read_text(encoding='utf-8'))
    code='\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code')
    assert 'rebuild_source_tables' not in code
    assert 'from us_migration.cleaning import' not in code
    assert 'from us_migration.preparation import' not in code


@pytest.mark.parametrize('bad',[None,np.nan,np.inf,'','NA','null','<NA>','missing'])
def test_final_contract_catches_missing_markers_and_nonfinite_values(bad):
    frame=pd.DataFrame({'county_fips':['01001'],'year':[2020],'value':[bad]})
    with pytest.raises(AssertionError):definitions()['assert_complete'](frame,['county_fips','year'])


def test_final_contract_detects_duplicate_keys():
    frame=pd.DataFrame({'county_fips':['01001']*2,'year':[2020]*2,'value':[1,2]})
    with pytest.raises(AssertionError):definitions()['assert_complete'](frame,['county_fips','year'])


def test_geographic_reference_checks_year_not_just_code():
    reference=pd.DataFrame({'county_fips':['01001'],'county_name':['Example'],'year':[2020]})
    result=definitions()['repair_identifiers'](reference.assign(year=2021),reference)
    assert result.geography_caution.all()
