# Acquisition and exploratory analysis methodology

The analysis asks which county characteristics are associated with migration.
It does not estimate causal effects. Use the cleaned tables for data discovery
and model design, with the following decisions explicit.

## Time and coverage

- IRS year is the ending filing year, not an exact calendar interval in which
  all moves occurred. Returns/individuals cover the matched tax population.
- ACS values are five-year period estimates. A 2009 row describes 2005–2009;
  consecutive rows share four survey years. Migration estimates represent prior-year
  mobility pooled across that window, not cumulative five-year flows.
- FEMA events are assigned to incident start year. Missing starts remain missing;
  declaration dates do not silently substitute for incident dates. Events with
  missing starts and in-range declaration dates remain in the event table.
- NOAA monthly source history is preserved in full and filtered to 2009 onward
  during cleaning. Incomplete annual precipitation/temperature values remain null.
- The descriptive panel joins matching numeric year labels. It is not a forecast
  training table. The notebook's lagged comparison is exploratory and does not
  enforce release dates; production prediction requires publication-date-aware
  features and future-year/geographic holdouts.

## Geography

County codes are strings with leading zeros. Preserve source-year geography.
Neither identical FIPS nor changing names guarantee constant boundaries.
The county vintage table is an audit aid, not a population-weighted crosswalk.
Connecticut and Alaska use official state-level ACS and NOAA features and IRS interstate flows.
They remain in the analysis dataset with geography_level=state; county-only charts report them separately.
Other boundary changes still need review before modeling.

The county panel uses 50 states and DC. ACS source tables retain Puerto Rico
where published. Foreign origins and special IRS totals remain distinguishable.
NOAA uses a separate climate-state numbering scheme; the parser maps it to FIPS
using the published county readme, with the DC exception from the county crosswalk
(`18511` maps to `11001`). This retrieved version contains all 50 states and DC;
actual absent counties and join rates are reported in the notebook.

## Variables and missingness

- IRS returns/individuals: numeric negative suppression values and nonnumeric
  missing markers become null with a flag. AGI is in nominal thousands of dollars;
  negative AGI remains valid except the documented `-1` suppression marker.
- IRS row types distinguish domestic county pairs, nonmigrants, domestic totals,
  all-migration totals, state summaries, and other/foreign rows. Canonical pair
  data use only the inflow publication view. County totals use published domestic
  aggregates because suppressed/pooled small flows prevent reliable reconstruction.
  Exact repeated numeric county-pair records are collapsed in the canonical table;
  original rows and a duplicate audit table are retained. Conflicting pair values
  cause cleaning to fail rather than choosing one arbitrarily. The retrieved
  2013–2014 source files contain such exact duplicates in both publication views.
- ACS negative special values become null with flags. MOEs remain alongside
  estimates. Metadata determine which estimate variables exist; their associated
  MOEs are requested even if omitted from the standalone variable listing.
  Missing B23025 (2009-2010) and B15003 (2009-2011) measures are reconstructed
  from matching five-year B23001 and B15002 tables, respectively. Employment sums
  disjoint employed/unemployed sex-age cells (including ages 65+); education sums
  male/female counts. MOEs of sums use the root-sum-of-squares approximation.
  Reconstruction flags distinguish historical observations from imputation.
  Education/employment counts never use state/national median fills; unresolved
  gaps remain missing and fail final validation. Derived percentages require positive denominators; education requires
  all four degree-count components. Derived percentage MOEs are not propagated.
- Income, rent, and home values retain the published dollar basis. Pooled
  correlations can reflect inflation/trends; common-year and within-year
  comparisons provide sensitivity checks, not an inflation-adjusted series.
- FEMA county-year tables count distinct underlying incidents (`incidentId`),
  combining declaration numbers within each analysis geography. `fema_county_events`
  stores one row per geography/event with all declaration numbers; the earliest
  local incident-start date assigns its year, preventing cross-year double counting.
  Missing/invalid incident IDs fall back to declaration numbers, with an explicit
  method flag; titles alone are not used to guess event identity.
  Explicit statewide records expand to reference counties; unambiguous tribal names
  map through Census 2020 land overlaps. Unresolved areas remain in an audit. In the panel, absent counts become zero only for completed years covered
  by the bulk snapshot. This means no mapped declaration, not no hazard.
