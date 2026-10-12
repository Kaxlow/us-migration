"""Numerical contracts for county inputs and the published Phase 2 evidence."""
import hashlib
import json
from pathlib import Path
import sys

import nbformat
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from us_migration.unsupervised import FEATURES, prepare_cross_section

DATA = ROOT / 'website/data'
EXPORT = DATA / 'phase2'


@pytest.fixture
def panel():
    rows = []
    for i in range(3):
        row = dict(county_fips=f'{1001+i:05d}', county_name=f'County {i}', year=2023,
                   geography_level='county', population=1000*(i+1), median_household_income=40000+10000*i,
                   median_home_value=150000+20000*i, median_gross_rent=700+200*i, declarations=i,
                   inflow_individuals_per_1000=10+3*i, outflow_individuals_per_1000=6+i,
                   net_individuals_per_1000=4+2*i)
        for name in ['median_age','poverty_pct','unemployment_pct','vacancy_pct',
                     'homeownership_pct','bachelors_plus_pct','precipitation_inches','temperature_f']:
            row[name] = 20+i
        rows.append(row)
    return pd.DataFrame(rows)


def test_county_input_grain_and_no_outcome_leakage(panel):
    extra = panel.iloc[[0]].assign(geography_level='state', county_fips='02000')
    old = panel.iloc[[0]].assign(year=2022)
    counties, x, migration = prepare_cross_section(pd.concat([panel, extra, old]))
    assert len(counties) == 3
    assert list(x) == FEATURES and x.shape == (3, 13)
    assert migration.shape == (3, 2)
    assert not any('individual' in c or c in ['year','county_fips'] for c in x)
    assert np.allclose(x.log10_population, np.log10(panel.population))
    assert np.allclose(x.log1p_incidents, np.log1p(panel.declarations))


@pytest.mark.parametrize('fault', ['duplicate', 'nonfinite', 'nonpositive', 'arithmetic', 'constant'])
def test_invalid_inputs_fail_instead_of_silent_repair(panel, fault):
    if fault == 'duplicate': panel = pd.concat([panel, panel.iloc[[0]]])
    if fault == 'nonfinite': panel.loc[0, 'median_age'] = np.nan
    if fault == 'nonpositive': panel.loc[0, 'population'] = 0
    if fault == 'arithmetic': panel.loc[0, 'net_individuals_per_1000'] = 99
    if fault == 'constant': panel['temperature_f'] = 50
    with pytest.raises(ValueError): prepare_cross_section(panel)


def test_clustering_selection_and_published_outcomes():
    d = json.loads((DATA/'clustering.json').read_text())
    metrics = pd.read_csv(EXPORT/'clustering-metrics.csv')
    assignments = pd.read_csv(EXPORT/'cluster-assignments.csv', dtype={'county_fips':str})
    assert len(assignments) == assignments.county_fips.nunique() == d['counties']
    assert (assignments.year == d['year']).all()
    assert len(metrics) == 2*2*7
    for view, summary in d['views'].items():
        for method, key in [('kmeans','k'), ('hierarchical','hierarchical_k')]:
            group = metrics.loc[(metrics.view == view) & (metrics.method == method)]
            best = group.sort_values(['silhouette','k'], ascending=[False,True]).iloc[0]
            assert summary[key] == best.k
            assert set(group.k) == set(range(2,9))
            assert group.silhouette.between(-1,1).all()
        for profile in summary['profiles']:
            values = assignments.loc[assignments[view+'_kmeans'] == profile['cluster'], 'net_individuals_per_1000']
            assert len(values) == profile['counties']
            assert values.median() == pytest.approx(profile['net_median'])
            assert values.quantile(.25) == pytest.approx(profile['net_q25'])
        assert sum(summary['hierarchical_sizes']) == len(assignments)
        assert all(-1 <= x <= 1 for x in summary['seed_ari'])
    cross = pd.read_csv(EXPORT/'migration-characteristics-crosstab.csv', index_col=0)
    assert cross.to_numpy().sum() == len(assignments)


