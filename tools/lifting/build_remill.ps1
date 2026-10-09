param(
    [string]$LLVMRoot,
    [string]$RemillRoot,
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Python = 'C:/Python314/python.exe'
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\', '/')
if (-not $LLVMRoot) { $LLVMRoot = "$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc" }
if (-not $RemillRoot) { $RemillRoot = "$mwRoot/local/tools/remill-v6.0.1/remill-6.0.1" }
$LLVMRoot = (Resolve-Path $LLVMRoot).Path.Replace('\', '/')
$RemillRoot = (Resolve-Path $RemillRoot).Path.Replace('\', '/')
if ((git -C $RemillRoot rev-parse HEAD) -ne '0e324aee8c67a63ec759ef379dcfafa0b3cb1448') { throw 'Pinned Remill commit required' }
if (-not (Select-String -LiteralPath "$RemillRoot/CMakeLists.txt" -SimpleMatch 'option(MW34_X86_FIXTURE_ONLY')) {
    throw 'Apply the recorded remill-v6.0.1-x86.patch before building'
}
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$mwCMake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$(Split-Path $Python);$env:PATH"
$mwDeps = "$mwRoot/local/tools/remill-v6.0.1/dependencies-build"
$mwInstall = "$mwRoot/local/tools/remill-v6.0.1/install"
function Invoke-MWTool([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', "$RemillRoot/dependencies", '-B', $mwDeps, '-DUSE_EXTERNAL_LLVM=ON', "-DCMAKE_PREFIX_PATH=$LLVMRoot", "-DCMAKE_INSTALL_PREFIX=$mwInstall", '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=clang-cl', '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded', "-DPython3_EXECUTABLE=$Python")
Invoke-MWTool $mwCMake @('--build', $mwDeps, '--parallel', '8')
Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $RemillRoot, '-B', "$RemillRoot/build", "-DCMAKE_PREFIX_PATH=$mwInstall;$LLVMRoot", "-DCMAKE_INSTALL_PREFIX=$mwInstall", '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=clang-cl', '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded', '-DREMILL_ENABLE_TESTING=OFF', '-DREMILL_BUILD_SPARC32_RUNTIME=OFF', '-DREMILL_BARRIER_AS_NOP=ON', '-DMW34_X86_FIXTURE_ONLY=ON')
Invoke-MWTool $mwCMake @('--build', "$RemillRoot/build", '--target', 'remill-lift-21', 'x86', '--parallel', '8')
