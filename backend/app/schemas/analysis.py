"""Public response schema shared with the UI's TypeScript types."""

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    module_path: str = Field(min_length=1, max_length=4096)
    version_override: Literal["16", "17", "18", "19"] | None = None


class FileNode(BaseModel):
    id: str
    name: str
    relative_path: str
    kind: Literal["directory", "file"]
    extension: str | None = None
    size_bytes: int = 0
    file_count: int = 0
    directory_count: int = 0
    line_count: int = 0
    children: list["FileNode"] = Field(default_factory=list)


class ScanWarning(BaseModel):
    relative_path: str
    reason: str


class ModuleDetails(BaseModel):
    name: str
    absolute_path: str
    version: str | None
    detected_version: str | None
    manifest_version: str | None
    summary: str | None = None
    application: bool | None = None


class AnalysisResult(BaseModel):
    module: ModuleDetails
    root: FileNode
    revision: str = ""
    warnings: list[ScanWarning] = Field(default_factory=list)
    ignored_entries: int = 0


class ConfigResponse(BaseModel):
    demo_module_path: str
    supported_versions: list[str]


class RefreshRequest(AnalyzeRequest):
    previous_revision: str = Field(default="", max_length=64)


class RefreshResult(BaseModel):
    changed: bool
    revision: str
    changed_paths: list[str] = Field(default_factory=list)
    paths_truncated: bool = False
    analysis: AnalysisResult | None = None
