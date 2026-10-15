"""Refresh system: bounded, process-local incremental analysis cache and revisions.

Only filesystem metadata and parsed symbol models are cached. Nothing is written
inside the scanned addon. Cache entries are invalidated on a changed file stat
signature (size, mtime, ctime, inode, device); the cache is never trusted for
path validation or module manifest validation.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.scanner import DirectoryScanner, _line_count
from app.schemas.analysis import AnalysisResult, ModuleDetails, ScanWarning

MAX_LINE_CACHE = 12_000
MAX_PARSED_FILES = 1024
MAX_PARSED_BYTES = 24 * 1024 * 1024
MAX_SNAPSHOTS = 8
MAX_INSIGHT_RESULTS = 6
MAX_CHANGED_PATHS = 250


def signature(stat: Any) -> tuple[int, ...]:
    """Include ctime and inode to catch same-sized atomic replacements."""
    return (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns,
            getattr(stat, 'st_dev', 0), getattr(stat, 'st_ino', 0))


@dataclass
class CachedParse:
    signature: tuple[int, ...]
    inspection: Any
    complexities: dict | None
    source_bytes: int


class AnalysisCache:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.lines: OrderedDict[str, tuple[tuple[int, ...], int]] = OrderedDict()
        self.parsed: OrderedDict[tuple[str, str], CachedParse] = OrderedDict()
        self.parsed_bytes = 0
        self.snapshots: OrderedDict[tuple[str, str], dict[str, tuple[int, ...]]] = OrderedDict()
        self.insights: OrderedDict[tuple[str, str], Any] = OrderedDict()
        self.line_hits = 0
        self.line_misses = 0
        self.parse_hits = 0
        self.parse_misses = 0
        self.insight_hits = 0

    def line_count(self, path: Path, stat: Any) -> int:
        key, stamp = str(path), signature(stat)
        with self.lock:
            cached = self.lines.get(key)
            if cached and cached[0] == stamp:
                self.lines.move_to_end(key)
                self.line_hits += 1
                return cached[1]
            self.line_misses += 1
        lines = _line_count(path)
        # Do not persist a count if the file changed during reading.
        if signature(path.stat()) == stamp:
            with self.lock:
                self.lines[key] = (stamp, lines)
                self.lines.move_to_end(key)
                if len(self.lines) > MAX_LINE_CACHE:
                    self.lines.popitem(last=False)
        return lines

    def inspect(self, path: Path, parser_kind: str, parser: Callable[[str, bytes], Any],
                relative_path: str, complexity_fn: Callable[[bytes], dict] | None = None,
                max_bytes: int | None = None):
        """Return inspection (and optional complexities). Parser errors are NOT cached.

        The caller must validate paths, symlinks, suffix and file size before
        using this method. A final post-read stat check protects against saves
        taking place while parsing; on a race we retry at most once.
        """
        key = (str(path), parser_kind)
        for attempt in range(2):
            before = signature(path.stat())
            if max_bytes is not None and before[0] > max_bytes:
                raise OSError('Source exceeds the parser file-size limit.')
            with self.lock:
                existing = self.parsed.get(key)
                if existing and existing.signature == before:
                    self.parsed.move_to_end(key)
                    self.parse_hits += 1
                    if complexity_fn is None or existing.complexities is not None:
                        return existing.inspection, existing.complexities
                    # A standalone inspector may have cached the syntax tree
                    # before Insights requested complexity. Reuse its parse.
                    with path.open('rb') as stream:
                        raw = stream.read(max_bytes + 1) if max_bytes is not None else stream.read()
                    if (max_bytes is None or len(raw) <= max_bytes) and signature(path.stat()) == before:
                        existing.complexities = complexity_fn(raw)
                        return existing.inspection, existing.complexities
                self.parse_misses += 1
            with path.open('rb') as stream:
                data = stream.read(max_bytes + 1) if max_bytes is not None else stream.read()
            if max_bytes is not None and len(data) > max_bytes:
                raise OSError('Source exceeds the parser file-size limit.')
            inspection = parser(relative_path, data)
            complexity = complexity_fn(data) if complexity_fn is not None else None
            after = signature(path.stat())
            if after != before:
                if attempt == 0:
                    continue
                raise OSError('Source file changed during inspection; retry after saving.')
            # Keep large files uncached; still return their fresh inspection.
            if len(data) <= MAX_PARSED_BYTES:
                with self.lock:
                    old = self.parsed.pop(key, None)
                    if old:
                        self.parsed_bytes -= old.source_bytes
                    self.parsed[key] = CachedParse(before, inspection, complexity, len(data))
                    self.parsed_bytes += len(data)
                    while len(self.parsed) > MAX_PARSED_FILES or self.parsed_bytes > MAX_PARSED_BYTES:
                        _, evicted = self.parsed.popitem(last=False)
                        self.parsed_bytes -= evicted.source_bytes
            return inspection, complexity
        raise OSError('Unable to inspect source file.')

    def scan(self, root: Path, info: dict) -> tuple[AnalysisResult, dict[str, tuple[int, ...]]]:
        scanner = DirectoryScanner(root, line_counter=self.line_count)
        tree = scanner.scan()
        fingerprints = scanner.fingerprints
        revision = self.revision(fingerprints, scanner.ignored_entries, scanner.warnings)
        result = AnalysisResult(module=ModuleDetails(**info), root=tree, revision=revision,
                                warnings=scanner.warnings, ignored_entries=scanner.ignored_entries)
        return result, fingerprints

    @staticmethod
    def revision(fingerprints: dict[str, tuple[int, ...]], ignored: int,
                 warnings: list[ScanWarning]) -> str:
        # Stable across Python processes. Entries include directories + files,
        # and include non-source files to keep aggregate physical sizes correct.
        payload = json.dumps((sorted(fingerprints.items()), ignored,
                              [(w.relative_path, w.reason) for w in warnings]),
                             separators=(',', ':'), ensure_ascii=True)
        return hashlib.sha256(payload.encode('ascii')).hexdigest()

    def remember(self, root: Path, revision: str, fingerprints: dict[str, tuple[int, ...]]) -> None:
        key = (str(root), revision)
        with self.lock:
            self.snapshots[key] = fingerprints.copy()
            self.snapshots.move_to_end(key)
            while len(self.snapshots) > MAX_SNAPSHOTS:
                self.snapshots.popitem(last=False)

    def changes(self, root: Path, old_revision: str,
                new_fingerprints: dict[str, tuple[int, ...]]) -> tuple[list[str], bool]:
        with self.lock:
            previous = self.snapshots.get((str(root), old_revision))
        if previous is None:
            # Restarted server / expired snapshot: force a complete update.
            return ['*'], False
        paths = sorted(k for k in previous.keys() | new_fingerprints.keys()
                       if previous.get(k) != new_fingerprints.get(k))
        if len(paths) > MAX_CHANGED_PATHS:
            return paths[:MAX_CHANGED_PATHS], True
        return paths, False

    def get_insights(self, root: Path, revision: str, build: Callable[[], Any]):
        key = (str(root), revision)
        with self.lock:
            cached = self.insights.get(key)
            if cached is not None:
                self.insights.move_to_end(key)
                self.insight_hits += 1
                return cached
        result = build()
        with self.lock:
            self.insights[key] = result
            self.insights.move_to_end(key)
            while len(self.insights) > MAX_INSIGHT_RESULTS:
                self.insights.popitem(last=False)
        return result

    def stats(self) -> dict[str, int]:
        with self.lock:
            return {
                'line_hits': self.line_hits, 'line_misses': self.line_misses,
                'parse_hits': self.parse_hits, 'parse_misses': self.parse_misses,
                'insight_hits': self.insight_hits, 'line_entries': len(self.lines),
                'parse_entries': len(self.parsed), 'parsed_source_bytes': self.parsed_bytes,
                'snapshots': len(self.snapshots), 'insight_entries': len(self.insights),
            }


cache = AnalysisCache()
