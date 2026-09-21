# Processed data

This directory contains derived source tables, analysis datasets, and cleaning
audits. Generated files are ignored by Git.

The authoritative [cleaning notebook](../../notebooks/01_data_cleaning.ipynb)
rebuilds these outputs from the active raw snapshots. Run it from the repository
root using:

```powershell
python scripts/clean_data.py --start 2009 --end 2026
```

Alternatively, `python scripts/run_notebooks.py` executes both cleaning and EDA.
Cleaning runs offline and replaces derived outputs; acquire the raw data and
cleaning supplements first as described in [the workflow](../../docs/workflow.md).

- Source Parquet tables retain county characteristics, migration flows and totals,
  disaster records, and climate observations at their documented grains.
- `county_year_panel.parquet` joins the source measures; `prepared_geography_year.parquet`
  adds predictor imputation and temporal split information.
- `analysis_county_year.parquet` and `analysis_county_year.csv` contain the validated
  downstream cohort, including state-level observations for Alaska and Connecticut.
- `table_inventory.csv` records source-table dimensions, year ranges, and key checks;
  `provenance.json` records the build range and exact raw inputs.
- Cleaning manifests, exclusion tables, and imputation metadata document validation
  rules, omitted observations, and fitted imputation statistics.

See [the output table guide](../../docs/workflow.md#2-clean-source-tables) for
table grains and purposes, and [methodology](../../docs/methodology.md) for
definitions, inclusion rules, and interpretation limits.

See [the cleaned-data glossary](../../docs/data-glossary.md) for variable definitions, units, provenance flags, and event-count semantics.
