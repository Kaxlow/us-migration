# Cleaned-data glossary

The primary downstream file is `data/processed/analysis_county_year.parquet`
(with an equivalent CSV). One row is an analysis geography and ending year.
Alaska and Connecticut use state observations; other US analysis units are counties.
County-only EDA filters `geography_level == "county"`.
Source tables preserve missing values and uncertainty. The final cohort contains
only rows passing the explicit completeness, range, and arithmetic checks in
`notebooks/01_data_cleaning.ipynb`; exclusions are recorded, not silently dropped.

## Analysis fields

| Field | Definition and units |
|---|---|
| `county_fips` | Five-character Census geographic code; preserve leading zeros. State analysis units use the two-digit state code plus `000`. |
| `county_name` | Published geography label; may name a state. Not a join key. |
| `year` | ACS five-year window ending year and IRS migration-interval ending year; FEMA/climate are aligned to this calendar year. |
| `geography_level` | `county` or `state`. Do not treat state rows as counties. |
| `population` | ACS total population, persons (B01003_001). |
| `median_age` | ACS median age, years (B01002_001). |
| `median_household_income` | Median household income in the past 12 months (B19013_001), published release-year dollars. |
| `median_home_value` | Median value of owner-occupied housing units (B25077_001), published dollars. |
| `median_gross_rent` | Median monthly gross rent for renter-occupied units paying cash rent (B25064_001), published dollars. |
| `poverty_pct` | 100 times persons below poverty divided by persons for whom poverty status is determined. Not a share of all residents. |
| `unemployment_pct` | 100 times unemployed civilians divided by civilian labor force, age 16+. Not unemployed divided by population. |
| `vacancy_pct` | 100 times vacant housing units divided by all housing units. |
| `homeownership_pct` | 100 times owner-occupied units divided by occupied housing units. |
| `bachelors_plus_pct` | 100 times bachelor's, master's, professional, and doctorate counts combined, divided by population age 25+. |
| `declarations` | **Distinct underlying FEMA incidents**, despite the legacy column name. Multiple declaration numbers with the same `incidentId` count once per analysis geography, assigned to its earliest local incident-start year. Zero means no mapped FEMA incident in a completed covered year, not no hazard. |
| `precipitation_inches` | Sum of 12 complete monthly NOAA precipitation observations, inches/year. |
| `temperature_f` | Unweighted mean of 12 complete NOAA monthly mean temperatures, degrees Fahrenheit. |
| `inflow_individuals` | IRS individuals represented by published domestic migration inflow totals; not a count of all migrants. |
| `outflow_individuals` | IRS individuals represented by published domestic migration outflow totals. State units use interstate totals. |
| `net_individuals` | Inflow individuals minus outflow individuals; may be negative. |
| `inflow_individuals_per_1000` | 1,000 times inflow individuals divided by ACS population. |
| `outflow_individuals_per_1000` | 1,000 times outflow individuals divided by ACS population. |
| `net_individuals_per_1000` | 1,000 times net individuals divided by ACS population. |
| `identifier_repaired` | Whether the geographic identifier was repaired from an unambiguous reference. |
| `socioeconomic_imputed` | At least one eligible socioeconomic predictor was filled using training-period medians. Historical reconstruction alone does not set this flag. |
| `data_split` | `train` through 2018, `validation` 2019-2020, `test` thereafter; the current migration observations end in 2023. |
| `log10_population` | Base-10 logarithm of population. |
| `education_band` | Bachelor's-plus share: under 20%, 20 to <30%, 30 to <40%, or 40% or more. |
| `population_band` | Under 10,000; 10,000 to <50,000; 50,000 to <250,000; 250,000 or more. |
| `migration_balance` | `Net loss` below -1 net individual/1,000; `Net gain` above +1; otherwise `Near balance`. |
| `net_rate_iqr_flag` | Net migration rate outside the year's Q1 minus 1.5 IQR or Q3 plus 1.5 IQR; flagged observations are retained. |

Dollar variables are not converted to a common price year across releases. Conversion to a common dollar basis will be done when performing multi-year analysis on the data.
Migration rates mix IRS and ACS reference populations; rates above 1,000 per
1,000 are held out for denominator review. These are descriptive measures.

## Count components and provenance flags

The following components live in source/prepared tables. Their flags also travel
to the final analysis file so derived percentages remain auditable.

