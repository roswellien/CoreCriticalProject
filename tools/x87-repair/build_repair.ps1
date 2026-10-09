param(
    [string]$LLVMRoot,
    [string]$RemillRoot,
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$Python = 'C:/Python314/python.exe',
    [switch]$SkipToolchainBuild,
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
# Use a fresh PowerShell 7 process; developer setup is performed exactly once.
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
if (-not $SkipToolchainBuild) {
    Invoke-MWTool $Python @("$PSScriptRoot/prepare_toolchain.py", '--root', $mwRoot, '--remill-root', $RemillRoot, '--llvm-root', $LLVMRoot)
}
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw $mwRepairPath | ConvertFrom-Json
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Repair provenance changed: $($mwBinding[0])" }
}
foreach ($mwKind in @('store', 'load-store')) {
    $mwNumber = if ($mwKind -eq 'store') { 0 } else { 1 }
    $mwFixtureName = $mwKind.Replace('-', '_')
    $mwOutput = "$mwRoot/reports/x87-repair/$mwKind"
    $mwReferenceBuild = "$mwRoot/build/x87-repair-reference-$mwNumber"
    $mwReference = "$mwReferenceBuild/Release/mw34_x87_reference.exe"
    New-Item -ItemType Directory -Force $mwOutput | Out-Null
    $mwCommands.Clear()
    Invoke-MWTool "$LLVMRoot/bin/llvm-mc.exe" @('-triple=i686-pc-windows-msvc', '-filetype=obj', "$mwRoot/tests/x87-repair/$mwFixtureName.s", '-o', "$mwOutput/control-authored.obj")
    Invoke-MWTool "$LLVMRoot/bin/llvm-objcopy.exe" @('--dump-section', ".text=$mwOutput/control.bin", "$mwOutput/control-authored.obj")
    $mwHex = & $Python -c 'import pathlib,sys; b=pathlib.Path(sys.argv[1]).read_bytes(); expected=bytes.fromhex("d939c3" if sys.argv[2]=="store" else "d929d93ac3"); assert b==expected, "Authored fixture differs"; print(b.hex())' "$mwOutput/control.bin" $mwKind
    if ($LASTEXITCODE -ne 0) { throw 'Authored fixture identity failed' }
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/control-authored.obj" | Set-Content "$mwOutput/original-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Authored disassembly failed' }
    Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', '--address=268435456', "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwOutput/guest.ll")
    Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/guest.ll", '-o', "$mwOutput/guest.bc")
    Invoke-MWTool $Python @("$PSScriptRoot/adapt_control.py", '--kind', $mwKind, '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/layout.json")
    Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/host.ll", '-o', "$mwOutput/host-O2.ll")
    Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/host.ll", '-o', "$mwOutput/native-O0.obj")
    Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/host-O2.ll", '-o', "$mwOutput/native-O2.obj")
    Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32', "-DMW34_X87_FIXTURE_KIND=$mwNumber")
    Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release')
    foreach ($mwLevel in @('O0', 'O2')) {
        $mwBuild = "$mwRoot/build/x87-repair-$mwKind-$mwLevel"
        Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_LIFTED_OBJECT=$mwOutput/native-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", "-DMW34_X87_FIXTURE_KIND=$mwNumber", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release')
        Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
        & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/native-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
        if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
    }
    $mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'Authored source identity failed' }
    $mwHashes = [ordered]@{}
    foreach ($mwName in @('control.bin', 'control-authored.obj', 'original-disassembly.txt', 'guest.ll', 'guest.bc', 'host.ll', 'host-O2.ll', 'native-O0.obj', 'native-O2.obj', 'layout.json', 'native-O0-disassembly.txt', 'native-O2-disassembly.txt')) {
        if ((Get-Item -LiteralPath "$mwOutput/$mwName").Length -eq 0) { throw "Empty artifact: $mwName" }
        $mwHashes[$mwName] = Get-MWHash "$mwOutput/$mwName"
    }
    $mwRecord = [ordered]@{
        schema_version = 1; kind = $mwKind; scope = 'masked x87 control-word storage/load only'; entry_va = 268435456
        fixture_sha256 = Get-MWHash "$mwOutput/control.bin"
        contract_sha256 = Get-MWHash "$mwRoot/docs/x87-repair-contract.md"
        source_digest = $mwIdentity.source_digest; source_files = $mwIdentity.source_files
        remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; llvm_dll_sha256 = $mwRepair.llvm_dll_sha256
        repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
        target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
        optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2'); artifacts = $mwHashes
        reference_sha256 = Get-MWHash $mwReference
        native_O0_sha256 = Get-MWHash "$mwRoot/build/x87-repair-$mwKind-O0/mw34_x87_native.exe"
        native_O2_sha256 = Get-MWHash "$mwRoot/build/x87-repair-$mwKind-O2/mw34_x87_native.exe"
        commands = $mwCommands.ToArray()
    }
    foreach ($mwKey in @('baseline_semantics_sha256','repaired_semantics_sha256','baseline_remill_lifter_sha256','remill_lifter_sha256','patch_sha256')) { $mwRecord[$mwKey] = $mwRepair.$mwKey }
    $mwRecord | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 "$mwOutput/build.json"
    if ($RunComparison) {
        Invoke-MWTool $Python @("$PSScriptRoot/compare_control.py", '--kind', $mwKind, '--reference', $mwReference, '--native', "$mwRoot/build/x87-repair-$mwKind-O0/mw34_x87_native.exe", '--native', "$mwRoot/build/x87-repair-$mwKind-O2/mw34_x87_native.exe", '--fixture', "$mwOutput/control.bin", '--metadata', "$mwOutput/build.json", '--output-dir', "$mwOutput/comparison")
    }
}
