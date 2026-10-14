"""Bounded, read-only module-wide search and Odoo relationship index."""

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class InsightRequest(AnalyzeRequest):
    """Analyze a single Odoo addon, never an arbitrary repository."""


class InsightSymbol(BaseModel):
    id: str
    name: str
    kind: str
    relative_path: str
    line_start: int | None = None
    line_end: int | None = None
    size_bytes: int = 0
    line_count: int = 0
    complexity: int | None = None
    owner_model: str | None = None
    detail: str | None = None


class ModelLink(BaseModel):
    source: str
    target: str
    label: str
    relation_type: str
    relative_path: str
    line_start: int | None = None
    local_target: bool = False


class OdooModelSummary(BaseModel):
    name: str
    defined_here: bool = False
    source_classes: list[InsightSymbol] = Field(default_factory=list)
    fields: list[InsightSymbol] = Field(default_factory=list)
    methods: list[InsightSymbol] = Field(default_factory=list)
    views: list[InsightSymbol] = Field(default_factory=list)
    actions: list[InsightSymbol] = Field(default_factory=list)
    relations: list[ModelLink] = Field(default_factory=list)
    inherits: list[str] = Field(default_factory=list)
    delegates: list[str] = Field(default_factory=list)


class InsightsResponse(BaseModel):
    symbols: list[InsightSymbol] = Field(default_factory=list)
    models: list[OdooModelSummary] = Field(default_factory=list)
    relationships: list[ModelLink] = Field(default_factory=list)
    inspected_files: int = 0
    skipped_files: int = 0
    warnings: list[str] = Field(default_factory=list)
    truncated: bool = False
