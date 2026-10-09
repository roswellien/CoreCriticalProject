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
$mwOutput = "$mwRoot/reports/x87-bootstrap"
$mwReference = "$mwRoot/build/x87-control-reference/Release/mw34_x87_reference.exe"
New-Item -ItemType Directory -Force $mwOutput | Out-Null
$mwCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWTool([string]$Program, [string[]]$Arguments) {
    $mwCommands.Add(@($Program) + $Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
if ((git -C $RemillRoot rev-parse HEAD) -ne '0e324aee8c67a63ec759ef379dcfafa0b3cb1448') {
    throw 'Remill source must be the pinned v6.0.1 commit'
}
Invoke-MWTool "$LLVMRoot/bin/llvm-mc.exe" @('-triple=i686-pc-windows-msvc', '-filetype=obj', "$mwRoot/tests/x87/fixture_control.s", '-o', "$mwOutput/control-authored.obj")
Invoke-MWTool "$LLVMRoot/bin/llvm-objcopy.exe" @('--dump-section', ".text=$mwOutput/control.bin", "$mwOutput/control-authored.obj")
$mwHex = & $Python -c 'import pathlib,sys; b=pathlib.Path(sys.argv[1]).read_bytes(); assert b==bytes.fromhex("d939c3"), "Authored fixture differs"; print(b.hex())' "$mwOutput/control.bin"
if ($LASTEXITCODE -ne 0) { throw 'Authored fixture identity check failed' }
& "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/control-authored.obj" | Set-Content "$mwOutput/original-disassembly.txt"
if ($LASTEXITCODE -ne 0) { throw 'Authored disassembly failed' }
$mwLifter = "$RemillRoot/build/bin/lift/remill-lift-21.exe"
Invoke-MWTool $mwLifter @('--arch=x86', '--os=windows', '--address=268435456', "--bytes=$mwHex", "--ir_out=$mwOutput/control-guest.ll")
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/control-guest.ll", '-o', "$mwOutput/control-guest.bc")
Invoke-MWTool $Python @("$PSScriptRoot/adapt_control.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/control-guest.ll", '--host', "$mwOutput/control-host.ll", '--record', "$mwOutput/layout.json")
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/control-host.ll", '-o', "$mwOutput/control-host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/control-host.ll", '-o', "$mwOutput/control-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/control-host-O2.ll", '-o', "$mwOutput/control-O2.obj")
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', "$mwRoot/build/x87-control-reference", '-G', 'Visual Studio 18 2026', '-A', 'Win32')
Invoke-MWTool $mwCMake @('--build', "$mwRoot/build/x87-control-reference", '--config', 'Release')
# Run this script in its own PowerShell process so Visual Studio setup is local.
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
foreach ($mwLevel in @('O0', 'O2')) {
    $mwBuild = "$mwRoot/build/x87-control-native-$mwLevel"
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_LIFTED_OBJECT=$mwOutput/control-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release')
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/control-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
}
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Authored source identity failed' }
$mwHashes = [ordered]@{}
foreach ($mwArtifact in @('control.bin', 'control-authored.obj', 'original-disassembly.txt', 'control-guest.ll', 'control-guest.bc', 'control-host.ll', 'control-host-O2.ll', 'control-O0.obj', 'control-O2.obj', 'layout.json', 'native-O0-disassembly.txt', 'native-O2-disassembly.txt')) {
    if ((Get-Item -LiteralPath "$mwOutput/$mwArtifact").Length -eq 0) { throw "Empty artifact: $mwArtifact" }
    $mwHashes[$mwArtifact] = Get-MWHash "$mwOutput/$mwArtifact"
}
$mwRecord = [ordered]@{
    schema_version = 1
    scope = 'authored FNSTCW [ECX]; RET control-word storage only'
    entry_va = 268435456
    fixture_sha256 = Get-MWHash "$mwOutput/control.bin"
    contract_sha256 = Get-MWHash "$mwRoot/docs/x87-control-contract.md"
    source_digest = $mwIdentity.source_digest
    source_files = $mwIdentity.source_files
    remill_commit = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
    remill_lifter_sha256 = Get-MWHash $mwLifter
    remill_semantics_sha256 = Get-MWHash "$RemillRoot/build/lib/Arch/X86/Runtime/x86.bc"
    llvm_version = '21.1.8'
    llvm_dll_sha256 = Get-MWHash "$LLVMRoot/bin/LLVM-C.dll"
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
    optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    artifacts = $mwHashes
    reference_sha256 = Get-MWHash $mwReference
    native_O0_sha256 = Get-MWHash "$mwRoot/build/x87-control-native-O0/mw34_x87_native.exe"
    native_O2_sha256 = Get-MWHash "$mwRoot/build/x87-control-native-O2/mw34_x87_native.exe"
    commands = $mwCommands.ToArray()
}
$mwRecord | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) {
    Invoke-MWTool $Python @("$PSScriptRoot/compare_control.py", '--reference', $mwReference, '--native', "$mwRoot/build/x87-control-native-O0/mw34_x87_native.exe", '--native', "$mwRoot/build/x87-control-native-O2/mw34_x87_native.exe", '--fixture', "$mwOutput/control.bin", '--metadata', "$mwOutput/build.json", '--output-dir', "$mwOutput/comparison")
}
