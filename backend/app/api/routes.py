"""Localhost-only analysis endpoints."""

from pathlib import Path, PurePosixPath

from fastapi import APIRouter, HTTPException

from app.core.module_detector import SUPPORTED_VERSIONS, inspect_module
from app.core.scanner import AnalysisError, DirectoryScanner, resolve_module_path
from app.parsers.python_parser import MAX_PYTHON_BYTES, PythonInspectionError, inspect_python_source
from app.schemas.analysis import AnalysisResult, AnalyzeRequest, ConfigResponse, ModuleDetails
from app.schemas.python_inspection import PythonInspectRequest, PythonInspection

router = APIRouter(prefix="/api")
PROJECT_ROOT = Path(__file__).resolve().parents[3]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "2"}


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
        root = resolve_module_path(request.module_path.strip())
        inspect_module(root, request.version_override)
        relative = request.relative_path
        relative_parts = PurePosixPath(relative).parts
        if (not relative.endswith('.py') or not relative_parts
                or any(piece in ('.', '..', '') for piece in relative_parts)
                or relative.startswith('/') or '\\' in relative or ':' in relative):
            raise AnalysisError('Expected a relative .py path inside the selected module.')
        path = root
        for segment in relative_parts:
            path = path / segment
            if path.is_symlink():
                raise AnalysisError('Symbolic links are not supported for Python inspection.')
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise AnalysisError('Python file does not exist inside this addon.')
        if path.stat().st_size > MAX_PYTHON_BYTES:
            raise AnalysisError('Python file exceeds the 4 MiB static-analysis limit.')
        return inspect_python_source(relative, path.read_bytes())
    except (AnalysisError, PythonInspectionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail='Could not read Python source file.') from exc
