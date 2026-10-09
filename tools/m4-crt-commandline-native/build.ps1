param([Parameter(Mandatory=$true)][string]$OutputDirectory,[string]$ResearchDirectory='D:/Projects/MW34Recomp/reports/m4-crt-commandline-native/static-r1')
$ErrorActionPreference='Stop';if($PSVersionTable.PSVersion.Major-lt7){throw 'PowerShell7 required'}
$cmdRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$cmdOut=[IO.Path]::GetFullPath($OutputDirectory);$cmdResearch=[IO.Path]::GetFullPath($ResearchDirectory)
if([IO.Path]::GetDirectoryName($cmdOut)-ne(Join-Path $cmdRoot 'reports/m4-crt-commandline-native')){throw 'Immediate private command-line report required'}
$cmdName=Split-Path $cmdOut -Leaf;if($cmdName-notmatch '^[a-z0-9-]+$'){throw 'Simple report name required'}
$cmdBuilds=@{O0=(Join-Path $cmdRoot "build/m4-cmd-$cmdName-O0");O2=(Join-Path $cmdRoot "build/m4-cmd-$cmdName-O2")}
foreach($cmdP in @($cmdOut)+@($cmdBuilds.Values)){if(Test-Path -LiteralPath $cmdP){throw 'Fresh command-line report and build directories required before writes'}}
function Get-CmdHash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$cmdR9=Join-Path $cmdRoot 'reports/m4-runtime/context-r9/build.json';if((Get-CmdHash $cmdR9)-ne'12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5'){throw 'Frozen r9 build required'}
$cmdR=Get-Content -Raw -LiteralPath $cmdR9|ConvertFrom-Json;$cmdSources=[ordered]@{}
foreach($cmdProperty in $cmdR.source_files.PSObject.Properties){if((Get-CmdHash $cmdProperty.Name)-ne$cmdProperty.Value){throw 'Frozen r9 source changed'};$cmdSources[$cmdProperty.Name]=$cmdProperty.Value}
foreach($cmdPath in @($PSScriptRoot,$cmdResearch,(Join-Path $cmdRoot 'runtime'),(Join-Path $cmdRoot 'tools/m4-startup'))){foreach($cmdFile in Get-ChildItem -LiteralPath $cmdPath -Recurse -File){if($cmdFile.FullName-notmatch '__pycache__'){$cmdSources[$cmdFile.FullName]=Get-CmdHash $cmdFile.FullName}}}
$cmdDoc=Join-Path $cmdRoot 'docs/m4-crt-commandline-native-contract.md';$cmdSources[$cmdDoc]=Get-CmdHash $cmdDoc
$cmdLLVM=Join-Path $cmdRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$cmdVS='C:/Program Files/Microsoft Visual Studio/18/Community';$cmdCMake=Join-Path $cmdVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';$cmdCommands=[Collections.Generic.List[object]]::new();$cmdPassed=$false;$cmdTools=[ordered]@{}
New-Item -ItemType Directory -Path $cmdOut|Out-Null
foreach($cmdPair in $cmdSources.GetEnumerator()){$cmdDst=Join-Path $cmdOut ('sources/'+[IO.Path]::GetRelativePath($cmdRoot,$cmdPair.Key));New-Item -ItemType Directory -Force -Path (Split-Path $cmdDst -Parent)|Out-Null;Copy-Item -LiteralPath $cmdPair.Key -Destination $cmdDst}
function Run([string]$program,[string[]]$arguments,[string]$log){$cmdTools[$program]=Get-CmdHash $program;[IO.File]::WriteAllBytes((Join-Path $cmdOut $log),[byte[]]::new(0));&$program @arguments 2>&1|Tee-Object -FilePath (Join-Path $cmdOut $log);$cmdExit=$LASTEXITCODE;$cmdCommands.Add([ordered]@{program=$program;arguments=$arguments;exit_code=$cmdExit;log=(Join-Path $cmdOut $log);log_sha256=(Get-CmdHash (Join-Path $cmdOut $log))});if($cmdExit-ne0){throw 'Command-line component build failed'}}
try{
 Import-Module (Join-Path $cmdVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $cmdVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 Run (Join-Path $cmdLLVM 'opt.exe') @('-passes=verify','-disable-output',(Join-Path $cmdResearch 'host.ll')) 'verify.log'
 foreach($cmdLevel in @('O0','O2')){$cmdIR=Join-Path $cmdResearch 'host.ll';if($cmdLevel-eq'O2'){$cmdIR=Join-Path $cmdOut 'host-O2.ll';Run (Join-Path $cmdLLVM 'opt.exe') @('-passes=default<O2>','-S',(Join-Path $cmdResearch 'host.ll'),'-o',$cmdIR) 'opt-O2.log'};$cmdObject=Join-Path $cmdOut "writer-$cmdLevel.obj";Run (Join-Path $cmdLLVM 'llc.exe') @('-filetype=obj',"-$cmdLevel",$cmdIR,'-o',$cmdObject) "llc-$cmdLevel.log"
  $cmdFlags=if($cmdLevel-eq'O0'){'/Od /DNDEBUG'}else{'/O2 /DNDEBUG'}
  Run $cmdCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$cmdBuilds[$cmdLevel],'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$cmdLLVM/clang-cl.exe","-DCMAKE_CXX_FLAGS_RELEASE=$cmdFlags","-DMW34_CMD_INCLUDE=$cmdResearch","-DMW34_CMD_OBJECT=$cmdObject") "configure-$cmdLevel.log"
  Run $cmdCMake @('--build',$cmdBuilds[$cmdLevel],'--parallel','8','--verbose') "build-$cmdLevel.log"
 }
 foreach($cmdPair in $cmdSources.GetEnumerator()){if((Get-CmdHash $cmdPair.Key)-ne$cmdPair.Value){throw 'Command-line source changed during build'}};$cmdPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $cmdOut 'failure.txt');throw}
finally{$cmdArtifacts=[ordered]@{};foreach($cmdPath in @($cmdOut)+@($cmdBuilds.Values)){if(Test-Path -LiteralPath $cmdPath){foreach($cmdFile in Get-ChildItem -LiteralPath $cmdPath -Recurse -File){$cmdArtifacts[$cmdFile.FullName]=Get-CmdHash $cmdFile.FullName}}};[ordered]@{passed=$cmdPassed;scope='Compiled actual writer/typed native own host input/provider data registry; worker execution and original comparison pending';sources=$cmdSources;tools=$cmdTools;commands=$cmdCommands;artifacts=$cmdArtifacts;workers=@{O0=(Join-Path $cmdBuilds.O0 'commandline_preflight.exe');O2=(Join-Path $cmdBuilds.O2 'commandline_preflight.exe')};runtime_r9_build=$cmdR9;runtime_r9_sha256=(Get-CmdHash $cmdR9)}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $cmdOut 'build.json')}
