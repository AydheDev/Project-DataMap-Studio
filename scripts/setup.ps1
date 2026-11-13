$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
function Check-Exit($message) {
    if ($LASTEXITCODE -ne 0) { throw $message }
}
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Install Python 3.14 and add it to PATH, then run Setup.cmd again.' }
& $pythonCommand.Source -c "import sys; assert sys.version_info >= (3,14), 'Python 3.14 or newer is required'"
Check-Exit 'Python 3.14 or newer is required.'
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & $pythonCommand.Source -m venv .venv
    Check-Exit 'Could not create the Python environment.'
}
& '.\.venv\Scripts\python.exe' -m pip install -r backend/requirements-lock.txt
Check-Exit 'Python dependency installation failed.'
$pnpmCommand = Get-Command pnpm -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
Push-Location -LiteralPath frontend
try {
    if ($pnpmCommand) {
        & $pnpmCommand.Source install --frozen-lockfile
        Check-Exit 'Frontend dependency installation failed.'
        & $pnpmCommand.Source build
    } elseif ($npmCommand) {
        & $npmCommand.Source exec --yes --package=pnpm@11.25.0 -- pnpm install --frozen-lockfile
        Check-Exit 'Frontend dependency installation failed.'
        & $npmCommand.Source exec --yes --package=pnpm@11.25.0 -- pnpm build
    } else {
        throw 'Install Node.js 22.12+ (with npm) or pnpm, then run Setup.cmd again.'
    }
    Check-Exit 'Frontend build failed.'
} finally {
    Pop-Location
}
Write-Host 'DataMap Studio is ready. Double-click Start.cmd.' -ForegroundColor Green
