#requires -Version 7.0
[CmdletBinding()]
param([switch]$PreviewOnly)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'project_hub.psm1') -Force
Import-Module (Join-Path $PSScriptRoot 'workspace_request.psm1') -Force
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$managementRoot = Split-Path -Parent $PSScriptRoot
$form = [System.Windows.Forms.Form]::new()
$form.Text = '프로젝트 관리'
$form.ClientSize = [Drawing.Size]::new(700,540)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.Font = [Drawing.Font]::new('맑은 고딕',11)
$form.BackColor = [Drawing.Color]::White

function Add-Text($parent,$text,$x,$y,$w,$h) {
    $control = [Windows.Forms.Label]::new()
    $control.Text=$text; $control.SetBounds($x,$y,$w,$h); $parent.Controls.Add($control)
    return $control
}
function Add-Button($parent,$text,$x,$y,$w,$h) {
    $control=[Windows.Forms.Button]::new()
    $control.Text=$text; $control.SetBounds($x,$y,$w,$h); $parent.Controls.Add($control)
    return $control
}
function Show-Error($message) {
    [Windows.Forms.MessageBox]::Show($message,'확인이 필요합니다','OK','Warning') | Out-Null
}
function Select-Folder($initial) {
    $picker=[Windows.Forms.FolderBrowserDialog]::new()
    $picker.Description='프로젝트 폴더를 선택하세요.'
    $picker.UseDescriptionForTitle=$true
    $picker.SelectedPath=$initial
    try { if ($picker.ShowDialog($form) -eq 'OK') { return $picker.SelectedPath } } finally { $picker.Dispose() }
}
function Open-Project($path) {
    $target=Get-ProjectTarget -Path $path
    $herdr=Join-Path $managementRoot '.local/bin/herdr/herdr.exe'
    if (-not (Test-Path -LiteralPath $herdr -PathType Leaf)) { throw 'herdr 설치 파일을 찾을 수 없습니다.' }
    if ($env:HERDR_ENV -eq '1') { throw '이 창은 Windows에서 여세요. herdr 안에 중첩 실행하지 않습니다.' }
    # Launch/attach only. Never send commands into an existing pane from this external UI.
    Start-Process -FilePath $herdr -ArgumentList @('--session',$target.Session) -WorkingDirectory $target.Path -WindowStyle Normal | Out-Null
    $status.Text="열기 요청: $($target.Name)`n$($target.Path)`nAI 자동 시작·대화 복원은 아직 연결 전입니다. 기존 프로젝트 파일은 변경하지 않았습니다."
}

$heading=Add-Text $form '어떤 작업을 시작할까요?' 28 22 630 42
$heading.Font=[Drawing.Font]::new('맑은 고딕',19,[Drawing.FontStyle]::Bold)
Add-Text $form '새 프로젝트는 별도 폴더에서 시작하고, 기존 프로젝트는 원본을 그대로 엽니다.' 30 72 640 55 | Out-Null
$new=Add-Button $form '새 프로젝트 만들기' 30 138 310 62
$existing=Add-Button $form '기존 프로젝트 열기' 360 138 310 62
Add-Text $form '목적과 이름을 입력하고 기본 문서를 생성합니다.' 30 212 310 54 | Out-Null
Add-Text $form '폴더를 선택합니다. 기존 규칙을 덮어쓰지 않습니다.' 360 212 310 54 | Out-Null
$maintenance=Add-Button $form '관리 환경 열기' 30 290 310 48
$connect=Add-Button $form '관리 AI 연결·재개 요청' 360 290 310 48
Add-Text $form '공통 작업 방식·도구를 개선할 때 관리 프로젝트를 엽니다.' 30 350 640 30 | Out-Null
$status=Add-Text $form '관리 AI 연결 요청은 herdr 내부 실행기가 처리합니다. Desktop은 기존 창에 명령을 보내지 않습니다. 신규 프로젝트의 AI 연결은 아직 적용 전입니다.' 30 400 640 112
$status.ForeColor=[Drawing.Color]::FromArgb(80,80,80)

