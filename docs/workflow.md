# Reproduce the acquisition and exploratory analysis

Run these PowerShell commands from the repository root. The existing virtual
environment is `us-migration/`; substitute `.venv/` for a fresh checkout.

```powershell
.\us-migration\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts/download_data.py --start 2009 --end 2026
python scripts/download_cleaning_support.py
python -m pytest -q
# In Jupyter: run the needed notebooks, inspect outputs and save; then close or return here.
python -m jupyterlab
python scripts/audit_data.py
```

The downloader reads `CENSUS_API_KEY` from the root `.env` file, regardless of the
working directory. The key is sent only to the Census API. NOAA downloads here
use public county bulk files, so `NOAA_CDO_TOKEN` is not needed. Census uses several
hundred small historical state queries; three independent state requests run
concurrently. Retries handle transient HTTP errors and rate limits.

Request and activate a [Census API key](https://api.census.gov/data/key_signup.html).
Create the local configuration from `.env.example` when it is absent, then set
`CENSUS_API_KEY` in that file. Keep existing values when refreshing configuration:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item .env.example .env }
notepad .env
git check-ignore .env
```

The public NOAA bulk workflow can leave `NOAA_CDO_TOKEN` blank. Download scripts
load `.env` explicitly and redact credentials from recorded URLs and errors.

## 1. Coverage and acquisition

`coverage-manifest.json` defines source scope, grain, year meaning, access,
selected variables, coverage, and limitations. `coverage-observed.csv` is generated
from the actual cleaned data and includes unavailable source-years.

For IRS, start 2009 means the 2008–2009 filing-year migration interval. For ACS,
it means the 2005–2009 estimate. For FEMA and NOAA, it means incident start year
and calendar year, respectively. No recent unpublished years are manufactured.

Acquire sources independently or retry a partial run:

```powershell
python scripts/download_data.py --sources irs fema noaa --start 2009 --end 2026
python scripts/download_data.py --sources acs acs_flows --start 2009 --end 2026
```

Existing files are reused only after their checksum is verified. To check for
upstream revisions, add `--refresh`. IRS/NOAA discovery indexes are also refreshed
with this flag. Never run two download processes simultaneously: one process
owns the catalog. Interruptions preserve every completed request.

`data/raw/<source>/<logical-request>/<SHA-256>.<extension>` holds original response
bodies. ZIP files remain intact; cleaning reads archive members in memory.
Each snapshot has a metadata sidecar with source URL (credentials redacted),
retrieval timestamp, SHA-256, byte count, content type, and upstream revision
headers when available. Different revisions get different filenames.
`data/raw/catalog.json` selects the active version; `data/raw/runs/` records attempts.
`data/raw/latest_run.json` describes only the most recent invocation, not all sources.

A failed request is reported rather than silently replaced with an empty dataset.
Rerun the same command to resume failed requests. A nonzero downloader exit means
an unresolved retrieval problem. Unpublished metadata vintages above the highest
observed release and explicitly listed unavailable variables are reported as
coverage information rather than retrieval failures; inspect the run log.
No credentials are printed, stored in URL metadata, or included in notebooks.

The initial backfill uses a few GB including raw revisions, verification workbooks,
and cleaned tables. Processing and profiling load one or more large flow tables;
allow several GB of available RAM. A remote database is not required.

## 2. Clean source tables

The data-cleaning notebook reads the active local snapshots. Set its year parameters, restart
the project kernel, run all cells in Jupyter, inspect the results and save.
It verifies the inputs against their recorded hashes and writes Parquet files
under `data/processed/`. This directory is ignored by Git. Rerunning cleaning
replaces derived outputs, not raw snapshots. Use a consistent year range for the
final analysis; the provenance file records that range and exact input snapshots.

| Output | Grain / purpose |
|---|---|
| `county_features` | Native county × ACS ending year; estimates, MOEs, missing-value flags, selected percentages |
| `county_geography_vintages` | County codes/names by ACS release; not a boundary-allocation crosswalk |
| `irs_records` | All parsed IRS records, both publication views, with summary and suppression flags |
| `irs_duplicate_records` | Original repeated source rows for audit; retained without silently altering the source table |
| `irs_county_flows` | Domestic county pairs from the inflow view only; origin/destination are explicit |
| `irs_county_totals` | Published domestic totals per county/year/view |
| `acs_county_flows` | County/foreign-origin to county estimates, with domestic-pair flags and MOEs |
| `acs_state_county_flows` | State-origin to county estimates; separate from county-pair flows |
| `fema_declarations` | Declaration-area records, dates, county-code flags, and duration diagnostics |
| `fema_county_events` | One geography/event with declaration numbers, event dates, and linkage method |
| `fema_county_year` | Distinct incident IDs by earliest local start year; sparse event table |
| `climate_monthly` | County × month × climate variable, missing monthly values retained |
| `climate_county_year` | Annual precipitation sums and means of monthly temperatures; 12-month completeness counts |
| `county_year_panel` | ACS-centered, same-ending-year descriptive join of characteristics, IRS totals, FEMA, NOAA |
| `state_features`, `irs_state_totals`, `climate_state_year` | Official AK/CT state features, interstate migration and state climate |
| `fema_cleaned_incidents`, `fema_area_county_mapping` | Date-completed records and explicit geographic mappings |
| `prepared_geography_year` | Predictor imputation, flags and temporal split before final validation |
| `analysis_county_year` | Primary downstream predictor-imputed county/state analysis dataset; no missing/nonfinite values or documented rule violations |

`table_inventory.csv` reports table dimensions, year ranges, and duplicate-key
counts. `provenance.json` identifies the exact raw inputs. Source snapshot IDs
are retained on the source tables; derived table lineage is recorded at build level.
Missing source families are not synthesized. Check inventory and observed coverage
before using a partial download for analysis.

## 3. Execute and inspect the notebooks

Launch `python -m jupyterlab` from the active project environment and repository
root. Open a notebook, select the project's Python kernel, choose **Restart Kernel
and Run All Cells**, inspect each output for errors, and save with Ctrl+S.
JupyterLab is included in the development requirements. Check `sys.executable`
when selecting among kernels; an older saved kernel name can be replaced with the
Python kernel supplied by the current environment.

1. **Data cleaning:** set `START_YEAR` / `END_YEAR` in the parameter cell;
   rebuild from acquired raw snapshots and cleaning supplements.
2. **Exploration:** consume the processed outputs and regenerate charts and diagnostics.
3. **Clustering / PCA:** independently consume the cleaned analysis Parquet.
4. **Naive Bayes:** classify inflow tertiles and export evaluation evidence.
5. **Decision trees:** classify outflow tertiles and net direction; runs independently; export combines matching classification evidence.

The existing processed dataset permits independent analysis refreshes. All notebooks are maintained directly; reusable implementations live in the Python package. Execution generates
figures, tables and website exports; saving preserves cell counts and results.
Cleaning diagnostics use `reports/tables/` and `reports/figures/cleaning/`. Analytical results use owned topic bundles under `reports/analyses/`; website packaging copies those results. After changing a helper, restart the
kernel before rerunning so the imported implementation is refreshed.

## 4. Audit and document findings

`python scripts/audit_data.py` verifies active raw hashes, checks all expected
historical ACS state shards, writes observed coverage, and summarizes the executed
EDA into `reports/eda_summary.md`. Review that report alongside the notebooks.
`requirements-lock.txt` records the environment used for this run; it targets the
local Python 3.13 environment. The maintained direct requirements have bounded
versions; the lock provides the exact resolved versions for reproduction.

Raw/cleaned data and credentials are excluded from Git. The notebooks, code,
manifest, compact report, and diagnostic CSVs are reviewable project artifacts.
Review saved notebook outputs and generated artifacts before committing.
Classification is retrospective; deployment is a separately authorized action.

Historical ACS reconstruction and event deduplication are audited in `reports/tables/acs_historical_reconstruction.csv` and `reports/tables/fema_event_deduplication.csv`. See [the data glossary](data-glossary.md) for cleaned fields.


## Monetary imputation dollar basis

Before fitting monetary donor medians, convert training observations using annual
BLS CPI-U (`CUUR0000SA0`) to the latest ACS year in the panel (currently 2024).
Convert each fill back to its receiving row's dollar year and preserve observed
values exactly. Cleaned exports therefore retain their published-year units;
common-dollar exports are reserved for analysis-specific preparation.
See [the glossary](data-glossary.md#monetary-imputation-dollar-basis) for formulas,
index selection, and provenance. Factors and fitted-statistic units are recorded
in `reports/tables/monetary_imputation_factors.csv` and `socioeconomic_imputer.json`.

## Incremental website export

Python modules own reusable implementation. Notebooks own analysis choices, execution, evidence, and interpretation. After cleaning, exploration, clustering, PCA, Naive Bayes, and decision trees each consume the processed dataset independently. Their owned bundles live under `reports/analyses/`. The default exporter packages all available completed topics; select topics to avoid unrelated refreshes:

```powershell
python scripts/export_cleaning_evidence.py
python scripts/export_website_data.py
python scripts/export_website_data.py --topics pca
python scripts/export_website_data.py --topics classification
python -m pytest -q
```

Run the cleaning-evidence command after saving the cleaning notebook. Run the packaging command after saving an analytical notebook. Classification packaging requires both independently generated bundles, with matching input, county membership, split, and target context. A failed validation leaves existing publication artifacts intact. Packaging updates the compact Findings payload after selected topics.

Conclusions in clustering, PCA, Naive Bayes and decision trees are authored directly in Markdown cells. The repository module `src/us_migration/analysis_exports.py` copies that reviewed prose into the topic bundles. Each notebook invokes it with one collapsed helper call immediately before Conclusions; the conclusion sections contain only Markdown. Review the conclusion values after changing data or model choices, then save the notebook before exporting. Rebuild the landing-page county-pair flow files with `python scripts/build_flow_map.py` after refreshing `irs_county_flows.parquet`.

For a fresh checkout, regenerate ignored canonical figures by executing the corresponding notebooks before packaging. Existing committed website artifacts remain available for local preview. Source and cleaning audit tables remain in `reports/tables/`; numerical analytical evidence belongs to topic bundles.

Follow [Adding an analysis](adding-an-analysis.md) for incremental extensions and [website verification](../website/README.md#browser-verification) for interactive checks.
