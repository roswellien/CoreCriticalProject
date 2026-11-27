#include <cmath>

#include "check.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/interp.h"
#include "gamez/zclass/object3d.h"

// #485 (docs/fixed-step.md): frames drawn between simulation steps blend each
// moved node, and the simulation only ever sees the exact transforms.

namespace {
bool near(float a, float b) { return std::fabs(a - b) < 1e-4f; }

// A turn of `degrees` about the up axis, at `x` along the ground.
void yaw_at(float degrees, float x, float m[12]) {
  const float r = degrees * 3.14159265f / 180.0f;
  const float c = std::cos(r), s = std::sin(r);
  const float rows[12] = {c, 0, -s, 0, 1, 0, s, 0, c, x, 0, 0};
  for (int i = 0; i < 12; ++i) m[i] = rows[i];
}

float* local_of(zcls::Node* node) { return static_cast<zcls::Object3d*>(node->data)->floats(0x30); }
}  // namespace

TEST(interp_blend_matrix_ends_and_middle) {
  float from[12], to[12], out[12];
  yaw_at(0, 0, from);
  yaw_at(90, 10, to);
  zcls::interp::blend_matrix(from, to, 0.0f, out);
  for (int i = 0; i < 12; ++i) EXPECT(near(out[i], from[i]));
  zcls::interp::blend_matrix(from, to, 1.0f, out);
  for (int i = 0; i < 12; ++i) EXPECT(near(out[i], to[i]));
  zcls::interp::blend_matrix(from, to, 0.5f, out);
  float half[12];
  yaw_at(45, 5, half);
  for (int i = 0; i < 12; ++i) EXPECT(near(out[i], half[i]));
}

TEST(interp_blend_matrix_keeps_scale) {
  float from[12], to[12], out[12];
  yaw_at(0, 0, from);
  yaw_at(30, 0, to);
  for (int i = 0; i < 3; ++i) from[i] *= 2.0f, to[i] *= 4.0f;  // the right axis scaled 2, then 4
  zcls::interp::blend_matrix(from, to, 0.5f, out);
  EXPECT(near(std::sqrt(out[0] * out[0] + out[1] * out[1] + out[2] * out[2]), 3.0f));
  EXPECT(near(std::sqrt(out[3] * out[3] + out[4] * out[4] + out[5] * out[5]), 1.0f));
}

// Ours (#485): a node scaled to nothing on an axis at either end (hidden, or
// grown from 0 by an effect animation) has no rotation to blend: it is drawn
// with the newer rows, its position still blended, and never with a bogus
// rotation or a NaN.
TEST(interp_blend_matrix_a_flattened_row_takes_the_newer_rows) {
  float from[12], to[12], out[12];
  yaw_at(0, 0, from);
  yaw_at(30, 2, to);
  for (int i = 0; i < 3; ++i) from[i] = 0.0f;  // the right axis scaled to 0 at the start
  zcls::interp::blend_matrix(from, to, 0.5f, out);
  bool rows_are_newer = true;
  for (int c = 0; c < 9; ++c) rows_are_newer = rows_are_newer && out[c] == to[c];
  EXPECT(rows_are_newer);
  EXPECT(near(out[9], 0.5f * (from[9] + to[9])) && near(out[11], 0.5f * (from[11] + to[11])));
  yaw_at(0, 0, from);
  for (int c = 3; c < 6; ++c) to[c] = std::nanf("");  // the newer up axis not a number
  zcls::interp::blend_matrix(from, to, 0.5f, out);
  bool same_as_newer = true;
  for (int c = 0; c < 9; ++c) same_as_newer = same_as_newer && (out[c] == to[c] || (std::isnan(out[c]) && std::isnan(to[c])));
  EXPECT(same_as_newer);
}

