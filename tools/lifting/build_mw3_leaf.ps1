param(
    [string]$Game = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [string]$LiveSnapshot,
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
$mwOutput = "$mwRoot/reports/mw3-leaf-lift"
$mwReference = "$mwRoot/build/mw3-reference/Release/mw34_reference.exe"
function Invoke-MWTool([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
if ((git -C $RemillRoot rev-parse HEAD) -ne '0e324aee8c67a63ec759ef379dcfafa0b3cb1448') {
    throw 'Remill source must be the pinned v6.0.1 commit with the recorded local CMake patch'
}
# Full image, reviewed metadata, section mapping and slice identities are admitted
# before any original game instruction can reach an execution worker.
Invoke-MWTool $Python @("$mwRoot/tools/analysis/extract_mw3_leaf.py", $Game, '--output-dir', $mwOutput)
$mwSlice = "$mwOutput/sub_00409ed0.bin"
$mwSliceRecord = Get-Content -Raw "$mwOutput/slice.json" | ConvertFrom-Json
$mwHex = & $Python -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_bytes().hex())' $mwSlice
if ($LASTEXITCODE -ne 0) { throw 'Admitted slice could not be read' }
$mwLifter = "$RemillRoot/build/bin/lift/remill-lift-21.exe"
Invoke-MWTool $mwLifter @('--arch=x86', '--os=windows', '--address=4234960', "--bytes=$mwHex", "--ir_out=$mwOutput/sub_00409ed0-guest.ll")
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/sub_00409ed0-guest.ll", '-o', "$mwOutput/sub_00409ed0-guest.bc")
# The explicit entry/undefined-flag policy is filled by the reviewed adapter;
# default fixture admission never silently accepts a game entry or new helper.
Invoke-MWTool $Python @("$PSScriptRoot/host_adapter.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/sub_00409ed0-guest.ll", '--host', "$mwOutput/sub_00409ed0-host.ll", '--record', "$mwOutput/layout.json", '--profile', 'mw3-helper')
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/sub_00409ed0-host.ll", '-o', "$mwOutput/sub_00409ed0-host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/sub_00409ed0-host.ll", '-o', "$mwOutput/sub_00409ed0-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/sub_00409ed0-host-O2.ll", '-o', "$mwOutput/sub_00409ed0-O2.obj")
Invoke-MWTool $mwCMake @('-S', "$mwRoot/tools/lifting", '-B', "$mwRoot/build/mw3-reference", '-G', 'Visual Studio 18 2026', '-A', 'Win32')
Invoke-MWTool $mwCMake @('--build', "$mwRoot/build/mw3-reference", '--config', 'Release')
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
foreach ($mwLevel in @('O0', 'O2')) {
    $mwBuild = "$mwRoot/build/mw3-native-$mwLevel"
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', "$mwRoot/tools/lifting", '-B', $mwBuild, "-DMW34_LIFTED_OBJECT=$mwOutput/sub_00409ed0-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DMW34_FIXTURE_KIND=4', '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release')
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/sub_00409ed0-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
}
$mwSourceDigest = & $Python -c 'import sys,pathlib; sys.path.insert(0,sys.argv[1]); from compare_fixture import source_digest; print(source_digest(pathlib.Path(sys.argv[2])))' $PSScriptRoot $mwRoot
if ($LASTEXITCODE -ne 0) { throw 'Authored source digest failed' }
$mwHashes = [ordered]@{}
foreach ($mwArtifact in @('sub_00409ed0.bin', 'slice.json', 'sub_00409ed0-guest.ll', 'sub_00409ed0-guest.bc', 'sub_00409ed0-host.ll', 'sub_00409ed0-host-O2.ll', 'sub_00409ed0-O0.obj', 'sub_00409ed0-O2.obj', 'layout.json')) {
    if ((Get-Item -LiteralPath "$mwOutput/$mwArtifact").Length -eq 0) { throw "Empty generated artifact: $mwArtifact" }
    $mwHashes[$mwArtifact] = Get-MWHash "$mwOutput/$mwArtifact"
}
$mwRecord = [ordered]@{
    schema_version = 1
    scope = 'reviewed sub_00409ED0 original x86 versus Remill-generated native x64 only'
    fixture_kind = 'mw3_helper'
    entry_va = 4234960
    game_sha256 = Get-MWHash $Game
    slice_sha256 = Get-MWHash $mwSlice
    fixture_sha256 = Get-MWHash $mwSlice
    contract_sha256 = $mwSliceRecord.contract_sha256
    source_digest = $mwSourceDigest
    remill_commit = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
    remill_lifter_sha256 = Get-MWHash $mwLifter
    remill_semantics_sha256 = Get-MWHash "$RemillRoot/build/lib/Arch/X86/Runtime/x86.bc"
    llvm_version = '21.1.8'
    llvm_dll_sha256 = Get-MWHash "$LLVMRoot/bin/LLVM-C.dll"
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
    optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    artifacts = $mwHashes
    reference_sha256 = Get-MWHash $mwReference
    native_O0_sha256 = Get-MWHash "$mwRoot/build/mw3-native-O0/mw34_lifted.exe"
    native_O2_sha256 = Get-MWHash "$mwRoot/build/mw3-native-O2/mw34_lifted.exe"
}
$mwRecord | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) {
    $mwComparisonArguments = @("$PSScriptRoot/compare_mw3_leaf.py", '--game', $Game, '--reference', $mwReference, '--lifted', "$mwRoot/build/mw3-native-O0/mw34_lifted.exe", '--lifted', "$mwRoot/build/mw3-native-O2/mw34_lifted.exe", '--metadata', "$mwOutput/build.json", '--output-dir', "$mwRoot/reports/mw3-leaf-differential")
    if ($LiveSnapshot) { $mwComparisonArguments += @('--live-snapshot', $LiveSnapshot) }
    Invoke-MWTool $Python $mwComparisonArguments
    Invoke-MWTool $Python @("$PSScriptRoot/verify_mw3_leaf.py", '--report-dir', "$mwRoot/reports/mw3-leaf-differential", '--game', $Game, '--output', "$mwRoot/reports/mw3-leaf-differential/verification.json")
}
