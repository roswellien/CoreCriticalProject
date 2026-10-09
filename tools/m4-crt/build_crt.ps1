param([string]$OutputDirectory='D:/Projects/MW34Recomp/reports/m4-crt/native-preflight-r2',[string]$ReplayInclude='')
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use pwsh.exe (PowerShell7+) for the CRT evidence recipe'}
$mwCRTRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwCRTOutput=[System.IO.Path]::GetFullPath($OutputDirectory)
$mwCRTReports=Join-Path $mwCRTRoot 'reports/m4-crt'
if(-not $mwCRTOutput.StartsWith($mwCRTReports+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Fresh private CRT output required'}
$mwCRTName=Split-Path $mwCRTOutput -Leaf
if($mwCRTName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwCRTName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$'){throw 'Invalid CRT experiment name'}
$mwCRTBuild=Join-Path $mwCRTRoot "build/m4-crt-$mwCRTName"
if((Test-Path -LiteralPath $mwCRTOutput) -or (Test-Path -LiteralPath $mwCRTBuild)){throw 'CRT reports/derived build already exist'}
function Get-MWCRTHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwCRTRuntimeMap=Join-Path $mwCRTRoot 'reports/m4-runtime/context-r9/build.json'
if((Get-MWCRTHash $mwCRTRuntimeMap) -ne '12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5'){throw 'Exact frozen runtime r9 dependency build required'}
$mwCRTRuntime=Get-Content -Raw -LiteralPath $mwCRTRuntimeMap|ConvertFrom-Json
foreach($mwCRTProperty in $mwCRTRuntime.source_files.PSObject.Properties){if((Get-MWCRTHash $mwCRTProperty.Name) -ne $mwCRTProperty.Value){throw 'Consumed runtime source identity changed'}}
$mwCRTProvider=Join-Path $mwCRTRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
if((Get-MWCRTHash $mwCRTProvider) -ne '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'){throw 'Exact staged CRT provider required as original data'}
if($ReplayInclude){$ReplayInclude=(Resolve-Path -LiteralPath $ReplayInclude).Path}
function Get-MWCRTSources{
 $mwCRTMap=[ordered]@{}
 foreach($mwCRTProperty in $mwCRTRuntime.source_files.PSObject.Properties){$mwCRTMap[$mwCRTProperty.Name]=Get-MWCRTHash $mwCRTProperty.Name}
 foreach($mwCRTFile in @(Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File;Get-ChildItem -LiteralPath (Join-Path $mwCRTRoot 'tests/m4-crt') -Recurse -File;Get-Item -LiteralPath (Join-Path $mwCRTRoot 'docs/m4-crt-contract.md'))|Where-Object {$_.Extension -in @('.cpp','.hpp','.asm','.py','.ps1','.txt','.md') -and $_.FullName -notmatch '__pycache__'}|Sort-Object FullName){$mwCRTMap[$mwCRTFile.FullName]=Get-MWCRTHash $mwCRTFile.FullName}
 if($ReplayInclude){$mwCRTPrivate=(Resolve-Path -LiteralPath $ReplayInclude).Path;if(-not $mwCRTPrivate.StartsWith($mwCRTReports+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Private CRT replay include required'};$mwCRTSpec=Join-Path $mwCRTPrivate 'replay_spec.hpp';$mwCRTMap[$mwCRTSpec]=Get-MWCRTHash $mwCRTSpec}
 if($ReplayInclude){foreach($mwCRTFile in Get-ChildItem -LiteralPath (Join-Path $mwCRTRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime') -File -Recurse){$mwCRTMap[$mwCRTFile.FullName]=Get-MWCRTHash $mwCRTFile.FullName};$mwCRTState=Join-Path $mwCRTRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h';$mwCRTMap[$mwCRTState]=Get-MWCRTHash $mwCRTState}
 return $mwCRTMap
}
$mwCRTSources=Get-MWCRTSources
New-Item -ItemType Directory -Path $mwCRTOutput|Out-Null
$mwCRTCopies=[System.Collections.Generic.List[object]]::new()
foreach($mwCRTPath in $mwCRTSources.Keys){
 $mwCRTCopy=Join-Path (Join-Path $mwCRTOutput 'sources') ([System.IO.Path]::GetRelativePath($mwCRTRoot,$mwCRTPath))
 New-Item -ItemType Directory -Force -Path (Split-Path $mwCRTCopy)|Out-Null;Copy-Item -LiteralPath $mwCRTPath -Destination $mwCRTCopy
 if((Get-MWCRTHash $mwCRTCopy) -ne $mwCRTSources[$mwCRTPath]){throw 'Literal CRT source preservation failed'}
 $mwCRTCopies.Add([ordered]@{original_path=$mwCRTPath;preserved_path=$mwCRTCopy;sha256=$mwCRTSources[$mwCRTPath]})
}
$mwCRTCommands=[System.Collections.Generic.List[object]]::new()
function Invoke-MWCRTTool([string]$Program,[string[]]$Arguments,[string]$Log){
 $mwCRTSaved=$ErrorActionPreference;$ErrorActionPreference='Continue'
 try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log;$mwCRTExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwCRTSaved}
 $mwCRTCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwCRTExit;log_path=$Log;log_sha256=(Get-MWCRTHash $Log)})
 if($mwCRTExit -ne 0){throw "CRT tool failed $Program exit=$mwCRTExit"}
}
$mwCRTPassed=$false;$mwCRTFailure=$null
$mwCRTVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwCRTLLVM=Join-Path $mwCRTRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc'
try{
 Import-Module (Join-Path $mwCRTVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $mwCRTVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $mwCRTCMake=Join-Path $mwCRTVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 $mwCRTCTest=Join-Path $mwCRTVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
 $mwCRTNinja=Join-Path $mwCRTVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
 $env:PATH="$mwCRTLLVM/bin;$(Split-Path $mwCRTNinja);$env:PATH"
 $mwCRTTemp=Join-Path $mwCRTOutput 'compiler-temp';New-Item -ItemType Directory $mwCRTTemp|Out-Null;$env:TEMP=$mwCRTTemp;$env:TMP=$mwCRTTemp;$env:TMPDIR=$mwCRTTemp
 Invoke-MWCRTTool $mwCRTCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwCRTBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$mwCRTLLVM/bin/clang-cl.exe",'-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG',"-DMW34_CRT_REPLAY_INCLUDE=$ReplayInclude") (Join-Path $mwCRTOutput 'configure.log')
 Invoke-MWCRTTool $mwCRTCMake @('--build',$mwCRTBuild,'--parallel','8') (Join-Path $mwCRTOutput 'build.log')
 Invoke-MWCRTTool $mwCRTCTest @('--test-dir',$mwCRTBuild,'--verbose','--output-on-failure','--no-tests=error','--output-junit',(Join-Path $mwCRTOutput 'ctest.xml')) (Join-Path $mwCRTOutput 'ctest.log')
 if((Get-MWCRTSources|ConvertTo-Json -Compress) -ne ($mwCRTSources|ConvertTo-Json -Compress)){throw 'Source changed during CRT build'}
 if((Get-MWCRTHash $mwCRTProvider) -ne '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'){throw 'Provider changed during CRT build'}
 $mwCRTPassed=$true
}catch{$mwCRTFailure=$_.Exception.Message;throw}finally{
 $mwCRTArtifacts=[ordered]@{}
 foreach($mwCRTFile in @(Get-ChildItem -LiteralPath $mwCRTOutput -Recurse -File;if(Test-Path -LiteralPath $mwCRTBuild){Get-ChildItem -LiteralPath $mwCRTBuild -Recurse -File|Where-Object {$_.Extension -in @('.exe','.obj','.lib','.cmake','.json','.xml') -or $_.Name -in @('build.ninja','rules.ninja','CMakeCache.txt','.ninja_log')}})|Where-Object {$_.FullName -notmatch 'compiler-temp'}|Sort-Object FullName){$mwCRTArtifacts[$mwCRTFile.FullName]=Get-MWCRTHash $mwCRTFile.FullName}
 $mwCRTTools=[ordered]@{}
 foreach($mwCRTTool in @($mwCRTCMake,$mwCRTCTest,$mwCRTNinja,(Get-Process -Id $PID).Path,(Join-Path $mwCRTVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Command rc.exe -ErrorAction SilentlyContinue).Source)+@('clang-cl.exe','llvm-lib.exe','lld-link.exe','llvm-mt.exe'|ForEach-Object {Join-Path $mwCRTLLVM "bin/$_"})){if($mwCRTTool -and (Test-Path -LiteralPath $mwCRTTool)){$mwCRTTools[$mwCRTTool]=Get-MWCRTHash $mwCRTTool}}
 [ordered]@{passed=$mwCRTPassed;failure=$mwCRTFailure;scope='Authored native CRT service preflight only; original provider equivalence pending';source_files=$mwCRTSources;literal_source_copies=@($mwCRTCopies);tool_files=$mwCRTTools;artifacts=$mwCRTArtifacts;commands=@($mwCRTCommands);runtime_build_path=$mwCRTRuntimeMap;runtime_build_sha256=(Get-MWCRTHash $mwCRTRuntimeMap);provider_path=$mwCRTProvider;provider_sha256=(Get-MWCRTHash $mwCRTProvider);original_provider_executed=$false;actual_game_service_admitted=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 16|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwCRTOutput 'build.json')
}
Write-Output 'Native CRT service authored preflight passed; original provider comparison remains required'
