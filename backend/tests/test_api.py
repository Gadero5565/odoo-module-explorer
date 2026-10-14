from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok", "phase": "3"}


def test_demo_analysis():
    config = client.get("/api/config").json()
    path = Path(config["demo_module_path"])
    assert path.exists()
    response = client.post("/api/analyze", json={"module_path": str(path)})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["module"]["version"] == "19"
    assert data["root"]["file_count"] >= 8
    assert any(child["name"] == "models" for child in data["root"]["children"])
    assert data["root"]["size_bytes"] > 0


def test_invalid_module_path_returns_400(tmp_path):
    response = client.post("/api/analyze", json={"module_path": str(tmp_path)})
    assert response.status_code == 400
    assert "manifest" in response.json()["detail"]


def test_rejects_unsupported_override():
    response = client.post("/api/analyze", json={
        "module_path": "/tmp/example", "version_override": "15"
    })
    assert response.status_code == 422


def test_rejects_invalid_host():
    response = client.get("/api/health", headers={"host": "example.com"})
    assert response.status_code == 400


def test_python_inspection_endpoint_returns_nested_classes_and_methods():
    demo = client.get('/api/config').json()['demo_module_path']
    response = client.post('/api/python/inspect', json={
        'module_path': demo, 'relative_path': 'models/calendar_edition.py'
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['file']['kind'] == 'file'
    assert data['file']['relative_path'] == 'models/calendar_edition.py'
    assert data['symbol_count'] >= 2
    assert data['parse_error'] is None


def _make_test_module(tmp_path):
    module = tmp_path / 'test_addon'
    module.mkdir()
    (module / '__init__.py').write_text('', encoding='utf-8')
    (module / '__manifest__.py').write_text(
        repr({'name': 'Test', 'version': '19.0.1.0.0'}), encoding='utf-8'
    )
    return module


def test_python_inspection_path_guards(tmp_path):
    module = _make_test_module(tmp_path)
    (module / 'safe.py').write_text('class Safe: pass\n', encoding='utf-8')
    for rel in ('../outside.py', '/etc/passwd.py', 'C:/windows/test.py',
                'safe.txt', 'sub\\..\\safe.py'):
        res = client.post('/api/python/inspect', json={
            'module_path': str(module), 'relative_path': rel
        })
        assert res.status_code == 400, rel
    linked = module / 'linked.py'
    try:
        linked.symlink_to(module / 'safe.py')
    except (NotImplementedError, OSError):
        pass
    else:
        res = client.post('/api/python/inspect', json={
            'module_path': str(module), 'relative_path': 'linked.py'
        })
        assert res.status_code == 400


def test_python_inspection_handles_bad_syntax(tmp_path):
    module = _make_test_module(tmp_path)
    (module / 'broken.py').write_text('def fail(:\n', encoding='utf-8')
    res = client.post('/api/python/inspect', json={
        'module_path': str(module), 'relative_path': 'broken.py'
    })
    assert res.status_code == 200
    assert 'Syntax error' in res.json()['parse_error']


def test_demo_odoo_inspection_field_metadata_and_routes():
    demo = client.get('/api/config').json()['demo_module_path']
    model = client.post('/api/python/inspect', json={
        'module_path': demo, 'relative_path': 'models/calendar_edition.py',
    })
    assert model.status_code == 200
    payload = model.json()
    assert payload['odoo_model_count'] == 1
    assert payload['odoo_field_count'] == 4
    klass = next(item for item in payload['file']['children'] if item['kind'] == 'class')
    assert klass['odoo_class']['model_name'] == 'demo.calendar.edition'
    assert klass['odoo_class']['field_count'] == 4

    controller = client.post('/api/python/inspect', json={
        'module_path': demo, 'relative_path': 'controllers/preview.py',
    })
    assert controller.status_code == 200
    assert controller.json()['odoo_route_count'] == 1
