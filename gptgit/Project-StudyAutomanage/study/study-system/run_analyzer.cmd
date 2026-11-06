@echo off
chcp 65001 >nul
setlocal
if defined STUDY_PYTHON goto selected
if exist "%~dp0.venv\Scripts\python.exe" (
    set "STUDY_PYTHON=%~dp0.venv\Scripts\python.exe"
    goto selected
)
where py >nul 2>nul
if not errorlevel 1 goto python_launcher
python -X utf8 "%~dp0launch.py" %*
exit /b %ERRORLEVEL%
:python_launcher
py -3 -X utf8 "%~dp0launch.py" %*
exit /b %ERRORLEVEL%
:selected
"%STUDY_PYTHON%" -X utf8 "%~dp0launch.py" %*
exit /b %ERRORLEVEL%
