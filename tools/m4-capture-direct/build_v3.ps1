param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$cdRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$cdBase=Join-Path $cdRoot 'reports/m4-capture-direct'
$cdOut=[IO.Path]::GetFullPath($OutputDirectory)
if([IO.Path]::GetDirectoryName($cdOut)-ne$cdBase-or(Test-Path -LiteralPath $cdOut)){throw 'Fresh immediate direct-writer report required'}
if((Split-Path $cdOut -Leaf)-notmatch'^[a-z0-9-]+$'){throw 'Simple report name required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$cdSources=[ordered]@{}
foreach($cdName in @('capture_direct_v3.hpp','capture_direct_v3.cpp','driver_v3.cpp','preserve_v2.s','build_v3.ps1')){$cdPath=Join-Path $PSScriptRoot $cdName;$cdSources[$cdPath]=Hash $cdPath}
$cdVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$cdLLVM=Join-Path $cdRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$cdClang=Join-Path $cdLLVM 'clang-cl.exe';$cdAsm=Join-Path $cdLLVM 'clang.exe';$cdLink=Join-Path $cdLLVM 'lld-link.exe'
$cdTools=[ordered]@{};foreach($cdPath in @($cdClang,$cdAsm,$cdLink,(Join-Path $cdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$cdTools[$cdPath]=Hash $cdPath}
New-Item -ItemType Directory -Path $cdOut|Out-Null
New-Item -ItemType Directory -Path (Join-Path $cdOut 'sources')|Out-Null
foreach($cdPair in $cdSources.GetEnumerator()){Copy-Item -LiteralPath $cdPair.Key -Destination (Join-Path $cdOut ('sources/'+[IO.Path]::GetFileName($cdPair.Key)))}
$cdCommands=[Collections.Generic.List[object]]::new();$cdArtifacts=[ordered]@{};$cdWorkers=[ordered]@{};$cdObjects=[ordered]@{};$cdLibraries=[ordered]@{};$cdHeaders=[ordered]@{};$cdPassed=$false;$cdLibEnvironment=$null
function Run([string]$program,[string[]]$arguments,[string]$label){$cdLog=Join-Path $cdOut "$label.log";[IO.File]::WriteAllBytes($cdLog,[byte[]]::new(0));&$program @arguments 2>&1|Tee-Object -FilePath $cdLog|Out-Null;$cdExit=$LASTEXITCODE;$cdCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$cdExit;log_path=$cdLog;log_sha256=(Hash $cdLog)});if($cdExit-ne0){throw "Native build invocation failed: $label"}}
try{
 Import-Module (Join-Path $cdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $cdVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $cdLibEnvironment=$env:LIB
 foreach($cdLib in @('bcrypt.lib','kernel32.lib','msvcrt.lib','oldnames.lib','vcruntime.lib','ucrt.lib')){foreach($cdDirectory in ($env:LIB -split ';')){$cdPath=Join-Path $cdDirectory $cdLib;if(Test-Path -LiteralPath $cdPath){$cdLibraries[$cdPath]=Hash $cdPath;break}}}
 $cdPreserve=Join-Path $cdOut 'preserve.obj'
 Run $cdAsm @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $PSScriptRoot 'preserve_v2.s'),'-o',$cdPreserve) 'assembly'
 $cdObjects[$cdPreserve]=Hash $cdPreserve
 foreach($cdLevel in @('O0','O2')){
  $cdFlag=if($cdLevel-eq'O0'){'/Od'}else{'/O2'}
  $cdObject=Join-Path $cdOut "capture_direct-$cdLevel.obj";$cdDriver=Join-Path $cdOut "driver-$cdLevel.obj";$cdExe=Join-Path $cdOut "capture_driver-$cdLevel.exe"
  Run $cdClang @('/nologo','/std:c++20','/EHsc','/MD','/W4','/showIncludes',$cdFlag,'/c',(Join-Path $PSScriptRoot 'capture_direct_v3.cpp'),"/Fo$cdObject") "writer-$cdLevel"
  Run $cdClang @('/nologo','/std:c++20','/EHsc','/MD','/W4','/showIncludes',$cdFlag,'/c',(Join-Path $PSScriptRoot 'driver_v3.cpp'),"/Fo$cdDriver") "driver-$cdLevel"
  $cdLinkArgs=@('/nologo',"/out:$cdExe",$cdObject,$cdDriver,$cdPreserve,'bcrypt.lib','kernel32.lib');foreach($cdDirectory in ($env:LIB -split ';')){$cdLinkArgs+="/libpath:$cdDirectory"}
  Run $cdLink $cdLinkArgs "link-$cdLevel"
  $cdObjects[$cdObject]=Hash $cdObject;$cdObjects[$cdDriver]=Hash $cdDriver;$cdWorkers[$cdLevel]=$cdExe
 }
 foreach($cdPair in $cdSources.GetEnumerator()){if((Hash $cdPair.Key)-ne$cdPair.Value){throw 'Source changed during build'}}
 $cdPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $cdOut 'failure.txt');throw}
finally{
 foreach($cdLog in Get-ChildItem -LiteralPath $cdOut -Filter '*.log' -File){foreach($cdLine in Get-Content -LiteralPath $cdLog.FullName){if($cdLine-match'Note: including file:\s*(.+?)\s*$'){$cdPath=$Matches[1].Trim();if(Test-Path -LiteralPath $cdPath){$cdHeaders[[IO.Path]::GetFullPath($cdPath)]=Hash $cdPath}}}}
 foreach($cdFile in Get-ChildItem -LiteralPath $cdOut -Recurse -File){$cdArtifacts[$cdFile.FullName]=Hash $cdFile.FullName}
 [ordered]@{passed=$cdPassed;sources=$cdSources;tools=$cdTools;artifacts=$cdArtifacts;objects=$cdObjects;workers=$cdWorkers;libraries=$cdLibraries;compiler_read_headers=$cdHeaders;commands=@($cdCommands);SDK_library_search_environment=$cdLibEnvironment;SDK_file_open_attestation=$false;native_executed=$false;game_executed=$false;scope='Transport writer build only; frozen strict v1 archive reader unchanged; ASCII logical name subset; no game semantic proof'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $cdOut 'build.json')
}
