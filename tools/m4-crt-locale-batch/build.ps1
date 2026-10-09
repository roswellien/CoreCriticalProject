param(
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [Parameter(Mandatory=$true)][string]$PreparationDirectory,
 [Parameter(Mandatory=$true)][string]$PreparationSha256
)
$ErrorActionPreference='Stop'
$lbRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$lbBase=Join-Path $lbRoot 'reports/m4-crt-locale-batch'
$lbOut=[IO.Path]::GetFullPath($OutputDirectory)
$lbPrep=[IO.Path]::GetFullPath($PreparationDirectory)
if([IO.Path]::GetDirectoryName($lbOut)-ne$lbBase-or(Test-Path -LiteralPath $lbOut)-or[IO.Path]::GetDirectoryName($lbPrep)-ne$lbBase){throw 'Fresh locale batch build and owned preparation required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$lbReport=Join-Path $lbPrep 'report.json'
if((Hash $lbReport)-ne$PreparationSha256){throw 'Externally fixed preparation identity required'}
$lbPreparation=Get-Content -Raw -LiteralPath $lbReport|ConvertFrom-Json -AsHashtable
if(-not$lbPreparation.passed-or$lbPreparation.native_executed-or$lbPreparation.State_reseed_after_writer){throw 'Source-only prepared batch with persistent State required'}
$lbPins=Get-Content -Raw -LiteralPath (Join-Path $lbPrep 'pins.json')|ConvertFrom-Json -AsHashtable
foreach($lbPair in $lbPins.files.GetEnumerator()){if((Hash $lbPair.Key)-ne$lbPair.Value){throw "Prepared dependency changed: $($lbPair.Key)"}}
$lbObjects=$lbPreparation.entry_objects;$lbLibraries=$lbPreparation.libraries
$lbWriterPath=Join-Path $lbRoot 'reports/m4-capture-direct/build-r4/build.json'
if((Hash $lbWriterPath)-ne'909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96'){throw 'Canonical checked direct writer identity required'}
$lbWriter=Get-Content -Raw -LiteralPath $lbWriterPath|ConvertFrom-Json -AsHashtable
$lbSources=[ordered]@{}
foreach($lbFile in Get-ChildItem -LiteralPath $lbPrep -File|Where-Object{$_.Extension-in@('.cpp','.hpp','.inc')}){$lbSources[$lbFile.FullName]=Hash $lbFile.FullName}
foreach($lbPath in @($PSCommandPath,(Join-Path $lbRoot 'tools/m4-guest-cw/guest_cw.cpp'),(Join-Path $lbRoot 'tools/m4-crt-allocation/capture.s'))){$lbSources[$lbPath]=Hash $lbPath}
foreach($lbPair in $lbWriter.sources.GetEnumerator()){$lbSources[$lbPair.Key]=$lbPair.Value}
New-Item -ItemType Directory -Path $lbOut|Out-Null
foreach($lbPair in $lbSources.GetEnumerator()){
 $lbCopy=Join-Path $lbOut ('sources/'+[IO.Path]::GetRelativePath($lbRoot,$lbPair.Key))
 New-Item -ItemType Directory -Force -Path (Split-Path $lbCopy -Parent)|Out-Null
 Copy-Item -LiteralPath $lbPair.Key -Destination $lbCopy
 if((Hash $lbCopy)-ne$lbPair.Value){throw 'Exact compilation-source preservation required'}
}
$lbVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$lbLLVM=Join-Path $lbRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$lbClang=Join-Path $lbLLVM 'clang-cl.exe';$lbAsm=Join-Path $lbLLVM 'clang.exe';$lbLink=Join-Path $lbLLVM 'lld-link.exe'
$lbTools=[ordered]@{};$lbCommands=[Collections.Generic.List[object]]::new();$lbArtifacts=[ordered]@{};$lbHeaders=[ordered]@{};$lbWorkers=[ordered]@{};$lbPassed=$false;$lbLibEnvironment=$null
foreach($lbPath in @($lbClang,$lbAsm,$lbLink,(Join-Path $lbVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$lbTools[$lbPath]=Hash $lbPath}
function Run([string]$p,[string[]]$a,[string]$label){
 $lbLog=Join-Path $lbOut "$label.log";[IO.File]::WriteAllBytes($lbLog,[byte[]]::new(0))
 &$p @a 2>&1|Tee-Object -FilePath $lbLog|Out-Null;$lbExit=$LASTEXITCODE
 $lbCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$lbExit;log_path=$lbLog;log_sha256=(Hash $lbLog)})
 if($lbExit-ne0){throw "Actual locale-batch compiler failed: $label"}
}
try{
 Import-Module (Join-Path $lbVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $lbVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $lbLibEnvironment=$env:LIB
 foreach($lbLevel in @('O0','O2')){
  $lbFlag=if($lbLevel-eq'O0'){'/Od'}else{'/O2'}
  $lbLevelObjects=@($lbObjects.Keys|Where-Object{$_-match"-$lbLevel\.obj$"})
  $lbEntry=@($lbLevelObjects|Where-Object{$_-match"candidate-$lbLevel\.obj$"})
  $lbControl=@($lbLevelObjects|Where-Object{$_-match"control-$lbLevel\.obj$"})
  if($lbEntry.Count-ne1-or$lbControl.Count-ne1){throw 'Unique frozen original entry and control COFF required'}
  $lbCommon=@('/nologo','/std:c++20','/EHs','/MD','/W4','/showIncludes',$lbFlag,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/DMW34_ENTRY_OBJECT_SHA="{0}"'-f$lbObjects[$lbEntry[0]]),('/DMW34_CONTROL_OBJECT_SHA="{0}"'-f$lbObjects[$lbControl[0]]),'/DMW34_INITTERM_SOURCE_SHA="960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678"','/DMW34_REPLAY_INPUT_SHA="4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a"','/DMW34_MAINARGS_RECOVERY_SHA="ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038"')
  foreach($lbDir in @($lbPrep,(Join-Path $lbRoot 'tools/m4-capture-direct'),(Join-Path $lbRoot 'tools/m4-crt'),(Join-Path $lbRoot 'tools/m4-crt-fdiv'),(Join-Path $lbRoot 'tools/m4-crt-commandline-native'),(Join-Path $lbRoot 'tools/m4-runtime'),(Join-Path $lbRoot 'tools/m4-startup'),(Join-Path $lbRoot 'tools/m4-guest-cw'),(Join-Path $lbRoot 'runtime'),(Join-Path $lbRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'))){$lbCommon+="/I$lbDir"}
  $lbComposition=Join-Path $lbOut "composition-$lbLevel.obj";$lbCrt=Join-Path $lbOut "crt-$lbLevel.obj";$lbCW=Join-Path $lbOut "cw-$lbLevel.obj";$lbCapture=Join-Path $lbOut "capture-$lbLevel.obj";$lbExe=Join-Path $lbOut "locale_batch-$lbLevel.exe"
  Run $lbClang ($lbCommon+@('/c',(Join-Path $lbPrep 'composition.cpp'),"/Fo$lbComposition")) "composition-$lbLevel"
  Run $lbClang ($lbCommon+@('/c',(Join-Path $lbPrep 'crt_services.cpp'),"/Fo$lbCrt")) "crt-$lbLevel"
  Run $lbClang ($lbCommon+@('/c',(Join-Path $lbRoot 'tools/m4-guest-cw/guest_cw.cpp'),"/Fo$lbCW")) "cw-$lbLevel"
  Run $lbAsm @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $lbRoot 'tools/m4-crt-allocation/capture.s'),'-o',$lbCapture) "capture-$lbLevel"
  $lbArgs=@('/nologo',"/out:$lbExe",$lbComposition,$lbCrt,$lbCW,$lbCapture,(Join-Path $lbRoot "reports/m4-capture-direct/build-r4/capture_direct-$lbLevel.obj"),(Join-Path $lbRoot 'reports/m4-capture-direct/build-r4/preserve.obj'),'bcrypt.lib','kernel32.lib')+$lbLevelObjects
  $lbArgs+=@($lbLibraries.Keys|Where-Object{$_-match"-$lbLevel[/\\]"})
  foreach($lbDir in($env:LIB-split';')){$lbArgs+="/libpath:$lbDir"}
  Run $lbLink $lbArgs "link-$lbLevel";$lbWorkers[$lbLevel]=$lbExe
 }
 foreach($lbPair in $lbSources.GetEnumerator()){if((Hash $lbPair.Key)-ne$lbPair.Value){throw 'Source changed during compilation'}}
 foreach($lbPair in $lbObjects.GetEnumerator()){if((Hash $lbPair.Key)-ne$lbPair.Value){throw 'Literal guest COFF changed during compilation'}}
 foreach($lbPair in $lbLibraries.GetEnumerator()){if((Hash $lbPair.Key)-ne$lbPair.Value){throw 'Reused FDIV library changed during compilation'}}
 $lbPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $lbOut 'failure.txt');throw}
finally{
 foreach($lbLog in Get-ChildItem -LiteralPath $lbOut -Filter '*.log' -File){foreach($lbLine in Get-Content -LiteralPath $lbLog.FullName){if($lbLine-match'Note: including file:\s*(.+?)\s*$'){$lbPath=$Matches[1].Trim();if(Test-Path -LiteralPath $lbPath){$lbHeaders[[IO.Path]::GetFullPath($lbPath)]=Hash $lbPath}}}}
 foreach($lbFile in Get-ChildItem -LiteralPath $lbOut -Recurse -File){$lbArtifacts[$lbFile.FullName]=Hash $lbFile.FullName}
 [ordered]@{passed=$lbPassed;scope='Compiled literal critical-section/default-locale/parser research unit only; no execution';preparation_path=$lbReport;preparation_sha256=(Hash $lbReport);sources=$lbSources;tools=$lbTools;entry_objects=$lbObjects;libraries=$lbLibraries;direct_writer_build_path=$lbWriterPath;direct_writer_build_sha256=(Hash $lbWriterPath);direct_writer_objects=$lbWriter.objects;compiler_read_headers=$lbHeaders;artifacts=$lbArtifacts;commands=@($lbCommands);workers=$lbWorkers;SDK_library_search_environment=$lbLibEnvironment;SDK_file_open_attestation=$false;source_bodies_modified=$false;native_executed=$false;original_game_executed=$false;original_attach_proved=$false;full_CRT_complete=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -LiteralPath (Join-Path $lbOut 'build.json')
}
