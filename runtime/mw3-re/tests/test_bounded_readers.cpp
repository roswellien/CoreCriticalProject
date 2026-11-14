// M3 (docs/modding.md): the readers a broken mod file could crash, bounded
// by their archive entry. The shipped files read whole; truncated and
// garbled copies are refused or read, never a crash.
#include <cstdint>
#include <cfenv>
#include <array>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <random>
#include <string>
#include <stdexcept>
#include <vector>

#include "check.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_zbd.h"
#include "gamez/zclass/list.h"
#include "gamez/zerror/zerr.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zrender/zrndr_fog.h"
#include "frontend/core_critical/renderer/native_surface_identity.hpp"
#include "../tools/analysis/ground_targets.hpp"
#include <nlohmann-json/json.hpp>
#include <iomanip>
#include <sstream>
#include "platform/sha256.hpp"
#include "platform/prepared_visuals.h"
#include "gamez/zclass/cls_mechlib.h"
#include "gamez/zeffect/zeff_anim_init.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zsiscript/si_script.h"
#include "gamez/zutil/zutl_zar.h"
#include "mech3/mech_anim.h"
#include "mech3/mods.h"
#include "gamez/zutil/zutl_path.h"

namespace {
namespace fs = std::filesystem;
struct Entry {
  std::string name;
  std::vector<uint8_t> data;
};
std::vector<Entry> read_all(const std::string& path) {
  std::vector<Entry> out;
  zutl_zar::Archive a;
  zutl_zar::init(a);
  if (!zutl_zar::open(a, path.c_str())) return out;
  for (int i = 0; i < a.count; ++i) {
    Entry e;
    e.name = a.entries[i].name;
    uint32_t size = a.entries[i].length;
    e.data.resize(size);
    if (zutl_zar::read(a, i, e.data.data(), &size) == 0) out.push_back(std::move(e));
  }
  zutl_zar::destroy(a);
  return out;
}
void write_all(const std::string& path, const std::vector<Entry>& entries) {
  zutl_zar::Archive a;
  zutl_zar::init(a);
  zutl_zar::create(a, path.c_str());
  for (const Entry& e : entries) zutl_zar::add(a, e.name.c_str(), e.data.data(), static_cast<uint32_t>(e.data.size()));
  zutl_zar::close(a);
  zutl_zar::destroy(a);
}
bool is_tree(const std::string& n) { return n != "version" && n != "format" && n != "materials"; }
// A copy: cut short, bytes flipped, or words made huge.
void mutate(std::vector<uint8_t>& d, std::mt19937& r, int kind) {
  if (d.empty()) return;
  if (kind == 0) {
    d.resize(r() % d.size());
  } else if (kind == 1) {
    for (int n = 1 + r() % 16; n > 0; --n) d[r() % d.size()] ^= static_cast<uint8_t>(1 + r() % 255);
  } else {
    for (int n = 1 + r() % 4; n > 0 && d.size() >= 4; --n) {
      const size_t at = (r() % (d.size() / 4)) * 4;
      const uint32_t v = r() % 2 ? 0xffffffffu - r() % 16 : 0x10000u + r() % 0x7fffffffu;
      std::memcpy(&d[at], &v, 4);
    }
  }
}
}  // namespace

