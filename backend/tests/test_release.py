"""Release content/fallback tests that do not require npm or a real wheel build."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app, frontend_directory


def test_source_checkout_serves_frontend_if_built(monkeypatch, tmp_path):
    from app import main as module
    built = tmp_path / 'compiled'
    built.mkdir()
    (built / 'index.html').write_text('<h1>Built</h1>')
    monkeypatch.setattr(module, 'BUNDLED_WEB', tmp_path / 'not-present')
    monkeypatch.setattr(module, 'DEVELOPMENT_WEB', built)
    assert frontend_directory() == built
    monkeypatch.setattr(module, 'BUNDLED_WEB', built)
    assert frontend_directory() == built


def test_config_falls_back_to_bundled_demo(monkeypatch, tmp_path):
    # No need to create a wheel to test this path behavior.
    monkeypatch.setattr(routes, 'PROJECT_ROOT', tmp_path)
    with TestClient(app) as client:
        cfg = client.get('/api/config').json()
    # In source checkouts before release building the bundle does not exist.
    assert cfg['demo_module_path'] == '' or Path(cfg['demo_module_path']).is_dir()


def test_packager_checks_prebuilt_asset_completeness(tmp_path):
    import importlib.util
    script = Path(__file__).resolve().parents[2] / 'scripts' / 'build_release.py'
    spec = importlib.util.spec_from_file_location('release_builder', script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    frontend = tmp_path / 'frontend'
    pkg = tmp_path / 'app'
    demo = tmp_path / 'sample'
    demo.mkdir()
    (demo / '__manifest__.py').write_text("{'name': 'Demo'}")
    (frontend / 'dist' / 'assets').mkdir(parents=True)
    (frontend / 'dist' / 'index.html').write_text('<html></html>')
    (frontend / 'dist' / 'favicon.svg').write_text('<svg/>')
    (frontend / 'dist' / 'favicon.ico').write_bytes(b'icon fixture')
    (frontend / 'dist' / 'assets' / 'main.js').write_text('console.log(1)')
    lib = frontend / 'node_modules' / 'typescript'
    (lib / 'lib').mkdir(parents=True)
    (lib / 'lib' / 'typescript.js').write_text('// fixture grammar')
    (lib / 'LICENSE.txt').write_text('Fixture license')
    (demo / 'models').mkdir()
    (demo / 'models' / 'model.py').write_text('pass\n')
    web, vendor = builder.prepare_release_assets(frontend, pkg, demo)
    assert (web / 'assets' / 'main.js').exists()
    assert (web / 'favicon.svg').exists()
    assert (web / 'favicon.ico').exists()
    assert (vendor / 'typescript.js').exists()
    assert (pkg / 'demo_addon' / 'models' / 'model.py').exists()
    # A second build must not leave stale static files from the previous build.
    (web / 'stale.js').write_text('stale')
    builder.prepare_release_assets(frontend, pkg, demo)
    assert not (web / 'stale.js').exists()


def test_release_builder_resolves_windows_npm_cmd(monkeypatch):
    """Windows must launch npm.cmd rather than the Unix npm shell shim."""
    import importlib.util
    script = Path(__file__).resolve().parents[2] / 'scripts' / 'build_release.py'
    spec = importlib.util.spec_from_file_location('release_builder', script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    requested = []

    def which(name):
        requested.append(name)
        return 'C:/Program Files/nodejs/npm.cmd' if name == 'npm.cmd' else '/usr/bin/npm'

    monkeypatch.setattr(builder.shutil, 'which', which)
    assert builder._npm_executable(windows=True) == 'C:/Program Files/nodejs/npm.cmd'
    assert builder._npm_executable(windows=False) == '/usr/bin/npm'
    assert requested == ['npm.cmd', 'npm']


def test_release_builder_missing_windows_npm(monkeypatch):
    import importlib.util
    script = Path(__file__).resolve().parents[2] / 'scripts' / 'build_release.py'
    spec = importlib.util.spec_from_file_location('release_builder', script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    monkeypatch.setattr(builder.shutil, 'which', lambda name: None)
    assert builder._npm_executable(windows=True) is None


def test_license_distribution_metadata():
    root = Path(__file__).resolve().parents[2]
    metadata = (root / 'backend' / 'pyproject.toml').read_text(encoding='utf-8')
    assert 'license = "LGPL-3.0-only"' in metadata
    for path in ('LICENSE', 'LICENSES/GPL-3.0-only.txt',
                 'backend/LICENSE', 'backend/LICENSES/GPL-3.0-only.txt'):
        assert (root / path).is_file(), path


def test_frontend_favicon_assets_are_valid_and_declared():
    root = Path(__file__).resolve().parents[2] / 'frontend'
    html = (root / 'index.html').read_text(encoding='utf-8')
    assert 'href="/favicon.svg"' in html
    assert 'href="/favicon.ico"' in html
    assert (root / 'public' / 'favicon.svg').read_text(encoding='utf-8').startswith('<svg')
    ico = (root / 'public' / 'favicon.ico').read_bytes()
    assert len(ico) > 500
    assert ico[:4] == b'\x00\x00\x01\x00'
