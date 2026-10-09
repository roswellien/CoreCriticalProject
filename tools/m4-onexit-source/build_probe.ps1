$ErrorActionPreference='Stop'
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
$taskOut='D:/Projects/MW34Recomp/reports/m4-onexit-source/loader-probe-r1'
if(Test-Path -LiteralPath $taskOut){throw 'Fresh loader probe output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
& cl.exe /nologo /EHsc /O2 /W4 /Fe:"$taskOut/probe.exe" /Fo:"$taskOut/probe.obj" "$PSScriptRoot/loader_probe.cpp" /link /SUBSYSTEM:CONSOLE 2>&1 | Tee-Object -FilePath "$taskOut/compile.log"
if($LASTEXITCODE-ne0){throw 'Probe compiler failed'}
& "$taskOut/probe.exe" 2>&1|Tee-Object -FilePath "$taskOut/run.log"
if($LASTEXITCODE-ne0){throw 'Probe actual loader failed'}
