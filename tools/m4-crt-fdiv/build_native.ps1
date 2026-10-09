param([Parameter(Mandatory=$true)][string]$OutputDirectory,[Parameter(Mandatory=$true)][string]$ResearchDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major-lt7){throw 'PowerShell7 required'}
$fdRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$fdOut=[IO.Path]::GetFullPath($OutputDirectory);$fdResearch=[IO.Path]::GetFullPath($ResearchDirectory)
if([IO.Path]::GetDirectoryName($fdOut)-ne(Join-Path $fdRoot 'reports/m4-crt-fdiv')-or[IO.Path]::GetDirectoryName($fdResearch)-ne(Join-Path $fdRoot 'reports/m4-crt-fdiv')){throw 'Immediate private FDIV report directories required'}
$fdName=Split-Path $fdOut -Leaf;if($fdName-notmatch '^[a-z0-9-]+$'){throw 'Simple output name required'}
$fdBuilds=@{O0=(Join-Path $fdRoot "build/m4-fdiv-$fdName-O0");O2=(Join-Path $fdRoot "build/m4-fdiv-$fdName-O2")}
foreach($fdPath in @($fdOut)+@($fdBuilds.Values)){if(Test-Path -LiteralPath $fdPath){throw 'Fresh FDIV reports/build directories required before mutation'}}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$fdRuntime=Join-Path $fdRoot 'reports/m4-runtime/context-r9/build.json';if((Hash $fdRuntime)-ne'12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5'){throw 'Frozen r9 build association required'}
$fdSources=[ordered]@{};$fdBaseline=Get-Content -Raw -LiteralPath $fdRuntime|ConvertFrom-Json
foreach($fdPair in $fdBaseline.source_files.PSObject.Properties){if((Hash $fdPair.Name)-ne$fdPair.Value){throw 'Frozen r9 source changed'};$fdSources[$fdPair.Name]=$fdPair.Value}
foreach($fdPath in @($PSScriptRoot,$fdResearch,(Join-Path $fdRoot 'tests/m4-crt-fdiv'),(Join-Path $fdRoot 'tools/m4-guest-cw'),(Join-Path $fdRoot 'tools/m4-startup'),(Join-Path $fdRoot 'runtime'))){foreach($fdFile in Get-ChildItem -LiteralPath $fdPath -Recurse -File){if($fdFile.FullName-notmatch '__pycache__'){$fdSources[$fdFile.FullName]=Hash $fdFile.FullName}}}
$fdLLVM=Join-Path $fdRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$fdVS='C:/Program Files/Microsoft Visual Studio/18/Community';$fdCMake=Join-Path $fdVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$fdTools=[ordered]@{};$fdCommands=[Collections.Generic.List[object]]::new();$fdPassed=$false
New-Item -ItemType Directory -Path $fdOut|Out-Null
foreach($fdPair in $fdSources.GetEnumerator()){$fdCopy=Join-Path $fdOut ('sources/'+[IO.Path]::GetRelativePath($fdRoot,$fdPair.Key));New-Item -ItemType Directory -Force -Path (Split-Path $fdCopy -Parent)|Out-Null;Copy-Item -LiteralPath $fdPair.Key -Destination $fdCopy}
function Run([string]$program,[string[]]$arguments,[string]$log){$fdTools[$program]=Hash $program;$fdLog=Join-Path $fdOut $log;[IO.File]::WriteAllBytes($fdLog,[byte[]]::new(0));&$program @arguments 2>&1|Tee-Object -FilePath $fdLog|Out-Null;$fdExit=$LASTEXITCODE;$fdCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$fdExit;log=$fdLog;log_sha256=(Hash $fdLog)});if($fdExit-ne0){throw 'Required FDIV build/test command failed'}}
try{
 Import-Module (Join-Path $fdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $fdVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 Run (Join-Path $fdLLVM 'opt.exe') @('-passes=verify','-disable-output',(Join-Path $fdResearch 'host.ll')) 'verify.log'
 foreach($fdLevel in @('O0','O2')){$fdIR=Join-Path $fdResearch 'host.ll';if($fdLevel-eq'O2'){$fdIR=Join-Path $fdOut 'host-O2.ll';Run (Join-Path $fdLLVM 'opt.exe') @('-passes=default<O2>','-S',(Join-Path $fdResearch 'host.ll'),'-o',$fdIR) 'opt-O2.log'};$fdObject=Join-Path $fdOut "writer-$fdLevel.obj";Run (Join-Path $fdLLVM 'llc.exe') @('-filetype=obj',"-$fdLevel",$fdIR,'-o',$fdObject) "llc-$fdLevel.log"
  $fdFlags=if($fdLevel-eq'O0'){'/Od /DNDEBUG /showIncludes'}else{'/O2 /DNDEBUG /showIncludes'}
  Run $fdCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$fdBuilds[$fdLevel],'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$fdLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$fdFlags","-DMW34_FDIV_INCLUDE=$fdResearch","-DMW34_FDIV_OBJECT=$fdObject") "configure-$fdLevel.log"
  Run $fdCMake @('--build',$fdBuilds[$fdLevel],'--parallel','8','--verbose') "build-$fdLevel.log"
  Run (Join-Path $fdBuilds[$fdLevel] 'fdiv_native_tests.exe') @((Join-Path $fdRoot 'MW3/Mech3.exe'),(Join-Path $fdRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $fdResearch 'pack.bin'),(Join-Path $fdOut "native-$fdLevel.bin")) "tests-$fdLevel.log"
 }
 foreach($fdPair in $fdSources.GetEnumerator()){if((Hash $fdPair.Key)-ne$fdPair.Value){throw 'FDIV source changed during invocation'}};$fdPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $fdOut 'failure.txt');throw}
finally{$fdArtifacts=[ordered]@{};foreach($fdPath in @($fdOut)+@($fdBuilds.Values)){if(Test-Path -LiteralPath $fdPath){foreach($fdFile in Get-ChildItem -LiteralPath $fdPath -Recurse -File){$fdArtifacts[$fdFile.FullName]=Hash $fdFile.FullName}}};[ordered]@{passed=$fdPassed;scope='Native-only exact writer/real Windows lookup path and bounded typed FNCLEX; original execution absent';sources=$fdSources;tools=$fdTools;commands=$fdCommands;artifacts=$fdArtifacts;workers=@{O0=(Join-Path $fdBuilds.O0 'fdiv_native_tests.exe');O2=(Join-Path $fdBuilds.O2 'fdiv_native_tests.exe')};runtime_r9_build=$fdRuntime;runtime_r9_sha256=(Hash $fdRuntime);whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $fdOut 'build.json')}
