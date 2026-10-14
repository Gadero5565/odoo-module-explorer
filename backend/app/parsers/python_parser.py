"""Pure AST Python structure explorer; never imports or executes analyzed source.

Byte sizes and LOC are based on *physical line spans*. A synthetic `code` child
represents source outside definitions so treemap child areas sum exactly to
parent areas, even when functions are nested within classes or other functions.
"""

import ast
import io
import tokenize
from pathlib import Path

from app.schemas.python_inspection import PythonInspection, PythonSymbol

MAX_PYTHON_BYTES = 4 * 1024 * 1024
MAX_AST_SYMBOLS = 15_000


class PythonInspectionError(ValueError):
    """Invalid or unsafe source inspection request."""


class _SymbolLimit(Exception):
    pass


def _decorator_name(value: ast.expr) -> str:
    try:
        return ast.unparse(value)[:200]
    except (ValueError, RecursionError):
        return '<unknown>'


def _parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Compact parameter names only; no expressions evaluated."""
    args = node.args
    pieces = [arg.arg for arg in args.posonlyargs]
    if args.posonlyargs:
        pieces.append('/')
    pieces.extend(arg.arg for arg in args.args)
    if args.vararg:
        pieces.append('*' + args.vararg.arg)
    elif args.kwonlyargs:
        pieces.append('*')
    pieces.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        pieces.append('**' + args.kwarg.arg)
    return '(' + ', '.join(pieces)[:250] + ')'


def _nested_definitions(statements: list[ast.stmt]) -> list[ast.stmt]:
    """Find named definitions within if/try/except/match/with/loop blocks.

    Stop upon reaching a named definition; its body belongs to its own scope.
    """
    found: list[ast.stmt] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(node)
            return
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.stmt, ast.ExceptHandler, ast.match_case)):
                visit(child)

    for statement in statements:
        visit(statement)
    return found


class _Parser:
    def __init__(self, path: str, original: bytes):
        self.path = path
        self.line_sizes = [len(line) for line in original.splitlines(keepends=True)]
        self.created = 0

    def _measure(self, start: int, end: int) -> tuple[int, int]:
        sizes = self.line_sizes[start - 1:end]
        return sum(sizes), len(sizes)

    def _add_remainder(self, parent: PythonSymbol, begin: int, end: int) -> None:
        """One virtual child gathers discontinuous portions not held by sub-symbols."""
        intervals = sorted((c.line_start, c.line_end) for c in parent.children
                           if c.kind != 'code' and c.line_start and c.line_end)
        remaining_lines = 0
        remaining_bytes = 0
        cursor = begin
        for first, last in intervals:
            if first > cursor:
                size, count = self._measure(cursor, first - 1)
                remaining_bytes += size
                remaining_lines += count
            cursor = max(cursor, last + 1)
        if cursor <= end:
            size, count = self._measure(cursor, end)
            remaining_bytes += size
            remaining_lines += count
        if remaining_lines:
            parent.children.append(PythonSymbol(
                id=f'{parent.id}::@code', name='Other code / declarations',
                kind='code', relative_path=self.path,
                size_bytes=remaining_bytes, line_count=remaining_lines,
            ))
        parent.children.sort(key=lambda c: (-c.size_bytes, c.name.casefold()))

    def symbol(self, item: ast.stmt, parent: PythonSymbol | None = None) -> PythonSymbol:
        self.created += 1
        if self.created > MAX_AST_SYMBOLS:
            raise _SymbolLimit()
        is_class = isinstance(item, ast.ClassDef)
        is_async = isinstance(item, ast.AsyncFunctionDef)
        is_method = parent is not None and parent.kind == 'class' and not is_class
        kind = ('class' if is_class else 'async_method' if is_async and is_method
                else 'method' if is_method else 'async_function' if is_async else 'function')
        decorators = [_decorator_name(d) for d in item.decorator_list]
        start = min([item.lineno, *(d.lineno for d in item.decorator_list)])
        end = item.end_lineno or item.lineno
        size_bytes, line_count = self._measure(start, end)
        # AST node positions distinguish same-name redefinitions by source line.
        node = PythonSymbol(
            id=f'{self.path}::{kind}:{item.name}@{start}', name=item.name,
            kind=kind, relative_path=self.path,
            line_start=start, line_end=end, column_start=item.col_offset,
            size_bytes=size_bytes, line_count=line_count,
            decorators=decorators,
            parameters=None if is_class else _parameters(item),
        )
        for child in _nested_definitions(item.body):
            node.children.append(self.symbol(child, node))
        self._add_remainder(node, start, end)
        return node

    def parse(self, source: str) -> PythonInspection:
        bytes_total = sum(self.line_sizes)
        root = PythonSymbol(
            id=self.path, name=Path(self.path).name, kind='file',
            relative_path=self.path, size_bytes=bytes_total,
            line_count=len(self.line_sizes), line_start=1 if self.line_sizes else None,
            line_end=len(self.line_sizes) or None,
        )
        try:
            parsed = ast.parse(source, filename=self.path)
            for item in _nested_definitions(parsed.body):
                root.children.append(self.symbol(item))
            self._add_remainder(root, 1, len(self.line_sizes))
            return PythonInspection(file=root, symbol_count=self.created)
        except SyntaxError as exc:
            return PythonInspection(
                file=root, symbol_count=0,
                parse_error=f'Syntax error at line {exc.lineno}: {exc.msg}',
            )
        except (_SymbolLimit, RecursionError):
            return PythonInspection(
                file=root, symbol_count=0,
                parse_error='Python source exceeds the static parser complexity limit.',
            )


def inspect_python_source(relative_path: str, original: bytes) -> PythonInspection:
    if len(original) > MAX_PYTHON_BYTES:
        raise PythonInspectionError(f'Python file exceeds {MAX_PYTHON_BYTES // (1024 * 1024)} MiB limit.')
    parser = _Parser(relative_path, original)
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(original).readline)
        source = original.decode(encoding)
    except (SyntaxError, UnicodeError, LookupError) as exc:
        return PythonInspection(
            file=PythonSymbol(
                id=relative_path, name=Path(relative_path).name, kind='file',
                relative_path=relative_path, size_bytes=len(original),
                line_count=len(parser.line_sizes),
            ),
            parse_error=f'Could not decode Python source: {str(exc)[:180]}',
        )
    return parser.parse(source)
