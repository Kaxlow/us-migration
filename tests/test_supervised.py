"""Contracts for retrospective classification and notebook-derived evidence."""
from pathlib import Path
import ast
import json
import sys
import warnings
import hashlib
import nbformat
import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import KBinsDiscretizer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.supervised import (FEATURES, RATE_CLASSES, NET_CLASSES, prepare_classification,
                                    rate_labels, task_rows, metrics, QUESTION)
OUT=ROOT/'website/data/classification'

def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))

@pytest.fixture(scope='module')
def bundle():
    nb,dt=read('naive-bayes.json'),read('decision-trees.json')
    assert nb['context']==dt['context']==read('context.json')
    return nb['context'], {**nb['tasks'],**dt['tasks']}

@pytest.fixture(scope='module')
def panel():
    source=ROOT/'data/processed/analysis_county_year.parquet'
    if not source.exists(): pytest.skip('Local cleaned input is optional for export-only checks')
    return pd.read_parquet(source)

def test_rate_boundaries_and_invalid_cuts():
    assert rate_labels([-1,10,10.01,20,20.01,100],[10,20]).tolist()==['Low','Low','Medium','Medium','High','High']
    for cuts in [[10,10],[20,10],[np.nan,20],[10]]:
        with pytest.raises(ValueError): rate_labels([2],cuts)
    with pytest.raises(ValueError): rate_labels([np.inf],[1,2])

def test_shared_split_and_training_derived_labels(panel,bundle):
    c,x,thresholds=prepare_classification(panel)
    assert c.county_fips.is_unique and len(c)==3050
    assert list(x)==FEATURES and x.shape==(3050,13)
    assert c.classification_split.value_counts().to_dict()=={'train':2440,'test':610}
    assert c.net_class.eq('Balanced').sum()==8
    exported=pd.read_csv(OUT/'county-profiles.csv',dtype={'county_fips':str})
    assert c.county_fips.tolist()==exported.county_fips.tolist()
    assert c.classification_split.tolist()==exported.classification_split.tolist()
    for outcome in ['inflow','outflow','net']:
        a,b,ya,yb=task_rows(c,x,outcome)
        assert set(a.index).isdisjoint(b.index)
        assert len(a)==(2432 if outcome=='net' else 2440) and len(b)==610
        assert set(ya)==set(NET_CLASSES if outcome=='net' else RATE_CLASSES)
    # Perturb held-out outcomes radically; training cuts and membership must stay fixed.
    changed=panel.copy()
    test_keys=set(c.loc[c.classification_split.eq('test'),'county_fips'])
    mask=changed.year.eq(2023)&changed.county_fips.isin(test_keys)
    changed.loc[mask,'inflow_individuals_per_1000']+=500
    changed.loc[mask,'net_individuals_per_1000']=changed.loc[mask,'inflow_individuals_per_1000']-changed.loc[mask,'outflow_individuals_per_1000']
    c2,x2,cuts2=prepare_classification(changed)
    assert thresholds==cuts2==bundle[0]['thresholds']
    pd.testing.assert_frame_equal(x,x2)
    assert c.classification_split.equals(c2.classification_split)

def notebook_nb_pipeline():
    book=nbformat.read(ROOT/'notebooks/naive_bayes.ipynb',as_version=4)
    cell=next(c.source for c in book.cells if c.cell_type=='code' and 'pipeline = Pipeline(' in c.source)
    tree=ast.parse(cell)
    # Instantiate the actual notebook specification without running its workflow.
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.Expr): break
        nodes.append(node)
    from sklearn.model_selection import GridSearchCV
    scope={'GridSearchCV':GridSearchCV,'cv':StratifiedKFold(5,shuffle=True,random_state=42)}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'notebook-pipeline','exec'),scope)
    return scope['pipeline'],scope['search']

def test_nb_preprocessing_fold_isolation_and_extremes(monkeypatch):
    pipeline,search=notebook_nb_pipeline()
    x=pd.DataFrame(np.arange(60*13).reshape(60,13),columns=FEATURES,dtype=float)
    x['log1p_incidents']=np.repeat([0.,1.],30)
    y=np.tile(RATE_CLASSES,20)
    fits=[]
    original=KBinsDiscretizer.fit
    def observed(self, frame, y=None, **kwargs):
        fits.append(set(frame.index))
        return original(self,frame,y,**kwargs)
    monkeypatch.setattr(KBinsDiscretizer,'fit',observed)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        search.fit(x,y)
    folds=list(search.cv.split(x,y))
    assert len(fits)==15
    expected=[set(x.index[a]) for a,b in folds]
    assert all(indices in expected and len(indices)==48 for indices in fits)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        fitted=clone(pipeline).fit(x,y)
    encoder=fitted.named_steps['bins']
    assert encoder.n_bins_[FEATURES.index('log1p_incidents')]<5
    edges=[e.copy() for e in encoder.bin_edges_]
    extreme=pd.DataFrame([[-1e8]*13,[1e8]*13],columns=FEATURES)
    transformed=encoder.transform(extreme).toarray()
    assert np.isfinite(transformed).all() and (transformed>=0).all()
    assert np.all(transformed.sum(axis=1)==13)
    assert all(np.array_equal(a,b) for a,b in zip(edges,encoder.bin_edges_))
    start=0
    for bins in encoder.n_bins_:
        assert transformed[0,start]==1 and transformed[1,start+bins-1]==1
        start+=bins

