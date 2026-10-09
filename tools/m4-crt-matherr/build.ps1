param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -lt 7){throw 'Use bundled pwsh.exe'}
$mwMathRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwMathOut=[IO.Path]::GetFullPath($OutputDirectory)
$mwMathAllowed=Join-Path $mwMathRoot 'reports/m4-crt-matherr'
$mwMathName=Split-Path $mwMathOut -Leaf
if(-not $mwMathOut.StartsWith($mwMathAllowed+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $mwMathName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or (Test-Path -LiteralPath $mwMathOut)){throw 'Fresh private matherr build directory required'}
function Get-MWMathHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwMathLLVM=Join-Path $mwMathRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
$mwMathVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$mwMathIR=Join-Path $mwMathAllowed 'abi-r1/host.ll'
$mwMathSources=[ordered]@{}
foreach($mwMathPath in @((Join-Path $mwMathAllowed 'preparation-r1/pins.json'),(Join-Path $mwMathAllowed 'abi-r1/pins.json'))){
 $mwMathPins=Get-Content -Raw -LiteralPath $mwMathPath|ConvertFrom-Json
 foreach($mwMathProperty in $mwMathPins.files.PSObject.Properties){if((Get-MWMathHash $mwMathProperty.Name) -ne $mwMathProperty.Value){throw 'Frozen preparation/ABI dependency changed'}}
}
foreach($mwMathFile in @(Get-ChildItem -LiteralPath $PSScriptRoot -File;Get-Item -LiteralPath $mwMathIR;(Get-ChildItem -LiteralPath (Join-Path $mwMathRoot 'tools/m4-runtime') -File|Where-Object {$_.Extension -in '.cpp','.hpp'});(Get-ChildItem -LiteralPath (Join-Path $mwMathRoot 'tools/m4-startup') -File|Where-Object {$_.Extension -in '.cpp','.hpp'});(Get-ChildItem -LiteralPath (Join-Path $mwMathRoot 'runtime/memory') -File);(Get-Item -LiteralPath (Join-Path $mwMathRoot 'runtime/core/guest_address.hpp')))){$mwMathSources[$mwMathFile.FullName]=Get-MWMathHash $mwMathFile.FullName}
New-Item -ItemType Directory $mwMathOut|Out-Null
$mwMathCopies=[Collections.Generic.List[object]]::new()
foreach($mwMathPath in $mwMathSources.Keys){$mwMathCopy=Join-Path (Join-Path $mwMathOut 'sources') ([IO.Path]::GetRelativePath($mwMathRoot,$mwMathPath));New-Item -ItemType Directory -Force -Path (Split-Path $mwMathCopy)|Out-Null;Copy-Item -LiteralPath $mwMathPath -Destination $mwMathCopy;$mwMathCopies.Add([ordered]@{original_path=$mwMathPath;preserved_path=$mwMathCopy;sha256=$mwMathSources[$mwMathPath]})}
$mwMathCommands=[Collections.Generic.List[object]]::new()
function Invoke-MWMath([string]$Program,[string[]]$Arguments,[string]$Log){$mwMathSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Tee-Object -FilePath $Log|Out-Null;$mwMathExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwMathSaved};$mwMathCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwMathExit;log_path=$Log;log_sha256=(Get-MWMathHash $Log)});if($mwMathExit -ne 0){throw "Matherr tool failed $Program exit=$mwMathExit"}}
$mwMathPassed=$false;$mwMathFailure=$null;$mwMathBuilds=[Collections.Generic.List[object]]::new()
try{
 Import-Module (Join-Path $mwMathVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $mwMathVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 $mwMathCMake=Join-Path $mwMathVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
 $mwMathNinja=Join-Path $mwMathVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
 $env:PATH="$mwMathLLVM;$(Split-Path $mwMathNinja);$env:PATH"
 $mwMathTemp=Join-Path $mwMathOut 'compiler-temp';New-Item -ItemType Directory $mwMathTemp|Out-Null
 $env:TEMP=$mwMathTemp;$env:TMP=$mwMathTemp;$env:TMPDIR=$mwMathTemp
 foreach($mwMathLevel in @('O0','O2')){
  $mwMathObject=Join-Path $mwMathOut "native-$mwMathLevel.obj"
  Invoke-MWMath (Join-Path $mwMathLLVM 'clang.exe') @('-target','x86_64-pc-windows-msvc',"-$mwMathLevel",'-c',$mwMathIR,'-o',$mwMathObject) (Join-Path $mwMathOut "IR-$mwMathLevel.log")
  $mwMathBuild=Join-Path $mwMathRoot "build/m4-crt-matherr-$mwMathName-$mwMathLevel"
  if(Test-Path -LiteralPath $mwMathBuild){throw 'Fresh native build required'}
  $mwMathOpt=if($mwMathLevel -eq 'O0'){'/Od'}else{'/O2'}
  Invoke-MWMath $mwMathCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwMathBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$mwMathLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$mwMathOpt /DNDEBUG /showIncludes","-DMW34_MATHERR_OBJECT=$mwMathObject") (Join-Path $mwMathOut "configure-$mwMathLevel.log")
  Invoke-MWMath $mwMathCMake @('--build',$mwMathBuild,'--verbose','--parallel','6') (Join-Path $mwMathOut "build-$mwMathLevel.log")
  $mwMathExe=Join-Path $mwMathBuild 'mw34_matherr_native.exe'
  Invoke-MWMath $mwMathExe @((Join-Path $mwMathRoot 'MW3/Mech3.exe'),(Join-Path $mwMathRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $mwMathAllowed 'preparation-r1/source.bin'),(Join-Path $mwMathOut "native-$mwMathLevel.bin")) (Join-Path $mwMathOut "run-$mwMathLevel.log")
  Invoke-MWMath (Join-Path $mwMathLLVM 'llvm-objdump.exe') @('--disassemble','--reloc','--x86-asm-syntax=intel',$mwMathObject) (Join-Path $mwMathOut "decode-$mwMathLevel.txt")
  $mwMathBuilds.Add([ordered]@{level=$mwMathLevel;directory=$mwMathBuild;object=$mwMathObject;worker=$mwMathExe;observations=(Join-Path $mwMathOut "native-$mwMathLevel.bin")})
 }
 foreach($mwMathPath in $mwMathSources.Keys){if((Get-MWMathHash $mwMathPath) -ne $mwMathSources[$mwMathPath]){throw 'Source changed during matherr build'}}
 $mwMathPassed=$true
}catch{$mwMathFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwMathOut 'failure.txt');throw}finally{
 $mwMathArtifacts=[ordered]@{}
 foreach($mwMathFile in @(Get-ChildItem -LiteralPath $mwMathOut -Recurse -File;foreach($mwMathLevel in @('O0','O2')){$mwMathTree=Join-Path $mwMathRoot "build/m4-crt-matherr-$mwMathName-$mwMathLevel";if(Test-Path -LiteralPath $mwMathTree){Get-ChildItem -LiteralPath $mwMathTree -Recurse -File|Where-Object {$_.Extension -in '.exe','.obj','.lib','.txt','.cmake','.json' -or $_.Name -in 'build.ninja','rules.ninja','.ninja_log'}}})|Where-Object {$_.FullName -notmatch 'compiler-temp'}|Sort-Object FullName){$mwMathArtifacts[$mwMathFile.FullName]=Get-MWMathHash $mwMathFile.FullName}
 $mwMathTools=[ordered]@{}
 foreach($mwMathTool in @($mwMathCMake,$mwMathNinja,(Get-Process -Id $PID).Path,(Join-Path $mwMathVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'))+@('clang.exe','clang-cl.exe','lld-link.exe','llvm-objdump.exe'|ForEach-Object {Join-Path $mwMathLLVM $_})){if($mwMathTool -and (Test-Path -LiteralPath $mwMathTool)){$mwMathTools[$mwMathTool]=Get-MWMathHash $mwMathTool}}
 [ordered]@{passed=$mwMathPassed;failure=$mwMathFailure;scope='Actual ABI-lowered complete matherr leaf typed r9 import experiment; original comparison and independent acceptance pending';source_files=$mwMathSources;literal_sources=@($mwMathCopies);tool_files=$mwMathTools;artifacts=$mwMathArtifacts;commands=@($mwMathCommands);builds=@($mwMathBuilds);original_comparison_passed=$false;independent_acceptance=$false;callback_invoked=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwMathOut 'build.json')
}
