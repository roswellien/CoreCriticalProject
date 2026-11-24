# Shared helpers for signing and verifying staged MW3-RE native preview directories.
# Kept parameterless so callers can dot-source them without overwriting their own param() bindings.

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

    $manifest = [System.IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
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
        Assert-UnlinkedPath -Path $filePath -IncludeParents

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

    $manifest = [System.IO.File]::ReadAllText((Join-Path $fullRoot 'runtime.json')) | ConvertFrom-Json
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
