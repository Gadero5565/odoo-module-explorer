"""Localhost-only analysis endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.module_detector import SUPPORTED_VERSIONS, inspect_module
from app.core.scanner import AnalysisError, DirectoryScanner, resolve_module_path
from app.core.source_files import resolve_source_file
from app.parsers.js_parser import MAX_JS_BYTES, JSInspectionError, inspect_js_source
from app.parsers.python_parser import MAX_PYTHON_BYTES, PythonInspectionError, inspect_python_source
from app.parsers.xml_parser import MAX_XML_BYTES, XMLInspectionError, inspect_xml_source
from app.schemas.analysis import AnalysisResult, AnalyzeRequest, ConfigResponse, ModuleDetails
from app.schemas.js_inspection import JSInspectRequest, JSInspection
from app.schemas.python_inspection import PythonInspectRequest, PythonInspection
from app.schemas.xml_inspection import XMLInspectRequest, XMLInspection

router = APIRouter(prefix="/api")
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "5"}


@router.get("/config", response_model=ConfigResponse)
def config() -> ConfigResponse:
    return ConfigResponse(
        demo_module_path=str(PROJECT_ROOT / "samples" / "demo_odoo_module"),
        supported_versions=sorted(SUPPORTED_VERSIONS),
    )


@router.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    try:
        path = resolve_module_path(request.module_path.strip())
        info = inspect_module(path, request.version_override)
        scanner = DirectoryScanner(path)
        root = scanner.scan()
        return AnalysisResult(
            module=ModuleDetails(**info), root=root,
            warnings=scanner.warnings, ignored_entries=scanner.ignored_entries,
        )
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/python/inspect", response_model=PythonInspection)
def inspect_python(request: PythonInspectRequest) -> PythonInspection:
    """Inspect one .py file under a validated addon root, without executing it."""
    try:
        path = resolve_source_file(request.module_path, request.version_override,
                                   request.relative_path, '.py', MAX_PYTHON_BYTES)
        return inspect_python_source(request.relative_path, path.read_bytes())
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
        return inspect_xml_source(request.relative_path, path.read_bytes())
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
        return inspect_js_source(request.relative_path, path.read_bytes())
    except (AnalysisError, JSInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read JavaScript source file.') from exc
