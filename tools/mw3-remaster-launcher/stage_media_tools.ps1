param(
    [Parameter(Mandatory = $true)][string]$PublishDirectory,
    [string]$MediaBuildDirectory = "$PSScriptRoot/../../local/tools/installer-media-20261021-r2/payload"
)
$ErrorActionPreference = 'Stop'
$media = Get-Content -LiteralPath "$PSScriptRoot/Core/SupportedMedia.json" -Raw | ConvertFrom-Json
$receipt = Get-Content -LiteralPath (Join-Path $MediaBuildDirectory 'provenance.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $MediaBuildDirectory 'unshield.exe')).Hash -ine $media.staticUnshield) {
    throw 'Unexpected static media extractor. Build and review the pinned source recipe first.'
}
foreach ($name in @('unshield.exe', 'LICENSE-unshield.txt', 'LICENSE-zlib.txt')) {
    $source = Join-Path $MediaBuildDirectory $name
    $pin = $receipt.files.$name
    if (-not $pin -or (Get-Item -LiteralPath $source).Length -ne $pin.bytes -or
        (Get-FileHash -LiteralPath $source).Hash -ine $pin.sha256) { throw "Dependency provenance mismatch: $name" }
}
$target = Join-Path $PublishDirectory 'Tools/Unshield'
New-Item -ItemType Directory -Path $target -Force | Out-Null
foreach ($name in @('unshield.exe', 'LICENSE-unshield.txt', 'LICENSE-zlib.txt', 'provenance.json')) {
    Copy-Item -LiteralPath (Join-Path $MediaBuildDirectory $name) -Destination $target
}
@'
Media extraction dependencies
Unshield 1.6.2, commit 51de441ba6893f11026d4671ccef9e8e2a4634fa, MIT.
Source: https://github.com/twogood/unshield
zlib 1.3.2, zlib license. Source: https://zlib.net/fossils/zlib-1.3.2.tar.gz
Both libraries and the MSVC runtime are statically linked into unshield.exe.
The exact admitted executable hash is embedded in SupportedMedia.json.
Included licenses and provenance identify the corresponding source archives.
Rebuild recipe: tools/mw3-remaster-launcher/build_media_tools.ps1.
No original game data or patch payload is included here. This does not clear
other native game/codec artifacts for distribution.
'@ | Set-Content -LiteralPath (Join-Path $target 'DEPENDENCIES.txt') -Encoding utf8
