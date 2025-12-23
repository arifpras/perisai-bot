from fastapi.testclient import TestClient
from app_fastapi import app

client = TestClient(app)


def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_query_agg_q1_2023_avg_yield():
    # This tests the aggregation path for Q1 2023 average yield
    payload = {"q": "average yield Q1 2023"}
    r = client.post('/query', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert 'intent' in data and 'result' in data
    assert data['intent']['type'] in ('AGG_RANGE', 'RANGE')
    # If aggregation returned, ensure structure
    if 'value' in data['result']:
        assert 'n' in data['result']
        assert isinstance(data['result']['n'], int)
