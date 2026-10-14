"""Bounded, static CSS/SCSS structure analyzer for Odoo addon stylesheets.

A tolerant lexical parser, not a Sass compiler. It handles quoted literals,
comments, parentheses, brackets, interpolation, nested SCSS rules and Sass
statements; it never evaluates expressions or reads imported files. Source
positions use physical UTF-8 bytes. One residual node per parent retains
comments, punctuation and whitespace so children partition byte sizes exactly.
"""

from bisect import bisect_left
from pathlib import Path

from app.schemas.style_inspection import StyleInspection, StyleMetadata, StyleSymbol

MAX_STYLE_BYTES = 3 * 1024 * 1024
MAX_STYLE_NODES = 20_000
MAX_STYLE_DEPTH = 96
MAX_PRELUDE_BYTES = 8_192


class StyleInspectionError(ValueError):
    """Requested source cannot be safely inspected."""


def _brief(data: bytes) -> str:
    return ' '.join(data.decode('utf-8', errors='replace').split())[:300]


class _Parser:
    def __init__(self, path: str, data: bytes) -> None:
        self.path = path
        self.data = data
        self.syntax = 'scss' if path.lower().endswith('.scss') else 'css'
        self.newlines = [i for i, char in enumerate(data) if char == 10]
        self.length = len(data)
        self.pos = 0
        self.nodes = 0
        self.counts = {
            'selector_count': 0, 'declaration_count': 0, 'variable_count': 0,
            'mixin_count': 0, 'function_count': 0, 'include_count': 0,
            'at_rule_count': 0, 'keyframes_count': 0,
        }
        self.imports: list[str] = []

    def _line_span(self, begin: int, end: int) -> tuple[int | None, int | None, int]:
        if end <= begin:
            return None, None, 0
        first = bisect_left(self.newlines, begin) + 1
        last = bisect_left(self.newlines, end - 1) + 1
        return first, last, last - first + 1

    def _node(self, kind: str, name: str, begin: int, end: int,
              metadata: StyleMetadata | None = None,
              children: list[StyleSymbol] | None = None) -> StyleSymbol:
        self.nodes += 1
        if self.nodes > MAX_STYLE_NODES:
            raise StyleInspectionError('Stylesheet exceeds the 20,000 node limit.')
        first, last, lines = self._line_span(begin, end)
        return StyleSymbol(
            id=f'{self.path}::style:{begin}:{end}', name=name[:250], kind=kind,
            relative_path=self.path, size_bytes=end - begin, line_count=lines,
            line_start=first, line_end=last, metadata=metadata or StyleMetadata(),
            children=children or [],
        )

    def _skip_gap(self) -> None:
        """Skip whitespace/comments without treating their delimiters as syntax."""
        data = self.data
        while self.pos < self.length:
            pos = self.pos
            if data[pos] in b' \t\r\n\f':
                self.pos += 1
            elif data[pos:pos + 2] == b'/*':
                end = data.find(b'*/', pos + 2)
                if end < 0:
                    raise StyleInspectionError('Unterminated stylesheet block comment.')
                self.pos = end + 2
            elif self.syntax == 'scss' and data[pos:pos + 2] == b'//':
                end = data.find(b'\n', pos + 2)
                self.pos = self.length if end < 0 else end + 1
            else:
                return

    def _read_until(self) -> tuple[bytes, int]:
        """Read a statement header up to an unquoted {, ; or }.

        Parentheses/brackets and Sass interpolation keep internal punctuation
        out of the block parser. The raw source itself is never modified.
        """
        data = self.data
        start = self.pos
        parentheses = 0
        brackets = 0
        interpolations = 0
        while self.pos < self.length:
            pos = self.pos
            char = data[pos]
            next_two = data[pos:pos + 2]
            if char in (34, 39):  # quoted strings
                quote = char
                self.pos += 1
                while self.pos < self.length:
                    current = data[self.pos]
                    if current == 92:  # escaped quote or character
                        self.pos += 2
                    elif current == quote:
                        self.pos += 1
                        break
                    else:
                        self.pos += 1
                else:
                    raise StyleInspectionError('Unterminated stylesheet string literal.')
                continue
            if next_two == b'/*':
                end = data.find(b'*/', pos + 2)
                if end < 0:
                    raise StyleInspectionError('Unterminated stylesheet block comment.')
                self.pos = end + 2
                continue
            if (self.syntax == 'scss' and next_two == b'//' and not parentheses
                    and not brackets and (pos == start or data[pos - 1] in b' \t\n\r')):
                end = data.find(b'\n', pos + 2)
                self.pos = self.length if end < 0 else end + 1
                continue
            if next_two == b'#{' and self.syntax == 'scss':
                interpolations += 1
                self.pos += 2
                continue
            if interpolations:
                if char == 123:
                    interpolations += 1
                elif char == 125:
                    interpolations -= 1
                self.pos += 1
                continue
            if char == 92:  # escaped separator in CSS selector
                self.pos += 2
                continue
            if char == 40:
                parentheses += 1
            elif char == 41:
                parentheses = max(parentheses - 1, 0)
            elif char == 91:
                brackets += 1
            elif char == 93:
                brackets = max(brackets - 1, 0)
            elif char in (123, 125, 59) and not parentheses and not brackets:
                return data[start:pos], char
            self.pos += 1
        if interpolations:
            raise StyleInspectionError('Unterminated Sass interpolation.')
        return data[start:self.pos], 0

    @staticmethod
    def _describe(header: bytes, block: bool) -> tuple[str, str, StyleMetadata]:
        prelude = _brief(header)
        meta = StyleMetadata(prelude=prelude, nested=block)
        value = prelude.strip()
        if value.startswith('@'):
            command = value.split(None, 1)[0].split('(', 1)[0]
            meta.at_rule = command
            meta.parameters = value[len(command):].strip()[:300] or None
            if command == '@mixin':
                return 'mixin', value, meta
            if command == '@function':
                return 'function', value, meta
            if command == '@include':
                return 'include', value, meta
            if command in ('@keyframes', '@-webkit-keyframes'):
                return 'keyframes', value, meta
            if command in ('@import', '@use', '@forward'):
                meta.import_target = value[len(command):].strip()[:250]
            return 'at_rule', value, meta
        # Custom declarations and Sass variables may have nested values,
        # but ordinary block headers (e.g. &:hover) are selectors.
        if value.startswith('$') and ':' in value and not block:
            prop, val = value.split(':', 1)
            meta.property = prop.strip()
            meta.value = val.strip()[:300]
            return 'variable', prop.strip(), meta
        if not block and ':' in value:
            prop, val = value.split(':', 1)
            meta.property = prop.strip()[:250]
            meta.value = val.strip()[:300]
            meta.important = '!important' in val.lower()
            return 'declaration', prop.strip()[:250], meta
        if block:
            meta.selector = value
            return 'selector', value, meta
        return 'other', value[:150] or 'Other statement', meta

    def _with_other(self, parent: StyleSymbol, begin: int, end: int,
                    spans: list[tuple[int, int, StyleSymbol]]) -> None:
        cursor = begin
        residual = 0
        lines = 0
        for start, stop, _ in spans:
            if start > cursor:
                residual += start - cursor
                lines += self._line_span(cursor, start)[2]
            cursor = max(cursor, stop)
        if cursor < end:
            residual += end - cursor
            lines += self._line_span(cursor, end)[2]
        if residual:
            parent.children.append(StyleSymbol(
                id=f'{parent.id}::@other', name='Other source / comments',
                kind='other', relative_path=self.path,
                size_bytes=residual, line_count=lines,
            ))
        parent.children.sort(key=lambda node: (-node.size_bytes, node.name.casefold()))

    def _children(self, parent: StyleSymbol, begin: int, depth: int,
                  in_block: bool) -> int:
        if depth > MAX_STYLE_DEPTH:
            raise StyleInspectionError('Stylesheet nesting exceeds 96 levels.')
        spans: list[tuple[int, int, StyleSymbol]] = []
        data = self.data
        while self.pos < self.length:
            self._skip_gap()
            if self.pos >= self.length:
                break
            if data[self.pos] == 125:
                if not in_block:
                    raise StyleInspectionError('Unexpected closing brace in stylesheet.')
                self.pos += 1
                self._with_other(parent, begin, self.pos, spans)
                return self.pos
            start = self.pos
            header, boundary = self._read_until()
            if len(header) > MAX_PRELUDE_BYTES:
                raise StyleInspectionError('Stylesheet rule header exceeds 8 KiB.')
            if boundary == 123:
                if not header.strip():
                    raise StyleInspectionError('Unexpected opening brace in stylesheet.')
                kind, name, meta = self._describe(header, True)
                self.pos += 1
                child = self._node(kind, name, start, self.pos, meta)
                end = self._children(child, start, depth + 1, True)
                # Parent node's physical span includes the entire block.
                first, last, line_count = self._line_span(start, end)
                child.size_bytes = end - start
                child.line_count = line_count
                child.line_start = first
                child.line_end = last
            elif boundary in (59, 125, 0):
                if boundary == 125 and not in_block:
                    raise StyleInspectionError('Unexpected closing brace in stylesheet.')
                if boundary == 0 and in_block:
                    raise StyleInspectionError('Unclosed stylesheet block.')
                if not header.strip():
                    if boundary == 59:
                        self.pos += 1
                    continue
                kind, name, meta = self._describe(header, False)
                if boundary == 59:
                    self.pos += 1
                child = self._node(kind, name, start, self.pos, meta)
            else:
                raise StyleInspectionError('Invalid stylesheet token.')
            counter = child.kind + '_count'
            if counter in self.counts:
                self.counts[counter] += 1
            if child.kind == 'at_rule':
                if child.metadata.import_target and len(self.imports) < 200:
                    self.imports.append(child.metadata.import_target)
            spans.append((start, self.pos, child))
            parent.children.append(child)
            if boundary == 0:
                break
        if in_block:
            raise StyleInspectionError('Unclosed stylesheet block.')
        self._with_other(parent, begin, self.pos, spans)
        return self.pos

    def parse(self) -> StyleInspection:
        physical_lines = len(self.data.splitlines())
        root = StyleSymbol(
            id=self.path, name=Path(self.path).name, kind='file',
            relative_path=self.path, size_bytes=self.length,
            line_count=physical_lines,
            line_start=1 if self.length else None,
            line_end=physical_lines or None,
        )
        try:
            if self.data.startswith(b'\xef\xbb\xbf'):
                self.pos = 3  # UTF-8 BOM is residual source, not a selector token.
            self._children(root, 0, 0, False)
            return StyleInspection(file=root, syntax=self.syntax, imports=self.imports, **self.counts)
        except (StyleInspectionError, RecursionError) as exc:
            root.children = []
            return StyleInspection(
                file=root, syntax=self.syntax, parse_error=str(exc),
            )


def inspect_style_source(relative_path: str, data: bytes) -> StyleInspection:
    if not relative_path.lower().endswith(('.css', '.scss')):
        raise StyleInspectionError('Expected a .css or .scss file.')
    if len(data) > MAX_STYLE_BYTES:
        raise StyleInspectionError('Stylesheet exceeds the 3 MiB analysis limit.')
    try:
        data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise StyleInspectionError('Stylesheet source must be UTF-8 encoded.') from exc
    return _Parser(relative_path, data).parse()
