#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$checker = Join-Path $PSScriptRoot 'check_project_docs.ps1'
$fixtureRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('codex-guide-test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $fixtureRoot
$utf8 = [System.Text.UTF8Encoding]::new($false)
$cases = 0

function Write-Fixture {
    param($Name, $Text)
    [System.IO.File]::WriteAllText((Join-Path $fixtureRoot $Name), $Text, $utf8)
}

function Assert-Check {
    param([string[]]$Names, [int]$Code, [string[]]$Kinds = @())
    $result = (& $checker -ProjectRoot $fixtureRoot -Files $Names) | ConvertFrom-Json
    $actualCode = $LASTEXITCODE
    $actualKinds = @($result.findings | ForEach-Object { $_.kind } | Sort-Object)
    if ($actualCode -ne $Code -or ($actualKinds -join ',') -ne (($Kinds | Sort-Object) -join ',')) {
        throw "Unexpected result for $($Names -join ','): code=$actualCode, kinds=$($actualKinds -join ',')"
    }
    $script:cases++
    return $result
}

try {
    Write-Fixture '한 글&자료.md' '# Source'
    Write-Fixture 'other.html' '<p id="target">Other</p><a href="not-recursed.md">Not checked recursively</a>'
    Write-Fixture 'good.html' @'
<!doctype html>
<!-- <a href="missing-comment.md"></a><p id="duplicate"></p> -->
<A title="a > b" HREF='한%20글&amp;자료.md'>Source</A>
<a
 href="#%EA%B0%9C%EB%85%90%26A">Encoded anchor</a>
<section ID="개념&amp;A">Target</section>
<a href=other.html#unverified>File only</a>
<a href="https://example.invalid">External</a>
<a href="/Library/not-local">Absolute</a>
<a href="%2Fnot-local">Encoded absolute</a>
<a href="#">Top</a><a href="">Empty</a><a href="?view=1">Query</a>
<pre id="example"><code><a href="missing-code.md"></a></code></pre>
<script>const example = '<a href="missing-script.md">';</script>
<style>.a::after { content: '<a href="missing-style.md">'; }</style>
'@
    Write-Fixture 'good.md' @'
[Source](<한 글&자료.md>)
[Encoded](%ED%95%9C%20%EA%B8%80%26%EC%9E%90%EB%A3%8C.md#heading)
[Heading](#not-checked)
`[Example](missing-inline.md)`
````text
[Example](missing-fence.md)
```
[Still example](missing-fence-too.md)
````
'@
    Write-Fixture 'broken.html' @'
<div id="same"></div>
<a href="missing.md">Missing file</a>
<a href="#absent">Missing anchor</a>
<div id="same"></div>
'@
    Write-Fixture 'case.html' '<div id="Case"></div><a href="#case">Case-sensitive</a>'
    Write-Fixture 'base.html' '<base href="https://example.invalid/"><a href="missing.md">Skip base</a><a href="#x">Skip base</a>'
    Write-Fixture 'empty.html' '<a href="#missing">No IDs</a>'
    Write-Fixture 'skipped.txt' 'Not a supported document'
    [System.IO.File]::WriteAllBytes((Join-Path $fixtureRoot 'invalid.html'), [byte[]]@(0xc3, 0x28))
    $before = @(Get-ChildItem -LiteralPath $fixtureRoot -File | Sort-Object Name | Get-FileHash | Select-Object -ExpandProperty Hash) -join ','
    $beforeCount = @(Get-ChildItem -LiteralPath $fixtureRoot -File).Count

    $good = Assert-Check @('good.html') 0
    if ($good.relative_links_checked -ne 2 -or $good.html_anchors_checked -ne 1 -or $good.html_ids_checked -ne 2) { throw 'HTML counters or example exclusion failed' }
    if (@($good.skipped_checks | Where-Object reason -eq 'cross_file_fragment').Count -ne 1) { throw 'Cross-file fragment not disclosed' }
    $markdown = Assert-Check @('good.md') 0
    if ($markdown.relative_links_checked -ne 2 -or $markdown.links_skipped -ne 1) { throw 'Markdown regression failed' }
    $mixed = Assert-Check @('good.html', 'good.md') 0
    if ($mixed.checked_files.Count -ne 2 -or $mixed.relative_links_checked -ne 4) { throw 'Mixed input failed' }
    $broken = Assert-Check @('broken.html') 1 @('broken_relative_link', 'missing_html_id', 'duplicate_html_id')
    if (@($broken.findings | Where-Object { -not $_.line -or -not $_.target }).Count) { throw 'Missing finding location/target' }
    if (($broken.findings | Where-Object kind -eq 'duplicate_html_id').first_line -ne 1) { throw 'Duplicate ID first location missing' }
    $null = Assert-Check @('case.html') 1 @('missing_html_id')
    $null = Assert-Check @('empty.html') 1 @('missing_html_id')
    $base = Assert-Check @('base.html') 0
    if ($base.relative_links_checked -ne 0 -or @($base.skipped_checks | Where-Object reason -eq 'html_base_href').Count -ne 2) { throw 'Base href should be explicitly skipped' }
    $null = Assert-Check @('missing.html') 1 @('missing_file')
    $null = Assert-Check @('invalid.html') 1 @('unreadable_file')
    $null = Assert-Check @('skipped.txt') 1 @('unsupported_file_type')
    $badRoot = (& $checker -ProjectRoot (Join-Path $fixtureRoot 'absent') -Files @('good.html')) | ConvertFrom-Json
    if ($LASTEXITCODE -ne 2 -or $badRoot.status -ne 'CHECK_ERROR') { throw 'Invalid root exit code failed' }
    $cases++
    $after = @(Get-ChildItem -LiteralPath $fixtureRoot -File | Sort-Object Name | Get-FileHash | Select-Object -ExpandProperty Hash) -join ','
    if ($before -ne $after -or $beforeCount -ne @(Get-ChildItem -LiteralPath $fixtureRoot -File).Count) { throw 'Read-only invariant failed' }
    $cases++
    "PASS: $cases cases; fixture bytes and file count unchanged."
} finally {
    $resolvedFixture = [System.IO.Path]::GetFullPath($fixtureRoot)
    $tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolvedFixture.StartsWith($tempBase, [System.StringComparison]::OrdinalIgnoreCase) -and (Split-Path -Leaf $resolvedFixture) -match '^codex-guide-test-[a-f0-9]{32}$') {
        Remove-Item -LiteralPath $resolvedFixture -Recurse -Force
    }
}
