$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot "backend")

$env:DATABASE_URL = if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "sqlite+aiosqlite:///./app.db" }
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"

& ".\.venv313\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
