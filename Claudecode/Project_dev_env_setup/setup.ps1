# 새 컴퓨터 개발환경 세팅 스크립트 (초안)
# 사용법과 옵션 설명은 같은 폴더의 README.md 참고
#
# 실행 방법 (PowerShell):
#   .\setup.ps1             -> 필요한 프로그램을 실제로 설치
#   .\setup.ps1 -DryRun     -> 설치하지 않고 "무엇을 할지"만 출력 (처음엔 이걸로 확인 권장)
#
# git pull 은 이 스크립트가 설치하는 프로그램을 갱신하지 않는다.
# 그래서 여러 번 실행해도 안전하게, 이미 맞는 항목은 건너뛰도록 만들었다.

param(
    # -DryRun 을 붙이면 실제 설치 없이 실행 계획만 보여준다
    [switch]$DryRun
)

# 오류가 나면 계속 진행하지 않고 즉시 멈춘다 (문제를 놓치지 않기 위함)
$ErrorActionPreference = "Stop"

# 이 스크립트는 aigit\Claudecode\Project_dev_env_setup 에 있다.
# 새 PC에서 폴더 위치가 달라도 동작하도록 스크립트 위치에서 계산한다.
$aigitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

# ---------------------------------------------------------------
# 1) winget 으로 설치할 프로그램 목록
#    Version 을 적으면 그 버전으로 고정한다. $null 이면 최신 버전을 설치한다.
#    Node, Python, Docker 는 기준 PC(2026-11-03)와 같은 버전이다.
#    Command 는 winget 이 아닌 방식(Microsoft Store, 직접 설치 등)으로 이미 설치됐는지 확인하는 명령어다.
#    winget 목록에 없어도 이 명령이 동작하면 중복 설치로 실패하지 않도록 건너뛴다.
#    ID 찾기: winget search 프로그램이름
# ---------------------------------------------------------------
$wingetPackages = @(
    @{ Id = "Microsoft.PowerShell"; Version = $null;     Command = "pwsh" },    # PowerShell 7
    @{ Id = "Git.Git";              Version = $null;     Command = "git" },     # 코드 버전 관리 도구
    @{ Id = "OpenJS.NodeJS.LTS";    Version = "26.13.0"; Command = "node" },    # Node.js. npm 도 함께 설치됨
    @{ Id = "Python.Python.3.14";   Version = "3.14.7";  Command = "python" },  # Python
    @{ Id = "Docker.DockerDesktop"; Version = "4.97.0";  Command = "docker" }   # Docker Desktop
)

# ---------------------------------------------------------------
# 2) npm 으로 설치할 전역 도구 목록 (-g = 컴퓨터 어디서나 쓰는 명령어)
#    Command 가 이미 있으면 건너뛴다. 다른 방식으로 설치된 도구를 중복 설치하지 않기 위함이다.
# ---------------------------------------------------------------
$npmGlobalPackages = @(
    @{ Package = "@anthropic-ai/claude-code"; Command = "claude" },  # Claude Code
    @{ Package = "@openai/codex";             Command = "codex" }    # Codex CLI
)

# ---------------------------------------------------------------
# 3) herdr integration 목록. 설정 폴더가 있어야 설치할 수 있다.
# ---------------------------------------------------------------
$herdrIntegrations = @(
    @{ Name = "claude"; ConfigDir = (Join-Path $HOME ".claude") },
    @{ Name = "codex";  ConfigDir = (Join-Path $HOME ".codex") }
)

# ---------------------------------------------------------------
# 4) 프로젝트별 의존성 목록
#    라이브러리 이름은 여기 적지 않는다. 각 프로젝트의 잠금 파일이 원본이다.
#    폴더를 자동 검색하지 않는다. 실행 결과물 안의 package.json 까지 설치되기 때문이다.
# ---------------------------------------------------------------
$projects = @(
    @{
        Path     = "Claudecode\Project_webportfolio"
        LockFile = "package-lock.json"
        Stamp    = "node_modules\.package-lock.json"
        Install  = { npm ci }
        Check    = { npm run build }
    }
)

