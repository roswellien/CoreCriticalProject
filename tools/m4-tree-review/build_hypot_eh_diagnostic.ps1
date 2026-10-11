param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskOut=[IO.Path]::GetFullPath($Output)
if([IO.Path]::GetDirectoryName($taskOut)-ne(Join-Path $taskRoot 'reports/m4-tree-review')-or(Test-Path -LiteralPath $taskOut)){throw 'Fresh owned output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$taskCompiler=Join-Path $taskRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang++.exe'
$taskInclude=Join-Path $taskRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'
$taskRuntime=Join-Path $taskRoot 'reports/m4-hypot-native/control-preparation-r1/control_runtime.cpp'
$taskProbe=Join-Path $PSScriptRoot 'hypot_eh_diagnostic.cpp'
$taskCommands=[Collections.Generic.List[object]]::new()
$taskPassed=$false
try{
 foreach($level in @('O0','O2')){
  $taskObjects=@()
  foreach($source in @($taskRuntime,$taskProbe)){
   $taskStem=[IO.Path]::GetFileNameWithoutExtension($source)
   $taskObj=Join-Path $taskOut "$taskStem-$level.obj"
   $taskDep=Join-Path $taskOut "$taskStem-$level.d"
   $taskArguments=@("-$level",'-std=c++20','-fexceptions','-frounding-math','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-isystem',$taskInclude,'-MD','-MF',$taskDep,'-c',$source,'-o',$taskObj)
   &$taskCompiler @taskArguments 2>&1|Tee-Object -FilePath (Join-Path $taskOut "$taskStem-$level.log")
   $taskCommands.Add([ordered]@{program=$taskCompiler;arguments=$taskArguments;exit_code=$LASTEXITCODE})
   if($LASTEXITCODE-ne0){throw 'Actual diagnostic compiler failed'}
   $taskObjects+=$taskObj
  }
  $taskExe=Join-Path $taskOut "diagnostic-$level.exe"
  $taskArguments=@($taskObjects)+@('-o',$taskExe)
  &$taskCompiler @taskArguments 2>&1|Tee-Object -FilePath (Join-Path $taskOut "link-$level.log")
  $taskCommands.Add([ordered]@{program=$taskCompiler;arguments=$taskArguments;exit_code=$LASTEXITCODE})
  if($LASTEXITCODE-ne0){throw 'Actual diagnostic linker failed'}
 }
 $taskPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $taskOut 'failure.txt');throw}
finally{
 $taskPins=[ordered]@{}
 foreach($path in @($PSCommandPath,$taskRuntime,$taskProbe,$taskCompiler,(Get-Command link.exe).Source,(Join-Path $taskRoot 'reports/m4-hypot-native/control-preparation-r1/control_probe.cpp'))){$taskPins[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
 foreach($file in Get-ChildItem -LiteralPath $taskOut -File){$taskPins[$file.FullName]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
 [ordered]@{passed=$taskPassed;diagnostic_only=$true;initializer_credit=0;commands=$taskCommands;files=$taskPins}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $taskOut 'report.json')
}
