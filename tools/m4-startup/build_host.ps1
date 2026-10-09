param(
    [string]$Image = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [string]$OutputDirectory = 'D:/Projects/MW34Recomp/reports/m4-startup/foundation-r1',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$LLVMRoot = 'D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc'
)
$ErrorActionPreference = 'Stop'
$mwRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
$mwReports = [System.IO.Path]::GetFullPath((Join-Path $mwRoot 'reports/m4-startup'))
if (-not $mwOutput.StartsWith($mwReports + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'M4 output must be a new directory under reports/m4-startup'
}
if (Test-Path -LiteralPath $mwOutput) { throw 'Refusing to overwrite M4 evidence' }
$mwName = Split-Path $mwOutput -Leaf
if ($mwName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$') { throw 'Invalid M4 experiment name' }
$mwBuild = Join-Path $mwRoot "build/m4-startup-$mwName"
if (Test-Path -LiteralPath $mwBuild) { throw 'Refusing to overwrite M4 build' }
function Get-MWHash([string]$Path) {
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}
function Get-MWSources {
    $mwSources = [ordered]@{}
    $mwCandidates = @(
        Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File
        Get-ChildItem -LiteralPath (Join-Path $mwRoot 'tests/m4-startup') -Recurse -File
        Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/core/guest_address.hpp')
        Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/memory/guest_memory.hpp')
        Get-Item -LiteralPath (Join-Path $mwRoot 'runtime/memory/guest_memory.cpp')
        Get-Item -LiteralPath (Join-Path $mwRoot 'tools/analysis/pe.py')
    ) | Where-Object { $_.Extension -in @('.cpp','.hpp','.py','.ps1','.txt') -and $_.FullName -notmatch '__pycache__' } | Sort-Object FullName
    foreach ($mwFile in $mwCandidates) { $mwSources[$mwFile.FullName] = Get-MWHash $mwFile.FullName }
    return $mwSources
}
$mwInitialSources = Get-MWSources
if ((Get-MWHash $Image) -ne '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf') { throw 'Unadmitted M4 image' }
$mwPriorPins = Join-Path $mwRoot 'reports/m3-acceptance/final-pins.json'
if ((Get-MWHash $mwPriorPins) -ne 'bfd3dd2014fc6d6a6de2f8981064c506863651db8cf134b6f878de6dd1e7ec01') { throw 'Changed M3 final binding' }
$mwPriorAcceptance = Join-Path $mwRoot 'reports/m3-acceptance/root-review/report.json'
if ((Get-MWHash $mwPriorAcceptance) -ne 'c4e6880be032d3dbf953d181fdea4a379cfbc5fa8f33eb2612e08d5df64657ef') { throw 'Changed M3 acceptance' }
New-Item -ItemType Directory $mwOutput | Out-Null
$mwTemp = Join-Path $mwOutput 'compiler-temp'
New-Item -ItemType Directory $mwTemp | Out-Null
$env:TEMP = $mwTemp; $env:TMP = $mwTemp; $env:TMPDIR = $mwTemp
$mwCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWTool([string]$Program, [string[]]$Arguments, [string]$Log) {
    & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log
    $mwExit = $LASTEXITCODE
    $mwCommands.Add([ordered]@{ program=$Program; arguments=$Arguments; exit_code=$mwExit; log_path=$Log; log_sha256=(Get-MWHash $Log) })
    if ($mwExit -ne 0) { throw "M4 tool failed: $Program (exit $mwExit)" }
}
Import-Module (Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$mwCMake = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
$mwCTest = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
$mwNinja = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
$env:PATH = "$LLVMRoot/bin;$(Split-Path $mwNinja);$env:PATH"
Invoke-MWTool $mwCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$LLVMRoot/bin/clang-cl.exe",'-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG') (Join-Path $mwOutput 'configure.log')
Invoke-MWTool $mwCMake @('--build',$mwBuild,'--parallel','8') (Join-Path $mwOutput 'build.log')
Invoke-MWTool $mwCTest @('--test-dir',$mwBuild,'--output-on-failure','--no-tests=error','--output-junit',(Join-Path $mwOutput 'ctest.xml')) (Join-Path $mwOutput 'ctest.log')
$mwHost = Join-Path $mwBuild 'mw34_m4_startup_host.exe'
Invoke-MWTool $Python @((Join-Path $mwRoot 'tests/m4-startup/check_host.py'),'--host',$mwHost,'--out',(Join-Path $mwOutput 'public-controls')) (Join-Path $mwOutput 'public-controls.log')
Invoke-MWTool $Python @((Join-Path $PSScriptRoot 'verify_host.py'),'--host',$mwHost,'--windows-probe',(Join-Path $mwBuild 'mw34_m4_windows_image_probe.exe'),'--image',$Image,'--out',(Join-Path $mwOutput 'actual-image')) (Join-Path $mwOutput 'actual-image.log')
$mwFinalSources = Get-MWSources
if (($mwInitialSources | ConvertTo-Json -Compress) -ne ($mwFinalSources | ConvertTo-Json -Compress)) { throw 'M4 source snapshot changed; preserve this build and run fresh' }
$mwTools = [ordered]@{}
foreach ($mwTool in @($Python,$mwCMake,$mwCTest,$mwNinja,(Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'))) { $mwTools[$mwTool] = Get-MWHash $mwTool }
foreach ($mwToolName in @('clang-cl.exe','llvm-lib.exe','lld-link.exe','llvm-mt.exe')) {
    $mwTool = Join-Path $LLVMRoot "bin/$mwToolName"; $mwTools[$mwTool] = Get-MWHash $mwTool
}
$mwArtifacts = [ordered]@{}
foreach ($mwFile in @(
    Get-ChildItem -LiteralPath $mwOutput -Recurse -File
    Get-ChildItem -LiteralPath $mwBuild -Recurse -File | Where-Object { $_.Extension -in @('.exe','.obj','.lib','.cmake') -or $_.Name -in @('build.ninja','CMakeCache.txt','.ninja_log') }
) | Sort-Object FullName) {
    if ($mwFile.FullName -notmatch 'compiler-temp') { $mwArtifacts[$mwFile.FullName] = Get-MWHash $mwFile.FullName }
}
$mwActual = Get-Content -Raw -LiteralPath (Join-Path $mwOutput 'actual-image/report.json') | ConvertFrom-Json
$mwPublic = Get-Content -Raw -LiteralPath (Join-Path $mwOutput 'public-controls/report.json') | ConvertFrom-Json
if ($mwActual.passed -ne $true -or $mwPublic.passed -ne $true -or $mwActual.native_game_startup_or_menus_proven -ne $false) { throw 'M4 foundation result/status differs' }
[ordered]@{
    schema_version=1; passed=$true; experiment='M4 native image mapping foundation'; milestone_M4_complete=$false
    image_path=[System.IO.Path]::GetFullPath($Image); image_sha256=(Get-MWHash $Image)
    host_path=$mwHost; host_sha256=(Get-MWHash $mwHost); source_files=$mwFinalSources; tool_files=$mwTools; artifacts=$mwArtifacts
    commands=@($mwCommands); actual_image_report=(Join-Path $mwOutput 'actual-image/report.json'); public_controls_report=(Join-Path $mwOutput 'public-controls/report.json')
    m3_final_pins_path=$mwPriorPins; m3_final_pins_sha256=(Get-MWHash $mwPriorPins); m3_acceptance_path=$mwPriorAcceptance; m3_acceptance_sha256=(Get-MWHash $mwPriorAcceptance)
    original_x86_executed=$false; import_resolution_performed=$false
    scope='Checked fixed-base PE32 mapping into native x64 GuestMemory, full mapped-byte comparison and unresolved startup denial; no native menus/gameplay claim'
} | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwOutput 'build.json')
Write-Output "M4 image foundation passed; native startup remains unresolved. Build record: $(Join-Path $mwOutput 'build.json')"
