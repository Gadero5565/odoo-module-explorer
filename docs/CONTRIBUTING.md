# Contributing

Thank you for improving Odoo Module Explorer. Please open an issue describing a bug or enhancement before a large change.

## Local development

Use Python 3.10+ and Node.js 20+; see the root README for backend and frontend commands. Keep parsers static and read-only: never import or execute analyzed addon code. Preserve accurate physical byte totals independently from display filtering, and provide test fixtures for Odoo 16–19 semantics when adding language features.

Run `python -m pytest -q` from `backend/` and `npm test && npm run build` from `frontend/` before submitting a pull request.

Do not submit private company addons, proprietary source files, API credentials, or production database dumps. Prefer minimal synthetic samples in `samples/` or test fixtures.
