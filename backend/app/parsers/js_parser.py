"""Read-only JavaScript/OWL static analyzer using the TypeScript grammar.

We invoke the bundled Node bridge, not addon code. The bridge reads source
through stdin and constructs a syntax tree (never eval/require/import of addon
source). The Node binary and frontend TypeScript dependency must be installed.
"""

import json
import subprocess
from pathlib import Path

from pydantic import ValidationError

from app.schemas.js_inspection import JSInspection

MAX_JS_BYTES = 3 * 1024 * 1024
JS_TIMEOUT_SECONDS = 12
BRIDGE = Path(__file__).with_name('js_ast_bridge.cjs')


class JSInspectionError(ValueError):
    """Missing runtime dependency, parser failure, or invalid source size."""


def inspect_js_source(relative_path: str, data: bytes) -> JSInspection:
    if len(data) > MAX_JS_BYTES:
        raise JSInspectionError('JavaScript file exceeds the 3 MiB analysis limit.')
    try:
        source = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise JSInspectionError('JavaScript source must be UTF-8 encoded.') from exc
    # JS UTF-8 BOM: keep bytes unchanged in the reported total by passing the BOM
    # to the parser as U+FEFF. Node accounts for its physical UTF-8 bytes.
    if data.startswith(b'\xef\xbb\xbf'):
        source = '\ufeff' + source
    try:
        result = subprocess.run(
            ['node', str(BRIDGE), relative_path],
            input=source.encode('utf-8'), capture_output=True,
            timeout=JS_TIMEOUT_SECONDS, check=False,
            cwd=BRIDGE.parent,
        )
    except FileNotFoundError as exc:
        raise JSInspectionError('Node.js not found. Install Node.js 20+ to inspect JavaScript.') from exc
    except subprocess.TimeoutExpired as exc:
        raise JSInspectionError('JavaScript inspection exceeded the 12-second time limit.') from exc
    if result.returncode != 0:
        reason = result.stderr.decode('utf-8', errors='replace').strip()[:500]
        raise JSInspectionError(reason or 'JavaScript static parser failed.')
    try:
        inspection = JSInspection.model_validate(json.loads(result.stdout))
    except (ValueError, ValidationError) as exc:
        raise JSInspectionError('JavaScript parser produced an invalid response.') from exc
    if inspection.file.size_bytes != len(data):
        raise JSInspectionError('JavaScript parser returned inconsistent source byte totals.')
    return inspection
