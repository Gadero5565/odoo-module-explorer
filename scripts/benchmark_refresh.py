"""Synthetic local performance smoke test (no addon source is ever executed).

Run from the repository root:  python scripts/benchmark_refresh.py
The timings are for your machine only; there are no hardcoded thresholds.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

from app.services.refresh import AnalysisCache  # noqa: E402
from app.services.insights import build_insights  # noqa: E402


def timed(operation):
    start = perf_counter()
    result = operation()
    return result, 1000 * (perf_counter() - start)


def run():
    with TemporaryDirectory(prefix='odoo-explorer-perf-') as temp:
        root = Path(temp) / 'benchmark_addon'
        (root / 'models').mkdir(parents=True)
        (root / '__manifest__.py').write_text(repr({'name': 'Benchmark', 'version': '19.0.1.0.0'}))
        (root / '__init__.py').write_text('')
        for number in range(400):
            (root / 'models' / f'model_{number:03}.py').write_text(
                f'from odoo import fields, models\n'
                f'class Model{number}(models.Model):\n'
                f'    _name = "benchmark.model.{number}"\n'
                f'    value = fields.Char()\n'
                f'    def action_run(self):\n'
                f'        return self.value\n', encoding='utf-8')
        info = {'name': root.name, 'absolute_path': str(root), 'version': '19',
                'detected_version': '19', 'manifest_version': '19.0.1.0.0'}
        cache = AnalysisCache()
        (initial, _), cold = timed(lambda: cache.scan(root, info))
        (_, _), warm = timed(lambda: cache.scan(root, info))

        def index():
            scan, _ = cache.scan(root, info)
            return build_insights(root, tree=scan.root, parse_cache=cache)

        initial_index, cold_index = timed(index)
        _, warm_index = timed(index)
        path = root / 'models' / 'model_007.py'
        path.write_text(path.read_text(encoding='utf-8') + '\n# changed\n', encoding='utf-8')
        new_scan, _ = cache.scan(root, info)
        _, incremental_index = timed(index)
        assert new_scan.revision != initial.revision
        assert initial_index.inspected_files == 402
        print(f'Files: {initial.root.file_count}; symbols: {len(initial_index.symbols)}')
        print(f'Filesystem scan (cold / warm): {cold:.1f} / {warm:.1f} ms')
        print(f'Insights index (cold / cached-parses / one changed): '
              f'{cold_index:.1f} / {warm_index:.1f} / {incremental_index:.1f} ms')
        print('Cache counters:', cache.stats())


if __name__ == '__main__':
    run()