namespace {
// Authored source bytes, independent of the renderer/exporter. Offsets are
// those of the accepted v27 file format, including original polygon order.
struct GroundFixture {
  std::vector<std::uint8_t> bytes;
  std::size_t material{}, models{}, nodes{}, world{}, partition{};
  template <typename T> void put(std::size_t offset, T value) {
    std::memcpy(bytes.data() + offset, &value, sizeof value);
  }
  std::size_t append(std::size_t count) { auto p = bytes.size(); bytes.resize(p + count); return p; }
  explicit GroundFixture(std::uint32_t corners = 3, bool normals = false,
                         std::uint32_t polygons = 1, bool reverse_first = false) {
    append(0x24);
    put<std::uint32_t>(0, 0x02971222); put<std::uint32_t>(4, 27);
    put<std::int32_t>(8, 1); put<std::int32_t>(12, std::int32_t(bytes.size()));
    auto texture = append(0x28);
    std::memcpy(bytes.data() + texture + 8, "ground", 7);
    put<std::int32_t>(texture + 0x24, -1);
    put<std::int32_t>(16, std::int32_t(bytes.size()));
    material = append(16 + 0x2c);
    put<std::int32_t>(material, 1); put<std::int32_t>(material + 4, 1);
    put<std::int32_t>(material + 8, -1); put<std::int32_t>(material + 12, 0);
    bytes[material + 16] = 255; bytes[material + 17] = 1;
    put<std::int16_t>(material + 16 + 0x28, -1); put<std::int16_t>(material + 16 + 0x2a, -1);
    put<std::int32_t>(20, std::int32_t(bytes.size()));
    models = append(12 + 2 * 0x60);
    put<std::int32_t>(models, 2); put<std::int32_t>(models + 4, 1);
    put<std::int32_t>(models + 8, 1);
    put<std::uint32_t>(models + 12 + 0x10, polygons); put<std::uint32_t>(models + 12 + 0x14, corners);
    put<std::uint32_t>(models + 12 + 0x18, normals ? corners : 0);
    put<std::uint32_t>(models + 12 + 0xc, 1);
    put<std::uint32_t>(models + 12 + 0x5c, std::uint32_t(bytes.size()));
    put<std::uint32_t>(models + 12 + 0x60 + 0x5c, 0xffffffffu);
    auto positions = append(corners * 12);
    put<float>(positions + 12, 1); put<float>(positions + 24 + 4, 1);
    if (corners == 4) { put<float>(positions + 36, 1); put<float>(positions + 40, 1); }
    if (normals) {
      const auto n = append(corners * 12);
      for (std::uint32_t i = 0; i < corners; ++i) put<float>(n + i * 12 + 8, 1);
    }
    auto poly = append(polygons * 0x24);
    for (std::uint32_t p = 0; p < polygons; ++p)
      put<std::uint32_t>(poly + p * 0x24, corners | (normals ? 0x200 : 0));
    const float coords[][2] = {{0,0},{1,0},{.5f,1},{1,1}};
    for (std::uint32_t p = 0; p < polygons; ++p) {
      const bool reversed = (p % 2 != 0) != reverse_first;
      const auto indices = append(corners * 4);
      for (std::uint32_t c = 0; c < corners; ++c) put<std::uint32_t>(indices+c*4,reversed ? corners-1-c : c);
      if (normals) {
        const auto indices = append(corners * 4);
        for (std::uint32_t c = 0; c < corners; ++c) put<std::uint32_t>(indices+c*4,reversed ? corners-1-c : c);
      }
      const auto uv = append(corners * 8);
      for (std::uint32_t c = 0; c < corners; ++c) {
        const auto v = reversed ? corners-1-c : c;
        put<float>(uv+c*8,coords[v][0]); put<float>(uv+c*8+4,coords[v][1]);
      }
      append(corners * 12); // Colours do not enter the UV identity.
    }
    put<std::int32_t>(24, 2); put<std::int32_t>(28, -1);
    put<std::int32_t>(32, std::int32_t(bytes.size()));
    nodes = append(2 * 0xd4);
    std::memcpy(bytes.data() + nodes, "authored_world", 15);
    std::memcpy(bytes.data() + nodes + 0xd4, "authored_ground", 16);
    put<std::int32_t>(nodes + 0x34, 2); put<std::int32_t>(nodes + 0x3c, -1);
    put<std::int32_t>(nodes + 0xd4 + 0x34, 5);
    put<std::uint32_t>(nodes + 0xd0, zcls::kNodeLive);
    put<std::uint32_t>(nodes + 0xd4 + 0xd0, zcls::kNodeLive);
    world = append(0xbc);
    put<float>(world + 0x24, 1000); put<float>(world + 0x28, 100);
    put<std::int32_t>(world + 0x88, 1); put<std::int32_t>(world + 0x8c, 1);
    partition = append(0x48); put<std::int16_t>(partition + 0x3a, 1);
    auto member = append(4); put<std::uint32_t>(member, 1);
    auto object = append(0x90);
    for (int i = 0; i < 4; ++i) put<float>(object + 0x30 + i * 20, 1);
  }
  zcls::ZbdSourceRequest request() const {
    platform::integrity::Sha256 hash; hash.update(bytes.data(), bytes.size());
    return {"zbd/t1/gamez.zbd", hash.hex(), bytes.size(), {0}};
  }
};

struct GroundFixtureScope {
  zcls::NodePool nodes = std::move(zcls::nodes());
  zcls::Lists lists = std::move(zcls::lists());
  zmod::ModelPool models = std::move(zmod::models());
  zmod::MaterialTable materials = std::move(zmod::materials());
  zimg::TextureTable textures = zimg::textures();
  zutl::Mounts mounts = zutl::mounts();
  zmod::Fog fog = zmod::fog();
  zrndr::FogColor fog_color = zrndr::fog_color();
  zrndr::DeviceFog device_fog = zrndr::device_fog();
  std::array<char, 0x30> remembered{};
  std::fenv_t fp;
  bool strict;
  explicit GroundFixtureScope(const GroundFixture& fixture, bool isolated) : strict(isolated) {
    std::fegetenv(&fp);
    std::memcpy(remembered.data(), zcls::zbd_path(), remembered.size());
    zcls::nodes() = {}; zcls::nodes().block_size = 2;
    zcls::lists() = {}; zcls::lists().chunk_size = 8;
    zmod::models() = {}; zmod::materials() = {}; zimg::textures() = {};
    zrndr::device_fog().active = 0; zrndr::device_fog().send = nullptr;
    const auto root = fs::path(MW3_TEST_TMP) / "ground-source";
    fs::create_directories(root / "zbd/t1");
    std::ofstream out(root / "zbd/t1/gamez.zbd", std::ios::binary | std::ios::trunc);
    out.write(reinterpret_cast<const char*>(fixture.bytes.data()), std::streamsize(fixture.bytes.size()));
    zutl::mounts() = {}; zutl::mount(root.string());
  }
  ~GroundFixtureScope() {
    // StrictExport's context owns every raw allocation, including unattached
    // partial reads. Ordinary/ObserveSelected use normal canonical ownership.
    if (!strict) {
      for (auto& m : zmod::models().slots) {
        std::uint32_t zero{}; std::memcpy(m.header + 0xc, &zero, 4);
        zmod::model_release(&m);
      }
      for (auto& block : zcls::nodes().blocks)
        for (int i = 0; i < zcls::nodes().block_size; ++i) {
          auto& n = block[i];
          if (n.cls() == 2 && n.data) {
            auto* w = static_cast<zcls::World*>(n.data);
            if (w->rows) {
              for (int z = 0; z < w->get<std::int32_t>(0x8c); ++z) {
                for (int x = 0; x < w->get<std::int32_t>(0x88); ++x) delete[] w->rows[z][x].nodes;
                delete[] w->rows[z];
              }
              delete[] w->rows;
            }
            delete[] w->lights; delete[] w->sounds; delete[] w->light_data; delete[] w->sound_data;
            delete w;
          } else if (n.cls() == 5) delete static_cast<zcls::Object3d*>(n.data);
          delete[] n.parents; delete[] n.children;
        }
    }
    zcls::nodes() = std::move(nodes); zcls::lists() = std::move(lists);
    zmod::models() = std::move(models); zmod::materials() = std::move(materials);
    zimg::textures() = textures; zutl::mounts() = std::move(mounts);
    zmod::fog() = fog; zrndr::fog_color() = fog_color; zrndr::device_fog() = device_fog;
    std::memcpy(zcls::zbd_path(), remembered.data(), remembered.size());
    std::fesetenv(&fp);
  }
};

std::uint64_t authored_ground_uv_hash(std::uint32_t corner_count = 3, bool normals = false,
                                     std::uint32_t polygons = 1, bool reverse_first = false,
                                     bool textured = true) {
  // Independent documented FNV stream; no model/parser/renderer values seed it.
  const float corners[][8] = {{0,0,0,0,0,0,0,0}, {1,0,0,0,0,0,1,0}, {0,1,0,0,0,0,.5f,1}, {1,1,0,0,0,0,1,1}};
  std::uint64_t value = 0xcbf29ce484222325ULL;
  const auto fold = [&value](const void* data, std::size_t size) {
    auto* p = static_cast<const std::uint8_t*>(data);
    while (size--) { value ^= *p++; value *= 0x100000001b3ULL; }
  };
  fold(&polygons,4);
  for (std::uint32_t p = 0; p < polygons; ++p) {
    fold(&corner_count,4);
    const bool reversed = (p % 2 != 0) != reverse_first;
    for (std::uint32_t c = 0; c < corner_count; ++c) {
      float record[8]; std::memcpy(record,corners[reversed ? corner_count-1-c : c],sizeof record);
      if (normals) record[5] = 1;
      if (!textured) record[6] = record[7] = 0;
      fold(record,sizeof record);
    }
  }
  return value;
}
std::vector<std::string> ground_read_errors;
void capture_ground_read_error(int level, const char*, int line, const char* message) {
  ground_read_errors.push_back(std::to_string(level) + ":" + std::to_string(line) + ":" + message);
}
}

