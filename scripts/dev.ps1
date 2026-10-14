# Run in PowerShell after completing the README setup steps.
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Error 'Backend environment is missing. Run the backend setup steps in README.md first.'
}
Write-Host 'Starting FastAPI at http://127.0.0.1:7764' -ForegroundColor Cyan
Start-Process powershell -ArgumentList @('-NoExit', '-Command', "Set-Location '$projectRoot\backend'; & '$python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 7764")
Write-Host 'Starting React/Vite at http://127.0.0.1:5173' -ForegroundColor Cyan
Set-Location (Join-Path $projectRoot 'frontend')
npm run dev
