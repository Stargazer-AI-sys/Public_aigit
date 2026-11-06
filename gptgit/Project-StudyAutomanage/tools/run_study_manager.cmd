@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0..\study\study-system"
if exist ".test-deps\jsonschema" set "PYTHONPATH=%CD%\.test-deps;%PYTHONPATH%"
if defined STUDY_PYTHON goto selected
if exist ".venv\Scripts\python.exe" (
    set "STUDY_PYTHON=%CD%\.venv\Scripts\python.exe"
    goto selected
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -X utf8 -m analyzer.management
) else (
    python -X utf8 -m analyzer.management
)
goto finished
:selected
"%STUDY_PYTHON%" -X utf8 -m analyzer.management
:finished
if errorlevel 1 pause
