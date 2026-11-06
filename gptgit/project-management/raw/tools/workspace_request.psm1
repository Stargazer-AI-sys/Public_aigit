#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function New-WorkspaceRequest {
    param([string]$ProjectPath,[string]$Store)
    $path=(Resolve-Path -LiteralPath $ProjectPath).Path
    [IO.Directory]::CreateDirectory($Store) | Out-Null
    $file=Join-Path $Store 'request.json'
    $lock=[IO.File]::Open((Join-Path $Store 'request.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try {
        if(Test-Path -LiteralPath $file){
            $old=Get-Content $file -Raw | ConvertFrom-Json -AsHashtable
            if($old.project_path -ne $path){throw '다른 프로젝트 요청이 있습니다.'}
            if($old.status -in @('pending','processing','uncertain')){return $old}
        }
        $request=@{schema_version=1;request_id=[guid]::NewGuid().ToString('D');project_path=$path;herdr_session='project-management';resume_saved=$true;status='pending';created_at=[DateTimeOffset]::Now.ToString('o');roles=@{}}
        Write-WorkspaceRequest -Request $request -Store $Store
        return $request
    } finally {$lock.Dispose()}
}
function Write-WorkspaceRequest {
    param([hashtable]$Request,[string]$Store)
    $file=Join-Path $Store 'request.json'
    $tmp=Join-Path $Store ([guid]::NewGuid().ToString('N')+'.tmp')
    [IO.File]::WriteAllText($tmp,($Request | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    [IO.File]::Move($tmp,$file,$true)
}
function Get-WorkspaceRequest {
    param([string]$ProjectPath,[string]$Store)
    $request=Get-Content (Join-Path $Store 'request.json') -Raw | ConvertFrom-Json -AsHashtable
    if($request.schema_version -ne 1 -or $request.project_path -ne (Resolve-Path -LiteralPath $ProjectPath).Path -or $request.herdr_session -ne 'project-management' -or $request.resume_saved -ne $true){throw '프로젝트 연결 요청이 일치하지 않습니다.'}
    $id=[guid]::Empty
    if(-not [guid]::TryParseExact($request.request_id,'D',[ref]$id)){throw '요청 ID가 잘못됐습니다.'}
    return $request
}
Export-ModuleMember -Function New-WorkspaceRequest,Get-WorkspaceRequest,Write-WorkspaceRequest
