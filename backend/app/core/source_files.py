"""Validate read-only requests for individual addon source files."""

from pathlib import Path, PurePosixPath

from app.core.module_detector import inspect_module
from app.core.scanner import AnalysisError, resolve_module_path


def resolve_source_file(module_path: str, version_override: str | None,
                        relative: str, extension: str, max_size: int) -> Path:
    root = resolve_module_path(module_path.strip())
    inspect_module(root, version_override)
    parts = PurePosixPath(relative).parts
    if (not relative.endswith(extension) or not parts
            or any(part in ('', '.', '..') for part in parts)
            or relative.startswith('/') or '\\' in relative or ':' in relative):
        raise AnalysisError(f'Expected a relative {extension} path inside the selected module.')
    path = root
    for segment in parts:
        path = path / segment
        if path.is_symlink():
            raise AnalysisError('Symbolic links are not supported for source inspection.')
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise AnalysisError('Source file does not exist inside this addon.')
    if path.stat().st_size > max_size:
        raise AnalysisError(f'Source file exceeds the {max_size // (1024 * 1024)} MiB static-analysis limit.')
    return path
