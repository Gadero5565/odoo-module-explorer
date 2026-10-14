"""Safe, read-only XML/QWeb/Odoo static structure parser for Odoo 16–19.

lxml provides Odoo semantics while expat supplies exact XML byte spans (including
multiline start/end tags). No network, DTDs, entity expansion, or source execution.
Every XML element is addressable; a synthetic 'other' node preserves inter-element
text, comments and declarations so physical byte sizes remain additive.
"""

from bisect import bisect_left
from io import BytesIO
from pathlib import Path
from xml.parsers import expat

from lxml import etree

from app.schemas.xml_inspection import XMLInspection, XMLMetadata, XMLSymbol

MAX_XML_BYTES = 4 * 1024 * 1024
MAX_XML_ELEMENTS = 20_000
MAX_XML_DEPTH = 128


class XMLInspectionError(ValueError):
    """Unsupported, excessive, or unsafe XML inspection request."""


class _Span:
    __slots__ = ('start', 'end')

    def __init__(self, start: int) -> None:
        self.start = start
        self.end = start


def _read_tag_end(data: bytes, index: int) -> int:
    """Return byte after closing '>', respecting XML attribute string quotes."""
    quote = 0
    for pos in range(index, len(data)):
        char = data[pos]
        if quote:
            if char == quote:
                quote = 0
        elif char in (34, 39):
            quote = char
        elif char == 62:
            return pos + 1
    raise XMLInspectionError('Unterminated XML tag.')


def _spans(data: bytes) -> list[_Span]:
    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    spans: list[_Span] = []
    opened: list[_Span] = []

    def start(_name: str, _attrs: dict[str, str]) -> None:
        if len(spans) >= MAX_XML_ELEMENTS or len(opened) >= MAX_XML_DEPTH:
            raise XMLInspectionError('XML exceeds the 20,000 element or 128 nesting depth limit.')
        span = _Span(parser.CurrentByteIndex)
        spans.append(span)
        opened.append(span)

    def end(_name: str) -> None:
        span = opened.pop()
        at = parser.CurrentByteIndex
        # expat points at the opening '<' of the end tag or immediately after
        # a self-closing start tag; both cases are covered without guesswork.
        span.end = _read_tag_end(data, at) if data[at:at + 2] == b'</' else at

    def doctype(*_args: object) -> None:
        raise XMLInspectionError('DTD declarations are not allowed in static XML inspection.')

    def entity(*_args: object) -> None:
        raise XMLInspectionError('Entity declarations are not allowed in static XML inspection.')

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = entity
    parser.ExternalEntityRefHandler = lambda *_args: 0
    parser.Parse(data, True)
    return spans


def _tag_name(value: str) -> str:
    return value.rsplit('}', 1)[-1]


def _attr(element: etree._Element, name: str) -> str | None:
    return element.get(name)


def _field_value(record: etree._Element, name: str) -> str | None:
    # Direct child only: fields nested in the view's arch are not record metadata.
    for child in record:
        if isinstance(child.tag, str) and _tag_name(child.tag) == 'field' and child.get('name') == name:
            return child.get('ref') or child.get('eval') or (child.text or '').strip() or None
    return None


def _view_type(record: etree._Element) -> str | None:
    explicitly = _field_value(record, 'type')
    if explicitly:
        return explicitly
    for child in record:
        if isinstance(child.tag, str) and _tag_name(child.tag) == 'field' and child.get('name') == 'arch':
            for arch in child:
                if isinstance(arch.tag, str):
                    name = _tag_name(arch.tag)
                    # tree is the legacy view-root name in Odoo 16/17.
                    return 'list' if name == 'tree' else 'inherited xpath' if name == 'xpath' else name
    return None


def _describe(element: etree._Element) -> tuple[str, str, XMLMetadata]:
    tag = _tag_name(element.tag)
    attrs = {str(_tag_name(key)): value[:300] for key, value in element.attrib.items()}
    meta = XMLMetadata(attributes=attrs, directive_count=sum(key.startswith('t-') for key in attrs))
    meta.xml_id = _attr(element, 'id')
    meta.field_name = _attr(element, 'name') if tag == 'field' else None
    meta.field_ref = _attr(element, 'ref') if tag == 'field' else None
    meta.xpath_expr = _attr(element, 'expr') if tag == 'xpath' else None
    meta.xpath_position = _attr(element, 'position') if tag == 'xpath' else None
    meta.qweb_name = _attr(element, 't-name')
    meta.qweb_inherit = _attr(element, 't-inherit') or _attr(element, 't-extend')
    meta.qweb_mode = _attr(element, 't-inherit-mode')
    meta.qweb_call = _attr(element, 't-call')

    if tag == 'record':
        meta.record_model = _attr(element, 'model')
        if meta.record_model == 'ir.ui.view':
            meta.target_model = _field_value(element, 'model')
            meta.inherit_ref = _field_value(element, 'inherit_id')
            meta.view_type = _view_type(element)
            return 'view', meta.xml_id or 'ir.ui.view', meta
        if meta.record_model and (meta.record_model.startswith('ir.actions.') or meta.record_model == 'ir.actions'):
            meta.action_res_model = _field_value(element, 'res_model')
            return 'action', meta.xml_id or meta.record_model, meta
        return 'record', meta.xml_id or meta.record_model or 'record', meta
    if tag in ('menuitem', 'menu'):
        meta.menu_parent = _attr(element, 'parent')
        meta.menu_action = _attr(element, 'action')
        return 'menu', meta.xml_id or _attr(element, 'name') or tag, meta
    if tag in ('template', 'report', 'act_window', 'act_window_view'):
        if tag == 'template':
            meta.inherit_ref = _attr(element, 'inherit_id')
            return 'template', meta.xml_id or _attr(element, 'name') or 'template', meta
        if tag in ('act_window', 'report'):
            meta.action_res_model = _attr(element, 'res_model') or _attr(element, 'model')
            return 'action', meta.xml_id or tag, meta
    if meta.qweb_name or meta.qweb_inherit:
        return 'template', meta.qweb_name or meta.qweb_inherit or tag, meta
    if tag == 'xpath':
        return 'xpath', meta.xpath_expr or 'xpath', meta
    if tag == 'field':
        return 'field', meta.field_name or 'field', meta
    if tag in ('odoo', 'data', 'templates', 'openerp'):
        return 'root', tag, meta
    return 'element', meta.xml_id or tag, meta


