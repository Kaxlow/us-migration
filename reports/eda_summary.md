# Download and exploratory analysis report

Generated 2026-09-21T00:18:08.328056+00:00.

Verified SHA-256 checksums for 473 active snapshots (1.34 GB). Previous immutable versions and exploratory verification files may use additional disk space.

County panel: 49,717 rows, 3,109 distinct native county codes, 2009–2024. Counts include code changes across years, not a fixed geography.

Missing historical ACS flow state shards: 0.

| Table | Rows | Years | Duplicate keys |
|---|---:|---|---:|
| county_features | 51,533 | 2009–2024 | 0.0 |
| county_geography_vintages | 51,533 | 2009–2024 | 0.0 |
| state_features | 32 | 2009–2024 | 0.0 |
| irs_records | 2,957,793 | 2009–2023 | nan |
| irs_duplicate_records | 3,994 | 2014–2014 | nan |
| irs_county_flows | 922,341 | 2009–2023 | 0.0 |
| irs_county_totals | 93,851 | 2009–2023 | 0.0 |
| irs_state_totals | 60 | 2009–2023 | 0.0 |
| acs_county_flows | 5,803,110 | 2009–2020 | 0.0 |
| acs_state_county_flows | 131,135 | 2021–2022 | 0.0 |
| fema_declarations | 34,290 | 2009–2026 | 0.0 |
| fema_cleaned_incidents | 34,290 | 2009–2026 | 0.0 |
| fema_area_county_mapping | 34,589 | 2009–2026 | 0.0 |
| fema_county_events | 25,050 | 2009–2026 | 0.0 |
| fema_county_year | 19,435 | 2009–2026 | 0.0 |
| climate_monthly | 2,714,688 | 2009–2026 | 0.0 |
| climate_county_year | 53,414 | 2009–2025 | 0.0 |
| climate_state_year | 34 | 2009–2025 | 0.0 |
| county_year_panel | 49,717 | 2009–2024 | 0.0 |

## Data quality findings

- IRS 2009–2011 uses legacy XLS archives; later CSVs require UTF-8 or Windows-1252 decoding. The cleaner preserves both publication views and exports inflow-view domestic county pairs separately.
- ACS 2009–2010 lack the selected B23025 and B15003 tables; 2011 lacks the selected B15003 table. These measures are reconstructed from same-window B23001 employment and B15002 education observations, with component-based MOEs; no median imputation is used for education or employment.
- ACS county-to-county data end in 2020. State-to-county API vintages observed here end in 2022; later attempted metadata endpoints returned 404.
- NOAA county state codes were mapped explicitly to Census FIPS. No annual climate value is generated without all 12 monthly observations.
- Retrieved NOAA files include all 50 states and DC. The special DC climate code is crosswalked to 11001, and both documented -99.99 and observed -99.90 temperature missing markers are recognized.
- IRS 2013–2014 contains 2,020 exact duplicate source rows across both views. The original records and a duplicate audit table are preserved; the canonical inflow table removes 1,007 repeated county-pair records after checking for numeric conflicts.
- Alaska and Connecticut use official state-level features and interstate outcomes in the analysis file; county-only charts report them separately.
- FEMA counts use distinct official incident IDs per analysis geography, combining different declaration numbers for the same event. Original declarations and the event mapping audit are retained.
- Monetary imputation fits training donors in a common dollar basis using annual BLS CPI-U, then converts fills back to each row year; observed ACS monetary values are preserved.
- The panel is a native-geography descriptive join, not a geographically harmonized or release-date-safe modeling dataset.

## Correlation findings

The validated predictor-imputed cohort contains 46,026 geography-years; 3,691 input rows are excluded with recorded reasons.
It has 0 missing values, 0 infinities, and 0 duplicate county-year keys under the documented rules.
Raw-versus-cleaned comparison images are in `reports/figures/cleaning/`; the ten captioned findings charts are in `reports/figures/eda/` and `reports/eda_visualizations.md`.
Ordinary IQR outliers are retained and flagged; denominator-review cases above 1,000 per 1,000 residents are held out without claiming the original counts are erroneous.

Largest absolute Spearman associations with net IRS individuals per 1,000 ACS residents in the latest-year validated county cross section with training-imputed socioeconomic predictors:

- homeownership_pct: Spearman 0.290, Pearson 0.292, pair count 3,050.
- median_age: Spearman 0.252, Pearson 0.254, pair count 3,050.
- median_home_value: Spearman 0.238, Pearson 0.085, pair count 3,050.
- precipitation_inches: Spearman 0.210, Pearson 0.208, pair count 3,050.
- temperature_f: Spearman 0.145, Pearson 0.163, pair count 3,050.

These are exploratory associations. Population-denominator mismatch, nominal dollar units, overlapping ACS windows, changing geography, and IRS series breaks constrain interpretation. They do not establish causation.

## Reproducibility

See `docs/workflow.md` for commands, `docs/coverage-manifest.json` for planned scope, `docs/coverage-observed.csv` for observed source-year coverage, and the executed notebooks for diagnostics and plots. Raw requests, timestamps, headers, and checksums live under `data/raw/`; exact processed input versions are listed in `data/processed/provenance.json`.

Unresolved/nonpublished request IDs across run logs: 6. See `reports/tables/acquisition_status.csv`; metadata 404s are recorded separately from successful data retrievals.
