param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$ctRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$ctBase=Join-Path $ctRoot 'reports/m4-capture-direct';$ctOut=[IO.Path]::GetFullPath($OutputDirectory)
if([IO.Path]::GetDirectoryName($ctOut)-ne$ctBase-or(Test-Path -LiteralPath $ctOut)){throw 'Fresh immediate controls build required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$ctPrimary=Join-Path $ctBase 'build-r1/build.json';$ctBuild=Get-Content -Raw -LiteralPath $ctPrimary|ConvertFrom-Json
if(-not$ctBuild.passed){throw 'Passed frozen writer build required'}
foreach($ctPair in $ctBuild.sources.PSObject.Properties){if((Hash $ctPair.Name)-ne$ctPair.Value){throw 'Frozen transport source changed'}}
foreach($ctPair in $ctBuild.objects.PSObject.Properties){if((Hash $ctPair.Name)-ne$ctPair.Value){throw 'Frozen transport object changed'}}
$ctSources=[ordered]@{};foreach($ctName in @('controls.cpp','hardware.s','build_controls.ps1')){$ctPath=Join-Path $PSScriptRoot $ctName;$ctSources[$ctPath]=Hash $ctPath}
New-Item -ItemType Directory -Path $ctOut|Out-Null;New-Item -ItemType Directory -Path (Join-Path $ctOut 'sources')|Out-Null
foreach($ctPair in $ctSources.GetEnumerator()){Copy-Item -LiteralPath $ctPair.Key -Destination (Join-Path $ctOut ('sources/'+[IO.Path]::GetFileName($ctPair.Key)))}
$ctVS='C:/Program Files/Microsoft Visual Studio/18/Community';$ctLLVM=Join-Path $ctRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$ctClang=Join-Path $ctLLVM 'clang-cl.exe';$ctAsm=Join-Path $ctLLVM 'clang.exe';$ctLink=Join-Path $ctLLVM 'lld-link.exe'
$ctCommands=[Collections.Generic.List[object]]::new();$ctArtifacts=[ordered]@{};$ctWorkers=[ordered]@{};$ctPassed=$false;$ctTools=[ordered]@{};$ctHeaders=[ordered]@{}
foreach($ctPath in @($ctClang,$ctAsm,$ctLink,(Join-Path $ctVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$ctTools[$ctPath]=Hash $ctPath}
function Run([string]$p,[string[]]$a,[string]$label){$ctLog=Join-Path $ctOut "$label.log";[IO.File]::WriteAllBytes($ctLog,[byte[]]::new(0));&$p @a 2>&1|Tee-Object -FilePath $ctLog|Out-Null;$ctExit=$LASTEXITCODE;$ctCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$ctExit;log_path=$ctLog;log_sha256=(Hash $ctLog)});if($ctExit-ne0){throw "Control build failed: $label"}}
try{
 Import-Module (Join-Path $ctVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $ctVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $ctBoundary=Join-Path $ctOut 'hardware.obj';Run $ctAsm @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $PSScriptRoot 'hardware.s'),'-o',$ctBoundary) 'hardware'
 foreach($ctLevel in @('O0','O2')){$ctFlag=if($ctLevel-eq'O0'){'/Od'}else{'/O2'};$ctObject=Join-Path $ctOut "controls-$ctLevel.obj";$ctExe=Join-Path $ctOut "capture_controls-$ctLevel.exe";Run $ctClang @('/nologo','/std:c++20','/EHsc','/MD','/W4','/showIncludes',$ctFlag,'/c',(Join-Path $PSScriptRoot 'controls.cpp'),"/Fo$ctObject") "controls-$ctLevel";$ctArgs=@('/nologo',"/out:$ctExe",$ctObject,$ctBoundary,(Join-Path $ctBase "build-r1/capture_direct-$ctLevel.obj"),(Join-Path $ctBase 'build-r1/preserve.obj'),'bcrypt.lib','kernel32.lib');foreach($ctDir in($env:LIB-split';')){$ctArgs+="/libpath:$ctDir"};Run $ctLink $ctArgs "link-$ctLevel";$ctWorkers[$ctLevel]=$ctExe}
 foreach($ctPair in $ctSources.GetEnumerator()){if((Hash $ctPair.Key)-ne$ctPair.Value){throw 'Controls source changed during compilation'}};$ctPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $ctOut 'failure.txt');throw}
finally{
 foreach($ctLog in Get-ChildItem -LiteralPath $ctOut -Filter '*.log' -File){foreach($ctLine in Get-Content -LiteralPath $ctLog.FullName){if($ctLine-match'Note: including file:\s*(.+?)\s*$'){$ctPath=$Matches[1].Trim();if(Test-Path -LiteralPath $ctPath){$ctHeaders[[IO.Path]::GetFullPath($ctPath)]=Hash $ctPath}}}}
 foreach($ctFile in Get-ChildItem -LiteralPath $ctOut -Recurse -File){$ctArtifacts[$ctFile.FullName]=Hash $ctFile.FullName}
 [ordered]@{passed=$ctPassed;primary_build=$ctPrimary;primary_sha256=(Hash $ctPrimary);sources=$ctSources;tools=$ctTools;artifacts=$ctArtifacts;compiler_read_headers=$ctHeaders;workers=$ctWorkers;commands=@($ctCommands);native_executed=$false;game_executed=$false;planned_hardware_pairs_per_level=47;planned_refusals_per_level=27;planned_default_limit_records_per_level=200001;scope='Control fixture compilation only; strict host state domain and unchanged capture limits'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $ctOut 'build.json')
}
