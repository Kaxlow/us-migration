"""Independently verify published three-outcome summaries against their rows."""
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from us_migration.outcomes import OUTCOME_DEFINITIONS, RATE_FIELDS, COUNT_FIELDS
DATA=ROOT/'website/data'
PHASE=DATA/'phase2'


def test_shared_contract_and_all_map_rates():
    d=json.loads((DATA/'analysis.json').read_text())
    assert d['outcomes']==OUTCOME_DEFINITIONS==json.loads((DATA/'outcomes.json').read_text())
    all_rows=pd.DataFrame([dict(zip(d['migrationFields'],r)) for rows in d['migration'].values() for r in rows])
    assert np.isfinite(all_rows[COUNT_FIELDS+RATE_FIELDS]).all().all()
    assert np.allclose(all_rows.net_individuals,all_rows.inflow_individuals-all_rows.outflow_individuals)
    assert np.allclose(all_rows.net_individuals_per_1000,all_rows.inflow_individuals_per_1000-all_rows.outflow_individuals_per_1000,atol=.00011)
    for o in OUTCOME_DEFINITIONS:
        assert np.allclose(all_rows[o['rate']],1000*all_rows[o['count']]/all_rows.population,atol=.000051)
        values=all_rows[o['rate']].abs() if o['id']=='net' else all_rows[o['rate']]
        assert d['colorLimits'][o['id']]==pytest.approx(values.quantile(.95),abs=.0001)


def test_cluster_summaries_for_each_outcome():
    rows=pd.read_csv(PHASE/'cluster-assignments.csv')
    d=json.loads((DATA/'clustering.json').read_text())
    for view,summary in d['views'].items():
        for p in summary['profiles']:
            group=rows.loc[rows[view+'_kmeans'].eq(p['cluster'])]
            for o in OUTCOME_DEFINITIONS:
                for suffix,q in [('median',.5),('q25',.25),('q75',.75)]:
                    assert p[o['id']+'_'+suffix]==pytest.approx(group[o['rate']].quantile(q))


def test_pca_associations_and_identical_score_bins():
    rows=pd.read_csv(PHASE/'pca-county-scores.csv')
    associations=pd.read_csv(PHASE/'pca-migration-associations.csv')
    quintiles=pd.read_csv(PHASE/'pca-score-quintiles.csv')
    assert len(associations)==39
    assert not associations.duplicated(['component','outcome']).any()
    for o in OUTCOME_DEFINITIONS:
        for a in associations.loc[associations.outcome.eq(o['id'])].itertuples():
            # Rank correlation through pandas, independently of notebook scipy call.
            expected=rows[a.component].rank().corr(rows[o['rate']].rank())
            assert a.spearman_rho==pytest.approx(expected)
        for pc,group in quintiles.loc[quintiles.outcome.eq(o['id'])].groupby('component'):
            bands=pd.qcut(rows[pc],5,labels=False)+1
            for q in group.itertuples():
                values=rows.loc[bands.eq(q.quintile),o['rate']]
                assert q.counties==len(values)
                assert [q.q25,q.median,q.q75]==pytest.approx(values.quantile([.25,.5,.75]).tolist())


def test_rankings_and_trends_use_shared_rows():
    d=json.loads((DATA/'analysis.json').read_text())
    rows=pd.read_csv(DATA/'latest-counties.csv',dtype={'county_fips':str})
    for o in OUTCOME_DEFINITIONS:
        for kind,field,cohort in [('rateRankings',o['rate'],rows.loc[rows.population.ge(10000)]),('countRankings',o['count'],rows)]:
            selected=[r for r in d[kind] if r['outcome']==o['id']]
            for direction in ['highest']+(['lowest'] if o['id']=='net' else []):
                actual={r['county_fips'] for r in selected if r['ranking']==direction}
                expected=cohort.nlargest(10,field) if direction=='highest' else cohort.nsmallest(10,field)
                assert actual==set(expected.county_fips)
    source=ROOT/'data/processed/analysis_county_year.parquet'
    if source.exists():
        panel=pd.read_parquet(source).query("geography_level == 'county'")
        balanced=panel.groupby('county_fips').year.nunique().loc[lambda s:s.eq(panel.year.nunique())].index
        panel=panel.loc[panel.county_fips.isin(balanced)]
        trend=pd.DataFrame(d['trend'])
        for o in OUTCOME_DEFINITIONS:
            for row in trend.loc[trend.outcome.eq(o['id'])].itertuples():
                values=panel.loc[panel.year.eq(row.year),o['rate']]
                assert [row.q25,row.median,row.q75]==pytest.approx(values.quantile([.25,.5,.75]).tolist())
