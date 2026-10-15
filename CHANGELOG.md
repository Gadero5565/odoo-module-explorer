
# Changelog

All notable user-facing changes to Odoo Module Explorer are documented here. The project uses semantic versions.

## Unreleased

## 0.1.0 - 2026-10-15

Initial public release.

### Added

- Local, read-only static analysis of Odoo 16–19 addons without requiring an Odoo server or database.
- Interactive React treemap with file sizes, line counts, and file statistics.
- Python model, field, method, controller, and ORM structure inspection.
- XML/QWeb, JavaScript/OWL, and CSS/SCSS structural inspection.
- Global symbol search and static Odoo model relationship visualization.
- Incremental analysis caching and automatic refresh.
- Standalone command-line launcher with bundled frontend and example addon.
- Odoo Source and All Files analysis profiles with path-aware exclusions.
- Application SVG and ICO favicons.
- Installation, usage, troubleshooting, and contributor documentation.
- Product screenshots and application relaunch instructions.

### Improved

- Hide Odoo field and residual declaration nodes in Python treemaps by default, with independent visibility controls.
- Exclude recognized third-party libraries and description assets from Odoo Source analysis to improve focus and performance.
- Preserve physical file exploration using the All Files profile.
- Provide consistent analysis-profile behavior across scanning, statistics, insights, and refresh.
- Support reproducible standalone wheel builds and independent installation.
- Apply LGPL-3.0-only project licensing and include license files in distributions.

### Security

- Upgrade Apache ECharts to 6.1.0 to address a moderate-severity cross-site scripting advisory.
