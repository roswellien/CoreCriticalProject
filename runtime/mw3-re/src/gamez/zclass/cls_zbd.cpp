#include "gamez/zclass/cls_zbd.h"
#include "gamez/zutil/zutl_zip.h"
#include "upgrades/json/gamez_json.h"

#include <cstdio>
#include <memory>
#include <set>
#include <string>
#include <vector>
#include <algorithm>
#include <array>
#include <atomic>
#include <cerrno>
#include <limits>
#include <map>
#include <mutex>
#include <stdexcept>
#include "platform/sha256.hpp"
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <fcntl.h>
#include <io.h>
#include <share.h>
#endif

#include "gamez/zclass/camera.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_world.h"
#include "gamez/zclass/display.h"
#include "gamez/zclass/list.h"
#include "gamez/zerror/zerr.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_matl.h"

namespace zcls {

namespace {
constexpr std::uint64_t kProofLimit = 512ULL * 1024 * 1024;
std::atomic<std::uint64_t> g_world_source_epoch{};
std::weak_ptr<const ZbdObservationSession> g_source_session;
std::mutex g_source_session_mutex;
std::string logical_member(const char* path) {
  std::string result = path ? path : "";
  for (auto& c : result) {
    if (c == '\\') c = '/';
    if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
  }
  return result;
}
}
std::uint64_t world_source_epoch() { return g_world_source_epoch.load(); }
std::uint64_t invalidate_world_source_proofs() { return g_world_source_epoch.fetch_add(1) + 1; }
std::shared_ptr<const ZbdObservationSession>
observe_zbd_sources(std::vector<ZbdSourceRequest> sources) {
  auto session = std::make_shared<ZbdObservationSession>();
  session->sources = std::move(sources);
  std::lock_guard<std::mutex> lock(g_source_session_mutex);
  g_source_session = session;
  return session;
}
void ZbdReadContext::require(bool condition, const char* reason) {
  if (condition) return;
  failed = true;
  if (!failure) failure = reason;
  if (strict()) throw std::runtime_error(std::string("Ground source export: ") + reason);
  // Proof refusal must not keep optional metadata allocations alive while
  // the ordinary decoder continues with its existing error/return behavior.
  std::vector<std::uint8_t>().swap(model_ok);
  std::vector<std::uint8_t>().swap(node_ok);
  std::vector<std::int32_t>().swap(node_models);
  std::vector<ZbdPartitionProof>().swap(partitions);
}
void ZbdReadContext::allocate(std::uint64_t bytes) {
  if (!strict()) return;
  // Charge a conservative control-block/vector allowance before allocating.
  require(bytes <= kProofLimit - 64 && allocated_bytes <= kProofLimit - bytes - 64,
          "decoded source allocation budget exceeded");
  allocated_bytes += bytes + 64;
}
void ZbdReadContext::span(std::FILE* stream, std::uint64_t bytes, bool allocation) {
  if (!strict()) return;
  const long position = std::ftell(stream);
  require(position >= 0 && std::uint64_t(position) <= section_end &&
              bytes <= section_end - std::uint64_t(position), "source section span exceeded");
  if (allocation) allocate(bytes);
}
void ZbdReadContext::model_result(std::uint32_t slot, bool success) {
  require(success, "model payload read failed");
  if (slot < model_ok.size()) model_ok[slot] = success;
}
void ZbdReadContext::node_result(std::uint32_t slot, std::int32_t model, bool success) {
  require(success, "node payload read failed");
  if (slot < node_ok.size()) {
    node_ok[slot] = success;
    node_models[slot] = model;
  }
}
void ZbdReadContext::partition(Node* world, std::int32_t x, std::int32_t z,
                               Node** entries, std::int32_t count) {
  if (failed) return;
  try {
  require(count >= 0, "negative world membership count");
  if (failed) return;
  allocate(sizeof(ZbdPartitionProof) + std::uint64_t(count) * sizeof(std::uint32_t));
  ZbdPartitionProof value;
  const auto index = node_index_of(world);
  require(index >= 0 && index < node_count, "world partition has no canonical node slot");
  value.world_node = std::uint32_t(index);
  value.x = x; value.z = z;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto slot = entries ? node_index_of(entries[i]) : -1;
    require(slot >= 0 && slot < node_count, "invalid world membership node");
    if (failed) return;
    value.nodes.push_back(std::uint32_t(slot));
  }
  partitions.push_back(std::move(value));
  } catch (const std::bad_alloc&) {
    require(false, "optional membership proof allocation failed");
  }
}
void ZbdReadContext::publish() {
  try { publish_checked(); }
  catch (const std::bad_alloc&) { require(false, "optional source publication allocation failed"); }
}
void ZbdReadContext::publish_checked() {
  require(snapshot_verified && !transformed, "source snapshot is unverified or transformed");
  if (failed) return;
  struct Visit { std::uint32_t slot; std::int32_t child; };
  // Conservatively reserve DFS, member-map and vector bookkeeping before
  // these temporary proof allocations (they coexist with decoded geometry).
  allocate(std::uint64_t(node_count) * 160);
  std::vector<std::uint8_t> color(std::size_t(node_count), 0);
  std::vector<Visit> stack;
  std::map<std::uint32_t, std::vector<std::uint32_t>> members;
  // Traverse the canonical partition/child graph once, retaining original
  // model slots and detecting cycles rather than following observed draws.
  for (const auto& area : partitions)
    for (const auto root : area.nodes) {
      require(root < color.size(), "world root outside source node table");
      if (failed) return;
      if (color[root] == 2) continue;
      stack.push_back({root, 0});
      while (!stack.empty()) {
        auto& visit = stack.back();
        const auto slot = visit.slot;
        require(slot < node_ok.size() && node_ok[slot], "world membership references an unread node");
        if (failed) return;
        auto* node = node_at(std::int32_t(slot));
        require(node && node->cls() != 0 && (node->link & kNodeLive),
                "world membership references a free node slot");
        if (failed) return;
        if (!color[slot]) {
          color[slot] = 1;
          const auto model = node_models[slot];
          if (model >= 0 && expected.model_slots.count(std::uint32_t(model)))
            members[std::uint32_t(model)].push_back(slot);
        }
        if (visit.child < node->child_count()) {
          const auto child = node->children ? node_index_of(node->children[visit.child++]) : -1;
          require(child >= 0 && child < node_count, "invalid world descendant reference");
          if (failed) return;
          require(color[std::size_t(child)] != 1, "source world child graph contains a cycle");
          if (failed) return;
          if (!color[std::size_t(child)]) stack.push_back({std::uint32_t(child), 0});
        } else {
          color[slot] = 2;
          stack.pop_back();
        }
      }
    }
  std::vector<std::pair<std::uint32_t, std::shared_ptr<const SourceAsset>>> ready;
  for (const auto slot : expected.model_slots) {
    require(slot < model_ok.size() && model_ok[slot], "requested original model was not decoded");
    require(members.count(slot) && !members.at(slot).empty(),
            "requested source model has no verified world membership");
    if (failed) return;
    allocate(sizeof(SourceAsset) + sizeof(WorldSourceIdentity) + member.size() * 2 + 256 +
             std::uint64_t(members.at(slot).size()) * 160);
    auto source = std::make_shared<SourceAsset>();
    source->name = member + ":" + std::to_string(slot);
    source->world = WorldSourceIdentity{"gamez-zbd-v27", member, sha256,
                                        input_bytes, load_epoch, slot};
    for (const auto index : members.at(slot)) {
      auto* node = node_at(std::int32_t(index));
      require(node->model == zmod::model_at(std::int32_t(slot)), "node/model source slot disagrees");
      require(std::memchr(node->name(), 0, 0x24) != nullptr, "unterminated source node name");
      if (failed) return;
      ++source->nodes[node->name()];
    }
    ready.emplace_back(slot, std::move(source));
  }
  // Publish only after every requested selector and needed membership passes.
  for (const auto& entry : ready) {
    auto* model = zmod::model_at(std::int32_t(entry.first));
    model->world_source_asset = entry.second;
    for (const auto index : members.at(entry.first))
      node_at(std::int32_t(index))->source_asset = entry.second;
  }
}

