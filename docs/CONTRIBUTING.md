# Contributing to Odoo Module Explorer

Contributions, bug reports, tests and documentation improvements are welcome. Please check existing issues before proposing a major change.

## Development environment

See **[Build from source](INSTALLATION.md#build-from-source)** for the complete setup and the correct command order: install frontend dependencies with `npm ci` before running backend tests that exercise JavaScript analysis.

Required for development: Python 3.10–3.13, Node.js 20.19+ or 22.12+ with npm, Git, and an isolated Python environment.

## Validation

Run these checks before opening a pull request:

```powershell
# In frontend/
npm ci
npm test
npm run build
```

```powershell
# In backend/ after frontend npm ci
python -m pytest -q
python -m ruff check app tests
```

## Code and security practices

- Keep source analysis read-only. Parsers must not import or execute code from addons under inspection.
- Preserve physical source byte counts independently from treemap display filters.
- Include regression tests with representative Odoo 16–19 source fixtures when changing parsers.
- Keep analysis size limits, warnings, and path validation explicit.
- Do not submit proprietary addons, secrets, real company data, or production database dumps; use synthetic samples instead.

## Pull requests

Describe the behavior you are changing, the tests performed and any user-visible limitations. Submit changes against `main` through a pull request. Code contributions are accepted under the project's [LGPL-3.0-only license](../LICENSE).
