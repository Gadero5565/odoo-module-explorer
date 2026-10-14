# Release checklist — v0.1.0 candidate (Phase 9)

Phase 9 is **not yet published**. Accept it only after the full build and installed-wheel checks on Windows pass.

## Prerequisites

- Windows PowerShell, Python 3.10–3.13, a virtualenv and pip
- Node.js 20.19+ / 22.12+, npm (for the build and at runtime only for JS/OWL parsing)
- Network for the initial `pip install` / `npm install` dependencies; no Odoo service or database
- A checked-out Git repo containing the **Phase 8 approved files**, including `frontend/package-lock.json` when available

## Build and installed-wheel validation

1. From the project root, run `python -m pip install --upgrade setuptools wheel`.
2. Run `.\scripts\build_release.ps1` (executes npm install/ci, the React production build, then wheel packaging).
3. Verify `release\odoo_module_explorer_backend-0.1.0-py3-none-any.whl` exists.
4. Run `.\scripts\install_release.ps1 -Version 3.10` to install the wheel in a fresh `.release-venv`.
5. Run `.\.release-venv\Scripts\odoo-explorer.exe --version`; expect `0.1.0`.
6. Run `.\.release-venv\Scripts\odoo-explorer.exe --no-browser --port 17764 "C:\path\to\demo_odoo_module"`.
7. Open `http://127.0.0.1:17764` and verify the addon path is pre-filled, then click **Analyze**. Check the treemap, file inspector, global search, model relationships, and auto-refresh.
8. Open `*.js` and confirm OWL metadata works **without a running npm dev server**. The installed wheel must work outside the source checkout, even if `frontend/node_modules` is renamed temporarily. (Keep the Node.js executable available.)
9. Click **Explore sample module** and verify it is present even outside the source checkout.
10. Stop the server with Ctrl+C; verify no port/listener remains running.
11. Verify the original source-dev workflow still works with `npm run dev` + Uvicorn.
12. Run `python -m pytest backend/tests -q`, `npm test --prefix frontend`, and `npm run build --prefix frontend`.
13. Review `.github/workflows/release-wheel.yml` and trigger it manually. Download the wheel artifact and repeat a fresh-install smoke test.

## Git acceptance and release

- Do not commit generated `frontend/dist`, `frontend/node_modules`, `backend/app/web_dist`, `backend/app/vendor/typescript.js`, `backend/app/demo_addon`, or `.release-venv`.
- Commit and push only after testing: `git add . && git commit -m "build: add standalone CLI and bundled release packaging" && git push origin main`.
- The CI workflow builds an artifact; it **does not automatically upload to PyPI or create a GitHub Release**.
- Optional future release: only after a fully tested artifact, tag `v0.1.0` and attach the CI wheel to GitHub Releases manually.
- Decide the project's own open-source license before broad public distribution. The bundled TypeScript parser retains its third-party license.

## Known limitations

- A full release wheel is assembled only on a machine with installed npm packages. The source ZIP alone is not a prebuilt wheel.
- Installing Python dependencies initially needs a package index unless you prepare an offline wheelhouse.
- Node.js is required for JavaScript/OWL analysis; Python, XML, and CSS/SCSS analysis does not require Node.
- Metrics are static approximations; the Odoo ORM registry and compiled asset bundles are not calculated.
- Local server only; not designed for external/public deployment.
