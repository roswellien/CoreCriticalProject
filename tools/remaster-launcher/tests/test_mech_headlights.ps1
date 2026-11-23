param(
    [Parameter(Mandatory=$true)][string]$LLVMDirectory,
    [Parameter(Mandatory=$true)][string]$VulkanInclude,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string[]]$Checks = @()
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$output = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force $output | Out-Null
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$installation = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$installation) { throw 'Install Visual Studio C++ tools' }
$vcvars = Join-Path $installation 'VC/Auxiliary/Build/vcvars64.bat'
$environmentLines = & $env:ComSpec /d /s /c "`"$vcvars`" >nul && set"
if ($LASTEXITCODE) { throw 'Could not initialize C++ tools' }
foreach ($line in $environmentLines) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
}
$compiler = Join-Path $LLVMDirectory 'clang-cl.exe'
$hostSource = Join-Path $projectRoot 'tools/m4-crt-heap-carry/host'
$sources = @('tests/mech_headlights_checks.cpp', 'tests/additional_chassis_checks.cpp',
    'tests/chassis_sockets_checks.cpp', 'tests/controller_math_test.cpp',
    'test_photo_replay.cpp', 'test_campaign_lighting.cpp', 'test_vehicle_lighting.cpp', 'test_effect_lighting.cpp')
if ($Checks.Count) {
    $known = $sources | ForEach-Object { [IO.Path]::GetFileNameWithoutExtension($_) }
    foreach ($check in $Checks) { if ($check -notin $known) { throw "Unknown check: $check" } }
    $sources = $sources | Where-Object { [IO.Path]::GetFileNameWithoutExtension($_) -in $Checks }
}
$previousPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    foreach ($source in $sources) {
        $name = [IO.Path]::GetFileNameWithoutExtension($source)
        $inputPath = Join-Path $projectRoot "tools/remaster-launcher/$source"
        & $compiler /nologo /std:c++20 /O2 /EHsc /showIncludes "/I$hostSource" "/I$VulkanInclude" $inputPath "/Fe:$output/$name.exe" "/Fo:$output/$name.obj" /link user32.lib dxgi.lib d3d11.lib *> "$output/$name-build.txt"
        if ($LASTEXITCODE) { Get-Content "$output/$name-build.txt" -Tail 30; throw "Compile failed: $name" }
        & "$output/$name.exe" *> "$output/$name-run.txt"
        if ($LASTEXITCODE) { Get-Content "$output/$name-run.txt"; throw "Check failed: $name" }
        Write-Output "$name passed"
        if ($name -eq 'test_campaign_lighting') {
            & "$output/$name.exe" manual *> "$output/$name-manual.txt"
            if ($LASTEXITCODE) { throw 'Manual campaign check failed' }
        }
    }
} finally {
    $ErrorActionPreference = $previousPreference
}