namespace {
std::FILE* proof_temporary_file() {
#if defined(_WIN32)
  // Unlike CRT tmpfile's drive-root path, the user's OS temp directory is
  // writable without elevated privileges. D removes this owned file on close.
  wchar_t directory[MAX_PATH + 1]{}, name[MAX_PATH + 1]{};
  const auto count = GetTempPathW(MAX_PATH, directory);
  if (!count || count >= MAX_PATH || !GetTempFileNameW(directory, L"mwp", 0, name)) return nullptr;
  // Secure fopen denies read sharing for a writer, preventing ReOpenFile.
  // Permit the read-only reopen; still deny other writers. D adds delete sharing.
  auto* output = _wfsopen(name, L"w+bTD", _SH_DENYWR);
  if (!output) {
    DeleteFileW(name);
    return nullptr;
  }
  return output;
#else
  return std::tmpfile();
#endif
}
// Consume the completed writer, including on failure. The existing OpenHook
// must see the same read-only access as zutl::open(path, "rb"), never the
// writable stream used to construct our optional private snapshot.
std::FILE* readonly_snapshot(std::FILE* writer) {
#if defined(_WIN32)
  std::unique_ptr<std::FILE, int (*)(std::FILE*)> close_writer(writer, std::fclose);
  const auto handle = reinterpret_cast<HANDLE>(_get_osfhandle(_fileno(writer)));
  if (handle == INVALID_HANDLE_VALUE) return nullptr;
  // Reopen this exact file object, not its name. Both temporary handles share
  // deletion; the file stays private and is removed after the last close.
  const auto readonly = ReOpenFile(handle, GENERIC_READ | DELETE,
      FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, FILE_FLAG_DELETE_ON_CLOSE);
  if (readonly == INVALID_HANDLE_VALUE) return nullptr;
  const auto descriptor = _open_osfhandle(reinterpret_cast<intptr_t>(readonly), _O_RDONLY | _O_BINARY);
  if (descriptor == -1) { CloseHandle(readonly); return nullptr; }
  auto* input = _fdopen(descriptor, "rb");
  if (!input) _close(descriptor);
  return input;
#else
  // C permits changing an existing stream's access mode with a null name.
  // Implementations that cannot reopen the anonymous temp refuse optional
  // proof, and StrictExport fails, rather than handing a writer to the hook.
  return std::freopen(nullptr, "rb", writer);
#endif
}
std::FILE* freeze_source(std::FILE* input, ZbdReadContext& proof,
                         std::string& digest, std::uint64_t& length) {
  struct PreserveErrno {
    int saved = errno;
    ~PreserveErrno() { errno = saved; }
  } preserve_errno;
  std::fpos_t saved;
  if (!input || std::ferror(input) || std::feof(input) || std::fgetpos(input, &saved) != 0) {
    proof.require(false, "source snapshot cannot preserve input state");
    return input;
  }
  const auto position = std::ftell(input);
  auto* frozen = proof.snapshot_factory ? proof.snapshot_factory() : proof_temporary_file();
  if (!frozen || position < 0) {
    if (frozen) std::fclose(frozen);
    proof.require(false, "private source snapshot is unavailable");
    return input;
  }
  platform::integrity::Sha256 hash;
  std::array<unsigned char, 65536> bytes;
  bool complete = std::fseek(input, 0, SEEK_SET) == 0;
  length = 0;
  while (complete) {
    const auto count = std::fread(bytes.data(), 1, bytes.size(), input);
    if (!count) { complete = std::ferror(input) == 0; break; }
    if (count > kProofLimit - length || std::fwrite(bytes.data(), 1, count, frozen) != count) {
      complete = false;
      break;
    }
    hash.update(bytes.data(), count);
    length += count;
  }
  complete = complete && std::fflush(frozen) == 0;
  if (!complete) {
    std::fclose(frozen);
    const bool restored = std::fsetpos(input, &saved) == 0;
    std::clearerr(input); // Incoming flags were explicitly checked clear.
    if (!restored)
      throw std::runtime_error("Cannot restore the optional source snapshot input position");
    proof.require(false, "bounded source snapshot failed");
    return input;
  }
  try {
    digest = hash.hex();
  } catch (const std::bad_alloc&) {
    std::fclose(frozen);
    const bool restored = std::fsetpos(input, &saved) == 0;
    std::clearerr(input);
    if (!restored) throw std::runtime_error("Cannot restore the optional source snapshot input position");
    proof.require(false, "optional source hash allocation failed");
    return input;
  }
  frozen = readonly_snapshot(frozen);
  if (!frozen || std::fseek(frozen, position, SEEK_SET) != 0) {
    if (frozen) std::fclose(frozen);
    const bool restored = std::fsetpos(input, &saved) == 0;
    std::clearerr(input);
    if (!restored) throw std::runtime_error("Cannot restore the optional source snapshot input position");
    proof.require(false, "read-only source snapshot is unavailable");
    return input;
  }
  std::fclose(input);
  return frozen;
}
const char kFile[] = "C:\\zipper\\GameZMech3\\zClass\\cls_zbd.c";

void source_push_front(int list, Node* node, ZbdReadContext* proof) {
  if (proof && !lists().free)
    proof->allocate(std::uint64_t(lists().chunk_size) * sizeof(ListItem));
  push_front(list, node);
}
int source_seek(std::FILE* stream, long offset, int origin, ZbdReadContext* proof) {
  const auto result = std::fseek(stream, offset, origin);
  if (proof) proof->require(result == 0, "source section seek failed");
  return result;
}

int read_error(int line, const char* msg) {
  zerr::report(0x200, kFile, line, msg);
  return -1;
}

template <typename T>
T* read_data(Node* node, std::FILE* f, bool* ok, ZbdReadContext* proof) {
  if (proof) { proof->span(f, sizeof(T::raw)); proof->allocate(sizeof(T)); }
  auto* d = new T{};
  if (proof) proof->own_new(d);
  node->data = d;
  *ok = std::fread(d->raw, sizeof d->raw, 1, f) == 1;
  if (proof) proof->require(*ok, "node class data read failed");
  return d;
}

// An index list after a count; the exe ignores the list's result.
Node** read_list(int32_t count, std::FILE* f, ZbdReadContext* proof) {
  if (proof) proof->require(count >= 0 && count <= proof->node_count, "invalid node list count");
  if (count < 1) return nullptr;
  if (proof) {
    proof->span(f, std::uint64_t(count) * 4);
    proof->allocate(std::uint64_t(count) * sizeof(Node*));
  }
  Node** out = new Node*[count]();
  if (proof) proof->own_new(out, true);
  read_node_list(out, count, f, proof);
  return out;
}

int read_world(Node* node, std::FILE* f, ZbdReadContext* proof) {
  bool ok;
  World* w = read_data<World>(node, f, &ok, proof);
  if (!ok) return read_error(0x406, "Error reading node world data.");
  const int32_t lights = w->get<int32_t>(0xa0), sounds = w->get<int32_t>(0xac);
  if ((w->lights = read_list(lights, f, proof))) {
    if (proof) proof->allocate(std::uint64_t(lights) * sizeof(void*));
    w->light_data = new void*[lights]();
    if (proof) proof->own_new(w->light_data, true);
  }
  if ((w->sounds = read_list(sounds, f, proof))) {
    if (proof) proof->allocate(std::uint64_t(sounds) * sizeof(void*));
    w->sound_data = new void*[sounds]();
    if (proof) proof->own_new(w->sound_data, true);
  }
  const int32_t rows = w->get<int32_t>(0x8c), cols = w->get<int32_t>(0x88);
  if (proof) {
    proof->require(rows >= 0 && cols >= 0, "negative world partition dimensions");
    if (proof->strict()) {
      proof->require(rows <= 1048576 && cols <= 1048576, "world partition dimensions exceed export cap");
      proof->span(f, std::uint64_t(rows) * cols * sizeof(Partition::raw));
      proof->allocate(std::uint64_t(rows) * sizeof(Partition*) +
                      std::uint64_t(rows) * cols * sizeof(Partition));
    }
  }
  w->rows = new Partition*[rows > 0 ? rows : 0]();
  if (proof) proof->own_new(w->rows, true);
  for (int32_t z = 0; z < rows; ++z) {
    if (proof) proof->allocate(0);
    w->rows[z] = new Partition[cols > 0 ? cols : 0]();
    if (proof) proof->own_new(w->rows[z], true);
  }
  for (int32_t z = 0; z < rows; ++z) {
    for (int32_t x = 0; x < cols; ++x) {
      Partition& p = w->rows[z][x];
      if (proof) proof->span(f, sizeof p.raw);
      if (std::fread(p.raw, sizeof p.raw, 1, f) != 1) {
        if (proof) proof->require(false, "world partition read failed");
        return read_error(0x455, "Error reading world area partition data.");
      }
      p.nodes = read_list(p.get<int16_t>(0x3a), f, proof);
      if (proof) proof->partition(node, x, z, p.nodes, p.get<int16_t>(0x3a));
    }
  }
  w->put<int32_t>(4, 0), w->put<int32_t>(8, 0), w->put<int32_t>(0xc, 0);
  w->area_pending = nullptr;
  source_push_front(kAllNodes, node, proof), source_push_front(kWorlds, node, proof);
  world_set_fog_type(node, w->get<uint32_t>(0x10));
  world_set_fog_color(node, w->get<float>(0x14), w->get<float>(0x18), w->get<float>(0x1c));
  world_set_fog_altitude(node, w->get<float>(0x2c), w->get<float>(0x28));
  world_set_fog_range(node, w->get<float>(0x20), w->get<float>(0x24));
  world_set_fog_density(node, w->get<float>(0x30));
  world_push_fog(node);
  return 1;
}
}  // namespace

