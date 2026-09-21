"""Independent Vintage 2025 map export; does not run or modify the EDA pipeline."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import zipfile
import requests
import pandas as pd
import shapefile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/website'
OUT = ROOT / 'website/data'

def download(url, name):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    if not path.exists():
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        path.write_bytes(response.content)
        path.with_suffix(path.suffix + '.json').write_text(json.dumps({
            'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(response.content).hexdigest()
        }, indent=2))
    return path

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/'
    county_url = base + 'counties/totals/co-est2025-alldata.csv'
    cbsa_url = base + 'metro/totals/cbsa-est2025-alldata.csv'
    county = pd.read_csv(download(county_url, 'co-est2025-alldata.csv'), encoding='latin1', dtype={'STATE': str, 'COUNTY': str})
    county = county.loc[county.SUMLEV.eq(50)].copy()
    county['id'] = county.STATE.str.zfill(2) + county.COUNTY.str.zfill(3)
    cbsa = pd.read_csv(download(cbsa_url, 'cbsa-est2025-alldata.csv'), encoding='latin1', dtype=str)
    area_types = cbsa.loc[cbsa.LSAD.isin(['Metropolitan Statistical Area', 'Micropolitan Statistical Area'])].set_index('CBSA').LSAD
    members = cbsa.loc[cbsa.STCOU.notna()].copy()
    members['id'] = members.STCOU.str.zfill(5)
    assert not members.id.duplicated().any()
    members['area'] = members.CBSA.map(area_types)
    assert members.area.notna().all()
    classification = members.set_index('id')['area'].to_dict()
    county['area'] = county.id.map(classification).fillna('Outside metro/micro')
    county['change'] = (county.POPESTIMATE2025 / county.POPESTIMATE2024 - 1) * 100
    assert county.id.is_unique and county.POPESTIMATE2024.gt(0).all()
    groups = []
    for area, group in county.groupby('area'):
        p24, p25 = int(group.POPESTIMATE2024.sum()), int(group.POPESTIMATE2025.sum())
        groups.append({'name': area, 'population2024': p24, 'population2025': p25, 'change': (p25 / p24 - 1) * 100})
    records = [{'id': r.id, 'name': r.CTYNAME, 'state': r.STNAME, 'population2024': int(r.POPESTIMATE2024), 'population2025': int(r.POPESTIMATE2025), 'change': round(r.change, 5), 'area': r.area} for r in county.itertuples()]
    (OUT / 'population.json').write_text(json.dumps({'source': county_url, 'classificationSource': cbsa_url, 'groups': groups, 'counties': records}, separators=(',', ':')), encoding='utf-8')
    for level in ['county', 'state']:
        url = f'https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_{level}_20m.zip'
        archive = download(url, f'{level}-2025.zip')
        with zipfile.ZipFile(archive) as z:
            stem = next(n[:-4] for n in z.namelist() if n.endswith('.shp'))
            with z.open(stem+'.shp') as shp, z.open(stem+'.dbf') as dbf, z.open(stem+'.shx') as shx:
                reader = shapefile.Reader(shp=shp, dbf=dbf, shx=shx)
                features = []
                for record in reader.iterShapeRecords():
                    props = record.record.as_dict()
                    if int(props['STATEFP']) > 56:
                        continue
                    features.append({'type': 'Feature', 'id': props['GEOID'], 'properties': {'name': props['NAME']}, 'geometry': record.shape.__geo_interface__})
        (OUT / f'{level}.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}, separators=(',', ':')))
    mapped = {f['id'] for f in json.loads((OUT/'county.geojson').read_text())['features']}
    assert set(county.id) <= mapped, f'Missing geometry: {set(county.id)-mapped}'
    (OUT / 'population-provenance.json').write_text(json.dumps([json.loads(p.read_text()) for p in RAW.glob('*.json')], indent=2))
    print(f'Exported {len(records)} counties. Area growth:', groups)

if __name__ == '__main__':
    main()
