# Development plan — Odoo Module Explorer

Target Odoo versions: **16, 17, 18, 19**. Standalone local application first; editor plugins later.

| Phase | Scope | Completion criteria |
|---|---|---|
| 1 | Scanner + treemap | Select an addon, see sizes/counts/lines, drill into folders, inspect files, rank and filter, tests pass |
| 2 | Python syntax parser | Click Python files to view nested classes, functions, methods, decorators and sizes |
| 3 | Odoo Python semantics | Detect models and inheritance, fields, computed methods, controller routes, constraints; **accepted and pushed** |
| 4 | XML & QWeb | Parse views, records, actions, menus, inheritance, XPath, and QWeb templates; **accepted and pushed** |
| 5 | JS & OWL | JS classes, functions, OWL template references, hooks, services, and registry declarations; **accepted and pushed** |
| 6 | SCSS/CSS | Selectors, variables, mixins, rules and file metrics; **accepted and pushed** |
| 7 | Advanced exploration | Global source search, logical model grouping, static model relationships/graph, source jump, ranking by size/lines/complexity; **ready for local acceptance** |
| 8 | Watch & performance | Incremental rescans, caching, robustness, security regression and performance tests |
| 9 | Packaging | Standalone CLI launcher, bundled frontend, documentation and first release |
| E1 | VS Code extension | Webview, analyze active addon, source jump navigation |
| E2 | PyCharm plugin | Embedded UI, module commands and source navigation |

### Release rule

Do not push a phase before the user runs and accepts it locally. Keep automated checks passing before every commit.

### Phase 7 manual acceptance checklist

- [ ] Open the sample addon, choose **Advanced Insights**, and confirm indexed symbols and Odoo model counts.
- [ ] Global search locates Odoo fields, methods, XML views, JS/OWL and SCSS; filters work across kinds and model associations.
- [ ] Click a search result from a nested method/field/template: the file explorer opens at the correct source location and the appropriate inspector updates.
- [ ] In **Odoo models**, verify definition/extension grouping, fields, methods, views and actions for `demo.calendar.edition` and `demo.calendar.day`.
- [ ] Check relation graph and source edges; external targets are visibly unresolved (not assumed installed).
- [ ] Rank by bytes, lines and approximate Python method complexity; verify metric semantics.
- [ ] Analyze real `demo_odoo_module`, test malformed source and limits, recheck all previous functionality.
- [ ] Backend `pytest -q`, frontend `npm test` and `npm run build` on Windows pass; commit/push **after approval**.

### Phase 6 manual acceptance checklist

- [ ] Open sample `calendar_widget.scss` and verify `$calendar-accent`, `$calendar-radius`, the `@mixin` and `@include` nodes.
- [ ] Drill into `.o_calendar_widget`, `&:hover`, media rules and declarations, confirming source bytes/lines and breadcrumbs.
- [ ] Open `calendar_print.css` and verify `:root`, `@media print`, custom property and `!important` declarations.
- [ ] Inspect real SCSS source in `demo_odoo_module`, checking nested syntax/interpolation and no unintended parse failures.
- [ ] Verify syntax errors preserve the original file's byte and line totals.
- [ ] Regression-check Python, Odoo fields, XML/QWeb and JS/OWL navigation.
- [ ] Run backend `pytest -q`, frontend `npm test` and `npm run build` on Windows.
- [ ] Push Phase 6 to `main` **only after approval**.

### Phase 5 manual acceptance checklist

- [ ] Open sample JS `static/src/components/calendar_widget/calendar_widget.js`; verify `CalendarWidget`, template `demo.CalendarWidget`, setup hooks, and action registration.
- [ ] Drill into class/methods and confirm Size / Lines metrics, exact bytes, and breadcrumbs.
- [ ] Open `static/src/services/calendar_state.js`; verify service, dependencies, `start()` and registry key.
- [ ] Test real `demo_odoo_module` OWL JS components and confirm reasonable parsing.
- [ ] Test malformed JS, file path validation, and previous Python/XML behavior.
- [ ] Run backend `pytest -q`, frontend `npm test`, and `npm run build` locally.
- [ ] Push to `main` **only after approval**.

