"""Phase 7 module-wide index: search provenance, graph edges, safety, and bounds."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import insights as service

client = TestClient(app)


def _addon(tmp_path: Path) -> Path:
    module = tmp_path / 'insights_addon'
    module.mkdir()
    (module / '__manifest__.py').write_text(repr({'name': 'Index', 'version': '19.0.1.0.0'}))
    (module / '__init__.py').write_text('')
    return module


def test_demo_index_contains_real_symbols_models_and_links():
    demo = client.get('/api/config').json()['demo_module_path']
    response = client.post('/api/insights', json={'module_path': demo})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['inspected_files'] >= 10
    assert data['skipped_files'] == 0
    assert data['truncated'] is False
    assert all(item['relative_path'] and item['id'] for item in data['symbols'])
    edition = next(m for m in data['models'] if m['name'] == 'demo.calendar.edition')
    assert edition['defined_here'] is True
    assert len(edition['fields']) == 4
    assert edition['views']
    assert any(f['name'] == 'day_ids' for f in edition['fields'])
    assert any(link['source'] == 'demo.calendar.edition' and link['target'] == 'demo.calendar.day'
               and link['local_target'] for link in data['relationships'])
    assert any(item['kind'] == 'registration' for item in data['symbols'])
    assert any(item['kind'] == 'selector' for item in data['symbols'])
    assert any(item['kind'] == 'template' for item in data['symbols'])
    assert any(item['name'] == '_compute_day_count' and item['complexity'] is not None
               for item in data['symbols'])


def test_inherited_extension_fields_external_and_internal_models(tmp_path):
    addon = _addon(tmp_path)
    (addon / 'models.py').write_text('''from odoo import models, fields, api
class Item(models.Model):
    _name = 'addon.item'
    name = fields.Char()
    company_id = fields.Many2one('res.company')
    parent_id = fields.Many2one('addon.item')
    @api.depends('name')
    def _compute_label(self):
        for rec in self:
            if rec.name and len(rec.name) > 2:
                rec.label = rec.name
class ItemExtension(models.Model):
    _inherit = 'addon.item'
    extra = fields.Boolean()
class EmployeeExtension(models.Model):
    _inherit = 'hr.employee'
    item_id = fields.Many2one('addon.item')
''')
    data = service.build_insights(addon)
    models = {m.name: m for m in data.models}
    assert models['addon.item'].defined_here is True
    assert len(models['addon.item'].source_classes) == 2
    assert len(models['addon.item'].fields) == 4
    assert models['hr.employee'].defined_here is False
    assert models['res.company'].defined_here is False
    assert any(not link.local_target and link.target == 'res.company' for link in data.relationships)
    assert any(link.local_target and link.source == 'hr.employee' for link in data.relationships)
    method = next(symbol for symbol in data.symbols if symbol.name == '_compute_label')
    assert method.owner_model == 'addon.item'
    assert method.complexity >= 3


def test_source_is_not_executed_and_broken_files_are_reported(tmp_path):
    addon = _addon(tmp_path)
    marker = tmp_path / 'executed.txt'
    (addon / 'models.py').write_text(f'''open({str(marker)!r}, 'w').write('executed')
from odoo import models
class Sample(models.Model):
    _name = 'addon.safe'
''')
    (addon / 'bad.py').write_text('def broken(:\n')
    data = service.build_insights(addon)
    assert not marker.exists()
    assert any(model.name == 'addon.safe' for model in data.models)
    assert any('bad.py' in note for note in data.warnings)


def test_skip_links_and_index_limits(monkeypatch, tmp_path):
    addon = _addon(tmp_path)
    (addon / 'one.py').write_text('class First: pass\n')
    (addon / 'two.py').write_text('class Second: pass\n')
    try:
        (addon / 'linked.py').symlink_to(addon / 'two.py')
    except (OSError, NotImplementedError):
        pass
    monkeypatch.setattr(service, 'MAX_FILES', 1)
    data = service.build_insights(addon)
    assert data.inspected_files == 1
    assert data.truncated
    assert data.skipped_files >= 1
    assert not any(symbol.relative_path == 'linked.py' for symbol in data.symbols)


def test_endpoint_rejects_non_addon_and_invalid_version(tmp_path):
    assert client.post('/api/insights', json={'module_path': str(tmp_path)}).status_code == 400
    assert client.post('/api/insights', json={
        'module_path': str(tmp_path), 'version_override': '15'
    }).status_code == 422


def test_complexity_nested_functions_not_double_counted():
    source = b'''def outer(x):
    if x:
        return x
    def nested():
        if x:
            return x
        return 0
    return nested()
'''
    scores = service._function_complexities(source)
    assert scores[('outer', 1)] == 2
    assert scores[('nested', 4)] == 2