def test_pca_geometry_and_shared_cohort():
    d = json.loads((DATA/'pca.json').read_text())
    c = json.loads((DATA/'clustering.json').read_text())
    assert d['input_sha256'] == c['input_sha256']
    assert d['features'] == c['features'] == FEATURES
    scores = pd.read_csv(EXPORT/'pca-county-scores.csv', dtype={'county_fips':str})
    assignments = pd.read_csv(EXPORT/'cluster-assignments.csv', dtype={'county_fips':str})
    assert scores.county_fips.tolist() == assignments.county_fips.tolist()
    assert np.allclose(scores.net_individuals_per_1000, assignments.net_individuals_per_1000)
    coefficients = pd.read_csv(EXPORT/'pca-coefficients.csv', index_col=0).to_numpy()
    assert np.allclose(coefficients.T @ coefficients, np.eye(13), atol=1e-9)
    correlations = pd.read_csv(EXPORT/'pca-variable-correlations.csv', index_col=0).to_numpy()
    assert np.max(np.abs(correlations)) <= 1 + 1e-10
    variance = pd.read_csv(EXPORT/'pca-variance.csv')
    assert variance.variance_ratio.sum() == pytest.approx(1)
    assert (variance.eigenvalue.diff().dropna() <= 0).all()
    assert np.allclose(variance.cumulative, variance.variance_ratio.cumsum())
    assert d['retained'] == np.searchsorted(variance.cumulative, .8) + 1
    assert d['retained90'] == np.searchsorted(variance.cumulative, .9) + 1
    covariance = np.cov(scores[[f'PC{i}' for i in range(1,14)]], rowvar=False)
    assert np.allclose(covariance, np.diag(variance.eigenvalue), atol=1e-9)
    quintiles = pd.read_csv(EXPORT/'pca-score-quintiles.csv')
    assert (quintiles.groupby(['component','outcome']).counties.sum() == d['counties']).all()
    assert (quintiles.q25 <= quintiles['median']).all()
    assert (quintiles['median'] <= quintiles.q75).all()
    a = pd.read_csv(EXPORT/'characteristics-standardized-sample.csv')
    b = pd.read_csv(EXPORT/'pca-standardized-sample.csv')
    pd.testing.assert_frame_equal(a,b)
    assert not any(c.endswith(('_pct', '_inches', '_f', '_per_1000')) for c in a.columns)
    migration_sample = pd.read_csv(EXPORT/'migration-standardized-sample.csv')
    assert list(migration_sample) == ['inflow', 'outflow']
    source = ROOT / d['input']
    if source.exists():
        assert hashlib.sha256(source.read_bytes()).hexdigest() == d['input_sha256']


@pytest.mark.parametrize('name', ['03_clustering','04_pca'])
def test_notebook_is_executed_and_contains_real_estimator_code(name):
    book = nbformat.read(ROOT/f'notebooks/{name}.ipynb', as_version=4)
    nbformat.validate(book)
    cells = [c for c in book.cells if c.cell_type == 'code']
    assert all(c.execution_count is not None for c in cells)
    assert not any(o.output_type == 'error' for c in cells for o in c.outputs)
    assert sum('image/png' in o.get('data',{}) for c in cells for o in c.outputs) >= 7
    code = '\n'.join(c.source for c in cells)
    assert ('KMeans(' if name == '03_clustering' else "PCA(svd_solver='full'") in code
    for cell in cells: compile(cell.source, name, 'exec')


def test_interactive_exports_and_geographic_examples():
    summary = json.loads((DATA/'clustering.json').read_text())
    charts = json.loads((EXPORT/'clustering-charts.json').read_text())
    rows = pd.DataFrame(charts['counties'])
    saved = pd.read_csv(EXPORT/'cluster-assignments.csv', dtype={'county_fips': str})
    assert rows.county_fips.tolist() == saved.county_fips.tolist()
    assert np.allclose(rows.inflow - rows.outflow, rows.net_individuals_per_1000)
    for view in ['characteristics', 'migration']:
        assert rows[view+'_kmeans'].tolist() == saved[view+'_kmeans'].tolist()
        for profile in summary['interpretations'][view]:
            examples = rows.loc[rows.county_name.isin(profile['examples'])]
            assert len(examples) == 3
            assert (examples[view+'_kmeans'] == profile['cluster']).all()
        tree = charts['trees'][view]
        assert len(tree['icoord']) == len(tree['dcoord']) == len(tree['ivl'])-1
        assert np.isfinite(tree['dcoord']).all()
        means = np.array(charts['profiles'][view]['values'])
        weights = rows.groupby(view+'_kmeans').size().to_numpy()
        assert np.allclose(np.average(means, axis=0, weights=weights), 0, atol=1e-10)
