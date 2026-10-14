"""Statically recognize Odoo Python constructs using AST only.

Never imports addons, executes attributes/calls or resolves the Odoo registry.
Only literal values are interpreted; expressions are shown as text or left unknown.
"""

import ast

from app.schemas.odoo_inspection import (
    OdooClassInfo, OdooFieldInfo, OdooMethodInfo, OdooRouteInfo,
)

ORM_OVERRIDES = {
    'create', 'write', 'unlink', 'read', 'search', 'search_read', 'search_count',
    'copy', 'default_get', 'name_get', 'name_search', 'fields_get',
    '_search', '_read_group', '_name_search', 'read_group', 'web_read',
}
FIELD_TYPES = {
    'Binary', 'Boolean', 'Char', 'Date', 'Datetime', 'Float', 'Html', 'Image',
    'Integer', 'Json', 'Many2many', 'Many2one', 'Many2oneReference', 'Monetary',
    'One2many', 'Properties', 'PropertiesDefinition', 'Reference', 'Selection', 'Text',
}
RELATIONAL = {'Many2one', 'One2many', 'Many2many', 'Many2oneReference'}


def _expr(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)[:180]
    except (ValueError, RecursionError):
        return None


def _literal(node: ast.AST | None):
    """Restrict values to AST literals rather than evaluating source expressions."""
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, MemoryError, RecursionError):
        return None
    return value if isinstance(value, (str, bool, int, float, tuple, list, dict, type(None))) else None


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, str)][:100]
    return []


def _kw(call: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _str(call: ast.Call, name: str) -> str | None:
    value = _literal(_kw(call, name))
    return value if isinstance(value, str) else None


def _bool(call: ast.Call, name: str) -> bool | None:
    value = _literal(_kw(call, name))
    return value if type(value) is bool else None


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _dotted(node.value)
        return f'{left}.{node.attr}' if left else node.attr
    return ''


class OdooAliases:
    """Recognize aliases for the conventional Odoo imports in one Python module."""

    def __init__(self, tree: ast.Module):
        self.models = {'models', 'odoo.models'}
        self.fields = {'fields', 'odoo.fields'}
        self.http = {'http', 'odoo.http'}
        self.controller_classes = {'Controller', 'http.Controller', 'odoo.http.Controller'}
        self.routes = {'route', 'http.route', 'odoo.http.route'}
        self.api = {'api', 'odoo.api'}
        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom):
                if statement.module == 'odoo':
                    for alias in statement.names:
                        if alias.name in ('models', 'fields', 'http', 'api'):
                            getattr(self, alias.name).add(alias.asname or alias.name)
                elif statement.module == 'odoo.http':
                    for alias in statement.names:
                        if alias.name == 'Controller':
                            self.controller_classes.add(alias.asname or alias.name)
                        if alias.name == 'route':
                            self.routes.add(alias.asname or alias.name)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    if alias.name == 'odoo':
                        self.models.add((alias.asname or 'odoo') + '.models')
                        self.fields.add((alias.asname or 'odoo') + '.fields')
                        self.http.add((alias.asname or 'odoo') + '.http')

    def field_type(self, func: ast.AST) -> str | None:
        name = _dotted(func)
        prefix, _, field_type = name.rpartition('.')
        if prefix in self.fields and field_type in FIELD_TYPES:
            return field_type
        return None

    def class_type(self, node: ast.ClassDef) -> str | None:
        bases = {_dotted(base) for base in node.bases}
        for name, category in [('TransientModel', 'transient'), ('AbstractModel', 'abstract'),
                               ('Model', 'model')]:
            if any(base == f'{prefix}.{name}' for base in bases for prefix in self.models):
                return category
        if bases & self.controller_classes or any(base == f'{prefix}.Controller' for base in bases for prefix in self.http):
            return 'controller'
        return None

    def is_route(self, decorator: ast.AST) -> bool:
        call = decorator if isinstance(decorator, ast.Call) else None
        return _dotted(call.func if call else decorator) in self.routes

    def api_decorator(self, decorator: ast.AST) -> str | None:
        func = decorator.func if isinstance(decorator, ast.Call) else decorator
        dotted = _dotted(func)
        prefix, _, action = dotted.rpartition('.')
        return action if prefix in self.api else None


def _assignments(node: ast.ClassDef) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}
    for stmt in node.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            result[stmt.targets[0].id] = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.value:
            result[stmt.target.id] = stmt.value
    return result


