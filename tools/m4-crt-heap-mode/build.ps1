param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$cpRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$cpOut=[IO.Path]::GetFullPath($OutputDirectory);$cpBase=Join-Path $cpRoot 'reports/m4-crt-heap-mode'
if([IO.Path]::GetDirectoryName($cpOut)-ne$cpBase-or(Test-Path -LiteralPath $cpOut)){throw 'Fresh immediate private composition output required'}
$cpName=Split-Path $cpOut -Leaf;if($cpName-notmatch'^[a-z0-9-]+$'){throw 'Simple experiment name'}
$cpBuilds=@{O0=(Join-Path $cpRoot "reports/m4-crt-heap-mode/$cpName/O0");O2=(Join-Path $cpRoot "reports/m4-crt-heap-mode/$cpName/O2")};foreach($cpBuild in $cpBuilds.Values){if(Test-Path -LiteralPath $cpBuild){throw 'Fresh composition build directories required'}}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$cpPrep=Join-Path $cpBase 'preparation-r2';$cpReceipt=Get-Content -Raw -LiteralPath (Join-Path $cpPrep 'report.json')|ConvertFrom-Json
if(-not $cpReceipt.passed -or $cpReceipt.State_reseed_after_writer){throw 'Completed additive preparation required'}
$cpPins=Get-Content -Raw -LiteralPath (Join-Path $cpPrep 'pins.json')|ConvertFrom-Json;foreach($cpPair in $cpPins.files.PSObject.Properties){if((Hash $cpPair.Name)-ne$cpPair.Value){throw 'Composition prerequisite changed'}}
$cpPrimary=Join-Path $cpRoot 'reports/m4-crt-fdiv/native-build-r3/build.json';$cpGate=Get-Content -Raw -LiteralPath $cpPrimary|ConvertFrom-Json
$cpSources=[ordered]@{};foreach($cpPair in $cpGate.sources.PSObject.Properties){$cpSources[$cpPair.Name]=$cpPair.Value}
foreach($cpFile in Get-ChildItem -LiteralPath $PSScriptRoot,$cpPrep -Recurse -File|Where-Object{$_.Extension-in@('.cpp','.hpp','.inc','.py','.ps1','.s','.ll')-or$_.Name-eq'CMakeLists.txt'}){$cpSources[$cpFile.FullName]=Hash $cpFile.FullName}
foreach($cpFile in @((Join-Path $cpRoot 'tools/m4-crt/crt_services.cpp'),(Join-Path $cpRoot 'tools/m4-crt/crt_services.hpp'))){$cpSources[$cpFile]=Hash $cpFile}
New-Item -ItemType Directory -Path $cpOut|Out-Null
foreach($cpPair in $cpSources.GetEnumerator()){$cpCopy=Join-Path $cpOut ('sources/'+[IO.Path]::GetRelativePath($cpRoot,$cpPair.Key));New-Item -ItemType Directory -Force -Path (Split-Path $cpCopy -Parent)|Out-Null;Copy-Item -LiteralPath $cpPair.Key -Destination $cpCopy;if((Hash $cpCopy)-ne$cpPair.Value){throw 'Exact literal source preservation'}}
$cpVS='C:/Program Files/Microsoft Visual Studio/18/Community';$cpLLVM=Join-Path $cpRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$cpCMake=Join-Path $cpVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$cpNinja=Join-Path $cpVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$cpTools=[ordered]@{};$cpCommands=[Collections.Generic.List[object]]::new();$cpArtifacts=[ordered]@{};$cpLibraries=[ordered]@{};$cpObjects=[ordered]@{};$cpWorkers=[ordered]@{};$cpPassed=$false;$cpLibEnvironment=$null
foreach($cpTool in @($cpCMake,$cpNinja,(Join-Path $cpLLVM 'clang-cl.exe'),(Join-Path $cpLLVM 'clang.exe'),(Join-Path $cpLLVM 'lld-link.exe'),(Join-Path $cpLLVM 'llvm-mt.exe'),'C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe',(Join-Path $cpVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$cpTools[$cpTool]=Hash $cpTool}
function Run([string]$p,[string[]]$a,[string]$log){$cpLog=Join-Path $cpOut $log;[IO.File]::WriteAllBytes($cpLog,[byte[]]::new(0));&$p @a 2>&1|Tee-Object -FilePath $cpLog|Out-Null;$cpCode=$LASTEXITCODE;$cpCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$cpCode;log_path=$cpLog;log_sha256=(Hash $cpLog)});if($cpCode-ne0){throw 'Actual composition build invocation failed'}}
try{
 Import-Module (Join-Path $cpVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $cpVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $cpLibEnvironment=$env:LIB
 foreach($cpLevel in @('O0','O2')){
  $cpProducer=Join-Path (Join-Path $cpRoot 'reports/m4-crt-commandline-carry/preparation-r5') "producer-$cpLevel.obj";$cpObjects[$cpProducer]=Hash $cpProducer
  $cpParser=Join-Path $cpRoot "reports/m4-crt-mainargs/recovery-r3/normal_parser-$cpLevel.obj";$cpObjects[$cpParser]=Hash $cpParser
  $cpHeapObjects=@();foreach($cpKind in @("fragment","provider")){$cpHeapObject=Join-Path (Join-Path $cpRoot 'reports/m4-crt-heap-init/preparation-r2') "$cpKind-$cpLevel.obj";$cpObjects[$cpHeapObject]=Hash $cpHeapObject;$cpHeapObjects+=$cpHeapObject};$cpHeapList=$cpHeapObjects -join ";"
  $cpHeapModeObjects=@();foreach($cpKind in @("selector","probe")){$cpHeapModeObject=Join-Path $cpPrep "$cpKind-$cpLevel.obj";$cpObjects[$cpHeapModeObject]=Hash $cpHeapModeObject;$cpHeapModeObjects+=$cpHeapModeObject};$cpHeapModeList=$cpHeapModeObjects -join ";"
  $cpLocaleObjects=@();foreach($cpKind in @("mbinit","setmbcp","lock")){$cpLocaleObject=Join-Path $cpRoot "reports/m4-crt-locale-default/preparation-r4/$cpKind-$cpLevel.obj";$cpObjects[$cpLocaleObject]=Hash $cpLocaleObject;$cpLocaleObjects+=$cpLocaleObject};$cpLocaleList=$cpLocaleObjects -join ";"
  $cpCapture=Join-Path $cpOut "capture-$cpLevel.obj";Run (Join-Path $cpLLVM 'clang.exe') @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $PSScriptRoot 'capture.s'),'-o',$cpCapture) "capture-$cpLevel.log"
  $cpObject=Join-Path $cpRoot "reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-$cpLevel.obj";$cpObjects[$cpObject]=Hash $cpObject
  $cpMatherr=Join-Path $cpRoot "reports/m4-crt-matherr/paired-native-build-r7/native-$cpLevel.obj";$cpObjects[$cpMatherr]=Hash $cpMatherr
  $cpControl=Join-Path $cpRoot "reports/m4-crt-entry-control/build-r6/control-$cpLevel.obj";$cpObjects[$cpControl]=Hash $cpControl
  $cpIniterm=Join-Path $cpRoot "reports/m4-crt-entry-initterm/provider-preparation-r3/provider-$cpLevel.obj";$cpObjects[$cpIniterm]=Hash $cpIniterm
  $cpMainargs=Join-Path $cpRoot "reports/m4-crt-mainargs/recovery-r3/mainargs-$cpLevel.obj";$cpObjects[$cpMainargs]=Hash $cpMainargs
  $cpArgv=Join-Path $cpRoot "reports/m4-crt-mainargs/recovery-r3/normal_argv-$cpLevel.obj";$cpObjects[$cpArgv]=Hash $cpArgv
  $cpLibrary=Join-Path $cpRoot "build/m4-fdiv-native-build-r3-$cpLevel/fdiv_registry.lib";$cpLibraries[$cpLibrary]=Hash $cpLibrary
  $cpFlags=if($cpLevel-eq'O0'){'/Od /DNDEBUG /showIncludes'}else{'/O2 /DNDEBUG /showIncludes'}
  Run $cpCMake @('-G','Ninja','-S',(Join-Path $PSScriptRoot 'native'),'-B',$cpBuilds[$cpLevel],'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_MAKE_PROGRAM=$cpNinja","-DCMAKE_CXX_COMPILER=$cpLLVM/clang-cl.exe","-DMW34_CAPTURE_OBJECT=$cpCapture","-DMW34_HEAP_OBJECTS=$cpHeapList","-DMW34_HEAP_MODE_OBJECTS=$cpHeapModeList","-DMW34_LOCALE_OBJECTS=$cpLocaleList","-DMW34_CMD_OBJECT=$cpProducer","-DMW34_PARSER_OBJECT=$cpParser","-DMW34_MATHERR_OBJECT=$cpMatherr","-DMW34_CONTROL_OBJECT=$cpControl","-DMW34_INITTERM_OBJECT=$cpIniterm" ,"-DMW34_MAINARGS_OBJECT=$cpMainargs","-DMW34_ARGV_OBJECT=$cpArgv","-DMW34_MAINARGS_RECOVERY_SHA=ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038","-DMW34_INITTERM_SOURCE_SHA=960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678","-DMW34_CONTROL_OBJECT_SHA=$($cpObjects[$cpControl])","-DCMAKE_CXX_FLAGS_RELEASE=$cpFlags","-DMW34_FDIV_LIBRARY=$cpLibrary","-DMW34_ENTRY_OBJECT=$cpObject","-DMW34_ENTRY_OBJECT_SHA=$($cpObjects[$cpObject])","-DMW34_COMPOSITION_SOURCE=$cpPrep/composition.cpp","-DMW34_COMPOSITION_DIRECTORY=$cpPrep",'-DMW34_REPLAY_INPUT_SHA=4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a') "configure-$cpLevel.log"
  Run $cpCMake @('--build',$cpBuilds[$cpLevel],'--verbose') "build-$cpLevel.log";$cpWorkers[$cpLevel]=Join-Path $cpBuilds[$cpLevel] 'entry_heap_mode.exe'
 }
 foreach($cpPair in $cpSources.GetEnumerator()){if((Hash $cpPair.Key)-ne$cpPair.Value){throw 'Source changed during build'}};foreach($cpPair in $cpLibraries.GetEnumerator()){if((Hash $cpPair.Key)-ne$cpPair.Value){throw 'Frozen Registry library changed'}};foreach($cpPair in $cpObjects.GetEnumerator()){if((Hash $cpPair.Key)-ne$cpPair.Value){throw 'Frozen entry object changed'}};$cpPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $cpOut 'failure.txt');throw}
