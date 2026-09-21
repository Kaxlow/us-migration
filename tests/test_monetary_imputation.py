import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.preparation import SocioeconomicImputer


def sample():
    p=pd.DataFrame({'county_fips':['01001','01001','99001'],'year':[2017,2018,2024],'population':[1000.]*3})
    for c in SocioeconomicImputer.levels+SocioeconomicImputer.counts+SocioeconomicImputer.historical_counts:p[c]=100.
    for c in ['bachelors','masters','professional_degree','doctorate']:p[c]=10.
    for c in SocioeconomicImputer.monetary:p[c]=[100.,200.,np.nan]
    return p


def test_common_basis_fit_back_conversion_and_original_values():
    p=sample();indices={2017:100.,2018:200.,2024:400.}
    imputer=SocioeconomicImputer().fit(p,price_index=indices)
    assert imputer.base_year==2024
    for c in imputer.monetary:assert imputer.stats[c]['global']==400.
    result,_=imputer.transform(p)
    for c in imputer.monetary:
        assert result[c].tolist()==[100.,200.,400.]
        assert result[c+'_imputed'].tolist()==[False,False,True]
    target=p.iloc[[2]].assign(year=2018)
    assert imputer.transform(target)[0].median_home_value.iloc[0]==200.
    future=p.copy();future.loc[2,imputer.monetary]=1e8
    assert SocioeconomicImputer().fit(future,price_index=indices).stats==imputer.stats


def test_missing_price_year_is_not_silently_filled():
    with pytest.raises(ValueError,match='CPI coverage'):
        SocioeconomicImputer().fit(sample(),price_index={2017:100.,2018:200.})
