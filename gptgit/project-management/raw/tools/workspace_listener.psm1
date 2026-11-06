#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'workspace_request.psm1')
function Invoke-WorkspaceDelivery {
    param([string]$ProjectPath,[string]$Store,[scriptblock]$Executor)
    if(-not (Test-Path -LiteralPath (Join-Path $Store 'request.json'))){return @{status='no_request'}}
    $lock=[IO.File]::Open((Join-Path $Store 'request.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        $request=Get-WorkspaceRequest -ProjectPath $ProjectPath -Store $Store
        if($request.status -ne 'pending'){return @{status='not_pending';request_id=$request.request_id}}
        if($request.ContainsKey('delivery')){return @{status='already_claimed';request_id=$request.request_id}}
        # Persist a claim before executing: a crash must never silently resend a command.
        $request.delivery=@{status='claimed';claimed_at=[DateTimeOffset]::Now.ToString('o')}
        Write-WorkspaceRequest -Request $request -Store $Store
        $requestId=$request.request_id
    } finally {$lock.Dispose()}
    $errorText=$null
    try {$exitCode=& $Executor $requestId; if($exitCode -isnot [int]){throw '실행기의 종료 코드를 확인하지 못했습니다.'}}
    catch {$exitCode=1;$errorText=$_.Exception.Message}
    $lock=[IO.File]::Open((Join-Path $Store 'request.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        $request=Get-WorkspaceRequest -ProjectPath $ProjectPath -Store $Store
        if($request.request_id -ne $requestId){throw '처리 중 요청이 변경됐습니다. 다른 요청을 수정하지 않습니다.'}
        if($request.status -eq 'pending'){$request.status='blocked';$request.error=if($errorText){$errorText}else{'연결 전 검사 실패 또는 실행 완료 근거 없음. 다시 실행하지 않았습니다.'}}
        elseif($request.status -eq 'processing'){$request.status='uncertain';$request.error='실행기가 처리 중 상태로 종료됐습니다. 자동 재시도하지 않습니다.'}
        $request.delivery.status='returned'
        $request.delivery.exit_code=$exitCode
        $request.delivery.returned_at=[DateTimeOffset]::Now.ToString('o')
        Write-WorkspaceRequest -Request $request -Store $Store
        return @{status=$request.status;request_id=$requestId;exit_code=$exitCode}
    } finally {$lock.Dispose()}
}
function Write-ListenerStatus {
    param([string]$Store,[string]$State,[string]$Mode,[string]$Detail='')
    $data=@{schema_version=1;state=$State;mode=$Mode;pid=$PID;updated_at=[DateTimeOffset]::Now.ToString('o');detail=$Detail}
    $tmp=Join-Path $Store ([guid]::NewGuid().ToString('N')+'.tmp')
    [IO.File]::WriteAllText($tmp,($data | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    [IO.File]::Move($tmp,(Join-Path $Store 'listener.json'),$true)
}
Export-ModuleMember -Function Invoke-WorkspaceDelivery,Write-ListenerStatus
