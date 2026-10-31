# Ten findings from cleaned analysis data

## 1. 01_population_distribution

![Chart](../reports/analyses/exploration/figures/01_population_distribution.png)

The median county population is 26,767, while the largest county has 9,848,406 residents in this sample. A logarithmic axis reveals smaller counties that a few very large counties would compress on a linear scale.

## 2. 02_home_value_distribution

![Chart](../reports/analyses/exploration/figures/02_home_value_distribution.png)

The median of county home-value estimates is $174,600, compared with a mean of $211,434. The upper tail motivates comparing ranks and inspecting extreme counties rather than automatically deleting high home values.

## 3. 03_net_migration_over_time

![Chart](../reports/analyses/exploration/figures/03_net_migration_over_time.png)

All three panels use the same 3,007 counties in every year; lines show county medians and shading shows the middle 50%. Equal-county summaries describe the fixed sample; IRS methodology changes limit comparisons over time.

## 4. 04_inflow_vs_outflow

![Chart](../reports/analyses/exploration/figures/04_inflow_vs_outflow.png)

County inflow and outflow rates have a Spearman correlation of 0.80, illustrating substantial two-way movement. Counties above the diagonal gain IRS individuals on net, with matching logarithmic axes fitted to the observed range to spread out the points (symmetric logarithmic axes if zeros occur).

## 5. 05_county_gains_and_losses

![Chart](../reports/analyses/exploration/figures/05_county_gains_and_losses.png)

Largest net gains and losses and highest inflow/outflow rates in 2023, among counties with population at least 10,000. Supporting count rankings use the full eligible county cohort and include population and corresponding rates.

## 6. 06_homeownership_and_migration

![Chart](../reports/analyses/exploration/figures/06_homeownership_and_migration.png)

Net migration, inflow, and outflow use the same 3,050 counties in 2023. Panels describe outcome distributions and associations; shared characteristics, source coverage, and timing limit causal interpretation.

## 7. 07_education_bands

![Chart](../reports/analyses/exploration/figures/07_education_bands.png)

Net migration, inflow, and outflow use the same 3,050 counties in 2023. Panels describe outcome distributions and associations; shared characteristics, source coverage, and timing limit causal interpretation.

## 8. 08_temperature_and_migration

![Chart](../reports/analyses/exploration/figures/08_temperature_and_migration.png)

Net migration, inflow, and outflow use the same 3,050 counties in 2023. Panels describe outcome distributions and associations; shared characteristics, source coverage, and timing limit causal interpretation.

## 9. 09_disasters_and_migration

![Chart](../reports/analyses/exploration/figures/09_disasters_and_migration.png)

Net migration, inflow, and outflow use the same 3,050 counties in 2023. Panels describe outcome distributions and associations; shared characteristics, source coverage, and timing limit causal interpretation.

## 10. 10_correlation_matrix

![Chart](../reports/analyses/exploration/figures/10_correlation_matrix.png)

All cells use the same 3,050 counties. Strongest absolute associations: Net migration: Homeownership % (rho 0.290); Inflow: Home value (rho 0.442); Outflow: Gross rent (rho 0.420). Correlated characteristics and different relationships across outcomes motivate multivariable analysis.
