# Notebooks

- `01_data_cleaning.ipynb`: authoritative source-specific cleaning code, raw/clean comparisons, intermediate diagnostics, assertions and the imputed downstream export. Edit this notebook directly.
- `02_eda_findings.ipynb`: authoritative EDA source with ten findings charts, readable titles/axes and two-sentence captions, using the same imputed dataset.
- `03_clustering.ipynb`: independent migration and characteristic clustering, k-means k=2–8, cosine/average-linkage hierarchy, silhouettes, profiles, outcome comparisons and website exports.
- `04_pca.ipynb`: characteristic PCA, eigenvalue checks, variance retention, coefficients and correlation loadings, migration comparisons and website exports.

Inputs are original snapshots indexed by `data/raw/catalog.json`. The single cleaned downstream dataset is `data/processed/analysis_county_year.parquet` (also CSV). It retains training-only socioeconomic imputation and flags, with recalculated derived variables. Source and intermediate audit tables preserve uncertainty; the final export passes documented missingness, validity and uniqueness checks. No separate observed-only cleaned version is maintained.

Execute all four with `python scripts/run_notebooks.py`, Phase 2 only with
`python scripts/run_phase2.py`, or cleaning alone with `python scripts/clean_data.py`.
You can also select the repo environment in the IDE. All four notebooks are
maintained directly. Routine data refreshes execute their existing code with the
same methodology; deliberate methodology revisions and bug fixes are made in the
notebooks. Phase 2 exports directly to tracked website assets
and data so static hosting needs no Python runtime. See
[the Phase 2 guide](../docs/methodology.md#clustering-and-pca) and
[the cleaning guide](../docs/notebook-cleaning.md) for methods and output paths.

## Net migration, inflows, and outflows

All three rates per 1,000 ACS residents receive equal emphasis. County downloads
retain their supporting counts. The ten EDA chart groups, cluster distributions,
PCA associations, and score quintiles compare the same observations across
outcomes. Findings and captions are regenerated from executed analyses.