// Mech3.exe 1.2 @ 0x004fea80. Indices are not bounds-checked.
int read_node_list(Node** out, int32_t count, std::FILE* f, ZbdReadContext* proof) {
  if (proof) {
    proof->require(count >= 0 && count <= proof->node_count, "invalid node list count");
    if (proof->strict()) proof->span(f, std::uint64_t(count) * 4, true);
  }
  if (count == 0) return 0;
  std::vector<int32_t> index(count > 0 ? count : 0);
  if (std::fread(index.data(), static_cast<size_t>(count) * 4, 1, f) != 1) {
    if (proof) proof->require(false, "node index list read failed");
    zerr::report(0x200, kFile, 0x302, "Error reading GameZ Node list.");
    return -1;
  }
  for (int32_t i = 0; i < count; ++i) {
    if (proof) proof->require(index[i] >= 0 && index[i] < proof->node_count, "node list index outside source table");
    out[i] = node_at(index[i]);
  }
  return 0;
}

// Mech3.exe 1.2 @ 0x004feaf0. 1 when the node has data or links, 0 when not,
// -1 on a read error or an unknown class (7, 8 and above 10).
int read_node(Node* node, std::FILE* f, ZbdReadContext* proof) {
  if (proof) proof->require(node->parent_count() >= 0 && node->child_count() >= 0,
                            "negative node relationship count");
  int result = 0;
  bool ok;
  switch (node->cls()) {
    case 0:
      break;
    case 1: {
      result = 1;
      Camera* c = read_data<Camera>(node, f, &ok, proof);
      if (!ok) return read_error(0x3a3, "Error reading node camera data.");
      for (int i = 0; i < 4; ++i) {
        const auto index = c->get<int32_t>(4 * i);
        if (proof) proof->require(index >= -1 && index < proof->node_count, "camera node index outside source table");
        c->nodes[i] = node_at(index);
      }
      source_push_front(kAllNodes, node, proof), source_push_front(kCameras, node, proof);
      camera_set_clip(node, c->get<float>(0xb0), c->get<float>(0xb4));
      camera_set_fov(node, c->get<float>(0xd8), c->get<float>(0xdc));
      break;
    }
    case 2:
      result = read_world(node, f, proof);
      if (result < 0) return result;
      break;
    case 3:
      result = 1;
      read_data<Window>(node, f, &ok, proof);
      if (!ok) return read_error(0x3e9, "Error reading node window data.");
      source_push_front(kAllNodes, node, proof), source_push_front(kWindows, node, proof);
      break;
    case 4: {
      result = 1;
      Display* d = read_data<Display>(node, f, &ok, proof);
      if (!ok) return read_error(0x3cc, "Error reading node display data.");
      source_push_front(kAllNodes, node, proof), source_push_front(kDisplays, node, proof);
      display_set_clear_color(node, d->get<float>(0x10), d->get<float>(0x14), d->get<float>(0x18));
      break;
    }
    case 5:
      read_data<Object3d>(node, f, &ok, proof);
      if (!ok) return read_error(0x355, "Error reading node object3d data.");
      result = 1;
      source_push_front(kAllNodes, node, proof);
      break;
    case 6:
      read_data<Lod>(node, f, &ok, proof);
      if (!ok) return read_error(0x36a, "Error reading node lod data.");
      result = 1;
      source_push_front(kAllNodes, node, proof);
      break;
    case 9: {
      result = 1;
      Light* l = read_data<Light>(node, f, &ok, proof);
      if (!ok) return read_error(0x37f, "Error reading node light data.");
      l->nodes = read_list(l->get<int32_t>(0xc8), f, proof);
      source_push_front(kAllNodes, node, proof), source_push_front(kLights, node, proof);
      break;
    }
    case 10: {
      result = 1;
      zerr::report(0x200, kFile, 0x323, "Reading sound node data: Must complete software.");
      Sound* s = read_data<Sound>(node, f, &ok, proof);
      if (!ok) return read_error(0x32e, "Error reading node sound data.");
      s->put<int32_t>(0, 0), s->put<int32_t>(4, 0);
      s->nodes = read_list(s->get<int32_t>(0x8c), f, proof);
      source_push_front(kAllNodes, node, proof), source_push_front(kSounds, node, proof);
      break;
    }
    default: {
      if (proof) proof->require(false, "unsupported node class");
      char msg[160];
      std::snprintf(msg, sizeof msg,
                    "gClsReadNode(): Unrecognized node class type:\n  node = %s class_type = %d\n",
                    node->name(), node->cls());
      zerr::report(0x400, kFile, 0x48f, msg);
      return -1;
    }
  }
  if ((node->parents = read_list(node->parent_count(), f, proof))) result = 1;
  if ((node->children = read_list(node->child_count(), f, proof))) return 1;
  return result;
}

