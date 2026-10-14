"""Normalized, read-only CSS/SCSS source inspection payloads."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class StyleInspectRequest(AnalyzeRequest):
    relative_path: str = Field(min_length=5, max_length=2048)


StyleKind = Literal[
    'file', 'selector', 'declaration', 'variable', 'mixin', 'function',
    'include', 'at_rule', 'keyframes', 'other',
]


class StyleMetadata(BaseModel):
    prelude: str | None = None
    property: str | None = None
    value: str | None = None
    selector: str | None = None
    at_rule: str | None = None
    parameters: str | None = None
    import_target: str | None = None
    important: bool = False
    nested: bool = False


class StyleSymbol(BaseModel):
    id: str
    name: str
    kind: StyleKind
    relative_path: str
    size_bytes: int = Field(ge=0)
    line_count: int = Field(ge=0)
    line_start: int | None = None
    line_end: int | None = None
    metadata: StyleMetadata = Field(default_factory=StyleMetadata)
    children: list['StyleSymbol'] = Field(default_factory=list)


class StyleInspection(BaseModel):
    file: StyleSymbol
    syntax: Literal['css', 'scss']
    selector_count: int = 0
    declaration_count: int = 0
    variable_count: int = 0
    mixin_count: int = 0
    function_count: int = 0
    include_count: int = 0
    at_rule_count: int = 0
    keyframes_count: int = 0
    imports: list[str] = Field(default_factory=list)
    parse_error: str | None = None