TEST(interp_apply_blends_restore_gives_back_the_exact_matrix) {
  zcls::interp::clear();
  zcls::Node* node = zcls::object3d_create();
  EXPECT(node != nullptr);
  if (!node) return;
  float m[12];
  yaw_at(0, 0, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  yaw_at(0, 2, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  zcls::interp::apply(0.25f);
  EXPECT(near(local_of(node)[9], 0.5f));
  zcls::interp::restore();
  EXPECT(local_of(node)[9] == 2.0f);
  zcls::interp::clear();
}

// A node update during the draw builds the local matrix from the angles and
// clears that flag (1); the stale flag (0x20) may change too. Restore gives
// back the whole data flags word as the draw found it, with the local.
TEST(interp_restore_gives_back_the_whole_flags_word) {
  zcls::interp::clear();
  zcls::Node* node = zcls::object3d_create();
  EXPECT(node != nullptr);
  if (!node) return;
  auto* data = static_cast<zcls::Object3d*>(node->data);
  float m[12];
  yaw_at(0, 0, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  yaw_at(0, 2, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  data->put<uint32_t>(0, data->get<uint32_t>(0) | 1u);
  const uint32_t before = data->get<uint32_t>(0);
  zcls::interp::apply(0.5f);
  data->put<uint32_t>(0, (data->get<uint32_t>(0) & ~1u) ^ 0x20u);  // what a node update in the draw does
  zcls::interp::restore();
  EXPECT(data->get<uint32_t>(0) == before);
  EXPECT(local_of(node)[9] == 2.0f);
  zcls::interp::clear();
}

// A move marks a node and its children changed (0x2000000), skipping a child
// that still has the mark; the renderers clear it on what they walk. With the
// fixed step the draws' clearing never stays (two steps may run with no draw
// between them, below 30 fps): restore gives the marks back, and each step's
// settle_world_caches clears them on the active nodes in the world tree, so the
// next step's move marks the child again.
TEST(interp_changed_marks_are_cleared_by_the_step_not_the_draw) {
  constexpr uint32_t kMark = 0x2000000, kActive = 4, kInWorldTree = 0x80000;
  zcls::interp::clear();
  zcls::Node* parent = zcls::object3d_create();
  zcls::Node* child = zcls::object3d_create();
  EXPECT(parent != nullptr && child != nullptr);
  if (!parent || !child) return;
  zcls::node_add_child(parent, child);
  for (zcls::Node* n : {parent, child}) n->set_flags((n->flags() | kActive | kInWorldTree) & ~kMark);
  zcls::node_mark_unk25(parent);
  EXPECT((parent->flags() & kMark) && (child->flags() & kMark));
  zcls::interp::record();
  zcls::interp::apply(0.5f);
  for (zcls::Node* n : {parent, child}) n->set_flags(n->flags() & ~kMark);  // what the renderers do
  zcls::interp::restore();
  EXPECT((parent->flags() & kMark) && (child->flags() & kMark));
  zcls::interp::settle_world_caches();
  EXPECT(!(parent->flags() & kMark) && !(child->flags() & kMark));
  // The child's world cache brought up to date, then the parent moves again.
  static_cast<zcls::Object3d*>(child->data)->put<uint32_t>(0, 0);
  zcls::node_mark_unk25(parent);
  EXPECT((child->flags() & kMark) && (static_cast<zcls::Object3d*>(child->data)->get<uint32_t>(0) & 0x20));
  zcls::interp::clear();
}

TEST(interp_snaps_a_jump_and_a_new_node) {
  zcls::interp::clear();
  zcls::Node* node = zcls::object3d_create();
  EXPECT(node != nullptr);
  if (!node) return;
  float m[12];
  yaw_at(0, 0, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  zcls::interp::apply(0.5f);  // one record: nothing to blend from
  EXPECT(local_of(node)[9] == 0.0f);
  zcls::interp::restore();
  yaw_at(0, zcls::interp::kSnapDistance + 10.0f, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  zcls::interp::apply(0.5f);  // farther than a step allows: drawn where it is
  EXPECT(local_of(node)[9] == zcls::interp::kSnapDistance + 10.0f);
  zcls::interp::restore();
  zcls::interp::clear();
}

// A node placed between frames (outside a step) is drawn where it was put and
// keeps that place; the blend of its older records never overwrites it.
TEST(interp_node_moved_outside_a_step_keeps_its_place) {
  zcls::interp::clear();
  zcls::Node* node = zcls::object3d_create();
  EXPECT(node != nullptr);
  if (!node) return;
  float m[12];
  yaw_at(0, 0, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  yaw_at(0, 1, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  yaw_at(0, 20, m);  // placed by something outside the step
  zcls::object3d_set_matrix(node, m);
  zcls::interp::apply(0.5f);
  EXPECT(local_of(node)[9] == 20.0f);
  zcls::interp::restore();
  EXPECT(local_of(node)[9] == 20.0f);
  zcls::interp::clear();
}

TEST(interp_forgotten_node_starts_fresh) {
  zcls::interp::clear();
  zcls::Node* node = zcls::object3d_create();
  EXPECT(node != nullptr);
  if (!node) return;
  float m[12];
  yaw_at(0, 0, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  zcls::interp::forget(node);  // as node_slot_free does
  yaw_at(0, 3, m);
  zcls::object3d_set_matrix(node, m);
  zcls::interp::record();
  zcls::interp::apply(0.5f);  // no record from before the reuse
  EXPECT(local_of(node)[9] == 3.0f);
  zcls::interp::restore();
  zcls::interp::clear();
}
