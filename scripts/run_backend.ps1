# Script to run the backend FastAPI application locally
# Automatically resolves the backend path

Write-Host "Starting ModelRouter AI Backend..."

# Determine the absolute path to the backend directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Resolve-Path (Join-Path $ScriptDir "..\backend")

# Switch to the backend directory and run
Push-Location $BackendDir
$env:PYTHONPATH="."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Pop-Location
