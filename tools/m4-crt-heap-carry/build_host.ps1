param(
    [Parameter(Mandatory=$true)][string]$GameDirectory,
    [Parameter(Mandatory=$true)][string]$RuntimeDirectory,
    [Parameter(Mandatory=$true)][string]$RemillInclude,
    [Parameter(Mandatory=$true)][string]$VulkanInclude,
    [string]$OutputDirectory = "$PSScriptRoot/../../local/native-host-build",
    [string]$LLVMDirectory = '',
    [string]$CMake = '',
    [string]$Ninja = '',
    [int]$Jobs = 2,
    [switch]$Release
)
$ErrorActionPreference = 'Stop'
# Import only the installed compiler environment; do not retain or print its values.
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (!(Test-Path -LiteralPath $vswhere)) { throw 'Install Visual Studio C++ Build Tools and a Windows SDK first' }
$installation = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'No installed x64 C++ toolchain was found' }
$vcvars = Join-Path $installation 'VC/Auxiliary/Build/vcvars64.bat'
$environmentLines = & $env:ComSpec /d /s /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE) { throw 'Could not initialize the installed C++ toolchain' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
}
if (!$LLVMDirectory) {
    $clang = Get-Command clang-cl.exe -ErrorAction SilentlyContinue
    if (!$clang) { throw 'Install LLVM 21.1.8 and provide -LLVMDirectory' }
    $LLVMDirectory = Split-Path $clang.Source -Parent
}
if (!$CMake) { $CMake = Join-Path $installation 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' }
if (!$Ninja) { $Ninja = Join-Path $installation 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe' }
$arguments = @((Join-Path $PSScriptRoot 'build_host.py'), '--game', $GameDirectory,
    '--runtime', $RuntimeDirectory, '--remill-include', $RemillInclude,
    '--vulkan-include', $VulkanInclude, '--llvm', $LLVMDirectory,
    '--cmake', $CMake, '--ninja', $Ninja, '--output', $OutputDirectory, '--jobs', "$Jobs")
if ($Release) { $arguments += '--release' }
& python @arguments
if ($LASTEXITCODE) { throw 'Native host build failed; inspect the output logs' }
