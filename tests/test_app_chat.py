from fastapi.testclient import TestClient
from app_fastapi import app

client = TestClient(app)


def test_chat_point():
    r = client.post('/chat', json={'q': 'yield 2023-05-02 10 year'})
    assert r.status_code == 200
    data = r.json()
    assert 'text' in data
    assert 'rows' in data and isinstance(data['rows'], list)
    assert any(r.get('tenor') == '10_year' for r in data['rows'])


def test_chat_plot_agg():
    # request agg + plot
    r = client.post('/chat', json={'q': 'average yield 2023', 'plot': True})
    assert r.status_code == 200
    data = r.json()
    assert 'text' in data
    # for plot=True we expect an image_base64
    assert 'image_base64' in data
    assert isinstance(data['image_base64'], str)
    # basic sanity: base64 decodes to non-empty bytes
    import base64
    b = base64.b64decode(data['image_base64'])
    assert len(b) > 100