# Odoo Module Explorer

A local, **read-only** explorer for Odoo addons (Odoo **16, 17, 18, 19**). Python / FastAPI backend and React / TypeScript / Apache ECharts frontend.

**Phase 1 (accepted):** Treemap for folders/files, byte sizes, file counts, physical source lines, filters, ranked items, search, and breadcrumbs.

**Phase 2 (accepted):** Click a `.py` file to inspect its **classes, functions, methods, nested functions, async definitions, decorators, function parameter names, line ranges, and physical source sizes**. All symbol trees are produced by Python `ast` without running any addon code. Classes and functions drill down just like directories; breadcrumbs navigate back up. Phase 2 source-size partitioning remains intact.

**Phase 3 (ready for local testing):** AST-only Odoo 16–19 model and controller semantics. Classes expose model kinds (`Model`, `TransientModel`, `AbstractModel`, `Controller`), literal `_name` / `_inherit` / `_inherits` / `_description`, counts of direct field declarations, and categorized methods. Odoo fields are individually clickable treemap nodes showing their types, relations, compute/inverse/search/related metadata and literal boolean attributes. Methods show computed-field dependencies, onchange/constraint fields, CRUD overrides, and HTTP route metadata. The analyzer remains read-only and **does not import or run Odoo**.

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
- Click a **class** to show its methods and, when it is an Odoo model, its **field declarations**; click a **field** to inspect its type, comodel, compute/default details, and literal attributes.
- Select a **method** to see detected compute/onchange/constraint/action/ORM roles; select the bundled `controllers/preview.py` to inspect a controller route.
- The synthetic gray **Other code / declarations** region represents imports, model metadata assignments and miscellaneous statements outside child definitions and recognized field declarations. It ensures child byte and line totals exactly partition the parent.
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
- Odoo model identities are inferred from **direct Odoo base classes only**, not from the runtime registry. A class extending an Odoo model using `_inherit` has no new `_name` unless explicitly declared; we show its inheritance metadata. Delegated inheritance comes from literal `_inherits` dictionaries. Unresolved/dynamic expressions remain unknown (their source expression may be displayed), not guesses.
- Fields are detected from **direct class-level** `fields.Type(...)` assignments of known Odoo types. Dynamically generated fields, conditional class declarations and additions from other installed addons are not resolved. Python files using syntax newer than the analyzer interpreter may report syntax errors; Python 3.10 runs are supported for this phase.
- The method role is a useful static classification **based on names and decorators**, not proof of effective Odoo behavior. HTTP route properties are recorded only when statically literal; no actual route registration is performed.
- `.git`, caches, virtualenvs, generated distributions and symlink entries are ignored. The backend is intended to run only on your computer; keep it bound to `127.0.0.1`.
- No network communication or analytics are used for scanning. The module's code is **never executed**.

## Phase 3 manual acceptance

1. Open the sample addon, then `models/calendar_edition.py`: verify four field nodes appear when opening `CalendarEdition`.
2. Click `name`, `day_ids`, and `day_count` and inspect their field types, relation, required, and compute metadata.
3. Click `_compute_day_count`: verify role `compute` and dependency `day_ids`; click `action_publish`: verify `business action`.
4. Open sample `controllers/preview.py`, click its class and route method, and verify `/demo/calendar/preview`, `auth=user`, `type=http`.
5. Open your `demo_odoo_module/models/calendar_edition.py` and `calendar_import.py`, checking inheritance and field lists, without any Odoo server running.
6. Check Size / Lines treemaps and breadcrumb navigation and ensure total bytes/lines remain consistent.
7. Verify XML/JS files still behave as in Phase 1, and ordinary Python classes as in Phase 2.
8. Run backend `pytest -q` and frontend `npm test && npm run build` locally.

## Repository workflow

Local development → your Windows acceptance testing → **push only an accepted phase** to `main`.

Repository: https://github.com/Gadero5565/odoo-module-explorer

Detailed plan and test checklist: [docs/ROADMAP.md](docs/ROADMAP.md).
