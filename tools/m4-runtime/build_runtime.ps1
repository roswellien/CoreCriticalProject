param(
    [string]$OutputDirectory = 'D:/Projects/MW34Recomp/reports/m4-runtime/context-r1',
    [string]$Image = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$LLVMRoot = 'D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc'
)
$ErrorActionPreference = 'Stop'
$mwRuntimeRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwRuntimeOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
$mwRuntimeReports = Join-Path $mwRuntimeRoot 'reports/m4-runtime'
if (-not $mwRuntimeOutput.StartsWith($mwRuntimeReports + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Runtime output must be a fresh private M4-runtime directory' }
$mwRuntimeName = Split-Path $mwRuntimeOutput -Leaf
if ($mwRuntimeName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwRuntimeName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$') { throw 'Invalid runtime experiment name' }
$mwRuntimeBuild = Join-Path $mwRuntimeRoot "build/m4-runtime-$mwRuntimeName"
if (Test-Path -LiteralPath $mwRuntimeOutput) { throw 'Runtime report output already exists' }
if (Test-Path -LiteralPath $mwRuntimeBuild) { throw 'Runtime derived build already exists' }
function Get-MWRuntimeHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
function Get-MWRuntimeSources {
    $mwRuntimeSources = [ordered]@{}
    $mwRuntimeCandidates = @(
        Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File
        Get-ChildItem -LiteralPath (Join-Path $mwRuntimeRoot 'tests/m4-runtime') -Recurse -File
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'docs/m4-runtime-contract.md')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'runtime/core/guest_address.hpp')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'runtime/memory/guest_memory.hpp')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'runtime/memory/guest_memory.cpp')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'tools/m4-startup/image_loader.hpp')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'tools/m4-startup/image_loader.cpp')
        Get-Item -LiteralPath (Join-Path $mwRuntimeRoot 'tools/m4-startup/admission.hpp')
    ) | Where-Object { $_.Extension -in @('.cpp','.hpp','.py','.ps1','.txt','.md') -and $_.FullName -notmatch '__pycache__' } | Sort-Object FullName
    foreach ($mwRuntimeFile in $mwRuntimeCandidates) { $mwRuntimeSources[$mwRuntimeFile.FullName] = Get-MWRuntimeHash $mwRuntimeFile.FullName }
    return $mwRuntimeSources
}
$mwRuntimePriorPins = Join-Path $mwRuntimeRoot 'reports/m4-startup/root-review/pins.json'
if ((Get-MWRuntimeHash $mwRuntimePriorPins) -ne 'af3668c716e4e9485e6ab7d4cd72de0025d13acf51619209a6bff32cfbf3482c') { throw 'Earlier M4 prerequisite map changed' }
$mwRuntimeFrozen = Get-Content -Raw -LiteralPath $mwRuntimePriorPins | ConvertFrom-Json
$mwRuntimeInitialSources = Get-MWRuntimeSources
foreach ($mwRuntimeOldSource in @('runtime/core/guest_address.hpp','runtime/memory/guest_memory.hpp','runtime/memory/guest_memory.cpp','tools/m4-startup/image_loader.hpp','tools/m4-startup/image_loader.cpp','tools/m4-startup/admission.hpp')) {
    $mwRuntimePath = [System.IO.Path]::GetFullPath((Join-Path $mwRuntimeRoot $mwRuntimeOldSource))
    if ($mwRuntimeInitialSources[$mwRuntimePath] -ne $mwRuntimeFrozen.files.$mwRuntimePath) { throw "Frozen dependency changed: $mwRuntimePath" }
}
if ((Get-MWRuntimeHash $Image) -ne '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf') { throw 'Unadmitted actual runtime image' }
$mwRuntimeProvider = Join-Path $mwRuntimeRoot 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
if ((Get-MWRuntimeHash $mwRuntimeProvider) -ne '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7') { throw 'Unadmitted continuation provider data' }
New-Item -ItemType Directory -Path $mwRuntimeOutput | Out-Null
$mwRuntimeSourceCopies = [System.Collections.Generic.List[object]]::new()
foreach ($mwRuntimeSourcePath in $mwRuntimeInitialSources.Keys) {
    $mwRuntimeRelative = [System.IO.Path]::GetRelativePath($mwRuntimeRoot, $mwRuntimeSourcePath)
    $mwRuntimePreservedPath = Join-Path (Join-Path $mwRuntimeOutput 'sources') $mwRuntimeRelative
    New-Item -ItemType Directory -Force -Path (Split-Path $mwRuntimePreservedPath) | Out-Null
    Copy-Item -LiteralPath $mwRuntimeSourcePath -Destination $mwRuntimePreservedPath
    if ((Get-MWRuntimeHash $mwRuntimePreservedPath) -ne $mwRuntimeInitialSources[$mwRuntimeSourcePath]) { throw 'Literal runtime source copy changed' }
    $mwRuntimeSourceCopies.Add([ordered]@{ original_path=$mwRuntimeSourcePath; preserved_path=$mwRuntimePreservedPath; sha256=$mwRuntimeInitialSources[$mwRuntimeSourcePath] })
}
$mwRuntimeCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWRuntimeTool([string]$Program, [string[]]$Arguments, [string]$Log) {
    $mwRuntimeSavedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log; $mwRuntimeExit = $LASTEXITCODE }
    finally { $ErrorActionPreference = $mwRuntimeSavedPreference }
    $mwRuntimeCommands.Add([ordered]@{ program=$Program; arguments=$Arguments; exit_code=$mwRuntimeExit; log_path=$Log; log_sha256=(Get-MWRuntimeHash $Log) })
    if ($mwRuntimeExit -ne 0) { throw "Runtime tool failed: $Program (exit $mwRuntimeExit)" }
}
$mwRuntimePassed = $false
try {
    Import-Module (Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
    $mwRuntimeCMake = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
    $mwRuntimeCTest = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
    $mwRuntimeNinja = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
    $env:PATH = "$LLVMRoot/bin;$(Split-Path $mwRuntimeNinja);$env:PATH"
    $mwRuntimeTemp = Join-Path $mwRuntimeOutput 'compiler-temp'; New-Item -ItemType Directory $mwRuntimeTemp | Out-Null
    $env:TEMP = $mwRuntimeTemp; $env:TMP = $mwRuntimeTemp; $env:TMPDIR = $mwRuntimeTemp
    Invoke-MWRuntimeTool $mwRuntimeCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwRuntimeBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$LLVMRoot/bin/clang-cl.exe",'-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG') (Join-Path $mwRuntimeOutput 'configure.log')
    Invoke-MWRuntimeTool $mwRuntimeCMake @('--build',$mwRuntimeBuild,'--parallel','8') (Join-Path $mwRuntimeOutput 'build.log')
    Invoke-MWRuntimeTool $mwRuntimeCTest @('--test-dir',$mwRuntimeBuild,'--verbose','--output-on-failure','--no-tests=error','--output-junit',(Join-Path $mwRuntimeOutput 'ctest.xml')) (Join-Path $mwRuntimeOutput 'ctest.log')
    $mwRuntimeHost = Join-Path $mwRuntimeBuild 'mw34_m4_runtime_host.exe'
    Invoke-MWRuntimeTool $Python @((Join-Path $mwRuntimeRoot 'tests/m4-runtime/check_runtime.py'),'--host',$mwRuntimeHost,'--image',$Image,'--out',(Join-Path $mwRuntimeOutput 'actual-controls')) (Join-Path $mwRuntimeOutput 'actual-controls.log')
    if ((Get-MWRuntimeSources | ConvertTo-Json -Compress) -ne ($mwRuntimeInitialSources | ConvertTo-Json -Compress)) { throw 'Runtime sources changed during build; preserve attempt and rebuild fresh' }
    $mwRuntimePassed = $true
} catch {
    $mwRuntimeFailure = $_.Exception.Message
    throw
} finally {
    $mwRuntimeArtifacts = [ordered]@{}
    foreach ($mwRuntimeFile in @(
        Get-ChildItem -LiteralPath $mwRuntimeOutput -Recurse -File
        if (Test-Path -LiteralPath $mwRuntimeBuild) { Get-ChildItem -LiteralPath $mwRuntimeBuild -Recurse -File | Where-Object { $_.Extension -in @('.exe','.obj','.lib','.cmake','.json') -or $_.Name -in @('build.ninja','rules.ninja','CMakeCache.txt','.ninja_log') } }
    ) | Sort-Object FullName) {
        if ($mwRuntimeFile.FullName -notmatch 'compiler-temp') { $mwRuntimeArtifacts[$mwRuntimeFile.FullName] = Get-MWRuntimeHash $mwRuntimeFile.FullName }
    }
    $mwRuntimeTools = [ordered]@{}
    foreach ($mwRuntimeTool in @($Python,$mwRuntimeCMake,$mwRuntimeCTest,$mwRuntimeNinja,(Get-Process -Id $PID).Path,(Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')) + @('clang-cl.exe','llvm-lib.exe','lld-link.exe','llvm-mt.exe' | ForEach-Object { Join-Path $LLVMRoot "bin/$_" })) {
        if ($mwRuntimeTool -and (Test-Path -LiteralPath $mwRuntimeTool)) { $mwRuntimeTools[$mwRuntimeTool] = Get-MWRuntimeHash $mwRuntimeTool }
    }
    $mwRuntimeRC = 'C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe'
    if (Test-Path -LiteralPath $mwRuntimeRC) { $mwRuntimeTools[$mwRuntimeRC] = Get-MWRuntimeHash $mwRuntimeRC }
    $mwRuntimeSDK = 'C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/winnt.h'
    [ordered]@{schema_version=1; passed=$mwRuntimePassed; failure=$mwRuntimeFailure; experiment='Native startup context/routing prerequisite'; milestone_M4_complete=$false;
        source_files=$mwRuntimeInitialSources; literal_source_copies=@($mwRuntimeSourceCopies); tool_files=$mwRuntimeTools; artifacts=$mwRuntimeArtifacts; commands=@($mwRuntimeCommands);
        image_path=$Image; image_sha256=(Get-MWRuntimeHash $Image); prior_pins_path=$mwRuntimePriorPins; prior_pins_sha256=(Get-MWRuntimeHash $mwRuntimePriorPins);
        continuation_provider_path=$mwRuntimeProvider; continuation_provider_sha256=(Get-MWRuntimeHash $mwRuntimeProvider);
        previous_runtime_preservation='reports/m4-runtime/pre-service-continuation-extension/manifest.json'; previous_runtime_durable_map='reports/m4-runtime/durable-r4-chain-r1/pins.json';
        nt_tib32_sdk_header_path=$mwRuntimeSDK; nt_tib32_sdk_header_sha256=(Get-MWRuntimeHash $mwRuntimeSDK);
        original_x86_executed=$false; game_native_translation_executed=$false; CRT_SEH_MFC_startup_complete=$false; native_menus_complete=$false
    } | ConvertTo-Json -Depth 16 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwRuntimeOutput 'build.json')
}
Write-Output "Runtime context/routing prerequisite passed; full native startup remains open. $(Join-Path $mwRuntimeOutput 'build.json')"