// Mech3.exe 1.2 @ 0x004ff200. All slots are read first, then each node's
// data in slot order. Returns the capacity, 0 for an empty pool, -1 on error.
int read_nodes(int32_t size, std::FILE* f, ZbdReadContext* proof) {
  if (proof) proof->require(size >= 0 && size <= 1048576, "invalid node table size");
  NodePool& p = nodes();
  if (size == 0) return 0;
  const int32_t bs = p.block_size;
  if (proof) proof->require(bs > 0 && bs <= 1048576, "invalid node pool block size");
  if (proof) proof->span(f, std::uint64_t(size) * 0xd4);
  int32_t block = 0, done = 0;
  std::vector<uint8_t> buf;
  if (size > 0) {
    do {
      if (block == static_cast<int32_t>(p.blocks.size())) {
        if (proof) proof->allocate(std::uint64_t(bs) * sizeof(Node));
        p.blocks.emplace_back(new Node[bs]{});
        p.capacity += bs;
      }
      const int32_t n = size < done + bs ? size - done : bs;
      if (proof) proof->span(f, std::uint64_t(n) * 0xd4, true);
      buf.resize(static_cast<size_t>(n) * 0xd4);
      if (std::fread(buf.data(), buf.size(), 1, f) != 1) {
        if (proof) proof->require(false, "node table read failed");
        return read_error(0x4e8, "Error reading GameZ Node buffer.");
      }
      for (int32_t i = 0; i < n; ++i) {
        Node& node = p.blocks[block][i];
        node = Node{};
        std::memcpy(node.raw, buf.data() + i * 0xd4, 0xd0);
        std::memcpy(&node.link, buf.data() + i * 0xd4 + 0xd0, 4);
      }
      done += bs;
      ++block;
    } while (done < size);
  }
  if (proof && proof->strict()) {
    proof->allocate(std::uint64_t(size));
    std::vector<std::uint8_t> seen(std::size_t(size), 0);
    for (auto index = p.free_head; index != -1;) {
      proof->require(index >= 0 && index < size && !seen[std::size_t(index)],
                      "source node free list index/cycle is invalid");
      seen[std::size_t(index)] = 1;
      auto* node = node_at(index);
      proof->require(node->cls() == 0 && !(node->link & kNodeLive), "free node slot is live");
      const auto next = node->link & kNodeLinkMask;
      index = next == kNodeLinkMask ? -1 : std::int32_t(next);
    }
  }
  if (size < done) {
    for (int32_t i = size; i < done; ++i) *node_at(i) = Node{};
    for (int32_t i = size; i < done; ++i) free_node(i);
  }
  for (; block < static_cast<int32_t>(p.blocks.size()); ++block) {
    for (int32_t i = 0; i < bs; ++i) p.blocks[block][i] = Node{};
    for (int32_t i = 0; i < bs; ++i) free_node(block * bs + i);
  }
  p.live = 0;
  for (int32_t i = 0; i < size; ++i) {
    Node* node = node_at(i);
    const auto model_slot = node->get<int32_t>(0x3c);
    if (proof) proof->require(node->cls() == 0 || (model_slot >= -1 && model_slot < proof->model_count),
                              "node model index outside source table");
    node->model = zmod::model_at(model_slot);
    node->action = nullptr;
    const auto result = read_node(node, f, proof);
    if (proof) proof->node_result(std::uint32_t(i), node->cls() == 0 ? -1 : model_slot, result >= 0);
    if (result < 1) {
      node->link &= ~kNodeLive;
    } else {
      ++p.live;
      node->link |= kNodeLive;
    }
  }
  for (ListItem* item = lists().list[kWorlds].head; item; item = item->next) {
    if (!item->node) continue;
    if (proof && item->node->child_count() > 0)
      proof->partition(item->node, -1, -1, item->node->children, item->node->child_count());
    auto* w = static_cast<World*>(item->node->data);
    for (int32_t i = 0; i < w->get<int32_t>(0xa0); ++i) w->light_data[i] = w->lights[i]->data;
    for (int32_t i = 0; i < w->get<int32_t>(0xac); ++i) w->sound_data[i] = w->sounds[i]->data;
  }
  return p.capacity;
}

