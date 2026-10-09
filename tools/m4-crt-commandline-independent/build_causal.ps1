param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$mwCmdRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$mwCmdOut=[IO.Path]::GetFullPath($OutputDirectory);$mwCmdBase=Join-Path $mwCmdRoot 'reports/m4-crt-commandline-native'
if(-not $mwCmdOut.StartsWith($mwCmdBase+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $mwCmdOut)){throw 'Fresh independent private controls path required'}
$mwCmdVS='C:/Program Files/Microsoft Visual Studio/18/Community';$mwCmdLLVM=Join-Path $mwCmdRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
Import-Module "$mwCmdVS/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $mwCmdVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
New-Item -ItemType Directory $mwCmdOut|Out-Null
function Get-MWCmdHash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
$mwCmdPins=Get-Content -Raw -LiteralPath (Join-Path $mwCmdBase 'author-review-r1/pins.json')|ConvertFrom-Json
$mwCmdSources=[ordered]@{};foreach($mwCmdPath in @($PSCommandPath,(Join-Path $PSScriptRoot 'causal.cpp'))){$mwCmdSources[$mwCmdPath]=Get-MWCmdHash $mwCmdPath;Copy-Item -LiteralPath $mwCmdPath -Destination (Join-Path $mwCmdOut (Split-Path $mwCmdPath -Leaf))}
$mwCmdCalls=[Collections.Generic.List[object]]::new();$mwCmdConsumed=[ordered]@{};$mwCmdPassed=$false;$mwCmdFailure=$null
function Invoke-MWCmd([string]$Program,[string[]]$Arguments,[string]$Log){[IO.File]::WriteAllText($Log,'');$mwCmdOld=$ErrorActionPreference;$ErrorActionPreference='Continue';try{& $Program @Arguments 2>&1|Set-Content -Encoding utf8 -LiteralPath $Log;$mwCmdExit=$LASTEXITCODE}finally{$ErrorActionPreference=$mwCmdOld};$mwCmdCalls.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$mwCmdExit;log_path=$Log;log_sha256=(Get-MWCmdHash $Log)});if($mwCmdExit -ne 0){throw "Independent tool failed: $Program exit=$mwCmdExit; actual log $Log"}}
try{
 foreach($mwCmdLevel in @('O0','O2')){
  $mwCmdLibrary=[IO.Path]::GetFullPath((Join-Path $mwCmdRoot "build/m4-cmd-native-build-r3-$mwCmdLevel/commandline_registry.lib"));$mwCmdHash=Get-MWCmdHash $mwCmdLibrary
  $mwCmdRecorded=@($mwCmdPins.bindings|Where-Object {$_.path -eq $mwCmdLibrary});if($mwCmdRecorded.Count -ne 1 -or $mwCmdRecorded[0].sha256 -ne $mwCmdHash){throw 'Exact frozen accepted-candidate library hash required'};$mwCmdConsumed[$mwCmdLibrary]=$mwCmdHash
  $mwCmdExe=Join-Path $mwCmdOut "causal-$mwCmdLevel.exe";$mwCmdObj=Join-Path $mwCmdOut "causal-$mwCmdLevel.obj";$mwCmdFlag=if($mwCmdLevel -eq 'O0'){'/Od'}else{'/O2'}
  Invoke-MWCmd "$mwCmdLLVM/clang-cl.exe" @('/nologo','/MD','/EHsc','/std:c++20',$mwCmdFlag,('-Wno-invalid-offset'+'of'),'/showIncludes','/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',"/I$mwCmdRoot/tools/m4-crt-commandline-native","/I$mwCmdRoot/tools/m4-runtime","/I$mwCmdRoot/tools/m4-startup","/I$mwCmdRoot/runtime","/I$mwCmdRoot/reports/m4-crt-commandline-native/static-r1","/I$mwCmdRoot/local/tools/remill-v6.0.1/remill-6.0.1/include",'/c',(Join-Path $PSScriptRoot 'causal.cpp'),"/Fo:$mwCmdObj") (Join-Path $mwCmdOut "compile-$mwCmdLevel.log")
  Invoke-MWCmd "$mwCmdLLVM/clang-cl.exe" @('/nologo',$mwCmdObj,$mwCmdLibrary,"/Fe:$mwCmdExe",'/link','bcrypt.lib') (Join-Path $mwCmdOut "link-$mwCmdLevel.log")
  Invoke-MWCmd $mwCmdExe @((Join-Path $mwCmdRoot 'MW3/Mech3.exe'),(Join-Path $mwCmdRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),(Join-Path $mwCmdRoot 'reports/m4-crt-commandline-native/static-r1/pack.bin')) (Join-Path $mwCmdOut "run-$mwCmdLevel.log")
 }
 foreach($mwCmdPath in $mwCmdSources.Keys){if((Get-MWCmdHash $mwCmdPath) -ne $mwCmdSources[$mwCmdPath]){throw 'Own independent source changed during tests'}};$mwCmdPassed=$true
}catch{$mwCmdFailure=$_.Exception.Message;$_|Out-String|Set-Content -LiteralPath (Join-Path $mwCmdOut 'failure.txt');throw}finally{
 $mwCmdTools=[ordered]@{};foreach($mwCmdPath in @("$mwCmdLLVM/clang-cl.exe",(Get-Command link.exe).Source,(Get-Process -Id $PID).Path,"$mwCmdVS/Common7/Tools/Microsoft.VisualStudio.DevShell.dll")){$mwCmdTools[$mwCmdPath]=Get-MWCmdHash $mwCmdPath}
 $mwCmdFiles=[ordered]@{};foreach($mwCmdFile in Get-ChildItem -LiteralPath $mwCmdOut -File){$mwCmdFiles[$mwCmdFile.FullName]=Get-MWCmdHash $mwCmdFile.FullName}
 [ordered]@{passed=$mwCmdPassed;failure=$mwCmdFailure;sources=$mwCmdSources;tools=$mwCmdTools;consumed_libraries=$mwCmdConsumed;commands=@($mwCmdCalls);artifacts=$mwCmdFiles;scope='Own independent actual compiled native library controls only; original/provider code not executed';whole_M4_complete=$false}|ConvertTo-Json -Depth 15|Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwCmdOut 'build.json')
}
