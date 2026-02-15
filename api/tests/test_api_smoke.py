import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def test_generate_preset_smoke():
    client = TestClient(app)
    project = client.post('/projects', json={}).json()
    pid = project['id']
    for step in range(1, 7):
        res = client.post(f'/projects/{pid}/generate/step/{step}')
        assert res.status_code == 200
    latest = client.get(f'/projects/{pid}/artifacts/latest')
    assert latest.status_code == 200
