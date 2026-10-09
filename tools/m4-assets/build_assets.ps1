param(
    [string]$OutputDirectory = 'D:/Projects/MW34Recomp/reports/m4-assets/parser-r1',
    [string]$Archive = 'D:/Projects/MW34Recomp/MW3/zbd/reader.zbd',
    [string[]]$Entries = @('dialog.zrd','detail.zrd','fonts.zrd','sounds.zrd'),
    [string]$Label = 'MAINMENU',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
    [string]$LLVMRoot = 'D:/Projects/MW34Recomp/local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc'
)
$ErrorActionPreference = 'Stop'
$mwAssetRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$mwAssetOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
$mwAssetReports = Join-Path $mwAssetRoot 'reports/m4-assets'
if (-not $mwAssetOutput.StartsWith($mwAssetReports + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Asset output must be a fresh private M4-assets directory' }
$mwAssetName = Split-Path $mwAssetOutput -Leaf
if ($mwAssetName -notmatch '^[a-z][a-z0-9-]{0,63}$' -or $mwAssetName -match '^(con|prn|aux|nul|com[0-9]|lpt[0-9])$') { throw 'Invalid asset experiment name' }
$mwAssetBuild = Join-Path $mwAssetRoot "build/m4-assets-$mwAssetName"
# Both guards precede input/tool/source reads and every write. Sequential,
# private ordinary directories only; these are not atomic publisher guards.
if (Test-Path -LiteralPath $mwAssetOutput) { throw 'Asset report output already exists' }
if (Test-Path -LiteralPath $mwAssetBuild) { throw 'Asset derived build already exists' }
function Get-MWAssetHash([string]$Path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
function Get-MWAssetSources {
    $mwAssetSources = [ordered]@{}
    $mwAssetCandidates = @(
        Get-ChildItem -LiteralPath $PSScriptRoot -Recurse -File
        Get-ChildItem -LiteralPath (Join-Path $mwAssetRoot 'tests/m4-assets') -Recurse -File
        Get-Item -LiteralPath (Join-Path $mwAssetRoot 'docs/m4-assets-contract.md')
        Get-Item -LiteralPath (Join-Path $mwAssetRoot 'tools/m4-startup/admission.hpp')
    ) | Where-Object { $_.Extension -in @('.cpp','.hpp','.py','.ps1','.txt','.md') -and $_.FullName -notmatch '__pycache__' } | Sort-Object FullName
    foreach ($mwAssetFile in $mwAssetCandidates) { $mwAssetSources[$mwAssetFile.FullName] = Get-MWAssetHash $mwAssetFile.FullName }
    return $mwAssetSources
}
$mwAssetArchiveBefore = Get-MWAssetHash $Archive
if ($mwAssetArchiveBefore -ne '5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a') { throw 'Unsupported installed reader asset identity' }
$mwAssetInitialSources = Get-MWAssetSources
New-Item -ItemType Directory -Path $mwAssetOutput | Out-Null
$mwAssetSourceCopies = [System.Collections.Generic.List[object]]::new()
foreach ($mwAssetSourcePath in $mwAssetInitialSources.Keys) {
    $mwAssetRelative = [System.IO.Path]::GetRelativePath($mwAssetRoot, $mwAssetSourcePath)
    $mwAssetPreservedPath = Join-Path (Join-Path $mwAssetOutput 'sources') $mwAssetRelative
    New-Item -ItemType Directory -Force -Path (Split-Path $mwAssetPreservedPath) | Out-Null
    Copy-Item -LiteralPath $mwAssetSourcePath -Destination $mwAssetPreservedPath
    if ((Get-MWAssetHash $mwAssetPreservedPath) -ne $mwAssetInitialSources[$mwAssetSourcePath]) { throw 'Literal asset source copy changed' }
    $mwAssetSourceCopies.Add([ordered]@{ original_path=$mwAssetSourcePath; preserved_path=$mwAssetPreservedPath; sha256=$mwAssetInitialSources[$mwAssetSourcePath] })
}
$mwAssetCommands = [System.Collections.Generic.List[object]]::new()
function Invoke-MWAssetTool([string]$Program, [string[]]$Arguments, [string]$Log) {
    $mwAssetSavedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Program @Arguments 2>&1 | Tee-Object -FilePath $Log; $mwAssetExit = $LASTEXITCODE }
    finally { $ErrorActionPreference = $mwAssetSavedPreference }
    $mwAssetCommands.Add([ordered]@{ program=$Program; arguments=$Arguments; exit_code=$mwAssetExit; log_path=$Log; log_sha256=(Get-MWAssetHash $Log) })
    if ($mwAssetExit -ne 0) { throw "Asset tool failed: $Program (exit $mwAssetExit)" }
}
$mwAssetPassed = $false
try {
    Import-Module (Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $VSRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
    $mwAssetCMake = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
    $mwAssetCTest = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe'
    $mwAssetNinja = Join-Path $VSRoot 'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
    $env:PATH = "$LLVMRoot/bin;$(Split-Path $mwAssetNinja);$env:PATH"
    $mwAssetTemp = Join-Path $mwAssetOutput 'compiler-temp'; New-Item -ItemType Directory $mwAssetTemp | Out-Null
    $env:TEMP = $mwAssetTemp; $env:TMP = $mwAssetTemp; $env:TMPDIR = $mwAssetTemp
    Invoke-MWAssetTool $mwAssetCMake @('-G','Ninja','-S',$PSScriptRoot,'-B',$mwAssetBuild,'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_COMPILER=$LLVMRoot/bin/clang-cl.exe",'-DCMAKE_CXX_FLAGS_RELEASE=/O2 /DNDEBUG') (Join-Path $mwAssetOutput 'configure.log')
    Invoke-MWAssetTool $mwAssetCMake @('--build',$mwAssetBuild,'--parallel','8') (Join-Path $mwAssetOutput 'build.log')
    Invoke-MWAssetTool $mwAssetCTest @('--test-dir',$mwAssetBuild,'--verbose','--output-on-failure','--no-tests=error','--output-junit',(Join-Path $mwAssetOutput 'ctest.xml')) (Join-Path $mwAssetOutput 'ctest.log')
    $mwAssetHost = Join-Path $mwAssetBuild 'mw34_m4_assets.exe'
    $mwAssetCheckArgs = @((Join-Path $mwAssetRoot 'tests/m4-assets/check_assets.py'),'--host',$mwAssetHost,'--archive',$Archive,'--out',(Join-Path $mwAssetOutput 'actual-controls'))
    foreach ($mwAssetEntry in $Entries) { $mwAssetCheckArgs += @('--entry',$mwAssetEntry) }
    if ($Label) { $mwAssetCheckArgs += @('--label',$Label) }
    Invoke-MWAssetTool $Python $mwAssetCheckArgs (Join-Path $mwAssetOutput 'actual-controls.log')
    if ((Get-MWAssetSources | ConvertTo-Json -Compress) -ne ($mwAssetInitialSources | ConvertTo-Json -Compress)) { throw 'Asset sources changed during build; preserve attempt and rebuild fresh' }
    if ((Get-MWAssetHash $Archive) -ne $mwAssetArchiveBefore) { throw 'Original read-only asset input changed' }
    $mwAssetPassed = $true
} catch {
    $mwAssetFailure = $_.Exception.Message
    throw
} finally {
    $mwAssetArtifacts = [ordered]@{}
    foreach ($mwAssetFile in @(
        Get-ChildItem -LiteralPath $mwAssetOutput -Recurse -File
        if (Test-Path -LiteralPath $mwAssetBuild) { Get-ChildItem -LiteralPath $mwAssetBuild -Recurse -File | Where-Object { $_.Extension -in @('.exe','.obj','.lib','.cmake','.json') -or $_.Name -in @('build.ninja','rules.ninja','CMakeCache.txt','.ninja_log') } }
    ) | Sort-Object FullName) {
        if ($mwAssetFile.FullName -notmatch 'compiler-temp') { $mwAssetArtifacts[$mwAssetFile.FullName] = Get-MWAssetHash $mwAssetFile.FullName }
    }
    $mwAssetTools = [ordered]@{}
    foreach ($mwAssetTool in @($Python,$mwAssetCMake,$mwAssetCTest,$mwAssetNinja,(Get-Process -Id $PID).Path,(Join-Path $VSRoot 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')) + @('clang-cl.exe','llvm-lib.exe','lld-link.exe','llvm-mt.exe' | ForEach-Object { Join-Path $LLVMRoot "bin/$_" })) {
        if ($mwAssetTool -and (Test-Path -LiteralPath $mwAssetTool)) { $mwAssetTools[$mwAssetTool] = Get-MWAssetHash $mwAssetTool }
    }
    foreach ($mwAssetSDKFile in @('C:/Program Files (x86)/Windows Kits/10/bin/10.0.26100.0/x64/rc.exe','C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/bcrypt.h','C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/Windows.h')) {
        if (Test-Path -LiteralPath $mwAssetSDKFile) { $mwAssetTools[$mwAssetSDKFile] = Get-MWAssetHash $mwAssetSDKFile }
    }
    [ordered]@{ schema_version=1; passed=$mwAssetPassed; failure=$mwAssetFailure; experiment='Native read-only reader archive/binary token parser prerequisite'; milestone_M4_complete=$false;
        source_files=$mwAssetInitialSources; literal_source_copies=@($mwAssetSourceCopies); tool_files=$mwAssetTools; artifacts=$mwAssetArtifacts; commands=@($mwAssetCommands);
        archive_path=$Archive; archive_sha256_before=$mwAssetArchiveBefore; archive_sha256_after=(Get-MWAssetHash $Archive);
        original_x86_executed=$false; widget_callbacks_executed=$false; guest_reader_object_implemented=$false; native_startup_or_menus_complete=$false
    } | ConvertTo-Json -Depth 16 | Set-Content -Encoding utf8 -LiteralPath (Join-Path $mwAssetOutput 'build.json')
}
Write-Output "Asset parser prerequisite passed; original widget/service integration remains open. $(Join-Path $mwAssetOutput 'build.json')"
