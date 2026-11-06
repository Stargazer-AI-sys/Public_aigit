#requires -Version 7.0
[CmdletBinding()]
param([switch]$Apply, [switch]$ReuseOnly, [string]$ExpectedRequestId)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
# Never execute a live query, even a read, outside a genuine Herdr pane.
if($env:HERDR_ENV -ne '1' -or -not $env:HERDR_PANE_ID -or $env:HERDR_SESSION -ne 'project-management'){throw 'project-management herdr 내부에서만 실행할 수 있습니다.'}
Import-Module ./tools/agent_sessions.psm1 -Force
Import-Module ./tools/workspace_request.psm1 -Force
$store=Join-Path $root '.local/workspace-connect'
$herdr=Join-Path $root '.local/bin/herdr/herdr.exe'
$pwsh=(Get-Process -Id $PID).Path
function Invoke-Herdr([string[]]$Arguments){
    $output=& $herdr @Arguments
    if($LASTEXITCODE -ne 0){throw "herdr 명령 실패: $($Arguments[0]) $($Arguments[1]). 재전송하지 않습니다."}
    $response=$output | ConvertFrom-Json -AsHashtable
    if(-not $response.ContainsKey('result')){throw 'herdr 응답 형식 오류'}
    return $response.result
}
function Get-Plans {
    $plans=@{}
    foreach($role in @('master','producer')){
        # A record selects explicit resume. Without one a genuinely new role may start.
        $saved=Get-RoleRecord -ProjectPath $root -Role $role
        $plans[$role]=Get-LiveRolePlan -ProjectPath $root -Role $role -ResumeSaved:([bool]$saved)
    }
    return $plans
}
$request=Get-WorkspaceRequest -ProjectPath $root -Store $store
if(-not $Apply){@{request_id=$request.request_id;request_status=$request.status;plans=(Get-Plans);mutations=$false} | ConvertTo-Json -Depth 12;exit 0}
$lock=[IO.File]::Open((Join-Path $store 'request.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
    $request=Get-WorkspaceRequest -ProjectPath $root -Store $store
    if($ExpectedRequestId -and $request.request_id -ne $ExpectedRequestId){throw '요청 ID가 변경됐습니다. 다른 요청은 처리하지 않습니다.'}
    if($request.status -ne 'pending'){throw "요청 상태는 $($request.status)입니다. 중복/불확실 요청은 자동 재실행하지 않습니다."}
    $plans=Get-Plans
    foreach($role in @('master','producer')){if($plans[$role].action -eq 'blocked'){throw "$role 연결 차단: $($plans[$role].reason)"}}
    if($ReuseOnly -and @($plans.Values | Where-Object {$_.action -ne 'reuse'}).Count -gt 0){throw '기존 창 유지 검사입니다. 두 역할 모두 reuse여야 하며 새 창을 만들지 않습니다.'}
    # Authenticate every missing role before creating any pane. No auth check for preserved roles.
    foreach($role in @('master','producer')){
        if($plans[$role].action -eq 'reuse'){continue}
        $script=if($role -eq 'master'){'./tools/start_master.ps1'}else{'./tools/start_claude.ps1'}
        $check=& $pwsh -NoProfile -File $script -CheckOnly
        if($LASTEXITCODE -ne 0){throw "$role 구독 인증 검사 실패. 창을 만들지 않습니다."}
    }
    $request.status='processing'
    Write-WorkspaceRequest -Request $request -Store $store
    $anchor=$env:HERDR_PANE_ID
    foreach($role in @('master','producer')){
        $saved=Get-RoleRecord -ProjectPath $root -Role $role
        $plan=Get-LiveRolePlan -ProjectPath $root -Role $role -ResumeSaved:([bool]$saved)
        if($plan.action -eq 'blocked'){throw "$role 상태가 바뀌었습니다. $($plan.reason)"}
        if($ReuseOnly -and $plan.action -ne 'reuse'){throw '역할 상태가 바뀌었습니다. ReuseOnly이므로 새 창을 만들지 않습니다.'}
        if($plan.action -eq 'reuse'){
            $request.roles[$role]=@{status='preserved';pane_id=$plan.pane_id;conversation_check=$plan.conversation_check}
            if($role -eq 'master'){$anchor=$plan.pane_id}
            Write-WorkspaceRequest -Request $request -Store $store
            continue
        }
        # Persist intent BEFORE a mutation: a crash/timeout must not trigger blind resubmission.
        $request.roles[$role]=@{status='creating';action=$plan.action}
        Write-WorkspaceRequest -Request $request -Store $store
        $split=Invoke-Herdr -Arguments @('pane','split',$anchor,'--direction','right','--cwd',$root,'--no-focus')
        $pane=$split.pane.pane_id
        if($pane -notmatch '^w\d+:p\d+$'){throw '생성된 창 ID를 확인할 수 없습니다.'}
        $request.roles[$role].pane_id=$pane
        $request.roles[$role].status='created'
        Write-WorkspaceRequest -Request $request -Store $store
        # Only inject into the newly created, idle PowerShell shell, never an existing user pane.
        $ready=$false
        for($i=0;$i -lt 20;$i++){
            $proc=(Invoke-Herdr -Arguments @('pane','process-info','--pane',$pane)).process_info
            $fg=@($proc.foreground_processes)
            if($proc.shell_pid -and $fg.Count -eq 1 -and $fg[0].pid -eq $proc.shell_pid -and $fg[0].name -match '^(pwsh|powershell)(\.exe)?$'){$ready=$true;break}
            Start-Sleep -Milliseconds 250
        }
        if(-not $ready){throw '새 PowerShell 창의 전경 상태를 확인하지 못했습니다. 입력하지 않습니다.'}
        $script=if($role -eq 'master'){'./tools/start_master.ps1'}else{'./tools/start_claude.ps1'}
        $command="& '"+$pwsh.Replace("'","''")+"' -NoProfile -File '"+$script+"'"
        if($plan.action -eq 'resume'){$command+=' -ResumeSaved'}
        $request.roles[$role].status='dispatching'
        Write-WorkspaceRequest -Request $request -Store $store
        Invoke-Herdr -Arguments @('pane','run',$pane,$command) | Out-Null
        $request.roles[$role].status='submitted_unverified'
        Write-WorkspaceRequest -Request $request -Store $store
        # Admission is not execution success. Confirm the same newly-created pane is recognized.
        $detected=$false
        for($i=0;$i -lt 30;$i++){
            $after=Get-LiveRolePlan -ProjectPath $root -Role $role -ResumeSaved:([bool]$saved)
            if($after.action -eq 'reuse' -and $after.pane_id -eq $pane){$detected=$true;break}
            if($after.action -eq 'blocked' -and $after.reason -match '대화 ID 불일치'){throw '시작 후 대화 ID 불일치'}
            Start-Sleep -Milliseconds 500
        }
        if(-not $detected){throw '제출 후 AI 창 확인이 완료되지 않았습니다. 같은 명령을 재전송하지 않습니다.'}
        $request.roles[$role].status='detected_not_restore_verified'
        $request.roles[$role].conversation_check=$after.conversation_check
        Write-WorkspaceRequest -Request $request -Store $store
        if($role -eq 'master'){$anchor=$pane}
    }
    $request.status='processed'
    Write-WorkspaceRequest -Request $request -Store $store
    @{request=$request;restore_verified=$false;prompts_sent=0} | ConvertTo-Json -Depth 12
} catch {
    if($request.status -eq 'processing'){
        $request.status='uncertain';$request.error=$_.Exception.Message
        Write-WorkspaceRequest -Request $request -Store $store
    }
    throw
} finally {$lock.Dispose()}
