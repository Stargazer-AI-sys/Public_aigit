#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string[]]$Files = @(
        'README.md',
        'AGENTS.md',
        'docs/01_requirements/신규_개발_프로젝트_요구사항_작성양식.md',
        'docs/02_design/management_workflow.md'
    )
)

# Read-only checks for inline Markdown links and static HTML guides.
$ErrorActionPreference = 'Stop'
$findings = [System.Collections.Generic.List[object]]::new()
$checked = [System.Collections.Generic.List[string]]::new()
$checkedLinks = 0
$skippedLinks = 0
$checkedAnchors = 0
$checkedIds = 0
$skippedChecks = [System.Collections.Generic.List[object]]::new()
$utf8 = [System.Text.UTF8Encoding]::new($false, $true)

function Add-SkippedCheck {
    param($File, $Line, $Target, $Reason, [switch]$Partial)
    if (-not $Partial) { $script:skippedLinks++ }
    $script:skippedChecks.Add([pscustomobject]@{
        file = $File; line = $Line; target = $Target; reason = $Reason
    })
}

function Test-DocumentLink {
    param([string]$Target, $File, $SourcePath, $Line, [switch]$Html, $Ids)
    $targetValue = $Target.Trim()
    if (-not $targetValue) {
        Add-SkippedCheck $File $Line $Target 'empty_target'
        return
    }
    if ($targetValue.StartsWith('#')) {
        if (-not $Html) {
            Add-SkippedCheck $File $Line $Target 'markdown_heading'
        } elseif ($targetValue -eq '#') {
            Add-SkippedCheck $File $Line $Target 'document_top'
        } else {
            $anchor = [uri]::UnescapeDataString($targetValue.Substring(1))
            $script:checkedAnchors++
            if (-not $Ids.ContainsKey($anchor)) {
                $script:findings.Add([pscustomobject]@{
                    kind = 'missing_html_id'; file = $File; line = $Line; target = $Target
                })
            }
        }
        return
    }
    if ($targetValue -match '^[a-zA-Z][a-zA-Z0-9+.-]*:' -or $targetValue -match '^[\\/]') {
        Add-SkippedCheck $File $Line $Target 'external_or_absolute'
        return
    }
    $relative = [uri]::UnescapeDataString(($targetValue -split '[#?]', 2)[0])
    if (-not $relative) {
        Add-SkippedCheck $File $Line $Target 'same_document_query'
        return
    }
    if ([System.IO.Path]::IsPathRooted($relative) -or $relative -match '^[a-zA-Z][a-zA-Z0-9+.-]*:') {
        Add-SkippedCheck $File $Line $Target 'external_or_absolute'
        return
    }
    $script:checkedLinks++
    try {
        $linkPath = Join-Path (Split-Path -Parent $SourcePath) $relative
        $exists = Test-Path -LiteralPath $linkPath -ErrorAction Stop
    } catch { $exists = $false }
    if (-not $exists) {
        $script:findings.Add([pscustomobject]@{
            kind = 'broken_relative_link'; file = $File; line = $Line; target = $Target
        })
    }
    if ($targetValue.Contains('#')) {
        Add-SkippedCheck $File $Line $Target 'cross_file_fragment' -Partial
    }
}

function Test-HtmlGuide {
    param([string]$Content, $File, $SourcePath)
    # Tokenize tags without treating quoted '>' characters as tag endings.
    # Ignore comments and the bodies of code examples and raw-text elements.
    $tagPattern = '(?s)<!--.*?(?:-->|$)|<![^>]*>|<\s*(?<closing>/)?\s*(?<tag>[a-zA-Z][\w:-]*)\b(?<attrs>(?:"[^"]*"|''[^'']*''|[^''">])*)>'
    $attributePattern = '(?<name>[^\s=/>]+)(?:\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+)))?'
    $ids = [System.Collections.Generic.Dictionary[string,int]]::new([System.StringComparer]::Ordinal)
    $links = [System.Collections.Generic.List[object]]::new()
    $hasBase = $false
    $offset = 0
    while ($offset -lt $Content.Length) {
        $token = [regex]::Match($Content.Substring($offset), $tagPattern)
        if (-not $token.Success) { break }
        $start = $offset + $token.Index
        $offset = $start + $token.Length
        if (-not $token.Groups['tag'].Success -or $token.Groups['closing'].Success) { continue }
        $line = 1 + [regex]::Matches($Content.Substring(0, $start), '\n').Count
        $tag = $token.Groups['tag'].Value.ToLowerInvariant()
        $attributes = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($attribute in [regex]::Matches($token.Groups['attrs'].Value, $attributePattern)) {
            $name = $attribute.Groups['name'].Value
            $value = ''
            foreach ($group in @('double', 'single', 'bare')) {
                if ($attribute.Groups[$group].Success) { $value = $attribute.Groups[$group].Value; break }
            }
            if (-not $attributes.ContainsKey($name)) { $attributes.Add($name, [System.Net.WebUtility]::HtmlDecode($value)) }
        }
        if ($attributes.ContainsKey('id')) {
            $id = $attributes['id']
            $script:checkedIds++
            if ($ids.ContainsKey($id)) {
                $script:findings.Add([pscustomobject]@{
                    kind = 'duplicate_html_id'; file = $File; line = $line; target = $id; first_line = $ids[$id]
                })
            } else { $ids.Add($id, $line) }
        }
        if ($tag -eq 'base' -and $attributes.ContainsKey('href')) { $hasBase = $true }
        if ($tag -in @('a', 'area', 'link') -and $attributes.ContainsKey('href')) {
            $links.Add([pscustomobject]@{ target = $attributes['href']; line = $line })
        }
        if ($tag -in @('script', 'style', 'pre', 'code', 'textarea', 'title')) {
            $closing = [regex]::Match($Content.Substring($offset), ('(?is)</\s*' + $tag + '\s*>'))
            $offset = if ($closing.Success) { $offset + $closing.Index + $closing.Length } else { $Content.Length }
        }
    }
    foreach ($link in $links) {
        if ($hasBase -and $link.target -notmatch '^[a-zA-Z][a-zA-Z0-9+.-]*:' -and $link.target -notmatch '^[\\/]') {
            Add-SkippedCheck $File $link.line $link.target 'html_base_href'
            continue
        }
        Test-DocumentLink $link.target $File $SourcePath $link.line -Html -Ids $ids
    }
}

