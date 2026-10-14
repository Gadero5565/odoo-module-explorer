# Odoo Module Explorer

A local, **read-only** explorer for Odoo addons (Odoo **16, 17, 18, 19**). Python / FastAPI backend and React / TypeScript / Apache ECharts frontend.

**Phase 1 (accepted):** Treemap for folders/files, byte sizes, file counts, physical source lines, filters, ranked items, search, and breadcrumbs.

**Phase 2 (ready for local testing):** Click a `.py` file to inspect its **classes, functions, methods, nested functions, async definitions, decorators, function parameter names, line ranges, and physical source sizes**. All symbol trees are produced by Python `ast` without running any addon code. Classes and functions drill down just like directories; breadcrumbs navigate back up. No Odoo-specific field or model interpretation yet (Phase 3).

## Requirements

- Python **3.10+** with pip (tested here on Python 3.13; CI matrix configured for 3.10–3.13)
- Node.js **20.19+ or 22.12+**, npm
- Windows 10/11; Linux/macOS using equivalent shell commands
- A real addon containing `__manifest__.py` and `__init__.py`, or the included sample addon
- **No running Odoo server or database required**

## Run locally on Windows (PowerShell)

Unzip, open two terminals in the project folder. If you already installed Phase 1, you can keep the existing `.venv` and skip its creation. Copy only the new source project files over your old project, leaving `node_modules` and `.venv` untouched.

**Terminal 1 — Backend:**

```powershell
cd backend
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 7764
```

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` and `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 7764` without activating.

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm install
npm run dev
```

Go to **http://127.0.0.1:5173**. Enter the absolute addon path or click **Explore sample module**.

- Click a **folder** to show its children (Phase 1).
- Click any **Python file** in the explorer, treemap, or rank list. The UI requests the Python structure lazily, only for the selected file.
- Click a **class** to show its methods; click a **method** to inspect decorators, parameters, byte size and line range.
- The synthetic gray **Other code / declarations** region represents import lines, Odoo field declarations and miscellaneous statements not contained in child definitions. It ensures child byte and line totals exactly partition the parent.
- Use breadcrumbs to return to any parent scope. When exploring Python symbols, the **Files** metric is hidden because file count is not a meaningful symbol-level measurement.
- **Rescan** recalculates physical files and resets Python symbol inspection. Reopen the file to inspect updated definitions.

## Production-like single-server run

After npm installation, in `frontend/` run `npm run build`. Start FastAPI on `127.0.0.1:7764` and open **http://127.0.0.1:7764**. The backend serves the built React app if `frontend/dist/` exists.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m ruff check app tests
```

```powershell
cd frontend
npm test
npm run build
```

**API endpoints:**

- `GET /api/health` — backend status
- `GET /api/config` — bundled sample path and allowed Odoo versions
- `POST /api/analyze` — `{"module_path": "C:\\...\\addon", "version_override": null}`
- `POST /api/python/inspect` — `{"module_path": "C:\\...\\addon", "relative_path": "models/calendar_edition.py", "version_override": null}`

Swagger: **http://127.0.0.1:7764/docs**.

## Source metrics and caveats

- Folder/file sizes are **raw physical bytes**, not compression, compiled bundles, or runtime memory usage.
- Python symbols use inclusive **physical line spans**, with decorator lines included. Code outside nested definitions is grouped into *Other code* rather than double-counted. These are not cyclomatic complexity, logical LOC, or statement counts.
- Source inspection has a **4 MiB file limit**, rejects path traversal/symlinks, and does not open file paths outside the chosen addon. Syntax errors return a warning and preserve file-level totals. Python encoding declarations and CRLF are supported.
- Python AST doesn't fully understand dynamically generated classes, monkeypatching, or Odoo registry semantics. Phase 3 will add Odoo-aware interpretation; functions defined only at runtime remain out of scope.
- `.git`, caches, virtualenvs, generated distributions and symlink entries are ignored. The backend is intended to run only on your computer; keep it bound to `127.0.0.1`.
- No network communication or analytics are used for scanning. The module's code is **never executed**.

## Repository workflow

Local development → your Windows acceptance testing → **push only an accepted phase** to `main`.

Repository: https://github.com/Gadero5565/odoo-module-explorer

Detailed plan and test checklist: [docs/ROADMAP.md](docs/ROADMAP.md).