OpenHook g_open_hook = nullptr;
void set_open_hook(OpenHook hook) { g_open_hook = hook; }
OpenHook open_hook() { return g_open_hook; }

// Mech3.exe 1.2 @ 0x004ff6a0. Only the signature and version are checked.
std::FILE* open_zbd(const char* path, ZbdHeader* header, ZbdReadContext* proof) {
  std::FILE* f = nullptr;
  try {
    bool from_mod = false;
    {
      // UPGRADE (mods): an enabled mod's unzbd JSON for this world, as the file it stands for (docs/modding.md, gamez
      // JSON); one that does not read is said and the gamez.zbd read. The file stays until the next open: the caller
      // reads on from it, and Windows will not remove an open file.
      static std::unique_ptr<zutl_zip::ScratchFile> scratch;
      static std::set<std::string> said;
      std::vector<uint8_t> bytes;
      std::string what, why;
      const int got = gamez_from_mod(path, &bytes, &what, &why);
      if (got > 0) scratch = std::make_unique<zutl_zip::ScratchFile>(bytes.data(), bytes.size());
      if (got > 0 && scratch->file) {
        f = std::fopen(scratch->path.string().c_str(), "rb");
        from_mod = f != nullptr;
        if (said.insert(what + "\n").second) std::printf("mw3: mod: %s instead of %s\n", what.c_str(), path);
      } else if (got != 0 && said.insert(what + "\n" + why).second) {
        std::printf("mw3: mod: %s: %s; %s read instead\n", what.c_str(), why.c_str(), path);
      }
    }
    if (!f) f = zutl::open(path, "rb");  // FIX (A): the mounts (zutl_path.h)
    if (f && proof) {
      if (from_mod) proof->transformed = true;
      proof->require(!proof->expected.member.empty() && proof->expected.member.size() <= 1024 &&
          proof->expected.sha256.size() == 64 && proof->expected.bytes > 0 &&
          proof->expected.bytes <= kProofLimit && proof->expected.model_slots.size() <= 4096,
          "source request exceeds export contract bounds");
      try { proof->member = logical_member(path); }
      catch (const std::bad_alloc&) { proof->require(false, "optional source name allocation failed"); }
      proof->require(proof->member == proof->expected.member, "logical source member differs from target");
      if (!proof->failed) {
        f = freeze_source(f, *proof, proof->sha256, proof->input_bytes);
        proof->require(proof->sha256 == proof->expected.sha256 &&
                        proof->input_bytes == proof->expected.bytes,
                        "resolved source pin differs from target");
      }
    }
    if (f && g_open_hook) f = g_open_hook(path, f);
    if (f && proof && !proof->failed) {
      std::string effective_hash;
      std::uint64_t effective_bytes{};
      f = freeze_source(f, *proof, effective_hash, effective_bytes);
      proof->transformed = proof->transformed || from_mod ||
          effective_hash != proof->sha256 || effective_bytes != proof->input_bytes;
      proof->require(!proof->transformed, "raw/effective transformed source is not eligible");
      proof->snapshot_verified = !proof->failed;
    }
  } catch (...) {
    if (f) std::fclose(f);
    throw;
  }
  if (!f) return nullptr;
  int line;
  const char* msg;
  if (std::fread(header, sizeof *header, 1, f) != 1) {
    line = 0x584, msg = "Error reading GameZ header data.";
  } else if (header->signature != 0x02971222) {
    line = 0x58d, msg = "Error reading GameZ header data; incompatible file type";
  } else if (header->version != 27) {
    line = 0x596, msg = "Error reading GameZ header data; incompatible file version";
  } else {
    if (proof) {
      const bool bounded = header->texture_count >= 0 && header->texture_count <= zimg::kMaxTextures &&
          header->node_array_size >= 0 && header->node_array_size <= 1048576 &&
          header->textures_offset >= int(sizeof(ZbdHeader)) &&
          header->materials_offset >= header->textures_offset &&
          header->models_offset >= header->materials_offset &&
          header->nodes_offset >= header->models_offset &&
          std::uint64_t(header->nodes_offset) <= proof->input_bytes &&
          header->node_last_free >= -1 && header->node_last_free < header->node_array_size;
      try {
        proof->require(bounded, "invalid source section/count header");
        if (!proof->failed) {
          proof->node_count = header->node_array_size;
          proof->texture_count = header->texture_count;
          proof->allocate(std::uint64_t(proof->node_count) * 5);
          proof->node_ok.assign(std::size_t(proof->node_count), 0);
          proof->node_models.assign(std::size_t(proof->node_count), -1);
        }
      } catch (const std::bad_alloc&) {
        try { proof->require(false, "optional node proof allocation failed"); }
        catch (...) { std::fclose(f); throw; }
      } catch (...) {
        std::fclose(f);
        throw;
      }
    }
    return f;
  }
  zerr::report(0x200, kFile, line, msg);
  std::fclose(f);
  if (proof) proof->require(false, "source header read/version failed");
  return nullptr;
}