TEST(bounded_world_source_strict_authored_identity_and_membership) {
  GroundFixture fixture;
  zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport);
  proof.expected = fixture.request();
  GroundFixtureScope scope(fixture, true); // Restores pools before proof's raw owners die.
  EXPECT(zcls::read_zbd(proof.expected.member.c_str(), &proof) == 0);
  EXPECT(!proof.failed && proof.snapshot_verified && proof.allocated_bytes < 512 * 1024 * 1024ULL);
  auto* m = zmod::model_at(0); auto* n = zcls::node_at(1);
  EXPECT(m && m->world_source_asset && n->source_asset == m->world_source_asset);
  if (m && m->world_source_asset && m->world_source_asset->world) {
    const auto& source = *m->world_source_asset->world;
    EXPECT(source.kind == "gamez-zbd-v27" && source.member == proof.expected.member);
    EXPECT(source.sha256 == proof.expected.sha256 && source.bytes == fixture.bytes.size());
    EXPECT(source.model_slot == 0 && source.load_epoch == zcls::world_source_epoch());
    EXPECT(m->world_source_asset->nodes.at("authored_ground") == 1);
  }
  EXPECT(proof.partitions.size() == 1 && proof.partitions[0].nodes == std::vector<std::uint32_t>{1});
  EXPECT(cc_mw3_re::native_mesh_uv_hash(*m) == authored_ground_uv_hash());
}

TEST(bounded_world_source_observation_preserves_legacy_failed_read_results) {
  int cases = 0;
  for (int variant = 0; variant != 4; ++variant) {
    GroundFixture fixture;
    if (variant == 1) { // The legacy model table suppresses this non-first payload failure.
      fixture.put<std::int32_t>(fixture.models + 4, 2); fixture.put<std::int32_t>(fixture.models + 8, -1);
      fixture.put<std::uint32_t>(fixture.models + 12 + 0x60 + 0x14, std::uint32_t(fixture.bytes.size() / 12 + 1));
    } else if (variant == 2) fixture.put<std::int32_t>(fixture.nodes + 0xd4 + 0x34, 7);
    else if (variant == 3) fixture.put<std::int32_t>(fixture.nodes + 0xd4 + 0x5c, 1); // Missing child list at EOF.
    int ordinary{}, ordinary_fp{};
    std::vector<std::string> ordinary_errors;
    {
      GroundFixtureScope scope(fixture, false);
      ground_read_errors.clear(); zerr::set_sink(capture_ground_read_error);
      std::feclearexcept(FE_ALL_EXCEPT); std::fesetround(FE_DOWNWARD);
      ordinary = zcls::read_zbd("zbd/t1/gamez.zbd", nullptr);
      ordinary_fp = std::fetestexcept(FE_ALL_EXCEPT);
      ordinary_errors = ground_read_errors; zerr::set_sink(nullptr);
      EXPECT(std::fegetround() == FE_DOWNWARD);
      EXPECT(!zmod::model_at(0)->world_source_asset);
    }
    {
      zcls::ZbdReadContext proof(zcls::ZbdReadMode::ObserveSelected); proof.expected = fixture.request();
      GroundFixtureScope scope(fixture, false);
      ground_read_errors.clear(); zerr::set_sink(capture_ground_read_error);
      std::feclearexcept(FE_ALL_EXCEPT); std::fesetround(FE_DOWNWARD);
      EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd", &proof) == ordinary);
      EXPECT(std::fegetround() == FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT) == ordinary_fp);
      EXPECT(ground_read_errors == ordinary_errors); zerr::set_sink(nullptr);
      EXPECT(proof.failed == (variant != 0));
      EXPECT(bool(zmod::model_at(0)->world_source_asset) == (variant == 0));
    }
    if (variant) {
      zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport); proof.expected = fixture.request();
      GroundFixtureScope scope(fixture, true);
      bool refused = false;
      try { zcls::read_zbd("zbd/t1/gamez.zbd", &proof); }
      catch (const std::runtime_error&) { refused = true; }
      EXPECT(refused && proof.failed && !zmod::model_at(0)->world_source_asset);
    }
    ++cases;
  }
  std::printf("  world source: %d Off/Observe result/error/FP comparisons; 3 strict failure controls\n", cases);
  EXPECT(cases == 4);
}