@pytest.mark.parametrize('outcome',['inflow','outflow','net'])
def test_predictions_metrics_baseline_and_selection(outcome,bundle):
    context,tasks=bundle;t=tasks[outcome]
    rows=pd.read_csv(OUT/f'{outcome}-predictions.csv',dtype={'county_fips':str})
    profiles=pd.read_csv(OUT/'county-profiles.csv',dtype={'county_fips':str}).set_index('county_fips')
    assert len(rows)==rows.county_fips.nunique()==t['test_count']==610
    assert (rows.classification_split=='test').all()
    assert rows.actual.tolist()==profiles.loc[rows.county_fips,outcome+'_class'].tolist()
    assert set(rows.county_fips)==set(profiles.loc[profiles.classification_split.eq('test')].index)
    for key,column in [('model','predicted'),('baseline','baseline')]:
        actual=metrics(rows.actual,rows[column],t['model']['classes'])
        for measure in ['accuracy','balanced_accuracy','macro_f1']:
            assert actual[measure]==pytest.approx(t[key][measure])
        assert actual['confusion']==t[key]['confusion']
        assert np.allclose(actual['confusion_normalized'],t[key]['confusion_normalized'])
        assert np.array(actual['confusion']).sum()==610
    counts=profiles.loc[profiles.classification_split.eq('train'),outcome+'_class'].value_counts().drop('Balanced',errors='ignore')
    assert rows.baseline.nunique()==1 and rows.baseline.iloc[0] in counts[counts==counts.max()].index
    probabilities=rows.filter(like='probability_').to_numpy()
    assert ((probabilities>=0)&(probabilities<=1)).all() and np.allclose(probabilities.sum(axis=1),1)
    tuning=pd.read_csv(OUT/f'{outcome}-tuning.csv')
    if outcome=='inflow':
        expected=tuning.sort_values(['mean_test_score','alpha'],ascending=[False,False]).iloc[0]
        assert len(tuning)==3 and t['selected']['alpha']==expected.alpha
    else:
        expected=tuning.assign(order=tuning.criterion.map({'gini':0,'entropy':1})).sort_values(['mean_test_score','max_depth','min_samples_leaf','order'],ascending=[False,True,False,True]).iloc[0]
        assert len(tuning)==18
        for key in ['criterion','max_depth','min_samples_leaf']: assert t['selected'][key]==expected[key]
    assert t['selected_cv_macro_f1']==pytest.approx(expected.mean_test_score)
    assert t['selected_train_macro_f1']==pytest.approx(expected.mean_train_score)

def test_tree_structure_and_predictions(panel,bundle):
    counties,x,_=prepare_classification(panel)
    for outcome in ['outflow','net']:
        t=bundle[1][outcome]
        assert [tree['depth'] for tree in t['trees']]==[2,4,6]
        for tree in t['trees']:
            nodes=[]
            def check(node,depth=0):
                nodes.append(node)
                assert sum(node['proportions'].values())==pytest.approx(1)
                assert depth<=tree['depth']
                if 'children' in node:
                    assert node['feature'] in FEATURES
                    assert sum(c['samples'] for c in node['children'])==node['samples']
                    for child in node['children']:check(child,depth+1)
                else: assert node['samples']>=tree['params']['min_samples_leaf']
            check(tree['root'])
            assert len(nodes)==tree['node_count']
            assert sum('children' not in node for node in nodes)==tree['leaf_count']
            for suffix in ['svg','png']: assert (ROOT/f"website/assets/classification/{outcome}-tree-{tree['depth']}.{suffix}").stat().st_size>1000
        selected=next(tree for tree in t['trees'] if tree['params']==t['selected'])
        def predict(row,node):
            if 'children' not in node:return node['prediction']
            return predict(row,node['children'][int(np.float32(row[node['feature']])>node['threshold'])])
        xt=task_rows(counties,x,outcome)[1]
        saved=pd.read_csv(OUT/f'{outcome}-predictions.csv')
        assert [predict(row,selected['root']) for _,row in xt.iterrows()]==saved.predicted.tolist()

def test_saved_notebooks_and_assets(bundle):
    for name in ['naive_bayes','decision_trees']:
        book=nbformat.read(ROOT/f'notebooks/{name}.ipynb',as_version=4)
        nbformat.validate(book)
        cells=[c for c in book.cells if c.cell_type=='code']
        assert all(c.execution_count is not None for c in cells)
        assert not any(o.output_type=='error' for c in cells for o in c.outputs)
        assert sum('image/png' in o.get('data',{}) for c in cells for o in c.outputs)>=8
        for cell in cells:compile(cell.source,name,'exec')
    for task in bundle[1].values():
        for sample in task['samples']:
            frame=pd.read_csv(OUT/(sample['name']+'.csv'))
            assert len(frame)==20 and list(frame)==sample['columns']
            for image in sample['images']:assert (ROOT/'website/assets/classification'/image).exists()
    summary=pd.read_csv(OUT/'question-9-results.csv').set_index('outcome')
    for outcome,task in bundle[1].items():
        for metric in ['accuracy','balanced_accuracy','macro_f1']:
            assert summary.loc[outcome,metric]==pytest.approx(task['model'][metric])
    assert json.loads((ROOT/'website/data/introduction.json').read_text(encoding='utf-8'))['questions'][8]['text']==QUESTION

def test_source_provenance_when_available(bundle):
    path=ROOT/bundle[0]['input']
    if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==bundle[0]['input_sha256']

def test_manual_workflow_has_no_runner_entrypoints():
    for name in ['run_notebooks.py','run_phase2.py','clean_data.py']:
        assert not (ROOT/'scripts'/name).exists()
    import us_migration.cleaning as cleaning
    assert not hasattr(cleaning,'main')
    assert 'jupyterlab' in (ROOT/'requirements-dev.txt').read_text()
    for path in [ROOT/'README.md',ROOT/'docs/workflow.md',ROOT/'notebooks/README.md',ROOT/'website/chapters/components.js']:
        assert not any(name in path.read_text(encoding='utf-8') for name in ['run_notebooks.py','run_phase2.py','clean_data.py'])
