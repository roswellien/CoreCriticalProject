# FSR Vulkan feasibility probe

This standalone diagnostic fills the missing SDK/provider compatibility criterion
for [FidelityFX stage 1](../../docs/fidelityfx-feasibility-2026-10-29.md). It never
loads original game code or dispatches an image. It is not linked into the host.

## Inputs and build

Use LLVM 21.1.8, Visual Studio C++ Build Tools, Windows SDK and Vulkan-Headers
1.4.321, matching the maintained host's toolchain. `dependencies.json` pins the
SDK source, archive and consumed SDK/Vulkan files. The SDK is an external local
input; do not commit its archive, headers or DLLs to this directory.

Download the archive URL in that manifest and verify its SHA-256 before extracting.
Only the listed SDK files are needed, preserving their paths beneath
`Kits/FidelityFX/`. Sample/media assets are unnecessary. Upstream archive URLs can
be regenerated: a changed digest requires a reviewed dependency update, not an
automatic bypass. The signed DLLs have separate redistribution terms in the
pinned `docs/license.md`; headers carry their own notices.

```powershell
pwsh -File tools/fidelityfx-probe/build_probe.ps1 `
  -SdkDirectory C:/Dev/FSR/Kits/FidelityFX `
  -VulkanInclude C:/Dev/Vulkan-Headers-1.4.321/include `
  -LLVMDirectory C:/Dev/LLVM-21.1.8/bin `
  -OutputDirectory C:/Dev/fsr-probe
C:/Dev/fsr-probe/probe.exe C:/Dev/FSR/Kits/FidelityFX/signedbin 0
```

The builder checks file pins and DLL signatures before compiling. Run from a
fresh output directory with no other FSR DLLs next to the executable: the upstream
loader searches the executable directory before its own directory. The builder
rejects an existing output directory rather than reusing its contents. Keep the DLLs
unchanged between build verification and execution. No SDK import library is
needed; the probe dynamically loads three exported entry points.

The second argument is the enumerated GPU index. Every run prints the device list.
An unavailable SDK, invalid GPU or failed API call exits nonzero. A successful run
queries each compatible upscaler, its required resources and memory usage, and
creates/destroys its real context at 1280x720 input / 1920x1080 output.

## Scope of results

The probe requests Vulkan 1.3, a compute queue and all supported core 1.1/1.2/1.3
features. This deliberately broad profile establishes feasibility, not a minimal
production feature set. It requests no device extensions. The native renderer
still uses its existing device policy. Later dispatch integration must narrow
features and validate synchronization and formats on the actual host device.

Sampled-format checks cover RGBA16F, RG16F, R32F and D32F. They do not allocate
application input/output images or validate storage-image usage. The contexts
allocate SDK-owned resources; no shader dispatch, Vulkan validation-layer pass,
presentation, image-quality or latency result is claimed.

Known failures release resources through diagnostic process teardown; successful
contexts and devices are explicitly destroyed. This is not a production recovery
strategy. No public FSR option or runtime fallback behavior is added here.
