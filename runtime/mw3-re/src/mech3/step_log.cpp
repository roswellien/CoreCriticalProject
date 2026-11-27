#include "mech3/step_log.h"

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>

#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_node.h"
#include "mech3/veh_basic_object.h"
#include "mech3/veh_controls.h"

namespace mech3 {

namespace {
std::FILE* g_file = nullptr;
uint64_t g_step = 0;
std::string g_vehicles;            // this step's vehicle lines
std::map<const void*, int> g_ids;  // vehicles by first appearance: addresses differ between runs

// FNV-1a over the bytes.
uint64_t fnv(uint64_t h, const void* p, std::size_t n) {
  const auto* b = static_cast<const uint8_t*>(p);
  for (std::size_t i = 0; i < n; ++i) h = (h ^ b[i]) * 0x100000001b3ull;
  return h;
}

bool is_live(const zcls::Node* node) { return (node->link & zcls::kNodeLive) != 0; }

// A node's object3d local transform into the hash, then its children's that
// the table walk does not reach (not marked live there: a mech's limbs, which
// the mech's own code poses each step).
void hash_object(const zcls::Node* node, uint64_t& h, int32_t& count) {
  if (node->cls() == 5 && node->data) {
    h = fnv(h, static_cast<zcls::Object3d*>(node->data)->floats(0x30), 0x30);
    ++count;
  }
  for (int32_t c = 0; c < node->child_count(); ++c) {
    const zcls::Node* child = node->children[c];
    if (child && !is_live(child)) hash_object(child, h, count);
  }
}
}  // namespace

bool step_log_open(const std::string& path) {
  g_file = std::fopen(path.c_str(), "wb");
  return g_file != nullptr;
}

bool step_log_on() { return g_file != nullptr; }

void step_log_vehicle(const BasicVehicle& v) {
  if (!g_file || !v.transform) return;
  const auto found = g_ids.emplace(&v, static_cast<int>(g_ids.size()));
  const float* m = v.transform;  // rows: right, up, forward, then the position
  int air = 0;
  if (v.controls)
    for (int i = 8; i < 16; ++i) air += v.controls->motion.support_word[i] != 0;
  const float top = v.controls ? v.controls->top_speed : 0.0f;
  char line[256];
  std::snprintf(line, sizeof line, "V %d top=%.9g pos=%.9g,%.9g,%.9g fwd=%.9g,%.9g,%.9g air=%d\n",
                found.first->second, top, m[9], m[10], m[11], m[6], m[7], m[8], air);
  g_vehicles += line;
}

void step_log_end_step() {
  if (!g_file) return;
  uint64_t h = 0xcbf29ce484222325ull;
  int32_t count = 0;
  for (int32_t i = 0, n = zcls::node_total(); i < n; ++i) {
    const zcls::Node* node = zcls::node_at(i);
    if (node && is_live(node)) hash_object(node, h, count);
  }
  std::fprintf(g_file, "S %llu objects=%d hash=%016llx\n%s", static_cast<unsigned long long>(g_step), count,
               static_cast<unsigned long long>(h), g_vehicles.c_str());
  std::fflush(g_file);  // a run that crashes keeps its steps up to the crash
  g_vehicles.clear();
  ++g_step;
}

}  // namespace mech3
