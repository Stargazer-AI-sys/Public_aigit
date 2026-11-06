#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$script:Root=Split-Path -Parent $PSScriptRoot
function Get-SessionProjectKey([string]$ProjectPath) {
    $path=(Resolve-Path -LiteralPath $ProjectPath).Path.TrimEnd('\','/').ToLowerInvariant()
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($path))).ToLowerInvariant()
}
function Get-RoleRecord {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[string]$Store=(Join-Path $script:Root '.local/agent-sessions'))
    $file=Join-Path $Store ((Get-SessionProjectKey $ProjectPath)+'.json')
    if (-not (Test-Path -LiteralPath $file)) { return $null }
    $data=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json -AsHashtable
    if ($data.schema_version -ne 1 -or (Get-SessionProjectKey $data.project_path) -ne (Get-SessionProjectKey $ProjectPath)) { throw '대화 기록의 프로젝트가 일치하지 않습니다.' }
    if ($data.roles.ContainsKey($Role)) { return $data.roles[$Role] }
    return $null
}
function Save-RoleRecord {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[string]$ConversationId,[string]$PaneId,[string]$HerdrSession,[ValidateSet('user_report','live_verified')][string]$Source,[string]$Evidence,[string]$Store=(Join-Path $script:Root '.local/agent-sessions'))
    $id=[guid]::Empty
    if (-not [guid]::TryParseExact($ConversationId,'D',[ref]$id)) { throw '정확한 UUID 대화 ID가 필요합니다.' }
    if (-not $Evidence -or -not $HerdrSession -or $PaneId -notmatch '^w\d+:p\d+$') { throw '세션·창·검증 근거가 필요합니다.' }
    [IO.Directory]::CreateDirectory($Store) | Out-Null
    $file=Join-Path $Store ((Get-SessionProjectKey $ProjectPath)+'.json')
    $lock=[IO.File]::Open("$file.lock",[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        $data=if(Test-Path -LiteralPath $file){Get-Content $file -Raw | ConvertFrom-Json -AsHashtable}else{@{schema_version=1;project_path=(Resolve-Path $ProjectPath).Path;roles=@{};history=@()}}
        if ($data.schema_version -ne 1 -or (Get-SessionProjectKey $data.project_path) -ne (Get-SessionProjectKey $ProjectPath)) { throw '다른 프로젝트 기록을 덮어쓸 수 없습니다.' }
        if ($data.roles.ContainsKey($Role)) { $data.history+=@(@{role=$Role;record=$data.roles[$Role]}) }
        $data.roles[$Role]=@{conversation_id=$ConversationId;pane_id=$PaneId;herdr_session=$HerdrSession;source=$Source;evidence=$Evidence;recorded_at=[DateTimeOffset]::Now.ToString('o');kind=$(if($Role -eq 'master'){'codex'}else{'claude'})}
        $temp="$file.$([guid]::NewGuid().ToString('N')).tmp"
        [IO.File]::WriteAllText($temp,($data | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temp,$file,$true)
    } finally { $lock.Dispose() }
}
function Get-RoleDecisionCore {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[hashtable]$Snapshot,[hashtable]$Record,[switch]$ResumeSaved)
    $kind=if($Role -eq 'master'){'codex'}else{'claude'}
    if (-not $Snapshot.ContainsKey('panes') -or -not $Snapshot.ContainsKey('agents') -or $Snapshot.version -ne '0.9.5' -or $Snapshot.protocol -ne 22) { throw '지원하는 herdr 상태 형식이 아닙니다. 시작하지 않습니다.' }
    if($null -eq $Snapshot.panes -or $null -eq $Snapshot.agents){throw 'herdr 창 목록이 누락됐습니다.'}
    foreach($item in $Snapshot.agents){
        if(@($Snapshot.panes | Where-Object {$_.pane_id -eq $item.pane_id}).Count -ne 1){return @{action='blocked';reason='창 목록과 AI 목록이 일치하지 않음'}}
    }
    $matches=@()
    foreach($pane in $Snapshot.panes) {
        $agent=@($Snapshot.agents | Where-Object {$_.pane_id -eq $pane.pane_id})
        $entry=if($agent.Count -eq 1){$agent[0]}else{$pane}
        if ($agent.Count -gt 1) { return @{action='blocked';reason='중복된 창 식별자'} }
        if ($entry['agent'] -ne $kind) { continue }
        $cwd=if($entry['foreground_cwd']){$entry['foreground_cwd']}else{$entry['cwd']}
        if (-not $cwd) { return @{action='blocked';reason='AI 창의 작업 경로 미확인'} }
        try { $same=(Get-SessionProjectKey $cwd) -eq (Get-SessionProjectKey $ProjectPath) } catch { return @{action='blocked';reason='AI 창의 작업 경로 확인 실패'} }
        if($same){$matches+=@($entry)}
    }
    if($matches.Count -gt 1){return @{action='blocked';reason='동일 프로젝트·역할의 창이 여러 개 존재'}}
    if($matches.Count -eq 1){
        $entry=$matches[0]
        if ($entry['agent_status'] -notin @('idle','done','working','blocked') -or $entry['launch_pending'] -or $entry['screen_detection_skipped']) { return @{action='blocked';reason='실행 상태 불명확';pane_id=$entry.pane_id} }
        return @{action='reuse';pane_id=$entry.pane_id;state=$entry['agent_status'];reason='기존 창 유지. 명령·프롬프트를 전송하지 않음'}
    }
    if($ResumeSaved){
        if (-not $Record -or $Record.kind -ne $kind -or $Record.source -notin @('user_report','live_verified')){return @{action='blocked';reason='검증 근거가 있는 저장 대화 없음'}}
        $id=[guid]::Empty
        if(-not [guid]::TryParseExact($Record.conversation_id,'D',[ref]$id)){return @{action='blocked';reason='저장 대화 ID 오류'}}
        return @{action='resume';conversation_id=$Record.conversation_id;source=$Record.source}
    }
    if($Record){return @{action='blocked';reason='저장 대화가 있습니다. ResumeSaved로 명시적으로 재개하세요.'}}
    return @{action='start';reason='같은 프로젝트·역할의 실행 및 저장 대화 없음'}
}
function Get-RoleDecision {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[hashtable]$Snapshot,[hashtable]$Record,[switch]$ResumeSaved)
    $decision=Get-RoleDecisionCore @PSBoundParameters
    # Window preservation and conversation identity are independent results.
    $windowStatus=switch($decision.action){'reuse'{'reusable'} 'start'{'absent'} 'resume'{'absent'} default{'unconfirmed'}}
    $decision.window_check=@{status=$windowStatus;source='herdr_snapshot';preserve_existing=$true}
    $identity=@{
        status=$(if($Record){'unverified'}else{'no_saved_record'})
        source='none'; observed_id=$null
        saved_id=$(if($Record){$Record['conversation_id']}else{$null})
        saved_source=$(if($Record){$Record['source']}else{$null})
        reason='현재 창의 대화 ID를 확인하지 못했습니다.'
    }
    if($decision.ContainsKey('pane_id')){
        $entries=@($Snapshot.agents | Where-Object {$_.pane_id -eq $decision.pane_id})
        if($entries.Count -eq 0){$entries=@($Snapshot.panes | Where-Object {$_.pane_id -eq $decision.pane_id})}
        if($entries.Count -eq 1){
            $session=$entries[0]['agent_session']
            $nativeId=[guid]::Empty
            if($session -and $session['kind'] -eq 'id' -and [guid]::TryParseExact([string]$session['value'],'D',[ref]$nativeId)){
                $identity.source='herdr_snapshot'
                $identity.observed_id=$nativeId.ToString('D')
                if($Record){
                    $savedId=[guid]::Empty
                    if(-not [guid]::TryParseExact([string]$Record['conversation_id'],'D',[ref]$savedId)){
                        $identity.status='unverified';$identity.reason='저장된 대화 ID 형식 오류'
                    } elseif($nativeId -eq $savedId){
                        $identity.status='matched';$identity.reason='현재 herdr 응답의 대화 ID가 저장값과 일치합니다.'
                    } else {
                        $identity.status='mismatch';$identity.reason='현재 herdr 응답의 대화 ID가 저장값과 다릅니다.'
                    }
                } else {$identity.reason='현재 대화 ID는 있으나 비교할 저장 기록이 없습니다.'}
            } elseif($session){$identity.reason='herdr 대화 참조가 UUID ID가 아니므로 비교하지 않았습니다.'}
        }
    }
    if(-not $Record){$identity.reason='비교할 저장 대화 기록이 없습니다.'}
    if($identity.status -eq 'mismatch'){
        $decision.action='blocked';$decision.reason='대화 ID 불일치. 기존 창은 유지하고 자동 작업을 차단합니다.'
    }
    $decision.conversation_check=$identity
    # This result never authorizes sending a prompt, including matched/idle cases.
    $decision.automatic_prompt_allowed=$false
    $decision.restore_verified=$false
    return $decision
}
function Invoke-HerdrRead([string[]]$Arguments) {
    if($env:HERDR_ENV -ne '1' -or -not $env:HERDR_PANE_ID -or -not $env:HERDR_SESSION){throw 'herdr 내부의 실제 pane/session 환경이 필요합니다. 외부 제어는 실행하지 않습니다.'}
    $output=& (Join-Path $script:Root '.local/bin/herdr/herdr.exe') @Arguments
    if($LASTEXITCODE -ne 0){throw 'herdr 상태 조회 실패. 시작하지 않습니다.'}
    $response=$output | ConvertFrom-Json -AsHashtable
    if(-not $response.ContainsKey('result')){throw 'herdr 응답 형식 오류'}
    return $response.result
}
function Enter-RoleStart {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[switch]$ResumeSaved)
    if($env:HERDR_ENV -ne '1' -or -not $env:HERDR_PANE_ID -or -not $env:HERDR_SESSION){throw 'herdr 내부에서만 AI 시작·재개가 가능합니다.'}
    $store=Join-Path $script:Root '.local/agent-sessions'
    [IO.Directory]::CreateDirectory($store) | Out-Null
    $lock=[IO.File]::Open((Join-Path $store ((Get-SessionProjectKey $ProjectPath)+"-$Role.start.lock")),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        $record=Get-RoleRecord -ProjectPath $ProjectPath -Role $Role
        if($record -and $record.herdr_session -ne $env:HERDR_SESSION){throw '저장된 herdr 세션과 현재 세션이 다릅니다.'}
        $result=Invoke-HerdrRead -Arguments @('api','snapshot')
        $decision=Get-RoleDecision -ProjectPath $ProjectPath -Role $Role -Snapshot $result.snapshot -Record $record -ResumeSaved:$ResumeSaved
        if($decision.action -eq 'blocked'){throw $decision.reason}
        if($decision.action -eq 'reuse'){$lock.Dispose();return @{decision=$decision;lease=$null}}
        $current=@($result.snapshot.panes | Where-Object {$_.pane_id -eq $env:HERDR_PANE_ID})
        if($current.Count -ne 1 -or $current[0]['agent'] -or $current[0]['restore_error']){throw '현재 창이 빈 셸인지 확인할 수 없습니다.'}
        $cwd=if($current[0]['foreground_cwd']){$current[0]['foreground_cwd']}else{$current[0]['cwd']}
        if(-not $cwd -or (Get-SessionProjectKey $cwd) -ne (Get-SessionProjectKey $ProjectPath)){throw '현재 창의 프로젝트 경로가 다릅니다.'}
        # This script runs synchronously in its own pane. Never inject input into another terminal.
        return @{decision=$decision;lease=$lock}
    } catch { $lock.Dispose();throw }
}
function Get-LiveRolePlan {
    param([string]$ProjectPath,[ValidateSet('master','producer')][string]$Role,[switch]$ResumeSaved)
    $result=Invoke-HerdrRead -Arguments @('api','snapshot')
    $record=Get-RoleRecord -ProjectPath $ProjectPath -Role $Role
    if($record -and $record.herdr_session -ne $env:HERDR_SESSION){throw '저장된 herdr 세션과 현재 세션이 다릅니다.'}
    Get-RoleDecision -ProjectPath $ProjectPath -Role $Role -Snapshot $result.snapshot -Record $record -ResumeSaved:$ResumeSaved
}
Export-ModuleMember -Function Get-RoleRecord,Save-RoleRecord,Get-RoleDecision,Enter-RoleStart,Get-LiveRolePlan
