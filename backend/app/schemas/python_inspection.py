"""Read-only Python source inspection API schema."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class PythonInspectRequest(AnalyzeRequest):
    relative_path: str = Field(min_length=4, max_length=2048)


class PythonSymbol(BaseModel):
    id: str
    name: str
    kind: Literal['file', 'class', 'method', 'function', 'async_method', 'async_function', 'code']
    relative_path: str
    size_bytes: int = 0
    line_count: int = 0
    line_start: int | None = None
    line_end: int | None = None
    column_start: int | None = None
    decorators: list[str] = Field(default_factory=list)
    parameters: str | None = None
    children: list['PythonSymbol'] = Field(default_factory=list)


class PythonInspection(BaseModel):
    file: PythonSymbol
    symbol_count: int = 0
    parse_error: str | None = None
