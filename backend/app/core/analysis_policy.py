"""Conservative Odoo source policy; no contents of excluded paths are opened.

The physical "all_files" view still applies the existing scanner safety excludes
(e.g. symlinks and machine caches). Vendor files remain manually inspectable
within the ordinary per-file limits, but are never added to semantic Insights.
"""

from typing import Literal

AnalysisProfile = Literal["odoo_source", "all_files"]
DEFAULT_PROFILE: AnalysisProfile = "odoo_source"


def is_vendor_path(relative_path: str, *, directory: bool = False) -> bool:
    """Recognize Odoo-specific vendor/description assets, not arbitrary `lib` dirs."""
    parts = tuple(part.casefold() for part in relative_path.replace("\\", "/").split("/"))
    if not parts:
        return False
    # Odoo's standard static asset layouts and optional root description folder.
    parents = parts if directory else parts[:-1]
    if parents and parents[0] == "description":
        return True
    if len(parents) >= 2 and parents[:2] in (("static", "lib"), ("static", "description")):
        return True
    if len(parents) >= 3 and parents[:3] == ("static", "src", "lib"):
        return True
    if directory:
        return False
    name = parts[-1]
    return (name.endswith((".min.js", ".min.css", ".js.map", ".css.map")))


def excluded_from_scan(relative_path: str, *, directory: bool,
                       profile: AnalysisProfile) -> bool:
    return profile == "odoo_source" and is_vendor_path(relative_path, directory=directory)
