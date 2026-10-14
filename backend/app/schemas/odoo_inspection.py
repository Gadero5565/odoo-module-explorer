"""Structured, non-executing Odoo semantics extracted from Python syntax."""

from typing import Literal

from pydantic import BaseModel, Field


class OdooClassInfo(BaseModel):
    category: Literal['model', 'transient', 'abstract', 'controller']
    model_name: str | None = None
    inherits: list[str] = Field(default_factory=list)
    delegates: dict[str, str] = Field(default_factory=dict)
    description: str | None = None
    field_count: int = 0
    method_count: int = 0
    field_types: dict[str, int] = Field(default_factory=dict)


class OdooFieldInfo(BaseModel):
    field_type: str
    relation: str | None = None
    string: str | None = None
    compute: str | None = None
    inverse: str | None = None
    search: str | None = None
    related: str | None = None
    required: bool | None = None
    readonly: bool | None = None
    store: bool | None = None
    default: str | None = None
    comodel_expression: str | None = None


class OdooRouteInfo(BaseModel):
    paths: list[str] = Field(default_factory=list)
    auth: str | None = None
    route_type: str | None = None
    methods: list[str] = Field(default_factory=list)
    csrf: bool | None = None


class OdooMethodInfo(BaseModel):
    role: Literal[
        'compute', 'inverse', 'search', 'constraint', 'onchange',
        'orm_override', 'controller_route', 'cron', 'business_action', 'default', 'other'
    ]
    api_decorators: list[str] = Field(default_factory=list)
    depends: list[str] = Field(default_factory=list)
    onchange_fields: list[str] = Field(default_factory=list)
    constraint_fields: list[str] = Field(default_factory=list)
    routes: list[OdooRouteInfo] = Field(default_factory=list)
