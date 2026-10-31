"""Publication respects topic dependencies, provenance, and file ownership."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.exports import (begin_analysis, finish_analysis, publish_files,
                                  read_bundle, export_topics, classification_files)


def seed(root, topic, files):
    publish_files(root/'reports/analyses'/topic, files)


def test_topic_export_preserves_unrelated_artifacts_and_removes_owned_stale_files(tmp_path):
    (tmp_path/'website').mkdir()
    seed(tmp_path,'pca',{'data/example.csv':b'pc,value\n1,0.5\n'})
    target=tmp_path/'website/data/pca'
    publish_files(target,{'obsolete.csv':b'old'})
    (target/'user-note.txt').write_text('keep')
    unrelated=tmp_path/'website/data/clustering/result.csv'
    unrelated.parent.mkdir();unrelated.write_text('unchanged')
    export_topics(tmp_path,['pca'])
    assert (target/'example.csv').read_bytes()==b'pc,value\n1,0.5\n'
    assert not (target/'obsolete.csv').exists()
    assert (target/'user-note.txt').read_text()=='keep'
    assert unrelated.read_text()=='unchanged'
    before={p.relative_to(tmp_path):p.read_bytes() for p in (tmp_path/'website').rglob('*') if p.is_file()}
    export_topics(tmp_path,['pca'])
    assert before=={p.relative_to(tmp_path):p.read_bytes() for p in (tmp_path/'website').rglob('*') if p.is_file()}


def test_invalid_bundle_fails_before_publication(tmp_path):
    seed(tmp_path,'pca',{'data/example.csv':b'original'})
    (tmp_path/'reports/analyses/pca/data/example.csv').write_bytes(b'edited')
    with pytest.raises(ValueError,match='changed artifact'):
        export_topics(tmp_path,['pca'])
    assert not (tmp_path/'website').exists()


def test_manifests_cannot_delete_or_write_outside_owner(tmp_path):
    owner=tmp_path/'owner';owner.mkdir()
    (tmp_path/'keep.txt').write_text('keep')
    (owner/'manifest.json').write_text(json.dumps({'files':{'../keep.txt':'hash'}}))
    with pytest.raises(ValueError,match='escapes'):
        publish_files(owner,{'new.txt':b'new'})
    assert (tmp_path/'keep.txt').read_text()=='keep'
    assert not (owner/'new.txt').exists()


def test_staged_analysis_preserves_previous_bundle_until_finished(tmp_path):
    seed(tmp_path,'pca',{'data/result.csv':b'previous'})
    run=begin_analysis(tmp_path,'pca')
    (run/'data/result.csv').write_bytes(b'recomputed')
    assert read_bundle(tmp_path,'pca')['data/result.csv']==b'previous'
    finish_analysis(tmp_path,'pca',run)
    assert read_bundle(tmp_path,'pca')['data/result.csv']==b'recomputed'


def test_classification_rejects_different_context_and_membership(tmp_path):
    bundles={name:read_bundle(ROOT,'classification/'+name) for name in ['naive-bayes','decision-trees']}
    for name,files in bundles.items():seed(tmp_path,'classification/'+name,files)
    assert 'data/question-9-results.csv' in classification_files(tmp_path)
    altered=copy.deepcopy(bundles['decision-trees'])
    d=json.loads(altered['data/decision-trees.json']);d['context']['seed']+=1
    altered['data/decision-trees.json']=json.dumps(d).encode()
    seed(tmp_path,'classification/decision-trees',altered)
    with pytest.raises(ValueError,match='provenance'):
        export_topics(tmp_path,['classification'])
    assert not (tmp_path/'website').exists()
    altered=copy.deepcopy(bundles['decision-trees']);altered['data/county-profiles.csv']+=b'changed row\n'
    seed(tmp_path,'classification/decision-trees',altered)
    with pytest.raises(ValueError,match='shared artifact'):
        classification_files(tmp_path)


def test_research_question_contract_and_narrative_evidence():
    intro=json.loads((ROOT/'website/data/introduction.json').read_text(encoding='utf-8'))
    assert [q['id'] for q in intro['questions']]==[f'q{i}' for i in range(1,11)]
    assert [q['number'] for q in intro['questions'] if q['status']=='planned']==[3,6,10]
    for q in intro['questions']:
        assert q['text'] and q['gap'] and q['evidence'].startswith('#')
    findings=json.loads((ROOT/'website/data/findings.json').read_text(encoding='utf-8'))
    assert findings['consistentInput']
    for name in ['clustering','pca']:
        result=json.loads((ROOT/f'website/data/{name}/{name}.json').read_text())
        assert findings[name]['conclusions']==result['conclusions']
