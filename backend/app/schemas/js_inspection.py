"""Version-agnostic JavaScript / OWL static inspection response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class JSInspectRequest(AnalyzeRequest):
    relative_path: str = Field(min_length=4, max_length=2048)


JSKind = Literal['file', 'class', 'function', 'method', 'property', 'service',
                 'registration', 'module', 'code']


class JSSymbol(BaseModel):
    id: str
    name: str
    kind: JSKind
    relative_path: str
    size_bytes: int = Field(ge=0)
    line_count: int = Field(ge=0)
    line_start: int | None = None
    line_end: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    children: list['JSSymbol'] = Field(default_factory=list)


class JSImport(BaseModel):
    source: str | None = None
    names: str | None = None


class JSRegistration(BaseModel):
    category: str | None = None
    key: str | None = None
    target: str | None = None
    line: int


class JSInspection(BaseModel):
    file: JSSymbol
    symbol_count: int = 0
    component_count: int = 0
    service_count: int = 0
    registration_count: int = 0
    imports: list[JSImport] = Field(default_factory=list)
    registrations: list[JSRegistration] = Field(default_factory=list)
    parse_error: str | None = None
