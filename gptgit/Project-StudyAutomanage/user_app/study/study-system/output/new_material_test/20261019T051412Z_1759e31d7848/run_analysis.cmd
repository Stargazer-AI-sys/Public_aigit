@echo off
chcp 65001 >nul
setlocal
set "PYTHONPATH=%~dp0..\..\..\.test-deps;%PYTHONPATH%"
echo Routing-table material only. Maximum new API requests: 1.
echo Enter your API key only at the hidden-input prompt in this window.
echo No automatic retry, approval or Notion publication.
call "%~dp0..\..\..\run_analyzer.cmd" batch --inventory "%~dp0inventory.csv" --workspace "%~dp0..\..\knowledge_base" --provider openai --allow-api --max-new-calls 1 --ask-api-key --model gpt-6-luna
set "TASK_EXIT=%ERRORLEVEL%"
echo.
echo Exit code: %TASK_EXIT%
pause
exit /b %TASK_EXIT%
