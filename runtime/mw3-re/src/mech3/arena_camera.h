#pragma once

// Ours (#529, docs/arena.md "Watching a match"): the spectator camera of a
// watched arena match. Pure math, with no engine, SDL or mech types, so the
// tests can drive it without an install.
//
// The camera only reads where the mechs are and writes the scene camera's
// place and angles after the game's own view has placed it (GameEngine's
// spectator_camera). It never touches a mech, a torso, the controls or the
// match clock, and a hidden match (arena_headless) never makes one, so the
// simulation and the arena log stay as they were.
//
// Every motion is frame-rate independent: smoothing is exponential in real
// seconds (1 - exp(-rate * dt)), never a fixed fraction per frame, because a
// watched match runs on the wall clock at whatever frame rate the machine
// gives (#517).
//
// Axes are the game's: y is up. A Pose's yaw and pitch follow the 3D replay
// viewer's convention (replay3d_view.cpp): the look direction is
// (cos(pitch) * sin(yaw), -sin(pitch), cos(pitch) * cos(yaw)), so pitch > 0
// looks down.

namespace mech3::arena_camera {

enum class Mode {
    Chase,    // behind the followed mech, turning with its heading
    Cockpit,  // at the followed mech's torso, looking where its torso looks
    Orbit,    // circling the middle of the standing mechs
    Overhead, // high above the followed mech, north up, never turning with it
    Free,     // flown by the viewer: mouse look and keyboard move
};
constexpr int kModeCount = 5;

// The mode's name for the on-screen label ("chase", "cockpit", ...).
const char *mode_name(Mode mode);

// The followed mech this frame.
struct Subject {
    bool present = false;         // false: no mech to follow (none standing)
    float centre[3] = {};         // its centroid node's world position
    float forward[3] = {0, 0, 1}; // its heading, flat (y 0) and unit length
    float cockpit[3] = {};        // its torso node's world position (the cockpit)
    float look[3] = {0, 0, 1};    // where its torso looks, unit length
};

// The standing mechs as a group, for the orbit (and for the overhead view
// when no mech is followed).
struct Action {
    int count = 0;        // standing mechs; 0: centre and radius mean nothing
    float centre[3] = {}; // their mean position
    float radius = 0;     // the farthest one's flat distance from the centre
};

// The viewer's input since the last update.
struct Input {
    float forward = 0; // -1 .. 1: W minus S
    float right = 0;   // -1 .. 1: D minus A
    float up = 0;      // -1 .. 1: E minus Q
    float look_dx = 0; // mouse counts moved right while looking
    float look_dy = 0; // mouse counts moved down while looking
    float zoom = 0;    // wheel notches (or zoom key presses), positive in / faster
    bool fast = false; // Shift held: the free camera flies four times as fast
};

struct Pose {
    float eye[3] = {0, 100, 0};
    float yaw = 0;
    float pitch = 0.6f;
};

// Tunables, in metres, seconds and radians. Public so the tests and the
// docs name the same numbers.
constexpr float kLookRadiansPerCount = 0.004f; // as the 3D replay's mouse look
constexpr float kMaxPitch = 1.5f;              // just short of straight up or down
constexpr float kFreeSpeed = 40.0f;            // the free camera's starting speed, m/s
constexpr float kFreeSpeedMin = 5.0f, kFreeSpeedMax = 400.0f;
constexpr float kFastFactor = 4.0f;
constexpr float kZoomStep = 1.25f; // one notch scales a distance or speed by this
constexpr float kChaseDistance = 25.0f, kChaseDistanceMin = 8.0f, kChaseDistanceMax = 150.0f;
constexpr float kOverheadHeight = 150.0f, kOverheadHeightMin = 40.0f, kOverheadHeightMax = 800.0f;
constexpr float kOverheadPitch = 1.45f; // nearly straight down
constexpr float kOrbitRadiusMin = 40.0f;
constexpr float kOrbitTurnRate = 0.15f; // radians per second round the action

class Camera {
  public:
    Mode mode() const { return mode_; }
    // A new mode, taken smoothly from where the camera is now. The free
    // camera starts at the current pose.
    void set_mode(Mode mode);
    // The next (+1) or previous (-1) of the four automatic modes, skipping Free.
    void cycle(int direction);
    // Into the free camera at the current pose, or back to the mode it left.
    void toggle_free();
    // The pose for this frame, `dt` real seconds after the last. The first
    // update, and the first after reset(), jumps straight to its target.
    Pose update(const Subject &subject, const Action &action, const Input &input, float dt);
    // The next update jumps rather than glides (a new match).
    void reset() { fresh_ = reset_pending_ = true; }
    const Pose &pose() const { return pose_; }

  private:
    Mode mode_ = Mode::Chase;
    Mode before_free_ = Mode::Chase;
    bool fresh_ = true;
    // A reset() not yet met by an automatic mode: the free camera keeps fresh_
    // for it, so the next match still opens with a jump.
    bool reset_pending_ = false;
    Pose pose_;
    // The smoothed points the automatic modes glide: where the eye is and the
    // point it looks at. Smoothing points rather than angles avoids a yaw that
    // wraps round the long way.
    float eye_[3] = {0, 100, 0};
    float aim_[3] = {0, 0, 0};
    float chase_distance_ = kChaseDistance;
    float overhead_height_ = kOverheadHeight;
    float orbit_zoom_ = 1.0f;
    float orbit_angle_ = 0;
    float free_speed_ = kFreeSpeed;
};

// The fraction of the way to a target that exponential smoothing at `rate`
// (per second) covers in `dt` seconds: 1 - exp(-rate * dt), in [0, 1].
float smoothing(float rate, float dt);

} // namespace mech3::arena_camera
