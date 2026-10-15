# Odoo Module Explorer

**Odoo Module Explorer** is a local, read-only code visualization and static analysis tool for **Odoo 16–19 addons**. Explore folder and file sizes, inspect Odoo models and frontend components, and navigate source relationships without an Odoo server or database.

[Installation](docs/INSTALLATION.md) · [Usage](docs/USAGE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Contributing](docs/CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [License](LICENSE)

## Features

- **Interactive treemap:** navigate directories, files, classes, methods and source elements by physical bytes, lines or other applicable metrics.
- **Odoo-aware Python analysis:** models and extensions, fields, methods, decorators, computed fields, controllers and ORM overrides.
- **Focused Python view:** field declarations and residual source code are hidden from the treemap by default; enable either category in Display filters without changing actual file sizes.
- **XML and QWeb:** inspect views, records, menus, actions, XPath and templates.
- **JavaScript and OWL:** inspect classes, components, hooks, services, imports and registry registrations.
- **CSS and SCSS:** navigate selectors, declarations, Sass variables, mixins and nested rules.
- **Advanced Insights:** search source symbols, inspect logical Odoo models and examine static relationships.
- **Refresh:** detect local file changes and reuse cached results.

All analysis runs on your computer. The application does not execute addon Python or JavaScript, install Odoo, query a database or upload your source code to a remote service.

## Install

**If an installable `.whl` file is available in [GitHub Releases](https://github.com/Gadero5565/odoo-module-explorer/releases)**, download it and follow the [prebuilt package installation guide](docs/INSTALLATION.md#install-a-prebuilt-wheel). A wheel is not the same as GitHub's **Code → Download ZIP** source archive.

**To install from source**, follow [Build from source](docs/INSTALLATION.md#build-from-source). This method works without a published Release, but requires Git, Python, Node.js and npm for the build.

The installed application is started from a terminal using its `odoo-explorer` command, which opens a local web interface at `http://127.0.0.1:7764`.

## Requirements

| | Installed wheel | Source build |
| --- | --- | --- |
| Python | 3.10–3.13 targeted | 3.10–3.13 targeted |
| Node.js | Required for JavaScript/OWL inspection | Required for build and JavaScript inspection |
| npm | Not needed | Required |
| Odoo server/database | Not needed | Not needed |

Windows PowerShell commands are provided in the [installation guide](docs/INSTALLATION.md). Node.js **20.19+ or 22.12+** is recommended for the frontend build.

## Usage

Select an addon directory containing `__manifest__.py` (for example, `C:\odoo\custom_addons\my_addon`) or choose **Explore sample module**. The treemap opens folders and files; click supported source symbols for inspection. Use **Display filters** to control visible Python fields and residual code. See [the usage guide](docs/USAGE.md) for more details.

## Security and limitations

- The web server listens on `127.0.0.1` only. Do not expose the local API to a public network.
- Results are based on static source inspection, not a running Odoo registry. Dynamic definitions and references to code outside the selected addon may remain unresolved.
- Asset sizes describe source files rather than compiled/minified browser bundles.
- Very large, malformed or unsupported source files may be skipped; check analyzer warnings.
- Review your organization's rules before analyzing confidential work, and use synthetic or authorized source for public screenshots or bug reports.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development setup and test commands. Please do not submit proprietary addons or credentials.

## License

Copyright © 2026 Gadeer Mahmoud and contributors.

Licensed under the **GNU Lesser General Public License, version 3.0 only** ([LGPL-3.0-only](LICENSE)). The included [GNU GPL v3 text](LICENSES/GPL-3.0-only.txt) forms part of LGPL v3's terms. The bundled TypeScript compiler parser retains its own license notice.
