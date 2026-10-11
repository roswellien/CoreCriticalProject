param([Parameter(Mandatory=$true)][string]$PreparationSha256,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskPrep=Join-Path $taskRoot 'reports/m4-hypot-native/control-denial-preparation-r2'
$taskOut=[IO.Path]::GetFullPath($Output)
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
if([IO.Path]::GetDirectoryName($taskOut)-ne(Join-Path $taskRoot 'reports/m4-hypot-native')-or(Test-Path -LiteralPath $taskOut)){throw 'Fresh assigned output required'}
$taskReportPath=Join-Path $taskPrep 'report.json'
if((Hash $taskReportPath)-ne$PreparationSha256){throw 'Exact frozen preparation required'}
$taskPrepReport=Get-Content -Raw -LiteralPath $taskReportPath|ConvertFrom-Json -AsHashtable
foreach($pair in $taskPrepReport.files.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw "Input changed: $($pair.Key)"}}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$taskCompiler=Join-Path $taskRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang++.exe'
$taskInclude=Join-Path $taskRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$taskCommands=[Collections.Generic.List[object]]::new()
$taskPassed=$false
try{
 foreach($level in @('O0','O2')){
  $taskExe=Join-Path $taskOut ("control-$level.exe")
  $taskArguments=@("-$level",'-std=c++20','-fexceptions','-frounding-math','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-isystem',$taskInclude,(Join-Path $taskPrep 'control_runtime.cpp'),(Join-Path $taskPrep 'control_probe.cpp'),'-o',$taskExe)
  &$taskCompiler @taskArguments 2>&1|Tee-Object -FilePath (Join-Path $taskOut "compile-$level.log")
  $taskCommands.Add([ordered]@{program=$taskCompiler;arguments=$taskArguments;exit_code=$LASTEXITCODE})
  if($LASTEXITCODE-ne0){throw 'Actual native control compiler failed'}
 }
 foreach($pair in $taskPrepReport.files.GetEnumerator()){if((Hash $pair.Key)-ne$pair.Value){throw 'Source changed during build'}}
 $taskPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $taskOut 'failure.txt');throw}
finally{
 $taskPins=[ordered]@{};foreach($pair in $taskPrepReport.files.GetEnumerator()){$taskPins[$pair.Key]=$pair.Value}
 foreach($path in @($taskReportPath,$PSCommandPath,$taskCompiler,(Get-Command link.exe).Source)){$taskPins[$path]=Hash $path}
 foreach($file in Get-ChildItem -LiteralPath $taskOut -File){$taskPins[$file.FullName]=Hash $file.FullName}
 [ordered]@{passed=$taskPassed;preparation=$taskPrep;preparation_sha256=$PreparationSha256;commands=$taskCommands;executables=@('control-O0.exe','control-O2.exe');native_executed=$false;initializer_credit=0;files=$taskPins}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $taskOut 'report.json')
}