TEST(bounded_world_source_strict_refuses_mutations_before_unbounded_decode) {
  int refused = 0;
  for (int variant = 0; variant != 10; ++variant) {
    GroundFixture fixture;
    if (variant == 0) fixture.put<std::int32_t>(8, -1);
    if (variant == 1) fixture.put<std::int32_t>(24, 0x7fffffff);
    if (variant == 2) fixture.put<std::int32_t>(32, 0x7fffffff);
    if (variant == 3) fixture.put<std::int16_t>(fixture.material + 16 + 0x2a, 0); // Used-list cycle.
    if (variant == 4) fixture.put<std::int32_t>(fixture.models + 8, 0); // Model free slot has payload.
    if (variant == 5) fixture.put<std::int32_t>(fixture.nodes + 0xd4 + 0x3c, 2);
    if (variant == 6) fixture.put<std::int32_t>(fixture.partition + 0x48, 2);
    if (variant == 7) fixture.put<std::int32_t>(fixture.world + 0x88, 0x7fffffff);
    if (variant == 8) fixture.bytes.resize(fixture.nodes + 0xd4);
    if (variant == 9) fixture.put<std::int16_t>(fixture.partition + 0x3a, -1);
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport); proof.expected = fixture.request();
    GroundFixtureScope scope(fixture, true);
    try { zcls::read_zbd("zbd/t1/gamez.zbd", &proof); }
    catch (const std::runtime_error&) { ++refused; }
    EXPECT(proof.failed && proof.allocated_bytes < 1024 * 1024);
  }
  std::printf("  world source: %d bounded malformed-source refusals\n", refused);
  EXPECT(refused == 10);
}

TEST(bounded_world_source_snapshot_failure_and_session_ownership) {
  GroundFixture fixture;
  {
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::ObserveSelected); proof.expected = fixture.request();
    proof.snapshot_factory = []() -> std::FILE* { return nullptr; };
    GroundFixtureScope scope(fixture, false);
    EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd", &proof) == 0);
    EXPECT(proof.failed && !proof.snapshot_verified && !zmod::model_at(0)->world_source_asset);
  }
  {
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport); proof.expected = fixture.request();
    proof.snapshot_factory = []() -> std::FILE* { return nullptr; };
    GroundFixtureScope scope(fixture, true);
    bool refused = false;
    try { zcls::read_zbd("zbd/t1/gamez.zbd", &proof); }
    catch (const std::runtime_error&) { refused = true; }
    EXPECT(refused && proof.failed && proof.allocated_bytes == 0);
  }
  {
    GroundFixtureScope scope(fixture, false);
    auto old = zcls::observe_zbd_sources({});
    auto current = zcls::observe_zbd_sources({fixture.request()}); old.reset();
    EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd") == 0);
    EXPECT(bool(zmod::model_at(0)->world_source_asset));
    const auto identity = zmod::model_at(0)->world_source_asset;
    auto* copy = zmod::model_copy(*zmod::model_at(0), 0, 0);
    EXPECT(copy->world_source_asset == identity);
    zcls::node_set_model(zcls::node_at(1), copy);
    EXPECT(zcls::node_at(1)->source_asset == identity);
    zcls::node_set_model(zcls::node_at(1), zmod::model_at(0));
    EXPECT(zmod::model_release(copy) == 0 && !copy->world_source_asset);
    EXPECT(zcls::reread(zcls::node_at(1), 0) == 0);
    EXPECT(zcls::node_at(1)->model->world_source_asset == identity);
    auto off = zcls::observe_zbd_sources({}); current.reset();
    const auto epoch = identity->world->load_epoch;
    EXPECT(zcls::read_zbd("missing-gamez.zbd") == -1 && zcls::world_source_epoch() != epoch);
    zcls::node_set_model(zcls::node_at(1), nullptr);
    EXPECT(!zcls::node_at(1)->source_asset);
    zmod::models().size = 2;
    // The scope still frees the arrays. Resetting the epoch is independently
    // enough to make every retained copy's immutable source stale.
    EXPECT(zcls::invalidate_world_source_proofs() != epoch);
  }
}

TEST(bounded_world_source_collector_session_lease_lifetime) {
  GroundFixture fixture;
  const auto pin = fixture.request();
  platform::prepared::EnvironmentSelection selection{};
  platform::prepared::MaterialTarget target{};
  target.source.kind = "gamez-zbd-v27";
  target.source.member = pin.member;
  target.source.sha256 = pin.sha256;
  target.source.bytes = pin.bytes;
  target.source.model_slot = 0;
  selection.material_targets["t1"].push_back(std::move(target));

  const auto collect_requests =
      [](const platform::prepared::EnvironmentSelection *env, bool enabled) {
        std::vector<zcls::ZbdSourceRequest> requests;
        const auto groups =
            platform::prepared::collect_material_target_sources(env, enabled);
        requests.reserve(groups.size());
        for (const auto &group : groups) {
          zcls::ZbdSourceRequest request;
          request.member = group.member;
          request.sha256 = group.sha256;
          request.bytes = group.bytes;
          request.model_slots.insert(group.model_slots.begin(),
                                     group.model_slots.end());
          requests.push_back(std::move(request));
        }
        return requests;
      };

  const auto initial_epoch = zcls::world_source_epoch();
  auto old_empty = zcls::observe_zbd_sources(collect_requests(nullptr, false));
  EXPECT(zcls::world_source_epoch() == initial_epoch);
  auto on_lease = zcls::observe_zbd_sources(collect_requests(&selection, true));
  EXPECT(zcls::world_source_epoch() == initial_epoch);
  old_empty.reset();
  EXPECT(zcls::world_source_epoch() == initial_epoch);

  std::uint64_t on_epoch = initial_epoch;
  {
    GroundFixtureScope scope(fixture, false);
    EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd") == 0);
    on_epoch = zcls::world_source_epoch();
    EXPECT(on_epoch != initial_epoch);
    const auto *model = zmod::model_at(0);
    EXPECT(model && model->world_source_asset && model->world_source_asset->world);
    if (model && model->world_source_asset && model->world_source_asset->world) {
      const auto &source = *model->world_source_asset->world;
      EXPECT(source.kind == "gamez-zbd-v27" && source.member == pin.member);
      EXPECT(source.sha256 == pin.sha256 && source.bytes == pin.bytes);
      EXPECT(source.model_slot == 0 && source.load_epoch == on_epoch);
    }
  }

  auto off_lease = zcls::observe_zbd_sources(collect_requests(&selection, false));
  EXPECT(zcls::world_source_epoch() == on_epoch);

  int ordinary = 0;
  int ordinary_fp = 0;
  {
    GroundFixtureScope scope(fixture, false);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::fesetround(FE_DOWNWARD);
    ordinary = zcls::read_zbd("zbd/t1/gamez.zbd", nullptr);
    ordinary_fp = std::fetestexcept(FE_ALL_EXCEPT);
    EXPECT(std::fegetround() == FE_DOWNWARD);
    EXPECT(zmod::model_at(0) && !zmod::model_at(0)->world_source_asset);
  }
  {
    GroundFixtureScope scope(fixture, false);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::fesetround(FE_DOWNWARD);
    EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd") == ordinary);
    EXPECT(std::fegetround() == FE_DOWNWARD &&
           std::fetestexcept(FE_ALL_EXCEPT) == ordinary_fp);
    EXPECT(zmod::model_at(0) && !zmod::model_at(0)->world_source_asset);
  }

  const auto epoch_before_reset = zcls::world_source_epoch();
  on_lease.reset();
  EXPECT(zcls::world_source_epoch() == epoch_before_reset);

  {
    GroundFixtureScope scope(fixture, false);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::fesetround(FE_DOWNWARD);
    EXPECT(zcls::read_zbd("zbd/t1/gamez.zbd") == ordinary);
    EXPECT(std::fegetround() == FE_DOWNWARD &&
           std::fetestexcept(FE_ALL_EXCEPT) == ordinary_fp);
    EXPECT(zmod::model_at(0) && !zmod::model_at(0)->world_source_asset);
  }
}

