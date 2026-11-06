#requires -Version 7.0
[CmdletBinding()]
param([switch]$Once,[switch]$AllowStartMissing,[ValidateRange(1,30)][int]$PollSeconds=2)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
if($env:HERDR_ENV -ne '1' -or -not $env:HERDR_PANE_ID -or $env:HERDR_SESSION -ne 'project-management'){throw '수신기는 실제 project-management herdr 내부 창에서만 실행할 수 있습니다.'}
Import-Module ./tools/workspace_listener.psm1 -Force
$store=Join-Path $root '.local/workspace-connect'
[IO.Directory]::CreateDirectory($store) | Out-Null
$lease=[IO.File]::Open((Join-Path $store 'listener.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$pwsh=(Get-Process -Id $PID).Path
$mode=if($AllowStartMissing){'allow-start-missing'}else{'reuse-only'}
Write-Host "관리 요청 수신 중 ($mode). 종료: Ctrl+C. 기존 AI 창에는 작업 메시지를 보내지 않습니다."
try {
    do {
        Write-ListenerStatus -Store $store -State waiting -Mode $mode
        $executor={
            param($requestId)
            Write-ListenerStatus -Store $store -State processing -Mode $mode -Detail $requestId
            $arguments=@('-NoProfile','-File','./tools/connect_workspace_agents.ps1','-Apply','-ExpectedRequestId',$requestId)
            if(-not $AllowStartMissing){$arguments+='-ReuseOnly'}
            $output=& $pwsh @arguments 2>&1
            $code=$LASTEXITCODE
            # Output is displayed only in this service pane; no prompt or credentials are collected.
            Write-Host ($output | Out-String)
            return [int]$code
        }
        $delivery=Invoke-WorkspaceDelivery -ProjectPath $root -Store $store -Executor $executor
        Write-ListenerStatus -Store $store -State waiting -Mode $mode -Detail ($delivery | ConvertTo-Json -Compress)
        if(-not $Once){Start-Sleep -Seconds $PollSeconds}
    } while(-not $Once)
} catch {
    Write-ListenerStatus -Store $store -State error -Mode $mode -Detail $_.Exception.Message
    throw
} finally {
    # A forced process kill may leave a stale heartbeat; the GUI marks old timestamps as stale.
    $lease.Dispose()
}
Write-ListenerStatus -Store $store -State stopped -Mode $mode
