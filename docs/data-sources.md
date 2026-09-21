# Data sources

The machine-readable [coverage manifest](coverage-manifest.json) describes planned
coverage. [Observed coverage](coverage-observed.csv) records what was actually
downloaded and cleaned. Source release limits differ; the data do not form a
balanced annual panel across all sources.

| Publisher / source | Official documentation | Local snapshot prefix |
|---|---|---|
| IRS SOI migration | [Index and release guides](https://www.irs.gov/statistics/soi-tax-stats-migration-data) | `data/raw/irs/` |
| Census ACS five-year characteristics | [Developer datasets](https://www.census.gov/data/developers/data-sets/acs-5year.html) | `data/raw/acs/` |
| Census ACS migration flows | [API documentation](https://www.census.gov/data/developers/data-sets/acs-migration-flows.html) | `data/raw/acs_flows/`, `data/raw/acs_state_flows/` |
| Census 2005–2009 county flows | [Original tables](https://www.census.gov/data/tables/2009/demo/geographic-mobility/county-to-county-migration-2005-2009.html) | `data/raw/acs_flows/2009/` |
| FEMA OpenFEMA v2 declarations | [Dataset fields and coverage](https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2) | `data/raw/fema/` |
| NOAA NCEI nClimDiv | [Versioned county files](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/), [county record layout](https://www.ncei.noaa.gov/pub/data/cirs/climdiv/county-readme.txt) | `data/raw/noaa/` |

Original publisher documentation and data notices remain applicable; the repo's
MIT license covers its original code, not a relicensing of source datasets.
Credit the publishers and specific releases in analysis products. Public download
access does not imply that a publisher endorses this analysis.

Every active raw snapshot has a URL, UTC retrieval timestamp, SHA-256 checksum,
byte count, and response metadata in `data/raw/catalog.json` and an adjacent
sidecar. Downloaded documentation includes IRS release PDFs, ACS variable
metadata, FEMA field metadata, and the NOAA record layout. No key is needed for
IRS/FEMA/NOAA bulk files. Census requests require `CENSUS_API_KEY` in `.env`.

The ACS field mapping is `ACS_VARIABLES` in `src/us_migration/acquisition.py`.
For each available estimate, request its published margin of error. The chosen
tables cover population, age, poverty, income, employment, education, housing
units, ownership, home values, and gross rent. Availability is checked per vintage.

See [workflow](workflow.md) for acquisition commands and [methodology](methodology.md)
for time alignment, geographic scope, measurement units, and missing-value rules.


Historical ACS supplements use same-vintage five-year B15002 (education, 2009-2011)
and B23001 (employment, 2009-2010), at county and state levels. Their immutable
snapshots live in `data/raw/acs_historical/`; field membership is selected and
validated from the saved Census variable metadata. See [the glossary](data-glossary.md).

Monetary imputation uses BLS annual CPI-U, series `CUUR0000SA0`, from `https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0`. Immutable responses are stored in `data/raw/inflation/cpi_u/`; [the compact annual reference](cpi-u-annual.csv) preserves source URLs and hashes.
