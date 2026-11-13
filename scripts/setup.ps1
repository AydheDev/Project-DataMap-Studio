$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
function Check-Exit($message) { if ($LASTEXITCODE -ne 0) { throw $message } }
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Install Python 3.14 for developer setup, or use the standalone executable.' }
& $pythonCommand.Source -c "import sys; assert sys.version_info >= (3,14)"
Check-Exit 'Python 3.14 or newer is required for developer setup.'
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $pythonCommand.Source -m venv .venv
    Check-Exit 'Could not create the Python environment.'
}
& '.\.venv\Scripts\python.exe' -m pip install -r desktop/requirements.txt
Check-Exit 'Desktop dependency installation failed.'
& '.\.venv\Scripts\python.exe' scripts/build_desktop.py
Check-Exit 'Desktop executable packaging failed.'
Write-Host 'Ready. Run dist\DataMapStudio.exe or double-click Start.cmd.' -ForegroundColor Green
