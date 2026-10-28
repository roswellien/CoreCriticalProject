# 32-bit main depth upgrade

The user authorized moving the playable native renderer to 32-bit depth after
Strider motion tests demonstrated surface visibility errors with the existing
16-bit depth attachment. This changes rendering precision, not game simulation.

`tools/remaster-launcher/apply_depth32.py` applies the upgrade to a prepared host
source directory. The world-lighting integration also calls it. It changes the
main render pass, physical depth image and guest-resolution staging depth image
to `D32_SFLOAT`. Shadow maps retain their separate existing capability policy.
Required floating-point depth attachment and blit support is checked explicitly;
unsupported hardware reports an error rather than silently reverting to D16.

Original guest depth surfaces and `Scene::depth` remain 16-bit. The authored
`depth_transfer.hpp` converts normalized values to float on upload and rounds
them back on an actual guest readback. Staging allocations use four bytes per
depth sample and align the depth offset to four bytes, including odd pixel
counts. GPU-resident passes retain full precision between scenes. Guest reads
necessarily return the original 16-bit representation. No shaders, gameplay,
model geometry, textures, normals, lighting strengths or launcher labels change.

## Local build and checks

The candidate preserves the active all-18-model host, including the newer Owens
and Firefly registrations, along with the previous display, input, file-failure
and damage-display repairs. Private build/evidence: `local/depth32-r1`.
Executable SHA256:
`7edfe73a041c108a2072b53f8c9271e1dcc0ab438b1071de387cb814d0fb3ea6`.
Its source snapshot identifies the preceding build and pins the actual sources.

- `test_depth32.cpp` uses the actual Vulkan renderer: every guest depth value
  survives upload/readback; colour transfers, odd dimensions, doubled output,
  2x/4x SSAA, GPU-resident depth, resident fetch and depth clears pass. All 64
  close-surface positions retain the nearer surface.
- The actual Strider torso precision stress test now uses the production
  conversion/rendering path. Strong pixel differences across 64 views fall
  from 1,016,049 with D16 to 31 with D32 at the tested depth distribution.
  These are stress-test inputs, not measured campaign camera depths.
- The existing damage-colour fixture passes for both status displays and the
  healthy-component/world-haze controls. The display fixture passes at
  3440x1440 with FXAA and correct guest copy-back/scissors.
- Native run `local/remaster/runs/20261020-095647-196` executes the menu and
  Instant Action at 3440x1440, FXAA and 16x AF, with original simulation, world,
  replacement meshes and HUD. Inspected frame 1600; retained high-resolution
  frames 1200 and 1600. The hidden-window test ends at its explicit 2200-frame
  budget (exit 1 with the expected budget diagnostic), not an unexpected crash.
- Launcher profile/model checks pass for all 18 models and current registrations.

This advances the native graphics precision boundary. It does not prove that
every reported flicker has the same cause, complete a campaign playthrough,
establish performance across devices, or add formal acceptance credit.
Acceptance remains **131/144**. User saves/settings are protected by private
game and registry copies during the native test. No commit is requested.
