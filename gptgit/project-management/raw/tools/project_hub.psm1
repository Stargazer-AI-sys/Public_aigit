#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ManagementRoot = Split-Path -Parent $PSScriptRoot

function Get-ProjectTarget {
    param([Parameter(Mandatory)][string]$Path)
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    if (-not (Test-Path -LiteralPath $resolved -PathType Container)) { throw '프로젝트 폴더를 선택하세요.' }
    $bytes = [Text.Encoding]::UTF8.GetBytes($resolved.TrimEnd('\','/').ToLowerInvariant())
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    $session = if ($resolved -eq $script:ManagementRoot) { 'project-management' } else { 'project-' + $hash.Substring(0,20) }
    [pscustomobject]@{ Path=$resolved; Name=(Split-Path $resolved -Leaf); Session=$session }
}

function New-ManagedProject {
    param([Parameter(Mandatory)][string]$Parent, [Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Purpose)
    if ($Name -ne $Name.Trim() -or $Name -match '[<>:"/\\|?*\x00-\x1f]' -or $Name -match '[. ]$' -or $Name -in @('.','..') -or $Name -match '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)' -or $Name.Length -gt 80) {
        throw '경로 대신 80자 이내의 올바른 프로젝트 이름을 입력하세요.'
    }
    if ([string]::IsNullOrWhiteSpace($Purpose)) { throw '프로젝트 목적을 입력하세요.' }
    $parentPath = (Resolve-Path -LiteralPath $Parent).Path
    if (-not (Test-Path -LiteralPath $parentPath -PathType Container)) { throw '저장할 상위 폴더가 없습니다.' }
    $target = Join-Path $parentPath $Name
    if (Test-Path -LiteralPath $target) { throw '같은 이름의 파일 또는 폴더가 있습니다. 기존 프로젝트 열기를 사용하세요.' }
    $templateRoot = Join-Path $script:ManagementRoot 'templates/project-v1'
    # Prepare all source text before creating anything. Literal replacement never evaluates user text.
    $contents = @{}
    foreach ($relative in @('README.md','AGENTS.md','docs/project.md','docs/04_records/work_log.md')) {
        $source = Get-Content -LiteralPath (Join-Path $templateRoot $relative) -Raw
        $contents[$relative] = [regex]::Replace($source, '\{\{(NAME|PURPOSE)\}\}', {
            param($match)
            if ($match.Groups[1].Value -eq 'NAME') { $Name } else { $Purpose }
        })
    }
    # No -Force: a concurrent creation must fail, never overwrite another project.
    New-Item -ItemType Directory -Path $target -ErrorAction Stop | Out-Null
    try {
        foreach ($relative in $contents.Keys) {
            $destination = Join-Path $target $relative
            [IO.Directory]::CreateDirectory((Split-Path $destination -Parent)) | Out-Null
            [IO.File]::WriteAllText($destination, $contents[$relative], [Text.UTF8Encoding]::new($false))
        }
        $metadata = @{ schema_version=1; template_version='1.0'; name=$Name; created_at=[DateTimeOffset]::Now.ToString('o'); conversation_sessions=@{} }
        [IO.File]::WriteAllText((Join-Path $target '.project-management.json'), ($metadata | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
        Get-ProjectTarget -Path $target
    } catch {
        throw "생성이 완료되지 않았습니다. 일부 파일을 보존했습니다. 확인할 위치: $target. $($_.Exception.Message)"
    }
}
Export-ModuleMember -Function Get-ProjectTarget,New-ManagedProject
