# Isolated D7VK evaluation fixture

Project-authored, asset-free DirectDraw4 / IDirect3D3 / IDirect3DDevice3
exercise. It dynamically loads an explicitly supplied graphics DLL, creates a
hidden normal-cooperative-level window, and checks offscreen RGB565 output.
It never loads or executes MW3. It is separate from the production runtime and
is not included in the root build.

The missing criterion addressed here is whether an existing Vulkan compatibility
provider preserves the surface contents across GPU draws, partial depth fills,
CPU locks, texture updates, and GDI writes needed by our recovered graphics
boundary. This is a narrow sampled-pixel check, not full-frame equivalence.

The fixture exercises six scene intervals with transformed 32-byte vertices,
triangle fans, FVF `0x1C4` and draw flags `0x18`. It checks eleven exact RGB565
pixels across full/partial D16 zero fills, preservation of CPU/GDI writes through
later draws, and reuse of an updated texture. Depth comparison, dimensions,
colors and normal window mode are authored choices, not recovered game settings.
No Flip, primary-surface presentation, resize, fullscreen transition, color-key,
fog, blend, palette, mipmap or guest ABI behavior is verified.

Build with Visual Studio CMake (use its absolute path if absent from PATH):

```powershell
cmake -S tools/d7vk-evaluation -B build/d7vk-evaluation-win32 -G 'Visual Studio 18 2026' -A Win32
cmake --build build/d7vk-evaluation-win32 --config Release --parallel 1
```

Run from a fresh ignored working directory so provider logs remain local:

```powershell
$taskFixture = 'D:/Projects/MW34Recomp/build/d7vk-evaluation-win32/Release/mw34_d7vk_fixture.exe'
$taskProvider = 'D:/Projects/MW34Recomp/local/work-ahead/d7vk-evaluation/release-v2.3/d7vk-v2.3/x32/ddraw.dll'
# Change to a fresh local/work-ahead/... directory before running.
& $taskFixture $taskProvider
if ($LASTEXITCODE -ne 0) { throw 'Graphics fixture failed' }
```

Require an absolute DLL path. The fixture returns 1 on a graphics/pixel failure,
2 on invalid argument count and 3 if the DLL cannot be loaded. It does not
substitute a provider after failure. Build with `-A x64` into another directory
when evaluating an actual x64 provider; the v2.3 x32 release cannot load there.

See the [evaluation](../../docs/d7vk-evaluation-r1.md) for source/binary identities,
retained failures and the adaptation decision. Do not copy this DLL into the
existing game installation or system directory for this fixture.
