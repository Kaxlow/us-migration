"""Resumable official-source acquisition with immutable, content-addressed snapshots."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw'
ACS_VARIABLES = {
    'B01003_001': 'population', 'B01002_001': 'median_age',
    'B19013_001': 'median_household_income', 'B25077_001': 'median_home_value',
    'B25064_001': 'median_gross_rent', 'B17001_001': 'poverty_universe',
    'B17001_002': 'below_poverty', 'B23025_003': 'civilian_labor_force',
    'B23025_005': 'unemployed', 'B25002_001': 'housing_units',
    'B25002_003': 'vacant_units', 'B25003_001': 'occupied_units',
    'B25003_002': 'owner_occupied_units', 'B15003_001': 'population_25_plus',
    'B15003_022': 'bachelors', 'B15003_023': 'masters',
    'B15003_024': 'professional_degree', 'B15003_025': 'doctorate',
}
IRS_INDEX = 'https://www.irs.gov/statistics/soi-tax-stats-migration-data'
NOAA_INDEX = 'https://www.ncei.noaa.gov/pub/data/cirs/climdiv/'


def safe_url(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path,
        urlencode([(k, '<redacted>' if k.lower() in {'key','token','api_key'} else v)
                   for k,v in parse_qsl(p.query)]), ''))


class SnapshotClient:
    def __init__(self, refresh=False):
        load_dotenv(ROOT / '.env')
        self.refresh = refresh
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'us-migration-research/0.1 (public-data acquisition)'
        self.session.mount('https://', HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504],
            allowed_methods=['GET'], respect_retry_after_header=True)))
        self.catalog_path = RAW / 'catalog.json'
        self.catalog = json.loads(self.catalog_path.read_text()) if self.catalog_path.exists() else {}
        self.attempts = []
        self.lock = threading.Lock()

    def fetch(self, logical_id, url, *, params=None, kind='binary'):
        if not self.refresh and logical_id in self.catalog:
            record = self.catalog[logical_id]
            path = ROOT / record['path']
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']:
                self.attempts.append(dict(logical_id=logical_id, status='cached', path=record['path']))
                return path
        public_url = safe_url(requests.Request('GET',url,params=params).prepare().url)
        try:
            for attempt in range(3):
                try:
                    response = self.session.get(url, params=params, timeout=(20,180))
                    break
                except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
                    if attempt==2: raise
                    time.sleep(2**attempt)
            response.raise_for_status()
            body = response.content
            if kind == 'json':
                json.loads(body)
            if kind == 'csv' and (b'<html' in body[:500].lower() or b'<!doctype' in body[:500].lower()):
                raise ValueError('HTML returned for data')
            # Never persist a server response that echoes credentials.
            for name in ['CENSUS_API_KEY','NOAA_CDO_TOKEN']:
                value = os.getenv(name, '')
                if value and value.encode() in body:
                    raise ValueError('Response contains credential')
            digest = hashlib.sha256(body).hexdigest()
            suffix = {'json':'.json','html':'.html','csv':'.csv','zip':'.zip','text':'.txt','pdf':'.pdf'}.get(kind,'.bin')
            folder = RAW / logical_id
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / (digest + suffix)
            if not path.exists():
                path.write_bytes(body)
            record = dict(logical_id=logical_id, url=public_url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                sha256=digest, bytes=len(body), path=path.relative_to(ROOT).as_posix(),
                content_type=response.headers.get('Content-Type'), etag=response.headers.get('ETag'),
                last_modified=response.headers.get('Last-Modified'))
            sidecar = path.with_suffix(path.suffix + '.metadata.json')
            if not sidecar.exists():
                sidecar.write_text(json.dumps(record,indent=2),encoding='utf-8')
            with self.lock:
                self.catalog[logical_id] = record
                RAW.mkdir(parents=True,exist_ok=True)
                temp = self.catalog_path.with_suffix('.tmp')
                temp.write_text(json.dumps(self.catalog,indent=2),encoding='utf-8')
                temp.replace(self.catalog_path)
            self.attempts.append(dict(logical_id=logical_id,status='downloaded',path=record['path']))
            print(f'{logical_id}: {len(body):,} bytes',flush=True)
            return path
        except (requests.RequestException, ValueError) as exc:
            # Exception strings can contain request URLs with API keys.
            status = getattr(getattr(exc,'response',None),'status_code',None)
            source=logical_id.split('/')[0]
            seen=[int(k.split('/')[1]) for k in self.catalog if k.startswith(source+'/') and k.split('/')[1].isdigit()]
            unpublished=status==404 and logical_id.endswith('/variables') and bool(seen) and int(logical_id.split('/')[1])>max(seen)
            label='not_published_api' if unpublished else 'failed'
            self.attempts.append(dict(logical_id=logical_id,status=label,http_status=status,
                                     error_type=type(exc).__name__,url=public_url))
            print(f'{logical_id}: {label} ({type(exc).__name__}, HTTP {status})',flush=True)
            return None

    def links(self, logical_id, url):
        path = self.fetch(logical_id,url,kind='html')
        if path is None:
            return []
        return [(a.get_text(' ',strip=True),urljoin(url,a['href']))
                for a in BeautifulSoup(path.read_bytes(),'html.parser').find_all('a',href=True)]

    def finish(self, args):
        folder = RAW / 'runs'; folder.mkdir(exist_ok=True)
        run = dict(start=args.start,end=args.end,sources=args.sources,attempts=self.attempts,
                   created_at=datetime.now(timezone.utc).isoformat())
        path = folder / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
        path.write_text(json.dumps(run,indent=2),encoding='utf-8')
        (RAW/'latest_run.json').write_text(json.dumps(run,indent=2),encoding='utf-8')


def download_irs(client, start, end):
    links = client.links('irs/index',IRS_INDEX)
    for year in range(start,end+1):
        candidates = [(t,u) for t,u in links if re.search(rf'{year-1}\s+to\s+{year}\b',t)]
        if not candidates:
            client.attempts.append(dict(logical_id=f'irs/{year}',status='not_published_in_index'))
            continue
        # County legacy ZIP occurs before the state-to-state ZIP in the official index.
        url = candidates[0][1]
        if url.endswith('.zip'):
            client.fetch(f'irs/{year}/legacy',url,kind='zip')
        else:
            releases = client.links(f'irs/{year}/index',url)
            for direction in ['inflow','outflow']:
                matches = [u for t,u in releases if re.search(rf'county{direction}.*\.csv$',u,re.I)]
                if not matches:
                    client.attempts.append(dict(logical_id=f'irs/{year}/{direction}',status='link_missing'))
                else:
                    client.fetch(f'irs/{year}/{direction}',matches[0],kind='csv')
            for t,u in releases:
                if u.endswith('.pdf') and ('guide' in t.lower() or 'record layout' in t.lower()):
                    client.fetch(f'irs/{year}/documentation',u,kind='pdf'); break


def download_acs(client,start,end):
    key = os.getenv('CENSUS_API_KEY')
    if not key:
        client.attempts.append(dict(logical_id='acs',status='missing_CENSUS_API_KEY')); return
    for year in range(start,end+1):
        base = f'https://api.census.gov/data/{year}/acs/acs5'
        metadata = client.fetch(f'acs/{year}/variables',base+'/variables.json',kind='json')
        if metadata is None:
            continue
        variables = json.loads(metadata.read_bytes())['variables']
        requested = [code+suffix for code in ACS_VARIABLES for suffix in ['E','M']]
        # MOEs are attributes of estimate variables and may be absent from variables.json.
        available = [code+suffix for code in ACS_VARIABLES if code+'E' in variables for suffix in ['E','M']]
        missing = [v for v in requested if v not in available]
        if missing:
            client.attempts.append(dict(logical_id=f'acs/{year}/schema',status='missing_variables',variables=missing))
        logical=f'acs/{year}/counties'
        if logical in client.catalog:
            old=json.loads((ROOT/client.catalog[logical]['path']).read_bytes())
            if not set(available).issubset(old[0]):
                client.catalog.pop(logical) # Old immutable snapshot remains on disk.
        client.fetch(f'acs/{year}/counties',base,
            params={'get':','.join(['NAME']+available),'for':'county:*','key':key},kind='json')


def download_acs_flows(client,start,end):
    for year in range(start,min(end,2020)+1):
        if year == 2009:
            url = 'https://www2.census.gov/programs-surveys/demo/tables/geographic-mobility/2009/county-to-county-migration-2005-2009/ctyxcty_us.txt'
            client.fetch('acs_flows/2009/bulk',url,kind='text')
            continue
        key = os.getenv('CENSUS_API_KEY')
        if not key:
            client.attempts.append(dict(logical_id=f'acs_flows/{year}',status='missing_CENSUS_API_KEY')); continue
        base = f'https://api.census.gov/data/{year}/acs/flows'
        client.fetch(f'acs_flows/{year}/variables',base+'/variables.json',kind='json')
        states = '01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56 72'.split() if year<=2015 else [None]
        def fetch_state(state):
            params={'get':'GEOID1,GEOID2,STATE1,COUNTY1,STATE2,COUNTY2,FULL1_NAME,FULL2_NAME,MOVEDIN,MOVEDIN_M,MOVEDOUT,MOVEDOUT_M',
                    'for':'county:*','key':key}
            if state: params['in']='state:'+state
            client.fetch(f'acs_flows/{year}/counties'+('_'+state if state else ''),base,params=params,kind='json')
        # Independent states, with serialized catalog writes and conservative concurrency.
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(fetch_state,states))
    # Same API path, different origin geography from 2021 onward.
    for year in range(max(start,2021),end+1):
        key = os.getenv('CENSUS_API_KEY')
        if not key:
            client.attempts.append(dict(logical_id=f'acs_state_flows/{year}',status='missing_CENSUS_API_KEY')); continue
        base = f'https://api.census.gov/data/{year}/acs/flows'
        metadata = client.fetch(f'acs_state_flows/{year}/variables',base+'/variables.json',kind='json')
        if metadata:
            client.fetch(f'acs_state_flows/{year}/counties',base,params={
                'get':'GEOID1,GEOID2,FULL1_NAME,FULL2_NAME,MOVEDIN,MOVEDIN_M',
                'for':'county:*','key':key},kind='json')


def download_fema(client,start,end):
    # Bulk is small enough to preserve the whole source including older incident dates.
    client.fetch('fema/declarations','https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries.csv',kind='csv')
    client.fetch('fema/documentation','https://www.fema.gov/api/open/v1/OpenFemaDataSetFields',
        params={'$filter':"openFemaDataSet eq 'DisasterDeclarationsSummaries'",'$top':1000},kind='json')


def download_noaa(client,start,end):
    links = client.links('noaa/index',NOAA_INDEX)
    client.fetch('noaa/documentation',urljoin(NOAA_INDEX,'county-readme.txt'),kind='text')
    client.fetch('noaa/county_crosswalk',urljoin(NOAA_INDEX,'county-to-climdivs.txt'),kind='text')
    for element in ['pcpncy','tmpccy','tmaxcy','tmincy']:
        matches = [u for t,u in links if re.search(rf'/climdiv-{element}-v[\d.]+-\d{{8}}$',u)]
        if matches:
            client.fetch(f'noaa/{element}',sorted(matches)[-1],kind='text')
        else:
            client.attempts.append(dict(logical_id=f'noaa/{element}',status='link_missing'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=int,default=2009)
    parser.add_argument('--end',type=int,default=datetime.now().year)
    parser.add_argument('--sources',nargs='+',choices=['irs','acs','acs_flows','fema','noaa'],default=['irs','acs','acs_flows','fema','noaa'])
    parser.add_argument('--refresh',action='store_true',help='Recheck upstream; preserve previous snapshot versions')
    args = parser.parse_args()
    if args.start < 2009 or args.end < args.start:
        parser.error('Require 2009 <= start <= end')
    client = SnapshotClient(args.refresh)
    try:
        for source in args.sources:
            globals()['download_'+source](client,args.start,args.end)
    finally:
        client.finish(args)
    failures = [a for a in client.attempts if a['status'] not in ['cached','downloaded','not_published_in_index','no_published_workbook_found','not_published_api','missing_variables']]
    print(f'Completed with {len(failures)} unsuccessful requests; see data/raw/latest_run.json',flush=True)
    return int(bool(failures))
