@echo off
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 --version >nul 2>&1
  if not errorlevel 1 (
    py -3 server.py
    pause
    exit /b
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python --version >nul 2>&1
  if not errorlevel 1 (
    python server.py
    pause
    exit /b
  )
)
echo Python 3 wurde nicht gefunden.
echo Bitte Python 3 installieren und danach diese Datei erneut starten.
pause
