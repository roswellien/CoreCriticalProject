#include "gamez/zclass/interp.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <unordered_map>
#include <vector>

#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/list.h"

namespace zcls::interp {

namespace {
// Object3d data (docs/zclass-world.md): +0x00 flags, +0x30 the local 3x4,
// +0x60 the cached world 3x4, stale while flag 0x20 is set.
constexpr int kFlagsOffset = 0x00;
constexpr int kLocalOffset = 0x30;
constexpr int kWorldOffset = 0x60;
constexpr uint32_t kWorldStale = 0x20;
constexpr std::size_t kMatrixBytes = 12 * sizeof(float);

struct Transforms {
  float local[12];
  float world[12];
  bool world_valid;
};

struct Record {
  Transforms previous;
  Transforms current;
  bool has_previous = false;
  // Set by apply when this node was drawn blended, so restore writes it back.
  bool blended = false;
  uint32_t flags_before_draw = 0;
  // What apply wrote. The draw itself may move a node (a camera, for one);
  // restore puts back only what still holds apply's blend.
  float applied_local[12];
  float applied_world[12];
};

std::unordered_map<const Node*, Record> g_records;
std::vector<Node*> g_blended;  // the nodes apply wrote, for restore
// Every node whose cached world matrix was stale when the draw began. The draw
// rebuilds those from the (blended) chain and marks them valid; restore marks
// them stale again, so the simulation rebuilds them from the exact chain.
std::vector<Node*> g_stale_before_draw;

Object3d* object_data(Node* node) { return static_cast<Object3d*>(node->data); }

// Records are only made from list 6 (every node made and not yet freed) and
// dropped when a slot is freed, so a recorded node is live; this checks the class.
bool is_live_object3d(const Node* node) { return node && node->cls() == 5 && node->data; }

Transforms read_transforms(Node* node) {
  Object3d* data = object_data(node);
  Transforms t;
  std::memcpy(t.local, data->floats(kLocalOffset), kMatrixBytes);
  std::memcpy(t.world, data->floats(kWorldOffset), kMatrixBytes);
  t.world_valid = (data->get<uint32_t>(kFlagsOffset) & kWorldStale) == 0;
  return t;
}

bool same_matrix(const float a[12], const float b[12]) { return std::memcmp(a, b, kMatrixBytes) == 0; }

float distance(const float a[12], const float b[12]) {
  const float dx = a[9] - b[9], dy = a[10] - b[10], dz = a[11] - b[11];
  return std::sqrt(dx * dx + dy * dy + dz * dz);
}

// A rotation matrix's rows to a quaternion (w, x, y, z), Shepperd's method.
void quaternion_of(const float r[9], float q[4]) {
  const float trace = r[0] + r[4] + r[8];
  if (trace > 0.0f) {
    const float s = std::sqrt(trace + 1.0f) * 2.0f;
    q[0] = 0.25f * s, q[1] = (r[5] - r[7]) / s, q[2] = (r[6] - r[2]) / s, q[3] = (r[1] - r[3]) / s;
  } else if (r[0] > r[4] && r[0] > r[8]) {
    const float s = std::sqrt(1.0f + r[0] - r[4] - r[8]) * 2.0f;
    q[0] = (r[5] - r[7]) / s, q[1] = 0.25f * s, q[2] = (r[3] + r[1]) / s, q[3] = (r[6] + r[2]) / s;
  } else if (r[4] > r[8]) {
    const float s = std::sqrt(1.0f + r[4] - r[0] - r[8]) * 2.0f;
    q[0] = (r[6] - r[2]) / s, q[1] = (r[3] + r[1]) / s, q[2] = 0.25f * s, q[3] = (r[7] + r[5]) / s;
  } else {
    const float s = std::sqrt(1.0f + r[8] - r[0] - r[4]) * 2.0f;
    q[0] = (r[1] - r[3]) / s, q[1] = (r[6] + r[2]) / s, q[2] = (r[7] + r[5]) / s, q[3] = 0.25f * s;
  }
}

// The inverse of quaternion_of: a unit quaternion to the matrix's rows.
void rows_of(const float q[4], float r[9]) {
  const float w = q[0], x = q[1], y = q[2], z = q[3];
  r[0] = 1 - 2 * (y * y + z * z), r[1] = 2 * (x * y + w * z), r[2] = 2 * (x * z - w * y);
  r[3] = 2 * (x * y - w * z), r[4] = 1 - 2 * (x * x + z * z), r[5] = 2 * (y * z + w * x);
  r[6] = 2 * (x * z + w * y), r[7] = 2 * (y * z - w * x), r[8] = 1 - 2 * (x * x + y * y);
}

void slerp(const float a[4], const float b[4], float t, float out[4]) {
  float to[4] = {b[0], b[1], b[2], b[3]};
  float cosine = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  if (cosine < 0.0f) {  // the short way round
    cosine = -cosine;
    for (float& c : to) c = -c;
  }
  float wa = 1.0f - t, wb = t;
  if (cosine < 0.9995f) {
    const float angle = std::acos(cosine);
    const float sine = std::sin(angle);
    wa = std::sin((1.0f - t) * angle) / sine;
    wb = std::sin(t * angle) / sine;
  }
  float length = 0.0f;
  for (int i = 0; i < 4; ++i) out[i] = wa * a[i] + wb * to[i], length += out[i] * out[i];
  length = std::sqrt(length);
  if (length > 0.0f)
    for (int i = 0; i < 4; ++i) out[i] /= length;
}
}  // namespace

void blend_matrix(const float from[12], const float to[12], float t, float out[12]) {
  // Each row's length is that axis's scale; the rotation is blended on the unit rows.
  float unit_from[9], unit_to[9], scale_from[3], scale_to[3];
  for (int row = 0; row < 3; ++row) {
    const float* a = from + 3 * row;
    const float* b = to + 3 * row;
    scale_from[row] = std::sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
    scale_to[row] = std::sqrt(b[0] * b[0] + b[1] * b[1] + b[2] * b[2]);
    for (int c = 0; c < 3; ++c) {
      unit_from[3 * row + c] = scale_from[row] > 0.0f ? a[c] / scale_from[row] : 0.0f;
      unit_to[3 * row + c] = scale_to[row] > 0.0f ? b[c] / scale_to[row] : 0.0f;
    }
  }
  float quaternion_from[4], quaternion_to[4], quaternion[4], rows[9];
  quaternion_of(unit_from, quaternion_from);
  quaternion_of(unit_to, quaternion_to);
  slerp(quaternion_from, quaternion_to, t, quaternion);
  rows_of(quaternion, rows);
  for (int row = 0; row < 3; ++row) {
    const float scale = scale_from[row] + (scale_to[row] - scale_from[row]) * t;
    for (int c = 0; c < 3; ++c) out[3 * row + c] = rows[3 * row + c] * scale;
  }
  for (int c = 9; c < 12; ++c) out[c] = from[c] + (to[c] - from[c]) * t;
}

void record() {
  // List 6 holds every node made and not yet freed; a removed item keeps its
  // place with no node until the list is purged.
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (!is_live_object3d(node)) continue;
    Record& r = g_records[node];
    const Transforms now = read_transforms(node);
    if (r.blended || !r.has_previous) {
      // A first record (or one left over from an unfinished draw): both ends are now.
      r.previous = now;
    } else {
      r.previous = r.current;
    }
    r.current = now;
    r.has_previous = true;
    r.blended = false;
  }
}

