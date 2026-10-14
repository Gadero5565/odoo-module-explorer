# Development plan — Odoo Module Explorer

Target Odoo versions: **16, 17, 18, 19**. Standalone local application first; editor plugins later.

| Phase | Scope | Completion criteria |
|---|---|---|
| 1 | Scanner + treemap | Select an addon, see sizes/counts/lines, drill into folders, inspect files, rank and filter, tests pass |
| 2 | Python syntax parser | Click Python files to view nested classes, functions, methods, decorators and sizes |
| 3 | Odoo Python semantics | Detect models and inheritance, fields, computed methods, controller routes, constraints |
| 4 | XML & QWeb | Parse views, records, actions, menus, inheritance and templates |
| 5 | JS & OWL | JS classes, functions, component/template links, services and registrations |
| 6 | SCSS/CSS | Selectors, variables, mixins, rules and file metrics |
| 7 | Advanced exploration | Odoo logical models, cross references, search, additional metrics, graph views |
| 8 | Watch & performance | Incremental rescans, caching, robustness, security regression and performance tests |
| 9 | Packaging | Standalone CLI launcher, bundled frontend, documentation and first release |
| E1 | VS Code extension | Webview, analyze active addon, source jump navigation |
| E2 | PyCharm plugin | Embedded UI, module commands and source navigation |

### Release rule

Do not push a phase before the user runs and accepts it locally. Keep automated checks passing before every commit.

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
