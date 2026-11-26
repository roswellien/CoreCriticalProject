#include "gamez/zclass/interp.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <unordered_map>
#include <vector>

#include "gamez/zclass/camera.h"
#include "gamez/zclass/class.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/list.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_cull.h"

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
// The records in list 6's order at the last record(): record and apply walk
// the list in that order, so the i-th live object3d's record is found here
// without a map lookup while the list has not changed (5,600 nodes in c2m1).
// Emptied when a record goes (forget), as a freed node's address may come back.
std::vector<std::pair<const Node*, Record*>> g_order;

// The record of the i-th live object3d on list 6 (record's order), else from
// the map; null for a node with none.
Record* find_record(const Node* node, std::size_t i) {
  if (i < g_order.size() && g_order[i].first == node) return g_order[i].second;
  auto found = g_records.find(node);
  return found == g_records.end() ? nullptr : &found->second;
}

// Cameras (class 1) are placed in the world each step on their own (the
// player's view: PlayerView::place, a position at data +0x14 and angles at
// +0x20), not through an object3d's transform, so they are blended here too:
// set through their setters (0x004f36b0, 0x004f3870), as the game moves them.
// Unblended, the view moved in 30 Hz jumps at any frame rate while the cockpit
// in front of it was blended. A camera given a whole matrix (+0x10 bit 1) is
// drawn as it is.
constexpr int kCameraFlags = 0x10;
constexpr int kCameraPosition = 0x14;
constexpr int kCameraAngles = 0x20;
constexpr uint32_t kCameraGivenMatrix = 2;
// A turn past this in one step is a cut (a new view mode), drawn where it is.
constexpr float kCameraSnapAngle = 1.5707964f;

struct CameraPose {
  float position[3];
  float angles[3];
};
struct CameraRecord {
  CameraPose previous;
  CameraPose current;
  CameraPose applied;  // what apply set; restore puts back only what still holds it
  bool has_previous = false;
  bool blended = false;
  unsigned pass = 0;
};
std::unordered_map<const Node*, CameraRecord> g_cameras;
std::vector<Node*> g_blended_cameras;

bool is_live_camera(const Node* node) { return node && node->cls() == 1 && node->data; }

// False for a camera given a whole matrix.
bool read_camera(Node* node, CameraPose* out) {
  const auto* d = static_cast<const Camera*>(node->data);
  if (d->get<uint32_t>(kCameraFlags) & kCameraGivenMatrix) return false;
  for (int i = 0; i < 3; ++i) {
    out->position[i] = d->get<float>(kCameraPosition + 4 * i);
    out->angles[i] = d->get<float>(kCameraAngles + 4 * i);
  }
  return true;
}

bool same_pose(const CameraPose& a, const CameraPose& b) { return std::memcmp(&a, &b, sizeof a) == 0; }

void set_camera(Node* node, const CameraPose& p) {
  camera_set_rotation(node, p.angles[0], p.angles[1], p.angles[2]);
  camera_set_position(node, p.position[0], p.position[1], p.position[2]);
}

// The short way from one angle to another, in -pi..pi.
float angle_step(float from, float to) {
  constexpr float kTurn = 6.2831853f;
  return std::remainder(to - from, kTurn);
}

void record_camera(Node* node) {
  CameraPose now;
  if (!read_camera(node, &now)) {
    g_cameras.erase(node);
    return;
  }
  CameraRecord& r = g_cameras[node];
  r.pass = g_pass;
  r.previous = (r.blended || !r.has_previous) ? now : r.current;
  r.current = now;
  r.has_previous = true;
  r.blended = false;
}

void apply_camera(Node* node, float alpha) {
  auto found = g_cameras.find(node);
  if (found == g_cameras.end()) return;
  CameraRecord& r = found->second;
  CameraPose now;
  if (!r.has_previous || !read_camera(node, &now)) return;
  if (!same_pose(now, r.current)) {  // moved outside a step: drawn as it is
    r.has_previous = false;
    return;
  }
  if (same_pose(r.previous, r.current)) return;
  const float* a = r.previous.position;
  const float* b = r.current.position;
  const float moved = std::sqrt((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1]) + (b[2] - a[2]) * (b[2] - a[2]));
  if (moved > kSnapDistance) return;
  CameraPose blend;
  for (int i = 0; i < 3; ++i) {
    const float turn = angle_step(r.previous.angles[i], r.current.angles[i]);
    if (std::fabs(turn) > kCameraSnapAngle) return;
    blend.angles[i] = r.previous.angles[i] + turn * alpha;
    blend.position[i] = a[i] + (b[i] - a[i]) * alpha;
  }
  set_camera(node, blend);
  read_camera(node, &r.applied);
  r.blended = true;
  g_blended_cameras.push_back(node);
}

// Every camera as the draw found it, its whole data: the draw derives from its
// place its matrices, world position (+0x2c) and zone list (+0x1e4), which the
// simulation reads (the weapons' casts, the turrets); restore puts it all
// back. Each step's camera_prepare works them out from the exact place.
struct CameraBefore {
  Node* node;
  bool posed;          // a camera placed by position and angles (not a whole matrix)
  CameraPose left;     // as apply left it: its blend, or as found
  uint8_t data[sizeof(Camera::raw)];
};
std::vector<CameraBefore> g_cameras_before;
// The nodes that follow a camera, moved by the draw (horizon_follow, the
// camera's +0x08 and +0x0c): put back as they were too.
std::vector<Node*> g_followers;
uint8_t g_zones_before[4];  // the zone list the weapons' casts read (zmod::zones)

