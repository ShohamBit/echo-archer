@echo off
pushd "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --comparison
) else (
    py main.py --comparison
)
if errorlevel 1 pause
popd
