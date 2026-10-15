"""Localhost-only analysis endpoints."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.module_detector import SUPPORTED_VERSIONS, inspect_module
from app.core.scanner import AnalysisError, resolve_module_path
from app.core.source_files import resolve_source_file
from app.parsers.js_parser import MAX_JS_BYTES, JSInspectionError, inspect_js_source
from app.parsers.python_parser import MAX_PYTHON_BYTES, PythonInspectionError, inspect_python_source
from app.parsers.style_parser import MAX_STYLE_BYTES, StyleInspectionError, inspect_style_source
from app.parsers.xml_parser import MAX_XML_BYTES, XMLInspectionError, inspect_xml_source
from app.schemas.analysis import (
    AnalysisResult,
    AnalyzeRequest,
    ConfigResponse,
    RefreshRequest,
    RefreshResult,
)
from app.schemas.insights import InsightRequest, InsightsResponse
from app.schemas.js_inspection import JSInspection, JSInspectRequest
from app.schemas.python_inspection import PythonInspection, PythonInspectRequest
from app.schemas.style_inspection import StyleInspection, StyleInspectRequest
from app.schemas.xml_inspection import XMLInspection, XMLInspectRequest
from app.services.insights import build_insights
from app.services.refresh import cache

router = APIRouter(prefix="/api")
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    development_demo = PROJECT_ROOT / "samples" / "demo_odoo_module"
    bundled_demo = Path(__file__).resolve().parents[1] / "demo_addon"
    demo_path = development_demo if development_demo.is_dir() else bundled_demo
    return ConfigResponse(
        demo_module_path=str(demo_path) if demo_path.is_dir() else "",
        supported_versions=sorted(SUPPORTED_VERSIONS),
        initial_module_path=os.getenv("ODOO_EXPLORER_INITIAL_MODULE") or None,
    )


@router.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    try:
        path = resolve_module_path(request.module_path.strip())
        info = inspect_module(path, request.version_override)
        result, fingerprints = cache.scan(path, info, request.analysis_profile)
        cache.remember(path, result.revision, fingerprints)
        return result
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/python/inspect", response_model=PythonInspection)
def inspect_python(request: PythonInspectRequest) -> PythonInspection:
    """Inspect one .py file under a validated addon root, without executing it."""
    try:
        path = resolve_source_file(request.module_path, request.version_override,
                                   request.relative_path, '.py', MAX_PYTHON_BYTES)
        return cache.inspect(path, ".py", inspect_python_source, request.relative_path, max_bytes=MAX_PYTHON_BYTES)[0]
    except (AnalysisError, PythonInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read Python source file.') from exc


@router.post("/xml/inspect", response_model=XMLInspection)
def inspect_xml(request: XMLInspectRequest) -> XMLInspection:
    """Parse Odoo data, views and QWeb XML without loading external entities."""
    try:
        path = resolve_source_file(request.module_path, request.version_override,
                                   request.relative_path, '.xml', MAX_XML_BYTES)
        return cache.inspect(path, ".xml", inspect_xml_source, request.relative_path, max_bytes=MAX_XML_BYTES)[0]
    except (AnalysisError, XMLInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read XML source file.') from exc


@router.post("/javascript/inspect", response_model=JSInspection)
def inspect_javascript(request: JSInspectRequest) -> JSInspection:
    """Inspect a JS file using syntax parsing, never executing addon source."""
    try:
        path = resolve_source_file(request.module_path, request.version_override,
                                   request.relative_path, '.js', MAX_JS_BYTES)
        return cache.inspect(path, ".js", inspect_js_source, request.relative_path, max_bytes=MAX_JS_BYTES)[0]
    except (AnalysisError, JSInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read JavaScript source file.') from exc


@router.post('/styles/inspect', response_model=StyleInspection)
def inspect_styles(request: StyleInspectRequest) -> StyleInspection:
    """Inspect one CSS/SCSS source file, never compiling or executing Sass."""
    try:
        suffix = Path(request.relative_path).suffix.lower()
        if suffix not in ('.css', '.scss'):
            raise AnalysisError('Expected a .css or .scss source file.')
        path = resolve_source_file(request.module_path, request.version_override,
                                   request.relative_path, Path(request.relative_path).suffix, MAX_STYLE_BYTES)
        return cache.inspect(path, suffix, inspect_style_source, request.relative_path, max_bytes=MAX_STYLE_BYTES)[0]
    except (AnalysisError, StyleInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read stylesheet source file.') from exc


@router.post('/insights', response_model=InsightsResponse)
def inspect_module_insights(request: InsightRequest) -> InsightsResponse:
    """Build a bounded, searchable source index for the selected local addon."""
    try:
        root = resolve_module_path(request.module_path.strip())
        inspect_module(root, request.version_override)
        analysis, fingerprints = cache.scan(root, inspect_module(root, request.version_override), request.analysis_profile)
        cache.remember(root, analysis.revision, fingerprints)
        return cache.get_insights(root, analysis.revision, lambda: build_insights(
            root, tree=analysis.root, parse_cache=cache, scan_warnings=analysis.warnings,
        ))
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Unable to read module source files.') from exc


@router.post('/refresh', response_model=RefreshResult)
def refresh_module(request: RefreshRequest) -> RefreshResult:
    """Metadata-only polling with cached source line metrics and optional diff.

    No filesystem watcher threads or unauthenticated filesystem paths are
    exposed. Only the selected validated addon root is scanned.
    """
    try:
        root = resolve_module_path(request.module_path.strip())
        info = inspect_module(root, request.version_override)
        result, fingerprints = cache.scan(root, info, request.analysis_profile)
        changed = result.revision != request.previous_revision
        paths, truncated = cache.changes(root, request.previous_revision, fingerprints) if changed else ([], False)
        cache.remember(root, result.revision, fingerprints)
        return RefreshResult(changed=changed, revision=result.revision,
                             changed_paths=paths, paths_truncated=truncated,
                             analysis=result if changed else None)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not scan module during refresh.') from exc


@router.get('/cache/stats')
def cache_stats() -> dict[str, int]:
    """Non-sensitive process cache diagnostics (no paths or source content)."""
    return cache.stats()