// Mech3.exe 1.2 @ 0x004fe100. -1 for a null node; one outside the pool
// returns whatever EAX held in the exe (here -1).
int32_t node_index_of(const Node* node) {
  if (!node) return -1;
  const NodePool& p = nodes();
  for (size_t b = 0; b < p.blocks.size(); ++b) {
    const Node* base = p.blocks[b].get();
    if (node >= base && node <= base + p.block_size - 1)
      return static_cast<int32_t>(node - base) + static_cast<int32_t>(b) * p.block_size;
  }
  return -1;
}

// Mech3.exe 1.2 @ 0x004ff7a0 (ECX file, EDX header, stack node, recurse):
// the node's model as the file has it, read again into a new slot; the
// node's current one is let go (freed when unused), kept when the read
// fails. 1 when the node is not in the file or its record is unreadable.
int reread_node(std::FILE* f, const ZbdHeader& h, Node* node, int32_t recurse, ZbdReadContext* proof) {
  const auto drop_proof = [&] {
    if (!proof || !node) return;
    if (node->model) node->model->world_source_asset.reset();
    if (node->source_asset && node->source_asset->world) node->source_asset.reset();
  };
  const int32_t index = node_index_of(node);
  if (index < 0 || index >= h.node_array_size) { drop_proof(); return 1; }
  source_seek(f, h.nodes_offset + index * 0xd4, SEEK_SET, proof);
  uint8_t record[0xd4];
  if (proof) { proof->section_end = proof->input_bytes; proof->span(f, sizeof record); }
  if (std::fread(record, sizeof record, 1, f) != 1) {
    drop_proof();
    if (proof) proof->require(false, "reread source node record failed");
    return read_error(0x624, "Error reading GameZ Node buffer."), 1;
  }
  source_seek(f, h.models_offset, SEEK_SET, proof);
  if (proof) proof->section_end = std::uint64_t(h.nodes_offset);
  zmod::Model* old = node->model;  // 0x004eb420
  if (proof) proof->reread_origin = old ? old->world_source_asset : nullptr;
  node_set_model(node, nullptr);
  int32_t model;
  std::memcpy(&model, record + 0x3c, 4);
  if (zmod::Model* m = zmod::reread_model(f, model, proof)) {
    node_set_model(node, m);
    if (old) zmod::model_release(old);
  } else {
    if (proof && old) old->world_source_asset.reset();
    node_set_model(node, old);
  }
  if (recurse)
    for (int32_t i = 0; i < node->child_count(); ++i) reread_node(f, h, node->children[i], recurse, proof);
  return 0;
}

