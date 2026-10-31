"""Shared cleaning conventions and validation fields."""
from .eda import FEATURES, OUTCOMES


TRAIN_END=2018


VALIDATION_END=2020


SMALL_MISSING_FRACTION=.05


STATE_UNITS={'02':'Alaska','09':'Connecticut'}


MEASURES=FEATURES+['inflow_individuals','outflow_individuals','net_individuals']+OUTCOMES


KEYS=['county_fips','year']


IDENTIFIERS=['county_fips','county_name','year']


POSITIVE=['population','median_household_income','median_home_value','median_gross_rent']


PERCENTAGES=['poverty_pct','unemployment_pct','vacancy_pct','homeownership_pct','bachelors_plus_pct']


US_STATES = set('01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56'.split())


NOAA_STATE_FIPS = dict(zip([f'{i:02}' for i in range(1,51)],
    '01 04 05 06 08 09 10 12 13 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56 15 02'.split()))
