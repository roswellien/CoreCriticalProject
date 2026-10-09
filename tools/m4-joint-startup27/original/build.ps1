param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$jointOriginalRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$jointOriginalOut=[IO.Path]::GetFullPath($Output)
if([IO.Path]::GetDirectoryName($jointOriginalOut)-ne (Join-Path $jointOriginalRoot 'reports/m4-joint-startup27')){throw 'Assigned original27 report path required'}
if(Test-Path -LiteralPath $jointOriginalOut){throw 'Original27 build report must be fresh'}
New-Item -ItemType Directory -Path $jointOriginalOut|Out-Null
$jointOriginalVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$jointOriginalCMake=Join-Path $jointOriginalVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$jointOriginalExtract=Join-Path $jointOriginalRoot 'reports/m4-joint-startup27/original-extraction-r1'
$jointOriginalBuild=Join-Path $jointOriginalOut 'build-x86'
$jointOriginalSources=[ordered]@{}
function Hash-JointOriginal([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
foreach($jointOriginalFile in @((Get-ChildItem -LiteralPath $PSScriptRoot -File),(Get-ChildItem -LiteralPath $jointOriginalExtract -File))){
 foreach($jointOriginalItem in $jointOriginalFile){$jointOriginalSources[$jointOriginalItem.FullName]=Hash-JointOriginal $jointOriginalItem.FullName}
}
$jointOriginalCommands=[Collections.Generic.List[object]]::new()
function Run-JointOriginal([string[]]$Arguments,[string]$Name){
 $jointOriginalLog=Join-Path $jointOriginalOut $Name
 & $jointOriginalCMake @Arguments 2>&1|Tee-Object -FilePath $jointOriginalLog
 $jointOriginalExit=$LASTEXITCODE
 $jointOriginalCommands.Add([ordered]@{program=$jointOriginalCMake;arguments=$Arguments;exit_code=$jointOriginalExit;log=$jointOriginalLog;log_sha256=(Hash-JointOriginal $jointOriginalLog)})
 if($jointOriginalExit-ne 0){throw 'Original27 build command failed'}
}
$jointOriginalPassed=$false
try{
 Import-Module (Join-Path $jointOriginalVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
 Enter-VsDevShell -VsInstallPath $jointOriginalVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
 Run-JointOriginal @('-S',$PSScriptRoot,'-B',$jointOriginalBuild,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_ORIGINAL_INCLUDE=$jointOriginalExtract") 'configure.log'
 Run-JointOriginal @('--build',$jointOriginalBuild,'--config','Release','--verbose') 'compile.log'
 foreach($jointOriginalPair in $jointOriginalSources.GetEnumerator()){if((Hash-JointOriginal $jointOriginalPair.Key)-ne $jointOriginalPair.Value){throw 'Original27 sources changed while compiling'}}
 $jointOriginalWorker=Join-Path $jointOriginalBuild 'Release/mw34_joint_startup27_original.exe'
 Copy-Item -LiteralPath $jointOriginalWorker -Destination (Join-Path $jointOriginalOut 'original-worker.exe')
 $jointOriginalPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $jointOriginalOut 'failure.txt');throw}
finally{
 $jointOriginalBindings=[ordered]@{}
 foreach($jointOriginalPair in $jointOriginalSources.GetEnumerator()){$jointOriginalBindings[$jointOriginalPair.Key]=$jointOriginalPair.Value}
 foreach($jointOriginalFile in Get-ChildItem -LiteralPath $jointOriginalOut -Recurse -File){$jointOriginalBindings[$jointOriginalFile.FullName]=Hash-JointOriginal $jointOriginalFile.FullName}
 foreach($jointOriginalTool in @('cl.exe','ml.exe','link.exe')){if(Get-Command $jointOriginalTool -ErrorAction SilentlyContinue){$jointOriginalToolPath=(Get-Command $jointOriginalTool).Source;$jointOriginalBindings[$jointOriginalToolPath]=Hash-JointOriginal $jointOriginalToolPath}}
 $jointOriginalBindings[$jointOriginalCMake]=Hash-JointOriginal $jointOriginalCMake
 [ordered]@{passed=$jointOriginalPassed;scope='Original27 compile-only original hardware observer; no guest execution or acceptance';sources=$jointOriginalSources;commands=$jointOriginalCommands;worker=(Join-Path $jointOriginalOut 'original-worker.exe');worker_sha256=if($jointOriginalPassed){Hash-JointOriginal (Join-Path $jointOriginalOut 'original-worker.exe')}else{$null};pack=(Join-Path $jointOriginalExtract 'pages.bin');original_record_size=117684;native_Common_size=116964;sequences=48;phases=1296;pages=14;direct_primary=$true;debugger_secondary_flag='--checkpoint';guest_executed=$false;whole_M4_complete=$false}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $jointOriginalOut 'build.json')
 $jointOriginalBindings[(Join-Path $jointOriginalOut 'build.json')]=Hash-JointOriginal (Join-Path $jointOriginalOut 'build.json')
 [ordered]@{files=$jointOriginalBindings}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $jointOriginalOut 'pins.json')
}
