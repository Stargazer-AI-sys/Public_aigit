@echo off
chcp 65001 >nul
setlocal
set "PYTHONPATH=%~dp0..\..\..\.test-deps;%PYTHONPATH%"
echo OSI material only. Maximum new API requests: 1.
echo Enter the API key at the hidden-input prompt in this terminal.
echo No automatic retry, approval or Notion publication.
call "%~dp0..\..\..\run_analyzer.cmd" batch --inventory "%~dp0inventory.csv" --workspace "%~dp0..\..\knowledge_base" --provider openai --allow-api --max-new-calls 1 --ask-api-key --model gpt-6-luna
set "TASK_EXIT=%ERRORLEVEL%"
echo Exit code: %TASK_EXIT%
pause
exit /b %TASK_EXIT%
