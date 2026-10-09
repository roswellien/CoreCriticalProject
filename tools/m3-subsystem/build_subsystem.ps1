param(
    [string]$LLVMRoot,
    [string]$RemillRoot,
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$Image,
    [Parameter(Mandatory = $true)][string]$FirstGatePins,
    [string]$OutputDirectory,
    [switch]$RunComparison
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\', '/')
if (-not $LLVMRoot) { $LLVMRoot = "$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc" }
if (-not $RemillRoot) { $RemillRoot = "$mwRoot/local/tools/remill-v6.0.1/remill-6.0.1" }
if (-not $Image) { $Image = "$mwRoot/MW3/Mech3.exe" }
if (-not $OutputDirectory) { $OutputDirectory = "$mwRoot/reports/m3-subsystem/connected-component" }
$LLVMRoot = (Resolve-Path -LiteralPath $LLVMRoot).Path.Replace('\', '/')
$RemillRoot = (Resolve-Path -LiteralPath $RemillRoot).Path.Replace('\', '/')
$Image = (Resolve-Path -LiteralPath $Image).Path.Replace('\', '/')
$FirstGatePins = (Resolve-Path -LiteralPath $FirstGatePins).Path.Replace('\', '/')
$mwOutput = [System.IO.Path]::GetFullPath($OutputDirectory).Replace('\', '/')
if (-not $mwOutput.StartsWith("$mwRoot/reports/m3-subsystem/", [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Private output must stay within ignored connected M3 reports' }
if (Test-Path -LiteralPath $mwOutput) { throw 'Refusing to replace any earlier connected M3 experiment; use a fresh OutputDirectory' }
$mwCMake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$mwCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWTool([string]$Program, [string[]]$Arguments, [string]$Log = '', [bool]$Quiet = $false) {
    $mwCommands.Add(@($Program) + $Arguments)
    $mwSavedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        if ($Log) {
            if ($Quiet) { & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log | Out-Null }
            else { & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log }
        } else { & $Program @Arguments }
    } finally { $ErrorActionPreference = $mwSavedPreference }
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
$mwPriorRecord = Get-Content -Raw -LiteralPath $FirstGatePins | ConvertFrom-Json
if ($mwPriorRecord.previous_gate_pins) { $mwPriorRecord = $mwPriorRecord.previous_gate_pins }
$mwPreviousPins = [ordered]@{}
foreach ($mwLabel in @('first_build', 'first_comparison_report', 'first_initial_failure_report', 'first_initial_failure_manifest', 'm2_final_pins', 'm2_independent_pins', 'first_independent_review')) {
    $mwPin = $mwPriorRecord.$mwLabel
    if (-not $mwPin -or -not [System.IO.Path]::IsPathRooted($mwPin.path) -or $mwPin.sha256 -notmatch '^[0-9a-f]{64}$') { throw "Missing precise prior gate pin: $mwLabel" }
    if ((Get-MWHash $mwPin.path) -ne $mwPin.sha256) { throw "Frozen previous gate changed: $mwLabel" }
    $mwPreviousPins[$mwLabel] = [ordered]@{ path = $mwPin.path; sha256 = $mwPin.sha256 }
}
$mwFirstReport = Get-Content -Raw -LiteralPath $mwPreviousPins.first_comparison_report.path | ConvertFrom-Json
if ($mwFirstReport.passed -ne $true -or $mwFirstReport.original_cases -ne 15780 -or $mwFirstReport.native_comparisons -ne 31560 -or
    $mwFirstReport.build_sha256 -ne $mwPreviousPins.first_build.sha256) { throw 'First actual whole-function comparison is not accepted and bound' }
$mwFirstBuild = Get-Content -Raw -LiteralPath $mwPreviousPins.first_build.path | ConvertFrom-Json
if ($mwFirstBuild.profile -ne 'm3-whole-function-558290' -or $mwFirstBuild.image_sha256 -ne '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf') { throw 'Prior accepted function/image identity differs' }
foreach ($mwSource in $mwFirstBuild.source_files.PSObject.Properties) {
    if ((Get-MWHash $mwSource.Name) -ne $mwSource.Value) { throw "Frozen first source changed: $($mwSource.Name)" }
}
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw -LiteralPath $mwRepairPath | ConvertFrom-Json
if ($mwRepair.remill_lifter_sha256 -ne 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38' -or
    $mwRepair.repaired_semantics_sha256 -ne '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca') { throw 'Unreviewed Remill/semantics binding' }
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Frozen toolchain changed: $($mwBinding[0])" }
}
if ((Get-MWHash "$LLVMRoot/bin/LLVM-C.dll") -ne '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb') { throw 'Unreviewed LLVM DLL' }
Invoke-MWTool $Python @("$PSScriptRoot/check_prior_gate.py", '--pins', $FirstGatePins)
$mwInitialIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Initial connected source identity failed' }
New-Item -ItemType Directory $mwOutput | Out-Null
Invoke-MWTool $Python @("$mwRoot/tests/m3-subsystem/check_prior_gate.py", '--out', "$mwOutput/prior-admission-controls") "$mwOutput/prior-admission-controls.log"
Invoke-MWTool $Python @("$PSScriptRoot/extract_image.py", '--image', $Image, '--output', $mwOutput, '--objdump', "$LLVMRoot/bin/llvm-objdump.exe") "$mwOutput/extraction.log"
$mwCodes = [ordered]@{ setter = "$mwOutput/setter.bin"; consumer = "$mwOutput/consumer.bin" }
$mwLayouts = [ordered]@{}
foreach ($mwKind in @('setter', 'consumer')) {
    $mwHex = & $Python -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_bytes().hex())' $mwCodes[$mwKind]
    if ($LASTEXITCODE -ne 0) { throw 'Private complete function read failed' }
    $mwAddress = if ($mwKind -eq 'setter') { '5603984' } else { '5612896' }
    Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', "--address=$mwAddress", "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwOutput/$mwKind-guest.ll") "$mwOutput/$mwKind-lifter.log"
    Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/$mwKind-guest.ll", '-o', "$mwOutput/$mwKind-guest.bc")
    $mwLayouts[$mwKind] = "$mwOutput/$mwKind-layout.json"
    Invoke-MWTool $Python @("$PSScriptRoot/adapt_subsystem.py", '--kind', $mwKind, '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/$mwKind-guest.ll", '--host', "$mwOutput/$mwKind-host.ll", '--record', $mwLayouts[$mwKind], '--extraction', "$mwOutput/extraction.json") "$mwOutput/$mwKind-adapter.log"
    Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=verify', '-disable-output', "$mwOutput/$mwKind-host.ll")
    Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/$mwKind-host.ll", '-o', "$mwOutput/$mwKind-host-O2.ll")
    Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/$mwKind-host.ll", '-o', "$mwOutput/$mwKind-O0.obj")
    Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/$mwKind-host-O2.ll", '-o', "$mwOutput/$mwKind-O2.obj")
}
Invoke-MWTool $Python @("$PSScriptRoot/check_adapter.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--directory', $mwOutput, '--record', "$mwOutput/adapter-controls.json") "$mwOutput/adapter-controls.log"
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
# All compiler scratch writes stay within the workspace's explicitly writable root.
$mwTemp = "$mwOutput/compiler-temp"
New-Item -ItemType Directory $mwTemp | Out-Null
$env:TEMP = $mwTemp; $env:TMP = $mwTemp; $env:TMPDIR = $mwTemp
$mwBuildName = Split-Path $mwOutput -Leaf
$mwReferenceBuild = "$mwRoot/build/m3-subsystem-$mwBuildName-reference"
$mwBuildDirectories = [ordered]@{ reference = $mwReferenceBuild }
$mwWorkers = [ordered]@{ original = "$mwReferenceBuild/Release/mw34_m3_subsystem_reference.exe" }
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32') "$mwOutput/reference-configure.log"
Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release') "$mwOutput/reference-build.log"
Invoke-MWTool $mwWorkers.original @('--check-protocol') "$mwOutput/original-protocol.log"
Invoke-MWTool $Python @("$mwRoot/tests/m3-subsystem/check_public_worker.py", '--worker', $mwWorkers.original) "$mwOutput/original-public-controls.log"
foreach ($mwLevel in @('O0', 'O2')) {
    foreach ($mwKind in @('setter', 'consumer')) {
        Invoke-MWTool "$LLVMRoot/bin/llvm-nm.exe" @('--undefined-only', "$mwOutput/$mwKind-$mwLevel.obj") "$mwOutput/$mwKind-$mwLevel-symbols.txt"
        $mwSymbols = (Get-Content -LiteralPath "$mwOutput/$mwKind-$mwLevel-symbols.txt") | ForEach-Object {
            if ($_ -match '^\s*U\s+(\S+)\s*$') { $matches[1] } elseif ($_ -match '\S') { throw "Unexpected object symbol output: $_" }
        }
        $mwExpected = if ($mwKind -eq 'setter') { '__remill_function_return,__remill_read_memory_32,__remill_write_memory_32' } else { '__remill_function_return,__remill_read_memory_16,__remill_read_memory_32,__remill_write_memory_16,__remill_write_memory_32' }
        if ((($mwSymbols | Sort-Object) -join ',') -ne $mwExpected) { throw 'Native object has unreviewed imported symbols' }
        Invoke-MWTool "$LLVMRoot/bin/llvm-objdump.exe" @('--disassemble', '--x86-asm-syntax=intel', "$mwOutput/$mwKind-$mwLevel.obj") "$mwOutput/$mwKind-$mwLevel-disassembly.txt" $true
    }
    $mwBuild = "$mwRoot/build/m3-subsystem-$mwBuildName-$mwLevel"
    $mwBuildDirectories[$mwLevel] = $mwBuild
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_SETTER_OBJECT=$mwOutput/setter-$mwLevel.obj", "-DMW34_CONSUMER_OBJECT=$mwOutput/consumer-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG -Wno-invalid-offsetof') "$mwOutput/native-$mwLevel-configure.log"
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8') "$mwOutput/native-$mwLevel-build.log"
    $mwWorkers["native-$mwLevel"] = "$mwBuild/mw34_m3_subsystem_native.exe"
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--check-protocol') "$mwOutput/native-$mwLevel-protocol.log"
    Invoke-MWTool $Python @("$mwRoot/tests/m3-subsystem/check_public_worker.py", '--worker', $mwWorkers["native-$mwLevel"], '--native') "$mwOutput/native-$mwLevel-public-controls.log"
    foreach ($mwCheck in @('context', 'state-storage', 'fp-environment')) {
        Invoke-MWTool $mwWorkers["native-$mwLevel"] @("--check-$mwCheck", $mwCodes.setter, $mwCodes.consumer, $Image) "$mwOutput/native-$mwLevel-$mwCheck.log"
    }
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--layout') "$mwOutput/native-$mwLevel-layout.log"
}
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $mwIdentity.source_digest -ne $mwInitialIdentity.source_digest) { throw 'Source snapshot changed during compilation; preserve this experiment and build fresh' }
$mwTools = [ordered]@{}
foreach ($mwTool in @('llvm-objdump.exe', 'llvm-nm.exe', 'llvm-as.exe', 'opt.exe', 'llc.exe', 'clang-cl.exe', 'LLVM-C.dll')) {
    $mwToolPath = "$LLVMRoot/bin/$mwTool"; $mwTools[$mwToolPath] = Get-MWHash $mwToolPath
}
foreach ($mwToolPath in @($Python, $mwCMake, $mwRepair.remill_lifter_path, $mwRepair.repaired_semantics_path, $mwRepairPath, $FirstGatePins)) { $mwTools[$mwToolPath] = Get-MWHash $mwToolPath }
foreach ($mwDriver in @("$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll", "$VSRoot/MSBuild/Current/Bin/MSBuild.exe", "$VSRoot/MSBuild/Current/Bin/amd64/MSBuild.exe")) { $mwTools[$mwDriver] = Get-MWHash $mwDriver }
foreach ($mwBuildLabel in $mwBuildDirectories.Keys) {
    $mwBuildDirectory = $mwBuildDirectories[$mwBuildLabel]
    $mwCache = "$mwBuildDirectory/CMakeCache.txt"
    Copy-Item -LiteralPath $mwCache -Destination "$mwOutput/$mwBuildLabel-CMakeCache.txt"
    $mwCompilerRecords = @(Get-ChildItem -LiteralPath "$mwBuildDirectory/CMakeFiles" -Recurse -File -Filter 'CMake*Compiler.cmake')
    $mwSelectedTools = [ordered]@{}
    foreach ($mwLine in Get-Content -LiteralPath $mwCache) {
        if ($mwLine -match '^CMAKE_(CXX_COMPILER|ASM_MASM_COMPILER|AR|LINKER|MT|RC_COMPILER|MAKE_PROGRAM):(?:FILEPATH|STRING)=(.+)$') {
            $mwToolPath = $matches[2]
            if (-not [System.IO.Path]::IsPathRooted($mwToolPath)) { throw 'Build tool path must be absolute' }
            $mwSelectedTools[$mwToolPath] = Get-MWHash $mwToolPath
        }
    }
    foreach ($mwCompilerRecord in $mwCompilerRecords) {
        Copy-Item -LiteralPath $mwCompilerRecord.FullName -Destination "$mwOutput/$mwBuildLabel-$($mwCompilerRecord.Name)"
        foreach ($mwLine in Get-Content -LiteralPath $mwCompilerRecord.FullName) {
            if ($mwLine -match '^set\(CMAKE_(CXX_COMPILER|ASM_MASM_COMPILER) "([^"]+)"\)') {
                $mwToolPath = $matches[2]
                if (-not [System.IO.Path]::IsPathRooted($mwToolPath)) { throw 'Compiled tool path must be absolute' }
                $mwSelectedTools[$mwToolPath] = Get-MWHash $mwToolPath
            }
        }
    }
    if (-not ($mwSelectedTools.Keys | Where-Object { $_ -match '/(cl|clang-cl)\.exe$' })) { throw 'Actual build compiler identity missing' }
    foreach ($mwToolPath in $mwSelectedTools.Keys) { $mwTools[$mwToolPath] = $mwSelectedTools[$mwToolPath] }
    $mwSelectedTools | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 "$mwOutput/$mwBuildLabel-selected-tools.json"
}
$mwHashes = [ordered]@{}
foreach ($mwArtifact in Get-ChildItem -LiteralPath $mwOutput -Recurse -File) {
    $mwRelative = $mwArtifact.FullName.Replace('\', '/').Substring($mwOutput.Length + 1)
    if ($mwRelative.StartsWith('compiler-temp/')) { continue }
    if ($mwArtifact.Length -eq 0 -and $mwArtifact.Extension -ne '.log') { throw "Empty artifact: $($mwArtifact.Name)" }
    $mwHashes[$mwRelative] = Get-MWHash $mwArtifact.FullName
}
foreach ($mwWorker in $mwWorkers.Values) { $mwHashes[$mwWorker] = Get-MWHash $mwWorker }
$mwRecord = [ordered]@{
    schema_version = 1; profile = 'm3-connected-buffer-component'; scope = 'Actual complete setter and consumer offline operation sequences; no gameplay call-chain claim'
    image_path = $Image; image_sha256 = Get-MWHash $Image; codes = $mwCodes; layouts = $mwLayouts
    source_digest = $mwIdentity.source_digest; source_files = $mwIdentity.absolute_source_files; source_relative_files = $mwIdentity.source_files
    tool_files = $mwTools; artifacts = $mwHashes; workers = $mwWorkers; previous_gate_pins = $mwPreviousPins
    first_gate_pins_path = $FirstGatePins; first_gate_pins_sha256 = Get-MWHash $FirstGatePins
    remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'); optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    fast_math = $false; static_native_translation = $true; semantic_repairs = @(); commands = $mwCommands.ToArray()
}
$mwRecord | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) { Invoke-MWTool $Python @("$PSScriptRoot/compare.py", '--build', "$mwOutput/build.json", '--out', "$mwOutput/comparison") }
