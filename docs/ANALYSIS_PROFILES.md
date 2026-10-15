# Analysis profiles

Odoo Module Explorer defaults to **Odoo Source**, a focused view of addon-authored files.
Switch the **Analysis profile** selector to **All Files** to inspect the physical addon tree.
Changing the profile triggers a new local backend scan; neither mode changes addon files.

| Behavior | Odoo Source (default) | All Files |
| --- | --- | --- |
| Odoo authored source and normal assets | Included | Included |
| `static/lib/` and `static/src/lib/` vendor directories | Excluded from scanning | Included in size and file metrics |
| `static/description/`, root `description/` | Excluded from scanning | Included |
| `*.min.js`, `*.min.css`, `*.js.map`, `*.css.map` | Excluded from scanning | Included |
| Author-defined top-level `lib/` with Python code | Included | Included |
| Advanced Insights | Excludes recognized vendor assets | Still excludes recognized vendor assets |
| Auto-refresh | Only changes to analyzed files trigger updates | Changes to included vendor assets also trigger updates |

The size, file, folder and source-line cards describe **the selected profile**, not
an estimate of the full on-disk size when Odoo Source is selected. "Excluded
paths" counts top-level exclusions (an excluded directory counts as one path,
not every descendant). The global semantic index avoids recognized vendor
bundles in both profiles so it is focused on application source. You can open
a single vendor JS file in All Files when it fits the normal parser size limit.

Both modes always exclude machine caches (`node_modules`, `.git`, `dist`, etc.)
and symlinks for safety. "All Files" means all **eligible addon files**, not
machine-generated dependencies or external linked locations.

For performance on very large modules, leave the profile set to Odoo Source.
The initial scan of All Files may take longer, especially when line counting
large third-party JavaScript bundles; repeated scans reuse cached line counts.
