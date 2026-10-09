param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe'}
$cdRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$cdOut=[IO.Path]::GetFullPath($OutputDirectory)
$cdAllowed=Join-Path $cdRoot 'reports/m4-crt-data'
if(-not $cdOut.StartsWith($cdAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Private data evidence path required'}
$cdName=Split-Path $cdOut -Leaf
if($cdName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $cdName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$'){throw 'Fresh simple ownership build name required'}
$cdBuild=Join-Path $cdRoot "build/m4-crt-data-$cdName"
if((Test-Path -LiteralPath $cdOut) -or (Test-Path -LiteralPath $cdBuild)){throw 'Fresh ownership report/build required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$cdSources=[ordered]@{}
foreach($rel in @('tools/m4-crt-data/data_imports.hpp','tools/m4-crt-data/data_imports.cpp','tools/m4-crt-data/provider_data.hpp','tools/m4-crt-data/ownership/CMakeLists.txt','tools/m4-crt-data/ownership/build.ps1','tests/m4-crt-data/ownership_tests.cpp','docs/m4-crt-data-admission.md','tools/m4-runtime/runtime.hpp','tools/m4-runtime/runtime.cpp','tools/m4-runtime/service_provider.hpp','tools/m4-startup/admission.hpp','tools/m4-startup/image_loader.hpp','tools/m4-startup/image_loader.cpp','runtime/core/guest_address.hpp','runtime/memory/guest_memory.hpp','runtime/memory/guest_memory.cpp')){$p=Join-Path $cdRoot $rel;$cdSources[$p]=Hash $p}
New-Item -ItemType Directory $cdOut|Out-Null
$cdCopies=[Collections.Generic.List[object]]::new()
foreach($p in $cdSources.Keys){$copy=Join-Path (Join-Path $cdOut 'sources') ([IO.Path]::GetRelativePath($cdRoot,$p));New-Item -ItemType Directory -Force (Split-Path $copy)|Out-Null;Copy-Item -LiteralPath $p -Destination $copy;if((Hash $copy) -ne $cdSources[$p]){throw 'Literal source copy mismatch'};$cdCopies.Add([ordered]@{original_path=$p;preserved_path=$copy;sha256=$cdSources[$p]})}
$cdCommands=[Collections.Generic.List[object]]::new()
function Run([string]$program,[string[]]$arguments,[string]$log){$saved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $program @arguments 2>&1|Tee-Object -FilePath $log;$code=$LASTEXITCODE}finally{$ErrorActionPreference=$saved};$cdCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$code;log_path=$log;log_sha256=(Hash $log)});if($code -ne 0){throw "Ownership command failed: $program exit=$code"}}
$cdVS='C:/Program Files/Microsoft Visual Studio/18/Community';$passed=$false;$failure=$null
$provider=Join-Path $cdRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';$game=Join-Path $cdRoot 'MW3/Mech3.exe';$raw=Join-Path $cdRoot 'reports/m4-crt-data/commandline-run-r1/original.bin'
try{
 Import-Module (Join-Path $cdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $cdVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $cmake=Join-Path $cdVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 Run $cmake @('-S',$PSScriptRoot,'-B',$cdBuild,'-G','Visual Studio 18 2026','-A','x64') (Join-Path $cdOut 'configure.log')
 Run $cmake @('--build',$cdBuild,'--config','Release','--verbose') (Join-Path $cdOut 'build.log')
 foreach($level in @('O0','O2')){Run (Join-Path $cdBuild "Release/data_reference_tests_$level.exe") @($provider,$game,$raw) (Join-Path $cdOut "test-$level.log")}
 foreach($p in $cdSources.Keys){if((Hash $p) -ne $cdSources[$p]){throw 'Ownership source changed during build'}}
 $passed=$true
}catch{$failure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $cdOut 'failure.txt');throw}finally{
 $artifacts=[ordered]@{};foreach($f in @(Get-ChildItem -LiteralPath $cdOut -Recurse -File;if(Test-Path -LiteralPath $cdBuild){Get-ChildItem -LiteralPath $cdBuild -Recurse -File|Where-Object {$_.Extension -in @('.exe','.obj','.lib','.txt','.cmake','.vcxproj','.props','.json','.tlog')}})|Sort-Object FullName){$artifacts[$f.FullName]=Hash $f.FullName}
 $toolFiles=[ordered]@{};foreach($p in @($cmake,(Get-Process -Id $PID).Path,(Join-Path $cdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Join-Path $cdVS 'MSBuild/Current/Bin/amd64/MSBuild.exe'))+@('cl.exe','link.exe','lib.exe','rc.exe'|ForEach-Object {(Get-Command $_ -ErrorAction SilentlyContinue).Source})){if($p -and (Test-Path -LiteralPath $p)){$toolFiles[$p]=Hash $p}}
 [ordered]@{passed=$passed;failure=$failure;scope='Reference-only data ownership and exact named-IAT admission, not native OS service/writer execution';source_files=$cdSources;literal_source_copies=@($cdCopies);tool_files=$toolFiles;artifacts=$artifacts;commands=@($cdCommands);inputs=@{provider=@{path=$provider;sha256=(Hash $provider)};game=@{path=$game;sha256=(Hash $game)};declared_original_reference=@{path=$raw;sha256=(Hash $raw)}};production_initialized_service=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $cdOut 'build.json')
}
