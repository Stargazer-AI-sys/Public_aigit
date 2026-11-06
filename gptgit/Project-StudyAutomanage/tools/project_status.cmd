@echo off
chcp 65001 >nul
setlocal
if defined STUDY_PYTHON goto selected
where python >nul 2>nul
if errorlevel 1 goto launcher
python -X utf8 "%~dp0project_status.py" %*
exit /b %ERRORLEVEL%
:launcher
py -3 -X utf8 "%~dp0project_status.py" %*
exit /b %ERRORLEVEL%
:selected
"%STUDY_PYTHON%" -X utf8 "%~dp0project_status.py" %*
exit /b %ERRORLEVEL%
