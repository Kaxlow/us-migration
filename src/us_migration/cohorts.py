"""Shared county cross-section and feature contract."""
import numpy as np
import pandas as pd

FEATURES = [
    'log10_population', 'median_age', 'log10_income', 'log10_home_value',
    'log10_rent', 'poverty_pct', 'unemployment_pct', 'vacancy_pct',
    'homeownership_pct', 'bachelors_plus_pct', 'log1p_incidents',
    'precipitation_inches', 'temperature_f',
]
LABELS = ['Log population', 'Median age', 'Log income', 'Log home value',
          'Log rent', 'Poverty %', 'Unemployment %', 'Vacancy %',
          'Homeownership %', "Bachelor’s+ %", 'Log1p incidents',
          'Precipitation', 'Temperature']
MIGRATION = ['inflow_individuals_per_1000', 'outflow_individuals_per_1000']
STANDARDIZED_FEATURES = [c.removesuffix('_pct').removesuffix('_inches').removesuffix('_f') for c in FEATURES]
STANDARDIZED_MIGRATION = ['inflow', 'outflow']


def prepare_cross_section(panel, year=2023):
    """One eligible county per row. No new imputation or outcome-driven filtering."""
    counties = panel.loc[panel.year.eq(year) & panel.geography_level.eq('county')].copy()
    counties = counties.sort_values('county_fips').reset_index(drop=True)
    if counties.empty or counties.county_fips.duplicated().any():
        raise ValueError('Expected a nonempty, unique county cross-section')
    for source, target in [('population', 'log10_population'),
                           ('median_household_income', 'log10_income'),
                           ('median_home_value', 'log10_home_value'),
                           ('median_gross_rent', 'log10_rent')]:
        if not (counties[source] > 0).all():
            raise ValueError(f'{source} must be positive before log10')
        counties[target] = np.log10(counties[source])
    if not (counties.declarations >= 0).all():
        raise ValueError('Incident counts must be nonnegative')
    counties['log1p_incidents'] = np.log1p(counties.declarations)
    characteristics = counties[FEATURES].copy()
    migration = counties[MIGRATION].copy()
    for frame in [characteristics, migration]:
        if not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError('Nonfinite model input; rerun the cleaning audit')
        if (frame.std(ddof=0) == 0).any():
            raise ValueError('Constant feature; revise the feature specification')
    if not np.allclose(counties.net_individuals_per_1000,
                       migration.iloc[:, 0] - migration.iloc[:, 1]):
        raise ValueError('Migration arithmetic mismatch')
    return counties, characteristics, migration