$existing.Add_Click({ try { $path=Select-Folder (Split-Path $managementRoot -Parent); if ($path) { Open-Project $path } } catch { Show-Error $_.Exception.Message } })
$maintenance.Add_Click({ try { Open-Project $managementRoot } catch { Show-Error $_.Exception.Message } })
$connect.Add_Click({
    try {
        $request=New-WorkspaceRequest -ProjectPath $managementRoot -Store (Join-Path $managementRoot '.local/workspace-connect')
        $script:connectionRequestId=$request.request_id
        Open-Project $managementRoot
        $status.Text="관리 AI 연결 요청 저장: $($request.status)`nherdr 내부 수신기가 켜져 있으면 자동 처리합니다.`n기본 모드는 기존 창 유지이며, AI가 없으면 자동 시작하지 않습니다."
    } catch { Show-Error $_.Exception.Message }
})
$script:connectionRequestId=$null
$connectionTimer=[Windows.Forms.Timer]::new()
$connectionTimer.Interval=2000
$connectionTimer.Add_Tick({
    if(-not $script:connectionRequestId){return}
    try {
        $store=Join-Path $managementRoot '.local/workspace-connect'
        $request=Get-WorkspaceRequest -ProjectPath $managementRoot -Store $store
        if($request.request_id -ne $script:connectionRequestId){return}
        $listenerText='수신기 응답 없음 — herdr 내부에서 수신기를 한 번 시작해야 합니다.'
        if(Test-Path -LiteralPath (Join-Path $store 'listener.json')){
            $listener=Get-Content (Join-Path $store 'listener.json') -Raw | ConvertFrom-Json
            $age=([DateTimeOffset]::Now-[DateTimeOffset]::Parse($listener.updated_at)).TotalSeconds
            if($age -ge 0 -and $age -lt 90 -and $listener.state -in @('waiting','processing')){
                $listenerText=if($listener.mode -eq 'reuse-only'){'수신기 최근 응답 있음 · 기존 창 유지 모드'}else{'수신기 최근 응답 있음 · 없는 역할 시작 허용 모드'}
            }
        }
        $requestText=switch($request.status){
            'pending' {if($request.ContainsKey('delivery')){'전달 이력 있음 — 자동 재전송하지 않습니다.'}else{'요청 대기'}}
            'processing' {'처리 중'}
            'processed' {'요청 처리 완료 · 대화 복원 성공을 의미하지 않습니다.'}
            'uncertain' {'결과 확인 필요 — 자동 재시도하지 않습니다.'}
            'blocked' {'연결 조건 미충족 — 기존 창은 유지합니다.'}
            default {'알 수 없는 요청 상태'}
        }
        $status.Text="$requestText`n$listenerText`n대화 ID 검증과 복원 결과는 별도 확인 대상입니다."
    } catch {$status.Text='연결 상태 파일을 읽지 못했습니다. 요청을 다시 전송하지 않았습니다.'}
})
$connectionTimer.Start()
$new.Add_Click({
    $dialog=[Windows.Forms.Form]::new()
    $dialog.Text='새 프로젝트 만들기'; $dialog.ClientSize=[Drawing.Size]::new(660,520)
    $dialog.Font=$form.Font; $dialog.StartPosition='CenterParent'; $dialog.FormBorderStyle='FixedDialog'; $dialog.MaximizeBox=$false
    Add-Text $dialog '프로젝트 이름' 24 20 600 26 | Out-Null
    $name=[Windows.Forms.TextBox]::new(); $name.SetBounds(24,52,610,32); $dialog.Controls.Add($name)
    Add-Text $dialog '어떤 결과를 만들고 싶나요?' 24 100 600 26 | Out-Null
    $purpose=[Windows.Forms.TextBox]::new(); $purpose.Multiline=$true; $purpose.SetBounds(24,132,610,100); $dialog.Controls.Add($purpose)
    Add-Text $dialog '저장할 상위 폴더 (프로젝트 이름의 새 폴더가 만들어집니다)' 24 248 610 28 | Out-Null
    $parent=[Windows.Forms.TextBox]::new(); $parent.ReadOnly=$true; $parent.SetBounds(24,284,500,32); $parent.Text=Split-Path $managementRoot -Parent; $dialog.Controls.Add($parent)
    $browse=Add-Button $dialog '선택' 538 282 96 36
    $browse.Add_Click({ $selected=Select-Folder $parent.Text; if ($selected) { $parent.Text=$selected } })
    Add-Text $dialog "생성: README · 작업 규칙 · 요구사항/계획 · 작업기록 · 기본 틀 버전`n기존 프로젝트 자료와 대화는 복사하지 않습니다. AI 호출은 하지 않습니다." 24 340 610 75 | Out-Null
    $create=Add-Button $dialog '이 내용으로 프로젝트 생성' 24 436 430 52
    $cancel=Add-Button $dialog '취소' 474 436 160 52
    $cancel.Add_Click({ $dialog.Close() })
    $create.Add_Click({
        try {
            $result=New-ManagedProject -Parent $parent.Text -Name $name.Text -Purpose $purpose.Text
            $status.Text="프로젝트 생성 완료: $($result.Name)`n$($result.Path)`n요구사항 합의와 AI 작업은 아직 시작하지 않았습니다. '기존 프로젝트 열기'로 열 수 있습니다."
            $dialog.Close()
        } catch { Show-Error $_.Exception.Message }
    })
    try { $dialog.ShowDialog($form) | Out-Null } finally { $dialog.Dispose() }
})
if ($PreviewOnly) {
    $form.Show()
    [Windows.Forms.Application]::DoEvents()
    $bitmap=[Drawing.Bitmap]::new($form.Width,$form.Height)
    $form.DrawToBitmap($bitmap,[Drawing.Rectangle]::new(0,0,$form.Width,$form.Height))
    $preview=Join-Path $managementRoot '.local/project-hub-preview.png'
    $bitmap.Save($preview,[Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose(); $connectionTimer.Dispose(); $form.Dispose(); Write-Output $preview
} else {
    try { [Windows.Forms.Application]::Run($form) } finally { $connectionTimer.Dispose(); $form.Dispose() }
}
