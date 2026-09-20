# Reproduce the acquisition and exploratory analysis

Run these PowerShell commands from the repository root. The existing virtual
environment is `us-migration/`; substitute `.venv/` for a fresh checkout.

```powershell
.\us-migration\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts/download_data.py --start 2009 --end 2026
python scripts/download_cleaning_support.py
python -m pytest -q
python scripts/run_notebooks.py
python scripts/audit_data.py
```

The downloader reads `CENSUS_API_KEY` from the root `.env` file, regardless of the
working directory. The key is sent only to the Census API. NOAA downloads here
use public county bulk files, so `NOAA_CDO_TOKEN` is not needed. Census uses several
hundred small historical state queries; three independent state requests run
concurrently. Retries handle transient HTTP errors and rate limits.

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

`scripts/clean_data.py` reads only the active snapshots; it needs no network.
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
| `fema_county_year` | Distinct disaster numbers beginning in each county/year; sparse event table |
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

Open these notebooks in the IDE and select the repo's Python environment, or run
`python scripts/run_notebooks.py` to execute both offline:

1. `01_data_cleaning.ipynb`: original raw responses, visible
   source cleaning, before/after table images, NOAA annual-completeness summaries, a full
   offline rebuild, and a final missing-free cohort with summaries/exclusion audits.
2. `02_eda_findings.ipynb`: exactly ten findings charts from that cohort, including
   distributions, a balanced-county trend, rankings, hexbin associations, grouped
   boxplots, and an annotated correlation matrix with pair counts.

Notebook 01 can start directly from existing raw snapshots and rebuilds the source
tables itself; a separate `clean_data.py` run is optional when using that notebook.
See [the notebook cleaning guide](notebook-cleaning.md) for exact inclusion rules,
derived variables, selection limitations, and the complete list of ten charts.

The runner registers its kernel and runtime files locally under `data/interim/`.
It executes using the Python interpreter that launched the command and stops on
cell errors. Notebooks contain saved outputs; CSV diagnostics are written to
`reports/tables/`, before/after PNGs to `reports/figures/cleaning/`, and ten captioned
EDA figures to `reports/figures/eda/`.
Edit cleaning code directly in notebook 01. `scripts/clean_data.py` executes that notebook alone.
`scripts/build_notebooks.py` preserves notebook 01 and regenerates only notebook 02, clearing its outputs.

## 4. Audit and document findings

`python scripts/audit_data.py` verifies active raw hashes, checks all expected
historical ACS state shards, writes observed coverage, and summarizes the executed
EDA into `reports/eda_summary.md`. Review that report alongside the notebooks.
`requirements-lock.txt` records the environment used for this run; it targets the
local Python 3.13 environment. The maintained direct requirements have bounded
versions; the lock provides the exact resolved versions for reproduction.

Raw/cleaned data and credentials are excluded from Git. The notebooks, code,
manifest, compact report, and diagnostic CSVs are reviewable project artifacts.
Review notebook outputs before committing. No modeling, geographic reallocation,
inflation adjustment, causal analysis, or deployment occurs in this pipeline.