def describe_class(node: ast.ClassDef, aliases: OdooAliases) -> OdooClassInfo | None:
    category = aliases.class_type(node)
    if category is None:
        return None  # Do not guess inheritance through arbitrary Python base classes.
    items = _assignments(node)
    if category == 'controller':
        return OdooClassInfo(category='controller')
    name = _literal(items.get('_name'))
    inherit = _literal(items.get('_inherit'))
    delegates = _literal(items.get('_inherits'))
    description = _literal(items.get('_description'))
    return OdooClassInfo(
        category=category,
        model_name=name if isinstance(name, str) else None,
        inherits=_strings(inherit),
        delegates={k: v for k, v in delegates.items() if isinstance(k, str) and isinstance(v, str)}
        if isinstance(delegates, dict) else {},
        description=description if isinstance(description, str) else None,
    )


def describe_field(stmt: ast.stmt, aliases: OdooAliases) -> tuple[str, OdooFieldInfo] | None:
    """Return a field only for a direct, simple class-level declaration."""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        field_name, expr = stmt.targets[0].id, stmt.value
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        field_name, expr = stmt.target.id, stmt.value
    else:
        return None
    if not isinstance(expr, ast.Call):
        return None
    field_type = aliases.field_type(expr.func)
    if field_type is None:
        return None
    relation_arg = expr.args[0] if expr.args else _kw(expr, 'comodel_name')
    relation = _literal(relation_arg) if field_type in RELATIONAL else None
    label = _str(expr, 'string')
    # Char('Label') / Many2one('related.model', string='Label') conventions
    if label is None and field_type not in RELATIONAL and expr.args:
        first = _literal(expr.args[0])
        if isinstance(first, str):
            label = first
    related = _literal(_kw(expr, 'related'))
    return field_name, OdooFieldInfo(
        field_type=field_type,
        relation=relation if isinstance(relation, str) else None,
        string=label,
        compute=_str(expr, 'compute'), inverse=_str(expr, 'inverse'),
        search=_str(expr, 'search'),
        related=related if isinstance(related, str) else None,
        required=_bool(expr, 'required'), readonly=_bool(expr, 'readonly'),
        store=_bool(expr, 'store'),
        default=_expr(_kw(expr, 'default')),
        comodel_expression=_expr(relation_arg) if field_type in RELATIONAL else None,
    )


def _route_info(decorator: ast.AST) -> OdooRouteInfo:
    if not isinstance(decorator, ast.Call):
        return OdooRouteInfo()
    first = decorator.args[0] if decorator.args else _kw(decorator, 'route')
    paths = _strings(_literal(first))
    methods = _strings(_literal(_kw(decorator, 'methods')))
    return OdooRouteInfo(
        paths=paths, methods=methods, auth=_str(decorator, 'auth'),
        route_type=_str(decorator, 'type'), csrf=_bool(decorator, 'csrf'),
    )


def describe_method(node: ast.FunctionDef | ast.AsyncFunctionDef, aliases: OdooAliases) -> OdooMethodInfo:
    api = [name for d in node.decorator_list if (name := aliases.api_decorator(d))]
    routes = [_route_info(d) for d in node.decorator_list if aliases.is_route(d)]
    decorated_values: dict[str, list[str]] = {}
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        action = aliases.api_decorator(decorator)
        if action in ('depends', 'depends_context', 'onchange', 'constrains'):
            decorated_values.setdefault(action, []).extend(
                x for arg in decorator.args for x in _strings(_literal(arg))
            )
    name = node.name
    if routes:
        role = 'controller_route'
    elif name in ORM_OVERRIDES:
        role = 'orm_override'
    elif name.startswith('_compute_') or any(d in api for d in ('depends', 'depends_context')):
        role = 'compute'
    elif name.startswith('_inverse_'):
        role = 'inverse'
    elif name.startswith('_search_'):
        role = 'search'
    elif 'constrains' in api or name.startswith('_check_'):
        role = 'constraint'
    elif 'onchange' in api or name.startswith('_onchange_'):
        role = 'onchange'
    elif name.startswith('_cron_'):
        role = 'cron'
    elif name.startswith('action_') or name.startswith('button_'):
        role = 'business_action'
    elif name.startswith('_default_'):
        role = 'default'
    else:
        role = 'other'
    return OdooMethodInfo(
        role=role, api_decorators=api,
        depends=decorated_values.get('depends', []) + decorated_values.get('depends_context', []),
        onchange_fields=decorated_values.get('onchange', []),
        constraint_fields=decorated_values.get('constrains', []),
        routes=routes,
    )
