"""Analysis eligibility and explicit data-quality checks."""
from datetime import datetime
import numpy as np
import pandas as pd
from .conventions import MEASURES, KEYS, IDENTIFIERS, POSITIVE, PERCENTAGES, US_STATES


def cohort_reasons(panel):
    """Boolean reason flags; separate missingness, invalidity, and analysis restrictions."""
    required = IDENTIFIERS + MEASURES + ['geography_caution']
    missing_columns = set(required) - set(panel)
    if missing_columns:
        raise ValueError('Required panel columns missing: ' + ', '.join(sorted(missing_columns)))
    values = panel[MEASURES].apply(pd.to_numeric, errors='coerce').astype(float)
    flags = pd.DataFrame(index=panel.index)
    flags['missing_required_value'] = panel[required].isna().any(axis=1) | values.isna().any(axis=1)
    text=panel[IDENTIFIERS].select_dtypes(include=['object','string']).astype('string')
    flags['literal_missing_marker']=text.apply(lambda s:s.str.strip().str.lower().isin(['na','n/a','nan','none','null','<na>','missing'])).any(axis=1)
    flags['blank_identifier'] = panel[['county_fips','county_name']].apply(lambda s: s.astype('string').str.strip().eq('').fillna(False)).any(axis=1)
    flags['malformed_fips'] = ~panel.county_fips.astype('string').str.fullmatch(r'\d{5}').fillna(False)
    state_unit=panel.county_fips.isin(['02000','09000']) & panel.get('geography_level',pd.Series('county',index=panel.index)).eq('state')
    flags['outside_us_county_scope'] = ~panel.county_fips.astype('string').str[:2].isin(US_STATES) | (panel.county_fips.astype('string').str[2:].eq('000') & ~state_unit)
    year=pd.to_numeric(panel.year,errors='coerce')
    flags['invalid_year'] = ~np.isfinite(year) | year.lt(2009) | year.gt(datetime.now().year) | year.mod(1).ne(0)
    flags['duplicate_county_year'] = panel.duplicated(KEYS, keep=False)
    flags['nonfinite_numeric'] = np.isinf(values.to_numpy()).any(axis=1)
    flags['nonpositive_denominator_or_median'] = values[POSITIVE].le(0).any(axis=1)
    flags['percentage_outside_0_100'] = (values[PERCENTAGES].lt(0) | values[PERCENTAGES].gt(100)).any(axis=1)
    count_cols = ['population', 'inflow_individuals', 'outflow_individuals', 'declarations']
    flags['invalid_count'] = (values[count_cols].lt(0) | values[count_cols].mod(1).gt(1e-8)).any(axis=1)
    flags['invalid_age_or_climate'] = (values.median_age.le(0) | values.median_age.gt(100)
        | values.temperature_f.lt(-60) | values.temperature_f.gt(130)
        | values.precipitation_inches.lt(0) | values.precipitation_inches.gt(1000))
    flags['inconsistent_net_migration'] = (values.net_individuals - (values.inflow_individuals - values.outflow_individuals)).abs().gt(1e-6)
    rate_error = pd.DataFrame(index=panel.index)
    for stem in ['inflow_individuals','outflow_individuals','net_individuals']:
        expected = 1000 * values[stem] / values.population.where(values.population.gt(0))
        rate_error[stem] = (expected - values[stem+'_per_1000']).abs().gt(1e-6)
    flags['inconsistent_rate'] = rate_error.any(axis=1)
    # This is an explicit analysis restriction, NOT proof the published flow is incorrect.
    flags['rate_denominator_review'] = values[['inflow_individuals_per_1000','outflow_individuals_per_1000']].gt(1000).any(axis=1)
    flags['geography_review'] = panel.geography_caution.fillna(True).astype(bool)
    return flags.fillna(False).astype(bool)


def assert_clean_cohort(clean):
    if clean.empty:
        raise ValueError('No records passed the documented analysis rules')
    assert not clean.isna().any().any(), 'Final analysis table has missing values'
    assert not clean.duplicated(KEYS).any(), 'Duplicate analysis keys'
    assert np.isfinite(clean.select_dtypes(include='number').to_numpy()).all(), 'Nonfinite values'
    assert not clean.select_dtypes(include=['object','string']).apply(lambda x: x.astype('string').str.strip().eq('')).any().any(), 'Blank strings'
    check = clean.assign(geography_caution=False)
    assert not cohort_reasons(check).any().any(), 'Analysis table violates its validation rules'


def build_analysis_cohort(panel):
    """Validate the prepared, imputed panel; record remaining exclusions and add transformations."""
    reasons = cohort_reasons(panel)
    accepted = ~reasons.any(axis=1)
    annotations=[c for c in panel if (c.endswith('_imputed') or c.endswith('_reconstructed')) or c in ['geography_level','data_split','identifier_repaired']]
    clean = panel.loc[accepted, IDENTIFIERS + MEASURES + annotations].copy()
    clean[MEASURES] = clean[MEASURES].astype(float)
    clean['year'] = pd.to_numeric(clean.year).astype(int)
    clean['log10_population'] = np.log10(clean.population)
    clean['education_band'] = pd.cut(clean.bachelors_plus_pct, [-np.inf,20,30,40,np.inf],
        labels=['Under 20%', '20 to <30%', '30 to <40%', '40% or more'], right=False).astype('string')
    clean['population_band'] = pd.cut(clean.population, [0,10000,50000,250000,np.inf],
        labels=['Under 10,000', '10,000 to <50,000', '50,000 to <250,000', '250,000 or more'], right=False).astype('string')
    clean['migration_balance'] = np.select([clean.net_individuals_per_1000.lt(-1),clean.net_individuals_per_1000.gt(1)],
        ['Net loss','Net gain'],default='Near balance')
    # Keep statistical outliers, label them for review, and do not confuse them with errors.
    grouped = clean.groupby('year').net_individuals_per_1000
    q1 = grouped.transform(lambda x: x.quantile(.25))
    q3 = grouped.transform(lambda x: x.quantile(.75))
    clean['net_rate_iqr_flag'] = clean.net_individuals_per_1000.lt(q1-1.5*(q3-q1)) | clean.net_individuals_per_1000.gt(q3+1.5*(q3-q1))
    exclusions = panel.loc[~accepted, IDENTIFIERS].copy()
    exclusions['reason'] = pd.Series(
        ['; '.join(row.index[row]) for _,row in reasons.loc[~accepted].iterrows()],
        index=exclusions.index,dtype='string')
    counts = pd.DataFrame({'rule':reasons.columns,'flagged_rows':reasons.sum().values})
    assert_clean_cohort(clean)
    return clean.reset_index(drop=True), exclusions.reset_index(drop=True), counts, reasons


def quality_scan(frame,keys):
    text=frame.select_dtypes(include=['object','string']).astype('string')
    markers=text.apply(lambda s:s.str.strip().str.lower().isin(['','na','n/a','nan','none','null','<na>','missing']))
    return {'rows':len(frame),'na_nan':int(frame.isna().sum().sum()),
            'blank_or_literal_missing':int(markers.sum().sum()),
            'infinite':int(np.isinf(frame.select_dtypes(include='number')).sum().sum()),
            'duplicate_keys':int(frame.duplicated(keys).sum())}


def assert_complete(frame,keys):
    report=quality_scan(frame,keys)
    assert report['rows']>0
    assert all(value==0 for key,value in report.items() if key!='rows'),report
    return report
