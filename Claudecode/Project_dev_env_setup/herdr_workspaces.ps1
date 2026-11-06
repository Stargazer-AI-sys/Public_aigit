# 프로젝트별 herdr 워크스페이스를 만드는 스크립트
# 사용법은 같은 폴더의 README.md 참고
#
# 실행 방법 (herdr 안의 PowerShell pane):
#   .\herdr_workspaces.ps1 -DryRun   -> 만들지 않고 계획만 출력
#   .\herdr_workspaces.ps1           -> 없는 워크스페이스만 생성

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# 새 PC에서 폴더 위치가 달라도 동작하도록 스크립트 위치에서 계산한다.
$aigitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

# 새 프로젝트가 생기면 이 목록에 한 줄만 추가한다.
$workspaces = @(
    @{ Label = "director";           Path = "Claudecode\Project_director" },
    @{ Label = "process-manage";     Path = "Claudecode\Project_process_manage" },
    @{ Label = "refactor";           Path = "Claudecode\Project_Refactor" },
    @{ Label = "webportfolio";       Path = "Claudecode\Project_webportfolio" },
    @{ Label = "project-management"; Path = "gptgit\project-management" },
    @{ Label = "network-engineer";   Path = "gptgit\Project-NetworkEngineer" },
    @{ Label = "study-automanage";   Path = "gptgit\Project-StudyAutomanage" },
    @{ Label = "resume";             Path = "gptgit\재취업 이력서" }
)

# herdr 밖에서는 어떤 세션을 조작하게 될지 보장되지 않으므로 생성하지 않는다.
$insideHerdr = $env:HERDR_ENV -eq "1"
if (-not $insideHerdr -and -not $DryRun) {
    throw "herdr 안의 pane 에서 실행하세요. 현재 터미널은 herdr 밖입니다."
}

$existing = $null
if ($insideHerdr) {
    $existing = herdr workspace list | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "herdr workspace list 실패 (종료 코드 $LASTEXITCODE). 중복을 확인할 수 없어 중단합니다."
    }
} else {
    Write-Warning "herdr 밖이라 기존 워크스페이스를 확인하지 못했습니다. 아래는 전체 목록입니다."
}

# 응답의 JSON 구조가 공식 문서에 없어 필드 이름에 의존하지 않고 문자열 값으로 찾는다.
# 잘못 일치하더라도 중복을 만들지 않고 건너뛰는 쪽으로 동작한다.
function Test-AlreadyExists($text, $value) {
    $jsonValue = (ConvertTo-Json -InputObject $value -Compress).Trim('"')
    return $text -match ('"' + [regex]::Escape($jsonValue) + '(\\\\)?"')
}

$created = 0
$skipped = 0
foreach ($workspace in $workspaces) {
    $label = $workspace.Label
    $fullPath = Join-Path $aigitRoot $workspace.Path

    if (-not (Test-Path -LiteralPath $fullPath -PathType Container)) {
        Write-Warning "폴더가 없어 건너뜁니다: $($workspace.Path)"
        $skipped++
        continue
    }

    if ($existing) {
        $folderName = Split-Path -Leaf $fullPath
        if ((Test-AlreadyExists $existing $label) -or
            (Test-AlreadyExists $existing $folderName) -or
            (Test-AlreadyExists $existing $fullPath)) {
            Write-Host "==> 건너뜀: $label 이미 있음"
            $skipped++
            continue
        }
    }

    Write-Host "==> 생성: $label ($($workspace.Path))"
    if ($DryRun) {
        Write-Host "    (DryRun: 실행하지 않음)"
        continue
    }
    herdr workspace create --cwd $fullPath --label $label --no-focus | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "워크스페이스 생성 실패 (종료 코드 $LASTEXITCODE): $label"
    }
    $created++
}

Write-Host ""
Write-Host "완료. 생성 $created 개, 건너뜀 $skipped 개"
