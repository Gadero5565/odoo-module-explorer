"""Console launcher for the local, read-only Odoo Module Explorer.

The app listens ONLY on loopback; no remote or public network access.
"""

import argparse
import os
import shutil
import sys
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from app.core.module_detector import inspect_module
from app.core.scanner import AnalysisError, resolve_module_path
from app.main import APP_VERSION, app, frontend_directory

DEFAULT_PORT = 7764


def _port(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Port must be an integer between 1024 and 65535.') from exc
    if number < 1024 or number > 65535:
        raise argparse.ArgumentTypeError('Port must be an integer between 1024 and 65535.')
    return number


def _open_when_ready(url: str) -> None:
    """Open the browser only after the API has started answering."""
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f'{url}/api/health', timeout=1) as res:
                if res.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            pass
        time.sleep(0.2)
    print('Browser not opened automatically. Visit: ' + url, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='odoo-explorer',
        description='Explore Odoo 16–19 addons locally in your browser.',
    )
    parser.add_argument('module_path', nargs='?', help='Optional path to an Odoo addon directory')
    parser.add_argument('--port', type=_port, default=DEFAULT_PORT, help='Loopback port (default 7764)')
    parser.add_argument('--no-browser', action='store_true', help='Do not launch a browser')
    parser.add_argument('--version', action='version', version=f'Odoo Module Explorer {APP_VERSION}')
    args = parser.parse_args(argv)

    if args.module_path:
        try:
            resolved = resolve_module_path(args.module_path)
            inspect_module(resolved)
        except AnalysisError as exc:
            parser.error(str(exc))
        os.environ['ODOO_EXPLORER_INITIAL_MODULE'] = str(resolved)
    else:
        os.environ.pop('ODOO_EXPLORER_INITIAL_MODULE', None)

    ui = frontend_directory()
    if ui is None:
        parser.error(
            'Web UI not built. For source checkouts run `npm install` and `npm run build` '
            'inside frontend/, or install a built release wheel.'
        )
    if shutil.which('node') is None:
        print('Warning: Node.js 20+ not found. JavaScript/OWL inspection will be unavailable.', file=sys.stderr)

    url = f'http://127.0.0.1:{args.port}'
    print(f'Odoo Module Explorer {APP_VERSION} — {url}', flush=True)
    print('Press Ctrl+C to stop. The server listens on 127.0.0.1 only.', flush=True)
    if not args.no_browser:
        threading.Thread(target=_open_when_ready, args=(url,), daemon=True).start()
    try:
        uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='info')
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
