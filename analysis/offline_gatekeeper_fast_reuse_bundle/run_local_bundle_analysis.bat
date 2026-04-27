@echo off
setlocal
set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..\..") do set REPO_ROOT=%%~fI
set PYTHONPATH=%REPO_ROOT%
"%REPO_ROOT%\.venv\Scripts\python.exe" "%SCRIPT_DIR%run_local_bundle_analysis.py" %*
