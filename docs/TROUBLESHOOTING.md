# Odoo Module Explorer troubleshooting

## Backend tests say `TypeScript parser missing`

When building from source, the JavaScript analyzer reads the TypeScript parser from `frontend/node_modules`. Run `npm ci` in `frontend/` **before** the backend tests:

```powershell
cd frontend
npm ci
Test-Path '.\node_modules\typescript\lib\typescript.js'  # True
cd ..\backend
python -m pytest -q
```

A prebuilt wheel already includes this parser; installed-wheel users do not need npm.

## `npm` or `npm.cmd` cannot be found on Windows

Install a supported Node.js version, reopen PowerShell and check:

```powershell
node --version
npm --version
where.exe npm
```

The release build script invokes `npm.cmd` on Windows. If the command remains missing, check that Node.js is in your PATH.

## PowerShell cannot find the `release` directory

Relative paths such as `./release/*.whl` depend on the shell's current folder. Use the absolute path of your checkout or a `Get-ChildItem` result:

```powershell
$RepoRoot = 'C:\path\to\odoo-module-explorer'
$Wheel = Get-ChildItem -Path (Join-Path $RepoRoot 'release') -Filter '*.whl' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Wheel) { throw 'Build a wheel first.' }
$Wheel.FullName
```

## `odoo-explorer` is not recognized

Run the executable from the virtual environment in which you installed the package:

```powershell
& "$env:USERPROFILE\OdooModuleExplorer\.venv\Scripts\odoo-explorer.exe" --version
```

## The browser says the web UI is not built

Running the CLI from an unbuilt source checkout does not produce a compiled UI. Follow [Build from source](INSTALLATION.md#build-from-source) and install the resulting wheel, or use a published prebuilt wheel.

## The addon directory is rejected

Select a directory containing `__manifest__.py`, not the parent addons folder or a single source file. Paths containing spaces should be quoted. The supported Odoo versions are 16–19.

## Port 7764 is already in use

Start the application with `--port 17764` and open `http://127.0.0.1:17764`.

## JavaScript analysis fails in a wheel installation

The wheel includes the TypeScript parser, but JavaScript analysis needs the `node` executable installed locally. Check `node --version` in a new terminal.

## Reporting an issue

Include your OS, Python and Node.js versions, `odoo-explorer --version`, the command you ran, and a sanitized error message. Do not upload private addon source or confidential information.
