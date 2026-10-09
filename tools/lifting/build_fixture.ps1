param(
    [ValidateSet('add', 'branch', 'memory', 'shift')][string]$FixtureKind = 'add',
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
$mwOutput = "$mwRoot/reports/fixture-$FixtureKind-lift"
$mwNativeStem = if ($FixtureKind -eq 'add') { 'fixture-native' } else { "fixture-native-$FixtureKind" }
$mwKindNumber = switch ($FixtureKind) { 'add' { 0 } 'branch' { 1 } 'memory' { 2 } 'shift' { 3 } }
New-Item -ItemType Directory -Force $mwOutput | Out-Null
function Invoke-MWTool([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Tool failed ($LASTEXITCODE): $Program" }
}
function Get-MWHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
if ((git -C $RemillRoot rev-parse HEAD) -ne '0e324aee8c67a63ec759ef379dcfafa0b3cb1448') {
    throw 'Remill source must be the pinned v6.0.1 commit with the recorded local CMake patch'
}
Invoke-MWTool $mwCMake @('-S', "$mwRoot/tools/lifting", '-B', "$mwRoot/build/fixture-reference", '-G', 'Visual Studio 18 2026', '-A', 'Win32')
Invoke-MWTool $mwCMake @('--build', "$mwRoot/build/fixture-reference", '--config', 'Release')
$mwObject = "$mwRoot/build/fixture-reference/fixture_$FixtureKind.obj"
$mwFixture = "$mwRoot/build/fixture-reference/fixture_$FixtureKind.bin"
Invoke-MWTool "$LLVMRoot/bin/llvm-mc.exe" @('-triple=i686-pc-windows-msvc', '-filetype=obj', "$mwRoot/tests/fixtures/fixture_$FixtureKind.s", '-o', $mwObject)
Invoke-MWTool "$LLVMRoot/bin/llvm-objcopy.exe" @('--dump-section', ".text=$mwFixture", $mwObject)
$mwFixtureHex = & $Python "$PSScriptRoot/fixture_catalog.py" --name $FixtureKind --check-file $mwFixture
if ($LASTEXITCODE -ne 0) { throw 'Authored fixture identity mismatch' }
& "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel $mwObject | Set-Content "$mwOutput/original-disassembly.txt"
if ($LASTEXITCODE -ne 0) { throw 'Original disassembly failed' }
$mwLifter = "$RemillRoot/build/bin/lift/remill-lift-21.exe"
Invoke-MWTool $mwLifter @('--arch=x86', '--os=windows', '--address=268435456', "--bytes=$mwFixtureHex", "--ir_out=$mwOutput/fixture-guest.ll")
if ($FixtureKind -eq 'branch') {
    # Deliberately unresolved JGE destination. It is lifted for the adapter's
    # rejection test only, never executed by the reference or native worker.
    Invoke-MWTool $mwLifter @('--arch=x86', '--os=windows', '--address=268435456', '--bytes=8b4424043b4424087d7f8b442408b111c366b93322c3', "--ir_out=$mwOutput/bad-target-guest.ll")
}
# Assemble the validated textual module explicitly. Remill's simultaneous
# bitcode output left an empty destination on this Windows build.
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/fixture-guest.ll", '-o', "$mwOutput/fixture-guest.bc")
$mwAdapterProfile = if ($FixtureKind -eq 'shift') { 'shift' } else { 'fixture' }
Invoke-MWTool $Python @("$PSScriptRoot/host_adapter.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/fixture-guest.ll", '--host', "$mwOutput/fixture-host.ll", '--record', "$mwOutput/layout.json", '--profile', $mwAdapterProfile)
Invoke-MWTool "$LLVMRoot/bin/opt.exe" @('-passes=default<O2>', '-S', "$mwOutput/fixture-host.ll", '-o', "$mwOutput/fixture-host-O2.ll")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O0', "$mwOutput/fixture-host.ll", '-o', "$mwOutput/fixture-O0.obj")
Invoke-MWTool "$LLVMRoot/bin/llc.exe" @('-filetype=obj', '-O2', "$mwOutput/fixture-host-O2.ll", '-o', "$mwOutput/fixture-O2.obj")
Import-Module "$VSRoot/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH = "$LLVMRoot/bin;$VSRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$env:PATH"
foreach ($mwLevel in @('O0', 'O2')) {
    $mwBuild = "$mwRoot/build/$mwNativeStem-$mwLevel"
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', "$mwRoot/tools/lifting", '-B', $mwBuild, "-DMW34_LIFTED_OBJECT=$mwOutput/fixture-$mwLevel.obj", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", "-DMW34_FIXTURE_KIND=$mwKindNumber", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release')
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8')
    & "$LLVMRoot/bin/llvm-objdump.exe" --disassemble --x86-asm-syntax=intel "$mwOutput/fixture-$mwLevel.obj" | Set-Content "$mwOutput/native-$mwLevel-disassembly.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Native disassembly failed' }
}
$mwHashes = [ordered]@{}
$mwArtifacts = @('fixture-guest.ll', 'fixture-guest.bc', 'fixture-host.ll', 'fixture-host-O2.ll', 'fixture-O0.obj', 'fixture-O2.obj', 'layout.json')
if ($FixtureKind -eq 'branch') { $mwArtifacts += 'bad-target-guest.ll' }
foreach ($mwArtifact in $mwArtifacts) {
    if ((Get-Item -LiteralPath "$mwOutput/$mwArtifact").Length -eq 0) { throw "Empty generated artifact: $mwArtifact" }
    $mwHashes[$mwArtifact] = Get-MWHash "$mwOutput/$mwArtifact"
}
$mwRecord = [ordered]@{
    schema_version = 1
    scope = "reviewed authored fixture_$FixtureKind only"
    fixture_kind = $FixtureKind
    remill_commit = '0e324aee8c67a63ec759ef379dcfafa0b3cb1448'
    remill_lifter_sha256 = Get-MWHash $mwLifter
    remill_semantics_sha256 = Get-MWHash "$RemillRoot/build/lib/Arch/X86/Runtime/x86.bc"
    llvm_version = '21.1.8'
    llvm_dll_sha256 = Get-MWHash "$LLVMRoot/bin/LLVM-C.dll"
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc')
    optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    fixture_sha256 = Get-MWHash $mwFixture
    artifacts = $mwHashes
    reference_sha256 = Get-MWHash "$mwRoot/build/fixture-reference/Release/mw34_reference.exe"
    native_O0_sha256 = Get-MWHash "$mwRoot/build/$mwNativeStem-O0/mw34_lifted.exe"
    native_O2_sha256 = Get-MWHash "$mwRoot/build/$mwNativeStem-O2/mw34_lifted.exe"
}
$mwRecord | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) {
    Invoke-MWTool $Python @("$PSScriptRoot/compare_fixture.py", '--reference', "$mwRoot/build/fixture-reference/Release/mw34_reference.exe", '--lifted', "$mwRoot/build/$mwNativeStem-O0/mw34_lifted.exe", '--lifted', "$mwRoot/build/$mwNativeStem-O2/mw34_lifted.exe", '--fixture', $mwFixture, '--fixture-name', $FixtureKind, '--metadata', "$mwOutput/build.json", '--output-dir', "$mwRoot/reports/fixture-$FixtureKind-differential")
    $mwControlArguments = @("$PSScriptRoot/check_controls.py", '--reference', "$mwRoot/build/fixture-reference/Release/mw34_reference.exe", '--lifted', "$mwRoot/build/$mwNativeStem-O0/mw34_lifted.exe", '--lifted', "$mwRoot/build/$mwNativeStem-O2/mw34_lifted.exe", '--fixture', $mwFixture, '--fixture-name', $FixtureKind, '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/fixture-guest.ll", '--report', "$mwOutput/controls.json")
    if ($FixtureKind -eq 'branch') { $mwControlArguments += @('--bad-target-guest', "$mwOutput/bad-target-guest.ll") }
    Invoke-MWTool $Python $mwControlArguments
}
