param(
    [string]$LLVMRoot,
    [string]$RemillRoot,
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Python = 'C:/Python314/python.exe',
    [switch]$RunComparison
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path.Replace('\', '/')
if (-not $LLVMRoot) { $LLVMRoot = "$mwRoot/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc" }
if (-not $RemillRoot) { $RemillRoot = "$mwRoot/local/tools/remill-v6.0.1/remill-6.0.1" }
$LLVMRoot = (Resolve-Path $LLVMRoot).Path.Replace('\', '/')
$RemillRoot = (Resolve-Path $RemillRoot).Path.Replace('\', '/')
$mwCMake = "$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
$mwCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWTool([string]$Program, [string[]]$Arguments) {
    $mwCommands.Add(@($Program) + $Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
$mwInitialFailure = "$mwRoot/reports/x87-arithmetic/baseline-failure/report.json"
if ((Get-MWHash $mwInitialFailure) -ne 'b2c41d795a7b3daa9fb5e7f7359b731569cc3ccb9aea5db1bb8b6bf75bd2b067') { throw 'Initial failed arithmetic evidence changed' }
$mwC1Baseline = "$mwRoot/reports/x87-store-c1/baseline-failure/report.json"
if ((Get-MWHash $mwC1Baseline) -ne '03eba1e074e3770bb42c2c411e876335f0cef556c9e4dd80d027cc960cd2f586') { throw 'Preserved final-store C1 baseline changed' }
$mwPreviousGate = "$mwRoot/reports/x87-range/independent-review/final-pins.json"
if ((Get-MWHash $mwPreviousGate) -ne '11c50568126933468e32ef061c0adf450aa0d61e1e0d01861d6f2d77fe5306d2') { throw 'Previous store-C1 final bindings changed' }
$mwRangeBaseline = "$mwRoot/reports/x87-range/baseline-failure/report.json"
if ((Get-MWHash $mwRangeBaseline) -ne 'f52847eb4f286ae7e6af20835898981a4ef0f8e7823d3eb46e6b803c6a7320fd') { throw 'Preserved range failure changed' }
$mwStateBaseline = "$mwRoot/reports/x87-state/baseline-failure/report.json"
if ((Get-MWHash $mwStateBaseline) -ne '7b0c935743991ecef15174d7c3d343852a772d63e0fc6d52a2cecf3198c88f11') { throw 'Preserved state failure changed' }
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw $mwRepairPath | ConvertFrom-Json
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Repair provenance changed: $($mwBinding[0])" }
}
foreach ($mwKind in @('push', 'pop', 'exchange', 'free')) {
$mwNumber = @('push', 'pop', 'exchange', 'free').IndexOf($mwKind)
$mwFixture = $mwKind
$mwCommands.Clear()
$mwOutput = "$mwRoot/reports/x87-state/$mwKind"
$mwReferenceBuild = "$mwRoot/build/x87-state-reference-$mwKind"
$mwReference = "$mwReferenceBuild/Release/mw34_x87_reference.exe"
New-Item -ItemType Directory -Force $mwOutput | Out-Null
Invoke-MWTool "$LLVMRoot/bin/llvm-mc.exe" @('-triple=i686-pc-windows-msvc', '-filetype=obj', "$mwRoot/tests/x87-state/$mwFixture.s", '-o', "$mwOutput/fixture-authored.obj")
Invoke-MWTool "$LLVMRoot/bin/llvm-objcopy.exe" @('--dump-section', ".text=$mwOutput/fixture.bin", "$mwOutput/fixture-authored.obj")
$mwHex = & $Python -c 'import pathlib,sys; b=pathlib.Path(sys.argv[1]).read_bytes(); assert b==bytes.fromhex({"push":"db29c3","pop":"db3ac3","exchange":"d9c9c3","free":"ddc1c3"}[sys.argv[2]]), "Authored fixture differs"; print(b.hex())' "$mwOutput/fixture.bin" $mwKind
if ($LASTEXITCODE -ne 0) { throw 'Authored fixture identity failed' }
& "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/fixture-authored.obj" | Set-Content "$mwOutput/original-disassembly.txt"
if ($LASTEXITCODE -ne 0) { throw 'Authored disassembly failed' }
Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', '--address=268435456', "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwOutput/guest.ll")
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/guest.ll", '-o', "$mwOutput/guest.bc")
Invoke-MWTool $Python @("$PSScriptRoot/adapt_state.py", '--kind', $mwKind, '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/layout.json")
Invoke-MWTool $Python @("$PSScriptRoot/run_adapter_controls.py", '--kind', $mwKind, '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/adapter-controls.json")
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/host.ll", '-o', "$mwOutput/host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/host.ll", '-o', "$mwOutput/native-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/host-O2.ll", '-o', "$mwOutput/native-O2.obj")
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32', "-DMW34_X87_FIXTURE_KIND=$mwNumber")
Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release')
foreach ($mwLevel in @('O0', 'O2')) {
    Invoke-MWTool $Python @("$PSScriptRoot/check_object.py", '--kind', $mwKind, '--nm', "$LLVMRoot/bin/llvm-nm.exe", '--object', "$mwOutput/native-$mwLevel.obj", '--record', "$mwOutput/native-$mwLevel-symbols.json")
    $mwBuild = "$mwRoot/build/x87-state-$mwKind-$mwLevel"
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_HOST_OBJECT=$mwOutput/native-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", "-DMW34_X87_FIXTURE_KIND=$mwNumber", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG -Wno-invalid-offsetof')
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
    Invoke-MWTool "$mwBuild/mw34_x87_native.exe" @('--check-memory-bridges')
    Invoke-MWTool "$mwBuild/mw34_x87_native.exe" @('--check-fp-environment')
    Invoke-MWTool "$mwBuild/mw34_x87_native.exe" @('--check-mxcsr-isolation')
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/native-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
}
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Authored source identity failed' }
$mwHashes = [ordered]@{}
foreach ($mwName in @('fixture.bin', 'fixture-authored.obj', 'original-disassembly.txt', 'guest.ll', 'guest.bc', 'host.strict-input.ll', 'host.ll', 'host-O2.ll', 'native-O0.obj', 'native-O2.obj', 'layout.json', 'adapter-controls.json', 'native-O0-disassembly.txt', 'native-O2-disassembly.txt', 'native-O0-symbols.json', 'native-O2-symbols.json')) {
    if ((Get-Item -LiteralPath "$mwOutput/$mwName").Length -eq 0) { throw "Empty artifact: $mwName" }
    $mwHashes[$mwName] = Get-MWHash "$mwOutput/$mwName"
}
$mwRecord = [ordered]@{
    initial_failure_provenance_path = $mwInitialFailure; initial_failure_provenance_sha256 = Get-MWHash $mwInitialFailure
    c1_baseline_path = $mwC1Baseline; c1_baseline_sha256 = Get-MWHash $mwC1Baseline
    previous_gate_provenance_path = $mwPreviousGate; previous_gate_provenance_sha256 = Get-MWHash $mwPreviousGate
    range_baseline_path = $mwRangeBaseline; range_baseline_sha256 = Get-MWHash $mwRangeBaseline
    state_baseline_path = $mwStateBaseline; state_baseline_sha256 = Get-MWHash $mwStateBaseline
    schema_version = 1; kind = $mwKind; semantic_stage = 'repaired'; scope = 'authored live raw80 stack/tag gate with reviewed internal static repair'; entry_va = 268435456
    fixture_sha256 = Get-MWHash "$mwOutput/fixture.bin"; contract_sha256 = Get-MWHash "$mwRoot/docs/x87-state-contract.md"
    source_digest = $mwIdentity.source_digest; source_files = $mwIdentity.source_files
    remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; llvm_dll_sha256 = $mwRepair.llvm_dll_sha256
    repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
    optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2'); artifacts = $mwHashes
    reference_sha256 = Get-MWHash $mwReference
    native_O0_sha256 = Get-MWHash "$mwRoot/build/x87-state-$mwKind-O0/mw34_x87_native.exe"
    native_O2_sha256 = Get-MWHash "$mwRoot/build/x87-state-$mwKind-O2/mw34_x87_native.exe"
    memory_bridge_checks_per_native = 12; fp_environment_checks_per_native = 15
    mxcsr_isolation_checks_per_native = 384; guest_mxcsr = 8064
    adapter_mutation_controls = $(if ($mwKind -eq 'pop') { 13 } else { 12 })
    rounding_bridge_checks_per_native = 0
    object_symbol_rejection_checks_per_native = 3
    commands = $mwCommands.ToArray()
}
$mwTools = [ordered]@{}
foreach ($mwTool in @('llvm-mc.exe','llvm-objcopy.exe','llvm-objdump.exe','llvm-nm.exe','llvm-as.exe','opt.exe','llc.exe','clang-cl.exe','LLVM-C.dll')) {
    $mwToolPath = "$LLVMRoot/bin/$mwTool"
    $mwTools[$mwToolPath] = Get-MWHash $mwToolPath
}
foreach ($mwToolPath in @($Python, $mwCMake, $mwRepair.remill_lifter_path)) { $mwTools[$mwToolPath] = Get-MWHash $mwToolPath }
$mwRecord['tool_files'] = $mwTools
$mwRecord['compiler'] = "$LLVMRoot/bin/clang-cl.exe"
foreach ($mwKey in @('baseline_semantics_sha256','repaired_semantics_sha256','baseline_remill_lifter_sha256','remill_lifter_sha256','patch_sha256')) { $mwRecord[$mwKey] = $mwRepair.$mwKey }
$mwRecord | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) {
    Invoke-MWTool $Python @("$PSScriptRoot/compare_state.py", '--kind', $mwKind, '--reference', $mwReference, '--native', "$mwRoot/build/x87-state-$mwKind-O0/mw34_x87_native.exe", '--native', "$mwRoot/build/x87-state-$mwKind-O2/mw34_x87_native.exe", '--fixture', "$mwOutput/fixture.bin", '--metadata', "$mwOutput/build.json", '--output-dir', "$mwOutput/comparison")
}

}
