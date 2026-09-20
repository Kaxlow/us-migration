# Notebooks

- `01_data_cleaning.ipynb`: authoritative source-specific cleaning code, raw/clean comparisons, intermediate diagnostics, assertions and the imputed downstream export. Edit this notebook directly.
- `02_eda_findings.ipynb`: ten findings charts with readable titles/axes and two-sentence captions, using the same imputed dataset.

Inputs are original snapshots indexed by `data/raw/catalog.json`. The single cleaned downstream dataset is `data/processed/analysis_county_year.parquet` (also CSV). It retains training-only socioeconomic imputation and flags, with recalculated derived variables. Source and intermediate audit tables preserve uncertainty; the final export passes documented missingness, validity and uniqueness checks. No separate observed-only cleaned version is maintained.

Execute both with `python scripts/run_notebooks.py`, cleaning alone with `python scripts/clean_data.py`, or select the repo environment in the IDE. Saved outputs, diagnostic CSVs and comparison/chart PNGs make the steps reviewable. See [the cleaning guide](../docs/notebook-cleaning.md) for rules, limitations and output paths.
