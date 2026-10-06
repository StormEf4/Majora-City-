@echo off
rem Majora City for Windows: runs ./majora-city inside WSL (Windows Subsystem for Linux).
rem Double-click to build the patch, or run from a terminal: majora-city.cmd build, majora-city.cmd update, ...
where wsl >nul 2>nul
if errorlevel 1 (
  echo Majora City builds inside WSL, which is not installed yet.
  echo Open PowerShell as Administrator, run:  wsl --install
  echo then restart your PC and double-click this file again. See BUILDING.md.
  pause
  exit /b 1
)
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=build"
wsl.exe --cd "%~dp0." -- bash ./majora-city %ARGS%
if "%~1"=="" pause
