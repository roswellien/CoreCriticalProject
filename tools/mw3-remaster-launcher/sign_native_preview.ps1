param(
    [string]$RuntimeDirectory = '',
    [string]$OutputDirectory = '',
    [string]$WindowsSignTool = '',
    [string]$SigningDlib = '',
    [string]$SigningMetadata = '',
    [string]$ReceiptPath = '',
    [string]$LauncherChecksProject = '',
    [string]$ChecksOutputDirectory = ''
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'native_preview_helpers.ps1')

if ($MyInvocation.InvocationName -ne '.') {
    foreach ($requiredName in @(
            'RuntimeDirectory',
            'OutputDirectory',
            'WindowsSignTool',
            'SigningDlib',
            'SigningMetadata'
        )) {
        $val = [string](Get-Variable -Name $requiredName -ValueOnly)
        if ([string]::IsNullOrWhiteSpace($val)) {
            throw "Missing required parameter: -$requiredName"
        }
    }

    $runtimeFull = [IO.Path]::GetFullPath($RuntimeDirectory)
    $outputFull = [IO.Path]::GetFullPath($OutputDirectory)
    $signToolFull = [IO.Path]::GetFullPath($WindowsSignTool)
    $dlibFull = [IO.Path]::GetFullPath($SigningDlib)
    $metadataFull = [IO.Path]::GetFullPath($SigningMetadata)

    foreach ($leaf in @($signToolFull, $dlibFull, $metadataFull)) {
        if (-not (Test-Path -LiteralPath $leaf -PathType Leaf)) {
            throw "Missing signing input: $leaf"
        }
        Assert-UnlinkedPath -Path $leaf -IncludeParents
    }

    if (-not (Test-Path -LiteralPath $runtimeFull -PathType Container)) {
        throw "Runtime directory does not exist: $runtimeFull"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $runtimeFull 'runtime.json') -PathType Leaf)) {
        throw "Runtime directory is missing runtime.json: $runtimeFull"
    }

    if (-not $ReceiptPath) {
        $ReceiptPath = $outputFull.TrimEnd('\', '/') + '.signatures.json'
    }
    $receiptFull = [IO.Path]::GetFullPath($ReceiptPath)

    if (-not $LauncherChecksProject) {
        $LauncherChecksProject = Join-Path $PSScriptRoot '../mw3-remaster-launcher-tests/LauncherChecks.csproj'
    }
    $checksProjFull = [IO.Path]::GetFullPath($LauncherChecksProject)
    if (-not (Test-Path -LiteralPath $checksProjFull -PathType Leaf)) {
        throw "LauncherChecks project does not exist: $checksProjFull"
    }

    if (Test-Path -LiteralPath $outputFull) {
        throw "Output directory already exists; supply a fresh path: $outputFull"
    }
    if (Test-Path -LiteralPath $receiptFull) {
        throw "Receipt path already exists; supply a fresh path: $receiptFull"
    }

    Assert-UnlinkedPath -Path $runtimeFull -IncludeParents
    Assert-UnlinkedPath -Path $outputFull -IncludeParents
    Assert-UnlinkedPath -Path $receiptFull -IncludeParents

    if ((Test-PathsOverlap $runtimeFull $outputFull) -or
        (Test-PathsOverlap $runtimeFull $receiptFull) -or
        (Test-PathsOverlap $outputFull $receiptFull)) {
        throw 'RuntimeDirectory, OutputDirectory, and ReceiptPath must not overlap'
    }

    $checksOutFull = ''
    if ($ChecksOutputDirectory) {
        $checksOutFull = [IO.Path]::GetFullPath($ChecksOutputDirectory)
        Assert-UnlinkedPath -Path $checksOutFull -IncludeParents
        if ((Test-PathsOverlap $runtimeFull $checksOutFull) -or
            (Test-PathsOverlap $outputFull $checksOutFull) -or
            (Test-PathsOverlap $receiptFull $checksOutFull)) {
            throw 'ChecksOutputDirectory must not overlap RuntimeDirectory, OutputDirectory, or ReceiptPath'
        }
    }

    # Pre-sign validation before allocating output or invoking Azure Artifact Signing.
    Test-NativePreviewPins -Root $runtimeFull -RequireExactClosure

    $allocatedChecksDir = ''
    try {
        if (-not $checksOutFull) {
            $allocatedChecksDir = Join-Path ([IO.Path]::GetTempPath()) ('mw3-preview-checks-' + [Guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $allocatedChecksDir | Out-Null
            $checksOutFull = $allocatedChecksDir
        }
        $checksOutNorm = $checksOutFull.TrimEnd('\', '/') + '/'

        Invoke-NativePreviewVerifier -ProjectPath $checksProjFull -BaseOutputPathNormalized $checksOutNorm -RuntimeDirectory $runtimeFull

        $inputManifestPath = Join-Path $runtimeFull 'runtime.json'
        $inputManifest = [System.IO.File]::ReadAllText($inputManifestPath) | ConvertFrom-Json
        $obsRel = 'metadata/build-observation.json'
        $obsSourcePath = Join-Path $runtimeFull ($obsRel.Replace('/', '\'))
        $obsHasSource = $false
        $obsBeforeBytes = [long]0
        $obsBeforeSha = ''
        if ((Test-Path -LiteralPath $obsSourcePath -PathType Leaf) -or
            ($null -ne $inputManifest.files.PSObject.Properties[$obsRel])) {
            $obsHasSource = $true
            $obsBeforeBytes = (Get-Item -LiteralPath $obsSourcePath -Force).Length
            $obsBeforeSha = (Get-FileHash -LiteralPath $obsSourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
        }

        New-Item -ItemType Directory -Path $outputFull | Out-Null
        $incompleteMarker = Join-Path $outputFull '.incomplete'
        [System.IO.File]::WriteAllText($incompleteMarker, "incomplete`n", [System.Text.UTF8Encoding]::new($false))

        Copy-UnlinkedDirectory -Source $runtimeFull -Destination $outputFull

        $peFiles = @(Get-PeFiles -Root $outputFull)
        if ($peFiles.Count -lt 1) {
            throw "No PE binaries found to verify or sign in $outputFull"
        }

        $receiptDir = [IO.Path]::GetDirectoryName($receiptFull)
        if ($receiptDir -and -not (Test-Path -LiteralPath $receiptDir -PathType Container)) {
            [IO.Directory]::CreateDirectory($receiptDir) | Out-Null
        }

        $global:LASTEXITCODE = 0
        & (Join-Path $PSScriptRoot 'sign_windows.ps1') -File $peFiles -SignTool $signToolFull -Dlib $dlibFull -Metadata $metadataFull -ReceiptPath $receiptFull
        if ($LASTEXITCODE) {
            throw "sign_windows.ps1 failed for $outputFull"
        }

        Assert-AllBinariesSigned -Root $outputFull

        if ($obsHasSource) {
            $obsOutPath = Join-Path $outputFull ($obsRel.Replace('/', '\'))
            $obsAfterBytes = (Get-Item -LiteralPath $obsOutPath -Force).Length
            $obsAfterSha = (Get-FileHash -LiteralPath $obsOutPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($obsAfterBytes -ne $obsBeforeBytes -or $obsAfterSha -cne $obsBeforeSha) {
                throw 'metadata/build-observation.json changed during runtime signing'
            }
        }

        $outManifestPath = Join-Path $outputFull 'runtime.json'
        $signedManifest = [System.IO.File]::ReadAllText($outManifestPath) | ConvertFrom-Json

        $rolesOut = [ordered]@{}
        $roleKeys = [string[]]@($signedManifest.roles.PSObject.Properties | ForEach-Object { [string]$_.Name })
        [System.Array]::Sort($roleKeys, [System.StringComparer]::Ordinal)
        foreach ($roleKey in $roleKeys) {
            $rolesOut[$roleKey] = [string]$signedManifest.roles.$roleKey
        }

        $depsOut = [string[]]@($signedManifest.dependencies | ForEach-Object { [string]$_ })

        $capsOut = [ordered]@{}
        if ($signedManifest.capabilities) {
            $capKeys = [string[]]@($signedManifest.capabilities.PSObject.Properties | ForEach-Object { [string]$_.Name })
            [System.Array]::Sort($capKeys, [System.StringComparer]::Ordinal)
            foreach ($capKey in $capKeys) {
                $capsOut[$capKey] = [int[]]@($signedManifest.capabilities.$capKey | ForEach-Object { [int]$_ })
            }
        }

        $filesOut = [ordered]@{}
        $fileKeys = [string[]]@($signedManifest.files.PSObject.Properties | ForEach-Object { [string]$_.Name })
        [System.Array]::Sort($fileKeys, [System.StringComparer]::Ordinal)
        foreach ($fileKey in $fileKeys) {
            $memberPath = Resolve-RuntimeRelativeFile -Root $outputFull -RelativePath $fileKey
            $memberBytes = (Get-Item -LiteralPath $memberPath -Force).Length
            $memberSha = (Get-FileHash -LiteralPath $memberPath -Algorithm SHA256).Hash.ToLowerInvariant()
            $filesOut[$fileKey] = [ordered]@{
                bytes  = [long]$memberBytes
                sha256 = [string]$memberSha
            }
        }

        $execRel = [string]$rolesOut['executable']
        $signedExecSha = [string]$filesOut[$execRel]['sha256']
        $provenanceOut = [ordered]@{
            source_commit = [string]$signedManifest.provenance.source_commit
            build_id      = 'mw3-re-' + $signedExecSha
            builder       = [string]$signedManifest.provenance.builder
        }

        $manifestOut = [ordered]@{
            schema_version = [int]$signedManifest.schema_version
            engine         = [string]$signedManifest.engine
            roles          = $rolesOut
            dependencies   = $depsOut
            files          = $filesOut
            provenance     = $provenanceOut
            capabilities   = $capsOut
        }

        $jsonOut = ConvertTo-Json -InputObject $manifestOut -Depth 10
        [System.IO.File]::WriteAllText($outManifestPath, $jsonOut, [System.Text.UTF8Encoding]::new($false))

        Test-NativePreviewPins -Root $outputFull -RequireExactClosure -IgnoreRelativePaths @('.incomplete')
        Invoke-NativePreviewVerifier -ProjectPath $checksProjFull -BaseOutputPathNormalized $checksOutNorm -RuntimeDirectory $outputFull

        Remove-Item -LiteralPath $incompleteMarker -Force
        Write-Output "Verified signed MW3-RE runtime ($($provenanceOut['build_id'])): $outputFull"
    }
    finally {
        if ($allocatedChecksDir -and (Test-Path -LiteralPath $allocatedChecksDir)) {
            Remove-Item -LiteralPath $allocatedChecksDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
