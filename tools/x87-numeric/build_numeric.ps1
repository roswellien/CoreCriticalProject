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
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw $mwRepairPath | ConvertFrom-Json
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Repair provenance changed: $($mwBinding[0])" }
}
$mwOutput = "$mwRoot/reports/x87-numeric"
$mwReferenceBuild = "$mwRoot/build/x87-numeric-reference"
$mwReference = "$mwReferenceBuild/Release/mw34_x87_reference.exe"
New-Item -ItemType Directory -Force $mwOutput | Out-Null
Invoke-MWTool "$LLVMRoot/bin/llvm-mc.exe" @('-triple=i686-pc-windows-msvc', '-filetype=obj', "$mwRoot/tests/x87-numeric/add_sub.s", '-o', "$mwOutput/add-sub-authored.obj")
Invoke-MWTool "$LLVMRoot/bin/llvm-objcopy.exe" @('--dump-section', ".text=$mwOutput/add-sub.bin", "$mwOutput/add-sub-authored.obj")
$mwHex = & $Python -c 'import pathlib,sys; b=pathlib.Path(sys.argv[1]).read_bytes(); assert b==bytes.fromhex("dd01dc4108dc21dd1ac3"), "Authored fixture differs"; print(b.hex())' "$mwOutput/add-sub.bin"
if ($LASTEXITCODE -ne 0) { throw 'Authored fixture identity failed' }
& "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/add-sub-authored.obj" | Set-Content "$mwOutput/original-disassembly.txt"
if ($LASTEXITCODE -ne 0) { throw 'Authored disassembly failed' }
Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', '--address=268435456', "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwOutput/add-sub-guest.ll")
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/add-sub-guest.ll", '-o', "$mwOutput/guest.bc")
Invoke-MWTool $Python @("$PSScriptRoot/adapt_numeric.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/add-sub-guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/layout.json")
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/host.ll", '-o', "$mwOutput/host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/host.ll", '-o', "$mwOutput/native-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/host-O2.ll", '-o', "$mwOutput/native-O2.obj")
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32')
Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release')
foreach ($mwLevel in @('O0', 'O2')) {
    $mwBuild = "$mwRoot/build/x87-numeric-$mwLevel"
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_LIFTED_OBJECT=$mwOutput/native-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release')
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
    Invoke-MWTool "$mwBuild/mw34_x87_native.exe" @('--check-memory-bridges')
    Invoke-MWTool "$mwBuild/mw34_x87_native.exe" @('--check-fp-environment')
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/native-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
}
Invoke-MWTool $Python @("$mwRoot/tests/x87-numeric/test_adapter_controls.py", '--root', $mwRoot, '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/add-sub-guest.ll", '--output-dir', "$mwOutput/adapter-controls")
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Authored source identity failed' }
$mwHashes = [ordered]@{}
foreach ($mwName in @('add-sub.bin', 'add-sub-authored.obj', 'original-disassembly.txt', 'add-sub-guest.ll', 'guest.bc', 'host.strict-input.ll', 'host.ll', 'host-O2.ll', 'native-O0.obj', 'native-O2.obj', 'layout.json', 'native-O0-disassembly.txt', 'native-O2-disassembly.txt', 'adapter-controls/report.json')) {
    if ((Get-Item -LiteralPath "$mwOutput/$mwName").Length -eq 0) { throw "Empty artifact: $mwName" }
    $mwHashes[$mwName] = Get-MWHash "$mwOutput/$mwName"
}
$mwRecord = [ordered]@{
    schema_version = 1; kind = 'add-sub'; scope = 'authored masked finite x87 add/sub directed corpus only'; entry_va = 268435456
    fixture_sha256 = Get-MWHash "$mwOutput/add-sub.bin"; contract_sha256 = Get-MWHash "$mwRoot/docs/x87-numeric-contract.md"
    source_digest = $mwIdentity.source_digest; source_files = $mwIdentity.source_files
    remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; llvm_dll_sha256 = $mwRepair.llvm_dll_sha256
    repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
    optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2'); artifacts = $mwHashes
    reference_sha256 = Get-MWHash $mwReference
    native_O0_sha256 = Get-MWHash "$mwRoot/build/x87-numeric-O0/mw34_x87_native.exe"
    native_O2_sha256 = Get-MWHash "$mwRoot/build/x87-numeric-O2/mw34_x87_native.exe"
    memory_bridge_checks_per_native = 8; fp_environment_checks_per_native = 15
    adapter_mutation_controls = 8
    commands = $mwCommands.ToArray()
}
$mwTools = [ordered]@{}
foreach ($mwTool in @('llvm-mc.exe','llvm-objcopy.exe','llvm-objdump.exe','llvm-as.exe','opt.exe','llc.exe','clang-cl.exe','LLVM-C.dll')) {
    $mwToolPath = "$LLVMRoot/bin/$mwTool"
    $mwTools[$mwToolPath] = Get-MWHash $mwToolPath
}
foreach ($mwToolPath in @($Python, $mwCMake, $mwRepair.remill_lifter_path)) { $mwTools[$mwToolPath] = Get-MWHash $mwToolPath }
$mwRecord['tool_files'] = $mwTools
$mwRecord['compiler'] = "$LLVMRoot/bin/clang-cl.exe"
foreach ($mwKey in @('baseline_semantics_sha256','repaired_semantics_sha256','baseline_remill_lifter_sha256','remill_lifter_sha256','patch_sha256')) { $mwRecord[$mwKey] = $mwRepair.$mwKey }
$mwRecord | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) {
    Invoke-MWTool $Python @("$PSScriptRoot/compare_numeric.py", '--reference', $mwReference, '--native', "$mwRoot/build/x87-numeric-O0/mw34_x87_native.exe", '--native', "$mwRoot/build/x87-numeric-O2/mw34_x87_native.exe", '--fixture', "$mwOutput/add-sub.bin", '--metadata', "$mwOutput/build.json", '--output-dir', "$mwOutput/comparison")
}
