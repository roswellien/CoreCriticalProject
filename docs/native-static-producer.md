# Development static geometry producer

Issue #177 introduces an opt-in native producer, `MW34_GPU_STATIC_PRODUCER=1`.
It is disabled by default. It builds on the resident world geometry and temporal
source contracts. It does not enable FSR upscaling or frame generation.

For an admitted static mesh, native code submits the existing immutable resident
geometry without generating or uploading a transformed/lit vertex stream. The
vertex shader projects raw positions and computes the original packed fog alpha.
The established modern per-pixel lighting path already owns RGB. Original cell
and LOD dispatch, matrix stack operations, mesh light/fog selection and the
fog-colour callback remain. CPU face visibility remains in this first slice.

Admission requires an opaque, static, normal-free mesh with decoded polygons,
supported material and provider-owned textures, a fully unclipped bounding box,
a supported positive fog range and a bounded light domain. Alternate renderers,
animation, morphing, transparent/deferred materials, zoom and replay retain the
established recompiled producer. Unknown required state is not invented. A
contract violation after native execution starts stops visibly.

The existing world-present receipt records native mesh, polygon and source
vertex counts and admission rejections. Equal captures with no admission during
the tested interval do not demonstrate a performance improvement.

## Original helper evidence

These contracts refer to the supported MW3 US 1.2 image, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Original bytes and decompilation remain local. These are bounded static
contracts, not whole-game equivalence claims.

| Function | Confirmed operation and native obligation |
| --- | --- |
| `sub_0051E9D0` (RVA `0011E9D0`) | Advances both matrix-stack pointers and installs the scratch matrix supplied in ECX. Native execution calls the recompiled helper. |
| `sub_0051FB30` (RVA `0011FB30`) | Composes the current view and prior stack matrix into the new scratch matrix. Native execution calls the recompiled helper. |
| `sub_0051EA00` (RVA `0011EA00`) | Pops both matrix-stack pointers. Native execution calls the recompiled helper. |
| `sub_0053DAA0` (RVA `0013DAA0`) | Selects mesh fog/light contributions and initializes dependent light state. Call site `0053F86C` passes the mesh header in ECX. Native execution calls the recompiled helper. |
| `sub_00543D90` (RVA `00143D90`) | Selects mesh light contributions. For the supported inactive point-light form `0x52`, it clears both contribution words; the active form is `0x252`. Native admission distinguishes these exact forms and retains this helper through the original mesh selection call. |
| `sub_00555A70` (RVA `00155A70`) | Computes per-vertex radial/height fog and conditionally updates fog colour through its callback. Native shader reproduces fog packing; native host retains the colour callback effect. |

The fog radius uses an exponent-based approximation rather than `sqrt`. Fog
packing rounds with `255.5 - 255 * fog` before truncating. The shader preserves
float32 storage boundaries with double intermediates and therefore requires
Vulkan `shaderFloat64` when this experimental option is enabled.

## Focused fixture

The existing world geometry fixture accepts `--native-static`. Eight authored
cases compare the resident-only shader with independently specified packed fog
bytes through the established shader. It checks full-resolution RGB8 as well
as RGB565 and depth, requires positive geometry, and verifies reuse across two
immutable geometry revisions. RGB565 alone can hide a one-byte fog error.

Deliberately replacing the radius approximation with `sqrt`, or changing
packing from `255.5` to `255.0`, must fail this fixture. Native Training capture
and performance evidence are separate from this authored GPU check. Broader
terrain, near-plane, animated and material coverage remains subsequent work.
