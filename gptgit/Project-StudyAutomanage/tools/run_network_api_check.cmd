@echo off
chcp 65001 >nul
setlocal
pushd "%~dp0..\study\study-system"
if errorlevel 1 goto missing_source
echo 18일차 1건의 핵심 분석을 검증합니다. 코멘트가 없어도 정상입니다.
echo API 키는 요청 시 이 창에 직접 입력하며 화면이나 파일에 저장하지 않습니다.
echo 누적 검증 한도는 100회/$2이며 자동 재시도하지 않습니다. 실제 적용값은 budget 명령으로 확인하세요.
call "%~dp0..\study\study-system\run_analyzer.cmd" run --provider openai --ask-api-key --model gpt-6-luna --inventory "%~dp0..\output\v0.2_core_priority_verification\live_check_inventory.csv" --filename "18일차.txt" --output-dir "%~dp0..\output\live_api_validation_v0.2" --cache-dir "%~dp0..\output\live_api_cache_v0.2"
set "TASK_EXIT=%ERRORLEVEL%"
popd
echo.
echo 실행 종료 코드: %TASK_EXIT%
pause
exit /b %TASK_EXIT%
:missing_source
echo 프로젝트 소스 폴더를 열 수 없습니다. API 호출은 하지 않았습니다.
pause
exit /b 2
