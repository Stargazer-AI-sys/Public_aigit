#requires -Version 7.0
# Reproducible project-local installs. No global PATH, shell policy or auth changes.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$installRoot = Join-Path $projectPath '.local/bin'
New-Item -ItemType Directory -Force $installRoot | Out-Null
$packages = @(
    @{Name='herdr'; Version='0.9.5'; File='herdr-v0.9.5.zip'; Url='https://github.com/herdrdev/herdr/releases/download/v0.9.5/herdr-windows-x86_64.zip'; Hash='d2c6c9c971c43a0bfdde8c692a9a1a7a45c3e4807cd01ae45662b4734fac1cbf'},
    @{Name='claude'; Version='2.1.308'; File='claude/claude.exe'; Url='https://downloads.claude.ai/claude-code-releases/2.1.308/win32-x64/claude.exe'; Hash='c9796ba22a9221586b36371b36f5b66198d66eb4badf6a4cf4a5f7b07becea53'}
)
foreach ($package in $packages) {
    $destination = Join-Path $installRoot $package.File
    New-Item -ItemType Directory -Force (Split-Path $destination) | Out-Null
    if (-not (Test-Path -LiteralPath $destination)) {
        Invoke-WebRequest -Uri $package.Url -OutFile $destination -TimeoutSec 120
    }
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLower() -ne $package.Hash) {
        throw "$($package.Name) 검증 실패. 기존 파일은 자동 교체하지 않습니다."
    }
    if ($package.Name -eq 'herdr') {
        $expandedPath = Join-Path $installRoot 'herdr'
        if (-not (Test-Path -LiteralPath $expandedPath)) {
            Expand-Archive -LiteralPath $destination -DestinationPath $expandedPath
        }
        # Validate the installed tree against the verified archive without replacing user files.
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $archive = [System.IO.Compression.ZipFile]::OpenRead($destination)
        try {
            foreach ($entry in $archive.Entries) {
                if ($entry.Name -eq '') { continue }
                $installedFile = [IO.Path]::GetFullPath((Join-Path $expandedPath $entry.FullName))
                if (-not $installedFile.StartsWith(([IO.Path]::GetFullPath($expandedPath) + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) { throw '압축 경로 오류' }
                if (-not (Test-Path -LiteralPath $installedFile -PathType Leaf)) { throw 'herdr 설치 파일 누락' }
                $stream = $entry.Open()
                try { $expectedHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)) } finally { $stream.Dispose() }
                if ((Get-FileHash -LiteralPath $installedFile).Hash -ne $expectedHash) { throw 'herdr 설치 파일 불일치' }
            }
        } finally { $archive.Dispose() }
    }
    Write-Output "$($package.Name) $($package.Version): 다운로드·설치 파일 검증 통과"
}
