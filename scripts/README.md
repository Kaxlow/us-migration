# Scripts

- `download_data.py --start 2009 --end 2026`: acquire official data and immutable raw snapshots; supports `--sources` and `--refresh`.
- `clean_data.py --start 2009 --end 2026`: execute the authoritative cleaning notebook, save outputs, and export source audit tables and the imputed downstream dataset.
- `run_notebooks.py`: execute all four numbered notebooks offline and save their outputs.
- `run_phase2.py`: execute only clustering and PCA, refreshing saved notebook outputs and tracked website images/data; requires the existing cleaned Parquet input.
- `audit_data.py`: verify hashes/state shards, export observed coverage, and summarize EDA findings.
- `download_cleaning_support.py`: acquire state ACS/IRS/NOAA supplements, historical five-year ACS components, annual CPI-U, and the Census tribal/county relationship file.

Run with the repo Python environment. See [workflow](../docs/workflow.md) for full commands, inputs, outputs, and limitations.

The notebooks are the authoritative analysis source. Data refreshes execute their
fixed methodology and update saved outputs, reports, and website exports.

## Net migration, inflows, and outflows

All three rates per 1,000 ACS residents receive equal emphasis. County downloads
retain their supporting counts. The ten EDA chart groups, cluster distributions,
PCA associations, and score quintiles compare the same observations across
outcomes. Findings and captions are regenerated from executed analyses.