void apply(float alpha) {
  g_blended.clear();
  g_stale_before_draw.clear();
  for (auto& [key, r] : g_records) {
    Node* node = const_cast<Node*>(key);
    if (!is_live_object3d(node)) continue;
    if (object_data(node)->get<uint32_t>(kFlagsOffset) & kWorldStale) g_stale_before_draw.push_back(node);
    if (!r.has_previous) continue;
    // Moved since its last record, outside a step (a placement between frames,
    // a tool): the records are out of date, so it is drawn as it is and its
    // records start again at the next step.
    if (!same_matrix(object_data(node)->floats(kLocalOffset), r.current.local)) {
      r.has_previous = false;
      continue;
    }
    const bool local_moved = !same_matrix(r.previous.local, r.current.local);
    const bool world_moved = r.previous.world_valid && r.current.world_valid &&
                             !same_matrix(r.previous.world, r.current.world);
    if (!local_moved && !world_moved) continue;
    const bool jumped = distance(r.previous.local, r.current.local) > kSnapDistance ||
                        (world_moved && distance(r.previous.world, r.current.world) > kSnapDistance);
    if (jumped) continue;
    Object3d* data = object_data(node);
    r.flags_before_draw = data->get<uint32_t>(kFlagsOffset);
    if (local_moved) blend_matrix(r.previous.local, r.current.local, alpha, data->floats(kLocalOffset));
    if (world_moved && (r.flags_before_draw & kWorldStale) == 0)
      blend_matrix(r.previous.world, r.current.world, alpha, data->floats(kWorldOffset));
    std::memcpy(r.applied_local, data->floats(kLocalOffset), kMatrixBytes);
    std::memcpy(r.applied_world, data->floats(kWorldOffset), kMatrixBytes);
    r.blended = true;
    g_blended.push_back(node);
  }
}

void restore() {
  for (Node* node : g_blended) {
    auto found = g_records.find(node);
    if (found == g_records.end() || !is_live_object3d(node)) continue;
    Record& r = found->second;
    r.blended = false;
    Object3d* data = object_data(node);
    // Something during the draw moved the node itself (a camera, a placed
    // mech): its new transform stands. Some movers write the local floats
    // without marking the cache, which still holds apply's blend, so the cache
    // is marked stale and rebuilt from the new transform.
    if (!same_matrix(data->floats(kLocalOffset), r.applied_local)) {
      data->put<uint32_t>(kFlagsOffset, data->get<uint32_t>(kFlagsOffset) | kWorldStale);
      continue;
    }
    std::memcpy(data->floats(kLocalOffset), r.current.local, kMatrixBytes);
    // A cache valid before the draw and still holding apply's blend goes back
    // to the exact one. A stale one is never marked valid here: the loop below
    // marks every cache stale before the draw stale again.
    const bool valid_before = (r.flags_before_draw & kWorldStale) == 0;
    const bool valid_now = (data->get<uint32_t>(kFlagsOffset) & kWorldStale) == 0;
    if (valid_before && valid_now && same_matrix(data->floats(kWorldOffset), r.applied_world))
      std::memcpy(data->floats(kWorldOffset), r.current.world, kMatrixBytes);
  }
  for (Node* node : g_stale_before_draw) {
    if (!is_live_object3d(node)) continue;
    Object3d* data = object_data(node);
    data->put<uint32_t>(kFlagsOffset, data->get<uint32_t>(kFlagsOffset) | kWorldStale);
  }
  g_blended.clear();
  g_stale_before_draw.clear();
}

void forget(const Node* node) {
  g_records.erase(node);
  g_blended.erase(std::remove(g_blended.begin(), g_blended.end(), node), g_blended.end());
  g_stale_before_draw.erase(std::remove(g_stale_before_draw.begin(), g_stale_before_draw.end(), node),
                            g_stale_before_draw.end());
}

void clear() {
  g_records.clear();
  g_blended.clear();
  g_stale_before_draw.clear();
}

}  // namespace zcls::interp