function Run-Step($description, [scriptblock]$action) {
    Write-Host "==> $description"
    if ($DryRun) {
        Write-Host "    (DryRun: 실행하지 않음)"
        return
    }
    # winget, npm 같은 외부 프로그램은 실패해도 PowerShell 오류가 나지 않아 종료 코드를 직접 확인한다
    $global:LASTEXITCODE = 0
    & $action
    if ($LASTEXITCODE -ne 0) {
        throw "실패 (종료 코드 $LASTEXITCODE): $description"
    }
}

# 방금 설치한 프로그램은 "현재 열린 터미널"의 PATH 에 아직 없어 다시 읽어온다.
function Update-SessionPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# 설치되어 있지 않으면 $null 을 돌려준다. winget 은 이때 0 이 아닌 코드로 끝나므로 초기화한다.
function Get-WingetInstalledVersion($id) {
    $output = winget list --id $id --exact --accept-source-agreements --disable-interactivity 2>&1 | Out-String
    $global:LASTEXITCODE = 0
    $match = [regex]::Match($output, "(?m)(?:^|\s)$([regex]::Escape($id))\s+(\S+)")
    if ($match.Success) { return $match.Groups[1].Value }
    return $null
}

# 명령어가 실제로 실행되는지 확인한다. Get-Command 만 쓰면 Microsoft Store 연결용 가짜 python.exe 도 찾아내므로
# 버전 출력까지 성공해야 설치된 것으로 본다.
function Test-CommandWorks($command) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { return $false }
    & $command --version *> $null
    $works = ($LASTEXITCODE -eq 0)
    $global:LASTEXITCODE = 0
    return $works
}

# winget 자체가 없으면 진행할 수 없으므로 먼저 확인
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget 을 찾을 수 없습니다. Microsoft Store 에서 '앱 설치 관리자'를 업데이트하세요."
}

