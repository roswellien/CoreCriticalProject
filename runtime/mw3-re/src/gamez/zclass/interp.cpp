#include "gamez/zclass/interp.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <unordered_map>
#include <vector>

#include "gamez/zclass/class.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/list.h"
#include "gamez/zmath/zmth_matrix.h"

namespace zcls::interp {

namespace {
// Object3d data (docs/zclass-world.md): +0x00 flags, +0x30 the local 3x4,
// +0x60 the cached world 3x4, stale while flag 0x20 is set.
constexpr int kFlagsOffset = 0x00;
constexpr int kLocalOffset = 0x30;
constexpr int kWorldOffset = 0x60;
constexpr uint32_t kWorldStale = 0x20;
// Node flag: in the world tree, so node_to_world keeps its cache (0x004ed280).
constexpr uint32_t kInWorldTree = 0x80000;
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
  // Set by apply when this node was drawn blended, until restore.
  bool blended = false;
  unsigned pass = 0;  // the record() pass that last found this node on list 6
};

std::unordered_map<const Node*, Record> g_records;
unsigned g_pass = 0;
// Every node as the draw found it: its local transform, its cached world
// matrix and whether that was stale. The draw rebuilds world caches from the
// (blended) chain, of nodes apply did not blend too (a turret whose hull
// moved); restore puts each back as it was, so the simulation never reads one.
struct BeforeDraw {
  Node* node;
  bool world_stale;
  bool blended = false;  // apply wrote applied_local (and maybe the cache)
  float local[12];
  float world[12];
  // What apply wrote. The draw itself may move a node (a camera, for one);
  // restore puts back only what still holds apply's blend.
  float applied_local[12];
};
std::vector<BeforeDraw> g_before_draw;

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
  // place with no node until the list is purged. A record whose node is no
  // longer on it is dropped: a whole scene can go without node_slot_free (a
  // mission's pools reset), and its node addresses may be handed out again.
  ++g_pass;
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (!is_live_object3d(node)) continue;
    Record& r = g_records[node];
    r.pass = g_pass;
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
  for (auto it = g_records.begin(); it != g_records.end();) {
    if (it->second.pass != g_pass) it = g_records.erase(it);
    else ++it;
  }
}

void settle_world_caches() {
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (!is_live_object3d(node) || !(node->flags() & kInWorldTree)) continue;
    if (!(object_data(node)->get<uint32_t>(kFlagsOffset) & kWorldStale)) continue;
    // As class.cpp's world_matrix: the chain onto a matrix of its own, which
    // brings each stale cache on it up to date (0x004ed280).
    zmth::Mat34 scratch;
    zmth::push(&scratch);
    zmth::load_identity();
    node_to_world(node, 1);
    zmth::pop();
  }
}

void apply(float alpha) {
  g_before_draw.clear();
  // Walked from list 6, never from the records: only a node on the list is
  // known to be live, so a record is only ever read through a live node.
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (!is_live_object3d(node)) continue;
    const Transforms now = read_transforms(node);
    BeforeDraw& b = g_before_draw.emplace_back();
    b.node = node;
    b.world_stale = !now.world_valid;
    std::memcpy(b.local, now.local, kMatrixBytes);
    std::memcpy(b.world, now.world, kMatrixBytes);
    auto found = g_records.find(node);
    if (found == g_records.end()) continue;
    Record& r = found->second;
    if (!r.has_previous) continue;
    // Moved since its last record, outside a step (a placement between frames,
    // a tool): the records are out of date, so it is drawn as it is and its
    // records start again at the next step.
    if (!same_matrix(now.local, r.current.local)) {
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
    if (local_moved) blend_matrix(r.previous.local, r.current.local, alpha, data->floats(kLocalOffset));
    if (world_moved && now.world_valid) blend_matrix(r.previous.world, r.current.world, alpha, data->floats(kWorldOffset));
    std::memcpy(b.applied_local, data->floats(kLocalOffset), kMatrixBytes);
    b.blended = true;
    r.blended = true;
  }
}

void restore() {
  for (const BeforeDraw& b : g_before_draw) {
    Node* node = b.node;
    if (!is_live_object3d(node)) continue;
    if (b.blended) {
      auto found = g_records.find(node);
      if (found != g_records.end()) found->second.blended = false;
    }
    Object3d* data = object_data(node);
    const uint32_t flags = data->get<uint32_t>(kFlagsOffset);
    // What apply left in the local transform: its blend, or the node as found.
    const float* left = b.blended ? b.applied_local : b.local;
    // Something during the draw moved the node itself (a camera, a placed
    // mech): its new transform stands. Some movers write the local floats
    // without marking the cache, so the cache is marked stale and rebuilt.
    if (!same_matrix(data->floats(kLocalOffset), left)) {
      data->put<uint32_t>(kFlagsOffset, flags | kWorldStale);
      continue;
    }
    // As the draw found it, the cache's content and its stale flag both: the
    // game reads a cache's matrix stale or not (a vehicle's turret turn), so a
    // stale one the draw rebuilt from the blended chain must not stay either.
    std::memcpy(data->floats(kLocalOffset), b.local, kMatrixBytes);
    std::memcpy(data->floats(kWorldOffset), b.world, kMatrixBytes);
    data->put<uint32_t>(kFlagsOffset, b.world_stale ? (flags | kWorldStale) : (flags & ~kWorldStale));
  }
  g_before_draw.clear();
}

void forget(const Node* node) {
  g_records.erase(node);
  g_before_draw.erase(std::remove_if(g_before_draw.begin(), g_before_draw.end(),
                                     [node](const BeforeDraw& b) { return b.node == node; }),
                      g_before_draw.end());
}

void clear() {
  g_records.clear();
  g_before_draw.clear();
}

}  // namespace zcls::interp
