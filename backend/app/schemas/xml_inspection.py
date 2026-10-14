"""Normalized read-only XML/Odoo/QWeb source inspection schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class XMLInspectRequest(AnalyzeRequest):
    relative_path: str = Field(min_length=5, max_length=2048)


class XMLMetadata(BaseModel):
    """Syntactic metadata only; references are not resolved against a running Odoo registry."""

    xml_id: str | None = None
    record_model: str | None = None
    target_model: str | None = None
    inherit_ref: str | None = None
    view_type: str | None = None
    xpath_expr: str | None = None
    xpath_position: str | None = None
    qweb_name: str | None = None
    qweb_inherit: str | None = None
    qweb_mode: str | None = None
    qweb_call: str | None = None
    field_name: str | None = None
    field_ref: str | None = None
    menu_parent: str | None = None
    menu_action: str | None = None
    action_res_model: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    directive_count: int = 0


XMLKind = Literal[
    'file', 'root', 'record', 'view', 'action', 'menu', 'template',
    'xpath', 'field', 'element', 'other',
]


class XMLSymbol(BaseModel):
    id: str
    name: str
    kind: XMLKind
    tag: str
    relative_path: str
    size_bytes: int = 0
    line_count: int = 0
    line_start: int | None = None
    line_end: int | None = None
    metadata: XMLMetadata = Field(default_factory=XMLMetadata)
    children: list['XMLSymbol'] = Field(default_factory=list)


class XMLInspection(BaseModel):
    file: XMLSymbol
    element_count: int = 0
    record_count: int = 0
    view_count: int = 0
    action_count: int = 0
    menu_count: int = 0
    template_count: int = 0
    xpath_count: int = 0
    field_count: int = 0
    parse_error: str | None = None
