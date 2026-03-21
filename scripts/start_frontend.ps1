$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot "frontend")

if (-not $env:VITE_API_URL) { $env:VITE_API_URL = "/api" }
if (-not $env:VITE_DEMO_USER_ID) { $env:VITE_DEMO_USER_ID = "900000001" }

npm run dev -- --host 127.0.0.1 --port 5173