TEST(bounded_world_source_independent_source_pins_are_required) {
  int refused = 0;
  for (int variant = 0; variant < 3; ++variant) {
    GroundFixture fixture;
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport); proof.expected = fixture.request();
    if (variant == 0) proof.expected.sha256[0] = proof.expected.sha256[0] == '0' ? '1' : '0';
    if (variant == 1) ++proof.expected.bytes;
    if (variant == 2) proof.expected.model_slots = {1}; // Valid free slot, never a ground selector.
    GroundFixtureScope scope(fixture, true);
    try { zcls::read_zbd("zbd/t1/gamez.zbd", &proof); }
    catch (const std::runtime_error&) { ++refused; }
    EXPECT(proof.failed);
    if (auto* model = zmod::model_at(0)) EXPECT(!model->world_source_asset);
  }
  EXPECT(refused == 3);
}

namespace {
using GroundJson = nlohmann::json;
std::string ground_hex(std::uint64_t value) {
  std::ostringstream out; out << std::hex << std::setfill('0') << std::setw(16) << value; return out.str();
}
std::vector<std::uint8_t> authored_ground_bank() {
  std::vector<std::uint8_t> bytes(88);
  const auto put = [&](std::size_t offset, const void* value, std::size_t size) { std::memcpy(bytes.data()+offset,value,size); };
  const std::uint32_t one=1,offset=64,flags=5; const std::int32_t none=-1; const std::int16_t dimension=2;
  put(4,&one,4); put(12,&one,4); std::memcpy(bytes.data()+24,"ground",7);
  put(56,&offset,4); put(60,&none,4); put(64,&flags,4); put(68,&dimension,2); put(70,&dimension,2);
  const std::uint16_t pixels[] = {0xf800,0x07e0,0x001f,0xffff}; put(80,pixels,sizeof pixels);
  return bytes;
}
std::string write_ground_bank(const std::vector<std::uint8_t>& bytes) {
  const auto directory = fs::path(MW3_TEST_TMP)/"ground-source/banks"; fs::create_directories(directory);
  std::ofstream stream(directory/"opaque.zbd",std::ios::binary|std::ios::trunc);
  stream.write(reinterpret_cast<const char*>(bytes.data()),std::streamsize(bytes.size())); stream.close();
  platform::integrity::Sha256 hash; hash.update(bytes.data(),bytes.size()); return hash.hex();
}
mw3::ground_targets::Request ground_export_request(const GroundFixture& fixture,
                                                  const std::vector<std::uint8_t>& bank) {
  const auto pin=fixture.request(); const auto directory=fs::path(MW3_TEST_TMP)/"ground-source";
  return {directory,directory,pin.member,pin.sha256,"t1","t1-model-0","environment/ground.bin",
          pin.bytes,0,{{"ground","banks/opaque.zbd",write_ground_bank(bank),"ground",bank.size(),0}}};
}
GroundJson ground_request_json(const mw3::ground_targets::Request& r) {
  GroundJson textures=GroundJson::array();
  for (const auto& t:r.textures) textures.push_back({{"texture",t.texture},{"member",t.member},
      {"sha256",t.sha256},{"bytes",t.bytes},{"entry",t.entry},{"mip",t.mip}});
  return {{"schema_version",1},{"data_root",r.data_root.u8string()},{"bank_root",r.bank_root.u8string()},
      {"source",{{"kind","gamez-zbd-v27"},{"member",r.member},{"sha256",r.sha256},{"bytes",r.bytes},{"model_slot",r.model_slot}}},
      {"region",r.region},{"asset_id",r.asset_id},{"surface_materials",r.surface_materials},{"textures",textures}};
}
}

TEST(ground_export_cpu_deterministic_original_polygons_and_rgb565_upload) {
  int cases=0;
  for (int variant=0;variant<6;++variant) {
    const std::uint32_t corners=variant%2 ? 4 : 3, polygons=variant>=4 ? 2 : 1;
    const bool normals=variant>=2, reversed=variant==5;
    GroundFixture fixture(corners,normals,polygons,reversed); GroundFixtureScope scope(fixture,false);
    const auto request=ground_export_request(fixture,authored_ground_bank());
    const auto first=mw3::ground_targets::export_target(request), second=mw3::ground_targets::export_target(request);
    EXPECT(first.material_targets==second.material_targets && first.receipt==second.receipt);
    const auto parsed=GroundJson::parse(first.material_targets); const auto& target=parsed.at("targets").at(0);
    EXPECT(target.at("mesh_uv_hash")==ground_hex(authored_ground_uv_hash(corners,normals,polygons,reversed)));
    EXPECT(target.at("asset_id")=="t1-model-0" && target.at("polygon_materials").size()==polygons);
    // Independently fold the four authored packed words, never RGBA/helper output.
    const unsigned char expected_bytes[]={0x00,0xf8,0xe0,0x07,0x1f,0x00,0xff,0xff};
    std::uint64_t expected=0xcbf29ce484222325ULL;
    for (auto byte:expected_bytes) { expected^=byte; expected*=0x100000001b3ULL; }
    for (const auto& key:target.at("surface_keys"))
      EXPECT(key.at("width")==2 && key.at("height")==2 && key.at("format")==1 && key.at("hash")==ground_hex(expected));
    const auto detail=GroundJson::parse(first.receipt);
    EXPECT(detail.at("nodes").at(0).at("name")=="authored_ground");
    EXPECT(detail.at("partitions").at(0).at("root_node")==1);
    EXPECT(detail.at("admitted_source_and_allocation_bytes").get<std::uint64_t>()<=512*1024*1024ULL);
    if (!variant) {
      const auto output=fs::path(MW3_TEST_TMP)/"authored-export";
      mw3::ground_targets::write_result(first,output);
      bool refused=false; try { mw3::ground_targets::write_result(second,output); }
      catch (const std::exception&) { refused=true; }
      EXPECT(refused && fs::is_regular_file(output/"material_targets.json") && fs::is_regular_file(output/"export-receipt.json"));
      EXPECT(std::distance(fs::directory_iterator(output),fs::directory_iterator{})==2);
    }
    ++cases;
  }
  std::printf("  ground export: %d source primitive/normal/order cases, each exported twice\n",cases);
  EXPECT(cases==6);
}

