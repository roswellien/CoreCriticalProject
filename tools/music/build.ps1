param([string]$Output='local/music-integration-r1/bin')
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
$destination=Join-Path $root $Output
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$compiler=Join-Path $root 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'
& $compiler /nologo /std:c++20 /O2 /EHsc "$PSScriptRoot/decode_music.cpp" "/Fo$destination/decode_music.obj" "/Fe$destination/decode_music.exe" /link mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib
if($LASTEXITCODE){throw 'Music preparation tool build failed'}
