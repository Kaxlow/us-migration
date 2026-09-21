"""Reconstruct unavailable ACS measures from matching five-year detailed tables."""
import hashlib
import json
import numpy as np
import pandas as pd
from .acquisition import ROOT

HISTORICAL_COUNTS = ['civilian_labor_force', 'unemployed', 'population_25_plus',
                     'bachelors', 'masters', 'professional_degree', 'doctorate']


def component_map(metadata, year):
    """Use disjoint published cells; include civilian employment at ages 65+."""
    result = {}
    if year <= 2011:
        result['population_25_plus'] = ['B15002_001']
        for name, label in [('bachelors', "Bachelor's degree"), ('masters', "Master's degree"),
                            ('professional_degree', 'Professional school degree'), ('doctorate', 'Doctorate degree')]:
            codes = sorted(k[:-1] for k,v in metadata.items() if k.startswith('B15002_') and k.endswith('E')
                           and v['label'].rstrip(':').endswith('!!'+label))
            if len(codes) != 2: raise ValueError('Unexpected education schema: '+name)
            result[name] = codes
    if year <= 2010:
        employed = sorted(k[:-1] for k,v in metadata.items() if k.startswith('B23001_') and k.endswith('E')
                          and v['label'].rstrip(':').endswith('!!Employed'))
        unemployed = sorted(k[:-1] for k,v in metadata.items() if k.startswith('B23001_') and k.endswith('E')
                            and v['label'].rstrip(':').endswith('!!Unemployed'))
        if len(employed) != 26 or len(unemployed) != 26:
            raise ValueError('Unexpected employment schema')
        result['civilian_labor_force'] = employed + unemployed
        result['unemployed'] = unemployed
    return result


def reconstruct(raw, mapping):
    result = pd.DataFrame(index=raw.index)
    for name,codes in mapping.items():
        for suffix,tail in [('E',''), ('M','_moe')]:
            values=raw[[c+suffix for c in codes]].apply(pd.to_numeric,errors='coerce')
            values=values.mask(values.lt(0))
            # Census approximation for the MOE of a sum of disjoint estimates.
            result[name+tail]=(values.pow(2).sum(axis=1,min_count=len(codes)).pow(.5)
                               if suffix=='M' else values.sum(axis=1,min_count=len(codes)))
    return result


def historical_values(year, geography):
    catalog=json.loads((ROOT/'data/raw/catalog.json').read_text())
    def read(logical):
        record=catalog[logical]; path=ROOT/record['path']
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=record['sha256']:raise ValueError('Historical snapshot checksum mismatch')
        return json.loads(body)
    meta=read(f'acs/{year}/variables')['variables']
    mapping=component_map(meta,year)
    keys=sorted(k for k in catalog if k.startswith(f'acs_historical/{year}/{geography}/'))
    if not keys:raise ValueError('Missing historical ACS support; run scripts/download_cleaning_support.py')
    merged=None
    for key in keys:
        data=read(key); frame=pd.DataFrame(data[1:],columns=data[0])
        frame['county_fips']=frame.state.str.zfill(2)+(frame['county'].str.zfill(3) if 'county' in frame else '000')
        frame=frame.set_index('county_fips').drop(columns=['NAME','state','county'],errors='ignore')
        if not frame.index.is_unique:raise ValueError('Duplicate historical ACS geography')
        merged=frame if merged is None else merged.join(frame,validate='one_to_one')
    return reconstruct(merged,mapping),mapping


def restore_historical(frame,year,geography):
    result=frame.copy()
    for name in HISTORICAL_COUNTS: result[name+'_reconstructed']=False
    if year>2011:return result
    values,mapping=historical_values(year,geography)
    for name in mapping:
        estimate=result.county_fips.map(values[name])
        use=result[name].isna() & estimate.notna()
        result.loc[use,name]=estimate[use]
        result.loc[use,name+'_moe']=result.loc[use,'county_fips'].map(values[name+'_moe'])
        result.loc[use,name+'_flag']='reconstructed_'+mapping[name][0].split('_')[0]
        result.loc[use,name+'_moe_flag']='derived_rss_moe'
        result.loc[use,name+'_reconstructed']=True
    return result
