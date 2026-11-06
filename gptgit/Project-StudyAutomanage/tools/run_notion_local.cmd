@echo off
chcp 65001 >nul
setlocal
if defined STUDY_PYTHON goto run
where python >nul 2>nul
if not errorlevel 1 set "STUDY_PYTHON=python"
:run
call "%~dp0..\study\study-system\run_analyzer.cmd" notion %*
exit /b %ERRORLEVEL%
