"""The website publishes the reviewed notebook prose without changing evidence."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.exports import notebook_conclusions


@pytest.mark.parametrize('name,topic', [
    ('clustering', 'clustering'), ('pca', 'pca'),
    ('naive_bayes', 'classification'), ('decision_trees', 'classification')])
def test_published_conclusions_match_authored_markdown(name, topic):
    sections = notebook_conclusions(ROOT, name)
    bundle = json.loads((ROOT/'website/data'/topic/(name.replace('_', '-')+'.json')).read_text(encoding='utf-8'))
    if 'tasks' in bundle:
        for outcome, section in zip(['inflow'] if name == 'naive_bayes' else ['outflow', 'net'], sections):
            assert bundle['tasks'][outcome]['conclusions'] == section['paragraphs']
    else:
        assert bundle['conclusion_sections'] == sections
        assert bundle['conclusions'] == [p for s in sections for p in s['paragraphs']]
    cells = json.loads((ROOT/'notebooks'/f'{name}.ipynb').read_text(encoding='utf-8'))['cells']
    index = next(i for i, c in enumerate(cells) if c['cell_type'] == 'markdown' and '## Conclusions' in ''.join(c['source']))
    assert all(c['cell_type'] == 'markdown' for c in cells[index:])
    export_cell = cells[index-1]
    assert ''.join(export_cell['source']).strip() == f"export_analysis('{name}', globals())"
    assert export_cell['metadata']['jupyter']['source_hidden'] is True
    assert 'remove-input' in export_cell['metadata']['tags']
    assert export_cell['outputs'] == []


def test_incomplete_analysis_keeps_previous_bundle(tmp_path):
    from us_migration.analysis_exports import export_analysis

    prior = tmp_path/'reports/analyses/classification/naive-bayes/data/naive-bayes.json'
    prior.parent.mkdir(parents=True)
    prior.write_text('previous completed result')
    with pytest.raises(ValueError, match='Run the notebook analysis cells'):
        export_analysis('naive_bayes', {'ROOT': tmp_path, 'BUNDLE': tmp_path/'staging'})
    assert prior.read_text() == 'previous completed result'
    assert not (tmp_path/'staging').exists()
