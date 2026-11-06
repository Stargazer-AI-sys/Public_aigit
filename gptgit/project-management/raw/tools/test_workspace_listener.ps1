#requires -Version 7.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'workspace_request.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'workspace_listener.psm1') -Force
$root=Split-Path -Parent $PSScriptRoot
$store=Join-Path $root ('.local/listener-tests/'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($store) | Out-Null
$script:count=0;$script:calls=0
function Assert($ok,$message){if(-not $ok){throw $message};$script:count++}
$never={param($id) throw 'executor must not run'}
Assert ((Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $never).status -eq 'no_request') '요청 없을 때 실행'
$request=New-WorkspaceRequest -ProjectPath $root -Store $store
$executor={
 param($id)
 $script:calls++
 $r=Get-WorkspaceRequest -ProjectPath $root -Store $store
 Assert ($r.delivery.status -eq 'claimed' -and $r.request_id -eq $id) '실행 전 ID/수신 이력 저장 실패'
 $r.status='processed';Write-WorkspaceRequest -Request $r -Store $store
 return [int]0
}
$done=Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $executor
Assert ($done.status -eq 'processed' -and $done.exit_code -eq 0 -and $script:calls -eq 1) '자동 수신 모의 실행 실패'
Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $never | Out-Null
Assert ($script:calls -eq 1) '완료 요청 재실행'
$request=New-WorkspaceRequest -ProjectPath $root -Store $store
$request.delivery=@{status='claimed'};Write-WorkspaceRequest -Request $request -Store $store
Assert ((Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $never).status -eq 'already_claimed') '중단 이후 무조건 재전송'
$request.status='processed';Write-WorkspaceRequest -Request $request -Store $store
New-WorkspaceRequest -ProjectPath $root -Store $store | Out-Null
$failed=Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor {param($id) return [int]1}
Assert ($failed.status -eq 'blocked') '사전 검사 실패를 완료로 오표시'
Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $never | Out-Null
New-WorkspaceRequest -ProjectPath $root -Store $store | Out-Null
$uncertain=Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor {
 param($id)
 $r=Get-WorkspaceRequest -ProjectPath $root -Store $store
 $r.status='processing';Write-WorkspaceRequest -Request $r -Store $store
 throw 'simulated interruption'
}
Assert ($uncertain.status -eq 'uncertain') '처리 중 오류를 재시도 가능으로 오표시'
Assert ((New-WorkspaceRequest -ProjectPath $root -Store $store).request_id -eq $uncertain.request_id) '불확실 요청 덮어쓰기'
Write-ListenerStatus -Store $store -State waiting -Mode reuse-only
$heartbeat=Get-Content (Join-Path $store 'listener.json') -Raw | ConvertFrom-Json
Assert ($heartbeat.mode -eq 'reuse-only' -and $heartbeat.state -eq 'waiting') '수신 모드 표시'
if($env:HERDR_ENV -ne '1'){
 $pwsh=(Get-Process -Id $PID).Path
 $output=& $pwsh -NoProfile -File (Join-Path $PSScriptRoot 'watch_workspace_requests.ps1') -Once 2>&1
 Assert ($LASTEXITCODE -ne 0 -and ($output | Out-String) -match 'herdr 내부') '외부 수신기 실행 차단'
}
Write-Output "PASS: $count listener checks. Mock executor only; no live Herdr or AI calls."
