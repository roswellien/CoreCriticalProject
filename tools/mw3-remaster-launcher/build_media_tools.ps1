param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$CMake = 'C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe',
    [string]$Generator = 'Visual Studio 18 2026'
)
$ErrorActionPreference = 'Stop'
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outputRoot) { throw 'Use a new dependency build directory; existing evidence is preserved.' }
if (-not (Test-Path -LiteralPath $CMake -PathType Leaf)) { throw 'Select an installed CMake and Visual Studio C++ toolchain.' }
New-Item -ItemType Directory -Path $outputRoot | Out-Null
$sources = @(
    @{name='zlib-1.3.2'; archive='zlib.tar.gz'; url='https://zlib.net/fossils/zlib-1.3.2.tar.gz'; sha256='bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16'},
    @{name='unshield-51de441ba6893f11026d4671ccef9e8e2a4634fa'; archive='unshield.tar.gz'; url='https://codeload.github.com/twogood/unshield/tar.gz/51de441ba6893f11026d4671ccef9e8e2a4634fa'; sha256='4bb95bd438faa717a05eda658a324562ce4e4243372a5d19e47f7e01634f7fe2'}
)
foreach ($source in $sources) {
    $archive = Join-Path $outputRoot $source.archive
    Invoke-WebRequest -Uri $source.url -OutFile $archive
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ine $source.sha256) { throw 'Dependency source hash mismatch.' }
    & tar -xf $archive -C $outputRoot
    if ($LASTEXITCODE) { throw 'Dependency source extraction failed.' }
}
function Invoke-CMake([string[]]$Arguments) {
    & $CMake @Arguments
    if ($LASTEXITCODE) { throw 'Dependency configure/build failed.' }
}
$zlibSource = Join-Path $outputRoot $sources[0].name
$zlibBuild = Join-Path $outputRoot 'zlib-build'
$unshieldSource = Join-Path $outputRoot $sources[1].name
$unshieldBuild = Join-Path $outputRoot 'unshield-build'
Invoke-CMake -Arguments @('-S', $zlibSource, '-B', $zlibBuild, '-G', $Generator, '-A', 'x64',
    '-DZLIB_BUILD_SHARED=OFF', '-DZLIB_BUILD_STATIC=ON', '-DZLIB_BUILD_TESTING=ON',
    '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded', '-DCMAKE_C_FLAGS=/Brepro', '-DCMAKE_STATIC_LINKER_FLAGS=/Brepro')
Invoke-CMake -Arguments @('--build', $zlibBuild, '--config', 'Release', '--parallel', '2')
Invoke-CMake -Arguments @('-S', $unshieldSource, '-B', $unshieldBuild, '-G', $Generator, '-A', 'x64',
    '-DBUILD_STATIC=ON', '-DBUILD_TESTING=OFF', '-DUSE_OUR_OWN_MD5=ON', '-DCMAKE_DISABLE_FIND_PACKAGE_OpenSSL=TRUE',
    '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded', '-DCMAKE_C_FLAGS=/Brepro', '-DCMAKE_EXE_LINKER_FLAGS=/Brepro',
    '-DCMAKE_STATIC_LINKER_FLAGS=/Brepro', "-DZLIB_INCLUDE_DIR=$zlibSource", "-DZLIB_LIBRARY=$zlibBuild/Release/zs.lib")
Invoke-CMake -Arguments @('--build', $unshieldBuild, '--config', 'Release', '--target', 'unshield', '--parallel', '2')
$ctest = Join-Path (Split-Path $CMake) 'ctest.exe'
& $ctest --test-dir $zlibBuild -C Release --output-on-failure
if ($LASTEXITCODE) { throw 'zlib dependency tests failed.' }
$payload = Join-Path $outputRoot 'payload'
New-Item -ItemType Directory -Path $payload | Out-Null
Copy-Item -LiteralPath (Join-Path $unshieldBuild 'src/Release/unshield.exe') -Destination $payload
Copy-Item -LiteralPath (Join-Path $unshieldSource 'LICENSE') -Destination (Join-Path $payload 'LICENSE-unshield.txt')
Copy-Item -LiteralPath (Join-Path $zlibSource 'LICENSE') -Destination (Join-Path $payload 'LICENSE-zlib.txt')
$files = @{}
foreach ($file in Get-ChildItem -LiteralPath $payload -File) {
    $files[$file.Name] = @{bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
@{schema_version=1; sources=$sources; generator=$Generator; cmake=(& $CMake --version | Select-Object -First 1);
  recipe_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash.ToLowerInvariant(); files=$files;
  linkage='static libunshield, zlib and MSVC runtime'; tests='zlib CTest passed';
  scope='Source build recipe and output identity; not a promise of identical binaries across toolchains/paths.'} |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $payload 'provenance.json') -Encoding utf8
Write-Output "Built media tools: $payload. Review the exact executable identity before updating admission."
