param([string]$OutputDirectory='D:/Projects/MW34Recomp/reports/m4-crt-entry/prefix-build-r2')
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'PowerShell7 required'}
$mwEntryRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwEntryOut=[System.IO.Path]::GetFullPath($OutputDirectory)
$mwEntryReports=Join-Path $mwEntryRoot 'reports/m4-crt-entry'
if(-not $mwEntryOut.StartsWith($mwEntryReports+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Fresh private entry report directory required'}
$mwEntryName=Split-Path $mwEntryOut -Leaf
if($mwEntryName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwEntryName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$'){throw 'Invalid output name'}
if(Test-Path -LiteralPath $mwEntryOut){throw 'Output already exists'}
function Get-MWEntrySHA([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwEntryPrep=Join-Path $mwEntryRoot 'reports/m4-crt-entry/native-preparation-r1'
if((Get-MWEntrySHA (Join-Path $mwEntryPrep 'report.json')) -ne '4c1174a4a68e6d6ea00c75bb053a4f16f68767d841132be9d6defeaecd5c7ed3'){throw 'Frozen entry object preparation required'}
$mwEntryPins=Get-Content -LiteralPath (Join-Path $mwEntryPrep 'pins.json') -Raw | ConvertFrom-Json
foreach($mwEntryProperty in $mwEntryPins.files.PSObject.Properties){if((Get-MWEntrySHA $mwEntryProperty.Name) -ne $mwEntryProperty.Value){throw "Entry prerequisite changed: $($mwEntryProperty.Name)"}}
New-Item -ItemType Directory -Path $mwEntryOut | Out-Null
$mwEntrySources=[ordered]@{}
$mwEntryPrefix=Join-Path $mwEntryRoot 'reports/m4-crt-entry/prefix-preparation-r2/prefix.cpp'
if((Get-MWEntrySHA $mwEntryPrefix) -ne '23b3540d937a1c6f2f2455a61e6e95f02b7fd905f8f959e5f60b48be755d2e22'){throw 'Exact fresh prefix derivative required'}
foreach($mwEntryPath in @($mwEntryPrefix,(Join-Path $mwEntryRoot 'tools/m4-crt/crt_services.cpp'),(Join-Path $mwEntryRoot 'tools/m4-crt/crt_services.hpp'),$PSCommandPath,(Join-Path $PSScriptRoot 'prefix/CMakeLists.txt'))+@(Get-ChildItem -LiteralPath (Join-Path $mwEntryRoot 'tools/m4-runtime'),(Join-Path $mwEntryRoot 'tools/m4-startup'),(Join-Path $mwEntryRoot 'runtime') -File -Recurse | Where-Object {$_.Extension -in @('.cpp','.hpp')} | Select-Object -ExpandProperty FullName)){
 $mwEntrySources[$mwEntryPath]=Get-MWEntrySHA $mwEntryPath
 $mwEntryCopy=Join-Path (Join-Path $mwEntryOut 'sources') ([System.IO.Path]::GetRelativePath($mwEntryRoot,$mwEntryPath))
 New-Item -ItemType Directory -Force -Path (Split-Path $mwEntryCopy) | Out-Null
 Copy-Item -LiteralPath $mwEntryPath -Destination $mwEntryCopy
}
$mwEntryVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwEntryLLVM=Join-Path $mwEntryRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwEntryCMake=Join-Path $mwEntryVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwEntryNinja=Join-Path $mwEntryVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$mwEntryTools=[ordered]@{}
foreach($mwEntryTool in @($mwEntryCMake,$mwEntryNinja,(Join-Path $mwEntryLLVM 'clang-cl.exe'),(Join-Path $mwEntryLLVM 'lld-link.exe'),(Join-Path $mwEntryLLVM 'llvm-lib.exe'))){$mwEntryTools[$mwEntryTool]=Get-MWEntrySHA $mwEntryTool}
$mwEntryCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MWEntryTool([string]$Program,[string[]]$Arguments,[string]$Log){
 $mwEntrySaved=$ErrorActionPreference;$ErrorActionPreference='Continue'
 try{& $Program @Arguments *> $Log;$mwEntryExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwEntrySaved}
 $mwEntryCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwEntryExit;log=$Log;log_sha256=(Get-MWEntrySHA $Log)})
 if($mwEntryExit -ne 0){throw "Entry tool failed: $Program exit=$mwEntryExit; $Log"}
}
$mwEntryPassed=$false;$mwEntryFailure=$null;$mwEntryBuilds=[System.Collections.Generic.List[object]]::new()
try{
 Import-Module (Join-Path $mwEntryVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $mwEntryVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
 $env:PATH="$mwEntryLLVM;$(Split-Path $mwEntryNinja);$env:PATH"
 $mwEntryTemp=Join-Path $mwEntryOut 'compiler-temp';New-Item -ItemType Directory -Path $mwEntryTemp | Out-Null
 $env:TEMP=$mwEntryTemp;$env:TMP=$mwEntryTemp;$env:TMPDIR=$mwEntryTemp
 foreach($mwEntryLevel in @('O0','O2')){
  $mwEntryBuild=Join-Path $mwEntryRoot "build/m4-crte-$mwEntryName-$mwEntryLevel"
  if(Test-Path -LiteralPath $mwEntryBuild){throw 'Build directory already exists'}
  $mwEntryObject=Join-Path $mwEntryPrep "candidate-$mwEntryLevel.obj"
  $mwEntryFlag=if($mwEntryLevel -eq 'O0'){'/Od'}else{'/O2'}
  Invoke-MWEntryTool $mwEntryCMake @('-G','Ninja','-S',(Join-Path $PSScriptRoot 'prefix'),'-B',$mwEntryBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$mwEntryLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$mwEntryFlag /DNDEBUG", "-DMW34_ENTRY_OBJECT=$mwEntryObject", "-DMW34_PREFIX_SOURCE=$mwEntryPrefix") (Join-Path $mwEntryOut "configure-$mwEntryLevel.log")
  Invoke-MWEntryTool $mwEntryCMake @('--build',$mwEntryBuild,'--verbose','--parallel','4') (Join-Path $mwEntryOut "build-$mwEntryLevel.log")
  $mwEntryWorker=Join-Path $mwEntryBuild 'mw34_crt_entry_first_fault.exe'
  Invoke-MWEntryTool $mwEntryWorker @((Join-Path $mwEntryRoot 'MW3/Mech3.exe'),$mwEntryObject,(Join-Path $mwEntryRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $mwEntryOut "native-$mwEntryLevel")) (Join-Path $mwEntryOut "native-$mwEntryLevel.log")
  $mwEntryBuilds.Add([ordered]@{level=$mwEntryLevel;directory=$mwEntryBuild;object=$mwEntryObject;worker=$mwEntryWorker})
 }
 foreach($mwEntryPath in $mwEntrySources.Keys){if((Get-MWEntrySHA $mwEntryPath) -ne $mwEntrySources[$mwEntryPath]){throw 'Source changed during entry build'}}
 $mwEntryPassed=$true
}catch{$mwEntryFailure=$_.Exception.Message;throw}finally{
 $mwEntryArtifacts=[ordered]@{}
 foreach($mwEntryFile in Get-ChildItem -LiteralPath $mwEntryOut -Recurse -File | Where-Object {$_.FullName -notmatch 'compiler-temp'} | Sort-Object FullName){$mwEntryArtifacts[$mwEntryFile.FullName]=Get-MWEntrySHA $mwEntryFile.FullName}
 foreach($mwEntryBuild in $mwEntryBuilds){foreach($mwEntryFile in Get-ChildItem -LiteralPath $mwEntryBuild.directory -Recurse -File | Where-Object {$_.Extension -in @('.obj','.exe','.json','.cmake') -or $_.Name -in @('.ninja_deps','.ninja_log','build.ninja','rules.ninja','CMakeCache.txt')} | Sort-Object FullName){$mwEntryArtifacts[$mwEntryFile.FullName]=Get-MWEntrySHA $mwEntryFile.FullName}}
 [ordered]@{passed=$mwEntryPassed;failure=$mwEntryFailure;scope='Research-only translated game entry to actual unconnected initialized FDIV data import after three reviewed CRT services; no service or startup acceptance';source_files=$mwEntrySources;primary_pre_call_tools=$mwEntryTools;artifacts=$mwEntryArtifacts;commands=@($mwEntryCommands);builds=@($mwEntryBuilds);original_executed=$false;native_entry_executed=$mwEntryPassed;full_CRT=$false;whole_M4_complete=$false} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $mwEntryOut 'build.json') -Encoding utf8
}
Write-Output 'Native entry three-service prefix probe completed at O0/O2; original comparison and independent review pending'
