# Odoo Module Explorer

A local, **read-only** explorer for Odoo addons (Odoo **16, 17, 18, 19**). Python / FastAPI backend and React / TypeScript / Apache ECharts frontend.

**Phase 1 (accepted):** Treemap for folders/files, byte sizes, file counts, physical source lines, filters, ranked items, search, and breadcrumbs.

**Phase 2 (accepted):** Click a `.py` file to inspect its **classes, functions, methods, nested functions, async definitions, decorators, function parameter names, line ranges, and physical source sizes**. All symbol trees are produced by Python `ast` without running any addon code. Classes and functions drill down just like directories; breadcrumbs navigate back up. Phase 2 source-size partitioning remains intact.

**Phase 3 (accepted):** AST-only Odoo 16–19 model and controller semantics. Classes expose model kinds (`Model`, `TransientModel`, `AbstractModel`, `Controller`), literal `_name` / `_inherit` / `_inherits` / `_description`, counts of direct field declarations, and categorized methods. Odoo fields are individually clickable treemap nodes showing their types, relations, compute/inverse/search/related metadata and literal boolean attributes. Methods show computed-field dependencies, onchange/constraint fields, CRUD overrides, and HTTP route metadata. The analyzer remains read-only and **does not import or run Odoo**.

**Phase 4 (ready for local testing):** Click any `.xml` file to explore its element hierarchy in the same treemap. Detects Odoo `record` definitions, views (`ir.ui.view`, target model, `inherit_id`, view type), actions, menus, field references, XPath expressions and positions, plus QWeb/OWL `t-name`, `t-inherit`, `t-inherit-mode`, `t-call`, and template attributes. Each node includes source line references, exact byte size and an inspector. Malformed XML is isolated to the selected file. **No Odoo or JavaScript is executed; DTD/entity declarations and network access are blocked.**

## Requirements

- Python **3.10+** with pip (backend tests verified on Python 3.13; CI targets 3.10–3.13)
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
- Click an **XML file** (`views/*.xml`, `data/*.xml`, or `static/src/**/*.xml`) to explore elements and records; navigate from `<odoo>` and `<data>` down to views, XML fields, XPath expressions and QWeb templates. Click any node to inspect its attributes and source location. This is source-level visualization, not a resolved Odoo view inheritance graph.
- **Rescan** recalculates physical files and resets Python and XML symbol inspection. Reopen the file to inspect updated definitions.

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
- `POST /api/xml/inspect` — `{"module_path": "C:\\...\\addon", "relative_path": "views/calendar_extended.xml", "version_override": null}`

Swagger: **http://127.0.0.1:7764/docs**.

## Source metrics and caveats

- Folder/file sizes are **raw physical bytes**, not compression, compiled bundles, or runtime memory usage.
- Python symbols use inclusive **physical line spans**, with decorator lines included. Code outside nested definitions is grouped into *Other code* rather than double-counted. These are not cyclomatic complexity, logical LOC, or statement counts.
- Python/XML inspection has a **4 MiB per-file limit**, rejects path traversal/symlinks, and does not open file paths outside the chosen addon. Syntax errors return a warning and preserve file-level totals. Python encoding declarations and CRLF are supported.
- Odoo model identities are inferred from **direct Odoo base classes only**, not from the runtime registry. A class extending an Odoo model using `_inherit` has no new `_name` unless explicitly declared; we show its inheritance metadata. Delegated inheritance comes from literal `_inherits` dictionaries. Unresolved/dynamic expressions remain unknown (their source expression may be displayed), not guesses.
- Fields are detected from **direct class-level** `fields.Type(...)` assignments of known Odoo types. Dynamically generated fields, conditional class declarations and additions from other installed addons are not resolved. Python files using syntax newer than the analyzer interpreter may report syntax errors; Python 3.10 runs are supported for this phase.
- The method role is a useful static classification **based on names and decorators**, not proof of effective Odoo behavior. HTTP route properties are recorded only when statically literal; no actual route registration is performed.
- XML element **byte sizes partition exactly** with `Other XML / text` representing comments, whitespace and raw content not assigned to nested elements. XML element **line counts can overlap** when nested tags touch the same physical line; line-mode treemap areas are approximate and are not additive. The file-level line count remains exact.
- XML parsing uses lxml with a strict, no-network configuration plus expat for byte offsets; external entities, DTDs and excessive nesting/element counts are rejected. The parser does not execute QWeb logic, load view inheritance from other modules, or resolve XML references against a database.
- `.git`, caches, virtualenvs, generated distributions and symlink entries are ignored. The backend is intended to run only on your computer; keep it bound to `127.0.0.1`.
- No network communication or analytics are used for scanning. The module's code is **never executed**.

## Phase 4 manual acceptance

1. Launch the demo addon. Open `views/calendar_extended.xml`, drill down through `odoo → data`, and verify two views, one action, two menus and the XPath.
2. Select `view_demo_calendar_edition_form_extend`: verify model/inheritance reference; select its `xpath` child to see expression and `position="after"`.
3. Select `action_demo_calendar_edition` and `menu_demo_calendar_editions`: verify target model, parent menu, and action reference.
4. Inspect `static/src/components/calendar_widget/calendar_widget_extension.xml`: verify QWeb name, inheritance mode, and XPath details.
5. Select a real module XML file such as `demo_odoo_module/views/calendar_edition_views.xml` and verify treemap drill-down, byte totals, breadcrumb navigation, Size/Lines switching, and inspector.
6. Recheck a Python Odoo class and a method from Phase 3. Run the backend and frontend tests; on Windows, run `npm run build` as the full UI compile check.
7. If you have any XML parsing issue, share the error, XML pattern and Odoo version; the scanner will preserve file totals even when parsing fails.

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
