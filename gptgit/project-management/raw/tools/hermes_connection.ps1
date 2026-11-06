#requires -Version 7.0
[CmdletBinding()]
param([ValidateSet('Check','Login')][string]$Action='Check')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$previousHome=$env:HERMES_HOME
try {
    # The managed install's runtime lookup depends on its data directory.
    # A plain hermes.exe launch otherwise selects the user's default home.
    $env:HERMES_HOME=(Resolve-Path .local/hermes-setup/data).Path
    $exe='./.local/hermes-setup/data/bin/hermes.exe'
    if(-not (Test-Path -LiteralPath $exe -PathType Leaf)){throw '프로젝트 Hermes 설치를 찾을 수 없습니다.'}
    if($Action -eq 'Check'){
        & $exe --version
        if($LASTEXITCODE -ne 0){throw 'Hermes 런타임 검사 실패'}
        & $exe auth status nous
        $result=$LASTEXITCODE
        Write-Host '이 검사는 모델 호출·플랜 공유·추가 과금 여부를 검증하지 않습니다. logged out은 아직 로그인하지 않은 상태입니다.'
    } else {
        # Invoke only after explicit consent to Nous linking and ChatGPT plan sharing.
        # Auth alone never enables the tool gateway or selects a paid model.
        & $exe auth add nous --type oauth --no-browser --timeout 300
        $result=$LASTEXITCODE
    }
} finally {
    if($null -eq $previousHome){Remove-Item Env:HERMES_HOME -ErrorAction SilentlyContinue}else{$env:HERMES_HOME=$previousHome}
}
exit $result
