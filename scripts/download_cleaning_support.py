"""Acquire official state measures and a tribal/county relationship reference."""
import json
import os
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.acquisition import SnapshotClient, ACS_VARIABLES, NOAA_INDEX


def main():
    client = SnapshotClient()
    jobs = []
    for year in range(2009, 2025):
        meta = json.loads((ROOT/client.catalog[f'acs/{year}/variables']['path']).read_bytes())['variables']
        available = [v+s for v in ACS_VARIABLES if v+'E' in meta for s in ['E','M']]
        jobs.append((f'acs_states/{year}/states', f'https://api.census.gov/data/{year}/acs/acs5',
                     {'get':','.join(['NAME']+available), 'for':'state:*', 'key':os.getenv('CENSUS_API_KEY')}, 'json'))
    # Matching five-year tables preserve period and county coverage.
    from us_migration.historical_acs import component_map
    for year in range(2009, 2012):
        meta=json.loads((ROOT/client.catalog[f'acs/{year}/variables']['path']).read_bytes())['variables']
        codes=sorted({code+suffix for cells in component_map(meta,year).values() for code in cells for suffix in ['E','M']})
        for geography,selector in [('counties','county:*'),('states','state:*')]:
            for part,offset in enumerate(range(0,len(codes),45)):
                jobs.append((f'acs_historical/{year}/{geography}/{part:02d}',
                             f'https://api.census.gov/data/{year}/acs/acs5',
                             {'get':','.join(['NAME']+codes[offset:offset+45]),'for':selector,
                              'key':os.getenv('CENSUS_API_KEY')},'json'))
    for year in range(2019, 2024):
        page = ROOT/client.catalog[f'irs/{year}/index']['path']
        links = [a['href'] for a in BeautifulSoup(page.read_bytes(),'html.parser').find_all('a',href=True)]
        for view in ['inflow','outflow']:
            url = next(u for u in links if f'state{view}' in u and u.endswith('.csv'))
            if url.startswith('/'): url='https://www.irs.gov'+url
            jobs.append((f'irs_states/{year}/{view}',url,None,'csv'))
    links=[a['href'] for a in BeautifulSoup((ROOT/client.catalog['noaa/index']['path']).read_bytes(),'html.parser').find_all('a',href=True)]
    for element in ['tmpcst','pcpnst','tmaxst','tminst']:
        url=next(u for u in links if u.startswith('climdiv-'+element+'-'))
        jobs.append((f'noaa_states/{element}',NOAA_INDEX+url,None,'text'))
    jobs.append(('geography/2020/tribal_counties',
                 'https://www2.census.gov/geo/docs/maps-data/data/rel2020/aiannh/tab20_aiannh20_county20_natl.txt',None,'text'))
    latest_acs=max(int(k.split('/')[1]) for k in client.catalog if k.startswith('acs/') and k.endswith('/variables'))
    for start in range(2009,latest_acs+1,10):
        end=min(start+9,latest_acs)
        jobs.append((f'inflation/cpi_u/{start}_{end}',
                     'https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0',
                     {'startyear':start,'endyear':end,'annualaverage':'true'},'json'))
    def fetch(job):
        key,url,params,kind=job
        return client.fetch(key,url,params=params,kind=kind)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(fetch,jobs))
    if any(p is None for p in results): raise RuntimeError('Support downloads incomplete; rerun to resume')
    import pandas as pd
    rows=[]
    for start in range(2009,latest_acs+1,10):
        record=client.catalog[f'inflation/cpi_u/{start}_{min(start+9,latest_acs)}']
        response=json.loads((ROOT/record['path']).read_bytes())
        if response.get('status')!='REQUEST_SUCCEEDED':raise ValueError('BLS index retrieval failed')
        rows.extend({'year':int(r['year']),'cpi_u':float(r['value']),'series':'CUUR0000SA0',
                     'source_url':record['url'],'source_sha256':record['sha256']}
                    for r in response['Results']['series'][0]['data'] if r['period']=='M13')
    index=pd.DataFrame(rows).sort_values('year')
    if set(index.year)!=set(range(2009,latest_acs+1)) or index.year.duplicated().any():
        raise ValueError('Incomplete annual inflation index')
    index.to_csv(ROOT/'docs/cpi-u-annual.csv',index=False)


if __name__=='__main__': main()
