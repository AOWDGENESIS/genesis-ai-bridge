@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ROOT=%~dp0"
set "LAUNCHER=%ROOT%scripts\genesis-bridge.py"
set "LOG=%TEMP%\genesis-ai-bridge-setup.log"

echo.
echo  Genesis AI Bridge
 echo ==================
echo.
echo  Einrichtung wird automatisch vorbereitet ...

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto :NO_PYTHON
    set "PY=python"
)

%PY% "%LAUNCHER%" setup --mode ui >"%LOG%" 2>&1
if errorlevel 1 goto :SETUP_ERROR

start "Genesis AI Bridge" /min %PY% "%LAUNCHER%" web --host 127.0.0.1 --port 8787

echo  Bridge wird gestartet ...
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8787"
echo.
echo  Fertig. Im Browser Datei, ZIP, mehrere Dateien oder Ordner auswaehlen und START druecken.
echo  Dieses Fenster kann geschlossen werden.
exit /b 0

:NO_PYTHON
echo.
echo  Python wurde nicht gefunden. Bitte Python 3 installieren.
echo  Details: %LOG%
pause
exit /b 1

:SETUP_ERROR
echo.
echo  Einrichtung konnte nicht abgeschlossen werden.
echo  Details:
type "%LOG%"
echo.
pause
exit /b 1
