param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$shRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$shBase=Join-Path $shRoot 'reports/m4-capture-shared';$shOut=[IO.Path]::GetFullPath($OutputDirectory)
if([IO.Path]::GetDirectoryName($shOut)-ne$shBase-or(Test-Path -LiteralPath $shOut)){throw 'Fresh immediate shared-pilot report required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$shSources=[ordered]@{}
foreach($shName in @('capture_shared.hpp','capture_shared.cpp','driver.cpp','controls.cpp','preserve_v2.s','hardware.s','prepare_sources.py','prepare_controls.py','build.ps1')){$shPath=Join-Path $PSScriptRoot $shName;$shSources[$shPath]=Hash $shPath}
$shReader=Join-Path $shRoot 'tools/m4-pipeline/capture_shared.py';$shSources[$shReader]=Hash $shReader
$shVS='C:/Program Files/Microsoft Visual Studio/18/Community';$shLLVM=Join-Path $shRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$shClang=Join-Path $shLLVM 'clang-cl.exe';$shAsm=Join-Path $shLLVM 'clang.exe';$shLink=Join-Path $shLLVM 'lld-link.exe'
$shTools=[ordered]@{};foreach($shPath in @($shClang,$shAsm,$shLink,(Join-Path $shVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$shTools[$shPath]=Hash $shPath}
New-Item -ItemType Directory -Path $shOut|Out-Null;New-Item -ItemType Directory -Path (Join-Path $shOut 'sources')|Out-Null
foreach($shPair in $shSources.GetEnumerator()){Copy-Item -LiteralPath $shPair.Key -Destination (Join-Path $shOut ('sources/'+[IO.Path]::GetFileName($shPair.Key)))}
$shCommands=[Collections.Generic.List[object]]::new();$shArtifacts=[ordered]@{};$shWorkers=[ordered]@{};$shControls=[ordered]@{};$shObjects=[ordered]@{};$shLibraries=[ordered]@{};$shHeaders=[ordered]@{};$shPassed=$false;$shLibEnvironment=$null
function Run([string]$program,[string[]]$arguments,[string]$label){$shLog=Join-Path $shOut "$label.log";[IO.File]::WriteAllBytes($shLog,[byte[]]::new(0));&$program @arguments 2>&1|Tee-Object -FilePath $shLog|Out-Null;$shExit=$LASTEXITCODE;$shCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$shExit;log_path=$shLog;log_sha256=(Hash $shLog)});if($shExit-ne0){throw "Pilot build failed: $label"}}
try{
 Import-Module (Join-Path $shVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $shVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $shLibEnvironment=$env:LIB;foreach($shLib in @('bcrypt.lib','kernel32.lib','msvcrt.lib','oldnames.lib','vcruntime.lib','ucrt.lib')){foreach($shDirectory in ($env:LIB -split ';')){$shPath=Join-Path $shDirectory $shLib;if(Test-Path -LiteralPath $shPath){$shLibraries[$shPath]=Hash $shPath;break}}}
 foreach($shAssembly in @('preserve_v2','hardware')){$shObj=Join-Path $shOut "$shAssembly.obj";Run $shAsm @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $PSScriptRoot "$shAssembly.s"),'-o',$shObj) $shAssembly;$shObjects[$shObj]=Hash $shObj}
 foreach($shLevel in @('O0','O2')){
  $shFlag=if($shLevel-eq'O0'){'/Od'}else{'/O2'}
  foreach($shUnit in @('capture_shared','driver','controls')){$shObj=Join-Path $shOut "$shUnit-$shLevel.obj";Run $shClang @('/nologo','/std:c++20','/EHsc','/MD','/W4','/showIncludes',$shFlag,'/c',(Join-Path $PSScriptRoot "$shUnit.cpp"),"/Fo$shObj") "$shUnit-$shLevel";$shObjects[$shObj]=Hash $shObj}
  foreach($shUnit in @('driver','controls')){$shExe=Join-Path $shOut "shared_$shUnit-$shLevel.exe";$shArgs=@('/nologo',"/out:$shExe",(Join-Path $shOut "capture_shared-$shLevel.obj"),(Join-Path $shOut "$shUnit-$shLevel.obj"),(Join-Path $shOut 'preserve_v2.obj'),'bcrypt.lib','kernel32.lib');if($shUnit-eq'controls'){$shArgs+=(Join-Path $shOut 'hardware.obj')};foreach($shDir in ($env:LIB-split';')){$shArgs+="/libpath:$shDir"};Run $shLink $shArgs "link-$shUnit-$shLevel";if($shUnit-eq'driver'){$shWorkers[$shLevel]=$shExe}else{$shControls[$shLevel]=$shExe}}
 }
 foreach($shPair in $shSources.GetEnumerator()){if((Hash $shPair.Key)-ne$shPair.Value){throw 'Pilot source changed during build'}};$shPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $shOut 'failure.txt');throw}
finally{
 foreach($shLog in Get-ChildItem -LiteralPath $shOut -Filter '*.log' -File){foreach($shLine in Get-Content -LiteralPath $shLog.FullName){if($shLine-match'Note: including file:\s*(.+?)\s*$'){$shPath=$Matches[1].Trim();if(Test-Path -LiteralPath $shPath){$shHeaders[[IO.Path]::GetFullPath($shPath)]=Hash $shPath}}}}
 foreach($shFile in Get-ChildItem -LiteralPath $shOut -Recurse -File){$shArtifacts[$shFile.FullName]=Hash $shFile.FullName}
 [ordered]@{passed=$shPassed;sources=$shSources;tools=$shTools;artifacts=$shArtifacts;objects=$shObjects;workers=$shWorkers;control_workers=$shControls;libraries=$shLibraries;compiler_read_headers=$shHeaders;commands=@($shCommands);SDK_library_search_environment=$shLibEnvironment;SDK_file_open_attestation=$false;native_executed=$false;game_executed=$false;scope='Additive shared transport pilot compilation only; no production-format adoption or game acceptance'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $shOut 'build.json')
}
