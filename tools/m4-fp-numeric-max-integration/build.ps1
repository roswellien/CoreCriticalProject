param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major-lt7){throw 'Bundled PowerShell7 required'}
$nmxRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$nmxOut=[IO.Path]::GetFullPath($OutputDirectory);$nmxName=Split-Path $nmxOut -Leaf
$nmxAllowed=Join-Path $nmxRoot 'reports/m4-fp-numeric-max-integration'
if([IO.Path]::GetDirectoryName($nmxOut)-ne$nmxAllowed -or $nmxName-notmatch'^[a-z][a-z0-9-]{0,63}$'){throw 'Immediate private integration output required'}
$nmxTrees=@{};foreach($nmxLevel in @('O0','O2')){$nmxTrees[$nmxLevel]=Join-Path $nmxRoot "build/m4-nmx-integration-$nmxName-$nmxLevel"}
foreach($nmxPath in @($nmxOut)+@($nmxTrees.Values)){if(Test-Path -LiteralPath $nmxPath){throw 'Entire report/all derived builds must be fresh before mutation'}}
function Hash-Nmx([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$nmxPrep=Join-Path $nmxAllowed 'preparation-r4';$nmxR9=Join-Path $nmxRoot 'reports/m4-runtime/context-r9/build.json'
if((Hash-Nmx $nmxR9)-ne'12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5'){throw 'Frozen r9 manifest required'}
$nmxPinned=Get-Content -Raw -LiteralPath (Join-Path $nmxPrep 'pins.json')|ConvertFrom-Json
foreach($nmxPair in $nmxPinned.files.PSObject.Properties){if((Hash-Nmx $nmxPair.Name)-ne$nmxPair.Value){throw 'Preparation source changed'}}
$nmxSources=[ordered]@{};$nmxR=Get-Content -Raw -LiteralPath $nmxR9|ConvertFrom-Json
foreach($nmxPair in $nmxR.source_files.PSObject.Properties){if((Hash-Nmx $nmxPair.Name)-ne$nmxPair.Value){throw 'Frozen shared r9 source changed'};$nmxSources[$nmxPair.Name]=$nmxPair.Value}
foreach($nmxFile in @((Get-ChildItem -LiteralPath $PSScriptRoot -File);(Get-ChildItem -LiteralPath $nmxPrep -File);(Get-Item -LiteralPath (Join-Path $nmxRoot 'tools/m4-fp-numeric-max/protocol.hpp'));(Get-Item -LiteralPath (Join-Path $nmxRoot 'tools/m4-fp-numeric-max/corpus.hpp')))){$nmxSources[$nmxFile.FullName]=Hash-Nmx $nmxFile.FullName}
New-Item -ItemType Directory -Path $nmxOut|Out-Null;$nmxCopies=[Collections.Generic.List[object]]::new()
foreach($nmxPath in $nmxSources.Keys){$nmxCopy=Join-Path $nmxOut ('sources/'+[IO.Path]::GetRelativePath($nmxRoot,$nmxPath));New-Item -ItemType Directory -Force -Path (Split-Path $nmxCopy)|Out-Null;Copy-Item -LiteralPath $nmxPath -Destination $nmxCopy;$nmxCopies.Add([ordered]@{original_path=$nmxPath;preserved_path=$nmxCopy;sha256=$nmxSources[$nmxPath]})}
$nmxVS='C:/Program Files/Microsoft Visual Studio/18/Community';$nmxLLVM=Join-Path $nmxRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$nmxCMake=Join-Path $nmxVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$nmxNinja=Join-Path $nmxVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$nmxCommands=[Collections.Generic.List[object]]::new();$nmxBuilds=[Collections.Generic.List[object]]::new();$nmxTools=[ordered]@{};$nmxPassed=$false;$nmxFailure=$null
function Run-Nmx([string]$p,[string[]]$a,[string]$log){$nmxTools[$p]=Hash-Nmx $p;[IO.File]::WriteAllText($log,'');$nmxSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{&$p @a 2>&1|Tee-Object -FilePath $log|Out-Null;$nmxExit=$LASTEXITCODE}finally{$ErrorActionPreference=$nmxSaved};$nmxCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$nmxExit;log_path=$log;log_sha256=(Hash-Nmx $log)});if($nmxExit-ne0){throw "Native numeric-max tool failed exit=$nmxExit"}}
try{
 Import-Module (Join-Path $nmxVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $nmxVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $env:PATH="$nmxLLVM;$(Split-Path $nmxNinja);$env:PATH";$nmxTemp=Join-Path $nmxOut 'compiler-temp';New-Item -ItemType Directory $nmxTemp|Out-Null;$env:TEMP=$nmxTemp;$env:TMP=$nmxTemp;$env:TMPDIR=$nmxTemp
 Run-Nmx (Join-Path $nmxLLVM 'llvm-link.exe') (@('-S')+@('4c19f0','4c1a00','780c10f0'|ForEach-Object {Join-Path $nmxPrep "$_-runtime.ll"})+@('-o',(Join-Path $nmxOut 'linked.ll'))) (Join-Path $nmxOut 'link.log')
 Run-Nmx (Join-Path $nmxLLVM 'opt.exe') @('-passes=verify','-S',(Join-Path $nmxOut 'linked.ll'),'-o',(Join-Path $nmxOut 'verified.ll')) (Join-Path $nmxOut 'verify.log')
 foreach($nmxLevel in @('O0','O2')){
  $nmxIR=Join-Path $nmxOut 'verified.ll';if($nmxLevel-eq'O2'){$nmxIR=Join-Path $nmxOut 'optimized.ll';Run-Nmx (Join-Path $nmxLLVM 'opt.exe') @('-passes=default<O2>,verify','-S',(Join-Path $nmxOut 'verified.ll'),'-o',$nmxIR) (Join-Path $nmxOut 'optimize.log')}
  $nmxObject=Join-Path $nmxOut "native-$nmxLevel.obj";Run-Nmx (Join-Path $nmxLLVM 'llc.exe') @('-filetype=obj',"-$nmxLevel",$nmxIR,'-o',$nmxObject) (Join-Path $nmxOut "llc-$nmxLevel.log")
  $nmxOpt=if($nmxLevel-eq'O0'){'/Od'}else{'/O2'}
  Run-Nmx $nmxCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$nmxTrees[$nmxLevel],'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$nmxLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$nmxOpt /DNDEBUG /showIncludes","-DMW34_NMX_OBJECT=$nmxObject") (Join-Path $nmxOut "configure-$nmxLevel.log")
  Run-Nmx $nmxCMake @('--build',$nmxTrees[$nmxLevel],'--verbose','--parallel','6') (Join-Path $nmxOut "build-$nmxLevel.log")
  $nmxExe=Join-Path $nmxTrees[$nmxLevel] 'mw34_nmx_integration.exe';$nmxUnit=Join-Path $nmxOut "unit-$nmxLevel"
  Run-Nmx $nmxExe @('--check-publication',(Join-Path $nmxOut "publication-$nmxLevel")) (Join-Path $nmxOut "publication-$nmxLevel.log")
  Run-Nmx $nmxExe @('--unit',(Join-Path $nmxRoot 'MW3/Mech3.exe'),(Join-Path $nmxRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),$nmxObject,$nmxUnit) (Join-Path $nmxOut "unit-$nmxLevel.log")
  foreach($nmxCorpus in @('default','directed')){Run-Nmx $nmxExe @('--replay',(Join-Path $nmxRoot 'MW3/Mech3.exe'),(Join-Path $nmxRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),$nmxObject,(Join-Path $nmxRoot "reports/m4-fp-numeric-max/original-r5-normal-windows/$nmxCorpus.bin"),(Join-Path $nmxOut "replay-$nmxCorpus-$nmxLevel")) (Join-Path $nmxOut "replay-$nmxCorpus-$nmxLevel.log")}
  $nmxBuilds.Add([ordered]@{level=$nmxLevel;directory=$nmxTrees[$nmxLevel];object=$nmxObject;worker=$nmxExe;unit_directory=$nmxUnit})
 }
 foreach($nmxPath in $nmxSources.Keys){if((Hash-Nmx $nmxPath)-ne$nmxSources[$nmxPath]){throw 'Integration source changed during compiler/worker run'}};$nmxPassed=$true
}catch{$nmxFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $nmxOut 'failure.txt');throw}finally{
 $nmxArtifacts=[ordered]@{};foreach($nmxPath in @($nmxOut)+@($nmxTrees.Values)){if(Test-Path -LiteralPath $nmxPath){foreach($nmxFile in Get-ChildItem -LiteralPath $nmxPath -Recurse -File|Where-Object {$_.FullName-notmatch'compiler-temp'}){$nmxArtifacts[$nmxFile.FullName]=Hash-Nmx $nmxFile.FullName}}}
 foreach($nmxTool in @($nmxCMake,$nmxNinja,(Get-Process -Id $PID).Path,(Join-Path $nmxVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'))){$nmxTools[$nmxTool]=Hash-Nmx $nmxTool}
 [ordered]@{passed=$nmxPassed;failure=$nmxFailure;scope='NEW shared-r9 compiled wrapper/body/exact MSVCP50 leaf native unit candidate; independent/offline comparison pending';source_files=$nmxSources;literal_sources=@($nmxCopies);tools=$nmxTools;artifacts=$nmxArtifacts;commands=@($nmxCommands);builds=@($nmxBuilds);runtime_r9=$nmxR9;runtime_r9_sha256=(Hash-Nmx $nmxR9);original_executed=$false;shared_runtime_modified=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -Encoding utf8 -LiteralPath (Join-Path $nmxOut 'build.json')
}
