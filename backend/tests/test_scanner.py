from pathlib import Path

import pytest

from app.core.module_detector import inspect_module
from app.core.scanner import AnalysisError, DirectoryScanner, resolve_module_path


def make_module(tmp_path: Path, version: str = "19.0.1.0.0") -> Path:
    module = tmp_path / "test_addon"
    module.mkdir()
    (module / "__init__.py").write_text("", encoding="utf-8")
    (module / "__manifest__.py").write_text(
        repr({"name": "Test", "version": version}), encoding="utf-8"
    )
    return module


def test_nested_size_file_count_and_sorted_children(tmp_path):
    module = make_module(tmp_path)
    folder = module / "models"
    folder.mkdir()
    (folder / "a.py").write_bytes(b"a\nb\nc")
    (folder / "big.py").write_bytes(b"a" * 100)
    (module / "README.md").write_bytes(b"Read me")
    root = DirectoryScanner(module).scan()
    assert root.size_bytes == sum(p.stat().st_size for p in module.rglob("*") if p.is_file())
    assert root.file_count == 5
    assert root.directory_count == 1
    assert root.children[0].name == "models"
    assert [p.name for p in root.children[0].children] == ["big.py", "a.py"]
    assert next(p for p in root.children[0].children if p.name == "a.py").line_count == 3
    assert root.children[0].relative_path == "models"


def test_non_source_files_not_counted_as_lines(tmp_path):
    module = make_module(tmp_path)
    (module / "logo.png").write_bytes(b"\x89PNG\n\x00")
    root = DirectoryScanner(module).scan()
    image = next(p for p in root.children if p.name == "logo.png")
    assert image.line_count == 0
    assert image.size_bytes == 6


def test_skips_generated_directories_and_symlink(tmp_path):
    module = make_module(tmp_path)
    cache = module / "__pycache__"
    cache.mkdir()
    (cache / "large.pyc").write_bytes(b"X" * 10000)
    external = tmp_path / "external.txt"
    external.write_bytes(b"secret")
    try:
        (module / "linked.txt").symlink_to(external)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable on this platform")
    scanner = DirectoryScanner(module)
    root = scanner.scan()
    assert root.file_count == 2
    assert scanner.ignored_entries == 2
    assert len(scanner.warnings) == 1
    assert scanner.warnings[0].relative_path == "linked.txt"


def test_static_manifest_version_and_safe_literal(tmp_path):
    module = make_module(tmp_path)
    assert inspect_module(module)["version"] == "19"
    assert inspect_module(module, "19")["version"] == "19"
    with pytest.raises(AnalysisError, match="conflicting"):
        inspect_module(module, "17")
    (module / "__manifest__.py").write_text("__import__('os').system('echo bad')")
    with pytest.raises(AnalysisError, match="statically parse"):
        inspect_module(module)


def test_unsupported_odoo_version(tmp_path):
    module = make_module(tmp_path, "15.0.1.0.0")
    with pytest.raises(AnalysisError, match="not supported"):
        inspect_module(module)
    with pytest.raises(AnalysisError, match="not supported"):
        inspect_module(module, "19")


def test_missing_manifest(tmp_path):
    with pytest.raises(AnalysisError, match="manifest"):
        inspect_module(tmp_path)


def test_root_must_be_directory(tmp_path):
    filename = tmp_path / "file.py"
    filename.write_text("hi")
    with pytest.raises(AnalysisError, match="directory"):
        resolve_module_path(str(filename))


def test_missing_version_is_permitted_with_override(tmp_path):
    module = make_module(tmp_path, "1.0.0")
    assert inspect_module(module)["version"] is None
    assert inspect_module(module, "16")["version"] == "16"
