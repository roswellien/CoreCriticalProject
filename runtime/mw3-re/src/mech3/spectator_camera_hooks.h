#pragma once

// Ours (#529, docs/arena.md "Watching a match"): the watched arena match's
// spectator camera as the game's frame calls it. Set by the SDL front end
// only for a watched match (mw3 --arena without --hidden); null for every
// other run, hidden arena runs included, so they take the stock path and stay
// byte for byte as before. The hooks only place the scene camera: they never
// change a mech or the match.
namespace zcls {
struct Node;
}

namespace mech3 {

class SpectatorCameraHooks {
  public:
    virtual ~SpectatorCameraHooks() = default;
    // In the world's tick, after the view's frame placed `camera` (the
    // mission's camera node): the spectator's camera written over it.
    virtual void place_camera(zcls::Node *camera) = 0;
};

void set_spectator_camera_hooks(SpectatorCameraHooks *hooks);
SpectatorCameraHooks *spectator_camera_hooks();

} // namespace mech3
