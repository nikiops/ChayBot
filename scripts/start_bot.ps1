$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot "backend")

$env:DATABASE_URL = if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "sqlite+aiosqlite:///./app.db" }
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"
$env:USE_NGROK_FOR_WEBAPP = if ($env:USE_NGROK_FOR_WEBAPP) { $env:USE_NGROK_FOR_WEBAPP } else { "true" }
$env:NGROK_BIN = if ($env:NGROK_BIN) { $env:NGROK_BIN } else { "ngrok" }
$env:NGROK_API_PORT = if ($env:NGROK_API_PORT) { $env:NGROK_API_PORT } else { "4040" }

& ".\.venv313\Scripts\python.exe" -m app.bot.main