- NOAA precipitation missing marker is `-9.99`; temperature missing marker is
  `-99.99` in the old readme and `-99.90` in the actual current files; both are
  normalized to null. Annual precipitation is the sum of 12 months. Annual temperatures are
  unweighted means of the 12 monthly means. `tmax_f`/`tmin_f` are monthly average
  maximum/minimum temperatures, not annual absolute extremes.
- Migration rates divide published IRS individuals by ACS population and multiply
  by 1,000. This is an approximate descriptive rate because numerator and
  denominator populations and reference periods differ. Net = inflow − outflow.

## EDA and interpretation

Report shapes, types, uniqueness, missingness, zero/negative counts, finite-value
quantiles, skew, and IQR outliers without removing observations. Inspect source
coverage by year, join match rates by state, ACS relative MOEs, IRS disclosure
flags, paired publication differences, disaster-date anomalies, and climate
completeness. A missing pair in sparse flow data is not evidence of zero migration.

Correlation analysis excludes numeric identifiers and MOE/flag columns. Matrices
use pairwise available data with at least 30 observations and export pair counts.
Pearson describes linear association; Spearman describes rank association. The
current notebooks compare the latest common year and a balanced-county time
series, with the IRS methodology break marked. Their ten findings charts use a
predictor-imputed analysis table with identical observations across correlation cells;
matrix pair counts are exported explicitly.
No independence-based significance tests or causal interpretations are made.
Repeated windows, spatial dependence, selective missingness, administrative
coverage, and reverse causality remain material limitations.

## Validated analysis cohort

The authoritative cleaning notebook exports a single downstream dataset,
`analysis_county_year`, retaining training-only socioeconomic imputation and flags.
No separate observed-only cleaned dataset is maintained.
It preserves selected identifiers, characteristics, IRS counts, and migration
rates, while requiring no missing/nonfinite values or violations of explicit
range/arithmetic checks. This does not erase missingness from the source audit
tables or assert that all publisher estimates are correct.

The full rule set, exact exclusions, retained IQR flags, transformations, and
sampling limitations are documented in [the cleaned-data glossary](data-glossary.md).
Rows requiring denominator review (inflow/outflow above 1,000 per 1,000 ACS
residents) are held out, rather than clipped or described as proven errors.
Year/state retention summaries accompany the predictor-imputed results. Population
and education bands and a log10 population column supplement the original values.

Training-only socioeconomic imputation uses 2009 to 2018; validation is 2019 to 2020 and testing is 2021 to 2023. Base counts are scaled by observed population, imputed counts are bounded by their universes, and derived rates are recalculated. Outcomes, population, and education/employment counts are not median-imputed. See the notebook cleaning guide for date completion, flags and reference-geography limits.


## Historical ACS reconstruction and comparability

[The data glossary](data-glossary.md) documents all downstream fields and source
count definitions. `scripts/download_cleaning_support.py` downloads immutable
county and state B15002/B23001 components with the original five-year window.
One-year tables were considered but are not mixed into the panel: they describe
a different period and omit counties below the publication threshold.
See [Census product guidance](https://www.census.gov/programs-surveys/acs/guidance/estimates.html)
and [the 2009 employment table](https://api.census.gov/data/2009/acs/acs5/groups/B23001.html).

Reconstruction fixes structural table availability, not every comparability issue.
Early windows straddle the 2008 employment/education questionnaire changes; the
published historical estimates preserve those measurement limitations. Monetary
values still use each release's published dollar basis, five-year windows overlap,
and native county boundaries are not fully harmonized.

FEMA event identity follows the publisher's `incidentId` in
[Disaster Declarations Summaries v2](https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2).
Distinct IDs are not merged merely because titles or dates resemble one another.
The `declarations` analysis column retains its name for compatibility but now
means distinct FEMA incidents, not distinct declaration numbers.


## Monetary imputation dollar basis

Before fitting monetary donor medians, convert training observations using annual
BLS CPI-U (`CUUR0000SA0`) to the latest ACS year in the panel (currently 2024).
Convert each fill back to its receiving row's dollar year and preserve observed
values exactly. Cleaned exports therefore retain their published-year units;
common-dollar exports are reserved for analysis-specific preparation.
See [the glossary](data-glossary.md#monetary-imputation-dollar-basis) for formulas,
index selection, and provenance. Factors and fitted-statistic units are recorded
in `reports/tables/monetary_imputation_factors.csv` and `socioeconomic_imputer.json`.
