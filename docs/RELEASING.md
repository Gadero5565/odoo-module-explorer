# Building and verifying a release

This guide describes repeatable release verification for Odoo Module Explorer.

## Prerequisites

- Python 3.10+ with pip, setuptools and wheel
- Node.js 20.19+ or 22.12+ with npm
- A clean checkout with the frontend package lockfile tracked when available
- Network access to install dependencies during a fresh build

## Windows release verification

Run these commands from the repository root:

```powershell
python -m pip install --upgrade setuptools wheel
python scripts/build_release.py
.\scripts\install_release.ps1 -Version 3.10
.\.release-venv\Scripts\odoo-explorer.exe --version
.\.release-venv\Scripts\odoo-explorer.exe --no-browser --port 17764 "C:\odoo\custom_addons\my_addon"
```

Open `http://127.0.0.1:17764` and verify: local path selection, treemap navigation, Python visibility filters, XML/QWeb and JavaScript/OWL drill-down, stylesheet inspection, Advanced Insights, and automatic refresh.

For a standalone package, ensure JavaScript inspection works **without a running Vite server or `frontend/node_modules`**. The Node.js executable must still be available.

Run the automated checks:

```powershell
python -m pytest backend/tests -q
npm test --prefix frontend
npm run build --prefix frontend
```

Check the wheel artifact at `release/odoo_module_explorer_backend-*.whl`. The GitHub Actions workflow `.github/workflows/release-wheel.yml` creates a build artifact on manual dispatch or version-tag pushes. It does not automatically publish to PyPI.

The distribution should contain the compiled UI, licensed TypeScript parser, example addon and CLI entry point. Never check in `.release-venv`, `node_modules`, `frontend/dist`, build artifacts, or staged wheel assets.

## Known limitations

- The wheel must be assembled on a machine with npm packages available.
- Installing Python dependencies generally needs a package index unless offline wheels are prepared.
- JavaScript analysis needs Node.js at runtime.
- Static analysis does not assemble an Odoo registry or calculate runtime bundle sizes.
- The server is intended for local use only.

## Publication

Publish a tagged GitHub Release only after a fresh-install smoke test. Choose a project-wide license before public redistribution and retain third-party license notices.
