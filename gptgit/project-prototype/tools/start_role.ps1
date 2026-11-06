[CmdletBinding()]
param(
 [ValidateSet('master','planner','planning-reviewer','developer','qa')][string]$Role='master',
 [string]$Packet,
 [string]$Model,
 [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$config=Join-Path $root 'config/runtime.local.json'
if(-not (Test-Path -LiteralPath $config)){$config=Join-Path $root 'config/runtime.example.json'}
$runtime=Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
$provider=if($Role -in @('planning-reviewer','developer')){'claude'}else{'codex'}
$exe=$runtime.$provider
if(-not (Get-Command $exe -ErrorAction SilentlyContinue)){throw "$provider 실행 파일 없음. config/runtime.local.json을 확인하세요."}
foreach($key in @('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL','OPENAI_API_BASE','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY')){
 if([Environment]::GetEnvironmentVariable($key)){throw "구독 외 연결 가능 설정 발견: $key. 자동 변경하지 않습니다."}
}
$prompt=if($Role -eq 'master'){'README.md와 AGENTS.md에서 시작하고 승인된 작업만 수행하세요.'}else{'마스터가 실제 모델을 확인하고 작업을 전달할 때까지 대기하세요. 작업을 시작하지 마세요.'}
if($Role -ne 'master'){
 if(-not $Packet){throw '담당 역할에는 검증할 Task packet이 필요합니다.'}
 $packetCheck=& $runtime.python -B ./tools/task_packet.py $Packet --root $root
 if($LASTEXITCODE -ne 0){throw "Task packet 검사 실패: $packetCheck"}
 $data=Get-Content -LiteralPath $Packet -Raw -Encoding UTF8 | ConvertFrom-Json
 if($data.role -ne $Role){throw 'packet 역할 불일치'}
 $packetModel=$data.session.model
 if($Model -and $packetModel -and $Model -ne $packetModel){throw 'Model과 packet 모델 불일치'}
 if(-not $Model){$Model=$packetModel}
}
if(-not $Model -or -not $Model.Trim()){throw '명시적인 모델이 필요합니다.'}
$checker=Join-Path (Split-Path -Parent $root) 'tools/check_agent_model.py'
if(-not (Test-Path -LiteralPath $checker)){throw '공유 모델 검사기가 없습니다.'}
$checkOutput=& $runtime.python -B $checker --role $Role --provider $provider --model $Model
if($LASTEXITCODE -ne 0){throw "모델 검사 실패: $checkOutput"}
try {$checkResult=$checkOutput | ConvertFrom-Json} catch {throw '모델 검사 결과가 JSON이 아닙니다.'}
if($checkResult.valid -ne $true){throw '모델 검사 결과가 유효하지 않습니다.'}
if($provider -eq 'codex'){
 $native=@('--cd',$root,'--model',$Model,'--no-daemon','--ask-for-approval','on-request','-c','approvals_reviewer="auto_review"','-c','forced_login_method="chatgpt"')
 if($Role -eq 'qa'){$native+=@('--sandbox','read-only')}else{$native+=@('--sandbox','workspace-write')}
 $native+=$prompt
}else{
 $settings=@{autoMemoryEnabled=$false;disableAllHooks=$true;permissions=@{deny=@('Read(../**)')}} | ConvertTo-Json -Depth 5 -Compress
 $native=@('--model',$Model,'--setting-sources','project','--settings',$settings,'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--permission-mode','auto','--append-system-prompt',(Get-Content ./CLAUDE.md -Raw -Encoding UTF8))
 if($Role -eq 'planning-reviewer'){$native+=@('--tools','Read,Grep,Glob')}
 $native+=$prompt
}
if($CheckOnly){@{role=$Role;provider=$provider;model=$Model;executable=$exe;arguments=$native;model_called=$false;authentication_checked=$false} | ConvertTo-Json -Depth 6;exit 0}
if($env:HERDR_ENV -ne '1'){throw '실제 역할 시작은 herdr 내부에서 마스터가 수행해야 합니다.'}
if($provider -eq 'codex'){
 # Native stderr may contain the successful login status in Windows PowerShell.
 # Limit the non-terminating preference to this command and always restore it.
 $previousErrorActionPreference=$ErrorActionPreference
 try {
  $ErrorActionPreference='Continue'
  $auth=& $exe login status 2>&1 | Out-String
  $authExitCode=$LASTEXITCODE
 } finally {$ErrorActionPreference=$previousErrorActionPreference}
 if($authExitCode -ne 0 -or $auth -notmatch 'Logged in using ChatGPT'){throw 'ChatGPT 로그인 확인 필요'}
}else{
 $auth=& $exe auth status | ConvertFrom-Json
 if($LASTEXITCODE -ne 0 -or -not $auth.loggedIn -or $auth.authMethod -ne 'claude.ai' -or $auth.subscriptionType -notin @('pro','max')){throw 'Claude 구독 판정 확인 필요. null도 성공으로 간주하지 않습니다.'}
}
& $exe @native
exit $LASTEXITCODE
