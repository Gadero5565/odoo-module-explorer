"""AST parser: source bytes, nesting, decorators and resilience."""

from app.parsers.python_parser import inspect_python_source


SOURCE = '''from odoo import models, fields

@api.model
class Planner(models.Model):
    name = fields.Char()  # field declarations are residual source in the general AST parser

    @api.depends("name")
    def _compute_title(self):
        if self.name:
            return self.name
        return None

    async def load_data(self, value):
        def normalize(text):
            return text.strip()
        return normalize(value)

@api.model
def top_level(value):
    return value
'''


def children_of_kind(node, kind):
    return [child for child in node.children if child.kind == kind]


def check_additivity(node):
    """Every level partitions physical bytes and lines with no duplication."""
    if node.children:
        assert node.size_bytes == sum(child.size_bytes for child in node.children)
        assert node.line_count == sum(child.line_count for child in node.children)
    for child in node.children:
        check_additivity(child)


def test_decorators_async_nested_definitions_and_totals():
    response = inspect_python_source("models/planner.py", SOURCE.encode("utf-8"))
    assert response.parse_error is None
    assert response.symbol_count == 5
    root = response.file
    check_additivity(root)
    klass = children_of_kind(root, 'class')[0]
    assert klass.name == 'Planner'
    assert klass.decorators == ['api.model']
    assert (klass.line_start, klass.line_end) == (3, 16)
    methods = children_of_kind(klass, 'method')
    assert len(methods) == 1 and methods[0].name == '_compute_title'
    assert methods[0].decorators == ['api.depends(\'name\')']
    async_method = children_of_kind(klass, 'async_method')[0]
    assert async_method.parameters == '(self, value)'
    assert children_of_kind(async_method, 'function')[0].name == 'normalize'
    assert children_of_kind(root, 'function')[0].name == 'top_level'
    assert '::' in klass.id and '@3' in klass.id


def test_non_ascii_and_crlf_sizes_are_physical():
    source = 'title = "مرحبا"\r\n\r\ndef work():\r\n    return "é"\r\n'
    data = source.encode('utf-8')
    result = inspect_python_source('x.py', data)
    assert result.file.size_bytes == len(data)
    assert result.file.line_count == 4
    check_additivity(result.file)


def test_same_name_redefinitions_have_distinct_ids():
    result = inspect_python_source('x.py', b'def f():\n    pass\ndef f():\n    return True\n')
    assert len({child.id for child in children_of_kind(result.file, 'function')}) == 2
    check_additivity(result.file)


def test_syntax_error_returns_warning_not_exception():
    result = inspect_python_source('broken.py', b'def broken(:\n    pass\n')
    assert 'Syntax error at line 1' in result.parse_error
    assert result.file.size_bytes == len(b'def broken(:\n    pass\n')
    assert result.symbol_count == 0


def test_encoding_declaration_and_missing_final_newline():
    data = '# coding: latin-1\n\ndef drink():\n    return "mat\xe9"'.encode('latin-1')
    result = inspect_python_source('x.py', data)
    assert result.parse_error is None
    assert result.file.line_count == 4
    check_additivity(result.file)


def test_empty_file_and_only_statements():
    empty = inspect_python_source('empty.py', b'')
    assert empty.file.line_count == 0 and empty.file.children == []
    other = inspect_python_source('statements.py', b'answer = 42\n')
    assert other.file.children[0].kind == 'code'
    check_additivity(other.file)


def test_nested_in_control_flow():
    source = b'''if True:
    class First:
        def method(self):
            if self:
                def inner():
                    return 42
            return inner()
'''
    result = inspect_python_source('code.py', source)
    assert result.symbol_count == 3
    check_additivity(result.file)


def test_definitions_in_except_and_match_blocks():
    source = '''try:
    raise ValueError()
except ValueError:
    def recovery():
        return True

match 1:
    case 1:
        class PatternResult:
            pass
'''
    result = inspect_python_source('x.py', source.encode('utf-8'))
    assert result.symbol_count == 2
    check_additivity(result.file)
