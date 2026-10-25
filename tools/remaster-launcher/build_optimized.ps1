param([string]$Revision='optimized-native-r1')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if($Revision -notmatch '^optimized-native-r[0-9]+$'){throw 'Invalid native build revision'}
$target=Join-Path $projectRoot ('local/remaster/'+$Revision)
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
$cmake="$vs/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$ninja="$vs/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
$compiler="$projectRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe"
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$defs=@()
foreach($line in Get-Content "$projectRoot/build/m4-crt-heap-carry-O2-lazy/CMakeCache.txt"){
 if($line -match '^(MW34_[A-Z_]+):[A-Z]+=(.*)$' -and $Matches[1] -notin @('MW34_COMPOSITION_SOURCE','MW34_COMPOSITION_DIRECTORY','MW34_MFC_OBJECT_LIST')){
  $defs+="-D$($Matches[1])=$($Matches[2])"
 }
}
$defs+="-DMW34_MFC_OBJECT_LIST=$target/optimized-mfc-objects.txt"
$dpiManifest=Join-Path $target 'host-source/graphics/native_host.manifest'
if(Test-Path -LiteralPath $dpiManifest){
 $defs+="-DCMAKE_EXE_LINKER_FLAGS=/manifest:embed /manifestinput:`"$dpiManifest`""
}
& $cmake -G Ninja -S "$target/build-definition" -B "$target/build" -DCMAKE_BUILD_TYPE=Release "-DCMAKE_MAKE_PROGRAM=$ninja" "-DCMAKE_CXX_COMPILER=$compiler" @defs "-DMW34_COMPOSITION_SOURCE=$target/host-source/composition.cpp" "-DMW34_COMPOSITION_DIRECTORY=$target/host-source"
if($LASTEXITCODE){throw 'Optimized Remaster configure failed'}
& $cmake --build "$target/build" --parallel 3
if($LASTEXITCODE){throw 'Optimized Remaster build failed'}
