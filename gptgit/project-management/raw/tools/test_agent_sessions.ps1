#requires -Version 7.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'agent_sessions.psm1') -Force
$root=Split-Path -Parent $PSScriptRoot
$testRoot=Join-Path $root ('.local/session-tests/'+[guid]::NewGuid().ToString('N'))
$other=Join-Path $testRoot 'other'
New-Item -ItemType Directory -Path $other | Out-Null
$store=Join-Path $testRoot 'store'
$script:count=0
function Assert($value,$message){if(-not $value){throw $message};$script:count++}
function Reject([scriptblock]$action){$failed=$false;try{& $action | Out-Null}catch{$failed=$true};Assert $failed '거절해야 할 작업이 허용됨'}
$id='11111111-1111-4111-8111-111111111111'
Save-RoleRecord -ProjectPath $root -Role master -ConversationId $id -PaneId 'w3:p1' -HerdrSession 'project-management' -Source user_report -Evidence 'synthetic test' -Store $store
$record=Get-RoleRecord -ProjectPath $root -Role master -Store $store
Assert ($record.conversation_id -eq $id -and $record.source -eq 'user_report') '저장·근거 구분 실패'
Assert ($null -eq (Get-RoleRecord -ProjectPath $other -Role master -Store $store)) '다른 프로젝트 기록 혼입'
Assert ($null -eq (Get-RoleRecord -ProjectPath $root -Role producer -Store $store)) '다른 역할 기록 혼입'
Reject {Save-RoleRecord -ProjectPath $root -Role master -ConversationId '--last' -PaneId 'w3:p1' -HerdrSession 'project-management' -Source user_report -Evidence 'bad' -Store $store}
$empty=@{version='0.9.5';protocol=22;panes=@();agents=@()}
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $empty).action -eq 'start') '신규 역할 시작 판정'
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $empty -Record $record).action -eq 'blocked') '저장 대화 무시 방지'
$resume=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $empty -Record $record -ResumeSaved
Assert ($resume.action -eq 'resume' -and $resume.conversation_id -eq $id) '정확한 ID 재개'
Assert ((Get-RoleDecision -ProjectPath $root -Role producer -Snapshot $empty -ResumeSaved).action -eq 'blocked') '없는 대화 재개 차단'
$pane=@{pane_id='w3:p1';agent='codex';cwd=$root;foreground_cwd=$root;agent_status='idle';launch_pending=$false;screen_detection_skipped=$false;agent_session=@{kind='id';value=$id}}
$live=@{version='0.9.5';protocol=22;panes=@($pane);agents=@($pane)}
foreach($state in @('idle','done','working','blocked')){
 $pane.agent_status=$state
 Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record -ResumeSaved).action -eq 'reuse') "기존 $state 창 보존"
}
$pane.agent_status='unknown'
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live).action -eq 'blocked') '상태 불명 차단'
$pane.agent_status='idle';$pane.foreground_cwd=$null;$pane.cwd=$null
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live).action -eq 'blocked') '경로 불명 차단'
$pane.cwd=$root;$pane.agent_session.value='22222222-2222-4222-8222-222222222222'
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record -ResumeSaved).action -eq 'blocked') '대화 불일치 차단'
$pane.agent_session.value=$id;$pane.launch_pending=$true
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live).action -eq 'blocked') '시작 중 중복 방지'
$pane.launch_pending=$false
$pane.agent_session=$null
$missing=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record -ResumeSaved
Assert ($missing.action -eq 'reuse' -and $missing.window_check.status -eq 'reusable') 'ID 누락 시 기존 창 유지'
Assert ($missing.conversation_check.status -eq 'unverified' -and $missing.conversation_check.source -eq 'none' -and $null -eq $missing.conversation_check.observed_id) 'ID 누락을 일치로 오표시'
Assert ($missing.conversation_check.saved_source -eq 'user_report' -and -not $missing.restore_verified -and -not $missing.automatic_prompt_allowed) '과거 근거를 현재 검증/작업 허가로 확대'
$pane.agent_session=@{kind='id';value=$id}
$matched=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record
Assert ($matched.conversation_check.status -eq 'matched' -and $matched.conversation_check.source -eq 'herdr_snapshot') '현재 ID 일치 표시'
Assert (-not $matched.automatic_prompt_allowed -and -not $matched.restore_verified) '일치를 작업 허가/복원 성공으로 확대'
$pane.agent_session.value='22222222-2222-4222-8222-222222222222'
$mismatch=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record
Assert ($mismatch.action -eq 'blocked' -and $mismatch.window_check.status -eq 'reusable' -and $mismatch.conversation_check.status -eq 'mismatch' -and $mismatch.window_check.preserve_existing) '재개 옵션 없이도 불일치 차단·기존 창 보존'
$pane.agent_session=@{kind='path';value='some/session/file'}
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record).conversation_check.status -eq 'unverified') '경로 참조를 ID 불일치로 오판'
$pane.agent_session=@{kind='id';value='bad-id'}
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live -Record $record).conversation_check.status -eq 'unverified') '잘못된 UUID 검증 처리'
$pane.agent_session=@{kind='id';value=$id}
$unsaved=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live
Assert ($unsaved.conversation_check.status -eq 'no_saved_record' -and $unsaved.conversation_check.observed_id -eq $id) '저장 기록 없음 구분'
$absent=Get-RoleDecision -ProjectPath $root -Role master -Snapshot $empty -Record $record -ResumeSaved
Assert ($absent.window_check.status -eq 'absent' -and $absent.conversation_check.status -eq 'unverified' -and -not $absent.restore_verified) '재개 계획을 복원 성공으로 오표시'
$pane.agent='claude';$pane.agent_session=$null
$producerRecord=$record.Clone();$producerRecord.kind='claude'
$producer=Get-RoleDecision -ProjectPath $root -Role producer -Snapshot $live -Record $producerRecord
Assert ($producer.action -eq 'reuse' -and $producer.conversation_check.status -eq 'unverified' -and $producer.conversation_check.source -eq 'none') 'Claude에 GPT 환경변수/과거 ID를 실시간 근거로 사용'
$pane.agent='codex';$pane.agent_session=@{kind='id';value=$id}
$dupe=$pane.Clone();$dupe.pane_id='w3:p9'
$live.panes+=@($dupe);$live.agents+=@($dupe)
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot $live).action -eq 'blocked') '여러 후보 임의 선택 방지'
Reject {Get-RoleDecision -ProjectPath $root -Role master -Snapshot @{version='future';protocol=999;panes=@();agents=@()}}
Reject {Get-RoleDecision -ProjectPath $root -Role master -Snapshot @{version='0.9.5';protocol=22}}
Assert ((Get-RoleDecision -ProjectPath $root -Role master -Snapshot @{version='0.9.5';protocol=22;panes=@();agents=@($pane)}).action -eq 'blocked') '누락된 창 목록으로 중복 시작 방지'
Reject {Get-RoleDecision -ProjectPath $root -Role master -Snapshot @{version='0.9.5';protocol=22;panes=$null;agents=@()}}
# Use the real external environment. Never fake HERDR_ENV for tests.
if($env:HERDR_ENV -ne '1'){Reject {Enter-RoleStart -ProjectPath $root -Role master}}
$file=Get-ChildItem $store -Filter '*.json' | Select-Object -First 1
$handle=[IO.File]::Open(($file.FullName+'.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try{Reject {Save-RoleRecord -ProjectPath $root -Role master -ConversationId $id -PaneId 'w3:p1' -HerdrSession 'project-management' -Source user_report -Evidence 'concurrent' -Store $store}}finally{$handle.Dispose()}
Assert ((Get-RoleRecord -ProjectPath $root -Role master -Store $store).conversation_id -eq $id) '동시 저장 실패 후 원본 보존'
Write-Output "PASS: $count checks. Synthetic snapshots only; no live herdr control, agent start or model call. $testRoot"
