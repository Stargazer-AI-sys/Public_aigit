#requires -Version 7.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'workspace_request.psm1') -Force
$root=Split-Path -Parent $PSScriptRoot
$store=Join-Path $root ('.local/connect-tests/'+[guid]::NewGuid().ToString('N'))
$script:count=0
function Assert($ok,$message){if(-not $ok){throw $message};$script:count++}
function Reject([scriptblock]$action){$failed=$false;try{& $action | Out-Null}catch{$failed=$true};Assert $failed '거절되지 않음'}
$first=New-WorkspaceRequest -ProjectPath $root -Store $store
Assert ($first.status -eq 'pending' -and $first.resume_saved -and $first.herdr_session -eq 'project-management') '명시적 재개 요청 저장'
$second=New-WorkspaceRequest -ProjectPath $root -Store $store
Assert ($first.request_id -eq $second.request_id) '중복 클릭 중복 요청'
foreach($state in @('processing','uncertain')){
 $first.status=$state;Write-WorkspaceRequest -Request $first -Store $store
 Assert ((New-WorkspaceRequest -ProjectPath $root -Store $store).request_id -eq $first.request_id) '불확실 요청 재전송 방지'
}
Reject {Get-WorkspaceRequest -ProjectPath $store -Store $store}
$first.status='processed';Write-WorkspaceRequest -Request $first -Store $store
$third=New-WorkspaceRequest -ProjectPath $root -Store $store
Assert ($third.request_id -ne $first.request_id) '완료 후 새 요청 생성'
$lock=[IO.File]::Open((Join-Path $store 'request.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try{Reject {New-WorkspaceRequest -ProjectPath $root -Store $store}}finally{$lock.Dispose()}
$before=(Get-FileHash (Join-Path $store 'request.json')).Hash
Get-WorkspaceRequest -ProjectPath $root -Store $store | Out-Null
Assert ((Get-FileHash (Join-Path $store 'request.json')).Hash -eq $before) '조회가 기록을 변경'
# Do not impersonate a Herdr environment; verify the real external guard in a child process.
if($env:HERDR_ENV -ne '1'){
 $pwsh=(Get-Process -Id $PID).Path
 $output=& $pwsh -NoProfile -File (Join-Path $PSScriptRoot 'connect_workspace_agents.ps1') -Apply 2>&1
 Assert ($LASTEXITCODE -ne 0 -and ($output | Out-String) -match 'herdr 내부') '외부 실행 차단'
}
Write-Output "PASS: $count request/guard checks. No live Herdr control or AI starts."
