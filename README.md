# Odoo Module Explorer

A local, **read-only** explorer for Odoo addons (Odoo **16, 17, 18, 19**). Python / FastAPI backend and React / TypeScript / Apache ECharts frontend.

**Phase 1 (accepted):** Treemap for folders/files, byte sizes, file counts, physical source lines, filters, ranked items, search, and breadcrumbs.

**Phase 2 (accepted):** Click a `.py` file to inspect its **classes, functions, methods, nested functions, async definitions, decorators, function parameter names, line ranges, and physical source sizes**. All symbol trees are produced by Python `ast` without running any addon code. Classes and functions drill down just like directories; breadcrumbs navigate back up. Phase 2 source-size partitioning remains intact.

**Phase 3 (accepted):** AST-only Odoo 16–19 model and controller semantics. Classes expose model kinds (`Model`, `TransientModel`, `AbstractModel`, `Controller`), literal `_name` / `_inherit` / `_inherits` / `_description`, counts of direct field declarations, and categorized methods. Odoo fields are individually clickable treemap nodes showing their types, relations, compute/inverse/search/related metadata and literal boolean attributes. Methods show computed-field dependencies, onchange/constraint fields, CRUD overrides, and HTTP route metadata. The analyzer remains read-only and **does not import or run Odoo**.

**Phase 4 (accepted):** Click any `.xml` file to explore its element hierarchy in the same treemap. Detects Odoo `record` definitions, views (`ir.ui.view`, target model, `inherit_id`, view type), actions, menus, field references, XPath expressions and positions, plus QWeb/OWL `t-name`, `t-inherit`, `t-inherit-mode`, `t-call`, and template attributes. Each node includes source line references, exact byte size and an inspector. Malformed XML is isolated to the selected file. **No Odoo or JavaScript is executed; DTD/entity declarations and network access are blocked.**

**Phase 5 (accepted):** Click any `.js` source to inspect JavaScript classes, methods, functions, async/arrow functions, `@odoo-module` imports, OWL component template references, hooks, registry entries, and service dependencies. Phase 5 uses TypeScript's JavaScript parser through a read-only Node.js subprocess; addon code is **never executed**. JavaScript file and nested symbol treemaps have exact additive source-byte sizes, with residual code shown as separate rectangles. The parser reads one `.js` source file lazily, when you select it.

**Phase 6 (accepted):** Click any `.scss` or `.css` file to inspect its nested selectors, ordinary declarations, Sass variables, mixins, functions, includes, CSS at-rules, keyframes, imports/use/forward references, and source line locations. The parser is self-contained Python and never compiles SCSS, executes scripts, or resolves imported files. It handles comments, strings, nested rules, interpolation, UTF-8 and CRLF, and shows residual source rectangles to preserve exact physical bytes. Malformed stylesheets show an inspection warning while preserving file-level totals.

**Phase 7 (ready for local testing):** Open **Advanced Insights** after analyzing an addon. A bounded on-demand index searches symbols across Python, XML/QWeb, JavaScript/OWL and SCSS/CSS. Explore logical Odoo model identities (`_name` and `_inherit`), member fields/methods, XML views/actions, and literal relationship edges with an interactive graph. External model references are explicitly marked as unresolved by this addon. Rank source symbols by bytes, physical lines or **approximate Python method complexity**. Click search results, model members or ranking rows to return to the matching source symbol in the existing file treemap. Indexing remains read-only, in-memory and does not launch Odoo. Index limits produce visible partial-results warnings rather than silently implying completeness.

## Requirements

- Python **3.10+** with pip (backend tests verified on Python 3.13; CI targets 3.10–3.13)
- Node.js **20.19+ or 22.12+**, npm (required for JS inspection as well as the frontend)
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
- **Rescan** recalculates physical files and resets Python, XML, JavaScript, and stylesheet symbol inspections. Reopen the file to inspect updated definitions.
- Click any **JavaScript file** (`static/src/**/*.js`) to explore OWL components, `static template`, `setup()` hooks, nested functions, service definitions and registry `category(...).add(...)` calls. The file inspector lists imports and registrations. Click a class or service to drill into methods.

- Click a **SCSS or CSS file** to inspect selectors, declarations, variables, mixins, functions, includes, media queries, keyframes, and imported stylesheet references. The inspector shows details for any selected node. CSS/SCSS source bytes are partitioned across recognized nodes and gray "Other source / comments" rectangles.
- Click **Advanced Insights** to build a module-wide index. Search for any named class/method/field, select an Odoo model to inspect its local class extensions, fields, methods, views and actions, open the Relationships tab to view its static graph, or rank symbols by bytes, lines and estimated Python complexity. Click a result to return to its original source node. Rescanning resets the index; you can also rebuild it manually.

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
- `POST /api/javascript/inspect` — `{ "module_path": "C:\\...\\addon", "relative_path": "static/src/components/calendar_widget/calendar_widget.js", "version_override": null }`
- `POST /api/styles/inspect` — `{ "module_path": "C:\\...\\addon", "relative_path": "static/src/components/calendar_widget/calendar_widget.scss", "version_override": null }`
- `POST /api/insights` — `{"module_path": "C:\\...\\addon", "version_override": null}`; bounded module-wide symbol and model reference index
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
- CSS/SCSS inspection has a **3 MiB per-file** limit, 20,000-node limit and 96-level nesting limit. CSS at-rules, nested Sass constructs and declarations are analyzed lexically (not Sass-compiled); syntactically ambiguous constructs and runtime/dynamic imports may not be resolved. The reported selectors are source selector blocks, **not** expanded compiled CSS selectors, and import references are displayed but never opened. Source **bytes** are additive; child physical line counts can overlap.
- `.git`, caches, virtualenvs, generated distributions and symlink entries are ignored. The backend is intended to run only on your computer; keep it bound to `127.0.0.1`.
- Phase 7's module-wide index is **built on demand**, scanning at most **500 files**, **24 MiB total read source**, and indexing at most **15,000 symbols** per request. Results report skipped files and warnings; parser failures affect individual files rather than the whole report. Unlike file-level source inspection, this index may take several seconds, particularly for many JS files because each uses a bounded Node parser subprocess. No persistent cache is stored in Phase 7; caching and live refresh belong to Phase 8.
- The Odoo logical model explorer groups extensions of a single literal `_inherit` model name and named models into a single list. References to other addons or dynamically constructed model names cannot be fully resolved. Relations show only statically declared field comodels, inheritance and delegated inheritance; they are **not a runtime registry or full view inheritance graph**. XML model associations come from syntactic metadata. A model referenced but not defined within the addon is marked accordingly.
- Approximate complexity is a syntax-based count of Python decision points, not an exact metric and not a treemap area or performance measurement. Code in separately defined nested functions is not attributed to outer methods. Byte and line rankings may include overlapping logical source spans from nested functions; this does not change the additive physical file treemap.
- No network communication or analytics are used for scanning. The module's code is **never executed**.

