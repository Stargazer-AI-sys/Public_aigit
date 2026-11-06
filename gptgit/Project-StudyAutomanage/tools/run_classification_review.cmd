@echo off
chcp 65001 >nul
setlocal
call "%~dp0..\study\study-system\run_analyzer.cmd" review %*
exit /b %ERRORLEVEL%