finally{
 $cpHeaders=[ordered]@{};foreach($cpLevel in @('O0','O2')){
$cpLog=Join-Path $cpOut "build-$cpLevel.log";if(Test-Path -LiteralPath $cpLog){foreach($cpLine in Get-Content -LiteralPath $cpLog){if($cpLine-match'Note: including file:\s*(.+?)\s*$'){$cpHeader=$Matches[1].Trim();if(Test-Path -LiteralPath $cpHeader){$cpHeaders[[IO.Path]::GetFullPath($cpHeader)]=Hash $cpHeader}}}}}
 foreach($cpDirectory in @($cpOut)+@($cpBuilds.Values)){if(Test-Path -LiteralPath $cpDirectory){foreach($cpFile in Get-ChildItem -LiteralPath $cpDirectory -Recurse -File){$cpArtifacts[$cpFile.FullName]=Hash $cpFile.FullName}}}
 [ordered]@{passed=$cpPassed;scope='Source/build-only genuine host heap bridge, immutable full HANDLE owner and exact new translated selector/probe and relocated RET to unresolved OS-query CALL; no worker executed';sources=$cpSources;tools=$cpTools;libraries=$cpLibraries;entry_objects=$cpObjects;compiler_read_headers=$cpHeaders;artifacts=$cpArtifacts;commands=@($cpCommands);workers=$cpWorkers;preparation_path=(Join-Path $cpPrep 'report.json');preparation_sha256=(Hash (Join-Path $cpPrep 'report.json'));SDK_library_search_environment=$cpLibEnvironment;SDK_file_open_attestation=$false;native_component_executed=$false;original_executed=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $cpOut 'build.json')
}
