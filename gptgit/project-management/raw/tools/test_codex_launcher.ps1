#requires -Version 7.0
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'codex_launcher.psm1') -Force
$testRoot = Join-Path (Split-Path -Parent $PSScriptRoot) ('.local/launcher-tests/' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$script:count = 0
function Assert($Value, [string]$Message) {
    if (-not $Value) { throw $Message }
    $script:count++
}
function Reject([scriptblock]$Action, [string]$Message) {
    $failed = $false
    try { & $Action | Out-Null } catch { $failed = $true }
    Assert $failed $Message
}
function Fixture([string]$Relative, [string]$Content = 'fixture') {
    $path = Join-Path $testRoot $Relative
    New-Item -ItemType Directory -Path (Split-Path $path) -Force | Out-Null
    Set-Content -LiteralPath $path -Value $Content -Encoding ascii
    return $path
}
$desktopRoot = Join-Path $testRoot 'profile with spaces/OpenAI/Codex/bin'
$old = Fixture 'profile with spaces/OpenAI/Codex/bin/old/codex.exe'
$new = Fixture 'profile with spaces/OpenAI/Codex/bin/new/codex.exe'
(Get-Item -LiteralPath $old).LastWriteTimeUtc = [datetime]'2025-01-01'
(Get-Item -LiteralPath $new).LastWriteTimeUtc = [datetime]'2026-01-01'
$standalone = Fixture 'standalone/codex.cmd'
$savedPath = $env:PATH
$result = Resolve-CodexExecutable -CommandPaths @($old) -DesktopRoots @($desktopRoot)
Assert ($result.path -eq $new -and $result.source -eq 'desktop') 'Old desktop PATH must not pin old build'
$result = Resolve-CodexExecutable -CommandPaths @((Join-Path $testRoot 'deleted/codex.exe')) -DesktopRoots @($desktopRoot)
Assert ($result.path -eq $new) 'Deleted PATH entry must not prevent desktop discovery'
$result = Resolve-CodexExecutable -CommandPaths @($old, $standalone) -DesktopRoots @($desktopRoot)
Assert ($result.path -eq $standalone -and $result.source -eq 'path') 'Standalone npm cmd must take priority'
$result = Resolve-CodexExecutable -CodexPath $old -CommandPaths @($standalone) -DesktopRoots @($desktopRoot)
Assert ($result.path -eq $old -and $result.source -eq 'explicit') 'Explicit override must be respected'
$result = Resolve-CodexExecutable -CommandPaths @() -DesktopRoots @((Join-Path $testRoot 'virtual-localappdata'), $desktopRoot)
Assert ($result.path -eq $new) 'Missing virtual LOCALAPPDATA must allow user profile fallback'
Reject { Resolve-CodexExecutable -CodexPath (Join-Path $testRoot 'missing.exe') } 'Missing explicit override must fail'
Reject { Resolve-CodexExecutable -CommandPaths @() -DesktopRoots @() } 'No installation must fail'
$textFile = Fixture 'codex.txt'
Reject { Resolve-CodexExecutable -CodexPath $textFile } 'Non executable override must fail'
Assert ($env:PATH -eq $savedPath) 'Resolution must not mutate PATH'

# Fake CLI commands only: never start an AI, herdr, a login or a model request.
$goodCli = Fixture 'fake cli/codex.cmd' @'
@echo off
if "%~1"=="--version" (
  echo codex-cli 9.9.9-test
  exit /b 0
)
if "%~1"=="login" if "%~2"=="status" (
  echo Logged in using ChatGPT
  exit /b 0
)
echo Unexpected interactive call 1>&2
exit /b 91
'@
Assert ((Get-CodexVersion -Path $goodCli) -eq 'codex-cli 9.9.9-test') 'Version probe must work with spaces and cmd'
$badCli = Fixture 'bad/codex.cmd' "@echo off`r`necho broken`r`nexit /b 12"
Reject { Get-CodexVersion -Path $badCli } 'Broken executable must fail distinctly'
$wrongCli = Fixture 'wrong/codex.cmd' "@echo off`r`necho some-other-program 1.0`r`nexit /b 0"
Reject { Get-CodexVersion -Path $wrongCli } 'Unrelated executable must fail version identification'

$fakeRoot = Join-Path $testRoot 'isolated project'
New-Item -ItemType Directory -Path (Join-Path $fakeRoot 'tools') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $fakeRoot '.local/bin/herdr') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $fakeRoot '.local/bin/herdr/herdr.exe') -Value 'must never run' -Encoding ascii
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'start_master.ps1') -Destination (Join-Path $fakeRoot 'tools/start_master.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'codex_launcher.psm1') -Destination (Join-Path $fakeRoot 'tools/codex_launcher.psm1')
$pwsh = (Get-Process -Id $PID).Path
$output = & $pwsh -NoProfile -File (Join-Path $fakeRoot 'tools/start_master.ps1') -CheckOnly -CodexPath $goodCli
Assert ($LASTEXITCODE -eq 0) 'CheckOnly should succeed without agent_sessions module or live herdr'
$diagnostic = ($output | Out-String) | ConvertFrom-Json
Assert ($diagnostic.project -eq $fakeRoot -and $diagnostic.mode -eq 'shared-server' -and $diagnostic.version -eq 'codex-cli 9.9.9-test') 'CheckOnly must report project version mode'
$output = & $pwsh -NoProfile -File (Join-Path $fakeRoot 'tools/start_master.ps1') -CheckOnly -NoDaemon -CodexPath $goodCli
Assert ($LASTEXITCODE -eq 0 -and (($output | Out-String | ConvertFrom-Json).mode -eq 'no-daemon')) 'NoDaemon check must remain non interactive'
Assert (-not (Test-Path (Join-Path $fakeRoot '.local/agent-sessions'))) 'CheckOnly must not enter role gate or create session state'
Assert ($env:PATH -eq $savedPath) 'Checks must preserve caller PATH'
Write-Output "PASS: $count checks. Synthetic paths and fake CLI only; no live herdr, AI, login or model call. $testRoot"
