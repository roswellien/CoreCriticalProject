param(
    [Parameter(Mandatory=$true)][string]$Compiler,
    [Parameter(Mandatory=$true)][string]$PublishDirectory,
    [Parameter(Mandatory=$true)][string]$RuntimeDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][string]$Version,
    [Parameter(Mandatory=$true)][long]$Sequence,
    [Parameter(Mandatory=$true)][string]$SigningKey,
    [Parameter(Mandatory=$true)][string]$KeyId,
    [Parameter(Mandatory=$true)][string]$WindowsSignTool,
    [Parameter(Mandatory=$true)][string]$SigningDlib,
    [Parameter(Mandatory=$true)][string]$SigningMetadata
)
# One release produces a full installer plus the separate launcher-only update.
$ErrorActionPreference = 'Stop'
$PublishDirectory = [IO.Path]::GetFullPath($PublishDirectory)
$RuntimeDirectory = [IO.Path]::GetFullPath($RuntimeDirectory)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$SigningKey = [IO.Path]::GetFullPath($SigningKey)
$numericVersion = ($Version -split '-')[0]
if ([version]::Parse($numericVersion).Build -lt 0 -or $Sequence -lt 1) { throw 'Supply a release version and positive launcher sequence' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh release output directory' }
foreach ($root in @($PublishDirectory, $RuntimeDirectory, $OutputDirectory)) {
    if ($SigningKey.StartsWith($root.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The update private key must stay outside all publication inputs and outputs'
    }
}
if (Test-Path -LiteralPath (Join-Path $PublishDirectory 'Runtime')) {
    throw 'Use a fresh launcher publication without Runtime; the full installer stages it after the launcher-only update is built'
}
# Reject a mismatched update key before signing/building either installer.
$trust = Get-Content -LiteralPath (Join-Path $PublishDirectory 'update-trust.json') -Raw | ConvertFrom-Json
$publicKey = $trust.public_keys.PSObject.Properties[$KeyId]
if (!$publicKey) { throw 'The release update key is not trusted by this launcher publication' }
$privateRsa = [Security.Cryptography.RSA]::Create()
$publicRsa = [Security.Cryptography.RSA]::Create()
try {
    $privateRsa.ImportFromPem([IO.File]::ReadAllText($SigningKey))
    $publicRsa.ImportFromPem([string]$publicKey.Value)
    if ($privateRsa.KeySize -lt 3072 -or
        [Convert]::ToBase64String($privateRsa.ExportSubjectPublicKeyInfo()) -ne [Convert]::ToBase64String($publicRsa.ExportSubjectPublicKeyInfo())) {
        throw 'The update signing key does not match the published launcher trust'
    }
} finally { $privateRsa.Dispose(); $publicRsa.Dispose() }

New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$common = @{
    Compiler=$Compiler; PublishDirectory=$PublishDirectory; InstallerVersion=$Version
    WindowsSignTool=$WindowsSignTool; SigningDlib=$SigningDlib; SigningMetadata=$SigningMetadata
}
$launcherSetup = Join-Path $OutputDirectory 'LauncherSetup'
$setupFilename = "corecriticalinstaller-$Version.exe"
& (Join-Path $PSScriptRoot 'build_installer.ps1') @common -OutputDirectory $launcherSetup
$updateDirectory = Join-Path $OutputDirectory 'LauncherUpdate'
& (Join-Path $PSScriptRoot 'build_ccupdate.ps1') -Installer (Join-Path $launcherSetup $setupFilename) `
    -InstallerReceipt (Join-Path $launcherSetup 'installer-build.json') -Version $numericVersion -Sequence $Sequence `
    -SigningKey $SigningKey -KeyId $KeyId -OutputDirectory $updateDirectory
$fullSetup = Join-Path $OutputDirectory 'Setup'
& (Join-Path $PSScriptRoot 'build_installer.ps1') @common -OutputDirectory $fullSetup -RuntimeDirectory $RuntimeDirectory

$artifacts = @{}
foreach ($relative in @("Setup/$setupFilename", "LauncherUpdate/corecritical-$numericVersion.ccupdate", "LauncherUpdate/corecritical-$numericVersion.zip")) {
    $path = Join-Path $OutputDirectory $relative
    $artifacts[$relative] = @{ bytes=(Get-Item -LiteralPath $path).Length; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
}
@{ version=$Version; launcher_sequence=$Sequence; artifacts=$artifacts; published=$false } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'launcher-release.json') -Encoding utf8NoBOM
Write-Output "Release built: Setup/$setupFilename and the matching LauncherUpdate .ccupdate + ZIP. Validate the upgrade before publication."
