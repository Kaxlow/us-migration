# Project methodology

This document explains the research design, data preparation, cohort definitions,
and analytical decisions used to study US migration. Field definitions and exact
cleaning rules live in the [cleaned-data glossary](data-glossary.md); acquisition
and execution instructions live in the [workflow](workflow.md).

## Contents

- [Research question and design](#research-question-and-design)
- [Data coverage and alignment](#data-coverage-and-alignment)
- [Data preparation](#data-preparation)
- [Analysis cohorts and features](#analysis-cohorts-and-features)
- [Analytical methods](#analytical-methods)
- [Validation and limitations](#validation-and-limitations)
- [Reproducibility](#reproducibility)
- [Supervised classification](#supervised-classification)
- [Planned supervised analyses](#planned-supervised-analyses)

## Research question and design

How are counties’ economic, demographic, and environmental characteristics associated with net migration, inflows, and outflows?

Net migration, inflow, and outflow rates per 1,000 ACS residents are coequal
outcomes. Counts describe volumes. Net equals inflow minus outflow at the row
level; medians and quartiles are calculated separately for each outcome.
Its scope is descriptive and retrospective: cleaned source tables support data
discovery, a geography-year panel supports exploration, and a single-year county
cohort supports clustering, PCA and held-out classification.

The panel joins matching numeric year labels. The notebook's lagged comparison
is exploratory and does not enforce publication dates. Future prediction work
requires publication-date-aware features and future-year/geographic holdouts.

## Data coverage and alignment

### Sources and time coverage

The project combines IRS migration, ACS five-year estimates, FEMA incidents, and
NOAA weather observations. The [data sources](data-sources.md),
[coverage manifest](coverage-manifest.json), and
[observed coverage](coverage-observed.csv) document source scope and availability.
Year labels have different meanings across sources:

| Source | Meaning of year and coverage |
| --- | --- |
| IRS | Ending filing year; returns and individuals cover the matched tax population. Moves can occur across different calendar intervals. |
| ACS | Ending year of a five-year estimate. A 2009 row describes 2005–2009; consecutive rows share four survey years. Migration estimates describe prior-year mobility pooled across that window. |
| FEMA | Incident start year, using the earliest local incident start for each geography/event. Events with missing starts and in-range declaration dates remain in the event table. |
| NOAA | Calendar year. Full monthly source history is preserved, with cleaning restricted to 2009 onward. Annual summaries require 12 complete months. |

### Geography

County codes are strings with leading zeros. Preserve source-year geography:
identical FIPS codes and changing names both require boundary review. The county
vintage table supports audits; boundary harmonization requires a separate
population-weighted crosswalk.

Connecticut and Alaska use official state-level ACS and NOAA features and IRS
interstate flows. They remain in the analysis dataset with
`geography_level=state`; county-only charts report them separately. Other boundary
changes still require review before modeling.

The county panel covers 50 states and DC. ACS source tables retain Puerto Rico
where published. Foreign origins and special IRS totals remain distinguishable.
NOAA uses a separate climate-state numbering scheme; the parser maps it to FIPS
using the published county readme, with the DC exception from the county crosswalk
(`18511` maps to `11001`). The retrieved version contains all 50 states and DC;
actual absent counties and join rates are reported in the cleaning notebook.

## Data preparation

### IRS migration records

Numeric negative suppression values and nonnumeric missing markers in returns
and individuals become null with a flag. AGI is in nominal thousands of dollars;
negative AGI remains valid except the documented `-1` suppression marker.

Row types distinguish domestic county pairs, nonmigrants, domestic totals,
all-migration totals, state summaries, and other/foreign rows. Canonical pair
data use the inflow publication view. County totals use published domestic
aggregates because suppressed/pooled small flows prevent reliable reconstruction.

Exact repeated numeric county-pair records are collapsed in the canonical table;
original rows and a duplicate audit table are retained. Conflicting pair values
cause cleaning to fail. The retrieved 2013–2014 source files contain exact
duplicates in both publication views.

### ACS estimates and historical reconstruction

Negative special values become null with flags. Margins of error (MOEs) remain
alongside estimates. Metadata determine which estimate variables exist; their
associated MOEs are requested even when omitted from the standalone listing.
Derived percentages require positive denominators; education requires all four
degree-count components. Derived percentage MOEs are not propagated.

Missing B23025 (2009–2010) and B15003 (2009–2011) measures are reconstructed from
matching five-year B23001 and B15002 tables, respectively. Employment sums disjoint
employed/unemployed sex-age cells, including ages 65+; education sums male/female
counts. MOEs of sums use the root-sum-of-squares approximation. Reconstruction
flags distinguish historical observations from imputation. Unresolved
education/employment gaps remain missing and fail final validation.

`scripts/download_cleaning_support.py` downloads immutable county and state
B15002/B23001 components with the original five-year window. Using same-vintage
five-year tables preserves the reference period and small-county coverage.
See [Census product guidance](https://www.census.gov/programs-surveys/acs/guidance/estimates.html)
and [the 2009 employment table](https://api.census.gov/data/2009/acs/acs5/groups/B23001.html).

### FEMA event identity and geographic mapping

Event identity follows the publisher's `incidentId` in
[Disaster Declarations Summaries v2](https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2).
County-year tables count distinct underlying incidents, combining declaration
numbers within each analysis geography. `fema_county_events` stores one row per
geography/event with all declaration numbers; the earliest local incident-start
date assigns its year, preventing cross-year double counting. The `declarations`
analysis column retains its name for compatibility and counts distinct incidents.

Missing/invalid incident IDs fall back to declaration numbers with an explicit
method flag. Distinct valid IDs remain separate even when titles or dates resemble
one another. Missing incident starts remain missing at source cleaning;
declaration dates are kept separately. The cleaning notebook documents downstream
date completion and its flags.

Explicit statewide records expand to reference counties; unambiguous tribal names
map through Census 2020 land overlaps. Unresolved areas remain in an audit. In the
panel, absent counts become zero only for completed years covered by the bulk
snapshot. A zero indicates an absence of mapped declarations within that coverage.

### NOAA annual summaries

The precipitation missing marker is `-9.99`; temperature missing markers are
`-99.99` in the old readme and `-99.90` in the retrieved files. These markers become
null. Annual precipitation sums 12 months; annual temperatures use unweighted means
of the 12 monthly means. Incomplete annual values remain null. `tmax_f` and
`tmin_f` describe monthly average maximum/minimum temperatures.

### Socioeconomic imputation

Socioeconomic donor statistics are fitted using 2009–2018 observations. The
inherited temporal split labels 2019–2020 as validation and 2021–2023 as testing.
Base counts are scaled by observed population, imputed counts are bounded by their
universes, and derived rates are recalculated. Outcomes, population, and
education/employment counts are excluded from median imputation. The cleaning
notebook documents date completion, flags, and reference-geography limits.

### Monetary imputation dollar basis

Before fitting monetary donor medians, convert training observations using annual
BLS CPI-U (`CUUR0000SA0`) to the latest ACS year in the panel (currently 2024).
Convert each fill back to its receiving row's dollar year and preserve observed
values exactly. Cleaned exports retain their published-year units; common-dollar
exports are reserved for analysis-specific preparation.

See [the glossary](data-glossary.md#monetary-imputation-dollar-basis) for formulas,
index selection, and provenance. Factors and fitted-statistic units are recorded
in `reports/tables/monetary_imputation_factors.csv` and `socioeconomic_imputer.json`.

## Analysis cohorts and features

### Longitudinal analysis cohort

The [cleaning notebook](../notebooks/data_cleaning.ipynb) exports
one downstream dataset, `analysis_county_year`, with training-only socioeconomic
imputation and flags. It preserves selected identifiers, characteristics, IRS
counts, and migration rates. Final rows must contain complete, finite values and
satisfy explicit range/arithmetic checks. Source audit tables retain missingness
and provenance for review.

The [cleaned-data glossary](data-glossary.md) defines the full rule set, exact
exclusions, retained IQR flags, transformations, and sampling limitations. Rows
with inflow/outflow above 1,000 per 1,000 ACS residents are held out for denominator
review. Year/state retention summaries accompany predictor-imputed results.
Population and education bands and a log10 population column supplement the
original values.

Migration rates divide published IRS individuals by ACS population and multiply
by 1,000. These are approximate descriptive rates because numerator and denominator
populations and reference periods differ. Net migration equals inflow minus outflow.

### 2023 clustering and PCA cohort

Both analyses use the same 3,050 eligible counties in 2023, excluding the Alaska
and Connecticut state substitutions. Six counties inherit predictor imputation;
133 net-rate outlier flags are retained. Source provenance, exclusions, and the
IRS/ACS population mismatch remain as described in the glossary.

Each county receives equal weight. A single year avoids pooling overlapping
county observations and different nominal-dollar years. Source imputation is
inherited from the prepared dataset and remains fixed for both analyses.

### Feature transformations and standardization

The 13 characteristic inputs are log10 population, median age, log10 income,
log10 home value, log10 rent, poverty percentage, unemployment percentage,
vacancy percentage, homeownership percentage, bachelor's-plus percentage,
log1p FEMA incident count, annual precipitation, and annual temperature.
Every transformed feature is standardized using the 2023 cohort's mean and
population standard deviation. Identifiers, year, labels, flags, and outcomes
are excluded from the characteristic matrix.

The separate migration matrix contains standardized inflow/outflow rates. Net
rate is redundant and used only for interpretation.

After `StandardScaler`, sample DataFrames, CSVs, and snapshots remove physical-unit
and percentage suffixes. Z-scores express deviations from the cohort mean in
population standard deviations while preserving the distribution's shape.
Source variables and original-unit outcome summaries retain their definitions.

## Analytical methods

### Exploratory data analysis

EDA describes distributions, coverage, and migration associations using source
audits and the longitudinal analysis cohort. The ten findings charts use the
predictor-imputed analysis table. Comparisons include the latest common year and
a balanced-county time series.

Correlation analysis excludes numeric identifiers and MOE/flag columns. Matrices
use pairwise available data with at least 30 observations and export pair counts.
The ten findings charts use identical observations across correlation cells.
Pearson describes linear association; Spearman describes rank association.
Distribution and coverage diagnostics are described under
[validation](#validation-and-limitations).

### Clustering and PCA

The executed notebooks [Clustering](../notebooks/clustering.ipynb) and
[PCA](../notebooks/pca.ipynb) contain estimator code, diagnostics, rendered
input samples, figures, and measured findings. Both use the [2023 cohort and transformed features](#2023-clustering-and-pca-cohort).
See [reproducibility](#reproducibility) for execution and output locations.

#### Clustering

Clustering describes groups of counties in two views: characteristics and migration.
Both input matrices independently use k-means with a squared Euclidean objective,
20 initializations, seed 42, and k=2 through 8. Full-cohort Euclidean silhouette
selects k; ties favor smaller k.

The hierarchical comparison uses average linkage on cosine distance (1 minus
similarity), with explicit rejection of zero-norm vectors. Cuts at k=2 through 8
are evaluated by cosine silhouette. Compare silhouettes within their respective
metrics. Dendrograms show the last 30 merged nodes.

Diagnostics report cluster sizes, input-space profiles, outcome medians/IQRs,
and every evaluated k. Adjusted Rand index compares methods at their selected k
and at the k-means k. Five alternate seeds (7, 19, 73, 101, 2026), each with 20
initializations, check initialization stability at the selected k.

Characteristic plots use PCA as a display projection; clustering fits the complete
characteristic matrix. Characteristic cluster selection uses input-space criteria;
outcome comparisons support subsequent interpretation.

#### PCA

PCA summarizes variation in the 13 characteristic inputs using full SVD without
whitening. Retain the minimum number of components reaching 80% cumulative feature
variance and report the 90% alternative. Component selection uses feature variance.

Exports include all 13 coefficients per component, eigenvalues, variance ratios,
scores, variable–component correlations, and Spearman associations with each migration rate.
The correlation loading matrix is distinguished from eigenvector coefficients.
Notebook assertions verify orthogonality, the eigenvalue relation, reconstruction,
and the correlation-loading formula.

Score quintiles show medians and IQRs for all three migration rates, using the
same bins for every outcome. Spearman associations cover all 13 components and
all three rates. Score plots retain all counties and saturate colors at the
95th percentile of absolute net rates or the respective inflow/outflow rates.

## Validation and limitations

### Data and implementation checks

Data audits report shapes, types, uniqueness, missingness, zero/negative counts,
finite-value quantiles, skew, and IQR outliers while retaining flagged observations.
They inspect source coverage by year, join match rates by state, ACS relative MOEs,
IRS disclosure flags, paired publication differences, disaster-date anomalies,
and climate completeness. Final cohort eligibility follows the separate rules
in the glossary.

Tests verify invalid-input rejection, unique county grain, excluded outcomes,
selection rules, assignment counts, exported medians, PCA geometry, shared rows,
finite numeric samples, input checksums, and error-free executed notebooks.
Website checks cover required sections, image and download availability, notebook
section anchors, desktop/mobile overflow, navigation, and existing chapter regression.

### Measurement and interpretation

The analyses describe associations and full-cohort patterns. Spatial dependence,
overlapping ACS windows, selective missingness, administrative coverage,
measurement uncertainty, unusual counties, source imputation, and reverse
causality limit interpretation. Inference is descriptive; independence-based
significance tests and causal estimation are outside the design.

Historical ACS reconstruction addresses structural table availability. Early
windows still straddle the 2008 employment/education questionnaire changes, and
native county boundaries require further harmonization. IRS methodology changes
also limit time-series comparability. Missing pairs in sparse migration data have
unknown flow values and must remain distinguishable from observed zeros.

Income, rent, and home values retain each release's published dollar basis.
Pooled correlations can reflect inflation and trends; common-year and within-year
comparisons provide sensitivity checks. Inflation adjustment for donor fitting
preserves published-year units in the final panel.

Annual weather measures describe individual years; long-run climate normals
require a separate construction. FEMA incidents measure mapped declarations and
cover only part of hazard exposure. Correlated housing/economic inputs may give
that domain more influence in the standardized characteristic matrix.

Clustering seed checks assess initialization stability. Sampling, temporal, and
feature-specification stability require additional evaluation. PCA score quintiles
describe bins, and their IQRs describe outcome spread rather than confidence
intervals. Data validation establishes documented rule compliance; publisher
estimates retain their measurement limitations.

### Implications for future prediction

The 2023 rows have been explored despite their inherited supervised `test` labels.
Subsequent prediction work requires a fresh evaluation design before claiming
untouched test performance. Publication-date alignment and temporal/geographic
holdouts must be established for that design.

## Reproducibility

### Implementations and execution

The [workflow](workflow.md) documents environment setup, source acquisition,
cleaning, and audits. Read the notebooks in this order; after cleaning, analytical notebooks execute independently: [Data cleaning](../notebooks/data_cleaning.ipynb),
[Exploration findings](../notebooks/exploration.ipynb),
[Clustering](../notebooks/clustering.ipynb), [PCA](../notebooks/pca.ipynb), [Naive Bayes](../notebooks/naive_bayes.ipynb),
and [Decision trees](../notebooks/decision_trees.ipynb).
Open each notebook in Jupyter, select the project kernel, restart and run all cells,
inspect outputs and save. Shared unsupervised validation and
image-export helpers live in [unsupervised.py](../src/us_migration/unsupervised.py).

For clustering and PCA alone, install `requirements-dev.txt` in the project
environment and first produce `data/processed/analysis_county_year.parquet` with
the data-cleaning notebook. From the repository root, run:

```powershell
.\us-migration\Scripts\python.exe -m jupyterlab
.\us-migration\Scripts\python.exe -m pytest tests/test_unsupervised.py tests/test_website_data.py -q
.\us-migration\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory website
```

Manual execution consumes the existing cleaned dataset. Select the project Python
kernel in Jupyter; both repository-root and notebook working directories are
supported. Edit all notebooks directly and save after execution.

### Outputs and findings

Clustering and PCA write independent canonical bundles under `reports/analyses/`, with numerical evidence, generated figures, and ownership manifests. Website packaging copies each bundle into its topic data and asset directories. Numeric samples include 20 rows; images display five. Separate row keys preserve FIPS leading zeros. Explanatory toy examples remain distinguished from measured findings.

Measured cluster solutions, variance summaries, and migration associations belong
to the executed [clustering](../notebooks/clustering.ipynb) and
[PCA](../notebooks/pca.ipynb) findings and their website chapters. Recompute these
outputs when inputs change. EDA findings are available in the
[summary](../reports/eda_summary.md) and [chart gallery](../reports/eda_visualizations.md).

GitHub code links target `Kaxlow/us-migration`, branch `main`, and notebook headings.
Their availability follows publication of the corresponding files to that branch.

## Supervised classification

Research Framework question 9: **How accurately can county characteristics classify
counties by migration outcome in terms of net migration, inflows, and outflows?**

The Naive Bayes and decision-tree notebooks use the same 3,050 eligible 2023 counties and 13 transformed
characteristics as clustering and PCA. Identifiers, migration measurements/derived categories
and flags stay outside predictors. Six inherited imputations and 133 outlier flags
remain. Standardization is specific to PCA/clustering; classification uses the
log-transformed continuous characteristics, with a learned bin encoder for NB.

Sort counties by FIPS, then split 80/20 using seed 42 before constructing labels:
2,440 training and 610 testing counties. Inflow/outflow targets use separate training-rate
tertiles (linear quantiles): low ≤ first cut, medium > first and ≤ second, high >
second. Fixed cuts define labels throughout training cross-validation and testing.
Net labels use sign; exclude exactly zero from the binary task. The eight balanced
counties all fall in training, leaving 2,432 binary training counties and 610 tests.
`website/data/classification/context.json` records full-precision boundaries and counts.

Five-fold shuffled stratified CV (seed 42) ranks candidates by mean macro-F1.
Learned predictor transformations fit only the current training fold. NB uses five
quantile bins, merged repeated edges, one-hot indicators and MultinomialNB with
learned priors; alpha candidates 0.1/1/10 break exact ties toward larger alpha.
Test values outside training ranges enter extreme bins. This count-vector
approximation loses within-bin detail and retains dependence among indicators.

Each tree target compares depths 2/4/6, minimum leaf sizes 10/25/50 and Gini/entropy,
with equal observation weights and seed 42. Exact ties favor shallower depth,
larger leaves, then Gini. Fit the best configuration at each depth for visualization;
only the selected tree per target receives final test evaluation. Training and
validation macro-F1 with fold standard deviations describe fit and variability.

Test metrics include accuracy, balanced accuracy, macro-F1 and per-class precision,
recall, F1 and support, with count/row-normalized confusion matrices. A majority
classifier fitted on training supplies each task's baseline. Predictions, settings,
metrics, bin boundaries, split membership, tree structures, diagrams and source
provenance are exported by notebook execution. Combined question 9 results compare
target-specific outcomes; this design does not isolate an algorithm effect.

The 2023 cohort was already explored before this split. These scores describe
retrospective held-out classification under a fixed specification, with spatial
dependence, inherited historical imputation, ACS window overlap and IRS/ACS
population mismatch limiting generalization. Tree rules and NB associations are
predictive rather than causal. Future forecasts need publication-date alignment
and fresh temporal/geographic evaluation.

Open either classification notebook in Jupyter, use **Restart Kernel and Run All Cells**, inspect and
save. Both consume the existing Parquet and write independent result bundles. Website export validates and combines those bundles for question 9. The website uses packaged JSON/CSV/figures from canonical result bundles;
fitted pickle files are unnecessary. Changes remain local pending explicit remote
publication authorization.

## Planned supervised analyses

Regression and boosting remain planned. Their future forecasting design will
require publication-date-aware predictors and temporal/geographic evaluation.
Contemporaneous outcomes and derived migration labels remain excluded from
predictors. Their design is separate from completed retrospective classification.

### Three-outcome deliverable contract

The shared outcome definitions supply identifiers, labels, count/rate fields, and
units. Cleaned-data column names retain their existing meanings. Long-form trend,
correlation-ranking, PCA-association, and score-quintile exports include `outcome`.
County exports contain all six measurements; cluster summaries include medians
and quartiles for every rate. Net summaries use individual county net values.

The ten EDA chart groups retain their themes and compare all three rates on shared
rows. Rate rankings retain the population ≥10,000 threshold; count rankings use
the full eligible latest-year county cohort. Trends use a fixed balanced cohort.
Notebook panels show every outcome. Website summaries compare outcomes together,
while detailed charts and maps offer selectors defaulting to net migration.
Map color limits use pooled-year 95th percentiles and remain fixed when the year
changes. Net colors diverge around zero; inflow/outflow colors are sequential.
Exact values remain available in tooltips and downloads.
