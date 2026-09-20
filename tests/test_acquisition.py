import sys
from pathlib import Path
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from us_migration import acquisition


def test_snapshot_is_immutable_and_cached_and_url_redacted(tmp_path,monkeypatch):
    monkeypatch.setattr(acquisition,'ROOT',tmp_path)
    monkeypatch.setattr(acquisition,'RAW',tmp_path/'raw')
    monkeypatch.setenv('CENSUS_API_KEY','unit-test-secret')
    class Response:
        content=b'[["value"],["1"]]'
        headers={'Content-Type':'application/json'}
        def raise_for_status(self): pass
    client=acquisition.SnapshotClient()
    calls=[]
    def get(*args,**kwargs):
        calls.append(1)
        return Response()
    monkeypatch.setattr(client.session,'get',get)
    first=client.fetch('acs/2020/counties','https://api.census.gov/data/2020/acs/acs5',params={'key':'unit-test-secret'},kind='json')
    assert first.read_bytes()==Response.content
    assert 'unit-test-secret' not in client.catalog_path.read_text()
    assert client.fetch('acs/2020/counties','https://api.census.gov/data/2020/acs/acs5',kind='json')==first
    assert len(calls)==1
    client.refresh=True
    Response.content=b'[["value"],["2"]]'
    second=client.fetch('acs/2020/counties','https://api.census.gov/data/2020/acs/acs5',kind='json')
    assert second!=first
    assert first.read_bytes()==b'[["value"],["1"]]'


def test_server_echoing_secret_is_not_saved(tmp_path,monkeypatch):
    monkeypatch.setattr(acquisition,'ROOT',tmp_path)
    monkeypatch.setattr(acquisition,'RAW',tmp_path/'raw')
    monkeypatch.setenv('CENSUS_API_KEY','unit-test-secret')
    class Response:
        content=b'"unit-test-secret"'
        headers={}
        def raise_for_status(self): pass
    client=acquisition.SnapshotClient()
    monkeypatch.setattr(client.session,'get',lambda *a,**kw:Response())
    assert client.fetch('test','https://api.census.gov/data',kind='json') is None
    assert not client.catalog
