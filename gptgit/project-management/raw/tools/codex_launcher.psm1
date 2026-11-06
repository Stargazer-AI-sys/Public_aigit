#requires -Version 7.0
Set-StrictMode -Version Latest

function Resolve-CodexExecutable {
    [CmdletBinding()]
    param(
        [string]$CodexPath,
        [string[]]$CommandPaths,
        [string[]]$DesktopRoots
    )
    if ($CodexPath) {
        if (-not (Test-Path -LiteralPath $CodexPath -PathType Leaf) -or
            [IO.Path]::GetExtension($CodexPath) -notin @('.exe', '.cmd')) {
            throw '지정한 CodexPath에 실행 파일(.exe 또는 .cmd)이 없습니다. 현재 설치 위치를 확인하세요.'
        }
        return [pscustomobject]@{ path = (Get-Item -LiteralPath $CodexPath).FullName; source = 'explicit' }
    }
    if (-not $PSBoundParameters.ContainsKey('DesktopRoots')) {
        $DesktopRoots = @(
            if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'OpenAI/Codex/bin' }
            if ($env:USERPROFILE) { Join-Path $env:USERPROFILE 'AppData/Local/OpenAI/Codex/bin' }
        ) | Select-Object -Unique
    }
    if (-not $PSBoundParameters.ContainsKey('CommandPaths')) {
        $CommandPaths = @(Get-Command codex -All -CommandType Application -ErrorAction SilentlyContinue |
            ForEach-Object { $_.Source })
    }
    # A desktop build may remain on PATH after an update. Never let that old
    # build take priority over an installed standalone CLI or a newer build.
    $desktopPaths = [System.Collections.Generic.List[string]]::new()
    foreach ($candidate in $CommandPaths) {
        if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        if ([IO.Path]::GetExtension($candidate) -notin @('.exe', '.cmd')) { continue }
        $fullPath = (Get-Item -LiteralPath $candidate).FullName
        $isDesktop = $fullPath -match '[\\/]OpenAI[\\/]Codex[\\/]bin[\\/][^\\/]+[\\/]codex\.exe$'
        foreach ($root in $DesktopRoots) {
            if ($root -and $fullPath.StartsWith(([IO.Path]::GetFullPath($root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
                $isDesktop = $true
            }
        }
        if (-not $isDesktop) { return [pscustomobject]@{ path = $fullPath; source = 'path' } }
        $desktopPaths.Add($fullPath)
    }
    foreach ($root in $DesktopRoots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        foreach ($directory in Get-ChildItem -LiteralPath $root -Directory) {
            $candidate = Join-Path $directory.FullName 'codex.exe'
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { $desktopPaths.Add($candidate) }
        }
    }
    $newest = $desktopPaths | Select-Object -Unique | ForEach-Object { Get-Item -LiteralPath $_ } |
        Sort-Object @{ Expression = 'LastWriteTimeUtc'; Descending = $true }, FullName | Select-Object -First 1
    if ($newest) { return [pscustomobject]@{ path = $newest.FullName; source = 'desktop' } }
    throw 'Codex 실행 파일을 찾지 못했습니다. 이 PC에 Codex CLI를 설치한 뒤 새 터미널을 열거나 -CodexPath로 실제 실행 파일을 지정하세요.'
}

function Get-CodexVersion {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)
    $PSNativeCommandUseErrorActionPreference = $false
    try {
        $output = (& $Path --version 2>&1 | Out-String)
        $code = $LASTEXITCODE
    } catch {
        throw "Codex 파일은 찾았지만 실행하지 못했습니다: $Path. 설치 상태·접근 권한을 확인하세요."
    }
    $versionLine = @($output -split '\r?\n' | Where-Object { $_ -match '^codex(?:-cli)?\s+\S+' }) | Select-Object -First 1
    if ($code -ne 0 -or -not $versionLine) {
        throw "Codex 파일은 찾았지만 버전 확인에 실패했습니다: $Path. 설치를 복구하거나 -CodexPath로 정상 CLI를 지정하세요."
    }
    return $versionLine.Trim()
}

Export-ModuleMember -Function Resolve-CodexExecutable, Get-CodexVersion
