"""Small, reusable diagnostics used by the executable notebooks."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from .acquisition import ROOT

FEATURES = ['population','median_age','median_household_income','median_home_value','median_gross_rent',
    'poverty_pct','unemployment_pct','vacancy_pct','homeownership_pct','bachelors_plus_pct',
    'declarations','precipitation_inches','temperature_f']
OUTCOMES = ['inflow_individuals_per_1000','outflow_individuals_per_1000','net_individuals_per_1000']
TABLES = ROOT/'reports/tables'


def profile(frame,columns=None):
    rows=[]
    for name in columns or frame.columns:
        s=frame[name]
        record=dict(variable=name,dtype=str(s.dtype),rows=len(s),missing=int(s.isna().sum()),
                    missing_pct=100*s.isna().mean(),unique=int(s.nunique(dropna=True)))
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            v=s.dropna().astype(float)
            finite=v[np.isfinite(v)]
            q=finite.quantile([.01,.25,.5,.75,.99])
            iqr=q.loc[.75]-q.loc[.25]
            record.update(zeros=int(v.eq(0).sum()),negative=int(v.lt(0).sum()),infinite=int((~np.isfinite(v)).sum()),
                minimum=finite.min(),p01=q.loc[.01],median=q.loc[.5],p99=q.loc[.99],maximum=finite.max(),
                skew=finite.skew(),iqr_outliers=int(((finite<q.loc[.25]-1.5*iqr)|(finite>q.loc[.75]+1.5*iqr)).sum()))
        rows.append(record)
    return pd.DataFrame(rows)


def coverage():
    rows=[]
    specs={'county_features':('acs','county_fips'), 'irs_county_flows':('irs','destination_fips'),
           'acs_county_flows':('acs_flows','destination_fips'),
           'acs_state_county_flows':('acs_state_flows','destination_fips'),
           'fema_declarations':('fema','county_fips'), 'climate_monthly':('noaa','county_fips')}
    for name,(source,geo) in specs.items():
        path=ROOT/'data/processed'/f'{name}.parquet'
        if not path.exists(): continue
        d=pd.read_parquet(path,columns=['year',geo])
        for year,g in d.groupby('year'):
            rows.append(dict(source=source,year=int(year),rows=len(g),geographies=g[geo].nunique()))
    frame=pd.DataFrame(rows)
    TABLES.mkdir(parents=True,exist_ok=True)
    frame.to_csv(TABLES/'observed_coverage.csv',index=False)
    return frame


def table_profiles():
    TABLES.mkdir(parents=True,exist_ok=True)
    all_profiles=[]
    for path in sorted((ROOT/'data/processed').glob('*.parquet')):
        # One table at a time keeps memory bounded. Profile selected numeric and categorical columns.
        schema=pq.read_schema(path)
        cols=[n for n in schema.names if n not in ['source_snapshot','archive_member','county_name','other_name','destination_name','origin_name']]
        frame=pd.read_parquet(path,columns=cols)
        result=profile(frame); result.insert(0,'table',path.stem)
        all_profiles.append(result)
    result=pd.concat(all_profiles,ignore_index=True)
    result.to_csv(TABLES/'variable_profiles.csv',index=False)
    return result


def correlation_bundle(data,columns,label):
    columns=[c for c in columns if c in data and data[c].notna().sum()>=3]
    values=data[columns].astype(float).replace([np.inf,-np.inf],np.nan)
    support=values.notna().astype('int64').T.dot(values.notna().astype('int64'))
    pearson=values.corr(method='pearson',min_periods=30)
    spearman=values.corr(method='spearman',min_periods=30)
    TABLES.mkdir(parents=True,exist_ok=True)
    for suffix,result in [('pearson',pearson),('spearman',spearman),('pair_counts',support)]:
        result.to_csv(TABLES/f'{label}_{suffix}.csv')
    return pearson,spearman,support


def source_audit():
    catalog=json.loads((ROOT/'data/raw/catalog.json').read_text())
    records=pd.DataFrame(catalog.values())
    records['source']=records.logical_id.str.split('/').str[0]
    return records.groupby('source').agg(snapshots=('sha256','size'),bytes=('bytes','sum'),
        first_retrieved=('retrieved_at','min'),last_retrieved=('retrieved_at','max'))
