"""Odoo 16–19 static semantics and physical-size accounting regression tests."""

from app.parsers.python_parser import inspect_python_source


def parse(source: str):
    result = inspect_python_source('models/demo.py', source.encode('utf-8'))
    assert result.parse_error is None
    return result


def children(node, kind: str):
    return [item for item in node.children if item.kind == kind]


def additive(node):
    if node.children:
        assert sum(c.size_bytes for c in node.children) == node.size_bytes, node.name
        assert sum(c.line_count for c in node.children) == node.line_count, node.name
    for child in node.children:
        additive(child)


def test_models_fields_methods_and_decorators():
    result = parse('''from odoo import api, fields, models
class Calendar(models.Model):
    _name = 'isc.calendar'
    _description = 'A Calendar'
    name = fields.Char(string='Title', required=True, default=lambda self: 'New')
    region_id = fields.Many2one('isc.region', ondelete='cascade')
    days = fields.One2many('isc.day', 'calendar_id')
    count = fields.Integer(compute='_compute_count', store=True)

    @api.depends('days')
    def _compute_count(self):
        return 1

    @api.constrains('name')
    def _check_name(self):
        pass

    @api.onchange('region_id')
    def _onchange_region(self):
        pass

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def action_confirm(self):
        pass
''')
    assert (result.odoo_model_count, result.odoo_field_count, result.odoo_route_count) == (1, 4, 0)
    klass = children(result.file, 'class')[0]
    meta = klass.odoo_class
    assert (meta.category, meta.model_name, meta.description) == ('model', 'isc.calendar', 'A Calendar')
    assert (meta.field_count, meta.method_count) == (4, 5)
    fields = {item.name: item.odoo_field for item in children(klass, 'odoo_field')}
    assert fields['name'].required is True
    assert 'lambda self' in fields['name'].default
    assert fields['region_id'].relation == 'isc.region'
    assert fields['days'].relation == 'isc.day'
    assert fields['count'].compute == '_compute_count'
    assert fields['count'].store is True
    methods = {item.name: item.odoo_method for item in children(klass, 'method')}
    assert methods['_compute_count'].role == 'compute'
    assert methods['_compute_count'].depends == ['days']
    assert methods['_check_name'].constraint_fields == ['name']
    assert methods['_onchange_region'].onchange_fields == ['region_id']
    assert methods['create'].role == 'orm_override'
    assert methods['create'].api_decorators == ['model_create_multi']
    assert methods['action_confirm'].role == 'business_action'
    additive(result.file)


def test_odoo_inheritance_abstract_transient_and_delegation():
    result = parse('''from odoo import models, fields
class Extension(models.Model):
    _inherit = ['hr.employee', 'mail.thread']
    related = fields.Many2one('res.partner')
class Wizard(models.TransientModel):
    _name = 'my.wizard'
class Base(models.AbstractModel):
    _name = 'my.abstract'
    _inherits = {'res.partner': 'partner_id'}
''')
    classes = {c.name: c.odoo_class for c in children(result.file, 'class')}
    assert classes['Extension'].model_name is None
    assert classes['Extension'].inherits == ['hr.employee', 'mail.thread']
    assert classes['Wizard'].category == 'transient'
    assert classes['Base'].category == 'abstract'
    assert classes['Base'].delegates == {'res.partner': 'partner_id'}
    assert result.odoo_model_count == 3
    additive(result.file)


def test_controller_routes_and_multiple_route_decorators():
    result = parse('''from odoo import http
class Controller(http.Controller):
    @http.route(['/x', '/y'], auth='user', type='json', methods=['POST'], csrf=False)
    def post(self):
        pass

    @http.route('/a', auth='public')
    @http.route('/b', auth='none')
    def get(self):
        pass
''')
    klass = children(result.file, 'class')[0]
    assert klass.odoo_class.category == 'controller'
    methods = {x.name: x.odoo_method for x in children(klass, 'method')}
    assert result.odoo_route_count == 3
    assert methods['post'].role == 'controller_route'
    assert methods['post'].routes[0].paths == ['/x', '/y']
    assert methods['post'].routes[0].auth == 'user'
    assert methods['post'].routes[0].methods == ['POST']
    assert methods['post'].routes[0].csrf is False
    additive(result.file)


def test_import_aliases_and_dynamic_values():
    result = parse('''from odoo import models as om, fields as f, api as a
class Aliased(om.Model):
    _name = 'my.aliased'
    company_id = f.Many2one(get_target(), string='Company', required=unknown_value)
    @a.depends('company_id')
    def _compute_company(self):
        pass
''')
    klass = children(result.file, 'class')[0]
    assert klass.odoo_class.model_name == 'my.aliased'
    field = children(klass, 'odoo_field')[0].odoo_field
    assert field.field_type == 'Many2one'
    assert field.relation is None
    assert field.comodel_expression == 'get_target()'
    assert field.required is None
    assert children(klass, 'method')[0].odoo_method.depends == ['company_id']
    additive(result.file)


def test_plain_python_classes_not_mistaken_for_odoo():
    result = parse('''class PurePython:
    _name = 'foo'
    name = fields.Char()
    def action_run(self):
        pass
''')
    klass = children(result.file, 'class')[0]
    assert klass.odoo_class is None
    assert not children(klass, 'odoo_field')
    assert children(klass, 'method')[0].odoo_method is None
    assert result.odoo_model_count == 0
    additive(result.file)


def test_static_parser_does_not_execute_code(tmp_path):
    marker = tmp_path / 'should_not_exist'
    result = parse(f'''from odoo import models, fields
class Unsafe(models.Model):
    _name = 'unsafe'
    dangerous = fields.Char(default=__import__('pathlib').Path({str(marker)!r}).touch())
''')
    assert not marker.exists()
    assert result.odoo_field_count == 1
    additive(result.file)


def test_complex_statements_are_not_double_counted():
    result = parse('''from odoo import models, fields
class Test(models.Model):
    _name = 'test.model'
    a = fields.Char(
        string='Multiline',
        compute='_compute_a',
    )
    b: str = fields.Char()
    ignored, other = fields.Char(), fields.Integer()
    def _compute_a(self):
        pass
''')
    klass = children(result.file, 'class')[0]
    assert {x.name for x in children(klass, 'odoo_field')} == {'a', 'b'}
    additive(result.file)
