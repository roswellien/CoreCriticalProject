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
