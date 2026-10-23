$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot '../../local/third-party/SDL3-3.4.18'
New-Item -ItemType Directory -Force $destination | Out-Null
$archive = Join-Path $destination 'runtime.zip'
Invoke-WebRequest 'https://github.com/libsdl-org/SDL/releases/download/release-3.4.18/SDL3-3.4.18-win32-x64.zip' -OutFile $archive
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne '75C2C0FC74E7D1206AAEDC22893A35887332F4F85F5C8B74FDDC10D177985F2C') {
    throw 'SDL3 download does not match the pinned upstream archive.'
}
Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $destination 'runtime') -Force
Write-Output 'SDL3 3.4.18 controller runtime ready. Rebuild the launcher to include it.'