// Mech3.exe 1.2 @ 0x004ff730 (ECX node, EDX recurse): from the file the last
// read_zbd remembered (the destructible buildings' reset, 0x00500760).
int reread(Node* node, int32_t recurse) {
  if (zbd_path()[0] == 0) return 1;
  ZbdHeader h;
  std::shared_ptr<const ZbdObservationSession> session;
  {
    std::lock_guard<std::mutex> lock(g_source_session_mutex);
    session = g_source_session.lock();
  }
  ZbdReadContext proof(ZbdReadMode::ObserveSelected);
  ZbdReadContext* selected{};
  try {
    if (session)
      for (const auto& source : session->sources)
        if (source.member == logical_member(zbd_path())) {
          proof.expected = source;
          proof.load_epoch = world_source_epoch();
          selected = &proof;
          break;
        }
  } catch (const std::bad_alloc&) {
    // Refuse optional provenance; the ordinary reread still runs once.
    selected = &proof;
    proof.require(false, "optional reread selection allocation failed");
  }
  std::FILE* f = open_zbd(zbd_path(), &h, selected);
  if (!f) {
    // All identities from this world become stale without changing the
    // legacy failure result or visiting a potentially malformed child tree.
    if (selected) invalidate_world_source_proofs();
    return 1;
  }
  if (selected && !selected->failed) {
    const auto saved = std::ftell(f);
    std::int32_t material_size{};
    const bool ok = std::fseek(f, h.materials_offset, SEEK_SET) == 0 &&
                    std::fread(&material_size, 4, 1, f) == 1 &&
                    material_size >= 0 && material_size <= 32000;
    std::fseek(f, saved, SEEK_SET);
    selected->require(ok, "reread source material table unavailable");
    if (ok) selected->material_count = material_size;
  }
  const int r = reread_node(f, h, node, recurse, selected);
  std::fclose(f);
  return r;
}