| Component | Definition / original ACS cells |
|---|---|
| `poverty_universe` | Population with determined poverty status, B17001_001. |
| `below_poverty` | Population below poverty, B17001_002. |
| `civilian_labor_force` | Civilian employed plus unemployed persons age 16+, B23025_003. For 2009-2010, sum disjoint employed and unemployed B23001 sex-age cells, including ages 65+. Armed forces are excluded. |
| `unemployed` | Unemployed civilian persons age 16+, B23025_005; reconstructed from all B23001 unemployed sex-age cells for 2009-2010. |
| `housing_units` | All housing units, B25002_001. |
| `vacant_units` | Vacant housing units, B25002_003. |
| `occupied_units` | Occupied housing units, B25003_001. |
| `owner_occupied_units` | Owner-occupied housing units, B25003_002. |
| `population_25_plus` | Population age 25+, B15003_001; B15002_001 for 2009-2011. |
| `bachelors` | Highest attainment bachelor's degree, B15003_022; B15002_015 + B15002_032 for 2009-2011. |
| `masters` | Highest attainment master's degree, B15003_023; B15002_016 + B15002_033 for 2009-2011. |
| `professional_degree` | Highest attainment professional school degree, B15003_024; B15002_017 + B15002_034 for 2009-2011. |
| `doctorate` | Highest attainment doctorate, B15003_025; B15002_018 + B15002_035 for 2009-2011. |

- `<variable>_imputed`: boolean for each of `median_age`, `median_household_income`,
  `median_home_value`, `median_gross_rent`, and the count components above.
  Education and employment flags remain false: those counts are never median-filled.
  Other missing levels use training-year state medians, with a national fallback;
  eligible counts use population-normalized medians. Missing education/employment
  after reconstruction causes a validation exclusion, not a statistical fill.
- `<variable>_reconstructed`: boolean for `civilian_labor_force`, `unemployed`,
  `population_25_plus`, `bachelors`, `masters`, `professional_degree`, and `doctorate`.
  True means an unavailable original measure was replaced with historical
  observations from equivalent cells in the same ACS five-year window/geography.
- `<variable>_moe`: published 90% margin of error in the estimate's units.
  Reconstructed sums use the square root of summed squared component MOEs,
  an approximation; derived percentage MOEs are not calculated.
- `<variable>_flag` / `<variable>_moe_flag`: source-table availability and cleaning
  annotation, including `not_available`, `special_value`, `reconstructed_B15002`,
  `reconstructed_B23001`, or `derived_rss_moe`. Empty means no such annotation.
- `source_snapshot`: raw content SHA-256 for the main input. Historical components
  have additional snapshots listed in `provenance.json`; that main hash alone is
  not the complete lineage of a reconstructed measure.
- `period_start`, `period_end`: ACS five-year bounds; not independent annual values.

Historical reconstruction uses five-year rather than one-year estimates to retain
small-county coverage and the same reference period. It does not undo questionnaire
changes in early windows. See [methodology](methodology.md).

## Supporting cleaned tables

| Table / artifact | Grain and purpose |
|---|---|
| `county_features`, `state_features` | ACS geography/ending year; estimates, base counts, MOEs, flags, reconstructed history. State inputs support Alaska and Connecticut analysis units. |
| `county_geography_vintages` | Native county code/name/year reference; not a boundary allocation crosswalk. |
| `irs_records` | Parsed source publication rows; both inflow/outflow views, summary categories and suppression annotations retained. |
| `irs_duplicate_records` | Repeated original IRS rows retained for audit. |
| `irs_county_flows` | Domestic origin/destination county pair and interval-ending year, canonical inflow view. `individuals`, `returns`, and `agi` preserve IRS meanings; AGI is in published thousands of dollars. |
| `irs_county_totals`, `irs_state_totals` | Geography/year/publication view totals; `row_type` identifies domestic totals and other published categories. |
| `acs_county_flows`, `acs_state_county_flows` | Origin/destination/ending-year flow estimates. `movers` and `movers_moe` are persons and their 90% MOE. `origin_geography`, `domestic_pair`, and `origin_id` distinguish county, state, and foreign/other origins; products are not interchangeable. |
| `fema_declarations` | Original FEMA declaration-area records plus parsed dates, geography, year, and duration checks. No original declarations are discarded merely because another declaration describes the same event. |
| `fema_cleaned_incidents` | Declaration-area rows after date completion/exclusions; despite its legacy name, it is not yet one row per incident. |
| `fema_area_county_mapping` | Source record `id` and mapped `county_fips`; `source_county_fips`, `mapping_method`, and `geography_reference_year` document published, statewide, name, tribal, or state-unit mapping. |
| `fema_county_events` | One `county_fips`/`event_id`; declaration numbers for the same underlying event are consolidated. See event fields below. |
| `fema_county_year` | Sparse geography/year incident totals (`declarations`) and distinct `incident_types`. |
| `climate_monthly` | NOAA county/year/month/element; source missing markers remain null. |
| `climate_county_year`, `climate_state_year` | Geography/calendar year; precipitation and temperature aggregates require 12 months. `tmax_f` and `tmin_f` are means of monthly maximum/minimum temperatures, not annual absolute extremes. |
| `climate_incomplete_years` | Climate groups failing full-year completeness. |
| `county_year_panel` | ACS-centered join of source features, IRS totals, FEMA incidents, and climate before imputation/validation. |
| `prepared_geography_year` | Panel with eligible imputation, provenance flags, and temporal split before cohort exclusions. |
| `analysis_county_year` | Validated downstream fields defined above; Parquet and CSV exports. |
| `analysis_exclusions.csv` | Rejected geography/year and semicolon-separated validation reasons. |
| `analysis_cleaning_manifest.json` | Cohort dimensions, validity checks, and transformation metadata. |
| `table_inventory.csv` | Dimensions, year bounds, and key checks for saved source tables. |
| `provenance.json` | Build-year range and exact immutable input snapshots, including historical ACS supplements. |
| `socioeconomic_imputer.json` | Fitted statistics for eligible predictors, training cutoff, and split settings. |
| `fema_date_cleaning.json`, `fema_date_exclusions.csv` | Date-completion diagnostics and excluded source records. |
| `fema_unresolved_areas.csv` | FEMA records whose areas could not be mapped confidently. |
| `climate_monthly_completeness.csv` | Climate month-count diagnostics. |

