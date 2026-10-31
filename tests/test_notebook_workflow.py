"""The notebook is the implementation, not a printed copy of module functions."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from us_migration.validation import assert_complete
from us_migration.preparation import repair_identifiers
from us_migration.cleaning import normalize_irs


def test_modules_import_without_reading_notebooks(monkeypatch):
    import importlib
    import us_migration.cleaning as cleaning
    import us_migration.preparation as preparation
    import us_migration.validation as validation
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        if path.suffix == '.ipynb':
            raise AssertionError('Package imports must be independent of notebooks')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', guarded)
    for module in [cleaning, preparation, validation]:
        importlib.reload(module)
    assert normalize_irs.__code__.co_filename.endswith('cleaning.py')


@pytest.mark.parametrize('bad',[None,np.nan,np.inf,'','NA','null','<NA>','missing'])
def test_final_contract_catches_missing_markers_and_nonfinite_values(bad):
    frame=pd.DataFrame({'county_fips':['01001'],'year':[2020],'value':[bad]})
    with pytest.raises(AssertionError):assert_complete(frame,['county_fips','year'])


def test_final_contract_detects_duplicate_keys():
    frame=pd.DataFrame({'county_fips':['01001']*2,'year':[2020]*2,'value':[1,2]})
    with pytest.raises(AssertionError):assert_complete(frame,['county_fips','year'])


def test_geographic_reference_checks_year_not_just_code():
    reference=pd.DataFrame({'county_fips':['01001'],'county_name':['Example'],'year':[2020]})
    result=repair_identifiers(reference.assign(year=2021),reference)
    assert result.geography_caution.all()
