#requires -Version 7.0
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'project_hub.psm1') -Force
$root=Split-Path -Parent $PSScriptRoot
$testRoot=Join-Path $root ('.local/hub-tests/' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$count=0
function Assert($condition,$message) { if (-not $condition) { throw $message }; $script:count++ }
function Must-Reject([scriptblock]$action) { $failed=$false; try { & $action | Out-Null } catch { $failed=$true }; Assert $failed '위험/중복 입력이 거절되지 않음' }
$purpose='문서 비교 도구. $(무실행) `리터럴` {{NAME}}'
$a=New-ManagedProject -Parent $testRoot -Name '한글 프로젝트' -Purpose $purpose
$b=New-ManagedProject -Parent $testRoot -Name '두 번째' -Purpose '다른 목적'
Assert ((Get-Content (Join-Path $a.Path 'docs/project.md') -Raw).Contains($purpose)) '사용자 입력 변형'
Assert (@(Get-ChildItem $a.Path -File -Recurse -Force).Count -eq 5) '불필요한 파일 복사'
$meta=Get-Content (Join-Path $a.Path '.project-management.json') -Raw | ConvertFrom-Json
Assert ($meta.template_version -eq '1.0' -and @($meta.conversation_sessions.PSObject.Properties).Count -eq 0) '과거 대화/버전 오염'
$before=(Get-FileHash (Join-Path $a.Path 'README.md')).Hash
Must-Reject { New-ManagedProject -Parent $testRoot -Name '한글 프로젝트' -Purpose '덮어쓰기' }
Assert ((Get-FileHash (Join-Path $a.Path 'README.md')).Hash -eq $before) '기존 파일 변경'
foreach ($bad in @('../escape','..','CON','a/b','a\b','tail.',' name','COM1.txt')) { Must-Reject { New-ManagedProject -Parent $testRoot -Name $bad -Purpose '거절' } }
Must-Reject { New-ManagedProject -Parent $testRoot -Name '빈 목적' -Purpose ' ' }
$reopen=Get-ProjectTarget -Path $a.Path
Assert ($reopen.Session -eq $a.Session -and $a.Session -ne $b.Session) '프로젝트 세션 분리 실패'
Assert ($reopen.Path -eq $a.Path) '기존 폴더 선택 경로 변경'
Assert ((Get-ProjectTarget -Path $root).Session -eq 'project-management') '관리 세션 호환 실패'
$loose=Join-Path $testRoot '기존 자료'
New-Item -ItemType Directory -Path $loose | Out-Null
Get-ProjectTarget -Path $loose | Out-Null
Assert (@(Get-ChildItem $loose -Force).Count -eq 0) '기존 폴더에 자동 문서 생성'
Write-Output "PASS: $count checks. Test files retained at $testRoot"