### Phase 4 manual acceptance checklist

- [ ] Open `views/calendar_extended.xml` in the sample module and drill into its `<odoo>` / `<data>` hierarchy.
- [ ] Find `view_demo_calendar_edition_list`: verify model `demo.calendar.edition` and view type `list`.
- [ ] Find `view_demo_calendar_edition_form_extend`: verify `inherit_id` and XPath `//field[@name='year']` with `position=after`.
- [ ] Find `action_demo_calendar_edition`: verify action model `ir.actions.act_window` and target `demo.calendar.edition`.
- [ ] Find `menu_demo_calendar_editions`: verify parent menu and action reference.
- [ ] Open `static/src/components/calendar_widget/calendar_widget_extension.xml` and inspect QWeb `t-name`, `t-inherit`, and XPath attributes.
- [ ] Analyze a real Odoo 16–19 module XML file (e.g. `demo_odoo_module/views/calendar_edition_views.xml`) and test Size / Lines, drill-down, and breadcrumbs.
- [ ] Verify Python/Odoo inspections still work; run `pytest -q` and `npm test && npm run build`.

### Phase 3 manual acceptance checklist

- [ ] Open sample `models/calendar_edition.py`, inspect its Odoo model metadata and 4 field nodes.
- [ ] Inspect `name` (Char/required), `day_ids` (One2many comodel) and `day_count` (computed field).
- [ ] Inspect `_compute_day_count` (@api.depends) and `action_publish` (business action).
- [ ] Open `controllers/preview.py`, inspect the HTTP controller and route metadata.
- [ ] Inspect real `demo_odoo_module/models/calendar_edition.py` and `calendar_import.py`.
- [ ] Verify `Other code` and child symbols still add up to exact physical file and class totals.
- [ ] Check breadcrumb return, Size/Lines switching, search, and non-Python file selection.
- [ ] Confirm the frontend build locally and backend tests pass.

### Phase 2 manual acceptance checklist

- [ ] Open the sample addon and select `models/calendar_edition.py`.
- [ ] Verify the Python file treemap shows its class and/or functions ordered by physical span size.
- [ ] Click the class rectangle to drill down into methods (including `Other code / declarations`).
- [ ] Click a method; verify its decorators (if any), parameters and exact line range in Inspector.
- [ ] Use breadcrumbs to return from method → class → file → parent folder.
- [ ] Switch Size / Lines while viewing symbols; verify `Files` is hidden in Python mode.
- [ ] Analyze real `demo_odoo_module/models/calendar_import.py` (large file), then `calendar_edition.py`.
- [ ] Verify opening a non-Python XML/JS file retains Phase 1 behavior.
- [ ] Edit a Python file then click **Rescan** and reopen it; verify changes appear.
- [ ] Run backend `pytest` and frontend `npm test && npm run build` locally.

### Phase 1 manual acceptance checklist

- [ ] Start both servers on Windows and open http://127.0.0.1:5173
- [ ] Click **Explore sample module**; verify folders, files, and totals are shown
- [ ] Click `models/` in treemap; verify `calendar_edition.py` and `calendar_day.py` appear
- [ ] Click a Python file; verify inspector shows accurate byte size and physical line count
- [ ] Navigate back using the breadcrumb or folder navigator
- [ ] Analyze a real Odoo 16–19 addon (e.g. `demo_odoo_module`)
- [ ] Switch Size / Files / Lines and verify changes in ordering and weights
- [ ] Search a file by name and navigate to it
- [ ] Enable Source only and Hide data/demo/i18n; verify the source statistics and visible treemap are consistent
- [ ] Try a nonexistent path; verify friendly error message
- [ ] Modify a file, click **Rescan**, and verify size changes
- [ ] Run `pytest` and `npm run build`
