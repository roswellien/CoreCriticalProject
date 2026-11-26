#pragma once

// Ours (#485, runtime/mw3-re/docs/fixed-step.md): drawing between simulation
// steps. With the fixed 1/30 s step a fast monitor draws several frames per
// step; without blending, everything would move in visible 30 Hz jumps. After
// each step `record` keeps every object3d's transforms (the local 3x4 at data
// +0x30 and, while valid, the cached world 3x4 at +0x60). Before a frame is
// drawn, `apply` writes each moved node's blend between its last two records
// (position and per-row scale in a straight line, rotation by quaternion
// slerp), keeping every node's transform and world cache as it found them;
// `restore` puts those back right after the draw (a cache the draw rebuilt
// from the blended chain too), so the simulation never sees a blended value.
// A node that moved farther than a step allows (spawned, placed, a camera
// cut) is drawn where it is.
namespace zcls {

struct Node;

namespace interp {

// The farthest a node may move in one step and still be blended, in meters.
// The fastest campaign objects (missiles) move well under this in 1/30 s.
constexpr float kSnapDistance = 50.0f;

// At the end of each step, before `record`: every stale cached world matrix in
// the world tree rebuilt from the exact transforms. The original's draw did so
// after each of its frames, and the game reads a cache stale or not (a
// vehicle's turret turn), so this runs once a step however many frames are
// drawn; `restore` keeps the draws themselves out of the caches.
void settle_world_caches();
void record();
void apply(float alpha);
void restore();
// A node's slot is being freed: its records go, so a node made in the same
// slot starts fresh (node_slot_free).
void forget(const Node* node);
// Everything dropped (a mission start).
void clear();

// The blend of two 3x4 transforms (rows right, up, forward, then the position)
// at t in 0..1, as `apply` does it; for the tests.
void blend_matrix(const float from[12], const float to[12], float t, float out[12]);

}  // namespace interp
}  // namespace zcls
