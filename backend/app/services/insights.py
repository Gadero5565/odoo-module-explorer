"""Bounded module-wide static search and logical Odoo model index.

This index only records literal / syntactic relationships within ONE addon.
It does not load modules, execute expressions, or claim to represent the
fully merged database registry. Each result points to a genuine source node.
"""

import ast
import io
import tokenize
from pathlib import Path

from app.core.analysis_policy import is_vendor_path
from app.core.scanner import DirectoryScanner
from app.parsers.js_parser import MAX_JS_BYTES, JSInspectionError, inspect_js_source
from app.parsers.python_parser import MAX_PYTHON_BYTES, inspect_python_source
from app.parsers.style_parser import MAX_STYLE_BYTES, inspect_style_source
from app.parsers.xml_parser import MAX_XML_BYTES, inspect_xml_source
from app.schemas.insights import InsightsResponse, InsightSymbol, ModelLink, OdooModelSummary

MAX_FILES = 500
MAX_BYTES = 24 * 1024 * 1024
MAX_SYMBOLS = 15_000
MAX_WARNINGS = 35
ALLOWED_EXTENSIONS = {'.py', '.xml', '.js', '.scss', '.css'}
INDEX_KINDS = {
    'class', 'method', 'async_method', 'function', 'async_function', 'odoo_field',
    'view', 'action', 'menu', 'record', 'template', 'xpath',
    'service', 'registration', 'selector', 'mixin', 'variable',
}


def _walk(nodes):
    for child in nodes:
        yield child
        yield from _walk(child.children)


def _odoo_name(node) -> tuple[str | None, bool]:
    info = node.odoo_class
    if not info or info.category == 'controller':
        return None, False
    if info.model_name:
        return info.model_name, True
    # _inherit without _name extends a model rather than defining a new one.
    if len(info.inherits) == 1:
        return info.inherits[0], False
    return None, False


def _function_complexities(data: bytes) -> dict[tuple[str, int], int]:
    """A simple, explicitly approximate cyclomatic score (baseline 1)."""
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        tree = ast.parse(data.decode(encoding))
    except (SyntaxError, UnicodeError, LookupError):
        return {}
    result: dict[tuple[str, int], int] = {}

    def score(func):
        decisions = 1

        def visit(node):
            nonlocal decisions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                return
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp,
                                 ast.ExceptHandler, ast.Assert, ast.Match)):
                decisions += 1
            if isinstance(node, ast.BoolOp):
                decisions += max(0, len(node.values) - 1)
            if isinstance(node, ast.comprehension):
                decisions += len(node.ifs) + 1
            for child in ast.iter_child_nodes(node):
                visit(child)
        for statement in func.body:
            visit(statement)
        return decisions

    for func in ast.walk(tree):
        if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([func.lineno, *(d.lineno for d in func.decorator_list)])
            result[(func.name, start)] = score(func)
    return result


