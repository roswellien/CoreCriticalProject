param(
    [Parameter(Mandatory=$true)][string]$Installer,
    [Parameter(Mandatory=$true)][string]$InstallerReceipt,
    [Parameter(Mandatory=$true)][string]$Version,
    [Parameter(Mandatory=$true)][long]$Sequence,
    [Parameter(Mandatory=$true)][string]$SigningKey,
    [Parameter(Mandatory=$true)][string]$KeyId,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
# Build and sign an update installer first, then pin its exact bytes in the signed envelope.
$ErrorActionPreference='Stop'
$Installer=[IO.Path]::GetFullPath($Installer)
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
$parsedVersion=[version]::Parse($Version)
if ($parsedVersion.Build -lt 0 -or $Sequence -lt 1) { throw 'Supply a release version and positive sequence' }
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh output directory' }
$receipt=Get-Content -LiteralPath $InstallerReceipt -Raw | ConvertFrom-Json
$installerHash=(Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
$launcherOnly = $receipt.native_preview_included -eq $false -and $receipt.native_preview_upgrade_only -ne $true
$runtimeUpgrade = $receipt.native_preview_included -eq $true -and
    $receipt.native_preview_upgrade_only -eq $true -and $receipt.kind -eq 'mw3-re-in-place-update' -and
    $receipt.native_preview_source_commit -match '^[0-9a-f]{40}$'
if ($receipt.source_preparation_included -ne $false -or !($launcherOnly -or $runtimeUpgrade) -or
    $receipt.windows_signed -ne $true -or $receipt.setup_sha256 -ne $installerHash -or
    [version]::Parse(($receipt.version -split '-')[0]) -ne $parsedVersion) { throw 'A matching signed launcher-only or in-place MW3-RE installer receipt is required' }
$signature=Get-AuthenticodeSignature -LiteralPath $Installer
if ($signature.Status -ne 'Valid' -or !$signature.TimeStamperCertificate) { throw 'The launcher installer needs a valid timestamped Windows signature' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$base=$Version
$archive=Join-Path $OutputDirectory ($base+'.zip')
$zip=[IO.Compression.ZipFile]::Open($archive,[IO.Compression.ZipArchiveMode]::Create)
try { $null=[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$Installer,'CoreCriticalSetup.exe',[IO.Compression.CompressionLevel]::Optimal) }
finally { $zip.Dispose() }
$manifest=@{
    schema_version=1;product_id='corecritical';update_type='launcher-inno-v1';version=$Version;sequence=$Sequence
    # Earlier helpers restart the retired executable name. The name migration
    # needs one full installer upgrade; subsequent updates use the new helper.
    minimum_launcher_version='1.0.27';package_bytes=(Get-Item -LiteralPath $archive).Length
    package_sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    installer=@{bytes=(Get-Item -LiteralPath $Installer).Length;sha256=$installerHash}
}
$manifestFile=Join-Path $OutputDirectory ($base+'.manifest.json')
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestFile -Encoding utf8NoBOM
& (Join-Path $PSScriptRoot 'sign_runtime_update.ps1') -Manifest $manifestFile -SigningKey $SigningKey -KeyId $KeyId -OutputFile (Join-Path $OutputDirectory ($base+'.ccupdate'))
if ($LASTEXITCODE) { throw 'Core Critical update signing failed' }
Write-Output "Deliver $base.ccupdate and $base.zip together. Keep the private key outside all packages."