void keep_camera(Node* node) {
  auto* d = static_cast<Camera*>(node->data);
  CameraBefore& c = g_cameras_before.emplace_back();
  c.node = node;
  std::memcpy(c.data, d->raw, sizeof c.data);
  for (Node* follower : {d->nodes[2], d->nodes[3]})
    if (follower) g_followers.push_back(follower);
}

void restore_cameras() {
  for (Node* node : g_blended_cameras) {
    auto found = g_cameras.find(node);
    if (found != g_cameras.end()) found->second.blended = false;
  }
  g_blended_cameras.clear();
  for (const CameraBefore& c : g_cameras_before) {
    if (!is_live_camera(c.node)) continue;
    // Placed again during the draw (the zoom window's view, by the HUD): its
    // new place and what was worked out from it stand.
    CameraPose now;
    if (c.posed && read_camera(c.node, &now) && !same_pose(now, c.left)) continue;
    std::memcpy(static_cast<Camera*>(c.node->data)->raw, c.data, sizeof c.data);
  }
  g_cameras_before.clear();
  std::memcpy(zmod::zones().list, g_zones_before, sizeof g_zones_before);
}

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
  bool flattened = false;  // a row of zero length at either end: no rotation to blend
  for (int row = 0; row < 3; ++row) {
    const float* a = from + 3 * row;
    const float* b = to + 3 * row;
    scale_from[row] = std::sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
    scale_to[row] = std::sqrt(b[0] * b[0] + b[1] * b[1] + b[2] * b[2]);
    flattened = flattened || !(scale_from[row] > 0.0f) || !(scale_to[row] > 0.0f);
    for (int c = 0; c < 3; ++c) {
      unit_from[3 * row + c] = scale_from[row] > 0.0f ? a[c] / scale_from[row] : 0.0f;
      unit_to[3 * row + c] = scale_to[row] > 0.0f ? b[c] / scale_to[row] : 0.0f;
    }
  }
  // A node scaled to nothing (hidden, or grown from 0 by an effect animation)
  // has no rotation to take a quaternion of: drawn with the newer rows.
  if (flattened) {
    for (int c = 0; c < 9; ++c) out[c] = to[c];
    for (int c = 9; c < 12; ++c) out[c] = from[c] + (to[c] - from[c]) * t;
    return;
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
  std::vector<std::pair<const Node*, Record*>> order;
  order.reserve(g_order.size());
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (is_live_camera(node)) {
      record_camera(node);
      continue;
    }
    if (!is_live_object3d(node)) continue;
    Record* known = find_record(node, order.size());
    Record& r = known ? *known : g_records[node];
    order.emplace_back(node, &r);
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
  if (g_records.size() != order.size())
    for (auto it = g_records.begin(); it != g_records.end();) {
      if (it->second.pass != g_pass) it = g_records.erase(it);
      else ++it;
    }
  g_order = std::move(order);
  for (auto it = g_cameras.begin(); it != g_cameras.end();) {
    if (it->second.pass != g_pass) it = g_cameras.erase(it);
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

void prepare_cameras() {
  for (Node* camera : rendered_cameras())
    if (is_live_camera(camera)) camera_prepare(camera);
}

void apply(float alpha) {
  g_before_draw.clear();
  g_cameras_before.clear();
  g_followers.clear();
  rendered_cameras().clear();
  std::memcpy(g_zones_before, zmod::zones().list, sizeof g_zones_before);
  // Walked from list 6, never from the records: only a node on the list is
  // known to be live, so a record is only ever read through a live node.
  for (ListItem* item = list_head(kAllNodes); item; item = item->next) {
    Node* node = item->node;
    if (is_live_camera(node)) {
      keep_camera(node);
      apply_camera(node, alpha);
      CameraBefore& c = g_cameras_before.back();
      c.posed = read_camera(node, &c.left);
      continue;
    }
    if (!is_live_object3d(node)) continue;
    const Transforms now = read_transforms(node);
    Record* known = find_record(node, g_before_draw.size());
    BeforeDraw& b = g_before_draw.emplace_back();
    b.node = node;
    b.world_stale = !now.world_valid;
    std::memcpy(b.local, now.local, kMatrixBytes);
    std::memcpy(b.world, now.world, kMatrixBytes);
    if (!known) continue;
    Record& r = *known;
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
    // (Not a node following a camera, the horizon: that the draw moves to the
    // drawn camera, and each step's camera_prepare to the exact one.)
    const bool moved = !same_matrix(data->floats(kLocalOffset), left);
    if (moved && std::find(g_followers.begin(), g_followers.end(), node) == g_followers.end()) {
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
  restore_cameras();
}

void forget(const Node* node) {
  g_records.erase(node);
  g_order.clear();
  g_cameras.erase(node);
  g_blended_cameras.erase(std::remove(g_blended_cameras.begin(), g_blended_cameras.end(), node), g_blended_cameras.end());
  g_cameras_before.erase(std::remove_if(g_cameras_before.begin(), g_cameras_before.end(),
                                        [node](const CameraBefore& c) { return c.node == node; }),
                         g_cameras_before.end());
  g_followers.erase(std::remove(g_followers.begin(), g_followers.end(), node), g_followers.end());
  std::vector<Node*>& drawn = rendered_cameras();
  drawn.erase(std::remove(drawn.begin(), drawn.end(), node), drawn.end());
  g_before_draw.erase(std::remove_if(g_before_draw.begin(), g_before_draw.end(),
                                     [node](const BeforeDraw& b) { return b.node == node; }),
                      g_before_draw.end());
}

void clear() {
  g_records.clear();
  g_order.clear();
  g_cameras.clear();
  g_blended_cameras.clear();
  g_cameras_before.clear();
  g_followers.clear();
  rendered_cameras().clear();
  g_before_draw.clear();
}

}  // namespace zcls::interp