TEST(ground_export_cpu_discovery_is_separate_and_untextured_is_explicit) {
  GroundFixture fixture; fixture.bytes[fixture.material+17]=0;
  GroundFixtureScope scope(fixture,false);
  auto request=ground_export_request(fixture,authored_ground_bank()); request.textures.clear();
  const mw3::ground_targets::InspectionRequest selected{request.data_root,request.member,request.sha256,"t1",request.bytes};
  const auto first=mw3::ground_targets::inspect_source(selected), second=mw3::ground_targets::inspect_source(selected);
  EXPECT(first==second);
  const auto inspection=GroundJson::parse(first);
  EXPECT(inspection.at("inspection_only")==true && !inspection.contains("targets") && !inspection.contains("mesh_uv_hash"));
  EXPECT(inspection.at("models").at(0).at("model_slot")==0);
  bool refused=false; try { mw3::ground_targets::read_request(first); } catch (const std::exception&) { refused=true; }
  EXPECT(refused);
  const auto exported=mw3::ground_targets::export_target(request); const auto parsed=GroundJson::parse(exported.material_targets);
  const auto& target=parsed.at("targets").at(0);
  EXPECT(target.at("polygon_materials").at(0)=="untextured" && target.at("surface_keys").at(0).is_null());
  EXPECT(target.at("mesh_uv_hash")==ground_hex(authored_ground_uv_hash(3,false,1,false,false)));
  const auto output=fs::path(MW3_TEST_TMP)/"authored-inspection";
  mw3::ground_targets::write_inspection(first,output);
  EXPECT(fs::is_regular_file(output/"source-inspection.json") && !fs::exists(output/"material_targets.json"));
}

TEST(ground_export_cpu_rejects_wrong_pins_and_unsupported_views) {
  int refused=0;
  for (int variant=0;variant<16;++variant) {
    GroundFixture fixture;
    if (variant==12) fixture.put<std::uint32_t>(fixture.partition+0x48,0); // World root has no selected source model.
    if (variant==15) fixture.put<std::uint32_t>(fixture.models+12+2*0x60,0x7fc00000u); // Nonfinite source position.
    GroundFixtureScope scope(fixture,false); auto bank=authored_ground_bank();
    if (variant==8) bank[64]=11; // Alpha-plane input is never silently downgraded.
    if (variant==9) bank.resize(bank.size()-2);
    if (variant==11) { const std::int16_t width=8192; std::memcpy(bank.data()+68,&width,2); }
    if (variant==13) bank[24]='x'; // Pinned bank actually lacks the requested member.
    if (variant==14) { const std::uint32_t count=2; std::memcpy(bank.data()+12,&count,4); }
    auto request=ground_export_request(fixture,bank);
    if (variant==0) request.textures[0].sha256=std::string(64,'0');
    if (variant==1) --request.textures[0].bytes;
    if (variant==2) request.textures[0].mip=1;
    if (variant==3) request.textures[0].entry="substitute";
    if (variant==4) request.sha256=std::string(64,'0');
    if (variant==5) { request.model_slot=1; request.asset_id="t1-model-1"; }
    if (variant==6) request.textures.clear();
    if (variant==7) { auto extra=request.textures[0]; extra.texture=extra.entry="unused"; request.textures.push_back(extra); }
    if (variant==10) request.textures[0].member="../banks/opaque.zbd";
    const auto rounding=std::fegetround(), flags=std::fetestexcept(FE_ALL_EXCEPT);
    try { mw3::ground_targets::export_target(request); } catch (const std::exception&) { ++refused; }
    EXPECT(zmod::models().slots.empty() && zcls::nodes().blocks.empty());
    EXPECT(std::fegetround()==rounding && std::fetestexcept(FE_ALL_EXCEPT)==flags);
  }
  std::printf("  ground export: %d wrong-pin/unsupported-view refusals\n",refused); EXPECT(refused==16);
}

TEST(ground_export_cpu_closed_request_schema) {
  GroundFixture fixture; GroundFixtureScope scope(fixture,false);
  const auto request=ground_export_request(fixture,authored_ground_bank());
  const auto valid=ground_request_json(request);
  EXPECT(mw3::ground_targets::read_request(valid.dump()).member==request.member);
  int refused=0;
  for (int variant=0;variant<8;++variant) {
    auto changed=valid;
    if (variant==0) changed["source"]["model_slot"]=true;
    if (variant==1) changed["textures"][0]["mip"]=false;
    if (variant==2) changed["unknown"]=1;
    if (variant==3) changed["source"]["unknown"]=1;
    if (variant==4) changed["textures"][0]["unknown"]=1;
    if (variant==5) changed["source"]["bytes"]=-1;
    if (variant==6) changed["textures"].push_back(changed["textures"][0]);
    auto bytes=changed.dump(); if (variant==7) bytes.insert(1,"\"schema_version\":1,");
    try { mw3::ground_targets::read_request(bytes); } catch (const std::exception&) { ++refused; }
  }
  EXPECT(refused==8);
  auto source=valid.at("source"); source.erase("model_slot");
  GroundJson inspection{{"schema_version",1},{"data_root",request.data_root.u8string()},{"source",source},{"region","t1"}};
  EXPECT(mw3::ground_targets::read_inspection_request(inspection.dump()).member==request.member);
  inspection["source"]["model_slot"]=0;
  bool rejected=false; try { mw3::ground_targets::read_inspection_request(inspection.dump()); }
  catch (const std::exception&) { rejected=true; } EXPECT(rejected);
}

