@echo off
chcp 65001 >nul
setlocal
if "%~1"=="" goto usage
if /I "%~1"=="prepare" goto run
if /I "%~1"=="send" goto run
if /I "%~1"=="status" goto run
if /I "%~1"=="analyze" goto run
if /I "%~1"=="review" goto run
goto usage
:run
if defined STUDY_PYTHON goto selected
if exist "%~dp0..\study\study-system\.venv\Scripts\python.exe" goto selected
for /f "delims=" %%P in ('where python 2^>nul') do if not defined STUDY_PYTHON set "STUDY_PYTHON=%%P"
if exist "%~dp0..\study\study-system\.test-deps\jsonschema" set "PYTHONPATH=%~dp0..\study\study-system\.test-deps;%PYTHONPATH%"
:selected
call "%~dp0..\study\study-system\run_analyzer.cmd" notion %*
exit /b %ERRORLEVEL%
:usage
echo 게시안 준비: %~nx0 prepare
echo 원본 상태 확인: %~nx0 status
echo 신규 분석: %~nx0 analyze --allow-api --max-new-calls 1 --ask-api-key --file "정확한 파일명"
echo 내용과 분류 승인: %~nx0 review
echo 확인한 게시안 전송: %~nx0 send --package "package.json 전체 경로" --allow-notion-write
echo 전송에는 현재 채팅의 Notion 연결 도구 중계가 필요합니다.
exit /b 2