## Phase 7 manual acceptance

1. Using your accepted Phase 6 checkout, extract **changes-only ZIP** into the **parent folder** containing `odoo-module-explorer` and replace matching files. Keep `.git`, `.venv`, `node_modules` and your local `frontend/package-lock.json` unchanged. Restart backend and frontend.
2. Open the sample addon; click **Advanced Insights** and let the index finish. Verify the dashboard shows `demo.calendar.edition`, `demo.calendar.day`, their Python fields and methods, XML views, CSS/SCSS selectors, and the JS registry/OWL symbols.
3. Under **Global symbols**, search `day_count`, filter kind `odoo_field`, click the result and verify the correct Python file and field inspector are selected. Then try an XML view and JS class.
4. Under **Odoo models**, inspect `demo.calendar.edition` and verify the declared fields, methods, linked XML views and actions. Verify external references are labeled as *referenced only* when applicable.
5. Under **Relationships**, inspect links from edition → day and use the graph and Source buttons. Internal/external status must reflect definitions present **within this addon**, not installed Odoo modules.
6. Under **Rankings**, switch Bytes, Lines and Complexity. Complexity should apply to Python functions/methods only. Click a ranked method and confirm the source navigation and breadcrumb behavior.
7. Test your real `demo_odoo_module` addon and verify indexing is usable. A large or malformed file should generate a warning instead of failing the entire index. Recheck existing Phases 1–6 features and Python 3.10 compatibility.
8. Run backend `python -m pytest -q`, frontend `npm test`, `npm run build`, and optionally GitHub Actions checks. **Do not push Phase 7 until you accept it locally**.

## Phase 6 manual acceptance

1. From your existing accepted Phase 5 checkout, extract the **changes-only ZIP** over the existing project root (preserve `.git`, `node_modules`, `.venv` and your `frontend/package-lock.json`). No new package dependency is introduced.
2. Launch the sample addon, open `static/src/components/calendar_widget/calendar_widget.scss`. Verify two `$calendar-*` variables, the `calendar-padding` mixin, nested `.o_calendar_widget` and `&:hover` selectors, an `@media` node, two `@include` statements, and their source lines.
3. Click the mixin, nested selector, and media rule; confirm children, byte sizes, selected details, and breadcrumbs. Switch Size/Lines and navigate back to the parent directory.
4. Open `static/src/components/calendar_widget/calendar_print.css`, verify `:root`, `@media print`, `--calendar-border`, declarations and `!important` handling.
5. Analyze real `demo_odoo_module` SCSS files (for example `calendar_designer.scss` or `calendar_regions.scss`), and verify source metrics without importing/compiling Sass.
6. Reopen Python, XML and JavaScript nodes to ensure prior features work. Run `python -m pytest tests -q`, `npm test`, and `npm run build` locally.
7. Invalid CSS/SCSS should report parse errors without changing file totals. Do not treat import references as resolved Odoo assets; that is outside the Phase 6 scope.

## Phase 5 manual acceptance

1. After updating the project, run `npm install` in `frontend/` **before** testing JS inspection. The backend uses this project's installed TypeScript parser; it is not a Python package dependency. Keep Node on your PATH.
2. Analyze the sample addon and open `static/src/components/calendar_widget/calendar_widget.js`. Verify `CalendarWidget` is recognized as an OWL component, `demo.CalendarWidget` is shown as its template, and `setup()` shows `useState` / `onMounted`.
3. Drill into `CalendarWidget` and click `setup` and `formatMonth`; verify exact size and source line ranges, then navigate with breadcrumbs.
4. From the `.js` file inspector, inspect the `@odoo/owl` and `@web/core/registry` imports; click the registered action `demo.calendar_widget`.
5. Open `static/src/services/calendar_state.js`. Check that `calendarStateService` is shown as a service and its `orm`, `notification` dependencies, `start()` method, and `calendar_state` registry entry appear.
6. Analyze real JS in `demo_odoo_module`, including `static/src/components/calendar_designer/calendar_designer.js` and `static/src/layers/calendar_home/calendar_home.js`. Check size ranking, search, navigation, and no reported syntax errors.
7. Verify the Python/Odoo, XML/QWeb and filesystem explorers still work. Run `python -m pytest -q`, `npm test`, and **`npm run build`** locally.
8. JavaScript static analysis covers `.js` in Phase 5; stylesheet structure analysis is added in Phase 6. Cross-file resolution of template names/imports is Phase 7. Incomplete/dynamic registrations or templates may not be resolved. Invalid JS returns a warning and preserves file totals.

## Phase 4 manual acceptance (completed)

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