TEST(bounded_mechlib_reads_the_shipped_trees_whole) {
  const std::string path = std::string(MW3_GAME_DIR) + "/zbd/mechlib.zbd";
  std::error_code ec;
  if (!fs::exists(path, ec)) return;
  zmod::models() = zmod::ModelPool{};
  zmod::reset_pool();
  zcls::MechLib lib;
  zutl_zar::init(lib.archive);
  EXPECT(zcls::mechlib_open(lib, path.c_str()));
  EXPECT(lib.materials.size() == 442);
  int trees = 0, loaded = 0;
  for (const Entry& e : read_all(path)) {
    if (!is_tree(e.name)) continue;
    ++trees;
    const auto* root = zcls::mechlib_load(lib, e.name.c_str());
    if (root) {
      ++loaded;
      platform::integrity::Sha256 expected;
      expected.update(e.data.data(), e.data.size());
      EXPECT(root->source_asset && root->source_asset->member_sha256 == expected.hex());
    }
  }
  std::printf("  mechlib: %d of %d trees read whole\n", loaded, trees);
  EXPECT(trees == 57 && loaded == 57);
  zcls::mechlib_close(lib);
}

TEST(bounded_mechlib_fuzz_never_crashes) {
  const std::string path = std::string(MW3_GAME_DIR) + "/zbd/mechlib.zbd";
  std::error_code ec;
  if (!fs::exists(path, ec)) return;
  const std::vector<Entry> all = read_all(path);
  std::vector<size_t> trees;
  for (size_t i = 0; i < all.size(); ++i)
    if (is_tree(all[i].name)) trees.push_back(i);
  const std::string dir = std::string(MW3_TEST_TMP) + "/bounded_mechlib";
  fs::create_directories(dir, ec);
  const std::string copy = dir + "/mechlib.zbd";
  std::mt19937 r(1234);
  int runs = 0, refused = 0, read = 0, cut = 0, cut_refused = 0, materials_refused = 0;
  for (int seed = 0; seed < 240; ++seed) {
    std::vector<Entry> m = all;
    const int kind = seed % 3;
    const bool materials = seed % 8 == 7;
    const std::string want = materials ? std::string("materials") : all[trees[r() % trees.size()]].name;
    Entry* target = nullptr;
    for (Entry& e : m)
      if (e.name == want) target = &e;
    if (!target) continue;
    const size_t before = target->data.size();
    mutate(target->data, r, kind);
    write_all(copy, m);
    zmod::models() = zmod::ModelPool{};
    zmod::reset_pool();
    zcls::MechLib lib;
    zutl_zar::init(lib.archive);
    const bool open = zcls::mechlib_open(lib, copy.c_str());
    if (materials) materials_refused += !open || lib.materials.empty();
    zcls::Node* t = open && !materials ? zcls::mechlib_load(lib, target->name.c_str()) : nullptr;
    if (!materials) {
      ++runs;
      t ? ++read : ++refused;
      if (kind == 0 && target->data.size() < before) ++cut, cut_refused += t == nullptr;
    }
    zcls::mechlib_close(lib);
  }
  std::printf("  mechlib fuzz: %d trees, %d refused, %d read; cut short %d, refused %d; materials refused %d\n", runs,
              refused, read, cut, cut_refused, materials_refused);
  EXPECT(runs > 150 && refused > 0 && cut_refused == cut);
}

namespace {
// Every motion in the archive at `path` loaded: how many read, how many refused.
void load_motions(const std::string& path, const std::vector<std::string>& names, int* read, int* refused) {
  *read = *refused = 0;
  if (!mech3::open_motions(path.c_str())) return;
  for (const std::string& n : names) {
    zsis::Script s;
    if (mech3::load_motion(s, n.c_str())) ++*read;
    else ++*refused;
    mech3::script_free_parts(s);
  }
  mech3::close_motions();
}
}  // namespace

TEST(bounded_motion_reads_the_shipped_motions_whole) {
  const std::string path = std::string(MW3_GAME_DIR) + "/zbd/motion.zbd";
  std::error_code ec;
  if (!fs::exists(path, ec)) return;
  std::vector<std::string> names;
  for (const Entry& e : read_all(path)) names.push_back(e.name);
  int read = 0, refused = 0;
  load_motions(path, names, &read, &refused);
  std::printf("  motion: %d of %zu read whole\n", read, names.size());
  EXPECT(names.size() == 258 && read == 258 && refused == 0);
}

TEST(bounded_motion_fuzz_never_crashes) {
  const std::string path = std::string(MW3_GAME_DIR) + "/zbd/motion.zbd";
  std::error_code ec;
  if (!fs::exists(path, ec)) return;
  const std::vector<Entry> all = read_all(path);
  const std::string dir = std::string(MW3_TEST_TMP) + "/bounded_motion";
  fs::create_directories(dir, ec);
  const std::string copy = dir + "/motion.zbd";
  std::mt19937 r(4321);
  int runs = 0, refused = 0, cut = 0, cut_refused = 0;
  for (int seed = 0; seed < 300; ++seed) {
    std::vector<Entry> m = all;
    Entry& e = m[r() % m.size()];
    const size_t before = e.data.size();
    const int kind = seed % 3;
    mutate(e.data, r, kind);
    write_all(copy, m);
    int ok = 0, bad = 0;
    load_motions(copy, {e.name}, &ok, &bad);
    ++runs, refused += bad;
    if (kind == 0 && e.data.size() < before) ++cut, cut_refused += bad;
  }
  std::printf("  motion fuzz: %d motions, %d refused; cut short %d, refused %d\n", runs, refused, cut, cut_refused);
  EXPECT(runs == 300 && refused > 0 && cut_refused == cut);
}

