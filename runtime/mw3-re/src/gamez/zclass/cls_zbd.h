#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include "gamez/zclass/cls_node.h"

// zClass\cls_zbd.c: reading gamez.zbd and its node part (docs/gamez.md).
namespace zcls {

enum class ZbdReadMode { ObserveSelected, StrictExport };
struct ZbdSourceRequest {
  std::string member, sha256;
  std::uint64_t bytes{};
  std::set<std::uint32_t> model_slots;
};
struct ZbdPartitionProof {
  std::uint32_t world_node{};
  std::int32_t x{}, z{};
  std::vector<std::uint32_t> nodes;
};
// Optional proof state only. Null retains the ordinary decoder. Bounds that
// can change a reader's result are enforced solely in isolated StrictExport.
struct ZbdReadContext {
  explicit ZbdReadContext(ZbdReadMode selected_mode) : mode(selected_mode) {}
  ZbdReadMode mode;
  ZbdSourceRequest expected;
  std::string member, sha256;
  const char* failure{};
  std::uint64_t input_bytes{}, section_end{}, allocated_bytes{}, load_epoch{};
  std::int32_t node_count{}, model_count{}, texture_count{}, material_count{};
  std::vector<std::uint8_t> model_ok, node_ok;
  std::vector<std::int32_t> node_models;
  std::vector<ZbdPartitionProof> partitions;
  std::shared_ptr<const SourceAsset> reread_origin;
  std::FILE* (*snapshot_factory)() = nullptr; // Authored failure control; default is private temp.
  bool failed{}, snapshot_verified{}, transformed{};
  bool strict() const { return mode == ZbdReadMode::StrictExport; }
  void require(bool condition, const char* reason);
  void span(std::FILE* stream, std::uint64_t bytes, bool allocation = false);
  void allocate(std::uint64_t bytes);
  void model_result(std::uint32_t slot, bool success);
  void node_result(std::uint32_t slot, std::int32_t model, bool success);
  void partition(Node* world, std::int32_t x, std::int32_t z, Node** entries, std::int32_t count);
  void publish();
  void publish_checked();
  // The isolated exporter restores its temporary pool containers before this
  // context dies. These owners free even allocations a failed legacy read did
  // not finish attaching. ObserveSelected retains ordinary pool ownership.
  template <typename T> T* own_new(T* pointer, bool array = false) {
    if (strict()) {
      require(pointer != nullptr, "source allocation failed");
      std::shared_ptr<void> owner(pointer, [array](void* value) {
        if (array) delete[] static_cast<T*>(value);
        else delete static_cast<T*>(value);
      });
      allocations.push_back(std::move(owner));
    }
    return pointer;
  }
  void* own_malloc(void* pointer) {
    if (strict()) {
      require(pointer != nullptr, "source allocation failed");
      std::shared_ptr<void> owner(pointer, std::free);
      allocations.push_back(std::move(owner));
    }
    return pointer;
  }
  std::vector<std::shared_ptr<void>> allocations;
};
struct ZbdObservationSession {
  std::vector<ZbdSourceRequest> sources;
};
// Latest registration wins. Destruction of an older lease never changes the
// current weak registration, including when a new renderer selects Off.
std::shared_ptr<const ZbdObservationSession>
observe_zbd_sources(std::vector<ZbdSourceRequest> sources);
std::uint64_t world_source_epoch();
std::uint64_t invalidate_world_source_proofs();

int read_node_list(Node** out, int32_t count, std::FILE* f, ZbdReadContext* proof = nullptr);  // 0x004fea80
int read_node(Node* node, std::FILE* f, ZbdReadContext* proof = nullptr);                      // 0x004feaf0
int read_nodes(int32_t size, std::FILE* f, ZbdReadContext* proof = nullptr);                   // 0x004ff200

struct ZbdHeader {                 // 0x24 bytes
  uint32_t signature;              // 0x02971222
  uint32_t version;                // 27
  int32_t texture_count;
  int32_t textures_offset, materials_offset, models_offset;
  int32_t node_array_size, node_last_free, nodes_offset;
};
static_assert(sizeof(ZbdHeader) == 0x24, "v27 source header layout");
std::FILE* open_zbd(const char* path, ZbdHeader* header, ZbdReadContext* proof = nullptr);     // 0x004ff6a0
// Ours, not the original's: given the opened file, may return another stream
// with the file's contents changed (the 1.2 data layer, mech3/patch12.h),
// closing the first. Null: none.
using OpenHook = std::FILE* (*)(const char* path, std::FILE* f);
void set_open_hook(OpenHook hook);
OpenHook open_hook();
char* zbd_path();                                             // 0x0060bf50, 0x30 bytes
int read_zbd(const char* path);                               // 0x004ff520
int read_zbd(const char* path, ZbdReadContext* proof);
int32_t node_index_of(const Node* node);                      // 0x004fe100
// A node's model (and with `recurse` its tree's) read again from the file
// the last read_zbd remembered: 0, or 1 without a file or the node in it.
int reread_node(std::FILE* f, const ZbdHeader& h, Node* node, int32_t recurse,
                ZbdReadContext* proof = nullptr);  // 0x004ff7a0
int reread(Node* node, int32_t recurse);                      // 0x004ff730

}  // namespace zcls