char* zbd_path() {
  static char path[0x30];
  return path;
}

// Mech3.exe 1.2 @ 0x004ff520. A path too long to remember is still read; the
// old remembered path stays.
int read_zbd(const char* path) {
  std::shared_ptr<const ZbdObservationSession> session;
  {
    std::lock_guard<std::mutex> lock(g_source_session_mutex);
    session = g_source_session.lock();
  }
  ZbdReadContext proof(ZbdReadMode::ObserveSelected);
  bool selected = false;
  // Optional setup is completed before the decoder starts. Never retry a
  // partially decoded world after an instrumentation allocation failure.
  try {
    if (session)
      for (const auto& source : session->sources)
        if (source.member == logical_member(path)) {
          proof.expected = source;
          selected = true;
          break;
        }
  } catch (const std::bad_alloc&) {}
  if (selected) return read_zbd(path, &proof);
  return read_zbd(path, nullptr);
}
int read_zbd(const char* path, ZbdReadContext* proof) {
  const auto epoch = invalidate_world_source_proofs();
  if (proof) proof->load_epoch = epoch;
  const size_t len = std::strlen(path);
  if (len == 0) return -1;
  if (len < 0x2f) {
    std::memcpy(zbd_path(), path, len + 1);
  } else {
    char msg[80];
    std::snprintf(msg, sizeof msg, "zbd_filename length %d exceeds storage string size %d.",
                  static_cast<int>(len), 0x30);
    zerr::report(0x200, kFile, 0x5c0, msg);
  }
  ZbdHeader h;
  std::FILE* f = open_zbd(path, &h, proof);
  if (!f) return -1;
  std::unique_ptr<std::FILE, int (*)(std::FILE*)> close_file(f, std::fclose);
  int line = 0;
  const char* msg = nullptr;
  source_seek(f, h.textures_offset, SEEK_SET, proof);
  if (proof) proof->section_end = proof->input_bytes ? std::uint64_t(h.materials_offset) : 0;
  const std::string where = zutl::find(path);
  if (zimg::read_texture_directory(h.texture_count, f, where.empty() ? path : where.c_str(), proof) < 0) {
    line = 0x5d1, msg = "Error reading GameZ texture data.";
  } else if (source_seek(f, h.materials_offset, SEEK_SET, proof),
             proof ? (proof->section_end = std::uint64_t(h.models_offset), zmod::read_materials(f, proof) < 0)
                   : zmod::read_materials(f) < 0) {
    line = 0x5dd, msg = "Error reading GameZ material data.";
  } else if (source_seek(f, h.models_offset, SEEK_SET, proof),
             proof ? (proof->section_end = std::uint64_t(h.nodes_offset), zmod::read_models(f, proof) < 0)
                   : zmod::read_models(f) < 0) {
    line = 0x5e9, msg = "Error reading GameZ model3d data.";
  } else {
    nodes().free_head = h.node_last_free;
    source_seek(f, h.nodes_offset, SEEK_SET, proof);
    if (proof) proof->section_end = proof->input_bytes;
    if (read_nodes(h.node_array_size, f, proof) >= 0) {
      close_file.reset();
      if (proof) proof->publish();
      return 0;
    }
    line = 0x5f6, msg = "Error reading GameZ node data.";
  }
  zerr::report(0x200, kFile, line, msg);
  close_file.reset();
  if (proof) proof->require(false, "source section decode failed");
  return -1;
}

}  // namespace zcls
