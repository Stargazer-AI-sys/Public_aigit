#requires -Version 7.0
[CmdletBinding()]
param([switch]$CheckOnly, [switch]$InspectOnly, [switch]$ResumeSaved)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectPath
$profilePath = (Resolve-Path '../../automation-agents/claude').Path
$claudeExe = Join-Path $projectPath '.local/bin/claude/claude.exe'
foreach ($path in @($claudeExe, "$profilePath/CLAUDE.md", "$profilePath/.claude/settings.json", "$profilePath/.claude/skills/automation-handoff/SKILL.md")) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "필수 파일 없음: $path" }
}
foreach ($name in @('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY')) {
    if ([Environment]::GetEnvironmentVariable($name)) { throw "구독 외 연결 설정 발견: $name. 자동 변경하지 않습니다." }
}
$auth = (& $claudeExe auth status | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or -not $auth.loggedIn -or $auth.authMethod -ne 'claude.ai' -or $auth.subscriptionType -ne 'pro') {
    throw 'Claude Pro 로그인 확인 필요. API 연결로 대체하지 않습니다.'
}
$settings = Get-Content "$profilePath/.claude/settings.json" -Raw | ConvertFrom-Json -AsHashtable
# These are per-process settings. No user settings or global PATH is rewritten.
$legacyClaudePath = [IO.Path]::GetFullPath((Join-Path $projectPath '../../Claudecode')).Replace('\','/')
$userClaudePath = (Join-Path $env:USERPROFILE '.claude').Replace('\','/')
$settings.claudeMdExcludes = @("$userClaudePath/CLAUDE.md", "$userClaudePath/rules/**", "$legacyClaudePath/**")
$settings.permissions = @{ deny = @(
    'Read(./guide_docs/AI_작업_요청과_재개_가이드.html)',
    'Read(./docs/workflows/guide-prototype/01-planning/**)',
    'Read(../skills/simple-user-guide/**)',
    'Read(../../Claudecode/**)'
) }
$env:CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD = '1'
$env:CLAUDE_CODE_DISABLE_AUTO_MEMORY = '1'
$env:DISABLE_AUTOUPDATER = '1'
$argsForClaude = @('--add-dir', $profilePath, '--setting-sources', 'project', '--settings', ($settings | ConvertTo-Json -Depth 10 -Compress), '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--permission-mode', 'manual')
if ($InspectOnly) { $argsForClaude += @('--tools', '') }
if ($CheckOnly) {
    [pscustomobject]@{
        project = $projectPath; profile = $profilePath; authentication = 'claude.ai / pro'
        cli = (& $claudeExe --version | Out-String).Trim(); interactive = $true
        userSettingsLoaded = $false; automaticMemory = $false; externalMcpServers = $false
        settings = $settings; modelCalled = $false
        limitation = 'Configuration checks only; confirm /context, /memory and /skills in the interactive session. Directory separation is not an OS sandbox.'
    } | ConvertTo-Json -Depth 10
    exit 0
}
if ($InspectOnly -and $ResumeSaved) { throw '로딩 검사와 기존 작업 재개를 동시에 실행하지 않습니다.' }
if ($InspectOnly) {
    & $claudeExe @argsForClaude
    exit $LASTEXITCODE
}
Import-Module (Join-Path $PSScriptRoot 'agent_sessions.psm1') -Force
$gate = Enter-RoleStart -ProjectPath $projectPath -Role producer -ResumeSaved:$ResumeSaved
if ($gate.decision.action -eq 'reuse') { $gate.decision | ConvertTo-Json; exit 0 }
try {
    if ($gate.decision.action -eq 'resume') { $argsForClaude += @('--resume', $gate.decision.conversation_id) }
    & $claudeExe @argsForClaude
    $agentExitCode = $LASTEXITCODE
} finally { $gate.lease.Dispose() }
exit $agentExitCode
