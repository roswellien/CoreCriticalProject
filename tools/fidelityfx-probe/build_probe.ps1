param(
    [Parameter(Mandatory=$true)][string]$SdkDirectory,
    [Parameter(Mandatory=$true)][string]$VulkanInclude,
    [Parameter(Mandatory=$true)][string]$LLVMDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dependencies.json') -Raw | ConvertFrom-Json
foreach ($group in @(@{Root=$SdkDirectory; Pins=$manifest.sdk_files}, @{Root=$VulkanInclude; Pins=$manifest.vulkan_files})) {
    foreach ($pin in $group.Pins.PSObject.Properties) {
        $file = Join-Path $group.Root $pin.Name
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.Value) {
            throw "Dependency hash mismatch: $file"
        }
    }
}
foreach ($name in @('amd_fidelityfx_loader_vk.dll', 'amd_fidelityfx_upscaler_vk.dll')) {
    $signature = Get-AuthenticodeSignature -LiteralPath (Join-Path $SdkDirectory "signedbin/$name")
    if ($signature.Status -ne 'Valid') { throw "Invalid SDK signature: $name ($($signature.Status))" }
}
$compiler = Join-Path $LLVMDirectory 'clang-cl.exe'
$version = (& $compiler --version) -join "`n"
if ($version -notmatch 'clang version 21\.1\.8\b') { throw 'The host toolchain requires LLVM 21.1.8' }
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$installation = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'Install Visual Studio C++ Build Tools and Windows SDK' }
$vcvars = Join-Path $installation 'VC/Auxiliary/Build/vcvars64.bat'
$environmentLines = & $env:ComSpec /d /s /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE) { throw 'Could not initialize compiler environment' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$output = (Resolve-Path -LiteralPath $OutputDirectory).Path
$arguments = @('/nologo', '/std:c++17', '/EHsc', '/MD', '/W4', '/WX',
    "/I$VulkanInclude", "/I$SdkDirectory/api/include", "/I$SdkDirectory/upscalers/include",
    (Join-Path $PSScriptRoot 'probe.cpp'), "/Fo$output/probe.obj", "/Fe$output/probe.exe",
    '/link', '/incremental:no')
& $compiler @arguments
if ($LASTEXITCODE) { throw 'FSR probe compilation failed' }
Write-Output "Built $output/probe.exe; run it with the pinned signedbin directory and GPU index"
