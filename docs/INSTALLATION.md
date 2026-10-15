# Installation

Odoo Module Explorer is a local application for examining Odoo 16–19 addons. It does not require an Odoo server or database.

Choose the installation method that matches the files you have:

- **[Install a prebuilt wheel](#install-a-prebuilt-wheel)** if an official `.whl` file is available from [GitHub Releases](https://github.com/Gadero5565/odoo-module-explorer/releases).
- **[Build from source](#build-from-source)** if you are developing the project or no wheel has been published.

The commands below are for **Windows PowerShell**. On Linux/macOS, use the equivalent `python3 -m venv`, `python -m pip`, and `<venv>/bin/odoo-explorer` commands.

## Start the application again

**Already installed the application? Skip the installation steps below.** You can reopen Odoo Module Explorer whenever you want by running the executable from the Python virtual environment used during installation. No `npm ci`, backend tests, or rebuild is needed to reopen an installed wheel.

Open **PowerShell** and use the command matching your installation:

**Recommended prebuilt wheel installation** (the default directory created by [Install a prebuilt wheel](#install-a-prebuilt-wheel)):

```powershell
& "$env:USERPROFILE\OdooModuleExplorer\.venv\Scripts\odoo-explorer.exe"
```

**Standalone wheel test installation** (the folder created by [Build from source](#build-from-source)):

```powershell
& "$env:USERPROFILE\OdooExplorerWheelTest\.venv\Scripts\odoo-explorer.exe"
```

**Installed with `scripts/install_release.ps1`** in a repository checkout (run this from that checkout's root):

```powershell
.\.release-venv\Scripts\odoo-explorer.exe
```

You can also use an **absolute path** to that checkout's `.release-venv\Scripts\odoo-explorer.exe` to start it from any directory. If your installation is in a custom location, replace the examples with the real path to its `odoo-explorer.exe`. An activated installation virtual environment also allows the shorter `odoo-explorer` command.

To open a specific addon directly, provide a path containing `__manifest__.py`:

```powershell
& "$env:USERPROFILE\OdooModuleExplorer\.venv\Scripts\odoo-explorer.exe" "C:\odoo\custom_addons\my_addon"
```

The application serves **http://127.0.0.1:7764** and normally opens your browser. **Keep the PowerShell terminal running** during use; close the app with `Ctrl+C`. The URL by itself cannot start a stopped server. If the port is occupied, append `--port 17764` and visit `http://127.0.0.1:17764`.

On Linux/macOS, the equivalent executable is usually `~/OdooModuleExplorer/.venv/bin/odoo-explorer`, or `<your-venv>/bin/odoo-explorer` for a custom installation.

### Optional: create a Windows desktop shortcut

To launch Odoo Module Explorer by double-clicking a shortcut, run the following **once**, after completing the recommended wheel installation:

```powershell
$Explorer = Join-Path $env:USERPROFILE 'OdooModuleExplorer\.venv\Scripts\odoo-explorer.exe'
if (-not (Test-Path $Explorer)) { throw 'Explorer not found. Install the wheel first or set $Explorer to your actual installed executable.' }
$Desktop = [Environment]::GetFolderPath('Desktop')
$Shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $Desktop 'Odoo Module Explorer.lnk'))
$Shortcut.TargetPath = $Explorer
$Shortcut.WorkingDirectory = Split-Path $Explorer -Parent
$Shortcut.Description = 'Launch Odoo Module Explorer locally'
$Shortcut.Save()
```

Afterward, double-click **Odoo Module Explorer** on your desktop. The application still needs its terminal window to remain open. If you move or delete the installation environment, update the shortcut or reinstall the wheel. Do not point the shortcut at the source folder or the `.whl` file.

## Prerequisites

- Python **3.10–3.13** with pip. Commands below use `py -3.10`; substitute an installed compatible version as needed.
- Node.js for **JavaScript/OWL analysis**. The other parsers do not require Node.js at runtime.
- For **building from source**, Git, npm, Node.js **20.19+ or 22.12+**, and an internet connection to install dependencies.

## Install a prebuilt wheel

This method does **not** require Git, frontend dependencies, npm, or a source checkout. It requires a `.whl` release asset; the repository's **Code → Download ZIP** is source code, not an installable wheel.

1. Download `odoo_module_explorer_backend-<version>-py3-none-any.whl` from [GitHub Releases](https://github.com/Gadero5565/odoo-module-explorer/releases) to your `Downloads` folder. If no wheel is listed, use [Build from source](#build-from-source).
2. Open a new PowerShell window and run:

```powershell
$InstallDir = Join-Path $env:USERPROFILE 'OdooModuleExplorer'
$Downloads = Join-Path $env:USERPROFILE 'Downloads'
$Wheel = Get-ChildItem -Path $Downloads -Filter 'odoo_module_explorer_backend-*.whl' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Wheel) { throw "No wheel found in $Downloads. Download a release wheel first." }

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
py -3.10 -m venv (Join-Path $InstallDir '.venv')
$Python = Join-Path $InstallDir '.venv\Scripts\python.exe'
$Explorer = Join-Path $InstallDir '.venv\Scripts\odoo-explorer.exe'
& $Python -m pip install $Wheel.FullName
if ($LASTEXITCODE -ne 0) { throw 'Wheel installation failed.' }
& $Explorer --version
& $Explorer
```

3. Your browser opens at **http://127.0.0.1:7764**. Select **Explore sample module** or supply an addon directory containing `__manifest__.py`.

Run an addon directly:

```powershell
& $Explorer 'C:\odoo\custom_addons\my_addon'
```

If the selected port is occupied, run `& $Explorer --port 17764`. Stop the app with `Ctrl+C` in its terminal.

To launch the installed application on a later day, see [Start the application again](#start-the-application-again).

The wheel includes the compiled React interface and TypeScript grammar. Node.js is still required for JavaScript/OWL inspection, but no frontend dev server or npm setup is needed.

## Build from source

This option also works if GitHub Releases has no downloadable wheel. Follow these steps **in order**. The source JavaScript analyzer requires TypeScript installed under `frontend/node_modules` before backend tests run.

### 1. Clone the repository

```powershell
$RepoRoot = Join-Path $env:USERPROFILE 'OdooExplorerSource\odoo-module-explorer'
New-Item -ItemType Directory -Path (Split-Path $RepoRoot) -Force | Out-Null
git clone https://github.com/Gadero5565/odoo-module-explorer.git $RepoRoot
Set-Location $RepoRoot
```

Choose an empty target directory. If you have already cloned the repository, use its existing path instead of cloning again.

### 2. Prepare Python

```powershell
py -3.10 -m venv (Join-Path $RepoRoot '.build-venv')
$Python = Join-Path $RepoRoot '.build-venv\Scripts\python.exe'
& $Python -m pip install --upgrade pip setuptools wheel
Set-Location (Join-Path $RepoRoot 'backend')
& $Python -m pip install -e '.[dev]'
```

### 3. Install frontend dependencies and test the frontend

```powershell
Set-Location (Join-Path $RepoRoot 'frontend')
npm ci
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' }
Test-Path '.\node_modules\typescript\lib\typescript.js'   # Must be True
npm test
npm run build
```

### 4. Test the backend

```powershell
Set-Location (Join-Path $RepoRoot 'backend')
& $Python -m pytest -q
& $Python -m ruff check app tests
```

### 5. Build the standalone wheel

```powershell
Set-Location $RepoRoot
& $Python .\scripts\build_release.py --skip-npm
$Wheel = Get-ChildItem -Path (Join-Path $RepoRoot 'release') -Filter '*.whl' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Wheel) { throw 'No wheel found; inspect the build output.' }
$Wheel.FullName
```

`--skip-npm` reuses the frontend installed and compiled in Step 3. Omit it to let the build script run `npm ci` and `npm run build` again.

### 6. Test the wheel independently

Do not test the installed wheel only from the source directory. Use an independent test folder and the **absolute wheel path**:

```powershell
$TestDir = Join-Path $env:USERPROFILE 'OdooExplorerWheelTest'
New-Item -ItemType Directory -Force -Path $TestDir | Out-Null
Copy-Item -LiteralPath $Wheel.FullName -Destination $TestDir
py -3.10 -m venv (Join-Path $TestDir '.venv')
$TestPython = Join-Path $TestDir '.venv\Scripts\python.exe'
$TestCLI = Join-Path $TestDir '.venv\Scripts\odoo-explorer.exe'
& $TestPython -m pip install (Join-Path $TestDir $Wheel.Name)
& $TestCLI --version
Set-Location $TestDir
& $TestCLI --port 17764
```

Open `http://127.0.0.1:17764`. Test the sample addon, including JavaScript inspection, **without a Vite server running**. The release wheel must not depend on the source checkout's `node_modules`.

## Working with the source checkout

To run a source development session with hot reload, start FastAPI and Vite in separate PowerShell windows after completing Steps 2–3:

```powershell
# Backend terminal, from the source root
Set-Location (Join-Path $RepoRoot 'backend')
& $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 7764
```

```powershell
# Frontend terminal, from the source root
Set-Location (Join-Path $RepoRoot 'frontend')
npm run dev
```

Open `http://127.0.0.1:5173` for development mode.

## Troubleshooting

See [Troubleshooting](TROUBLESHOOTING.md) for missing TypeScript dependencies, Node.js setup, path issues, port conflicts and reporting bugs.
