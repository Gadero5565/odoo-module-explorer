# Using Odoo Module Explorer

Odoo Module Explorer inspects one local Odoo addon at a time. It does not need an Odoo service, configuration or database.

## Open a module

Start the installed app with `odoo-explorer` or enter an addon directory in the web interface. The directory must contain `__manifest__.py`. Use **Explore sample module** to try a synthetic example.

## Browse the treemap

Click a folder to inspect its contents; click a supported source file to inspect its internal structure. Breadcrumbs return to parent nodes. Where available, change ranking and area metrics between source bytes, physical lines, symbol counts and complexity estimates.

## Python visibility filters

Python fields and **Other code / declarations** are hidden from the treemap by default. Open **Display filters** and enable either category to include it in the current chart, rankings and visible-scope statistics. The source is still fully analyzed, and physical file-size totals do not change.

## Source languages

- Python: classes, functions, Odoo models, fields, decorators, controllers and ORM method roles.
- XML/QWeb: records, views, menus, actions, XPath and templates.
- JavaScript/OWL: components, methods, hooks, services, imports and registry entries. Node.js must be available on the system for JavaScript inspection.
- CSS/SCSS: selectors, properties, variables, mixins and nested styles.

## Advanced Insights

Use global symbol search and logical model views to locate definitions and view static relationships in the currently analyzed addon. Links to models outside this addon may not be fully resolved.

## Refresh and data handling

Auto-refresh monitors changes to the currently selected addon and updates cached analysis. Nothing is written to the addon by the analyzer. The server runs on localhost, and source is not uploaded to an external service. Stop the app with `Ctrl+C` in its terminal.
