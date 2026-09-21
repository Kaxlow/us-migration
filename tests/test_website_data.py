"""Validate published measurements rather than visual implementation details."""
import json
from pathlib import Path
import pytest

DATA = Path(__file__).resolve().parents[1] / 'website/data'

def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))

def test_population_coverage_and_arithmetic():
    data = read('population.json')
    rows = data['counties']
    geometry = {f['id'] for f in read('county.geojson')['features']}
    assert len(rows) == len({r['id'] for r in rows}) == 3144
    assert {r['id'] for r in rows} <= geometry
    for r in rows:
        assert r['change'] == pytest.approx(100*(r['population2025']/r['population2024']-1), abs=0.00001)
    for g in data['groups']:
        selected = [r for r in rows if r['area'] == g['name']]
        for year in (2024, 2025):
            assert sum(r[f'population{year}'] for r in selected) == g[f'population{year}']
        assert g['change'] == pytest.approx(100*(g['population2025']/g['population2024']-1))
    assert sum(g['population2025'] for g in data['groups']) == sum(r['population2025'] for r in rows)

def test_analysis_export():
    d = read('analysis.json')
    assert d['counties'] == len(d['cross']) == 3050
    assert d['rows'] == sum(map(len,d['migration'].values())) == 46026
    assert len(d['captions']) == 10
    for year, values in d['migration'].items():
        rows = [dict(zip(d['migrationFields'],r)) for r in values]
        assert len(rows) == len({r['county_fips'] for r in rows})
        states = {r['county_fips'] for r in rows if r['geography_level']=='state'}
        assert states == {'02000','09000'}
        for r in rows:
            assert r['net_individuals'] == r['inflow_individuals']-r['outflow_individuals']
    assert len(d['correlation']['fields']) == len(d['correlation']['values']) == 16

def test_introduction_has_measured_definition_and_no_placeholders():
    d = read('introduction.json')
    text = ' '.join(d['paragraphs'])
    assert 'domestic inflow minus domestic outflow' in text
    assert 'combined balance of domestic and international' not in text
    assert all(s not in text for s in ('X%', 'Y%', 'Z%'))
    assert len(d['questions']) == 10
