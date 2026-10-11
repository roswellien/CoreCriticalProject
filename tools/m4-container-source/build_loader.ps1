param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskBase=Join-Path $taskRoot 'reports/m4-container-source'
$taskOut=[IO.Path]::GetFullPath($Output)
if([IO.Path]::GetDirectoryName($taskOut)-ne$taskBase-or(Test-Path -LiteralPath $taskOut)){throw 'Fresh assigned loader output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$taskVS='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module (Join-Path $taskVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $taskVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
& cl.exe /nologo /std:c++17 /EHsc /MT /O2 /W4 /WX /Fe:"$taskOut/probe.exe" /Fo:"$taskOut/probe.obj" "$PSScriptRoot/loader_probe.cpp" /link /SUBSYSTEM:CONSOLE 2>&1|Tee-Object -FilePath "$taskOut/compile.log"
if($LASTEXITCODE-ne0){throw 'Original32 loader compiler failed'}
& "$taskOut/probe.exe" "$taskOut/loaded-data-page.bin" 2>&1|Tee-Object -FilePath "$taskOut/loader.json"
if($LASTEXITCODE-ne0){throw 'Genuine loader observation failed'}
