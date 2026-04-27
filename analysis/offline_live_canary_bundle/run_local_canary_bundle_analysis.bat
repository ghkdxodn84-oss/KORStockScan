@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%..\.."

python "%SCRIPT_DIR%run_local_canary_bundle_analysis.py" %*
