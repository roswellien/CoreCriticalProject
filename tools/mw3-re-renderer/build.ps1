[CmdletBinding()]
param(
    [Parameter(Mandatory)][string] $UpstreamSource,
    [Parameter(Mandatory)][string] $OutputRoot,
    [Parameter(Mandatory)][string] $SdlDependencies,
    [Parameter(Mandatory)][string] $VulkanHeaders,
    [Parameter(Mandatory)][string] $Glslang,
    [ValidateRange(1, 32)][int] $Jobs = 6
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$upstreamPin = 'abc9dbddf9104e3e5e40e34561fdb7d846611e7e'
$UpstreamSource = (Resolve-Path -LiteralPath $UpstreamSource).Path
$SdlDependencies = (Resolve-Path -LiteralPath $SdlDependencies).Path
$VulkanHeaders = (Resolve-Path -LiteralPath $VulkanHeaders).Path
$Glslang = (Resolve-Path -LiteralPath $Glslang).Path
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
if ((git -C $UpstreamSource rev-parse HEAD) -ne $upstreamPin) {
    throw "Expected the mw3-re v1.0.1 commit $upstreamPin."
}
if (Test-Path -LiteralPath $OutputRoot) {
    throw "Use a fresh output directory: $OutputRoot"
}
foreach ($package in @('SDL3-3.4.12', 'SDL3_ttf-3.2.2', 'SDL3_sound-3.2.0')) {
    if (!(Test-Path -LiteralPath (Join-Path $SdlDependencies "$package/cmake"))) {
        throw "Missing $package Windows x64 development package."
    }
}
if (!(Test-Path -LiteralPath (Join-Path $VulkanHeaders 'vulkan/vulkan_core.h'))) {
    throw 'VulkanHeaders must be the include directory containing vulkan/vulkan_core.h.'
}

$source = Join-Path $OutputRoot 'source'
$build = Join-Path $OutputRoot 'build'
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
git -c core.autocrlf=false clone --no-hardlinks --no-checkout --quiet -- $UpstreamSource $source
git -C $source -c core.autocrlf=false checkout --quiet --detach $upstreamPin
$patch = Join-Path $PSScriptRoot 'upstream.patch'
git -C $source apply --check --unidiff-zero $patch
git -C $source apply --unidiff-zero $patch

$configureArgs = @(
    '-S', $source, '-B', $build, '-G', 'Ninja',
    '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_C_COMPILER=clang-cl', '-DCMAKE_CXX_COMPILER=clang-cl',
    '-DCMAKE_CXX_FLAGS:STRING=/DMW3_HAVE_LIBARCHIVE=0', '-DMW3_PACKAGE=ON',
    "-DSDL3_DIR=$SdlDependencies/SDL3-3.4.12/cmake",
    "-DSDL3_ttf_DIR=$SdlDependencies/SDL3_ttf-3.2.2/cmake",
    "-DSDL3_sound_DIR=$SdlDependencies/SDL3_sound-3.2.0/cmake",
    "-DGLSLANG=$Glslang", "-DCC_MW3_RE_ADAPTER=$PSScriptRoot", "-DCC_VULKAN_HEADERS=$VulkanHeaders"
)
cmake @configureArgs
cmake --build $build --target mw3 cc_mw3_re_adapter_checks --parallel $Jobs
