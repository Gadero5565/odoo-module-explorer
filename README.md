# Odoo Module Explorer

A **local, read-only source explorer** for Odoo 16, 17, 18 and 19 addons. Visualize where code lives, inspect implementation details, and navigate relationships without installing or running Odoo.

**Repository:** https://github.com/Gadero5565/odoo-module-explorer

## Features

- **Interactive treemap:** explore addons by directory, file, class, method and source element; sort by source bytes, physical lines or file count where applicable.
- **Python and Odoo models:** class and function structure, inheritance, fields, decorators, computed methods, HTTP routes and ORM method roles.
- **Python visibility controls:** field declarations and residual “Other code / declarations” are hidden in the treemap by default. Enable each category independently from **Display filters**. Visible scope counts, chart areas and rankings update; physical file size and module-wide totals remain unchanged.
- **XML and QWeb:** Odoo records, view declarations, XPath, actions, menus and templates.
- **JavaScript and OWL:** classes, methods, components, hooks, services, imports and registry registrations.
- **SCSS and CSS:** selectors, nested rules, declarations, Sass variables and mixins.
- **Advanced Insights:** global symbol search, logical Odoo model summaries, reference graphs and approximate method complexity rankings.
- **Automatic refresh:** checks local files approximately every four seconds, reuses cached parse results and updates the explorer on changes.
- **Standalone mode:** install a bundled wheel and launch with one `odoo-explorer` command.

The interface is **local-only** and scans the module directory you supply. It does not execute addon Python or JavaScript, run Odoo, read an Odoo database, or upload source files to a cloud service.

## Requirements

- Python **3.10 or newer** (the project targets Python 3.10–3.13).
- Node.js **20.19+ or 22.12+** and npm to build the frontend.
- Node.js at runtime **only** for JavaScript/OWL inspection. Python, XML and stylesheet inspection do not use Node.
- Windows, Linux or macOS. Windows PowerShell examples follow; other platforms can use the equivalent shell commands.

## Quick start (source checkout)

Clone the repository and start from its root:

```powershell
# Terminal 1: backend
cd backend
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 7764
```

```powershell
# Terminal 2: frontend (from repository root)
cd frontend
npm install
npm run dev
```

Navigate to **http://127.0.0.1:5173** and enter the path of a local addon, for example:

```text
C:\odoo\custom_addons\my_addon
```

Choose **Explore sample module** to try the bundled synthetic example.

## Build and run the standalone application

From the repository root:

```powershell
python -m pip install --upgrade setuptools wheel
python scripts/build_release.py
.\scripts\install_release.ps1 -Version 3.10
.\.release-venv\Scripts\odoo-explorer.exe "C:\odoo\custom_addons\my_addon"
```

The installed app opens at **http://127.0.0.1:7764**, with no separate frontend dev server. Options include `--no-browser`, `--port 17764`, and `--version`.

See [docs/RELEASING.md](docs/RELEASING.md) for build verification and distribution details.

## Using the Python treemap filters

While viewing a Python file, class or method, open **Display filters** (the sliders icon):

| Option | Initial state | Effect |
| --- | --- | --- |
| Show Odoo field declarations | Off | Displays individual `fields.*` declarations in the treemap, rankings and member list. |
| Show other code / declarations | Off | Displays synthetic residual source sections (imports, unmatched declarations, method body lines outside nested definitions). |

The count and size shown for the **current treemap scope** reflect the visible nodes. Hidden source is not deleted or ignored by the analyzer. Class/file inspector physical sizes and the four top-level module statistics continue to describe the complete scanned source. The Advanced Insights index retains all symbols, including those hidden in the treemap.

## Tests

```powershell
# From backend/
python -m pytest -q

# From frontend/
npm test
npm run build
```

A synthetic sample addon is included at `samples/demo_odoo_module/`. No real company addon or proprietary source is bundled.

## Security and limitations

- The server binds to `127.0.0.1`; **do not expose it to a public interface**.
- All findings are static. Dynamic field creation, the final Odoo model registry, full cross-addon resolution and compiled web asset sizes may require a running Odoo environment and are not claimed here.
- Approximate complexity is a source heuristic, not a complete runtime code quality assessment.
- Parser limits, ignored directories, and warnings can lead to partial analysis; check UI warnings before drawing conclusions.
- The source code is provided for local analysis; review permissions and privacy policies before using it with confidential company code.

## Project layout

```text
backend/    FastAPI server, read-only source parsers and CLI
frontend/   React, TypeScript, ECharts and UI tests
samples/    Synthetic example Odoo addon
scripts/    Developer setup, release build and benchmarking tools
docs/       Release and developer guidance
```

See [CHANGELOG.md](CHANGELOG.md) for user-facing changes. Contributions are welcome through issues and pull requests; see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Licensing

No project-wide license has been selected yet. The TypeScript parser dependency is distributed with its own upstream license. Please add an explicit project license before public redistribution.
