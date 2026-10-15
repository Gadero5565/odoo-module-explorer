"""Phase 11: profiles, vendor safety, performance bounds, semantic indexing and refresh."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.analysis_policy import is_vendor_path
from app.core.scanner import DirectoryScanner
from app.main import app

client = TestClient(app)


def addon(tmp_path: Path) -> Path:
    root = tmp_path / 'big_odoo_addon'
    root.mkdir()
    (root / '__init__.py').write_text('')
    (root / '__manifest__.py').write_text("{'version': '19.0.1.0.0'}")
    for folder in ('models', 'static/lib/pdfmake', 'static/src/lib/canvg',
                   'static/description', 'description', 'lib', 'static/src/js'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / 'models' / 'invoice.py').write_text("class Invoice: pass\n")
    (root / 'lib' / 'helpers.py').write_text("class MyAddonUtils: pass\n")
    (root / 'static/src/js' / 'widget.js').write_text('function addonWidget() {}\n')
    (root / 'static/src/js' / 'bundle.min.js').write_bytes(b'f()'*30000)
    (root / 'static/src/js' / 'bundle.min.js.map').write_bytes(b'{'*90000)
    (root / 'static/lib/pdfmake' / 'pdfmake.min.js').write_bytes(b'f()'*200000)
    (root / 'static/lib/pdfmake' / 'pdfmake.min.js.map').write_bytes(b'{'*200000)
    (root / 'static/src/lib/canvg' / 'canvg.js').write_text('function libraryInternal() {}\n')
    (root / 'static/description' / 'icon.png').write_bytes(b'PNG'*10000)
    (root / 'description' / 'index.html').write_text('<h1>description</h1>')
    return root


def flatten(node):
    yield node
    for child in node['children']:
        yield from flatten(child)


def test_precise_vendor_policy_keeps_authored_lib_and_app_files():
    assert is_vendor_path('static/lib/pdfmake', directory=True)
    assert is_vendor_path('static/src/lib/canvg', directory=True)
    assert is_vendor_path('static/description', directory=True)
    assert is_vendor_path('description', directory=True)
    assert is_vendor_path('STATIC/LIB/MyVendor/CORE.JS', directory=False)
    assert is_vendor_path('static/src/js/pdfmake.min.js.map')
    assert is_vendor_path('static/src/js/bundle.min.js')
    assert is_vendor_path('static/src/js/bundle.min.css')
    assert not is_vendor_path('lib', directory=True)
    assert not is_vendor_path('lib/helpers.py')
    assert not is_vendor_path('static/src/js/widget.js')
    assert not is_vendor_path('static/src/js/lib/helper.js')


def test_source_profile_skips_bundles_before_scanning(tmp_path):
    root = addon(tmp_path)
    seen = []

    def counted(path, stat):
        seen.append(str(path.relative_to(root)).replace('\\', '/'))
        return 1

    scanner = DirectoryScanner(root, line_counter=counted)
    tree = scanner.scan()
    files = {node['relative_path'] for node in flatten(tree.model_dump()) if node['kind'] == 'file'}
    assert 'models/invoice.py' in files
    assert 'lib/helpers.py' in files
    assert 'static/src/js/widget.js' in files
    assert 'static/src/js/bundle.min.js' not in files
    assert 'static/lib/pdfmake/pdfmake.min.js' not in files
    assert 'static/src/lib/canvg/canvg.js' not in files
    assert 'static/description/icon.png' not in files
    assert 'description/index.html' not in files
    assert not any('/lib/pdfmake/' in path for path in seen)
    assert all('.min.js' not in path for path in seen)
    assert scanner.excluded_entries >= 5
    assert tree.size_bytes < 100_000


def test_all_files_restores_physical_totals(tmp_path):
    root = addon(tmp_path)
    source = client.post('/api/analyze', json={'module_path': str(root)}).json()
    full = client.post('/api/analyze', json={
        'module_path': str(root), 'analysis_profile': 'all_files'}).json()
    assert source['analysis_profile'] == 'odoo_source'
    assert full['analysis_profile'] == 'all_files'
    assert full['excluded_entries'] == 0
    assert source['excluded_entries'] >= 5
    assert full['revision'] != source['revision']
    assert full['root']['size_bytes'] > source['root']['size_bytes']
    assert full['root']['file_count'] > source['root']['file_count']
    expected_size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    assert full['root']['size_bytes'] == expected_size
    full_paths = {n['relative_path'] for n in flatten(full['root'])}
    assert 'static/lib/pdfmake/pdfmake.min.js' in full_paths
    assert 'static/src/lib/canvg/canvg.js' in full_paths
    assert 'static/description/icon.png' in full_paths


def test_all_files_insights_still_skips_vendor_parsing(tmp_path):
    root = addon(tmp_path)
    for profile in ('odoo_source', 'all_files'):
        response = client.post('/api/insights', json={
            'module_path': str(root), 'analysis_profile': profile})
        assert response.status_code == 200, response.text
        index = response.json()
        names = {s['name'] for s in index['symbols']}
        assert 'addonWidget' in names
        assert 'Invoice' in names
        assert 'MyAddonUtils' in names
        assert 'libraryInternal' not in names
        assert not any('pdfmake' in s['relative_path'] for s in index['symbols'])
        assert not index['truncated']


def test_refresh_ignores_vendor_changes_in_source_mode(tmp_path):
    root = addon(tmp_path)
    source = client.post('/api/analyze', json={'module_path': str(root)}).json()
    full = client.post('/api/analyze', json={'module_path': str(root),
                                             'analysis_profile': 'all_files'}).json()
    vendor = root / 'static/lib/pdfmake/pdfmake.min.js'
    vendor.write_bytes(vendor.read_bytes() + b'f(2)')
    unchanged = client.post('/api/refresh', json={'module_path': str(root),
        'analysis_profile': 'odoo_source', 'previous_revision': source['revision']}).json()
    changed = client.post('/api/refresh', json={'module_path': str(root),
        'analysis_profile': 'all_files', 'previous_revision': full['revision']}).json()
    assert unchanged['changed'] is False
    assert changed['changed'] is True
    assert 'static/lib/pdfmake/pdfmake.min.js' in changed['changed_paths']
    assert changed['analysis']['analysis_profile'] == 'all_files'
    original = root / 'models/invoice.py'
    original.write_text('class Invoice:\n    pass\n')
    source_update = client.post('/api/refresh', json={'module_path': str(root),
        'analysis_profile': 'odoo_source', 'previous_revision': source['revision']}).json()
    assert source_update['changed'] is True
    assert 'models/invoice.py' in source_update['changed_paths']
    assert not any('pdfmake' in p for p in source_update['changed_paths'])


def test_invalid_profile_rejected(tmp_path):
    root = addon(tmp_path)
    for route in ('analyze', 'refresh', 'insights'):
        response = client.post('/api/' + route, json={
            'module_path': str(root), 'analysis_profile': 'invalid'})
        assert response.status_code == 422
