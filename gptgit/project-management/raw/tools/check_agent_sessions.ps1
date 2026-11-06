#requires -Version 7.0
[CmdletBinding()]
param([switch]$Live)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'agent_sessions.psm1') -Force
$projectPath=Split-Path -Parent $PSScriptRoot
$result=@{schema_version=2;project=$projectPath;mode=$(if($Live){'live-read-only'}else{'saved-records-only'});roles=@{};modelCalled=$false;startsAgent=$false;note='창 유지 판정과 대화 ID 검증은 별개입니다. matched도 복원 성공이나 새 작업 전송 허가를 의미하지 않습니다.'}
foreach($role in @('master','producer')) {
    $record=Get-RoleRecord -ProjectPath $projectPath -Role $role
    $result.roles[$role]=@{saved_record=$record}
    if($Live){$result.roles[$role].decision=Get-LiveRolePlan -ProjectPath $projectPath -Role $role -ResumeSaved}
    else {$result.roles[$role].verification=@{window='not_checked';conversation='not_checked';source='none';reason='저장 기록만 조회했습니다. 현재 세션은 조회하지 않았습니다.'}}
}
$result | ConvertTo-Json -Depth 10
