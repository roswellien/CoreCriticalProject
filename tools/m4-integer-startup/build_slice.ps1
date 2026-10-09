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
if (-not $OutputDirectory) { $OutputDirectory = "$mwRoot/reports/m4-integer-startup/whole-function" }
$mwOutput = [System.IO.Path]::GetFullPath($OutputDirectory).Replace('\', '/')
if (-not $mwOutput.StartsWith("$mwRoot/reports/m4-integer-startup/", [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Private output must stay within ignored M4 reports' }
$mwBuildName = Split-Path $mwOutput -Leaf
$mwBuildDirectories = [ordered]@{
    reference = "$mwRoot/build/m4-integer-startup-$mwBuildName-reference"
    O0 = "$mwRoot/build/m4-integer-startup-$mwBuildName-O0"
    O2 = "$mwRoot/build/m4-integer-startup-$mwBuildName-O2"
}
# Admit every output before private input resolution, source capture or mutation.
if (Test-Path -LiteralPath $mwOutput) { throw 'M4 report output already exists; use an entirely fresh OutputDirectory' }
foreach ($mwBuildLabel in $mwBuildDirectories.Keys) {
    if (Test-Path -LiteralPath $mwBuildDirectories[$mwBuildLabel]) { throw "M4 derived build directory already exists: $mwBuildLabel" }
}
$LLVMRoot = (Resolve-Path $LLVMRoot).Path.Replace('\', '/')
$RemillRoot = (Resolve-Path $RemillRoot).Path.Replace('\', '/')
$Image = (Resolve-Path -LiteralPath $Image).Path.Replace('\', '/')
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
if ($LASTEXITCODE -ne 0) { throw 'Initial M4 source identity failed' }
New-Item -ItemType Directory -Force $mwOutput | Out-Null
Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_build_paths.py", '--powershell', (Get-Process -Id $PID).Path, '--recipe', "$PSScriptRoot/build_slice.ps1", '--output', "$mwOutput/build-directory-controls.json") "$mwOutput/build-directory-controls.log"
$mwRepairPath = "$mwRoot/reports/x87-repair/toolchain/repair.json"
$mwRepair = Get-Content -Raw -LiteralPath $mwRepairPath | ConvertFrom-Json
if ($mwRepair.remill_lifter_sha256 -ne 'b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38' -or
    $mwRepair.repaired_semantics_sha256 -ne '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca') { throw 'Unreviewed Remill/semantics binding' }
foreach ($mwBinding in @(@('patch_path','patch_sha256'), @('repaired_semantics_path','repaired_semantics_sha256'), @('remill_lifter_path','remill_lifter_sha256'), @('baseline_semantics_path','baseline_semantics_sha256'), @('baseline_remill_lifter_path','baseline_remill_lifter_sha256'))) {
    if ((Get-MWHash $mwRepair.($mwBinding[0])) -ne $mwRepair.($mwBinding[1])) { throw "Frozen toolchain provenance changed: $($mwBinding[0])" }
}
if ((Get-MWHash "$LLVMRoot/bin/LLVM-C.dll") -ne '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb') { throw 'Unreviewed LLVM DLL' }
$mwPreviousPins = [ordered]@{
    "$mwRoot/reports/m4-initializer-chain/author-review-r1/pins.json" = 'e28c3df395eab9e89126f870753fb053423ce59afcd5e0b04346c63216e96c79'
    "$mwRoot/reports/m4-initializer-chain/independent-review/r6/pins.json" = '4875785ae97038dbe01d720a4d439fe27fcf3658406925379d6b6e4aae657d1b'
    "$mwRoot/reports/m3-acceptance/final-pins.json" = 'bfd3dd2014fc6d6a6de2f8981064c506863651db8cf134b6f878de6dd1e7ec01'
    "$mwRoot/reports/m4-initializer/independent-review/stage-safe-final-pins.json" = 'efe183aaadf9a0b7b0c44cf6bbb894e1900815b64b8c9cd03d7b3e440a72e9cb'
    "$mwRoot/reports/m4-startup/next-initializer-410940/pins.json" = '7521a5ed5229de80df26d98a47a31ae865203826d4ca614e88cd46e01ca5037c'
    "$mwRoot/reports/m4-startup/next-initializer-410940-events/pins.json" = 'c5320a5158100b8a80ce9d00113b9f4ce2ccb7576bbede30eba9e25b684499bb' 
    "$mwRoot/reports/m4-runtime/context-r7/build.json" = '02671aaae2e96ac9d1c507e3939c4a3047d67228b65efecae722f405e229a257'
}
foreach ($mwPin in $mwPreviousPins.Keys) {
    if ((Get-MWHash $mwPin) -ne $mwPreviousPins[$mwPin]) { throw "Frozen previous gate changed: $mwPin" }
}
Invoke-MWTool $Python @("$PSScriptRoot/recover.py", '--image', $Image, '--out', $mwOutput, '--decoder', "$LLVMRoot/bin/llvm-objdump.exe") "$mwOutput/extraction.log"
$mwCode = "$mwOutput/code.bin"
$mwSlice = Get-Content -Raw -LiteralPath "$mwOutput/report.json" | ConvertFrom-Json
$mwGuestInputs = [System.Collections.Generic.List[string]]::new()
foreach ($mwFunction in $mwSlice.functions) {
    $mwHex = & $Python -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).read_bytes().hex())' $mwFunction.code_path
    if ($LASTEXITCODE -ne 0) { throw 'Private complete function read failed' }
    $mwEntryName = ([uint32]$mwFunction.entry_va).ToString('x')
    $mwGuestPath = "$mwOutput/guest-$mwEntryName.ll"
    Invoke-MWTool $mwRepair.remill_lifter_path @('--arch=x86', '--os=windows', "--address=$($mwFunction.entry_va)", "--bytes=$mwHex", "--semantics_dir=$(Split-Path $mwRepair.repaired_semantics_path)", "--ir_out=$mwGuestPath") "$mwOutput/lifter-$mwEntryName.log"
    if ((Get-MWHash $mwGuestPath) -ne $mwFunction.guest_ir_sha256) { throw 'Individual complete guest IR identity changed' }
    $mwGuestInputs.Add($mwGuestPath)
}
Invoke-MWTool "$LLVMRoot/bin/llvm-link.exe" (@('-S') + $mwGuestInputs.ToArray() + @('-o', "$mwOutput/guest.ll"))
Invoke-MWTool "$LLVMRoot/bin/llvm-as.exe" @("$mwOutput/guest.ll", '-o', "$mwOutput/guest.bc")
Invoke-MWTool $Python @("$PSScriptRoot/adapt_slice.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/layout.json", '--recovery', "$mwOutput/report.json") "$mwOutput/adapter.log"
Invoke-MWTool $Python @("$PSScriptRoot/check_admission.py", '--llvm-dll', "$LLVMRoot/bin/LLVM-C.dll", '--guest', "$mwOutput/guest.ll", '--host', "$mwOutput/host.ll", '--record', "$mwOutput/adapter-controls.json", '--recovery', "$mwOutput/report.json") "$mwOutput/adapter-controls.log"
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
$mwReferenceBuild = $mwBuildDirectories.reference
$mwWorkers = [ordered]@{ original = "$mwReferenceBuild/Release/mw34_m4_reference.exe" }
$mwRuntimeWorkers = [ordered]@{}
Invoke-MWTool $mwCMake @('-S', $PSScriptRoot, '-B', $mwReferenceBuild, '-G', 'Visual Studio 18 2026', '-A', 'Win32') "$mwOutput/reference-configure.log"
Invoke-MWTool $mwCMake @('--build', $mwReferenceBuild, '--config', 'Release') "$mwOutput/reference-build.log"
Invoke-MWTool $mwWorkers.original @('--check-protocol') "$mwOutput/original-protocol.log"
Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_public_worker.py", '--worker', $mwWorkers.original) "$mwOutput/original-public-controls.log"
Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_staging.py", '--worker', $mwWorkers.original, '--output', "$mwOutput/original-staging-controls.json") "$mwOutput/original-staging-controls.log"
foreach ($mwLevel in @('O0', 'O2')) {
    Invoke-MWTool "$LLVMRoot/bin/llvm-nm.exe" @('--undefined-only', "$mwOutput/native-$mwLevel.obj") "$mwOutput/native-$mwLevel-symbols.txt"
    $mwSymbols = (Get-Content -LiteralPath "$mwOutput/native-$mwLevel-symbols.txt") | ForEach-Object {
        if ($_ -match '^\s*U\s+(\S+)\s*$') { $matches[1] } elseif ($_ -match '\S') { throw "Unexpected object symbol output: $_" }
    }
    if ((($mwSymbols | Sort-Object) -join ',') -ne 'mw34_integer_read32,mw34_integer_return,mw34_integer_tail_enter,mw34_integer_write32,mw34_integer_write8') { throw 'Native object has unreviewed imported helper/symbols' }
    $mwBuild = $mwBuildDirectories[$mwLevel]
    Invoke-MWTool $mwCMake @('-G', 'Ninja', '-S', $PSScriptRoot, '-B', $mwBuild, "-DMW34_HOST_OBJECT=$mwOutput/native-$mwLevel.obj", "-DMW34_RUNTIME_SOURCE_DIR=$mwRoot/tools/m4-runtime", "-DMW34_REMILL_INCLUDE=$RemillRoot/include", '-DCMAKE_CXX_COMPILER=clang-cl', '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG -Wno-invalid-offsetof') "$mwOutput/native-$mwLevel-configure.log"
    Invoke-MWTool $mwCMake @('--build', $mwBuild, '--parallel', '8') "$mwOutput/native-$mwLevel-build.log"
    $mwRuntimeWorkers[$mwLevel] = "$mwBuild/mw34_m4_runtime_component.exe"
    # The layout hash identifies the component under test here. This diagnostic
    # is not a production registration using a future accepted gate hash.
    Invoke-MWTool $mwRuntimeWorkers[$mwLevel] @($Image, (Get-MWHash "$mwOutput/native-$mwLevel.obj"), (Get-MWHash "$mwOutput/layout.json")) "$mwOutput/runtime-$mwLevel-integration.log"
    $mwWorkers["native-$mwLevel"] = "$mwBuild/mw34_m4_native.exe"
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--check-protocol') "$mwOutput/native-$mwLevel-protocol.log"
    Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_public_worker.py", '--worker', $mwWorkers["native-$mwLevel"], '--native') "$mwOutput/native-$mwLevel-public-controls.log"
    Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_staging.py", '--worker', $mwWorkers["native-$mwLevel"], '--output', "$mwOutput/native-$mwLevel-staging-controls.json") "$mwOutput/native-$mwLevel-staging-controls.log"
    foreach ($mwCheck in @('context', 'state-storage', 'fp-environment')) {
        Invoke-MWTool $mwWorkers["native-$mwLevel"] @("--check-$mwCheck", $mwCode, $Image) "$mwOutput/native-$mwLevel-$mwCheck.log"
    }
    Invoke-MWTool $mwWorkers["native-$mwLevel"] @('--layout') "$mwOutput/native-$mwLevel-layout.log"
    Invoke-MWTool "$LLVMRoot/bin/llvm-objdump.exe" @('--disassemble', '--x86-asm-syntax=intel', "$mwOutput/native-$mwLevel.obj") "$mwOutput/native-$mwLevel-disassembly.txt"
}
Invoke-MWTool $Python @("$mwRoot/tests/m4-integer-startup/check_runtime_integration.py", '--logs', "$mwOutput/runtime-O0-integration.log", "$mwOutput/runtime-O2-integration.log", '--output', "$mwOutput/runtime-integration-controls.json") "$mwOutput/runtime-integration-controls.log"
$mwIdentity = & $Python "$PSScriptRoot/source_identity.py" $mwRoot | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $mwIdentity.source_digest -ne $mwInitialIdentity.source_digest) { throw 'M4 source snapshot changed during compilation; preserve this run and rebuild fresh' }
$mwSources = $mwIdentity.absolute_source_files
$mwTools = [ordered]@{}
foreach ($mwTool in @('llvm-link.exe', 'llvm-objdump.exe', 'llvm-nm.exe', 'llvm-as.exe', 'opt.exe', 'llc.exe', 'clang-cl.exe', 'LLVM-C.dll')) {
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
foreach ($mwWorker in $mwRuntimeWorkers.Values) { $mwHashes[$mwWorker] = Get-MWHash $mwWorker }
$mwRecord = [ordered]@{
    schema_version = 1; profile = 'm4-integer-startup-fourteen-roots'; scope = 'Fourteen complete required integer roots and complete shared compiled tail; persistent ordered batch; full M4 remains open'
    image_path = $Image; image_sha256 = Get-MWHash $Image; code_path = $mwCode; code_sha256 = Get-MWHash $mwCode
    entry_va = 4435648; code_bytes = 389; functions = $mwSlice.functions; layout_path = "$mwOutput/layout.json"
    source_digest = $mwIdentity.source_digest; source_files = $mwSources; source_relative_files = $mwIdentity.source_files
    tool_files = $mwTools; artifacts = $mwHashes; workers = $mwWorkers; runtime_workers = $mwRuntimeWorkers; previous_gate_pins = $mwPreviousPins
    remill_commit = $mwRepair.remill_commit; llvm_version = '21.1.8'; repair_provenance_path = $mwRepairPath; repair_provenance_sha256 = Get-MWHash $mwRepairPath
    guest_ir_sha256 = Get-MWHash "$mwOutput/guest.ll"; host_ir_sha256 = Get-MWHash "$mwOutput/host.ll"
    target_triples = @('i686-pc-windows-msvc', 'x86_64-pc-windows-msvc'); optimization_levels = @('llc -O0', 'opt default<O2>; llc -O2')
    fast_math = $false; static_native_translation = $true; semantic_repairs = @(); commands = $mwCommands.ToArray()
}
$mwRecord | ConvertTo-Json -Depth 15 | Set-Content -Encoding utf8 "$mwOutput/build.json"
if ($RunComparison) { Invoke-MWTool $Python @("$PSScriptRoot/compare.py", '--build', "$mwOutput/build.json", '--out', "$mwOutput/comparison") }
