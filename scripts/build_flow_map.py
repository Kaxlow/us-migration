"""Package the cleaned IRS county-pair table for the landing-page explorer."""
from pathlib import Path
import hashlib
import json
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.exports import publish_files


def build(root=ROOT):
    root = Path(root)
    source = root/'data/processed/irs_county_flows.parquet'
    flows = pd.read_parquet(source)
    keys = ['year', 'origin_fips', 'destination_fips']
    if flows.duplicated(keys).any():
        raise ValueError('County-pair records must be unique within a year')
    if not flows['view'].eq('inflow').all():
        raise ValueError('Use the canonical inflow publication view exactly once')
    geography = pd.read_parquet(root/'data/processed/county_geography_vintages.parquet')
    names = geography.sort_values('year').drop_duplicates('county_fips', keep='last').set_index('county_fips').county_name.to_dict()
    ids = sorted(set(flows.origin_fips) | set(flows.destination_fips))
    files = {}
    years = []
    for year, group in flows.groupby('year', sort=True):
        rows = [[r.origin_fips, r.destination_fips,
                 None if pd.isna(r.individuals) else int(r.individuals)]
                for r in group.sort_values(keys).itertuples()]
        value = {'year': int(year), 'period_start': int(group.period_start.min()),
                 'columns': ['origin_fips', 'destination_fips', 'individuals'], 'flows': rows}
        files[f'{year}.json'] = (json.dumps(value, separators=(',', ':'))+'\n').encode()
        years.append(int(year))
    metadata = {
        'source': 'IRS Statistics of Income, county-to-county migration',
        'source_url': 'https://www.irs.gov/statistics/soi-tax-stats-migration-data',
        'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'years': years, 'counties': [{'id': i, 'name': names.get(i, 'County '+i)} for i in ids],
        'units': 'Individuals covered by matched IRS tax returns',
        'year_meaning': 'Ending filing year; each flow covers the preceding filing-year interval.',
        'net_rule': 'Inflow minus outflow for pairs with both directions reported. Missing or suppressed reverse flows remain unknown.',
        'boundary_note': '2025 display boundaries; unmatched historical counties remain in the table. Alaska and Hawaii appear as insets.',
        'coverage_note': 'Published domestic county pairs only. Suppression and unmatched returns limit coverage; sums of these pairs can differ from published county totals. IRS methodology changes affect comparisons across time.'
    }
    files['metadata.json'] = (json.dumps(metadata, indent=2)+'\n').encode()
    publish_files(root/'website/data/flows', files)
    return metadata


if __name__ == '__main__':
    metadata = build()
    print(f"Packaged {len(metadata['years'])} years and {len(metadata['counties'])} county identifiers")
