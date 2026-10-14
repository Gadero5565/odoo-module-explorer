"""Read-only directory scanner. No module imports, evaluation or symlink traversal."""

import os
from pathlib import Path

from app.schemas.analysis import FileNode, ScanWarning

# Never count machine-generated caches, repositories or dependencies as addon sources.
IGNORED_DIRECTORIES = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "node_modules", "dist", "build", ".tox", ".next",
})
IGNORED_FILES = frozenset({".DS_Store", "Thumbs.db"})
SOURCE_EXTENSIONS = frozenset({
    ".py", ".xml", ".js", ".jsx", ".ts", ".tsx", ".scss", ".css", ".less",
})
MAX_SCAN_DEPTH = 70
MAX_ENTRIES = 100_000
MAX_WARNINGS = 50


class AnalysisError(ValueError):
    """Safe, user-visible error for an invalid analysis request."""


def resolve_module_path(raw_path: str) -> Path:
    # A Windows path works when the backend is running on Windows. On Unix, it
    # is intentionally not remapped: analysis always happens on the backend host.
    path = Path(raw_path).expanduser()
    if path.is_symlink():
        raise AnalysisError("Symlinked module roots are not supported.")
    try:
        path = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AnalysisError("Module path does not exist or cannot be accessed.") from exc
    if not path.is_dir():
        raise AnalysisError("Module path must point to an Odoo addon directory.")
    return path


def _line_count(path: Path) -> int:
    """Stream textual source; count final unterminated lines correctly."""
    result = 0
    with path.open("rb") as stream:
        last_byte = b"\n"
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            result += chunk.count(b"\n")
            last_byte = chunk[-1:]
        if last_byte != b"\n":
            result += 1
    return result


class DirectoryScanner:
    def __init__(self, root: Path, line_counter=None):
        self.root = root
        self.line_counter = line_counter or (lambda path, stat: _line_count(path))
        self.fingerprints: dict[str, tuple[int, ...]] = {}
        self.warnings: list[ScanWarning] = []
        self.ignored_entries = 0
        self.seen_entries = 0

    def _warn(self, relative_path: str, reason: str) -> None:
        if len(self.warnings) < MAX_WARNINGS:
            self.warnings.append(ScanWarning(relative_path=relative_path, reason=reason))

    def scan(self) -> FileNode:
        return self._directory(self.root, "", depth=0)

    def _directory(self, path: Path, relative_path: str, depth: int) -> FileNode:
        if depth > MAX_SCAN_DEPTH:
            self._warn(relative_path, f"Skipped directory beyond maximum depth {MAX_SCAN_DEPTH}")
            return FileNode(
                id=relative_path or ".", name=path.name,
                relative_path=relative_path, kind="directory"
            )
        node = FileNode(
            id=relative_path or ".", name=path.name,
            relative_path=relative_path, kind="directory"
        )
        self.fingerprints[relative_path or "."] = (-1,)
        try:
            with os.scandir(path) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name.casefold())
        except OSError:
            self._warn(relative_path or ".", "Unable to list this directory")
            return node
        for entry in entries:
            rel = f"{relative_path}/{entry.name}" if relative_path else entry.name
            try:
                if entry.is_symlink():
                    self.ignored_entries += 1
                    self._warn(rel, "Skipped symbolic link")
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in IGNORED_DIRECTORIES:
                        self.ignored_entries += 1
                        continue
                    self.seen_entries += 1
                    if self.seen_entries > MAX_ENTRIES:
                        raise AnalysisError(f"Module exceeds {MAX_ENTRIES:,} scanned entries.")
                    child = self._directory(Path(entry.path), rel, depth + 1)
                elif entry.is_file(follow_symlinks=False):
                    if entry.name in IGNORED_FILES:
                        self.ignored_entries += 1
                        continue
                    self.seen_entries += 1
                    if self.seen_entries > MAX_ENTRIES:
                        raise AnalysisError(f"Module exceeds {MAX_ENTRIES:,} scanned entries.")
                    ext = Path(entry.name).suffix.lower()
                    # os.DirEntry.stat() has zero st_ino/st_dev on Windows. Cache lookups
                    # use Path.stat() (os.stat), so fingerprints must use that
                    # same source to avoid persistent cache misses.
                    stat = os.stat(entry.path, follow_symlinks=False)
                    self.fingerprints[rel] = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns,
                                              getattr(stat, "st_dev", 0), getattr(stat, "st_ino", 0))
                    lines = self.line_counter(Path(entry.path), stat) if ext in SOURCE_EXTENSIONS else 0
                    child = FileNode(
                        id=rel, name=entry.name, relative_path=rel, kind="file",
                        extension=ext or None, size_bytes=stat.st_size, file_count=1,
                        line_count=lines,
                    )
                else:
                    self.ignored_entries += 1
                    continue
                node.children.append(child)
                node.size_bytes += child.size_bytes
                node.file_count += child.file_count
                node.line_count += child.line_count
                node.directory_count += child.directory_count + (child.kind == "directory")
            except AnalysisError:
                raise
            except OSError:
                self._warn(rel, "Could not read file or directory")
        node.children.sort(key=lambda child: (-child.size_bytes, child.name.casefold()))
        return node
