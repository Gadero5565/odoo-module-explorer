"""JavaScript/OWL grammar tests; require Node + frontend TypeScript package."""

from pathlib import Path

import pytest

from app.parsers.js_parser import JSInspectionError, inspect_js_source

SAMPLE = b'''/** @odoo-module */
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
export class TestCard extends Component {
  static template = "test.Card";
  setup() { this.state = useState({ count: 0 }); }
  async show(value) { function localFn() { return value; } return localFn(); }
}
registry.category("actions").add("test.card", TestCard);
'''


def _analyze(source: bytes = SAMPLE):
    return inspect_js_source('static/src/test.js', source)


def _find(root, name):
    return next(node for node in root.children if node.name == name)


def _check_partition(node):
    if node.children:
        assert node.size_bytes == sum(ch.size_bytes for ch in node.children), node.id
        for child in node.children:
            _check_partition(child)


def test_owl_component_imports_template_hooks_registration():
    result = _analyze()
    assert result.parse_error is None
    assert result.component_count == 1
    assert result.registration_count == 1
    assert {i.source for i in result.imports} == {'@odoo/owl', '@web/core/registry'}
    klass = _find(result.file, 'TestCard')
    assert klass.metadata['is_owl_component'] is True
    assert klass.metadata['template'] == 'test.Card'
    assert 'useState' in klass.metadata['hooks']
    assert _find(klass, 'show').metadata['async'] is True
    assert _find(_find(klass, 'show'), 'localFn').kind == 'function'
    assert result.registrations[0].key == 'test.card'
    _check_partition(result.file)


def test_service_dependencies_and_arrow_methods():
    src = b'''import { registry } from '@web/core/registry';\nconst testService = {
 dependencies: ['orm','rpc'],
 start(env) { const getX = async (x) => x + 1; return { getX }; },
};
registry.category('services').add('test.service',testService);
'''
    result = _analyze(src)
    assert result.service_count == 1
    service = _find(result.file, 'testService')
    assert service.metadata['dependencies'] == ['orm', 'rpc']
    assert _find(service, 'start').kind == 'method'
    assert _find(_find(service, 'start'), 'getX').kind == 'function'
    _check_partition(result.file)


def test_unicode_utf8_bom_and_physical_byte_totals():
    src = '\ufeffexport function greet() { return "مرحبا 😀"; }\n'.encode('utf-8')
    result = _analyze(src)
    assert result.file.size_bytes == len(src)
    _check_partition(result.file)
    assert _find(result.file, 'greet').line_start == 1


def test_legacy_odoo_module_and_syntax_error_recovery():
    result = _analyze(b"odoo.define('legacy.Sample', function(require) {return {};});\n")
    assert _find(result.file, 'legacy.Sample').kind == 'module'
    broken = _analyze(b'class Broken { foo( {\n')
    assert broken.parse_error and 'syntax error' in broken.parse_error.lower()
    assert broken.file.size_bytes == len(b'class Broken { foo( {\n')


def test_does_not_evaluate_addon_source(tmp_path):
    target = tmp_path / 'should_not_exist'
    source = f'import fs from "fs"; fs.writeFileSync({str(target)!r}, "bad");\n'.encode()
    _analyze(source)
    assert not target.exists()


def test_oversized_source_rejected():
    with pytest.raises(JSInspectionError, match='3 MiB'):
        _analyze(b' ' * (3 * 1024 * 1024 + 1))


def test_real_sample_component():
    root = Path(__file__).resolve().parents[2] / 'samples/demo_odoo_module'
    file = root / 'static/src/components/calendar_widget/calendar_widget.js'
    parsed = inspect_js_source('static/src/components/calendar_widget/calendar_widget.js', file.read_bytes())
    assert parsed.component_count == 1
    assert parsed.registration_count == 1
    _check_partition(parsed.file)


def test_aliased_owl_import_registry_and_legacy_nested_definitions():
    src = b'''import { Component as OwlComponent } from '@odoo/owl';
import { registry as actionRegistry } from '@web/core/registry';
class Alias extends OwlComponent { static template = 'x.Alias'; }
actionRegistry.category('actions').add('x.alias', Alias);
'''
    result = _analyze(src)
    assert result.component_count == 1
    assert result.registrations[0].key == 'x.alias'
    assert _find(result.file, 'Alias').metadata['template'] == 'x.Alias'
    _check_partition(result.file)

    legacy = _analyze(b"odoo.define('legacy.Code', function (require) { class Inner { run() {} } return Inner; });")
    block = _find(legacy.file, 'legacy.Code')
    assert _find(block, 'Inner').kind == 'class'
    _check_partition(legacy.file)
