# Vulkan learning prototype

Standalone authored experiment, separate from native game startup. Enumerates
devices and selected advertised extensions, creates a Vulkan 1.0 logical device
and graphics queue, fills four regions of a host-visible buffer on the GPU,
applies a transfer-write to host-read barrier, waits on a fence and checks all
65,536 words. Writes a 256x256 PPM swatch from the verified readback.

This is a transfer/bootstrap prototype, not a raster renderer. No shaders,
surface, swapchain, game assets, ray tracing or validation layers are used.
Extension advertisement alone does not establish usable ray-tracing features.
Host-visible coherent memory is required; other memory paths fail explicitly.
Windows and Linux loader paths exist; only Windows x64 has been exercised.
The Vulkan 1.0 request minimizes bootstrap requirements; the eventual renderer's
minimum API/features remain to be chosen from measured requirements.

## Build

Requires a C++20 compiler and Khronos Vulkan headers. The loader is opened at
runtime; an SDK import library is unnecessary. The experiment used header tag
`v1.4.321`, commit `2cd90f9d20df57eac214c148f3aed885372ddcfe`, cloned into ignored
`local/tools/vulkan-headers-v1.4.321`. No third-party headers are vendored.

From the repository root with CMake available:

```powershell
cmake -S tools/vulkan-probe -B build/vulkan-probe-cmake -DVULKAN_HEADERS="$PWD/local/tools/vulkan-headers-v1.4.321/include" -DGLSLANG_VALIDATOR="$PWD/local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
cmake --build build/vulkan-probe-cmake --config Debug
New-Item -ItemType Directory -Force reports/vulkan-probe | Out-Null
./build/vulkan-probe-cmake/Debug/mw34_vulkan_probe.exe reports/vulkan-probe/swatch.ppm
```

For a single-configuration generator, the executable is directly in the build
directory. Linux requires `libvulkan.so.1`; Windows uses the system loader.
The actual first Windows run used MSVC 14.51 with `/std:c++20 /EHsc /W4 /WX`.

## Static MW3 graphics leads

```powershell
python tools/vulkan-probe/recover_guids.py MW3/Mech3.exe "C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um" reports/vulkan-probe/mw3-guid-leads.json
```

The tool validates the admitted executable identity before scanning exact GUID
definitions from the local SDK's `ddraw.h` and `d3d.h`. Reports pin input/header
hashes and record mapped offsets. A static match is a lead, not proof that the
game requests or uses that interface. Absence is not proof of non-use.
Keep output under ignored reports; do not commit game-derived traces/assets.

See [the investigation record](../../docs/vulkan-learning-prototype.md).

## Textured raster experiment

The standalone CMake project now also builds `mw34_vulkan_raster` and its two
SPIR-V shaders. A glslang compiler is required at configure time. The accepted
Windows run uses locally extracted LunarG 1.4.321.0 tools, without an SDK install.
Khronos validation and synchronization validation are required, not optional.

```powershell
./tools/vulkan-probe/run-raster.ps1 -Executable build/vulkan-probe-cmake/Debug/mw34_vulkan_raster.exe -ShaderDirectory build/vulkan-probe-cmake
```

The runner exercises default, depth-off, fog-off and opaque-front modes, then
checks all pixels through the independent oracle. It isolates implicit overlays
only for its child process and restores the previous environment. Raw executable
success means validation passed; pixel acceptance additionally requires the
oracle. PPM outputs are authored four-quadrant diagnostic images, not game frames.
See [the raster acceptance record](../../docs/vulkan-raster-prototype.md).
