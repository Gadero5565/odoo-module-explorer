# Run from the extracted source checkout after building the wheel.
# Usage: .\scripts\install_release.ps1 -Python py -Version 3.10
param([string]$Python = "py", [string]$Version = "3.10")
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
$wheel = Get-ChildItem '.\release\odoo_module_explorer_backend-*.whl' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $wheel) { throw 'Build a release wheel first using .\scripts\build_release.ps1.' }
if ($Python -eq 'py') { & py "-$Version" -m venv .release-venv }
else { & $Python -m venv .release-venv }
if ($LASTEXITCODE -ne 0) { throw 'Unable to create virtual environment' }
& .\.release-venv\Scripts\python.exe -m pip install "$($wheel.FullName)"
if ($LASTEXITCODE -ne 0) { throw 'Unable to install release wheel' }
Write-Host 'Installed. Try:' -ForegroundColor Green
Write-Host '  .\.release-venv\Scripts\odoo-explorer.exe --version'
Write-Host '  .\.release-venv\Scripts\odoo-explorer.exe "C:\path\to\addon"'
