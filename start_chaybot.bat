@echo off
setlocal EnableExtensions
title ChayBot Launcher

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo ==========================================
echo   ChayBot Launcher
echo ==========================================
echo.

if not exist "%ROOT%\backend\.venv313\Scripts\python.exe" (
  echo [ERROR] Missing backend venv: backend\.venv313\Scripts\python.exe
  echo Install backend dependencies first.
  goto :fail
)

where ngrok >nul 2>nul
if errorlevel 1 (
  echo [ERROR] ngrok is not available in PATH.
  echo Install ngrok or add it to PATH.
  goto :fail
)

if not exist "%ROOT%\frontend\node_modules" (
  echo [INFO] frontend\node_modules not found. Running npm install...
  pushd "%ROOT%\frontend"
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    goto :fail
  )
  popd
)

set "DATABASE_URL=sqlite+aiosqlite:///./app.db"
set "DEBUG=true"
set "ENVIRONMENT=development"
set "USE_NGROK_FOR_WEBAPP=true"
set "NGROK_BIN=ngrok"
set "NGROK_API_PORT=4040"
set "VITE_API_URL=/api"
set "VITE_DEMO_USER_ID=900000001"

if exist "%ROOT%\.env" (
  for /f "tokens=1,* delims==" %%A in ('findstr /B /C:"BOT_TOKEN=" "%ROOT%\.env"') do set "BOT_TOKEN=%%B"
  for /f "tokens=1,* delims==" %%A in ('findstr /B /C:"BOT_USERNAME=" "%ROOT%\.env"') do set "BOT_USERNAME=%%B"
  for /f "tokens=1,* delims==" %%A in ('findstr /B /C:"BOT_ADMIN_IDS=" "%ROOT%\.env"') do set "BOT_ADMIN_IDS=%%B"
)

if defined BOT_USERNAME (
  if "%BOT_USERNAME:~0,1%"=="@" set "BOT_USERNAME=%BOT_USERNAME:~1%"
)

if not defined BOT_TOKEN goto prompt_token
if /I "%BOT_TOKEN%"=="CHANGE_ME" goto prompt_token
goto check_username

:prompt_token
echo [WARN] BOT_TOKEN not found in .env
set /p "BOT_TOKEN=Enter BOT_TOKEN: "
if not defined BOT_TOKEN (
  echo [ERROR] BOT_TOKEN is required.
  goto :fail
)

:check_username
if not defined BOT_USERNAME goto prompt_username
if /I "%BOT_USERNAME%"=="change_me_bot" goto prompt_username
goto prepare_db

:prompt_username
echo [WARN] BOT_USERNAME not found in .env
set /p "BOT_USERNAME=Enter BOT_USERNAME (example: TestChay2323_bot): "
if not defined BOT_USERNAME (
  echo [ERROR] BOT_USERNAME is required.
  goto :fail
)
if "%BOT_USERNAME:~0,1%"=="@" set "BOT_USERNAME=%BOT_USERNAME:~1%"

:prepare_db
echo.
echo [1/4] Running Alembic migrations...
pushd "%ROOT%\backend"
call ".\.venv313\Scripts\alembic.exe" upgrade head
if errorlevel 1 (
  popd
  echo [ERROR] Alembic migration failed.
  goto :fail
)

echo [2/4] Loading seed data...
call ".\.venv313\Scripts\python.exe" -m app.db.seed
if errorlevel 1 (
  popd
  echo [ERROR] Seed loading failed.
  goto :fail
)
popd

echo [3/4] Starting backend...
start "ChayBot Backend" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\start_backend.ps1"
timeout /t 3 >nul

echo [4/4] Starting frontend and bot...
start "ChayBot Frontend" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\start_frontend.ps1"
timeout /t 5 >nul
set "BOT_TOKEN=%BOT_TOKEN%"
set "BOT_USERNAME=%BOT_USERNAME%"
start "ChayBot Bot" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$env:BOT_TOKEN='%BOT_TOKEN%'; $env:BOT_USERNAME='%BOT_USERNAME%'; if ('%BOT_ADMIN_IDS%' -ne '') { $env:BOT_ADMIN_IDS='%BOT_ADMIN_IDS%' }; & '%ROOT%\scripts\start_bot.ps1'"

echo.
echo Done.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo Bot:      @%BOT_USERNAME%
echo.
echo Send /start to the bot after all windows are up.
echo If Mini App does not open immediately, wait 5-10 seconds for ngrok.
goto :done

:fail
echo.
echo Launch aborted.
pause
exit /b 1

:done
echo.
pause
exit /b 0
