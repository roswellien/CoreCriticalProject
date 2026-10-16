param(
    [Parameter(Mandatory=$true)][string]$Generated,
    [string]$Build='build/pirates-moon-native-r1',
    [string]$Baseline='build/m4-crt-heap-carry-O2-loader'
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $root
$generatedPath=(Resolve-Path -LiteralPath $Generated).Path.Replace('\','/')
$reportRoot=[IO.Path]::GetFullPath((Join-Path $root 'reports/pirates-moon'))+[IO.Path]::DirectorySeparatorChar
if(-not $generatedPath.Replace('/','\').StartsWith($reportRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'PM generated directory must stay in reports/pirates-moon/'}
foreach($name in @('target.inc','entries.inc','routers.inc','objects.txt')){if(-not(Test-Path -LiteralPath (Join-Path $generatedPath $name))){throw "Missing generated PM input $name"}}
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
$llvm=Join-Path $root 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$cmake=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$ninja=Join-Path $vs 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
Import-Module (Join-Path $vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$defs=@()
foreach($line in (Get-Content (Join-Path $Baseline 'CMakeCache.txt'))){
    if($line -match '^(MW34_[A-Z_]+):[A-Z]+=(.*)$' -and $Matches[1] -ne 'MW34_MFC_OBJECT_LIST'){$defs+="-D$($Matches[1])=$($Matches[2])"}
}
& $cmake -G Ninja -S (Join-Path $PSScriptRoot 'native') -B $Build -DCMAKE_BUILD_TYPE=Release "-DCMAKE_MAKE_PROGRAM=$ninja" "-DCMAKE_CXX_COMPILER=$llvm/clang-cl.exe" @defs "-DMW34_PM_GENERATED=$generatedPath" "-DMW34_MFC_OBJECT_LIST=$generatedPath/objects.txt"
if($LASTEXITCODE){throw 'PM native configuration failed'}
& $cmake --build $Build --parallel 1
if($LASTEXITCODE){throw 'PM native build failed'}
