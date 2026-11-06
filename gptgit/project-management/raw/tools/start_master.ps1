#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$LoginClaude,
    [switch]$LoginCodex,
    [switch]$CheckOnly,
    [switch]$ResumeSaved,
    [switch]$NoDaemon,
    [string]$CodexPath
)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$herdrExe = Join-Path $projectPath '.local/bin/herdr/herdr.exe'
$claudeExe = Join-Path $projectPath '.local/bin/claude/claude.exe'
if (($LoginClaude -and $LoginCodex) -or (($LoginClaude -or $LoginCodex) -and ($CheckOnly -or $ResumeSaved -or $NoDaemon))) {
    throw '로그인은 -LoginCodex 또는 -LoginClaude만 선택하세요. 점검·재개·실행 옵션과 함께 사용하지 않습니다.'
}
foreach ($credentialName in @('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')) {
    if ([Environment]::GetEnvironmentVariable($credentialName)) { throw "구독 전용 시작을 위해 $credentialName 설정을 제거한 별도 터미널을 사용하세요. 자동 변경하지 않습니다." }
}
if ($LoginClaude) {
    if (-not (Test-Path -LiteralPath $claudeExe -PathType Leaf)) { throw 'Claude Code를 먼저 설치하세요.' }
    & $claudeExe auth login --claudeai
    exit $LASTEXITCODE
}
Import-Module (Join-Path $PSScriptRoot 'codex_launcher.psm1') -Force
$resolved = Resolve-CodexExecutable -CodexPath $CodexPath
$codexExe = $resolved.path
$codexVersion = Get-CodexVersion -Path $codexExe
if ($LoginCodex) {
    & $codexExe login -c 'forced_login_method="chatgpt"'
    exit $LASTEXITCODE
}
if (-not (Test-Path -LiteralPath $herdrExe -PathType Leaf)) { throw '프로젝트의 herdr가 없습니다. 이 PC에서 tools/install_local_agents.ps1 설치 절차를 확인하세요.' }
$PSNativeCommandUseErrorActionPreference = $false
try { $loginStatus = (& $codexExe login status 2>&1 | Out-String); $loginExitCode = $LASTEXITCODE }
catch { throw 'Codex 로그인 상태를 조회하지 못했습니다. -CodexPath로 정상 CLI를 지정하거나 설치 상태를 확인하세요.' }
if ($loginExitCode -ne 0 -or $loginStatus -notmatch 'Logged in using ChatGPT') {
    throw 'ChatGPT 로그인이 필요합니다. ./tools/start_master.ps1 -LoginCodex 실행 후 다시 확인하세요. 별도 경로를 지정했다면 같은 -CodexPath를 사용하세요.'
}
if ($CheckOnly) {
    [pscustomobject]@{
        project = $projectPath; codex = $codexExe; version = $codexVersion; source = $resolved.source
        login = 'ChatGPT'; herdr = $herdrExe; insideHerdr = ($env:HERDR_ENV -eq '1')
        mode = $(if ($NoDaemon) { 'no-daemon' } else { 'shared-server' })
        note = '경로·버전·로그인 점검만 완료. herdr 연결·대화 화면·공유 서버 동작은 시험하지 않았습니다.'
    } | ConvertTo-Json
    exit 0
}
$originalPath = $env:PATH
$originalLocation = Get-Location
try {
    # Child processes inherit this PATH; user/system PATH is never changed.
    $env:PATH = "$(Split-Path $codexExe);$(Split-Path $herdrExe);$(Split-Path $claudeExe);$originalPath"
    Set-Location -LiteralPath $projectPath
    Write-Host "프로젝트: $projectPath"
    Write-Host "Codex: $codexExe ($codexVersion)"
    if ($env:HERDR_ENV -eq '1') {
        Import-Module (Join-Path $PSScriptRoot 'agent_sessions.psm1') -Force
        $gate = Enter-RoleStart -ProjectPath $projectPath -Role master -ResumeSaved:$ResumeSaved
        if ($gate.decision.action -eq 'reuse') { $gate.decision | ConvertTo-Json; exit 0 }
        try {
            $argsForCodex = @('--cd', $projectPath, '-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"')
            if ($NoDaemon) { $argsForCodex += '--no-daemon' }
            if ($gate.decision.action -eq 'resume') { $argsForCodex = @('resume', $gate.decision.conversation_id) + $argsForCodex }
            # No automatic prompt or retry. Preserve the existing role/duplicate gate.
            & $codexExe @argsForCodex
            $agentExitCode = $LASTEXITCODE
            if ($agentExitCode -ne 0) {
                Write-Warning "Codex 종료 코드: $agentExitCode. 위 오류를 확인하세요. 공유 서버 오류라면 다음에 -NoDaemon으로 실행할 수 있습니다. 자동 재실행하지 않습니다."
            }
        } finally { $gate.lease.Dispose() }
        exit $agentExitCode
    } else {
        if ($ResumeSaved) { throw '대화 재개는 herdr 내부에서만 실행하세요. 외부에서 현재 창을 제어하지 않습니다.' }
        $nextCommand = './tools/start_master.ps1'
        if ($NoDaemon) { $nextCommand += ' -NoDaemon' }
        if ($CodexPath) { $nextCommand += " -CodexPath '" + $codexExe.Replace("'", "''") + "'" }
        Write-Host "herdr 안의 프로젝트 PowerShell에서 다시 실행하세요: $nextCommand"
        & $herdrExe --session project-management
        exit $LASTEXITCODE
    }
} finally {
    $env:PATH = $originalPath
    Set-Location -LiteralPath $originalLocation.Path
}
