@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: copilot-buddy-bridge.cmd
::
:: Stable launcher for the copilot-buddy bridge daemon.
:: Resolves the .venv Python at runtime so the service definition
:: does not break when the venv is recreated.
::
:: Usage (typically invoked by Task Scheduler, not manually):
::   copilot-buddy-bridge.cmd [--port COM3] [--log-file ...] ...
:: ============================================================

:: Derive repo root from this script's location (scripts\ → repo root)
for %%I in ("%~dp0..") do set "REPO_DIR=%%~fI"

:: Resolve Python from the repo-root .venv
set "VENV_PYTHON=%REPO_DIR%\.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found at %REPO_DIR%\.venv 1>&2
    echo Run: python -m venv .venv ^&^& .venv\Scripts\Activate.ps1 ^&^& python -m pip install -r bridge\requirements.txt 1>&2
    exit /b 1
)

:: Run the bridge daemon from the repo root, passing through all args
cd /d "%REPO_DIR%"
"%VENV_PYTHON%" -m bridge.copilot_bridge %*
