"""Write a compact reproducibility/coverage report after cleaning and notebook execution."""
import json
from pathlib import Path
import sys
import hashlib
from datetime import datetime,timezone
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration.acquisition import ROOT
from us_migration.eda import coverage


def main():
    catalog=json.loads((ROOT/'data/raw/catalog.json').read_text())
    broken=[]
    for logical,record in catalog.items():
        path=ROOT/record['path']
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            broken.append(logical)
    if broken: raise ValueError('Snapshot integrity failed: '+', '.join(broken))
    observed=coverage()
    latest={}
    for path in sorted((ROOT/'data/raw/runs').glob('*.json')):
        for attempt in json.loads(path.read_text())['attempts']:
            latest[attempt['logical_id']]=attempt
    # A successful catalog snapshot supersedes an earlier failed request for that same ID.
    unresolved=[v for k,v in latest.items() if k not in catalog and v['status'] not in ['not_published_in_index','missing_variables']
                and not (k.startswith('acs_flows/') and k.endswith('/counties') and any(x.startswith(k+'_') for x in catalog))]
    rows=[]
    for source in ['irs','acs','acs_flows','acs_state_flows','fema','noaa']:
        for year in range(2009,datetime.now().year+1):
            hit=observed.loc[observed.source.eq(source)&observed.year.eq(year)]
            status='downloaded_and_cleaned' if len(hit) else 'not_observed'
            if source=='acs_flows' and year>2020: status='product_replaced_by_state_to_county'
            if source=='acs_state_flows' and year<2021: status='product_not_yet_introduced'
            if source=='irs' and year>2023: status='not_in_verified_release_index'
            if source=='acs' and year>2024: status='api_vintage_not_published'
            if source=='acs_state_flows' and year>2022: status='api_vintage_not_published'
            rows.append(dict(source=source,year=year,status=status,rows=int(hit.rows.iloc[0]) if len(hit) else 0,
                geographies=int(hit.geographies.iloc[0]) if len(hit) else 0))
    pd.DataFrame(rows).to_csv(ROOT/'docs/coverage-observed.csv',index=False)
    panel=pd.read_parquet(ROOT/'data/processed/county_year_panel.parquet')
    inventory=pd.read_csv(ROOT/'data/processed/table_inventory.csv')
    totals=pd.read_parquet(ROOT/'data/processed/irs_county_totals.parquet')
    climate=pd.read_parquet(ROOT/'data/processed/climate_county_year.parquet')
    features=pd.read_parquet(ROOT/'data/processed/county_features.parquet')
    # Audit membership, not just counts: every state request must be represented in acquisition.
    state_keys='01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56 72'.split()
    missing_shards=[f'acs_flows/{year}/counties_{state}' for year in range(2010,2016) for state in state_keys
                    if f'acs_flows/{year}/counties_{state}' not in catalog]
    report=[ '# Download and exploratory analysis report', '',
        'Generated '+datetime.now(timezone.utc).isoformat()+'.', '',
        f"Verified SHA-256 checksums for {len(catalog):,} active snapshots ({sum(r['bytes'] for r in catalog.values())/1e9:.2f} GB). Previous immutable versions and exploratory verification files may use additional disk space.", '',
        f'County panel: {len(panel):,} rows, {panel.county_fips.nunique():,} distinct native county codes, {panel.year.min()}–{panel.year.max()}. Counts include code changes across years, not a fixed geography.', '',
        f'Missing historical ACS flow state shards: {len(missing_shards)}.', '',
        '| Table | Rows | Years | Duplicate keys |', '|---|---:|---|---:|']
    for r in inventory.itertuples():
        report.append(f'| {r.table} | {r.rows:,} | {r.min_year}–{r.max_year} | {r.duplicate_keys} |')
    report+=['', '## Data quality findings', '',
        '- IRS 2009–2011 uses legacy XLS archives; later CSVs require UTF-8 or Windows-1252 decoding. The cleaner preserves both publication views and exports inflow-view domestic county pairs separately.',
        '- ACS 2009–2010 lack the selected B23025 and B15003 tables; 2011 lacks the selected B15003 table. These are availability gaps, not observed zeros. Published MOEs are retained wherever estimates are available.',
        '- ACS county-to-county data end in 2020. State-to-county API vintages observed here end in 2022; later attempted metadata endpoints returned 404.',
        '- NOAA county state codes were mapped explicitly to Census FIPS. No annual climate value is generated without all 12 monthly observations.',
        '- Retrieved NOAA files include all 50 states and DC. The special DC climate code is crosswalked to 11001, and both documented -99.99 and observed -99.90 temperature missing markers are recognized.',
        '- IRS 2013–2014 contains 2,020 exact duplicate source rows across both views. The original records and a duplicate audit table are preserved; the canonical inflow table removes 1,007 repeated county-pair records after checking for numeric conflicts.',
        '- Alaska and Connecticut use official state-level features and interstate outcomes in the analysis file; county-only charts report them separately.',
        '- The panel is a native-geography descriptive join, not a geographically harmonized or release-date-safe modeling dataset.', '',
        '## Correlation findings', '']
    cleaning_manifest=ROOT/'data/processed/analysis_cleaning_manifest.json'
    if cleaning_manifest.exists():
        cleaned=json.loads(cleaning_manifest.read_text())
        report.extend([
            f"The validated predictor-imputed cohort contains {cleaned['analysis_rows']:,} geography-years; {cleaned['excluded_rows']:,} input rows are excluded with recorded reasons.",
            f"It has {cleaned['missing_values']} missing values, {cleaned['infinite_values']} infinities, and {cleaned['duplicate_keys']} duplicate county-year keys under the documented rules.",
            'Raw-versus-cleaned comparison images are in `reports/figures/cleaning/`; the ten captioned findings charts are in `reports/figures/eda/` and `reports/eda_visualizations.md`.',
            'Ordinary IQR outliers are retained and flagged; denominator-review cases above 1,000 per 1,000 residents are held out without claiming the original counts are erroneous.', ''])
    path=ROOT/'reports/tables/validated_latest_year_spearman.csv'
    if path.exists():
        spearman=pd.read_csv(path,index_col=0)
        pearson=pd.read_csv(ROOT/'reports/tables/validated_latest_year_pearson.csv',index_col=0)
        counts=pd.read_csv(ROOT/'reports/tables/validated_latest_year_pair_counts.csv',index_col=0)
        from us_migration.eda import FEATURES
        target='net_individuals_per_1000'
        ranks=pd.DataFrame({'spearman':spearman[target], 'pearson':pearson[target], 'pair_count':counts[target]}).loc[FEATURES]
        ranks=ranks.loc[ranks.spearman.abs().sort_values(ascending=False).index]
        ranks.to_csv(ROOT/'reports/tables/migration_correlations.csv')
        report.append('Largest absolute Spearman associations with net IRS individuals per 1,000 ACS residents in the latest-year validated county cross section with training-imputed socioeconomic predictors:')
        report.append('')
        for name,row in ranks.head(5).iterrows():
            report.append(f"- {name}: Spearman {row.spearman:.3f}, Pearson {row.pearson:.3f}, pair count {int(row.pair_count):,}.")
    report+=['', 'These are exploratory associations. Population-denominator mismatch, nominal dollar units, overlapping ACS windows, changing geography, and IRS series breaks constrain interpretation. They do not establish causation.', '',
        '## Reproducibility', '',
        'See `docs/workflow.md` for commands, `docs/coverage-manifest.json` for planned scope, `docs/coverage-observed.csv` for observed source-year coverage, and the executed notebooks for diagnostics and plots. Raw requests, timestamps, headers, and checksums live under `data/raw/`; exact processed input versions are listed in `data/processed/provenance.json`.', '',
        f'Unresolved/nonpublished request IDs across run logs: {len(unresolved)}. See `reports/tables/acquisition_status.csv`; metadata 404s are recorded separately from successful data retrievals.']
    pd.DataFrame(unresolved).to_csv(ROOT/'reports/tables/acquisition_status.csv',index=False)
    (ROOT/'reports/eda_summary.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('Wrote coverage and EDA report. Missing state shards:',len(missing_shards))
    if missing_shards: raise SystemExit(1)

if __name__=='__main__': main()
