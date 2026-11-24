param(
    [string]$Compiler = '',
    [string]$OutputDirectory = '',
    [string]$PublishDirectory = '',
    [string]$UpdateTrust = '',
    [string]$InstallerVersion = '1.0.28-preview',
    [string]$PreparationBundle = '',
    # MW3-RE Native preview runtime staged by tools/remaster-launcher/stage_mw3_re_runtime.py.
    [string]$NativePreviewDirectory = '',
    [switch]$NativePreviewUpgradeOnly,
    [string]$PlannerPythonArchive = '',
    [string]$WindowsSignTool = '',
    [string]$SigningDlib = '',
    [string]$SigningMetadata = '',
    [string]$InstallerId = '6B5D7A9E-3D8B-4C2E-99F1-23F7E5A4B101'
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'sign_native_preview.ps1')

if ($MyInvocation.InvocationName -ne '.') {
    if ([string]::IsNullOrWhiteSpace($Compiler) -or [string]::IsNullOrWhiteSpace($OutputDirectory)) {
        throw 'Specify -Compiler and -OutputDirectory'
    }
    $Compiler = [IO.Path]::GetFullPath($Compiler)
    if ($PreparationBundle -and $NativePreviewDirectory) { throw 'Choose source preparation or the MW3-RE runtime, not both' }
    if ($NativePreviewUpgradeOnly -and !$NativePreviewDirectory) { throw 'An in-place MW3-RE update requires a staged runtime' }
    if (!(Test-Path -LiteralPath $Compiler -PathType Leaf)) { throw 'Select an installed Inno Setup ISCC.exe compiler. No compiler is downloaded or installed by this build.' }
    if ($InstallerVersion -notmatch '^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$') { throw 'Invalid installer version' }
    $id = [Guid]::Parse($InstallerId).ToString().ToUpperInvariant()
    $OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $OutputDirectory) { throw 'Use a fresh installer output directory' }
    if ($WindowsSignTool -or $SigningDlib -or $SigningMetadata) {
        foreach ($signingPath in @($WindowsSignTool, $SigningDlib, $SigningMetadata)) {
            if (!$signingPath -or !(Test-Path -LiteralPath $signingPath -PathType Leaf)) { throw 'Provide all three Windows signing inputs' }
        }
    }
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
    # Keep release validation builds separate from a running development launcher.
    $checksOutput = (Join-Path $OutputDirectory 'checks-bin') + '/'
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
    foreach ($name in @('Core Critical Launcher.exe', 'hostfxr.dll', 'SDL3.dll', 'SDL3-LICENSE.txt', 'Tools/Unshield/unshield.exe', 'Tools/Unshield/provenance.json')) {
        if (!(Test-Path -LiteralPath (Join-Path $PublishDirectory $name) -PathType Leaf)) { throw "Incomplete launcher publication: $name" }
    }
    # A fresh publication only: the MW3-RE runtime and planner are copied in below, never reused.
    foreach ($name in @('Runtime', 'user', 'native-inputs', 'NativePreview', 'Planner', 'Tools/PlannerPython')) {
        if (Test-Path -LiteralPath (Join-Path $PublishDirectory $name)) { throw "Use a fresh launcher publication; it must not already contain: $name" }
    }
    if ($NativePreviewDirectory) {
        $NativePreviewDirectory = [IO.Path]::GetFullPath($NativePreviewDirectory)
        Test-NativePreviewPins -Root $NativePreviewDirectory
        $sourceNativePreview = $NativePreviewDirectory
        if ($WindowsSignTool -and -not (Test-NativePreviewSignedState -Root $NativePreviewDirectory)) {
            $signedPreviewDir = Join-Path $OutputDirectory 'NativePreviewSigned'
            & (Join-Path $PSScriptRoot 'sign_native_preview.ps1') -RuntimeDirectory $NativePreviewDirectory -OutputDirectory $signedPreviewDir -WindowsSignTool $WindowsSignTool -SigningDlib $SigningDlib -SigningMetadata $SigningMetadata -ReceiptPath (Join-Path $OutputDirectory 'native-preview-signatures.json') -ChecksOutputDirectory $checksOutput
            $sourceNativePreview = $signedPreviewDir
        }
        Copy-UnlinkedDirectory -Source $sourceNativePreview -Destination (Join-Path $PublishDirectory 'NativePreview')
    }
    # The launcher runs this planner; it is the only producer of MW3-RE arguments.
    New-Item -ItemType Directory -Path (Join-Path $PublishDirectory 'Planner') | Out-Null
    foreach ($plannerFile in @('mw3_re_launch.py', 'prepared_skin_packs.py', 'prepared_mech_packs.py',
            'content_capabilities.py', 'native_assets.py', 'legacy_content_capabilities.json')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot "../remaster-launcher/$plannerFile") -Destination (Join-Path $PublishDirectory "Planner/$plannerFile")
    }
    $pythonRoot = Join-Path $PublishDirectory 'Tools/PlannerPython'
    if ($NativePreviewDirectory -or $PlannerPythonArchive) {
        # Windows x64 embeddable package from the official Python 3.14.10 release.
        $archivePin = '90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159'
        if (!$PlannerPythonArchive) {
            $PlannerPythonArchive = Join-Path $OutputDirectory 'python-3.14.10-embed-amd64.zip'
            Invoke-WebRequest 'https://www.python.org/ftp/python/3.14.10/python-3.14.10-embed-amd64.zip' -OutFile $PlannerPythonArchive
        }
        if ((Get-FileHash -LiteralPath $PlannerPythonArchive -Algorithm SHA256).Hash -ine $archivePin) {
            throw 'Bundled planner Python archive differs from its published SHA-256'
        }
        Expand-Archive -LiteralPath $PlannerPythonArchive -DestinationPath $pythonRoot
        $python = Join-Path $pythonRoot 'python.exe'
        & $python -I -c 'import sys, json, hashlib; assert sys.version_info[:3] == (3, 14, 10)'
        if ($LASTEXITCODE) { throw 'The bundled planner Python could not load its standard library' }
    }
    if ($NativePreviewDirectory) { Test-NativePreviewPins -Root (Join-Path $PublishDirectory 'NativePreview') }
    if ($PreparationBundle) {
        $PreparationBundle = [IO.Path]::GetFullPath($PreparationBundle)
        & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --verify-bundled-preparation $PreparationBundle
        if ($LASTEXITCODE) { throw 'Bundled source preparation signature/contract verification failed' }
        foreach ($name in @('Preparation/initial.mw3update', 'Preparation/initial.zip', 'update-trust.json')) {
            $source = Join-Path $PreparationBundle $name
            if (!(Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing signed source preparation payload: $name" }
            $target = Join-Path $PublishDirectory $name
            if (Test-Path -LiteralPath $target) { throw "Preparation publication target already exists: $name" }
            New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
            Copy-Item -LiteralPath $source -Destination $target
        }
    }
    if ($WindowsSignTool -or $SigningDlib -or $SigningMetadata) {
        # Preserve the staged native runtime pins and the verified upstream Python package bytes.
        $previewPrefix = (Join-Path $PublishDirectory 'NativePreview') + [IO.Path]::DirectorySeparatorChar
        $pythonPrefix = $pythonRoot + [IO.Path]::DirectorySeparatorChar
        $peFiles = @(Get-ChildItem -LiteralPath $PublishDirectory -Recurse -File | Where-Object {
                $_.Extension -in @('.exe', '.dll', '.pyd') -and
                !$_.FullName.StartsWith($previewPrefix, [StringComparison]::OrdinalIgnoreCase) -and
                !$_.FullName.StartsWith($pythonPrefix, [StringComparison]::OrdinalIgnoreCase)
            } | Select-Object -ExpandProperty FullName)
        & (Join-Path $PSScriptRoot 'sign_windows.ps1') -File $peFiles -SignTool $WindowsSignTool -Dlib $SigningDlib -Metadata $SigningMetadata -ReceiptPath (Join-Path $OutputDirectory 'application-signatures.json')
    }
    & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --verify-media-tools (Join-Path $PublishDirectory 'Tools/Unshield')
    if ($LASTEXITCODE) { throw 'Published media extractor failed the actual launcher admission check after signing' }
    if ($NativePreviewDirectory) {
        $publishedNativePreview = Join-Path $PublishDirectory 'NativePreview'
        Test-NativePreviewPins -Root $publishedNativePreview
        & dotnet run --project (Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj') -c Release "--property:BaseOutputPath=$checksOutput" -- --verify-native-preview $publishedNativePreview
        if ($LASTEXITCODE) { throw 'Published NativePreview failed the launcher contract verification after staging' }
    }
    if ($WindowsSignTool) {
        Assert-AllBinariesSigned -Root $PublishDirectory
    }
    $arguments = @('/Qp', ('/O' + $OutputDirectory), ('/DPublishDirectory=' + $PublishDirectory),
        ('/DMyAppVersion=' + $InstallerVersion), ('/DInstallerAppId={{' + $id + '}'), (Join-Path $PSScriptRoot 'installer.iss'))
    if ($PreparationBundle) { $arguments = @('/DSourcePreparationIncluded=1') + $arguments }
    if ($NativePreviewDirectory) { $arguments = @('/DNativePreviewIncluded=1') + $arguments }
    if ($NativePreviewUpgradeOnly) { $arguments = @('/DNativePreviewUpgradeOnly=1') + $arguments }
    if ($WindowsSignTool) {
        $signCommand = '$q' + [IO.Path]::GetFullPath($WindowsSignTool) + '$q sign /fd SHA256 /tr http://timestamp.acs.microsoft.com /td SHA256 /dlib $q' + [IO.Path]::GetFullPath($SigningDlib) + '$q /dmdf $q' + [IO.Path]::GetFullPath($SigningMetadata) + '$q $f'
        $arguments = @('/DWindowsSigning=1', ('/Sartifact-signing=' + $signCommand)) + $arguments
    }
    & $Compiler @arguments
    if ($LASTEXITCODE) { throw 'Inno Setup compilation failed' }
    $setupFilename = "corecriticalinstaller-$InstallerVersion.exe"
    $setup = Join-Path $OutputDirectory $setupFilename
    if (!(Test-Path -LiteralPath $setup -PathType Leaf)) { throw 'Compiler did not produce the expected installer' }
    if ($WindowsSignTool) {
        & $WindowsSignTool verify /pa /all /v $setup
        $setupSignature = Get-AuthenticodeSignature -LiteralPath $setup
        if ($LASTEXITCODE -or $setupSignature.Status -ne 'Valid' -or -not [bool]$setupSignature.TimeStamperCertificate) {
            throw 'Final installer signature verification failed'
        }
    }
    $publishedPreviewManifest = $(if ($NativePreviewDirectory) {
            [System.IO.File]::ReadAllText((Join-Path $PublishDirectory 'NativePreview/runtime.json')) | ConvertFrom-Json
        } else { $null })
    @{
        kind                         = $(if ($NativePreviewUpgradeOnly) { 'mw3-re-in-place-update' } elseif ($NativePreviewDirectory) { 'mw3-re-playtest-preview' } elseif ($PreparationBundle) { 'private-source-preparation-playtest-preview' } else { 'local-launcher-preview-not-playable-release' })
        version                      = $InstallerVersion
        setup_filename               = $setupFilename
        compiler_sha256              = (Get-FileHash -LiteralPath $Compiler).Hash.ToLowerInvariant()
        setup_sha256                 = (Get-FileHash -LiteralPath $setup).Hash.ToLowerInvariant()
        setup_bytes                  = (Get-Item -LiteralPath $setup).Length
        source_preparation_included  = [bool]$PreparationBundle
        native_preview_included      = [bool]$NativePreviewDirectory
        native_preview_upgrade_only  = [bool]$NativePreviewUpgradeOnly
        native_preview_source_commit = $(if ($publishedPreviewManifest) { [string]$publishedPreviewManifest.provenance.source_commit } else { $null })
        windows_signed               = [bool]$WindowsSignTool
        clean_windows_verified       = $false
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'installer-build.json')
    Write-Output "Launcher preview installer: $setup"
}
