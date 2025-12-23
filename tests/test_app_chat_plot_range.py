from fastapi.testclient import TestClient
from app_fastapi import app

client = TestClient(app)


def test_chat_plot_range_keyword():
    # request a plot by including the word 'plot' in the query (no agg specified)
    r = client.post('/chat', json={'q': 'plot 10 year May 2023'})
    assert r.status_code == 200
    data = r.json()
    assert 'text' in data
    assert 'image_base64' in data
    import base64
    b = base64.b64decode(data['image_base64'])
    assert len(b) > 100