## FEMA event fields

| Field | Meaning |
|---|---|
| `incidentId` | FEMA's underlying incident identifier in the source. |
| `disasterNumber` | FEMA declaration number; multiple numbers may belong to one incident. |
| `id` | FEMA declaration-area record identifier, not an event identifier. |
| `event_id` | `incident:<incidentId>`, or `declaration:<disasterNumber>` when incident ID is missing/invalid. |
| `event_key_method` | `official_incident_id` or `declaration_fallback`; titles and dates alone do not establish identity. |
| `declaration_numbers` | Sorted, semicolon-separated declaration numbers contributing to this geography/event. |
| `declaration_count` | Number of distinct contributing declaration numbers before event consolidation. |
| `source_record_count` | Number of distinct contributing source record IDs. |
| `incidentBeginDate`, `incidentEndDate` | Earliest local start and latest local end across the linked, date-cleaned records. |
| `year` | Year of earliest local start; a linked event crossing years is counted only once per geography. |
| `incidentType` | Sorted unique source incident-type labels, semicolon-separated if they differ. |

`reports/tables/fema_event_deduplication.csv` lists geography/events linked to more
than one declaration number. `reports/tables/acs_historical_reconstruction.csv`
counts reconstructed county measures by year. Original raw snapshots remain intact.


## Monetary imputation dollar basis

Observed ACS monetary values stay exactly as published in all cleaned exports.
Before fitting the monetary donor medians, the imputer converts income, home
value, and gross rent to the latest ACS year present in the input panel (currently
2024). It uses the annual average, not seasonally adjusted BLS CPI-U all-items
US city average, series `CUUR0000SA0`, as a general purchasing-power deflator.
This is CPI-U, not the R-CPI-U-RS series recommended by Census for certain income
comparisons; the selected series and factors are explicit for reproducibility.

For a donor in year y, the fit value is `published_value * CPI(base_year) / CPI(y)`.
State and national fallback medians use training rows only. For a missing value
in year t, the monetary fill is `fitted_median * CPI(t) / CPI(base_year)`.
Thus filled and observed values share the receiving row's published-year dollar
basis. This temporary conversion does not turn cleaned exports into constant-dollar
series; a specific multi-year analysis must prepare its own common-dollar columns.

[Annual CPI values](cpi-u-annual.csv) include BLS API source URLs and raw-snapshot
checksums. The support downloader refreshes this compact reference from verified
cached snapshots. `reports/tables/monetary_imputation_factors.csv` records the factors
used, and `data/processed/socioeconomic_imputer.json` records the fit dollar year,
series, index values, output basis, and fitted donor statistics. Monetary entries
in those statistics are common-dollar values, not published-year amounts.

Sources: [BLS CPI database](https://www.bls.gov/cpi/data.htm) and
[Census comparison guidance](https://www.census.gov/programs-surveys/acs/guidance/comparing-acs-data/2024.html).
