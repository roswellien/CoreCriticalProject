param(
    [Parameter(Mandatory = $true)][string]$Compiler,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$PublishDirectory = '',
    [string]$UpdateTrust = '',
    [string]$InstallerVersion = '1.0.28-preview',
    [string]$PreparationBundle = '',
    [string]$RuntimeDirectory = '',
    [string]$WindowsSignTool = '',
    [string]$SigningDlib = '',
    [string]$SigningMetadata = '',
    [string]$InstallerId = '6B5D7A9E-3D8B-4C2E-99F1-23F7E5A4B101'
)
$ErrorActionPreference = 'Stop'
if ($PreparationBundle -and $RuntimeDirectory) { throw 'Choose source preparation or a precompiled runtime, not both' }
$Compiler = [IO.Path]::GetFullPath($Compiler)
if (!(Test-Path -LiteralPath $Compiler -PathType Leaf)) { throw 'Select an installed Inno Setup ISCC.exe compiler. No compiler is downloaded or installed by this build.' }
if ($InstallerVersion -notmatch '^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$') { throw 'Invalid installer version' }
$id = [Guid]::Parse($InstallerId).ToString().ToUpperInvariant()
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh installer output directory' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
# Keep release validation builds separate from a running development launcher.
$checksOutput = Join-Path $OutputDirectory 'checks-bin/'
if (!$PublishDirectory) {
    $PublishDirectory = Join-Path $OutputDirectory 'publish'
    & dotnet publish (Join-Path $PSScriptRoot 'MW3RemasterLauncher.csproj') -c Release -r win-x64 --self-contained true -o $PublishDirectory -v quiet
    if ($LASTEXITCODE) { throw 'Launcher publish failed' }
    & (Join-Path $PSScriptRoot 'stage_media_tools.ps1') -PublishDirectory $PublishDirectory
}
$PublishDirectory = [IO.Path]::GetFullPath($PublishDirectory)
if ($UpdateTrust) {
    $trustFile = [IO.Path]::GetFullPath($UpdateTrust)
    $trustConfig = Get-Content -LiteralPath $trustFile -Raw | ConvertFrom-Json
    if (!$trustConfig.public_keys -or @($trustConfig.public_keys.PSObject.Properties).Count -eq 0) { throw 'Supply public update trust configuration' }
    foreach ($key in $trustConfig.public_keys.PSObject.Properties) {
        $publicRsa = [Security.Cryptography.RSA]::Create()
        try { $publicRsa.ImportFromPem([string]$key.Value); if ($publicRsa.KeySize -lt 3072) { throw 'Update public key is too small' } }
        finally { $publicRsa.Dispose() }
    }
    Copy-Item -LiteralPath $trustFile -Destination (Join-Path $PublishDirectory 'update-trust.json')
}
if ($RuntimeDirectory -and !(Test-Path -LiteralPath (Join-Path $PublishDirectory 'update-trust.json'))) {
    throw 'Precompiled releases must include update-trust.json. Supply -UpdateTrust or a configured publication.'
}
foreach ($name in @('Core Critical Launcher.exe','hostfxr.dll','SDL3.dll','SDL3-LICENSE.txt','Tools/Unshield/unshield.exe','Tools/Unshield/provenance.json')) {
    if (!(Test-Path -LiteralPath (Join-Path $PublishDirectory $name) -PathType Leaf)) { throw "Incomplete launcher publication: $name" }
}
foreach ($name in @('Runtime','user','native-inputs')) {
    if (Test-Path -LiteralPath (Join-Path $PublishDirectory $name)) { throw "This launcher-only installer must not package private runtime or player inputs: $name" }
}
if ($RuntimeDirectory) {
    $RuntimeDirectory = [IO.Path]::GetFullPath($RuntimeDirectory)
    & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --validate-runtime $RuntimeDirectory
    if ($LASTEXITCODE) { throw 'Precompiled runtime validation failed' }
    $runtimeManifest = Get-Content -LiteralPath (Join-Path $RuntimeDirectory 'runtime.json') -Raw | ConvertFrom-Json
    if ($runtimeManifest.precompiled_runtime_version -ne 1) { throw 'Explicit precompiled runtime marker required' }
    Copy-Item -LiteralPath $RuntimeDirectory -Destination (Join-Path $PublishDirectory 'Runtime') -Recurse
}
if ($PreparationBundle) {
    $PreparationBundle = [IO.Path]::GetFullPath($PreparationBundle)
    & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --verify-bundled-preparation $PreparationBundle
    if ($LASTEXITCODE) { throw 'Bundled source preparation signature/contract verification failed' }
    foreach ($name in @('Preparation/initial.mw3update','Preparation/initial.zip','update-trust.json')) {
        $source = Join-Path $PreparationBundle $name
        if (!(Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing signed source preparation payload: $name" }
        $target = Join-Path $PublishDirectory $name
        if (Test-Path -LiteralPath $target) { throw "Preparation publication target already exists: $name" }
        New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
        Copy-Item -LiteralPath $source -Destination $target
    }
}
if ($WindowsSignTool -or $SigningDlib -or $SigningMetadata) {
    foreach ($signingPath in @($WindowsSignTool,$SigningDlib,$SigningMetadata)) {
        if (!$signingPath -or !(Test-Path -LiteralPath $signingPath -PathType Leaf)) { throw 'Provide all three Windows signing inputs' }
    }
    $peFiles=@(Get-ChildItem -LiteralPath $PublishDirectory -Recurse -File | Where-Object { $_.Extension -in @('.exe','.dll','.pyd') } | Select-Object -ExpandProperty FullName)
    & (Join-Path $PSScriptRoot 'sign_windows.ps1') -File $peFiles -SignTool $WindowsSignTool -Dlib $SigningDlib -Metadata $SigningMetadata -ReceiptPath (Join-Path $OutputDirectory 'application-signatures.json')
}
& dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --verify-media-tools (Join-Path $PublishDirectory 'Tools/Unshield')
if ($LASTEXITCODE) { throw 'Published media extractor failed the actual launcher admission check after signing' }
if ($RuntimeDirectory) {
    # Signing must not leave a runtime whose manifest pins describe different bytes.
    & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --validate-runtime (Join-Path $PublishDirectory 'Runtime')
    if ($LASTEXITCODE) { throw 'Published runtime changed during signing; refresh its pins before packaging' }
}
$arguments = @('/Qp',('/O'+$OutputDirectory),('/DPublishDirectory='+$PublishDirectory),
    ('/DMyAppVersion='+$InstallerVersion),('/DInstallerAppId={{'+$id+'}'),(Join-Path $PSScriptRoot 'installer.iss'))
if ($PreparationBundle) { $arguments = @('/DSourcePreparationIncluded=1') + $arguments }
if ($RuntimeDirectory) { $arguments = @('/DPrecompiledRuntimeIncluded=1') + $arguments }
if ($WindowsSignTool) {
    $signCommand='$q'+[IO.Path]::GetFullPath($WindowsSignTool)+'$q sign /fd SHA256 /tr http://timestamp.acs.microsoft.com /td SHA256 /dlib $q'+[IO.Path]::GetFullPath($SigningDlib)+'$q /dmdf $q'+[IO.Path]::GetFullPath($SigningMetadata)+'$q $f'
    $arguments=@('/DWindowsSigning=1',('/Sartifact-signing='+$signCommand))+$arguments
}
& $Compiler @arguments
if ($LASTEXITCODE) { throw 'Inno Setup compilation failed' }
$setupFilename = "corecriticalinstaller-$InstallerVersion.exe"
$setup = Join-Path $OutputDirectory $setupFilename
if (!(Test-Path -LiteralPath $setup -PathType Leaf)) { throw 'Compiler did not produce the expected installer' }
if ($WindowsSignTool) {
    & $WindowsSignTool verify /pa /all /v $setup
    if ($LASTEXITCODE -or (Get-AuthenticodeSignature -LiteralPath $setup).Status -ne 'Valid') { throw 'Final installer signature verification failed' }
}
@{
    kind = $(if ($RuntimeDirectory) {'private-precompiled-playtest-preview'} elseif ($PreparationBundle) {'private-source-preparation-playtest-preview'} else {'local-launcher-preview-not-playable-release'})
    version = $InstallerVersion
    setup_filename = $setupFilename
    compiler_sha256 = (Get-FileHash -LiteralPath $Compiler).Hash.ToLowerInvariant()
    setup_sha256 = (Get-FileHash -LiteralPath $setup).Hash.ToLowerInvariant()
    setup_bytes = (Get-Item -LiteralPath $setup).Length
    native_runtime_generation_complete = [bool]$RuntimeDirectory
    precompiled_runtime_included = [bool]$RuntimeDirectory
    source_preparation_included = [bool]$PreparationBundle
    windows_signed = [bool]$WindowsSignTool
    clean_windows_verified = $false
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'installer-build.json')
Write-Output "Launcher preview installer: $setup"
