"""Phase 9 launch tests (no browser/network process started by tests)."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import cli
from app.main import app


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(['--version'])
    assert exc.value.code == 0
    assert '0.1.0' in capsys.readouterr().out


@pytest.mark.parametrize('invalid', ['0', '80', '65536', 'not-a-port'])
def test_rejects_invalid_port(invalid):
    with pytest.raises(SystemExit) as exc:
        cli.main(['--port', invalid])
    assert exc.value.code == 2


def test_requires_built_ui(monkeypatch, capsys):
    monkeypatch.setattr(cli, 'frontend_directory', lambda: None)
    with pytest.raises(SystemExit) as exc:
        cli.main(['--no-browser'])
    assert exc.value.code == 2
    assert 'Web UI not built' in capsys.readouterr().err


def test_launcher_passes_optional_addon_path_and_loopback(monkeypatch, tmp_path):
    addon = tmp_path / 'addon'
    addon.mkdir()
    (addon / '__manifest__.py').write_text("{'name': 'Demo', 'version': '19.0.1.0.0'}")
    (addon / '__init__.py').write_text('')
    monkeypatch.setattr(cli, 'frontend_directory', lambda: tmp_path)
    calls = []
    monkeypatch.setattr(cli.uvicorn, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(cli.shutil, 'which', lambda binary: '/usr/bin/node')
    assert cli.main(['--no-browser', '--port', '17764', str(addon)]) == 0
    assert calls[0][1]['host'] == '127.0.0.1'
    assert calls[0][1]['port'] == 17764
    with TestClient(app) as client:
        cfg = client.get('/api/config').json()
    assert Path(cfg['initial_module_path']) == addon.resolve()
    assert cfg['supported_versions'] == ['16', '17', '18', '19']


def test_optional_module_rejects_invalid_path(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, 'frontend_directory', lambda: tmp_path)
    with pytest.raises(SystemExit) as exc:
        cli.main(['--no-browser', str(tmp_path)])
    assert exc.value.code == 2
