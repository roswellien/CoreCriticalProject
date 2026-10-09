param(
    [string]$LLVMRoot,
    [string]$RemillRoot,
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$Image,
    [string]$OutputDirectory,
    [switch]$RunComparison
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\', '/')
if (-not $LLVMRoot) { $LLVMRoot = "$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc" }
if (-not $RemillRoot) { $RemillRoot = "$mwRoot/local/tools/remill-v6.0.1/remill-6.0.1" }
if (-not $Image) { $Image = "$mwRoot/MW3/Mech3.exe" }
if (-not $OutputDirectory) { $OutputDirectory = "$mwRoot/reports/m3-slice/whole-function" }
$LLVMRoot = (Resolve-Path $LLVMRoot).Path.Replace('\', '/')
$RemillRoot = (Resolve-Path $RemillRoot).Path.Replace('\', '/')
$Image = (Resolve-Path -LiteralPath $Image).Path.Replace('\', '/')
$mwOutput = [System.IO.Path]::GetFullPath($OutputDirectory).Replace('\', '/')
if (-not $mwOutput.StartsWith("$mwRoot/reports/m3-slice/", [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Private output must stay within ignored M3 reports' }
if (Test-Path -LiteralPath "$mwOutput/build.json") { throw 'Refusing to replace an earlier M3 build record; use a fresh OutputDirectory' }
$mwCMake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$mwCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWTool([string]$Program, [string[]]$Arguments, [string]$Log = '') {
    $mwCommands.Add(@($Program) + $Arguments)
    if ($Log) {
        # Windows PowerShell wraps native stderr as an ErrorRecord. LLVM and
        # the bundled Python emit harmless diagnostics there, so judge native
        # success by its exit status while retaining both streams in the log.
        $mwSavedPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try { & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log }
        finally { $ErrorActionPreference = $mwSavedPreference }
    } else {
        & $Program @Arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
$mwInitialIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Initial M3 source identity failed' }
New-Item -ItemType Directory -Force $mwOutput | Out-Null
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw -LiteralPath $mwRepairPath | ConvertFrom-Json
if ($mwRepair.remill_lifter_sha256 -ne 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38' -or
    $mwRepair.repaired_semantics_sha256 -ne '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca') { throw 'Unreviewed Remill/semantics binding' }
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Frozen toolchain provenance changed: $($mwBinding[0])" }
}
if ((Get-MWHash "$LLVMRoot/bin/LLVM-C.dll") -ne '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb') { throw 'Unreviewed LLVM DLL' }
$mwPreviousPins = [ordered]@{
    "$mwRoot/reports/x87-state/independent-review/final-pins.json" = '3d93c36c3bb3d4c7839555fa2171b250a4fa1a849d9e51178ff402fefd1dd78d'
    "$mwRoot/reports/x87-state/baseline-failure/report.json" = '7b0c935743991ecef15174d7c3d343852a772d63e0fc6d52a2cecf3198c88f11'
    "$mwRoot/reports/m2-fp-policy/final-pins.json" = '1e85288d1b97d400f91400482bea22f3d3a3790acca0326e875ca65b0673f7c1'
}
foreach ($mwPin in $mwPreviousPins.Keys) {
    if ((Get-MWHash $mwPin) -ne $mwPreviousPins[$mwPin]) { throw "Frozen previous gate changed: $mwPin" }
}
Invoke-MWTool $Python @("$PSScriptRoot/extract_image.py", '--image', $Image, '--output', $mwOutput, '--objdump', "$LLVMRoot/bin/llvm-objdump.exe") "$mwOutput/extraction.log"
$mwCode = "$mwOutput/sub_00558290.bin"
$mwHex = & $Python -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_bytes().hex())' $mwCode
if ($LASTEXITCODE -ne 0) { throw 'Private slice read failed' }
Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', '--address=5603984', "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwOutput/guest.ll") "$mwOutput/lifter.log"
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/guest.ll", '-o', "$mwOutput/guest.bc")
Invoke-MWTool $Python @("$PSScriptRoot/adapt_slice.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/layout.json", '--slice-record', "$mwOutput/slice.json") "$mwOutput/adapter.log"
Invoke-MWTool $Python @("$PSScriptRoot/check_admission.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/adapter-controls.json", '--slice-record', "$mwOutput/slice.json") "$mwOutput/adapter-controls.log"
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=verify', '-disable-output', "$mwOutput/host.ll")
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/host.ll", '-o', "$mwOutput/host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/host.ll", '-o', "$mwOutput/native-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/host-O2.ll", '-o', "$mwOutput/native-O2.obj")
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
$mwTemp = "$mwOutput/compiler-temp"
New-Item -ItemType Directory -Force $mwTemp | Out-Null
$env:TEMP = $mwTemp; $env:TMP = $mwTemp; $env:TMPDIR = $mwTemp
$mwBuildName = Split-Path $mwOutput -Leaf
$mwReferenceBuild = "$mwRoot/build/m3-slice-$mwBuildName-reference"
$mwBuildDirectories = [ordered]@{ reference = $mwReferenceBuild }
$mwWorkers = [ordered]@{ original = "$mwReferenceBuild/Release/mw34_m3_reference.exe" }
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32') "$mwOutput/reference-configure.log"
Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release') "$mwOutput/reference-build.log"
Invoke-MWTool $mwWorkers.original @('--check-protocol') "$mwOutput/original-protocol.log"
Invoke-MWTool $Python @("$mwRoot/tests/m3-slice/check_public_worker.py", '--worker', $mwWorkers.original) "$mwOutput/original-public-controls.log"
foreach ($mwLevel in @('O0', 'O2')) {
    Invoke-MWTool "$LLVMRoot/bin/llvm-nm.exe" @('--undefined-only', "$mwOutput/native-$mwLevel.obj") "$mwOutput/native-$mwLevel-symbols.txt"
    $mwSymbols = (Get-Content -LiteralPath "$mwOutput/native-$mwLevel-symbols.txt") | ForEach-Object {
        if ($_ -match '^\s*U\s+(\S+)\s*$') { $matches[1] } elseif ($_ -match '\S') { throw "Unexpected object symbol output: $_" }
    }
    if ((($mwSymbols | Sort-Object) -join ',') -ne '__remill_function_return,__remill_read_memory_32,__remill_write_memory_32') { throw 'Native object has unreviewed imported helper/symbols' }
    $mwBuild = "$mwRoot/build/m3-slice-$mwBuildName-$mwLevel"
    $mwBuildDirectories[$mwLevel] = $mwBuild
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_HOST_OBJECT=$mwOutput/native-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG -Wno-invalid-offsetof') "$mwOutput/native-$mwLevel-configure.log"
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8') "$mwOutput/native-$mwLevel-build.log"
    $mwWorkers["native-$mwLevel"] = "$mwBuild/mw34_m3_native.exe"
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--check-protocol') "$mwOutput/native-$mwLevel-protocol.log"
    Invoke-MWTool $Python @("$mwRoot/tests/m3-slice/check_public_worker.py", '--worker', $mwWorkers["native-$mwLevel"], '--native') "$mwOutput/native-$mwLevel-public-controls.log"
    foreach ($mwCheck in @('context', 'state-storage', 'fp-environment')) {
        Invoke-MWTool $mwWorkers["native-$mwLevel"] @("--check-$mwCheck", $mwCode, $Image) "$mwOutput/native-$mwLevel-$mwCheck.log"
    }
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--layout') "$mwOutput/native-$mwLevel-layout.log"
    Invoke-MWTool "$LLVMRoot/bin/llvm-objdump.exe" @('--disassemble', '--x86-asm-syntax=intel', "$mwOutput/native-$mwLevel.obj") "$mwOutput/native-$mwLevel-disassembly.txt"
}
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $mwIdentity.source_digest -ne $mwInitialIdentity.source_digest) { throw 'M3 source snapshot changed during compilation; preserve this run and rebuild fresh' }
$mwSources = $mwIdentity.absolute_source_files
$mwTools = [ordered]@{}
foreach ($mwTool in @('llvm-objdump.exe', 'llvm-nm.exe', 'llvm-as.exe', 'opt.exe', 'llc.exe', 'clang-cl.exe', 'LLVM-C.dll')) {
    $mwToolPath = "$LLVMRoot/bin/$mwTool"; $mwTools[$mwToolPath] = Get-MWHash $mwToolPath
}
foreach ($mwToolPath in @($Python, $mwCMake, $mwRepair.remill_lifter_path, $mwRepair.repaired_semantics_path, $mwRepairPath)) { $mwTools[$mwToolPath] = Get-MWHash $mwToolPath }
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
foreach ($mwArtifact in Get-ChildItem -LiteralPath $mwOutput -File) {
    if ($mwArtifact.Length -eq 0 -and $mwArtifact.Extension -ne '.log') { throw "Empty artifact: $($mwArtifact.Name)" }
    $mwHashes[$mwArtifact.Name] = Get-MWHash $mwArtifact.FullName
}
foreach ($mwWorker in $mwWorkers.Values) { $mwHashes[$mwWorker] = Get-MWHash $mwWorker }
$mwRecord = [ordered]@{
    schema_version = 1; profile = 'm3-whole-function-558290'; scope = 'Complete first observed MW3 function only; no connected subsystem completion'
    image_path = $Image; image_sha256 = Get-MWHash $Image; code_path = $mwCode; code_sha256 = Get-MWHash $mwCode
    entry_va = 5603984; end_va = 5604027; code_bytes = 43; layout_path = "$mwOutput/layout.json"
    source_digest = $mwIdentity.source_digest; source_files = $mwSources; source_relative_files = $mwIdentity.source_files
    tool_files = $mwTools; artifacts = $mwHashes; workers = $mwWorkers; previous_gate_pins = $mwPreviousPins
    remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
    guest_ir_sha256 = Get-MWHash "$mwOutput/guest.ll"; host_ir_sha256 = Get-MWHash "$mwOutput/host.ll"
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'); optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    fast_math = $false; static_native_translation = $true; semantic_repairs = @(); commands = $mwCommands.ToArray()
}
$mwRecord | ConvertTo-Json -Depth 15 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) { Invoke-MWTool $Python @("$PSScriptRoot/compare_slice.py", '--build', "$mwOutput/build.json", '--out', "$mwOutput/comparison") }