# --- 프로그램 설치 ---
foreach ($package in $wingetPackages) {
    $id = $package.Id
    $wanted = $package.Version
    $installed = Get-WingetInstalledVersion $id

    if ($installed -and (-not $wanted -or $installed -eq $wanted)) {
        Write-Host "==> 건너뜀: $id $installed 이미 설치됨"
        continue
    }
    # winget 으로 설치한 기록은 없지만 같은 프로그램이 이미 동작하면 다른 방식으로 설치된 것이다.
    # 이때 winget 설치를 시도하면 "다른 버전이 이미 설치됨"(종료 코드 1638)으로 실패한다.
    if (-not $installed -and $package.Command -and (Test-CommandWorks $package.Command)) {
        Write-Warning "$id 은(는) winget 이 아닌 방식으로 이미 설치되어 있어 건너뜁니다. 버전은 직접 확인하세요: $($package.Command) --version"
        continue
    }
    # 기준보다 새 버전을 자동으로 낮추면 다른 프로젝트가 깨질 수 있어 사람이 판단하게 둔다
    if ($installed -and [version]$installed -gt [version]$wanted) {
        Write-Warning "$id 설치 버전 $installed 이(가) 기준 $wanted 보다 높습니다. 변경하지 않습니다."
        continue
    }

    $versionArgs = if ($wanted) { @("--version", $wanted) } else { @() }
    # --exact: 이름이 정확히 일치하는 것만, --silent: 설치 창 없이 조용히,
    # --accept-*-agreements: 약관 동의 질문 자동 통과
    Run-Step "winget 설치: $id $wanted" {
        winget install --id $id --exact --silent @versionArgs `
            --accept-package-agreements --accept-source-agreements
    }
}
Update-SessionPath

# --- npm 전역 도구 설치 ---
if (-not $DryRun -and -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Warning "npm 을 아직 찾을 수 없습니다. 터미널을 완전히 닫았다가 다시 열고 이 스크립트를 한 번 더 실행하세요."
    exit 1
}
foreach ($tool in $npmGlobalPackages) {
    if (Get-Command $tool.Command -ErrorAction SilentlyContinue) {
        Write-Host "==> 건너뜀: $($tool.Command) 이미 설치됨"
        continue
    }
    Run-Step "npm 전역 설치: $($tool.Package)" { npm install -g $tool.Package }
}
Update-SessionPath

# --- herdr 설치 ---
if (Get-Command herdr -ErrorAction SilentlyContinue) {
    Write-Host "==> 건너뜀: herdr 이미 설치됨"
} else {
    # 공식 설치 명령이다. 버전을 고를 수 없어 그 시점의 최신 버전이 설치된다.
    Run-Step "herdr 설치 (공식 설치 스크립트)" {
        powershell -ExecutionPolicy Bypass -c "irm https://herdr.dev/install.ps1 | iex"
    }
    Update-SessionPath
}

# --- herdr integration 설치 ---
$needsRerun = $false
$herdrReady = [bool](Get-Command herdr -ErrorAction SilentlyContinue)
foreach ($integration in $herdrIntegrations) {
    $name = $integration.Name
    if (-not (Test-Path -LiteralPath $integration.ConfigDir)) {
        # 설정 폴더는 첫 로그인 때 생긴다. 스크립트가 임의로 만들지 않는다.
        Write-Warning "$name 설정 폴더가 없어 integration 을 건너뜁니다. $name 에 로그인한 뒤 이 스크립트를 다시 실행하세요."
        $needsRerun = $true
        continue
    }
    if ($herdrReady) {
        $status = herdr integration status 2>&1 | Out-String
        if ($status -match "(?m)^$([regex]::Escape($name)):\s+current\b") {
            Write-Host "==> 건너뜀: herdr integration $name 최신 상태"
            continue
        }
    }
    Run-Step "herdr integration 설치: $name" { herdr integration install $name }
}

# --- 프로젝트 의존성 설치 ---
foreach ($project in $projects) {
    $projectDir = Join-Path $aigitRoot $project.Path
    if (-not (Test-Path -LiteralPath $projectDir)) {
        Write-Warning "프로젝트 폴더가 없어 건너뜁니다: $($project.Path)"
        continue
    }

    # 잠금 파일이 설치 기록보다 새로우면 git pull 로 의존성이 바뀐 것이다.
    # npm ci 는 node_modules 를 지우고 다시 만들므로 바뀌었을 때만 실행한다.
    $lockPath = Join-Path $projectDir $project.LockFile
    $stampPath = Join-Path $projectDir $project.Stamp
    if ((Test-Path -LiteralPath $stampPath) -and
        (Get-Item -LiteralPath $stampPath).LastWriteTime -ge (Get-Item -LiteralPath $lockPath).LastWriteTime) {
        Write-Host "==> 건너뜀: $($project.Path) 의존성 최신 상태"
        continue
    }

    Push-Location -LiteralPath $projectDir
    try {
        Run-Step "의존성 설치: $($project.Path)" $project.Install
        Run-Step "동작 확인: $($project.Path)" $project.Check
    } finally {
        Pop-Location
    }
}

# --- 결과 확인 ---
if (-not $DryRun) {
    Write-Host "==> 설치 확인 (버전 출력)"
    foreach ($command in "pwsh", "node", "npm", "git", "python", "docker", "herdr", "claude", "codex") {
        if (Get-Command $command -ErrorAction SilentlyContinue) {
            Write-Host "    $command : $(& $command --version 2>&1 | Select-Object -First 1)"
        } else {
            Write-Warning "$command 을(를) 찾을 수 없습니다. 터미널을 닫았다가 다시 열어 확인하세요."
        }
    }
}

Write-Host ""
if ($needsRerun) {
    Write-Host "아직 할 일: claude, codex 에 로그인한 뒤 이 스크립트를 한 번 더 실행하세요."
}
Write-Host "완료. 워크스페이스는 herdr pane 안에서 .\herdr_workspaces.ps1 로 만듭니다."
