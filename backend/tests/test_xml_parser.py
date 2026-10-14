"""Phase 4: exact spans, semantics, error isolation, safe XML parsing and endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.parsers.xml_parser import XMLInspectionError, inspect_xml_source

client = TestClient(app)


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _additive(node):
    # Physical bytes (not per-element LOC, which can share a source line).
    if node.children:
        assert node.size_bytes == sum(child.size_bytes for child in node.children), node.name
        for child in node.children:
            _additive(child)


def test_sample_views_and_inherited_xpath():
    demo = Path(__file__).parents[2] / 'samples' / 'demo_odoo_module'
    raw = (demo / 'views' / 'calendar_extended.xml').read_bytes()
    result = inspect_xml_source('views/calendar_extended.xml', raw)
    assert result.parse_error is None, result.parse_error
    assert result.element_count > 15
    assert (result.record_count, result.view_count, result.action_count, result.menu_count) == (3, 2, 1, 2)
    assert result.xpath_count == 1
    _additive(result.file)
    assert result.file.size_bytes == len(raw)
    nodes = list(_walk(result.file))
    form = next(n for n in nodes if n.name == 'view_demo_calendar_edition_form_extend')
    assert form.kind == 'view'
    assert form.metadata.target_model == 'demo.calendar.edition'
    assert form.metadata.inherit_ref == 'demo_odoo_module.view_demo_calendar_edition_form'
    assert form.metadata.view_type == 'inherited xpath'
    xp = next(n for n in nodes if n.kind == 'xpath')
    assert xp.metadata.xpath_expr == "//field[@name='year']"
    assert xp.metadata.xpath_position == 'after'
    act = next(n for n in nodes if n.kind == 'action')
    assert act.metadata.action_res_model == 'demo.calendar.edition'
    menu = next(n for n in nodes if n.name == 'menu_demo_calendar_editions')
    assert menu.metadata.menu_parent == 'menu_demo_calendar_root'
    assert menu.metadata.menu_action == 'action_demo_calendar_edition'
    assert xp.line_start is not None and xp.line_end >= xp.line_start


def test_qweb_template_inheritance_and_directives():
    demo = Path(__file__).parents[2] / 'samples' / 'demo_odoo_module'
    data = (demo / 'static/src/components/calendar_widget/calendar_widget_extension.xml').read_bytes()
    analysis = inspect_xml_source('static/src/components/calendar_widget/calendar_widget_extension.xml', data)
    assert analysis.parse_error is None
    assert analysis.template_count == 2
    nodes = list(_walk(analysis.file))
    main = next(node for node in nodes if node.metadata.qweb_name == 'demo.CalendarWidgetExtra')
    inherited = next(node for node in nodes if node.metadata.qweb_inherit == 'demo.CalendarWidget')
    assert main.kind == inherited.kind == 'template'
    assert inherited.metadata.qweb_mode == 'extension'
    assert any(node.metadata.directive_count for node in nodes)
    _additive(analysis.file)


def test_multiline_tags_utf8_crlf_and_same_line_elements():
    raw = ('<?xml version="1.0"?>\r\n<odoo>\r\n'
           ' <menuitem\r\n id="café"\r\n name="A > B"/>\r\n'
           ' <record id="x" model="a.b"><field name="x">ok</field></record>\r\n'
           '</odoo>\r\n').encode('utf-8')
    analysis = inspect_xml_source('test.xml', raw)
    assert analysis.parse_error is None
    nodes = list(_walk(analysis.file))
    menu = next(n for n in nodes if n.kind == 'menu')
    assert menu.name == 'café'
    assert (menu.line_start, menu.line_end) == (3, 5)
    assert analysis.record_count == 1
    _additive(analysis.file)


@pytest.mark.parametrize('data', [
    b'<odoo><record></odoo>',
    b'<!DOCTYPE odoo [<!ENTITY secret SYSTEM "file:///etc/passwd">]><odoo>&secret;</odoo>',
    b'<!DOCTYPE odoo SYSTEM "https://example.com/evil.dtd"><odoo/>',
    b'<odoo> &missing; </odoo>',
])
def test_bad_or_hostile_xml_returns_parse_error_without_execution(data):
    result = inspect_xml_source('bad.xml', data)
    assert result.parse_error
    assert result.file.size_bytes == len(data)
    assert result.file.children == []


def test_file_limit():
    with pytest.raises(XMLInspectionError):
        inspect_xml_source('huge.xml', b' ' * (4 * 1024 * 1024 + 1))


def test_max_depth():
    result = inspect_xml_source('deep.xml', b'<a>' * 130 + b'</a>' * 130)
    assert result.parse_error


def test_api_xml_inspection_and_path_guards(tmp_path):
    demo = client.get('/api/config').json()['demo_module_path']
    rsp = client.post('/api/xml/inspect', json={
        'module_path': demo, 'relative_path': 'views/calendar_extended.xml',
    })
    assert rsp.status_code == 200, rsp.text
    assert rsp.json()['view_count'] == 2
    assert rsp.json()['file']['size_bytes'] > 0
    for invalid in ('../abc.xml', '/etc/passwd.xml', r'views\calendar_extended.xml',
                    'views/no.xml', 'C:/x.xml', 'views/calendar_extended.py'):
        response = client.post('/api/xml/inspect', json={
            'module_path': demo, 'relative_path': invalid,
        })
        assert response.status_code == 400, invalid
    # symlinks are forbidden even if they point into the addon.
    module = tmp_path / 'sample'
    module.mkdir()
    (module / '__manifest__.py').write_text(repr({'name': 'Sample', 'version': '19.0.1.0.0'}))
    (module / 'target.xml').write_text('<odoo/>')
    try:
        (module / 'linked.xml').symlink_to(module / 'target.xml')
    except (NotImplementedError, OSError):
        pass
    else:
        response = client.post('/api/xml/inspect', json={
            'module_path': str(module), 'relative_path': 'linked.xml',
        })
        assert response.status_code == 400


def test_odoo_16_tree_view_and_legacy_qweb():
    source = b'''<odoo><record id="tree_view" model="ir.ui.view"><field name="model">res.partner</field><field name="arch" type="xml"><tree><field name="name"/></tree></field></record><template id="legacy" inherit_id="web.layout"><xpath expr="//main" position="inside"><div>ok</div></xpath></template></odoo>'''
    result = inspect_xml_source('legacy.xml', source)
    assert result.parse_error is None
    nodes = list(_walk(result.file))
    assert next(n for n in nodes if n.kind == 'view').metadata.view_type == 'list'
    assert next(n for n in nodes if n.kind == 'template').metadata.inherit_ref == 'web.layout'
    _additive(result.file)


def test_utf8_bom_and_unsupported_utf16_report_clear_results():
    utf8 = inspect_xml_source('bom.xml', b'\xef\xbb\xbf<odoo><menuitem id="a"/></odoo>')
    assert utf8.parse_error is None
    assert utf8.menu_count == 1
    _additive(utf8.file)
    unsupported = inspect_xml_source('other.xml', '<odoo/>'.encode('utf-16'))
    assert unsupported.parse_error and 'UTF-16' in unsupported.parse_error
    assert unsupported.file.children == []