def build_insights(root: Path, tree=None, parse_cache=None, scan_warnings=None) -> InsightsResponse:
    response = InsightsResponse()
    model_map: dict[str, OdooModelSummary] = {}
    symbol_ids: set[str] = set()
    files_seen = 0
    attempted_files = 0
    bytes_seen = 0

    def warn(value: str) -> None:
        if len(response.warnings) < MAX_WARNINGS:
            response.warnings.append(value[:350])

    def get_model(name: str) -> OdooModelSummary:
        if name not in model_map:
            model_map[name] = OdooModelSummary(name=name)
        return model_map[name]

    complexities: dict[tuple[str, int], int] = {}

    def add(node, kind: str | None = None, owner: str | None = None, detail: str | None = None):
        if node.id in symbol_ids:
            return next((symbol for symbol in response.symbols if symbol.id == node.id), None)
        if len(response.symbols) >= MAX_SYMBOLS:
            response.truncated = True
            return None
        symbol = InsightSymbol(
            id=node.id, name=node.name, kind=kind or node.kind,
            relative_path=node.relative_path, line_start=node.line_start,
            line_end=node.line_end, size_bytes=node.size_bytes,
            line_count=node.line_count, owner_model=owner, detail=detail,
            complexity=(complexities.get((node.name, node.line_start))
                        if node.kind in ("function", "async_function", "method", "async_method")
                        else None),
        )
        response.symbols.append(symbol)
        symbol_ids.add(node.id)
        return symbol

    scanner = DirectoryScanner(root) if tree is None else None
    tree = scanner.scan() if scanner is not None else tree
    for warning in (scanner.warnings if scanner is not None else (scan_warnings or [])):
        warn(f'{warning.relative_path}: {warning.reason}')
    paths = sorted((node for node in _walk([tree]) if node.kind == 'file'
                    and node.extension in ALLOWED_EXTENSIONS
                    and not is_vendor_path(node.relative_path)), key=lambda n: n.relative_path)

    for file in paths:
        if attempted_files >= MAX_FILES or bytes_seen + file.size_bytes > MAX_BYTES:
            response.truncated = True
            response.skipped_files += 1
            continue
        limit = {'.py': MAX_PYTHON_BYTES, '.xml': MAX_XML_BYTES, '.js': MAX_JS_BYTES,
                 '.scss': MAX_STYLE_BYTES, '.css': MAX_STYLE_BYTES}[file.extension]
        if file.size_bytes > limit:
            response.skipped_files += 1
            warn(f'{file.relative_path}: skipped, exceeds parser size limit')
            continue
        # DirectoryScanner skips symlink entries. Defend again against replacements
        # between scanning and indexing (best-effort local filesystem safety).
        path = root
        segments = file.relative_path.split('/')
        if any(segment in ('.', '..', '') for segment in segments):
            response.skipped_files += 1
            continue
        if any((path := path / segment).is_symlink() for segment in segments):
            response.skipped_files += 1
            warn(f'{file.relative_path}: skipped symbolic link')
            continue
        attempted_files += 1
        try:
            # Stat every file again to defend against replacements after scanning.
            live_size = path.stat().st_size
            if live_size > limit or bytes_seen + live_size > MAX_BYTES:
                response.skipped_files += 1
                continue
            if not path.resolve().is_relative_to(root):
                response.skipped_files += 1
                continue
            bytes_seen += live_size
            parser = ({'.py': inspect_python_source, '.xml': inspect_xml_source,
                       '.js': inspect_js_source}.get(file.extension) or inspect_style_source)
            if parse_cache is not None:
                inspection, cached_complexities = parse_cache.inspect(
                    path, file.extension, parser, file.relative_path,
                    _function_complexities if file.extension == '.py' else None,
                    max_bytes=limit,
                )
            else:
                data = path.read_bytes()
                if len(data) > limit:
                    response.skipped_files += 1
                    continue
                inspection = parser(file.relative_path, data)
                cached_complexities = _function_complexities(data) if file.extension == '.py' else None
        except (OSError, ValueError, JSInspectionError) as exc:
            response.skipped_files += 1
            warn(f'{file.relative_path}: {str(exc)[:180]}')
            continue
        files_seen += 1
        if inspection.parse_error:
            warn(f'{file.relative_path}: {inspection.parse_error}')
            continue
        if file.extension == '.py':
            complexities = cached_complexities or {}
            # The tree is a physical source tree. Class/field/ORM associations are
            # attached via explicit AST semantics, not filename heuristics.
            def visit_python(node, owner: str | None = None):
                name, defined_here = _odoo_name(node)
                current = name or owner
                model = get_model(name) if name else None
                if model is not None:
                    model.defined_here = model.defined_here or defined_here
                    info = node.odoo_class
                    for inherited in info.inherits:
                        if inherited != name and inherited not in model.inherits:
                            model.inherits.append(inherited)
                    for delegated in info.delegates:
                        if delegated not in model.delegates:
                            model.delegates.append(delegated)
                kind = node.kind
                symbol = (add(node, owner=current, detail=('Odoo model' if model else None))
                          if kind in INDEX_KINDS else None)
                if model and symbol:
                    model.source_classes.append(symbol)
                if owner and symbol and kind in ('method', 'async_method', 'odoo_field'):
                    target = get_model(owner)
                    (target.fields if kind == 'odoo_field' else target.methods).append(symbol)
                    if kind == 'odoo_field' and node.odoo_field and node.odoo_field.relation:
                        relation = node.odoo_field.relation
                        if isinstance(relation, str):
                            target.relations.append(ModelLink(
                                source=owner, target=relation, label=node.name,
                                relation_type=node.odoo_field.field_type,
                                relative_path=node.relative_path, line_start=node.line_start,
                            ))
                for child in node.children:
                    visit_python(child, current)
            for item in inspection.file.children:
                visit_python(item)
        elif file.extension == '.xml':
            for node in _walk(inspection.file.children):
                if node.kind not in INDEX_KINDS:
                    continue
                meta = node.metadata
                owner = (meta.target_model if node.kind == 'view'
                         else meta.action_res_model if node.kind == 'action' else None)
                symbol = add(node, owner=owner, detail=meta.xml_id or meta.qweb_name)
                if owner and symbol:
                    model = get_model(owner)
                    (model.views if node.kind == 'view' else model.actions).append(symbol)
        else:
            for node in _walk(inspection.file.children):
                if node.kind in INDEX_KINDS and node.kind != 'code':
                    meta = node.metadata
                    detail = None
                    if isinstance(meta, dict):
                        detail = str(meta.get('template') or meta.get('category') or '')[:180] or None
                    add(node, detail=detail)
    # Surface external relationship targets as reference-only nodes. They are not
    # presented as definitions inside this addon, and cannot resolve the registry.
    for model in list(model_map.values()):
        for rel in model.relations:
            if rel.target:
                get_model(rel.target)
        for external in [*model.inherits, *model.delegates]:
            if external:
                get_model(external)
    local = {name for name, m in model_map.items() if m.defined_here}
    for model in model_map.values():
        if model.source_classes:
            first = model.source_classes[0]
            for target in model.inherits:
                model.relations.append(ModelLink(
                    source=model.name, target=target, label='_inherit',
                    relation_type='inherit', relative_path=first.relative_path,
                    line_start=first.line_start,
                ))
            for target in model.delegates:
                model.relations.append(ModelLink(
                    source=model.name, target=target, label='_inherits',
                    relation_type='delegate', relative_path=first.relative_path,
                    line_start=first.line_start,
                ))
        for rel in model.relations:
            rel.local_target = rel.target in local
            response.relationships.append(rel)
    response.inspected_files = files_seen
    response.models = sorted(model_map.values(), key=lambda m: m.name.casefold())
    if response.truncated:
        warn('Index limits reached: some files or symbols were not included. Results are partial.')
    return response
