#requires -Version 7.0
[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectPath
try {
    $pwsh = (Get-Process -Id $PID).Path
    if ($CheckOnly) {
        Import-Module ./tools/project_hub.psm1 -Force
        Get-ProjectTarget -Path . | ConvertTo-Json
        foreach ($required in @('tools/project_hub_ui.ps1','templates/project-v1/README.md','.local/bin/herdr/herdr.exe')) {
            if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "필수 파일 없음: $required" }
        }
        exit 0
    }
    & $pwsh -NoProfile -STA -File ./tools/project_hub_ui.ps1
    exit $LASTEXITCODE
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    if (-not $CheckOnly) { Read-Host '내용을 확인한 뒤 Enter를 누르면 닫힙니다' | Out-Null }
    exit 1
}
