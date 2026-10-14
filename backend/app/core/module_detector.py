"""Read Odoo manifest metadata without evaluating or importing its source."""

import ast
import re
from pathlib import Path

from app.core.scanner import AnalysisError

SUPPORTED_VERSIONS = frozenset({"16", "17", "18", "19"})
VERSION_PATTERN = re.compile(r"^(\d{2})\.\d+(?:\.|$)")


def inspect_module(path: Path, version_override: str | None = None) -> dict:
    manifest = path / "__manifest__.py"
    if not manifest.is_file() or manifest.is_symlink():
        raise AnalysisError("This directory is not an Odoo addon: __manifest__.py is missing.")
    if not (path / "__init__.py").is_file():
        raise AnalysisError("This directory is not an Odoo addon: __init__.py is missing.")
    if manifest.stat().st_size > 1024 * 1024:
        raise AnalysisError("Module manifest exceeds the 1 MiB safety limit.")
    try:
        # literal_eval supports dictionaries of constant literals, but never executes code.
        metadata = ast.literal_eval(manifest.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, SyntaxError, ValueError, TypeError, MemoryError) as exc:
        raise AnalysisError("Could not statically parse __manifest__.py as a literal dict.") from exc
    if not isinstance(metadata, dict):
        raise AnalysisError("Odoo manifest must contain a Python dictionary.")
    manifest_version = metadata.get("version")
    if not isinstance(manifest_version, str):
        manifest_version = None
    match = VERSION_PATTERN.match(manifest_version) if manifest_version else None
    detected_version = match.group(1) if match else None
    if version_override and version_override not in SUPPORTED_VERSIONS:
        raise AnalysisError("Version override must be one of 16, 17, 18, or 19.")
    if detected_version and detected_version not in SUPPORTED_VERSIONS:
        raise AnalysisError(
            f"Odoo {detected_version} is not supported. Choose an Odoo 16–19 addon."
        )
    if detected_version and version_override and detected_version != version_override:
        raise AnalysisError(
            f"Manifest declares Odoo {detected_version}; remove the conflicting "
            f"Odoo {version_override} override."
        )
    resolved_version = detected_version or version_override
    summary = metadata.get("summary")
    return {
        "name": path.name,
        "absolute_path": str(path),
        "version": resolved_version,
        "detected_version": detected_version,
        "manifest_version": manifest_version,
        "summary": summary if isinstance(summary, str) else None,
        "application": metadata.get("application") if isinstance(metadata.get("application"), bool) else None,
    }