class _Parser:
    def __init__(self, relative_path: str, original: bytes):
        self.relative_path = relative_path
        self.data = original
        self.newlines = [i for i, char in enumerate(original) if char == 10]
        self.counts = dict(element_count=0, record_count=0, view_count=0, action_count=0,
                           menu_count=0, template_count=0, xpath_count=0, field_count=0)
        self.spans: list[_Span] = []
        self.offset = 0

    def _position(self, start: int, end: int) -> tuple[int | None, int | None, int]:
        if end <= start:
            return None, None, 0
        first = bisect_left(self.newlines, start) + 1
        last = bisect_left(self.newlines, end - 1) + 1
        return first, last, last - first + 1

    def _remainder(self, node: XMLSymbol, begin: int, end: int) -> None:
        cursor = begin
        residual = 0
        line_count = 0
        for child in sorted(node.children, key=lambda value: self._start_offsets[value.id]):
            start, stop = self._start_offsets[child.id], self._end_offsets[child.id]
            if start > cursor:
                residual += start - cursor
                line_count += self._position(cursor, start)[2]
            cursor = max(cursor, stop)
        if cursor < end:
            residual += end - cursor
            line_count += self._position(cursor, end)[2]
        if residual:
            node.children.append(XMLSymbol(
                id=f'{node.id}::@other', name='Other XML / text', kind='other', tag='',
                relative_path=self.relative_path, size_bytes=residual, line_count=line_count,
            ))
        node.children.sort(key=lambda item: (-item.size_bytes, item.name.casefold()))

    def _build(self, element: etree._Element, depth: int) -> XMLSymbol:
        if depth > MAX_XML_DEPTH:
            raise XMLInspectionError('XML exceeds the nesting depth limit.')
        span = self.spans[self.offset]
        index = self.offset
        self.offset += 1
        kind, name, meta = _describe(element)
        first, last, lines = self._position(span.start, span.end)
        node = XMLSymbol(
            id=f'{self.relative_path}::xml:{index}@{span.start}', name=name,
            kind=kind, tag=_tag_name(element.tag), relative_path=self.relative_path,
            size_bytes=span.end - span.start, line_count=lines,
            line_start=first, line_end=last, metadata=meta,
        )
        self._start_offsets[node.id] = span.start
        self._end_offsets[node.id] = span.end
        self.counts['element_count'] += 1
        if kind in ('record', 'view', 'action') and node.tag == 'record':
            self.counts['record_count'] += 1
        category = kind + '_count'
        if category in self.counts and kind != 'record':
            self.counts[category] += 1
        for child in element:
            if isinstance(child.tag, str):
                node.children.append(self._build(child, depth + 1))
        self._remainder(node, span.start, span.end)
        return node

    def parse(self) -> XMLInspection:
        root_node = XMLSymbol(
            id=self.relative_path, name=Path(self.relative_path).name,
            kind='file', tag='', relative_path=self.relative_path,
            size_bytes=len(self.data), line_count=len(self.data.splitlines()),
            line_start=1 if self.data else None,
            line_end=len(self.data.splitlines()) or None,
        )
        try:
            self.spans = _spans(self.data)
            safe_parser = etree.XMLParser(
                resolve_entities=False, no_network=True, load_dtd=False,
                recover=False, huge_tree=False, remove_comments=False,
            )
            doc = etree.parse(BytesIO(self.data), parser=safe_parser)
            source_root = doc.getroot()
            self._start_offsets = {}
            self._end_offsets = {}
            if source_root is not None:
                root_node.children = [self._build(source_root, 0)]
            if self.offset != len(self.spans):
                raise XMLInspectionError('Could not align XML elements to source byte ranges.')
            self._remainder(root_node, 0, len(self.data))
            return XMLInspection(file=root_node, **self.counts)
        except (XMLInspectionError, etree.XMLSyntaxError, expat.ExpatError, ValueError, RecursionError) as exc:
            # A broken XML file should not destroy the surrounding file browser.
            return XMLInspection(file=root_node, parse_error=f'XML parse error: {str(exc)[:260]}')


def inspect_xml_source(relative_path: str, original: bytes) -> XMLInspection:
    if len(original) > MAX_XML_BYTES:
        raise XMLInspectionError(f'XML exceeds the {MAX_XML_BYTES // (1024 * 1024)} MiB limit.')
    parser = _Parser(relative_path, original)
    # The byte-span scanner is UTF-8 aware, including BOM and CRLF. Multi-byte
    # UTF-16/32 markup delimiters need a different offset scanner; do not emit
    # incorrect sizes or source positions for those unusual Odoo inputs.
    if original.startswith((b'\xff\xfe', b'\xfe\xff', b'\x00\x00\xfe\xff', b'\xff\xfe\x00\x00')):
        return XMLInspection(file=XMLSymbol(
            id=relative_path, name=Path(relative_path).name, kind='file', tag='',
            relative_path=relative_path, size_bytes=len(original),
            line_count=len(original.splitlines()),
        ), parse_error='UTF-16/UTF-32 XML is not yet supported; use UTF-8.')
    return parser.parse()
