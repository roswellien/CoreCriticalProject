param([string]$Config = '')
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$vs = 'C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$output = Join-Path $projectRoot 'local/controller-unit-checks'
New-Item -ItemType Directory -Force $output | Out-Null
$compiler = Join-Path $projectRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'
& $compiler /nologo /std:c++20 /EHsc (Join-Path $PSScriptRoot 'controller_math_test.cpp') "/Fe:$output/controller_math_test.exe" "/Fo:$output/controller_math_test.obj"
if ($LASTEXITCODE) { throw 'Controller unit check compilation failed' }
if ($Config) { & "$output/controller_math_test.exe" $Config } else { & "$output/controller_math_test.exe" }
if ($LASTEXITCODE) { throw 'Controller unit checks failed' }
