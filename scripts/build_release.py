"""Build a self-contained Python wheel (UI, TS JS grammar, example addon).

Build requirements: Python 3.10+, Node.js 20+, npm, frontend dependencies,
setuptools and wheel. Runtime: Python + Node.js for JS/OWL analysis only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'
BACKEND = ROOT / 'backend'
APP = BACKEND / 'app'


class ReleaseBuildError(RuntimeError):
    """Release contents cannot be assembled or validated."""


def _command(argv: list[str], *, cwd: Path) -> None:
    print('> ' + ' '.join(argv), flush=True)
    subprocess.run(argv, cwd=str(cwd), check=True)


def _npm_executable(*, windows: bool | None = None) -> str | None:
    """Return the executable npm launcher for this platform.

    On Windows, npm installs as npm.cmd; Popen([...]) cannot be relied upon
    to resolve the PowerShell npm alias to that batch file.
    """
    if windows is None:
        windows = os.name == 'nt'
    return shutil.which('npm.cmd' if windows else 'npm')


def prepare_release_assets(frontend: Path = FRONTEND, app: Path = APP,
                           sample: Path | None = None) -> tuple[Path, Path]:
    """Stage assets into the Python package, checking prerequisites first."""
    compiled = frontend / 'dist'
    parser = frontend / 'node_modules' / 'typescript' / 'lib' / 'typescript.js'
    license_file = frontend / 'node_modules' / 'typescript' / 'LICENSE.txt'
    demo = sample if sample is not None else ROOT / 'samples' / 'demo_odoo_module'
    if not (compiled / 'index.html').is_file():
        raise ReleaseBuildError('Missing frontend/dist/index.html. Run npm run build in frontend.')
    if not any((compiled / 'assets').glob('*.js')):
        raise ReleaseBuildError('Missing frontend/dist/assets/*.js — UI build looks incomplete.')
    if not parser.is_file() or not license_file.is_file():
        raise ReleaseBuildError('Missing TypeScript runtime or LICENSE. Run npm install in frontend.')
    if not (demo / '__manifest__.py').is_file():
        raise ReleaseBuildError('Missing example addon __manifest__.py.')

    web = app / 'web_dist'
    vendor = app / 'vendor'
    example = app / 'demo_addon'
    for dest in (web, example):
        if dest.exists():
            shutil.rmtree(dest)
    shutil.copytree(compiled, web)
    shutil.copytree(demo, example, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    vendor.mkdir(parents=True, exist_ok=True)
    shutil.copy2(parser, vendor / 'typescript.js')
    shutil.copy2(license_file, vendor / 'LICENSE.txt')
    print(f'Staged UI, TypeScript grammar, and demo addon into {app}', flush=True)
    return web, vendor


def main(argv: list[str] | None = None) -> int:
    argp = argparse.ArgumentParser(description='Build the Odoo Module Explorer wheel')
    argp.add_argument('--skip-npm', action='store_true',
                      help='Use existing frontend/dist and node_modules (for CI)')
    argp.add_argument('--output', type=Path, default=ROOT / 'release',
                      help='Destination for built wheel')
    options = argp.parse_args(argv)
    if not options.skip_npm:
        npm = _npm_executable()
        if shutil.which('node') is None or npm is None:
            argp.error('Node.js 20+ and npm are required to build a release. '
                       'On Windows ensure npm.cmd is available on PATH.')
        command = 'ci' if (FRONTEND / 'package-lock.json').exists() else 'install'
        _command([npm, command], cwd=FRONTEND)
        _command([npm, 'run', 'build'], cwd=FRONTEND)
    try:
        prepare_release_assets()
    except ReleaseBuildError as exc:
        argp.error(str(exc))
    target = options.output.resolve()
    target.mkdir(parents=True, exist_ok=True)
    # Wheel is platform-independent: the JS grammar is JavaScript source (not
    # a compiled binary). Python, Node.js and OS architecture remain external.
    _command([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
              '--wheel-dir', str(target), str(BACKEND)], cwd=ROOT)
    built = sorted(target.glob('odoo_module_explorer_backend-*.whl'))
    if not built:
        raise ReleaseBuildError(f'Wheel was not created in {target}.')
    print('Built release wheel: ' + str(built[-1]), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
