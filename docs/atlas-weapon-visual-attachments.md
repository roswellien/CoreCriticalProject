# Atlas level forearms and weapon visuals

Execution boundary: selected owned-chassis external forearm geometry and the
presentation of its two original arm beams. Original weapon creation, updates,
collision, damage, heat, ammunition and RNG execute in their existing translated
bodies. The adapter reads their state and produces host draw commands and tracked
lights. The existing simulation socket adapter is unchanged and the candidate
Atlas pack contains no simulation sockets.

The level-forearm candidate is a local development asset. It rotates each complete
forearm assembly about the accepted elbow with corresponding bind/rest frames;
upper arms, shoulder spacing, body and leg animation retain their accepted data.
The local export check covered 666 actual original pose samples, both LODs and
independent mesh muzzle/axis landmarks. Generated meshes, textures, original
resources, static original-code exports and native captures remain local.

## Admission and ownership

Selected New alternatives can carry an inline schema 1 `weapon_attachments` table
for close/distance. Each table binds the complete loaded mesh/UV identity and at
most 64 unique source-control/weapon-definition keys to rigid forearm-local muzzle
positions. Both LODs must carry ordered matching keys. Python, C# and native mesh
admission validate their applicable identity, rig, bounds and resource contracts.
Only selected tables require `owned-chassis-weapon-visuals:1` and MWCHAS8. Older
catalog forms and Original admission retain their existing requirements. No
published runtime profile is changed to advertise this capability.

For the native player factory, the successful 0x584A70 return at 0x4B3FA5 retains its
weapon record in ESI. Authenticate definition, position/direction pointers,
manager membership, unique definition/control key, source actor root, mount
ancestry, firepoint profile and segment node. Start/restart assigns a fresh host
generation. Every deferred descriptor copies that full identity; pointer reuse
alone cannot authorize a draw. Stop, destruction, arm loss, actor retirement and
world/frontend changes retire the corresponding host snapshots and light tokens.

The original first segment supplies source S and hit endpoint E; current policy3
pose plus the mesh-bound attachment supplies D. A host affine shear maps S to D
and fixes E, preserving the original transverse geometry. Later segments retain
the original renderer. Reconstruct before near clipping so a newly visible source
does not depend on an old visible draw. CPU clipping interpolates UV, RGBA and
fog; it shares the existing fixed-capacity clipping kernel with missile exhaust.
Eligible fully visible uniform-color, unfogged polygons can use ModelInstance.
Other polygons use the attribute-preserving CPU path. No shader changes are made.

## Deferred views and effects

A view includes target, scene serial, role, camera matrix, projection, attached/
external policy and original camera producer. Original camera activation or an
actual world producer establishes the view independently of Sun lighting.
Cockpit/Original fallback passes original commands through. External views rebuild
from authenticated live source geometry, material and current device state.

Immutable host snapshots bracket the original 0x57E110 flush. Preparation validates
all replacements before suppressing verified first-segment commands. Replacement
and unaffected translucent commands use the original 0x57DEC0 signed first-TL-depth
ordering, preserving equal-key original order and commands outside that flush.
Different actors and actual views remain distinct; repeated identical views do
not emit duplicate geometry. Only this beam's authenticated material observations
become tracked lights. Shared particles and impacts retain their existing paths.

## Evidence and current limits

Static interpretations were checked against the local original MW3 1.2 executable
SHA256 95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf.
Original entry names remain `sub_` in the symbol table. Local source-projection
checks matched 180 vertices within 0.001772 pixels; source-style checks matched all
180 UV/RGBA/fog vertices after preserving the original mesh-sphere fog gate.
These checks cover the observed ERLaser_Large resource, not arbitrary effects.

The native development preview demonstrates level hands and aligned right-hand
firing with enhanced textures, normals, sky and red eyes. The maintained host and
private camera derivative have separately pinned source/executable receipts;
the translated module remains unchanged. A camera capture is not release or
simulation-equivalence acceptance.

The second original factory0x4AF2A0 is not yet authenticated. Unknown required
selected ownership fails visibly. Original global uniform lighting0x74A270 is
explicitly unsupported by the cold source-material decoder; it is lighting, not
fog, and is not silently approximated. Both-actor native firing, native arm-loss,
zoom, original-culled/new-visible, full CPU/GPU equivalence and gameplay-state A/B
acceptance remain required before enabling this candidate in a public runtime.
The draft PR and local preview do not claim those gates passed. No video or
published pack is replaced by this implementation.