try {
    $resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
    if (-not (Test-Path -LiteralPath $resolvedRoot -PathType Container) -or $Files.Count -eq 0) {
        throw 'Specify an existing project directory and at least one file.'
    }
    foreach ($file in $Files) {
        $path = if ([System.IO.Path]::IsPathRooted($file)) { $file } else { Join-Path $resolvedRoot $file }
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            $findings.Add([pscustomobject]@{ kind = 'missing_file'; file = $file; target = $null })
            continue
        }
        $extension = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
        if ($extension -notin @('.md', '.markdown', '.html', '.htm')) {
            $findings.Add([pscustomobject]@{ kind = 'unsupported_file_type'; file = $file; target = $extension })
            continue
        }
        try {
            $content = [System.IO.File]::ReadAllText($path, $utf8)
        } catch {
            $findings.Add([pscustomobject]@{ kind = 'unreadable_file'; file = $file; target = $null })
            continue
        }
        $checked.Add($file)
        if ($extension -in @('.html', '.htm')) {
            Test-HtmlGuide $content $file $path
            continue
        }
        $insideFence = $false
        $fenceChar = ''
        $fenceLength = 0
        $lineNumber = 0
        foreach ($line in ($content -split '\r?\n')) {
            $lineNumber++
            if ($line -match '^\s*(`{3,}|~{3,})(.*)$') {
                $marker = $Matches[1]
                $suffix = $Matches[2]
                if (-not $insideFence) {
                    $insideFence = $true
                    $fenceChar = $marker.Substring(0, 1)
                    $fenceLength = $marker.Length
                } elseif ($marker.StartsWith($fenceChar) -and $marker.Length -ge $fenceLength -and -not $suffix.Trim()) {
                    $insideFence = $false
                }
                continue
            }
            if ($insideFence) { continue }
            $prose = [regex]::Replace($line, '(`+).*?\1', '')
            foreach ($match in [regex]::Matches($prose, '\[[^\]\r\n]*\]\((?<target><[^>\r\n]+>|[^\s()]+)\)')) {
                $target = $match.Groups['target'].Value.Trim('<', '>')
                Test-DocumentLink $target $file $path $lineNumber
            }
        }
    }
    [pscustomobject]@{
        status = $(if ($findings.Count) { 'ISSUES_FOUND' } else { 'CHECKED_ITEMS_OK' })
        project_root = $resolvedRoot
        requested_files = @($Files)
        checked_files = $checked.ToArray()
        relative_links_checked = $checkedLinks
        html_anchors_checked = $checkedAnchors
        html_ids_checked = $checkedIds
        links_skipped = $skippedLinks
        skipped_checks = $skippedChecks.ToArray()
        findings = $findings.ToArray()
        scope = 'UTF-8, relative Markdown/HTML link paths, same-HTML ID anchors and duplicate IDs; no recursive scan.'
        not_checked = @('External URLs', 'Absolute paths', 'Markdown heading anchors', 'Cross-file fragments',
            'Reference-style Markdown links', 'Complex or malformed markup', 'Dynamic HTML or script-generated links',
            'HTML base href resolution', 'Image/media sources', 'Content accuracy or freshness', 'Implementation or runtime behavior',
            'GitHub synchronization', 'Skill discovery', 'API budget')
    } | ConvertTo-Json -Depth 6
    if ($findings.Count) { exit 1 }
    exit 0
} catch {
    [pscustomobject]@{ status = 'CHECK_ERROR'; message = $_.Exception.Message } | ConvertTo-Json
    exit 2
}
