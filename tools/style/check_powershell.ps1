<#
.SYNOPSIS
Formats and lints PowerShell files for tools/style/check_style.py.

.DESCRIPTION
PSScriptAnalyzer only runs inside PowerShell, so check_style.py calls this script and
reads what it prints. File paths arrive on standard input, one per line, so a long file
list never hits the command-line length limit.

Modes:
  Install      install the pinned PSScriptAnalyzer for the current user
  FormatCheck  print each file whose layout would change
  FormatFix    rewrite each file with the formatted layout (UTF-8 without BOM)
  Lint         print one line per default-rule finding: path:line RuleName message

Exit codes: 0 nothing found, 1 findings, 2 this script could not do its job.
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet('Install', 'FormatCheck', 'FormatFix', 'Lint')]
    [string] $Mode,

    [string] $SettingsPath = (Join-Path $PSScriptRoot 'PSScriptAnalyzerSettings.psd1')
)

$ErrorActionPreference = 'Stop'

# The only place the PSScriptAnalyzer version is pinned. Bump it together with
# docs/dependencies.md, choosing a release at least one month old.
$AnalyzerVersion = '1.25.0'

function Install-PinnedAnalyzer {
    Install-Module -Name PSScriptAnalyzer -RequiredVersion $AnalyzerVersion `
        -Repository PSGallery -Scope CurrentUser -Force
}

function Import-PinnedAnalyzer {
    $pinnedModule = Get-Module -ListAvailable -Name PSScriptAnalyzer |
        Where-Object { $_.Version -eq [version] $AnalyzerVersion }
    if (-not $pinnedModule) {
        $hint = 'Run: pwsh -File tools/style/check_powershell.ps1 -Mode Install'
        [Console]::Error.WriteLine("PSScriptAnalyzer $AnalyzerVersion is not installed. $hint")
        exit 2
    }
    Import-Module -Name PSScriptAnalyzer -RequiredVersion $AnalyzerVersion
}

function Read-PathList {
    $allInput = [Console]::In.ReadToEnd()
    return $allInput -split "`r?`n" | Where-Object { $_ -ne '' }
}

function Get-FormattedText([string] $Path) {
    $currentText = [System.IO.File]::ReadAllText($Path)
    if ($currentText.Trim() -eq '') {
        # Invoke-Formatter rejects empty input, and there is nothing to lay out.
        return $currentText
    }
    return Invoke-Formatter -ScriptDefinition $currentText -Settings $SettingsPath
}

function Find-LayoutChanges([string[]] $Paths, [bool] $WriteChanges) {
    $changedPaths = @()
    foreach ($path in $Paths) {
        $currentText = [System.IO.File]::ReadAllText($path)
        $formattedText = Get-FormattedText $path
        if ($formattedText -ceq $currentText) {
            continue
        }
        $changedPaths += $path
        if ($WriteChanges) {
            $utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
            [System.IO.File]::WriteAllText($path, $formattedText, $utf8WithoutBom)
        }
    }
    return $changedPaths
}

function Find-LintFindings([string[]] $Paths) {
    $findingLines = @()
    foreach ($path in $Paths) {
        foreach ($finding in Invoke-ScriptAnalyzer -Path $path) {
            $oneLineMessage = $finding.Message -replace '\s+', ' '
            $findingLines += "${path}:$($finding.Line) $($finding.RuleName) $oneLineMessage"
        }
    }
    return $findingLines
}

try {
    if ($Mode -eq 'Install') {
        Install-PinnedAnalyzer
        exit 0
    }

    Import-PinnedAnalyzer
    $paths = @(Read-PathList)
    $reportLines = switch ($Mode) {
        'FormatCheck' { Find-LayoutChanges $paths $false }
        'FormatFix' { Find-LayoutChanges $paths $true }
        'Lint' { Find-LintFindings $paths }
    }

    $reportLines | ForEach-Object { Write-Output $_ }
    # FormatFix has done its job once the files are rewritten, so only checks report findings.
    $foundSomething = @($reportLines).Count -gt 0 -and $Mode -ne 'FormatFix'
    exit ($foundSomething ? 1 : 0)
}
catch {
    [Console]::Error.WriteLine("check_powershell.ps1 failed: $_")
    exit 2
}
