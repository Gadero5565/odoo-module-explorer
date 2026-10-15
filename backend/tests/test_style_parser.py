"""CSS/SCSS structural and byte-preservation regression tests."""

from app.parsers.style_parser import inspect_style_source


def walk(node):
    yield node
    for child in node.children:
        yield from walk(child)


def assert_additive(node):
    if node.children:
        assert node.size_bytes == sum(child.size_bytes for child in node.children)
        for child in node.children:
            assert_additive(child)


def test_nested_scss_with_variables_mixin_function_import_media():
    src = b'''/* header */
@use "sass:color";
$accent: #2563eb !default;
@function spacing($step) { @return $step * 4px; }
@mixin button($color: $accent) {
  padding: spacing(2);
  background: $color;
}
.o_calendar_widget {
    @include button();
    color: #fff;
    &:hover { color: color.adjust($accent, $lightness: 10%); }
    @media (max-width: 700px) { padding: 8px; }
}
'''
    data = inspect_style_source('static/src/a.scss', src)
    assert data.parse_error is None
    assert data.variable_count == 1
    assert data.mixin_count == 1
    assert data.function_count == 1
    assert data.include_count == 1
    assert data.selector_count == 2
    assert data.declaration_count == 5
    assert data.at_rule_count == 3  # @use, @media, @return
    assert len(data.imports) == 1
    assert data.imports[0] == '"sass:color"'
    assert data.file.size_bytes == len(src)
    assert_additive(data.file)
    mixin = next(n for n in walk(data.file) if n.kind == 'mixin')
    assert mixin.line_start == 5
    assert mixin.children


def test_plain_css_media_custom_properties_and_url():
    src = b'''/* comment */
:root { --accent: #235; }
@media screen and (min-width: 500px) {
  .card > a[href^="https://"] { color: red !important; background: url(https://example.org/a.png); }
}
'''
    data = inspect_style_source('static/src/main.css', src)
    assert data.parse_error is None
    assert data.syntax == 'css'
    assert data.selector_count == 2
    assert data.declaration_count == 3
    assert data.at_rule_count == 1
    assert any(n.metadata.important for n in walk(data.file))
    assert_additive(data.file)


def test_scss_interpolation_and_escaped_tokens_unicode_bom_crlf():
    src = '\ufeff// note\r\n$clé: "été";\r\n.icon-#{$clé} { content: "\\\"}"; width: 100%; }\r\n'.encode()
    data = inspect_style_source('a.scss', src)
    assert data.parse_error is None
    assert data.variable_count == 1
    assert data.selector_count == 1
    assert data.declaration_count == 2
    assert data.file.size_bytes == len(src)
    assert_additive(data.file)
    assert next(n for n in walk(data.file) if n.kind == 'selector').line_start == 3


def test_comments_and_whitespace_only():
    src = b'/* just comment */\n\n'
    data = inspect_style_source('a.css', src)
    assert data.file.size_bytes == len(src)
    assert data.file.children[0].kind == 'other'
    assert data.selector_count == 0
    assert_additive(data.file)


def test_bad_syntax_preserves_physical_totals():
    for source in (b'.x { color: red;', b'.x }', b'/* unterminated', b'.x { content: "a; }'):
        data = inspect_style_source('a.scss', source)
        assert data.parse_error
        assert data.file.size_bytes == len(source)
        assert data.file.children == []


def test_empty_file():
    data = inspect_style_source('a.css', b'')
    assert data.parse_error is None
    assert data.file.children == []
    assert data.file.size_bytes == 0


def test_does_not_evaluate_imports_or_expressions(tmp_path):
    source = b'@import "../../secrets";\n.x { width: calc(100% - 2px); }'
    data = inspect_style_source('a.scss', source)
    assert data.parse_error is None
    assert data.imports == ['"../../secrets"']
    assert data.selector_count == 1
    assert_additive(data.file)


def test_nested_depth_limit_preserves_file():
    source = b'.x {' * 100 + b'}' * 100
    data = inspect_style_source('a.scss', source)
    assert 'nesting' in data.parse_error
    assert data.file.size_bytes == len(source)
    assert data.file.children == []


def test_reject_non_utf8_and_excessive_size():
    import pytest

    from app.parsers.style_parser import MAX_STYLE_BYTES, StyleInspectionError

    with pytest.raises(StyleInspectionError, match='UTF-8'):
        inspect_style_source('a.css', b'\xff')
    with pytest.raises(StyleInspectionError, match='3 MiB'):
        inspect_style_source('a.scss', b'a' * (MAX_STYLE_BYTES + 1))
