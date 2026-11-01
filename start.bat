@echo off
title OpenBB Indonesia
cd /d "%~dp0"

rem ---- Edit this if your conda / Python environment lives elsewhere ----
set "CONDA_ACTIVATE=%USERPROFILE%\OpenBB\conda\Scripts\activate.bat"

echo [1/4] Checking Docker...
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok
echo       Docker Desktop is not running - starting it...
set "DOCKER_EXE="
for %%P in ("%ProgramFiles%\Docker\Docker\Docker Desktop.exe" "%LOCALAPPDATA%\Docker\Docker Desktop.exe" "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe") do (
  if exist %%P set "DOCKER_EXE=%%~P"
)
if defined DOCKER_EXE (
  start "" "%DOCKER_EXE%"
) else (
  echo       Could not find Docker Desktop automatically - please open it from the Start menu.
)
set /a tries=0
:wait_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok
set /a tries+=1
if %tries% lss 36 goto wait_docker
echo       Docker is still not running after 3 minutes. Open Docker Desktop, wait for "Engine running", then run start.bat again.
pause
exit /b 1

:docker_ok
echo [2/4] Starting Workspace container "openbb"...
docker start openbb >nul 2>&1
if errorlevel 1 echo       Could not start the "openbb" container - see README "Rebuilding Workspace".

echo [3/4] Activating Python environment...
call "%CONDA_ACTIVATE%"
if errorlevel 1 (
  echo       Could not activate conda: %CONDA_ACTIVATE% - edit CONDA_ACTIVATE at the top of start.bat
  pause
  exit /b 1
)

echo [4/4] Starting data server - Workspace opens at http://localhost:3000
echo       Keep this window open. Press Ctrl+C or close it to stop.
start "" cmd /c "timeout /t 10 /nobreak >nul & start http://localhost:3000"
python run.py
pause