// anim.zbd (a whole file, not an archive): copies of c1's cut short, bytes
// flipped or words made huge, read with no world. Each read refuses the
// file (no defs, its counts 0) or reads every def and fails at the first
// lookup, the original's way; none crash or allocate what a count says.
TEST(bounded_anim_fuzz_never_crashes) {
  const std::string src = std::string(MW3_GAME_DIR) + "/zbd/c1/anim.zbd";
  std::error_code ec;
  if (!fs::exists(src, ec)) return;
  std::vector<uint8_t> all(fs::file_size(src, ec));
  if (std::FILE* f = std::fopen(src.c_str(), "rb")) {
    const size_t n = std::fread(all.data(), 1, all.size(), f);
    all.resize(n);
    std::fclose(f);
  }
  const std::string dir = std::string(MW3_TEST_TMP) + "/bounded_anim";
  fs::create_directories(dir, ec);
  const std::string copy = dir + "/anim.zbd";
  std::mt19937 r(777);
  int runs = 0, refused = 0, cut = 0, cut_refused = 0;
  for (int seed = 0; seed < 150; ++seed) {
    std::vector<uint8_t> d = all;
    const int kind = seed % 3;
    // Past the 12-byte header and the source list, so most changes land in the defs.
    std::vector<uint8_t> head(d.begin(), d.begin() + 12), body(d.begin() + 12, d.end());
    mutate(body, r, kind);
    d = head;
    d.insert(d.end(), body.begin(), body.end());
    if (std::FILE* f = std::fopen(copy.c_str(), "wb")) {
      std::fwrite(d.data(), 1, d.size(), f);
      std::fclose(f);
    }
    zeff::anim() = zeff::AnimState{};
    zeff::anim_allow_loading(1);
    zeff::anim_set_zbd_path(copy.c_str());
    zeff::anim_read_zbd();
    const bool was_refused = zeff::anim().defs == nullptr && zeff::anim().def_count() == 0;
    ++runs, refused += was_refused;
    if (kind == 0 && d.size() < all.size()) ++cut, cut_refused += was_refused;
    zeff::anim_free_all();
  }
  std::printf("  anim fuzz: %d reads, %d refused; cut short %d, refused %d\n", runs, refused, cut, cut_refused);
  EXPECT(runs == 150 && refused > 0 && cut_refused == cut);
  // A source count of 0xfffffff0 in the header: refused before anything is
  // allocated (unbounded, the list alone would be some 360 GB).
  std::vector<uint8_t> d = all;
  const uint32_t huge = 0xfffffff0u;
  std::memcpy(&d[8], &huge, 4);
  if (std::FILE* f = std::fopen(copy.c_str(), "wb")) {
    std::fwrite(d.data(), 1, d.size(), f);
    std::fclose(f);
  }
  zeff::anim() = zeff::AnimState{};
  zeff::anim_allow_loading(1);
  zeff::anim_set_zbd_path(copy.c_str());
  EXPECT(zeff::anim_read_zbd() == -1 && zeff::anim().defs == nullptr);
  zeff::anim_free_all();
}

// A mod's motion.zbd with one motion cut short (docs/modding.md, M3): the
// motion comes from the next copy (the install's), read whole; with no
// other copy it is refused. Every other motion is the mod's own.
TEST(bounded_motion_falls_back_to_the_next_copy) {
  const std::string install = MW3_GAME_DIR;
  std::error_code ec;
  if (!fs::exists(install + "/zbd/motion.zbd", ec)) return;
  const zutl::Mounts saved = zutl::mounts();
  const std::string wd = std::string(MW3_TEST_TMP) + "/motion_fallback";
  fs::remove_all(wd, ec);
  fs::create_directories(wd + "/mods/brokenwalk/zbd", ec);
  std::ofstream(wd + "/mods/brokenwalk/mod.txt") << "name=Broken walk\n";
  std::vector<Entry> all = read_all(install + "/zbd/motion.zbd");
  size_t walk_frames = 0;
  for (Entry& e : all)
    if (e.name == "madcat_walk") e.data.resize(e.data.size() / 2);  // cut short: refused
  write_all(wd + "/mods/brokenwalk/zbd/motion.zbd", all);
  auto load = [&](bool with_install, const char* name, uint32_t* frames) {
    zutl::mounts() = zutl::Mounts{};
    zutl::set_write_dir(wd);
    mech3::mods_mount(wd, {"brokenwalk"}, {install});
    if (with_install) zutl::mount(install);
    bool ok = false;
    if (mech3::open_motions("zbd\\motion.zbd")) {
      zsis::Script s;
      ok = mech3::load_motion(s, name);
      *frames = ok ? s.frame_count : 0;
      mech3::script_free_parts(s);
      mech3::close_motions();
    }
    return ok;
  };
  uint32_t frames = 0, whole = 0;
  {  // the install's own, for the frame count
    zutl::mounts() = zutl::Mounts{};
    zutl::mount(install);
    if (mech3::open_motions("zbd\\motion.zbd")) {
      zsis::Script s;
      if (mech3::load_motion(s, "madcat_walk")) whole = s.frame_count;
      mech3::script_free_parts(s);
      mech3::close_motions();
    }
  }
  (void)walk_frames;
  EXPECT(whole > 0);
  EXPECT(load(true, "madcat_walk", &frames) && frames == whole);   // the install's copy
  EXPECT(!mech3::motion_broken("madcat_walk"));
  EXPECT(!load(false, "madcat_walk", &frames));                    // no other copy: refused
  EXPECT(mech3::motion_broken("madcat_walk"));                     // broken, so the mech is refused
  EXPECT(load(false, "madcat_run", &frames) && frames > 0);        // the mod's own others
  // Missing from every copy (the shipped data has no elemental_limp): not
  // broken, so the Elemental keeps the exe's null limp and is not refused.
  EXPECT(!load(true, "elemental_limp", &frames) && !mech3::motion_broken("elemental_limp"));
  zutl::mounts() = saved;
}
