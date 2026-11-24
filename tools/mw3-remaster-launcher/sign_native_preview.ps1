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

function Assert-UnlinkedPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$IncludeParents
    )

    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if ([IO.File]::Exists($current) -or [IO.Directory]::Exists($current)) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
                throw "Path contains a link or reparse point: $current"
            }
        }
        if (-not $IncludeParents) {
            break
        }
        $parent = [IO.Path]::GetDirectoryName($current)
        if (-not $parent -or $parent -eq $current) {
            break
        }
        $current = $parent
    }
}

function Get-UnlinkedFiles {
    param(
        [Parameter(Mandatory = $true)][string]$Root
    )

    $fullRoot = [IO.Path]::GetFullPath($Root)
    if (-not (Test-Path -LiteralPath $fullRoot -PathType Container)) {
        throw "Directory does not exist: $fullRoot"
    }
    Assert-UnlinkedPath -Path $fullRoot -IncludeParents
    $prefix = $fullRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar

    $byRelative = @{}
    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $pending.Push($fullRoot)

    while ($pending.Count -gt 0) {
        $dir = $pending.Pop()
        Assert-UnlinkedPath -Path $dir

        foreach ($childDir in [IO.Directory]::GetDirectories($dir)) {
            $attrs = [IO.File]::GetAttributes($childDir)
            if (($attrs -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Directory contains a link or reparse point: $childDir"
            }
            $pending.Push($childDir)
        }

        foreach ($childFile in [IO.Directory]::GetFiles($dir)) {
            $attrs = [IO.File]::GetAttributes($childFile)
            if (($attrs -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "File is a link or reparse point: $childFile"
            }
            $relative = $childFile.Substring($prefix.Length).Replace('\', '/')
            $byRelative[$relative] = $childFile
        }
    }

    $sortedKeys = [string[]]$byRelative.Keys
    [System.Array]::Sort($sortedKeys, [System.StringComparer]::Ordinal)

    $results = New-Object 'System.Collections.Generic.List[object]'
    foreach ($key in $sortedKeys) {
        $results.Add([pscustomobject]@{
            RelativePath = $key
            FullName     = $byRelative[$key]
        })
    }
    return $results.ToArray()
}

function Copy-UnlinkedDirectory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $destFull = [IO.Path]::GetFullPath($Destination)
    Assert-UnlinkedPath -Path $destFull -IncludeParents
    if (-not (Test-Path -LiteralPath $destFull -PathType Container)) {
        New-Item -ItemType Directory -Path $destFull | Out-Null
    }

    foreach ($entry in @(Get-UnlinkedFiles -Root $Source)) {
        $targetPath = [IO.Path]::GetFullPath((Join-Path $destFull ($entry.RelativePath.Replace('/', '\'))))
        $targetDir = [IO.Path]::GetDirectoryName($targetPath)
        if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) {
            [IO.Directory]::CreateDirectory($targetDir) | Out-Null
        }
        [IO.File]::Copy($entry.FullName, $targetPath, $false)
        $destAttrs = [IO.File]::GetAttributes($targetPath)
        if (($destAttrs -band [IO.FileAttributes]::ReadOnly) -ne 0) {
            [IO.File]::SetAttributes($targetPath, $destAttrs -band (-bnot [IO.FileAttributes]::ReadOnly))
        }
    }
}

function Get-PeFiles {
    param(
        [Parameter(Mandatory = $true)][string]$Root
    )

    $peExtensions = @('.exe', '.dll', '.pyd')
    $pePaths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($entry in @(Get-UnlinkedFiles -Root $Root)) {
        $ext = [IO.Path]::GetExtension($entry.FullName).ToLowerInvariant()
        if ($peExtensions -contains $ext) {
            $pePaths.Add($entry.FullName)
        }
    }
    return $pePaths.ToArray()
}

function Test-ValidTimestampedSignature {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    $sig = Get-AuthenticodeSignature -LiteralPath $Path
    return ($sig.Status -eq 'Valid' -and [bool]$sig.TimeStamperCertificate)
}

function Assert-AllBinariesSigned {
    param(
        [Parameter(Mandatory = $true)][string]$Root
    )

    $fullRoot = [IO.Path]::GetFullPath($Root)
    Assert-UnlinkedPath -Path $fullRoot -IncludeParents
    $prefix = $fullRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar

    $failures = New-Object 'System.Collections.Generic.List[string]'
    foreach ($pePath in @(Get-PeFiles -Root $fullRoot)) {
        $sig = Get-AuthenticodeSignature -LiteralPath $pePath
        if ($sig.Status -ne 'Valid' -or -not [bool]$sig.TimeStamperCertificate) {
            $relative = $pePath.Substring($prefix.Length).Replace('\', '/')
            $hasTs = [bool]$sig.TimeStamperCertificate
            $failures.Add("$relative (Status=$($sig.Status), Timestamped=$hasTs)")
        }
    }

    if ($failures.Count -gt 0) {
        $joined = $failures -join '; '
        throw "Publish directory contains unsigned or untimestamped PE binaries: $joined"
    }
}

function Resolve-RuntimeRelativeFile {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        throw 'Native preview relative path cannot be empty'
    }
    if ($RelativePath.Contains('\') -or $RelativePath.Contains(':') -or
        $RelativePath.StartsWith('/') -or $RelativePath.EndsWith('/')) {
        throw "Invalid native preview relative path: $RelativePath"
    }
    foreach ($segment in $RelativePath.Split('/')) {
        if (-not $segment -or $segment -eq '.' -or $segment -eq '..') {
            throw "Invalid native preview relative path segment: $RelativePath"
        }
    }

    $fullRoot = [IO.Path]::GetFullPath($Root)
    $prefix = $fullRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $candidate = [IO.Path]::GetFullPath((Join-Path $fullRoot ($RelativePath.Replace('/', '\'))))
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Native preview path escapes runtime root: $RelativePath"
    }
    return $candidate
}

function Test-NativePreviewPins {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [switch]$RequireExactClosure,
        [string[]]$IgnoreRelativePaths = @()
    )

    $fullRoot = [IO.Path]::GetFullPath($Root)
    Assert-UnlinkedPath -Path $fullRoot -IncludeParents
    $manifestPath = Join-Path $fullRoot 'runtime.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Missing Native preview runtime.json: $manifestPath"
    }
    Assert-UnlinkedPath -Path $manifestPath

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.schema_version -ne 2 -or $manifest.engine -ne 'mw3-re') {
        throw 'The Native preview needs an MW3-RE schema 2 runtime.json'
    }
    if (-not $manifest.roles -or [string]::IsNullOrWhiteSpace([string]$manifest.roles.executable)) {
        throw 'Native preview runtime.json is missing roles.executable'
    }
    if (-not $manifest.files -or @($manifest.files.PSObject.Properties).Count -eq 0) {
        throw 'Native preview runtime.json contains no pinned files'
    }

    $execRel = [string]$manifest.roles.executable
    if ([IO.Path]::GetExtension($execRel).ToLowerInvariant() -ne '.exe') {
        throw "Native preview roles.executable must reference a .exe binary: $execRel"
    }
    $null = Resolve-RuntimeRelativeFile -Root $fullRoot -RelativePath $execRel
    $hasExecPin = $false

    $aliases = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $declaredSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)

    foreach ($entry in $manifest.files.PSObject.Properties) {
        $rel = [string]$entry.Name
        if ($rel.Equals('runtime.json', [System.StringComparison]::OrdinalIgnoreCase) -or -not $aliases.Add($rel)) {
            throw "Native preview runtime.json contains a self-pin or case-alias key: $rel"
        }
        $null = $declaredSet.Add($rel)
        if ($rel -ceq $execRel) {
            $hasExecPin = $true
        }

        $filePath = Resolve-RuntimeRelativeFile -Root $fullRoot -RelativePath $rel
        if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
            throw "Native preview pinned file is missing: $rel"
        }
        Assert-UnlinkedPath -Path $filePath

        $expectedBytes = [long]$entry.Value.bytes
        $expectedSha = ([string]$entry.Value.sha256).ToLowerInvariant()
        $actualBytes = (Get-Item -LiteralPath $filePath -Force).Length
        $actualSha = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualBytes -ne $expectedBytes -or $actualSha -cne $expectedSha) {
            throw "Native preview file differs from its runtime.json pin: $rel"
        }
    }

    if (-not $hasExecPin) {
        throw "Native preview roles.executable is not pinned in files: $execRel"
    }

    if ($RequireExactClosure) {
        $ignoredSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        $null = $ignoredSet.Add('runtime.json')
        foreach ($ignored in $IgnoreRelativePaths) {
            if (-not [string]::IsNullOrWhiteSpace($ignored)) {
                $null = $ignoredSet.Add($ignored)
            }
        }

        $diskSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
        foreach ($item in @(Get-UnlinkedFiles -Root $fullRoot)) {
            if (-not $ignoredSet.Contains($item.RelativePath)) {
                $null = $diskSet.Add($item.RelativePath)
            }
        }

        if (-not $diskSet.SetEquals($declaredSet)) {
            $extra = @($diskSet | Where-Object { -not $declaredSet.Contains($_) })
            $missing = @($declaredSet | Where-Object { -not $diskSet.Contains($_) })
            throw "Native preview closure mismatch (extra=[$($extra -join ', ')], missing=[$($missing -join ', ')])"
        }
    }
}

function Test-NativePreviewSignedState {
    param(
        [Parameter(Mandatory = $true)][string]$Root
    )

    Test-NativePreviewPins -Root $Root -RequireExactClosure

    $fullRoot = [IO.Path]::GetFullPath($Root)
    $peFiles = @(Get-PeFiles -Root $fullRoot)
    if ($peFiles.Count -eq 0) {
        return $false
    }
    foreach ($peFile in $peFiles) {
        if (-not (Test-ValidTimestampedSignature -Path $peFile)) {
            return $false
        }
    }

    $manifest = Get-Content -LiteralPath (Join-Path $fullRoot 'runtime.json') -Raw | ConvertFrom-Json
    if (-not $manifest.provenance -or -not $manifest.provenance.build_id) {
        return $false
    }
    $execPath = Resolve-RuntimeRelativeFile -Root $fullRoot -RelativePath ([string]$manifest.roles.executable)
    $execSha256 = (Get-FileHash -LiteralPath $execPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedBuildId = 'mw3-re-' + $execSha256
    return ([string]$manifest.provenance.build_id -ceq $expectedBuildId)
}

function Test-PathsOverlap {
    param(
        [Parameter(Mandatory = $true)][string]$First,
        [Parameter(Mandatory = $true)][string]$Second
    )

    $a = [IO.Path]::GetFullPath($First).TrimEnd('\', '/')
    $b = [IO.Path]::GetFullPath($Second).TrimEnd('\', '/')
    $sep = [IO.Path]::DirectorySeparatorChar
    if ($a.Equals($b, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    if ($a.StartsWith($b + $sep, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    if ($b.StartsWith($a + $sep, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    return $false
}

function Invoke-NativePreviewVerifier {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectPath,
        [Parameter(Mandatory = $true)][string]$BaseOutputPathNormalized,
        [Parameter(Mandatory = $true)][string]$RuntimeDirectory
    )

    & dotnet run --project $ProjectPath -c Release "--property:BaseOutputPath=$BaseOutputPathNormalized" -- --verify-native-preview $RuntimeDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "LauncherChecks --verify-native-preview failed for $RuntimeDirectory (exit $LASTEXITCODE)"
    }
}

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
        if ($ChecksOutputDirectory) {
            $checksOutFull = [IO.Path]::GetFullPath($ChecksOutputDirectory)
        }
        else {
            $allocatedChecksDir = Join-Path ([IO.Path]::GetTempPath()) ('mw3-preview-checks-' + [Guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory -Path $allocatedChecksDir | Out-Null
            $checksOutFull = $allocatedChecksDir
        }
        $checksOutNorm = $checksOutFull.TrimEnd('\', '/') + '/'

        Invoke-NativePreviewVerifier -ProjectPath $checksProjFull -BaseOutputPathNormalized $checksOutNorm -RuntimeDirectory $runtimeFull

        $inputManifestPath = Join-Path $runtimeFull 'runtime.json'
        $inputManifest = Get-Content -LiteralPath $inputManifestPath -Raw | ConvertFrom-Json
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

        & (Join-Path $PSScriptRoot 'sign_windows.ps1') -File $peFiles -SignTool $signToolFull -Dlib $dlibFull -Metadata $metadataFull -ReceiptPath $receiptFull
        if ($LASTEXITCODE -ne 0) {
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
        $signedManifest = Get-Content -LiteralPath $outManifestPath -Raw | ConvertFrom-Json

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
