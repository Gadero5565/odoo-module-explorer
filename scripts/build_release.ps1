# From project root: .\scripts\build_release.ps1
# Requires Python 3.10+, Node.js 20+, npm, and a working pip installation.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
python .\scripts\build_release.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Release wheel created in .\release\" -ForegroundColor Green
