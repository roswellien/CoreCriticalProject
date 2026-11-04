# mw3-re Vulkan development adapter

This Windows x64 experiment builds against mw3-re v1.0.1 at
`abc9dbddf9104e3e5e40e34561fdb7d846611e7e`. SDL owns the window and
input. Core Critical consumes the game's live 3D and HUD draws and presents
the Vulkan color target through the same-adapter DXGI bridge.

## Build

In a Visual Studio x64 developer shell with clang-cl 21.1.8, CMake, Ninja
and the Windows SDK on PATH, run:

```powershell
pwsh -NoProfile -File tools/mw3-re-renderer/build.ps1 -UpstreamSource $upstream -OutputRoot $trialRoot -SdlDependencies $sdlDependencies -VulkanHeaders $vulkanHeaders -Glslang $glslang
ctest --test-dir "$trialRoot/build" -R '^cc_mw3_re_adapter$' --output-on-failure
```

`$upstream` is a local checkout of the pinned commit. `$trialRoot` is a fresh
path outside either checkout. `$sdlDependencies` contains the Windows x64
development packages SDL 3.4.12, SDL_ttf 3.2.2 and SDL_sound 3.2.0 in their
versioned directories. `$vulkanHeaders` is the Vulkan include directory,
and `$glslang` is the path to glslangValidator. The build writes only into
the new output directory.

## Run

Use verified retail 1.2 files in `$game`, the local Windows Fonts directory
in `$fonts`, and a fresh writable profile in `$run`:

```powershell
& "$trialRoot/build/mw3.exe" --cc-vulkan --install $game --assets $fonts --write-dir $run --ready-file "$run/ready" --no-launcher --no-mods --original --no-wide-menus --no-import --no-vfw-helper --window 960x720 --mission t1 --seed 2718 --frame-ms 33 --frames 120 -nofmv
```

Run the D3D12 control with a different writable profile, with
`SDL_GPU_DRIVER=direct3d12` and the adapter switch omitted. This experiment
supports windowed rendering. The ready marker requires a real DXGI present.
The bridge can bind using a readback/upload of the first completed frame.
Subsequent visible frames use the resident target.

## Lighting comparison

The opt-in material pass replaces the stock lighting of one named opaque
surface. Other draws, simulation, fog and HUD follow the stock path.
The supported trial selects the Training Mad Cat's left calf using the
node name, texture name and hash of the live RGBA albedo.

For a matched external view, add `--tap 0x2d@90:94` to the Training
command. Use a fresh profile for each run. For the Off control, leave
`--cc-lighting` unset. For a geometric-normal comparison, add:

```text
--cc-lighting flat --cc-node lcalf --cc-texture mcat04 --cc-albedo-hash 396112bbfff8379a
```

Use `--cc-lighting normal` with the same selection and
`--cc-normal-map $normalMap` for the authored normal comparison. The local
BWNRM2 sidecar must contain one bound linear tangent-space image named `mcat04`.
Use `pack_normals` in [normal_materials.py](../remaster-launcher/normal_materials.py)
to encode it. `--cc-list-surfaces` prints bounded draw identities for
diagnostics. Invalid sidecars, albedo hashes and selections that never
reach the admitted draw fail the trial. `MW34_SUN_AZIMUTH` changes the
direction of the demonstration light for a separate matched run.

With `--shot <file.bmp> --shot-frame 180` in place of the visible frame
budget, the trial captures the Vulkan render target locally. The draw
keeps the original fog coefficient, depth and draw order. Clipped, biased,
translucent, multipass and unrecognized draws stay on the stock path. The
stock comparison is the reference for differences in raster edges and
filtering. The shared Vulkan shaders also interpolate diffuse color and fog
linearly in screen space, while the upstream shaders correct for perspective.

The integration patch applies to upstream's own source, licensed under
[its MIT license](https://github.com/telltaleatheist/mw3-re/blob/abc9dbddf9104e3e5e40e34561fdb7d846611e7e/LICENSE)
by Owen Morgan. Retain the upstream license in the disposable checkout.
Original media, dependencies and generated binaries remain local.
