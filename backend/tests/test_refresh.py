"""Phase 8: revision correctness, incremental parses, caching, limits, safety."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.parsers.python_parser import inspect_python_source
from app.services import refresh as refresh_service

client = TestClient(app)


def addon(tmp_path: Path) -> Path:
    module = tmp_path / 'cache_addon'
    module.mkdir()
    (module / '__manifest__.py').write_text(repr({'name': 'Cache', 'version': '19.0.1.0.0'}))
    (module / '__init__.py').write_text('')
    return module


def test_unchanged_revision_and_line_cache_reuse(tmp_path):
    root = addon(tmp_path)
    src = root / 'models.py'
    src.write_text('a\nb\nc\n')
    before = client.get('/api/cache/stats').json()['line_hits']
    first = client.post('/api/analyze', json={'module_path': str(root)}).json()
    assert len(first['revision']) == 64
    check = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': first['revision']
    }).json()
    assert check == {'changed': False, 'revision': first['revision'],
                     'changed_paths': [], 'paths_truncated': False, 'analysis': None}
    assert client.get('/api/cache/stats').json()['line_hits'] > before
    assert first['root']['line_count'] == 4  # manifest + source file


def test_scanner_fingerprints_match_path_stat_on_windows(tmp_path):
    # Windows os.DirEntry.stat() sets st_ino / st_dev to zero, but
    # Path.stat() does not. Both sides of the cache must use the same source.
    from app.core.module_detector import inspect_module

    root = addon(tmp_path)
    src = root / 'models.py'
    src.write_text('a\nb\n')
    local_cache = refresh_service.AnalysisCache()
    info = inspect_module(root)
    first, fingerprints = local_cache.scan(root, info)
    assert fingerprints['models.py'] == refresh_service.signature(src.stat())
    assert first.root.line_count == 3
    assert local_cache.stats()['line_hits'] == 0
    again, _ = local_cache.scan(root, info)
    assert again.revision == first.revision
    assert local_cache.stats()['line_hits'] >= 2  # manifest and models.py


def test_add_edit_same_size_and_delete_preserves_metrics(tmp_path):
    root = addon(tmp_path)
    initial = client.post('/api/analyze', json={'module_path': str(root)}).json()
    file = root / 'activity.py'
    file.write_text('a=1\n')
    added = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': initial['revision']
    }).json()
    assert added['changed'] and added['analysis']['root']['file_count'] == 3
    assert added['changed_paths'] == ['activity.py']
    old = file.stat()
    file.write_text('b=2\n')  # same number of bytes and lines
    os.utime(file, ns=(old.st_atime_ns, old.st_mtime_ns + 1_000_000_000))
    edited = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': added['revision']
    }).json()
    assert edited['changed'] and edited['revision'] != added['revision']
    assert edited['changed_paths'] == ['activity.py']
    file.unlink()
    removed = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': edited['revision']
    }).json()
    assert removed['changed'] and removed['analysis']['root']['file_count'] == 2
    assert removed['changed_paths'] == ['activity.py']


def test_renamed_directory_and_subtree_delta(tmp_path):
    root = addon(tmp_path)
    folder = root / 'models'
    folder.mkdir()
    (folder / 'a.py').write_text('pass')
    first = client.post('/api/analyze', json={'module_path': str(root)}).json()
    folder.rename(root / 'new_models')
    fresh = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': first['revision']
    }).json()
    assert fresh['changed']
    assert {'models', 'models/a.py', 'new_models', 'new_models/a.py'} <= set(fresh['changed_paths'])


def test_cache_reparses_changed_file_only_and_reuses_insights(tmp_path):
    root = addon(tmp_path)
    src1, src2 = root / 'a.py', root / 'b.py'
    src1.write_text('def first():\n    return 1\n')
    src2.write_text('def second():\n    return 2\n')
    start = client.get('/api/cache/stats').json()
    for i in range(2):
        res = client.post('/api/insights', json={'module_path': str(root)})
        assert res.status_code == 200, res.text
    stats = client.get('/api/cache/stats').json()
    assert stats['insight_hits'] > start['insight_hits']
    # Preserve b.py's existing parse; changing a.py invalidates only a.py.
    src1.write_text('def first():\n    return 3\n')
    os.utime(src1, None)
    prev_hits = stats['parse_hits']
    res = client.post('/api/insights', json={'module_path': str(root)})
    assert res.status_code == 200
    after = client.get('/api/cache/stats').json()
    assert after['parse_hits'] > prev_hits
    assert any(sym['name'] == 'first' for sym in res.json()['symbols'])


def test_source_inspection_reuses_parse_and_later_computes_complexity(tmp_path):
    root = addon(tmp_path)
    src = root / 'source.py'
    src.write_text('def logic(v):\n    if v:\n        return 1\n    return 0\n')
    payload = {'module_path': str(root), 'relative_path': 'source.py'}
    assert client.post('/api/python/inspect', json=payload).status_code == 200
    before = client.get('/api/cache/stats').json()['parse_hits']
    assert client.post('/api/python/inspect', json=payload).status_code == 200
    assert client.get('/api/cache/stats').json()['parse_hits'] > before
    ins = client.post('/api/insights', json={'module_path': str(root)})
    assert ins.status_code == 200
    assert next(sym['complexity'] for sym in ins.json()['symbols'] if sym['name'] == 'logic') >= 2


def test_refresh_unknown_revision_recovers_from_server_restart(tmp_path):
    root = addon(tmp_path)
    payload = client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': 'f' * 64
    }).json()
    assert payload['changed'] and payload['analysis']
    assert payload['changed_paths'] == ['*']
    assert payload['paths_truncated'] is False


def test_refresh_rejects_invalid_module_and_does_not_expose_source(tmp_path):
    root = addon(tmp_path)
    stats = client.get('/api/cache/stats').json()
    assert not any('path' in k or 'content' in k for k in stats)
    assert client.post('/api/refresh', json={'module_path': str(tmp_path)}).status_code == 400
    assert client.post('/api/refresh', json={
        'module_path': str(root), 'previous_revision': 'x' * 65
    }).status_code == 422


def test_cache_lru_caps_memory_and_does_not_execute_source(tmp_path, monkeypatch):
    root = addon(tmp_path)
    cache = refresh_service.AnalysisCache()
    monkeypatch.setattr(refresh_service, 'MAX_PARSED_FILES', 2)
    marker = tmp_path / 'should_not_exist'
    for i in range(4):
        file = root / f'file_{i}.py'
        file.write_text(f'open({str(marker)!r}, "w").write("BAD")\nvalue = {i}\n')
        inspected, _ = cache.inspect(file, '.py', inspect_python_source, file.name)
        assert inspected.file
    assert cache.stats()['parse_entries'] == 2
    assert not marker.exists()


def test_concurrent_line_count_refresh_stable(tmp_path):
    root = addon(tmp_path)
    (root / 'file.py').write_text('one\ntwo\nthree\n')
    cache = refresh_service.AnalysisCache()
    info = {'name': root.name, 'absolute_path': str(root), 'version': '19',
            'detected_version': '19', 'manifest_version': '19.0.1.0.0',
            'summary': None, 'application': None}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: cache.scan(root, info)[0], range(8)))
    assert len({r.revision for r in results}) == 1
    assert all(r.root.line_count == 4 for r in results)  # manifest + file


def test_malformed_source_still_has_scan_metrics(tmp_path):
    root = addon(tmp_path)
    (root / 'bad.py').write_text('def fail(:\n')
    first = client.post('/api/analyze', json={'module_path': str(root)}).json()
    assert first['root']['line_count'] == 2  # manifest + invalid Python file
    ins = client.post('/api/insights', json={'module_path': str(root)})
    assert ins.status_code == 200
    assert any('bad.py' in w for w in ins.json()['warnings'])
    fresh = client.post('/api/refresh', json={'module_path': str(root),
        'previous_revision': first['revision']}).json()
    assert fresh['changed'] is False


def test_source_changed_during_parse_is_retried_once(tmp_path):
    root = addon(tmp_path)
    file = root / 'model.py'
    file.write_text('def first():\n    pass\n')
    cache = refresh_service.AnalysisCache()
    attempts = []

    def moving_parser(relative, data):
        attempts.append(data)
        if len(attempts) == 1:
            file.write_text('def second():\n    pass\n')
        return inspect_python_source(relative, data)

    inspected, _ = cache.inspect(file, '.py', moving_parser, 'model.py', max_bytes=1024)
    assert len(attempts) == 2
    assert any(node.name == 'second' for node in inspected.file.children)


def test_parser_cannot_read_replaced_oversize_source(tmp_path):
    root = addon(tmp_path)
    file = root / 'large.py'
    file.write_bytes(b'x' * 101)
    cache = refresh_service.AnalysisCache()
    import pytest
    with pytest.raises(OSError, match='size limit'):
        cache.inspect(file, '.py', inspect_python_source, 'large.py', max_bytes=100)
