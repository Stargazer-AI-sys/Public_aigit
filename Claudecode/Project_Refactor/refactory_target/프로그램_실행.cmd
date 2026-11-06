@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if defined STUDY_PYTHON goto selected
where py >nul 2>nul
if not errorlevel 1 (
    py -3.14 -I -B -X utf8 "%~dp0start.py"
) else (
    python -I -B -X utf8 "%~dp0start.py"
)
goto finished
:selected
"%STUDY_PYTHON%" -I -B -X utf8 "%~dp0start.py"
:finished
if errorlevel 1 pause
