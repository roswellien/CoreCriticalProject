// Asset-free integration tests for the pack library's use of the existing mod engine.
#include "check.h"

#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

#include "gamez/zutil/zutl_path.h"
#include "gamez/zutil/zutl_zar.h"
#include "gamez/zclass/cls_mechlib.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/list.h"
#include "gamez/zclass/cls_mechlib_json.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_matl.h"
#include "zip_write.h"
#include "platform/sha256.hpp"
#include "upgrades/mods/mp_mods.h"
#include "mech3/mods.h"
#include "mech3/mech_names.h"
#include "mech3/mods_tables.h"
#include "mech3/mods_menu.h"
#include "upgrades/mods/mod_export.h"
#include "upgrades/mods/entry_archives.h"
#include "upgrades/mods/model_library_json.h"
#include "upgrades/mods/mod_report.h"
#include "upgrades/editor/save_as.h"
#include "upgrades/mods/campaign_entries.h"
#include "upgrades/mods/mods_delete.h"

namespace {
namespace fs = std::filesystem;

struct PackTest {
  const std::string library_before = mech3::mods_pack_library();
  const zutl::Mounts mounts_before = zutl::mounts();  // includes the global write directory
  const fs::path root = fs::path(MW3_TEST_TMP) / "pack-library";
  const fs::path library = root / "library";
  const std::string write = (root / "write").generic_string();

  PackTest() {
    std::error_code ec;
    fs::remove_all(root, ec);
    fs::create_directories(library);
    mech3::mods_pack_library() = library.generic_string();
    zutl::mounts() = {};
    zutl::set_write_dir(write);
  }
  ~PackTest() {
    mech3::mods_pack_library() = library_before;
    zutl::mounts() = mounts_before;
  }
};

void put(const fs::path& path, const std::string& text) {
  fs::create_directories(path.parent_path());
  std::ofstream(path, std::ios::binary) << text;
}

std::string read(const fs::path& path) {
  std::ifstream file(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
}

// The snapshot includes names and bytes, so an added cache or renamed file is a failure too.
std::map<std::string, std::string> snapshot(const fs::path& folder) {
  std::map<std::string, std::string> files;
  for (const auto& entry : fs::recursive_directory_iterator(folder))
    if (entry.is_regular_file()) files.emplace(fs::relative(entry.path(), folder).generic_string(), read(entry.path()));
  return files;
}

bool contains(const std::vector<std::string>& log, const std::string& text) {
  return std::any_of(log.begin(), log.end(), [&](const std::string& line) {
    return line.find(text) != std::string::npos;
  });
}

void manifest(const fs::path& folder, const std::string& id, const std::string& root = "mod") {
  put(folder / "pack.json", "{\"schema_version\":3,\"game_id\":\"mw3\",\"id\":\"" + id +
                           "\",\"gameplay\":{\"root\":\"" + root + "\"}}");
}

fs::path example_pack(PackTest& test) {
  const fs::path fixture = fs::path(MW3_SOURCE_DIR).parent_path().parent_path() /
                           "tests/fixtures/packs/valid/gameplay-only";
  const fs::path pack = test.library / "example-gameplay";
  fs::copy(fixture, pack, fs::copy_options::recursive);
  return pack;
}
}  // namespace

TEST(pack_library_fixture_restores_write_directory) {
  struct RestoreMounts {
    const zutl::Mounts before = zutl::mounts();
    ~RestoreMounts() { zutl::mounts() = before; }
  } restore;
  const std::string previous_write = (fs::path(MW3_TEST_TMP) / "previous-write").generic_string();
  zutl::set_write_dir(previous_write);
  {
    PackTest test;
    EXPECT(zutl::mounts().write == test.write);
  }
  EXPECT(zutl::mounts().write == previous_write);
}

TEST(pack_library_fixture_lists_mounts_ticks_and_hashes_like_player_mod) {
  PackTest test;
  const fs::path pack = example_pack(test);
  const auto before = snapshot(test.library);
  std::vector<std::string> log;
  const auto found = mech3::mods_found(test.write, &log);
  EXPECT(found.size() == 1 && log.empty());
  if (found.size() != 1) return;
  EXPECT(found[0].folder == "example-gameplay" && found[0].from_pack && found[0].error.empty());
  EXPECT(fs::equivalent(found[0].path, pack / "mod"));
  const auto entries = mech3::official_entries();
  const auto* ia = mech3::find_entry(entries, "ia");
  EXPECT(ia != nullptr);
  if (!ia) return;
  EXPECT(mech3::entry_save_ticks(test.write, *ia, {"example-gameplay"}));
  const auto enabled = mech3::entry_mount_list(test.write, *ia);
  EXPECT(enabled == std::vector<std::string>{"example-gameplay"});
  log = mech3::mods_mount(test.write, enabled, {});
  for (const auto& line : log) std::printf("%s\n", line.c_str());
  EXPECT(contains(log, "mounted [pack]"));
  EXPECT(zutl::mounts().mods == std::vector<std::string>{found[0].path});
  EXPECT(fs::equivalent(zutl::find("about_this_mod.txt"), pack / "mod/about_this_mod.txt"));
  EXPECT(!fs::exists(fs::path(test.write) / "mods"));
  const auto listed = mech3::mods_list(test.write, enabled);
  EXPECT(listed.size() == 1 && listed[0].on && mech3::mods_row_text(listed[0]).find("[pack]") != std::string::npos);
  const auto hash = mech3::mods_gameplay_hash(test.write, enabled);
  const std::string install = (test.root / "install").generic_string();
  const auto mounted_hash = mech3::mods_gameplay_hash(test.write, enabled, &install);
  EXPECT(hash != 0 && mounted_hash != 0);
  fs::create_directories(fs::path(test.write) / "mods");
  fs::copy(pack / "mod", fs::path(test.write) / "mods/example-gameplay", fs::copy_options::recursive);
  mech3::mods_pack_library().clear();
  EXPECT(mech3::mods_gameplay_hash(test.write, enabled) == hash);
  EXPECT(mech3::mods_gameplay_hash(test.write, enabled, &install) == mounted_hash);
  EXPECT(snapshot(test.library) == before);
}

namespace {
void set_word(std::vector<uint8_t>& bytes, size_t offset, uint32_t value) {
  std::memcpy(bytes.data() + offset, &value, 4);
}

std::vector<uint8_t> material_table(const std::vector<float>& colors) {
  std::vector<uint8_t> bytes(4 + colors.size() * 0x28, 0);
  set_word(bytes, 0, static_cast<uint32_t>(colors.size()));
  for (size_t i = 0; i < colors.size(); ++i) {
    bytes[4 + i * 0x28] = 255;
    bytes[5 + i * 0x28] = 0x10;
    std::memcpy(bytes.data() + 8 + i * 0x28, &colors[i], 4);
  }
  return bytes;
}

// cls_mechlib.cpp read_node/read_model: Object3d, model header, 3 vertices,
// one polygon, then its vertex indices. Each test tree has real geometry.
std::vector<uint8_t> model_tree(const std::string& name, uint32_t material = 0) {
  std::vector<uint8_t> bytes(0xd0 + 0x90, 0);
  std::memcpy(bytes.data(), name.c_str(), name.size() + 1);
  const int32_t object_class = 5;
  std::memcpy(bytes.data() + 0x34, &object_class, 4);
  set_word(bytes, 0x3c, 1);
  const size_t header = bytes.size();
  bytes.resize(header + 0x5c + 3 * 12 + 0x24 + 3 * 4);
  set_word(bytes, header + 0x10, 1);
  set_word(bytes, header + 0x14, 3);
  set_word(bytes, header + 0x34, 1);
  set_word(bytes, header + 0x38, 1);
  const float vertices[9] = {0, 0, 0, 1, 0, 0, 0, 1, 0};
  std::memcpy(bytes.data() + header + 0x5c, vertices, sizeof vertices);
  const size_t polygon = header + 0x5c + sizeof vertices;
  set_word(bytes, polygon, 3);
  set_word(bytes, polygon + 0x1c, material);
  set_word(bytes, polygon + 0x24 + 4, 1);
  set_word(bytes, polygon + 0x24 + 8, 2);
  return bytes;
}

void model_archive(const fs::path& path,
                   const std::vector<std::pair<std::string, std::string>>& models,
                   const std::vector<float>& colors = {1}, uint32_t material = 0) {
  fs::create_directories(path.parent_path());
  const bool confined = zutl::mounts().confined;
  zutl::mounts().confined = false;  // authored fixtures use host paths
  zutl_zar::Archive archive;
  zutl_zar::init(archive);
  EXPECT(zutl_zar::create(archive, path.string().c_str()));
  if (archive.file) {
    const uint32_t version = 27, format = 1;
    const auto materials = material_table(colors);
    zutl_zar::add(archive, "version", &version, 4);
    zutl_zar::add(archive, "format", &format, 4);
    zutl_zar::add(archive, "materials", materials.data(), static_cast<uint32_t>(materials.size()));
    for (const auto& model : models) {
      const auto bytes = model_tree(model.second, material);
      zutl_zar::add(archive, model.first.c_str(), bytes.data(), static_cast<uint32_t>(bytes.size()));
    }
  }
  zutl_zar::destroy(archive);
  zutl::mounts().confined = confined;
}

struct ModelLibraryTest {
  PackTest files;
  const fs::path install = files.root / "install";

  ModelLibraryTest() {
    if (zmod::models().slots.empty()) zmod::reset_pool();
    model_archive(install / "zbd/mechlib.zbd", {{"mech_stock.flt", "stock"}});
  }
  ~ModelLibraryTest() { mech3::mech_rows_clear(); }

  fs::path mod(const std::string& name, bool pack = false) {
    const fs::path folder = pack ? files.library / name / "mod" : fs::path(files.write) / "mods" / name;
    if (pack) manifest(files.library / name, name);
    put(folder / "mod.txt", "name=" + name + "\n");
    return folder;
  }
  std::vector<std::string> mount(const std::vector<std::string>& enabled) {
    zutl::mounts() = {};
    zutl::set_write_dir(files.write);
    zutl::mounts().confined = true;
    auto log = mech3::mods_mount(files.write, enabled, {install.generic_string()});
    zutl::mount(install.generic_string());
    return log;
  }
};

// Exercises the actual game reader, including the merged archive's lifetime.
void expect_models(const std::vector<std::pair<std::string, std::string>>& models) {
  zcls::MechLib library;
  zutl_zar::init(library.archive);
  const bool opened = zcls::mechlib_open(library, "zbd\\mechlib.zbd");
  EXPECT(opened);
  if (opened) {
    for (const auto& model : models) {
      zcls::Node* node = zcls::mechlib_load(library, model.first.c_str());
      EXPECT(node != nullptr);
      if (node) EXPECT(std::string(node->name()) == model.second);
    }
  }
  const std::vector<zcls::Node*> trees(library.trees.begin(), library.trees.end());
  zcls::mechlib_close(library);
  for (zcls::Node* tree : trees) zcls::node_destroy(tree);
}

std::vector<std::string> model_library_log() {
  zutl_zar::Archive archive;
  zutl_zar::init(archive);
  std::vector<std::string> log;
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd", &log));
  EXPECT(mech3::model_library_close(archive));
  return log;
}
}  // namespace

TEST(model_library_two_mods_keep_each_others_models_and_stock) {
  const std::vector<std::pair<bool, bool>> pack_sources = {{false, false}, {false, true}, {true, true}};
  for (const auto& packs : pack_sources) {
    ModelLibraryTest test;
    const auto one = test.mod("one", packs.first), two = test.mod("two", packs.second);
    model_archive(one / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}});
    model_archive(two / "ZBD/MECHLIB.ZBD", {{"mech_two.flt", "two"}});
    const auto pack_before = snapshot(test.files.library);
    const auto install_before = snapshot(test.install);
    test.mount({"one", "two"});
    expect_models({{"mech_one.flt", "one"}, {"mech_two.flt", "two"}, {"mech_stock.flt", "stock"}});
    test.mount({"two", "one"});
    expect_models({{"mech_one.flt", "one"}, {"mech_two.flt", "two"}, {"mech_stock.flt", "stock"}});
    EXPECT(snapshot(test.files.library) == pack_before);
    EXPECT(snapshot(test.install) == install_before);
  }
}

TEST(model_library_same_entry_uses_tick_order_then_write_directory) {
  ModelLibraryTest test;
  const auto one = test.mod("one"), two = test.mod("two", true);
  model_archive(one / "zbd/mechlib.zbd", {{"mech_shared.flt", "first"}});
  model_archive(two / "zbd/mechlib.zbd", {{"MECH_SHARED.FLT", "second"}});
  test.mount({"one", "two"});
  const auto log = model_library_log();
  EXPECT(std::count_if(log.begin(), log.end(), [&](const std::string& line) {
    return line.find("entry mech_shared.flt from " + (two / "zbd/mechlib.zbd").generic_string()) != std::string::npos &&
           line.find((one / "zbd/mechlib.zbd").generic_string() + " wins") != std::string::npos;
  }) == 1);
  expect_models({{"mech_shared.flt", "first"}, {"mech_stock.flt", "stock"}});
  test.mount({"two", "one"});
  expect_models({{"mech_shared.flt", "second"}, {"mech_stock.flt", "stock"}});
  model_archive(fs::path(test.files.write) / "zbd/mechlib.zbd", {{"mech_shared.flt", "write"}});
  test.mount({"two", "one"});
  expect_models({{"mech_shared.flt", "write"}, {"mech_stock.flt", "stock"}});
}

TEST(model_library_no_archive_and_no_mods_keep_the_original_path) {
  ModelLibraryTest test;
  test.mod("empty");
  test.mount({"empty"});
  expect_models({{"mech_stock.flt", "stock"}});
  EXPECT(fs::equivalent(zutl::find("zbd/mechlib.zbd"), test.install / "zbd/mechlib.zbd"));
  test.mount({});
  expect_models({{"mech_stock.flt", "stock"}});
  zutl_zar::Archive archive;
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  EXPECT(!mech3::model_library_is_merged(archive));
  mech3::model_library_close(archive);
}

TEST(model_library_unreadable_archive_does_not_hide_other_sources) {
  ModelLibraryTest test;
  const auto broken = test.mod("broken"), good = test.mod("good");
  put(broken / "zbd/mechlib.zbd", "not an archive");
  model_archive(good / "zbd/mechlib.zbd", {{"mech_good.flt", "good"}});
  test.mount({"broken", "good"});
  const auto log = model_library_log();
  EXPECT(std::count_if(log.begin(), log.end(), [&](const std::string& line) {
    return line.find((broken / "zbd/mechlib.zbd").generic_string() +
                     ": mechlib.zbd cannot be read, its models left out") != std::string::npos;
  }) == 1);
  expect_models({{"mech_good.flt", "good"}, {"mech_stock.flt", "stock"}});
  test.mount({"good", "broken"});
  expect_models({{"mech_good.flt", "good"}, {"mech_stock.flt", "stock"}});
}

TEST(model_library_bad_entry_ranges_names_and_headers_leave_the_whole_source_out) {
  ModelLibraryTest test;
  const auto broken = test.mod("broken"), good = test.mod("good");
  const fs::path archive = broken / "zbd/mechlib.zbd";
  model_archive(good / "zbd/mechlib.zbd", {{"mech_good.flt", "good"}});
  model_archive(archive, {{"mech_bad.flt", "bad"}});
  const std::string valid = read(archive);
  // These corruptions leave enough of the table intact for the legacy opener:
  // an entry in table bytes, a name with no terminator, and an incompatible version.
  const size_t last_entry = valid.size() - 8 - sizeof(zutl_zar::Entry);
  for (int corruption = 0; corruption < 3; ++corruption) {
    std::string bytes = valid;
    if (corruption == 0) {
      const uint32_t table_start = static_cast<uint32_t>(valid.size() - 8 - 4 * sizeof(zutl_zar::Entry));
      std::memcpy(bytes.data() + last_entry, &table_start, 4);
    } else if (corruption == 1) {
      std::memset(bytes.data() + last_entry + 8, 'x', 64);
    } else {
      bytes[0] = 0;
    }
    put(archive, bytes);
    test.mount({"broken", "good"});
    EXPECT(contains(model_library_log(), "mechlib.zbd cannot be read, its models left out"));
    expect_models({{"mech_good.flt", "good"}, {"mech_stock.flt", "stock"}});
    // Presence is table-only. A corrupt version payload is rejected by open,
    // while corrupt entry ranges/names are already rejected by the lookup.
    EXPECT(mech3::model_library_has(archive.generic_string(), "mech_bad.flt") == (corruption == 2));
  }
}

TEST(model_library_missing_model_warning_searches_all_sources) {
  ModelLibraryTest test;
  const auto rows = test.mod("rows"), models = test.mod("models");
  put(rows / "mod.txt", "name=Rows\nmech=scout tech=any mass=20 class=light model=remote\n"
                         "mech=absent tech=any mass=20 class=light model=missing\n");
  put(rows / "zbd/dfn_scout.zrd", "(version (2))\n");
  put(rows / "zbd/dfn_absent.zrd", "(version (2))\n");
  model_archive(rows / "zbd/mechlib.zbd", {{"mech_local.flt", "local"}});
  model_archive(models / "zbd/mechlib.zbd", {{"mech_remote.flt", "remote"}});
  const auto log = test.mount({"rows", "models"});
  EXPECT(mech3::mech_index("scout") >= 20);
  EXPECT(!contains(log, "no mech_remote.flt"));
  EXPECT(contains(log, "no mech_missing.flt in mechlib.zbd"));
  EXPECT(mech3::mech_index("absent") == -1);
  model_archive(fs::path(test.files.write) / "zbd/mechlib.zbd", {{"mech_missing.flt", "write"}});
  const auto with_write_model = test.mount({"rows", "models"});
  EXPECT(mech3::mech_index("absent") >= 20);
  EXPECT(!contains(with_write_model, "no mech_missing.flt"));
}

namespace {
void expect_materials(const std::vector<std::pair<std::string, float>>& expected) {
  zcls::MechLib library;
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  for (const auto& item : expected) {
    zcls::Node* node = zcls::mechlib_load(library, item.first.c_str());
    EXPECT(node && node->model && node->model->count(0x10) == 1);
    if (node && node->model && node->model->count(0x10) == 1) {
      const auto* material = node->model->polygons[0].material;
      EXPECT(material != nullptr);
      if (material) EXPECT(material->r == item.second);
    }
  }
  const std::vector<zcls::Node*> trees(library.trees.begin(), library.trees.end());
  zcls::mechlib_close(library);
  for (auto* tree : trees) zcls::node_destroy(tree);
}

void replace_entries(const fs::path& path, const std::vector<mech3::ArchiveEntry>& entries) {
  const bool confined = zutl::mounts().confined;
  zutl::mounts().confined = false;
  zutl_zar::Archive archive;
  EXPECT(zutl_zar::create(archive, path.string().c_str()));
  if (archive.file)
    for (const auto& entry : entries)
      zutl_zar::add(archive, entry.name.c_str(), entry.data.data(), static_cast<uint32_t>(entry.data.size()));
  zutl_zar::destroy(archive);
  zutl::mounts().confined = confined;
}
}  // namespace

TEST(model_library_review_materials_belong_to_each_model) {
  ModelLibraryTest test;
  const auto one = test.mod("one"), two = test.mod("two", true);
  model_archive(test.install / "zbd/mechlib.zbd", {{"mech_stock.flt", "stock"}}, {10, 10}, 1);
  model_archive(one / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}}, {10, 20}, 1);
  model_archive(two / "zbd/mechlib.zbd", {{"mech_two.flt", "two"}}, {10, 30, 40}, 2);
  for (const auto& order : {std::vector<std::string>{"one", "two"}, {"two", "one"}}) {
    test.mount(order);
    expect_materials({{"mech_stock.flt", 10}, {"mech_one.flt", 20}, {"mech_two.flt", 40}});
    zutl_zar::Archive archive;
    EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
    // The base's duplicate material slots must stay in place, while the mods'
    // copies of the same content reuse the first base slot.
    uint32_t index = 0;
    const int entry = zutl_zar::find(archive, "mech_stock.flt");
    std::FILE* file = zutl_zar::seek(archive, entry, nullptr);
    if (file) {
      std::fseek(file, 0xd0 + 0x90 + 0x5c + 3 * 12 + 0x1c, SEEK_CUR);
      EXPECT(std::fread(&index, 4, 1, file) == 1 && index == 1);
    } else EXPECT(false);
    mech3::model_library_close(archive);
  }
}

TEST(model_library_review_rewrite_keeps_the_source_model_fingerprint) {
  ModelLibraryTest test;
  const auto mod = test.mod("one");
  model_archive(mod / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}}, {20}, 0);
  const auto original = model_tree("one", 0);
  platform::integrity::Sha256 hash;
  hash.update(original.data(), original.size());
  test.mount({"one"});
  zcls::MechLib library;
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  auto* node = zcls::mechlib_load(library, "mech_one.flt");
  EXPECT(node && node->source_asset && node->source_asset->member_sha256 == hash.hex());
  zcls::mechlib_close(library);
  if (node) zcls::node_destroy(node);
}

TEST(model_library_review_bad_model_or_missing_materials_cannot_hide_stock) {
  ModelLibraryTest test;
  const auto mod = test.mod("bad");
  const auto path = mod / "zbd/mechlib.zbd";
  model_archive(path, {{"mech_stock.flt", "bad"}}, {20});
  std::vector<mech3::ArchiveEntry> valid;
  EXPECT(mech3::archive_read_entries(path.generic_string(), &valid));
  for (int problem = 0; problem < 7; ++problem) {
    auto entries = valid;
    auto& tree = entries.back().data;
    const size_t header = 0xd0 + 0x90;
    const size_t polygon = header + 0x5c + 3 * 12;
    if (problem == 0) set_word(tree, polygon + 0x1c, 99);
    if (problem == 1) tree.pop_back();
    if (problem == 2) set_word(tree, header + 0x10, UINT32_MAX);
    if (problem == 3) set_word(tree, polygon + 0x24, 99);
    if (problem == 4) set_word(tree, 0x5c, 1);  // claims a child not present
    if (problem == 5) entries.erase(entries.begin() + 2);  // missing materials
    if (problem == 6) entries[2].data = {255, 255, 255, 127};  // unreadable table
    replace_entries(path, entries);
    test.mount({"bad"});
    const auto log = model_library_log();
    if (problem == 5) {
      // An absent table inherits the base; an unreadable one still refuses models.
      EXPECT(!contains(log, path.generic_string() + ": entry mech_stock.flt:"));
    } else {
      EXPECT(contains(log, path.generic_string() + ": entry mech_stock.flt:"));
      EXPECT(contains(log, "left out"));
    }
    expect_materials({{"mech_stock.flt", 1}});
  }
}

TEST(model_library_review_overlapping_entries_and_table_only_presence) {
  ModelLibraryTest test;
  const auto bad = test.mod("bad");
  const auto file = bad / "zbd/mechlib.zbd";
  model_archive(file, {{"mech_bad.flt", "bad"}});
  std::string bytes = read(file);
  const size_t table = bytes.size() - 8 - 4 * sizeof(zutl_zar::Entry);
  for (size_t i = 0; i < 4; ++i) {
    const uint32_t start = 0, length = static_cast<uint32_t>(table);
    std::memcpy(bytes.data() + table + i * sizeof(zutl_zar::Entry), &start, 4);
    std::memcpy(bytes.data() + table + i * sizeof(zutl_zar::Entry) + 4, &length, 4);
    if (i < 3) {
      const std::string name = "entry_" + std::to_string(i);
      std::memset(bytes.data() + table + i * sizeof(zutl_zar::Entry) + 8, 0, 64);
      std::memcpy(bytes.data() + table + i * sizeof(zutl_zar::Entry) + 8, name.data(), name.size());
    }
  }
  put(file, bytes);
  EXPECT(!mech3::model_library_has(file.generic_string(), "mech_bad.flt"));
  test.mount({"bad"});
  EXPECT(contains(model_library_log(), "cannot be read"));
  expect_materials({{"mech_stock.flt", 1}});
  model_archive(file, {{"mech_bad.flt", "bad"}});
  bytes = read(file);
  bytes[0] = 0;  // table-only lookup must not read even the version payload
  put(file, bytes);
  EXPECT(mech3::model_library_has(file.generic_string(), "mech_bad.flt"));
}

TEST(model_library_review_nested_geometry_and_optional_polygon_arrays) {
  ModelLibraryTest test;
  const auto mod = test.mod("one");
  const auto path = mod / "zbd/mechlib.zbd";
  model_archive(path, {{"mech_one.flt", "parent"}}, {20, 30});
  std::vector<mech3::ArchiveEntry> entries;
  EXPECT(mech3::archive_read_entries(path.generic_string(), &entries));
  auto& tree = entries.back().data;
  const size_t header = 0xd0 + 0x90;
  const size_t vectors = header + 0x5c + 3 * 12;
  tree.insert(tree.begin() + vectors, 6 * 12, 0);  // three normals, three morphs
  set_word(tree, header + 0x18, 3);
  set_word(tree, header + 0x1c, 3);
  const size_t polygon = vectors + 6 * 12;
  set_word(tree, polygon, 0x203);
  set_word(tree, polygon + 0x0c, 1);
  set_word(tree, polygon + 0x10, 1);
  set_word(tree, polygon + 0x14, 1);
  const size_t normals = tree.size();
  tree.resize(tree.size() + 3 * 4 + 3 * 8 + 3 * 12);
  set_word(tree, normals + 4, 1);
  set_word(tree, normals + 8, 2);
  set_word(tree, 0x5c, 1);
  const auto child = model_tree("child", 1);
  tree.insert(tree.end(), child.begin(), child.end());
  replace_entries(path, entries);
  test.mount({"one"});
  zcls::MechLib library;
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  auto* parent = zcls::mechlib_load(library, "mech_one.flt");
  EXPECT(parent && parent->model && parent->child_count() == 1);
  if (parent && parent->model && parent->child_count() == 1) {
    auto* child_node = parent->children[0];
    EXPECT(parent->model->polygons[0].material->r == 20);
    EXPECT(child_node->model && child_node->model->polygons[0].material->r == 30);
    EXPECT(parent->model->normals && parent->model->morphs);
    EXPECT(parent->model->polygons[0].normal_indices && parent->model->polygons[0].uvs &&
           parent->model->polygons[0].colors);
  }
  zcls::mechlib_close(library);
  if (parent) zcls::node_destroy(parent);
}

TEST(model_library_review_texture_material_content_ignores_presence_pointer_values) {
  ModelLibraryTest test;
  for (int i = 0; i < 2; ++i) {
    const std::string name = i ? "two" : "one";
    const auto path = test.mod(name) / "zbd/mechlib.zbd";
    model_archive(path, {{"mech_" + name + ".flt", name}});
    std::vector<mech3::ArchiveEntry> entries;
    EXPECT(mech3::archive_read_entries(path.generic_string(), &entries));
    auto& materials = entries[2].data;
    materials[5] = 0x11;  // textured
    set_word(materials, 4 + 0x10, i ? 123 : 456);
    const size_t length = materials.size();
    materials.resize(length + 4 + 4);
    set_word(materials, length, 4);
    std::memcpy(materials.data() + length + 4, "skin", 4);
    replace_entries(path, entries);
  }
  test.mount({"one", "two"});
  zcls::MechLib library;
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  EXPECT(library.materials.size() == 2);  // stock plus one shared textured material
  if (library.materials.size() == 2)
    EXPECT(library.materials[1]->texture && std::string(library.materials[1]->texture) == "skin");
  zcls::mechlib_close(library);
}

TEST(model_library_review_write_only_and_plain_stream_ownership) {
  ModelLibraryTest test;
  test.mod("rows");
  test.mount({"rows"});
  zutl_zar::Archive archive;
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  EXPECT(!mech3::model_library_is_merged(archive));
  mech3::model_library_close(archive);
  model_archive(fs::path(test.files.write) / "ZBD/MECHLIB.ZBD", {{"mech_write.flt", "write"}}, {50});
  for (const auto& enabled : {std::vector<std::string>{}, {"rows"}}) {
    test.mount(enabled);
    EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
    EXPECT(mech3::model_library_is_merged(archive));
    mech3::model_library_close(archive);
    expect_materials({{"mech_stock.flt", 1}, {"mech_write.flt", 50}});
  }
}

TEST(model_library_review_reopen_keeps_a_live_owned_stream) {
  ModelLibraryTest test;
  const auto mod = test.mod("one");
  model_archive(mod / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}});
  test.mount({"one"});
  zutl_zar::Archive archive;
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  const bool live = mech3::model_library_is_merged(archive);
  EXPECT(live);
  // Avoid dereferencing the known dangling baseline FILE*; ownership is checked
  // first so this regression can fail without invoking undefined behavior.
  if (live) {
    uint32_t version = 0, size = 4;
    EXPECT(zutl_zar::read(archive, zutl_zar::find(archive, "version"), &version, &size) == 0);
    EXPECT(version == 27);
  }
  mech3::model_library_close(archive);
  EXPECT(!mech3::model_library_is_merged(archive));
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  zutl_zar::close(archive);  // recover a legacy close without closing its FILE* twice
  EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
  EXPECT(mech3::model_library_is_merged(archive));
  mech3::model_library_close(archive);
  zcls::MechLib library;
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  model_archive(mod / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}}, {60});
  EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
  zcls::Node* node = zcls::mechlib_load(library, "mech_one.flt");
  EXPECT(node && node->model && node->model->polygons[0].material);
  if (node && node->model && node->model->polygons[0].material)
    EXPECT(node->model->polygons[0].material->r == 60);
  zcls::mechlib_close(library);
  if (node) zcls::node_destroy(node);
}

TEST(model_library_review_repeated_names_are_not_self_conflicts) {
  ModelLibraryTest test;
  const auto mod = test.mod("one");
  model_archive(mod / "zbd/mechlib.zbd", {{"mech_one.flt", "first"}, {"MECH_ONE.FLT", "second"}});
  test.mount({"one"});
  const auto log = model_library_log();
  EXPECT(contains(log, "repeated entry mech_one.flt"));
  EXPECT(!contains(log, "entry mech_one.flt from"));
  expect_models({{"mech_one.flt", "first"}});
}

TEST(pack_library_player_folder_clash_wins_even_without_mod_txt) {
  PackTest test;
  example_pack(test);
  for (bool valid_mod : {false, true}) {
    fs::create_directories(fs::path(test.write) / "mods/example-gameplay");
    if (valid_mod) put(fs::path(test.write) / "mods/example-gameplay/mod.txt", "name=Player\n");
    std::vector<std::string> log;
    const auto found = mech3::mods_found(test.write, &log);
    EXPECT(found.size() == 1 && !found[0].from_pack);
    EXPECT(contains(log, "pack-id-clash") && contains(log, "example-gameplay"));
    EXPECT(!found.empty() && (valid_mod ? found[0].error.empty() : !found[0].error.empty()));
  }
}

TEST(pack_library_tick_order_and_player_write_directory_take_precedence) {
  PackTest test;
  manifest(test.library / "example-pack", "example-pack");
  put(test.library / "example-pack/mod/mod.txt", "name=Pack\n");
  put(test.library / "example-pack/mod/zbd/order.zrd", "pack");
  put(fs::path(test.write) / "mods/player/mod.txt", "name=Player\n");
  put(fs::path(test.write) / "mods/player/zbd/order.zrd", "player");
  const auto entries = mech3::official_entries();
  const auto* ia = mech3::find_entry(entries, "ia");
  EXPECT(ia != nullptr);
  if (!ia) return;
  for (const std::vector<std::string>& ticks : {std::vector<std::string>{"example-pack", "player"},
                                              std::vector<std::string>{"player", "example-pack"}}) {
    EXPECT(mech3::entry_save_ticks(test.write, *ia, ticks));
    const auto mounted = mech3::entry_mount_list(test.write, *ia);
    EXPECT(mounted == ticks);
    zutl::mounts() = {};
    zutl::set_write_dir(test.write);
    mech3::mods_mount(test.write, mounted, {});
    EXPECT(read(zutl::find("zbd/order.zrd")) == (ticks.front() == "player" ? "player" : "pack"));
  }
  put(fs::path(test.write) / "zbd/order.zrd", "write dir");
  EXPECT(read(zutl::find("zbd/order.zrd")) == "write dir");
}

TEST(pack_library_read_only_deletion_and_game_writes) {
  PackTest test;
  manifest(test.library / "example-pack", "example-pack");
  put(test.library / "example-pack/mod/mod.txt", "name=Pack\ncampaign=story.txt\n");
  put(test.library / "example-pack/mod/story.txt", "id=story\nname=Story\nmission=c1 1\n");
  put(test.library / "example-pack/mod/zbd/test.zrd", "pack data");
  const auto before = snapshot(test.library);
  const auto plan = mech3::delete_plan_for_mod(test.write, "example-pack");
  EXPECT(plan.kind == mech3::DeletePlan::kNone && plan.refused.find("launcher") != std::string::npos);
  std::string why;
  EXPECT(!mech3::delete_run(test.write, plan, &why));
  const auto campaign_plan = mech3::delete_plan_for_entry(test.write, "example-pack~story");
  EXPECT(campaign_plan.kind == mech3::DeletePlan::kNone && campaign_plan.refused.find("launcher") != std::string::npos);
  mech3::mods_mount(test.write, {"example-pack"}, {});
  EXPECT(zutl::write_path("zbd/test.zrd") == test.write + "/zbd/test.zrd");
  std::FILE* output = zutl::open("zbd/test.zrd", "wb");
  EXPECT(output != nullptr);
  if (output) {
    std::fputs("player change", output);
    std::fclose(output);
  }
  EXPECT(read(fs::path(test.write) / "zbd/test.zrd") == "player change");
  EXPECT(snapshot(test.library) == before);
}

TEST(pack_library_broken_and_legacy_sources_are_skipped_without_stopping_discovery) {
  PackTest test;
  example_pack(test);
  fs::create_directories(test.library / "missing-manifest");
  put(test.library / "unreadable-manifest/pack.json/child", "directory, not a file");
  put(test.library / "malformed/pack.json", "{");
  manifest(test.library / "missing-mod", "missing-mod");
  manifest(test.library / "bad-root", "bad-root", "../outside");
  put(test.library / "duplicate-key/pack.json", "{\"schema_version\":3,\"schema_version\":2}");
  for (const std::string& schema : {"1", "2"}) {
    put(test.library / ("ignored-" + schema) / "pack.json", "{\"schema_version\":" + schema +
        ",\"gameplay\":{\"root\":\"mod\"}}");
  }
  put(test.library / "ignored-visuals/pack.json", "{\"schema_version\":3,\"visuals\":[]}");
  std::vector<std::string> log;
  EXPECT(mech3::mods_found(test.write, &log).size() == 1);
  for (const char* name : {"missing-manifest", "unreadable-manifest", "malformed", "missing-mod", "bad-root", "duplicate-key"})
    EXPECT(contains(log, name));
  EXPECT(log.size() == 6 && !contains(log, "ignored-"));
  for (const auto& line : log) std::printf("%s\n", line.c_str());
  mech3::mods_pack_library().clear();
  EXPECT(mech3::mods_found(test.write).empty());
}

TEST(pack_library_unsafe_roots_and_missing_library_are_reported) {
  PackTest test;
  std::vector<std::string> roots = {"../outside", "/outside", "mod//data", "mod/", "mod.", "mod "};
  std::vector<std::string> devices = {"CON", "CONIN$", "CONOUT$", "PRN", "AUX", "NUL"};
  for (int i = 0; i <= 9; ++i) {
    devices.push_back("COM" + std::to_string(i));
    devices.push_back("LPT" + std::to_string(i));
  }
  for (const std::string& device : devices) {
    roots.push_back(device);
    roots.push_back("nested/" + device + ".data");
  }
  for (const std::string& root : roots) {
    manifest(test.library / "unsafe", "unsafe", root);
    std::vector<std::string> log;
    EXPECT(mech3::mods_found(test.write, &log).empty());
    EXPECT(contains(log, "path-unsafe"));
  }
  mech3::mods_pack_library() = (test.root / "missing-library").generic_string();
  std::vector<std::string> log;
  EXPECT(mech3::mods_found(test.write, &log).empty());
  EXPECT(contains(log, "cannot read pack library"));
}

TEST(pack_library_folder_must_match_manifest_id) {
  PackTest test;
  example_pack(test);
  for (const char* name : {"folder-a", "folder-b"}) {
    manifest(test.library / name, "same-id");
    put(test.library / name / "mod/mod.txt", "name=Same\n");
  }
  std::vector<std::string> log;
  EXPECT(mech3::mods_found(test.write, &log).size() == 1);
  EXPECT(log.size() == 2 && contains(log, "folder-a") && contains(log, "folder-b"));
  EXPECT(contains(log, "manifest-invalid") && !contains(log, "pack-id-clash"));
  fs::remove_all(test.library / "example-gameplay");
  const auto missing = mech3::mods_mount(test.write, {"example-gameplay"}, {});
  EXPECT(contains(missing, (test.library / "example-gameplay").generic_string()));
}

TEST(pack_library_unusable_mods_remain_listed_like_player_mods) {
  PackTest test;
  manifest(test.library / "unusable", "unusable");
  for (const char* contents : {"name=Wrong game\nfor=mw3pm\n", "description=No name\n"}) {
    put(test.library / "unusable/mod/mod.txt", contents);
    put(fs::path(test.write) / "mods/player/mod.txt", contents);
    std::vector<std::string> log;
    const auto found = mech3::mods_found(test.write, &log);
    EXPECT(found.size() == 2);
    if (found.size() != 2) return;
    EXPECT(!found[0].error.empty() && found[0].error == found[1].error);
    EXPECT(found[1].from_pack && contains(log, "mod unusable"));
    EXPECT(!contains(log, "gameplay-root-invalid"));
    const auto mounted = mech3::mods_mount(test.write, {"unusable"}, {});
    EXPECT(contains(mounted, found[1].error) && zutl::mounts().mods.empty());
  }
}

TEST(pack_library_metadata_bom_and_size_limits) {
  PackTest test;
  const fs::path pack = example_pack(test);
  put(pack / "pack.json", "\xef\xbb\xbf" + read(pack / "pack.json"));
  put(pack / "mod/mod.txt", "\xef\xbb\xbf" + read(pack / "mod/mod.txt"));
  std::vector<std::string> log;
  auto found = mech3::mods_found(test.write, &log);
  EXPECT(found.size() == 1 && log.empty() && found[0].error.empty());
  fs::resize_file(pack / "pack.json", 4 * 1024 * 1024 + 1);
  log.clear();
  EXPECT(mech3::mods_found(test.write, &log).empty());
  EXPECT(contains(log, "manifest-invalid") && contains(log, "pack.json exceeds 4194304 bytes"));
  manifest(pack, "example-gameplay");
  fs::resize_file(pack / "mod/mod.txt", 1024 * 1024 + 1);
  log.clear();
  found = mech3::mods_found(test.write, &log);
  EXPECT(found.size() == 1 && !found[0].error.empty());
  EXPECT(contains(log, "mod.txt exceeds 1048576 bytes") && !contains(log, "gameplay-root-invalid"));
  int errors = 0;
  EXPECT(contains(mech3::mod_check((pack / "mod").string(), "", &errors), "exceeds 1048576 bytes"));
  EXPECT(errors > 0);
  const auto exported = mech3::mod_export((pack / "mod").string(), (test.root / "large.zip").string());
  EXPECT(!exported.ok && exported.message.find("exceeds 1048576 bytes") != std::string::npos);
}

TEST(pack_library_mods_screen_uses_real_paths_and_refuses_library_writes) {
  PackTest test;
  const fs::path payload = test.library / "example-pack/mod";
  manifest(payload.parent_path(), "example-pack");
  put(payload / "mod.txt", "name=Pack\ncampaign=story.txt\n");
  put(payload / "story.txt", "name=Story\nmission=c1 1\n");
  const auto before = snapshot(test.library);
  const auto old_platform = mech3::mods_menu_platform();
  const auto old_write = mech3::mods_menu_write_dir();
  struct RestoreMenu {
    mech3::ModsMenuPlatform platform;
    std::string write;
    ~RestoreMenu() { mech3::mods_menu_platform() = platform; mech3::mods_menu_write_dir() = write; }
  } restore{old_platform, old_write};
  mech3::mods_menu_write_dir() = test.write;
  struct MenuEngine : mech3::Engine {
    int32_t fast_menu() override { return 1; }
  } engine;
  mech3::ModsScreen screen(engine, 0);
  screen.entry = "example-pack~story";
  screen.refill();
  std::string opened;
  mech3::mods_menu_platform().open_folder = [&](const std::string& path) { opened = path; return true; };
  screen.on_button(mech3::ModsScreen::kOpenFolder, 0, 0);
  EXPECT(opened == payload.generic_string());
  screen.report();
  EXPECT(read(screen.report_file).find(payload.generic_string()) != std::string::npos);
  EXPECT(read(screen.report_file).find("mods\\example-pack") == std::string::npos);
  screen.on_button(mech3::ModsScreen::kOpenFolder, 0, 0);
  EXPECT(opened == mech3::mod_reports_dir(test.write));
  screen.export_folder = "example-pack";
  const fs::path exported = test.root / "pack.zip";
  screen.export_mod(exported.string());
  const std::string note = std::string(screen.note.text ? screen.note.text : "") + " " +
                           (screen.restart.text ? screen.restart.text : "");
#if MW3_HAVE_LIBARCHIVE
  EXPECT(fs::is_regular_file(exported) && note.find("Exported") != std::string::npos);
#else
  EXPECT(note.find("cannot write archives") != std::string::npos);
#endif
  for (const fs::path& target : {payload / "out.zip", payload.parent_path() / "out.zip", test.library / "out.zip"}) {
    const auto result = mech3::mod_export(payload.string(), target.string());
    EXPECT(!result.ok && result.message == mech3::kPackReadOnlyMessage);
  }
  EXPECT(!mech3::mods_path_in_pack_library((test.root / "library-other/out.zip").string()));
  std::error_code link_error;
  const fs::path alias = test.root / "library-link";
  fs::create_directory_symlink(test.library, alias, link_error);
  if (!link_error) {
    const auto result = mech3::mod_export(payload.string(), (alias / "out.zip").string());
    EXPECT(!result.ok && result.message == mech3::kPackReadOnlyMessage);
  } else {
    std::printf("not run: linked export destination (%s)\n", link_error.message().c_str());
  }
  std::string copy, why;
  EXPECT(mech3::save_as_make_copy(test.write, "example-pack~story", "Player copy", &copy, &why));
  EXPECT(fs::is_regular_file(fs::path(test.write) / "mods" / copy / "mod.txt"));
  EXPECT(snapshot(test.library) == before);
}

namespace {
// Reuse the authored triangle JSON shape from test_bounded_readers.cpp.
std::string review_triangle_json(const char* y) {
  const std::string box = "{\"a\": {\"x\": 0, \"y\": 0, \"z\": 0}, \"b\": {\"x\": 1, \"y\": 1, \"z\": 1}}";
  const std::string v = "{\"x\": 0, \"y\": 0, \"z\": 0}";
  return "{\"nodes\": [{\"name\": \"tiny.flt\", \"flags\": {\"active\": true, \"bbox_node\": true, \"tree_valid\": true}, \"update_flags\": 1,"
         " \"zone_id\": -1, \"model_index\": 0, \"area_partition\": null, \"virtual_partition\": null, \"parent_indices\": [],"
         " \"child_indices\": [], \"active_bbox\": \"Node\", \"node_bbox\": " + box + ", \"model_bbox\": " + box + ", \"child_bbox\": " + box +
         ", \"field192\": 0, \"field196\": 160, \"field200\": 0, \"field204\": 0, \"data\": {\"Object3d\": {\"opacity\": null, \"color\": null,"
         " \"unk\": 0.0, \"transform\": \"Initial\", \"signs\": 0}}, \"data_ptr\": 1, \"parent_array_ptr\": 0, \"child_array_ptr\": 0, \"index\": 1}],"
         " \"models\": [{\"model_type\": \"Default\", \"facade_mode\": \"CylindricalY\", \"flags\": {\"lighting\": true}, \"parent_count\": 1,"
         " \"vertices\": [" + v + ", {\"x\": 1, \"y\": " + y + ", \"z\": 0}, {\"x\": 0, \"y\": 1, \"z\": 1}], \"normals\": [], \"morphs\": [], \"lights\": [],"
         " \"polygons\": [{\"flags\": {}, \"priority\": 0, \"zone_set\": [], \"vertex_indices\": [0, 1, 2], \"normal_indices\": null,"
         " \"vertex_colors\": [{\"r\": 255, \"g\": 255, \"b\": 255}, {\"r\": 255, \"g\": 255, \"b\": 255}, {\"r\": 255, \"g\": 255, \"b\": 255}],"
         " \"materials\": [{\"material_index\": 0, \"uv_coords\": null}], \"vertex_indices_ptr\": 1, \"normal_indices_ptr\": 0, \"uvs_ptr\": 0,"
         " \"vertex_colors_ptr\": 1, \"matl_refs_ptr\": 0, \"materials_ptr\": 0}], \"texture_scroll\": {\"u\": 0, \"v\": 0},"
         " \"bbox_mid\": " + v + ", \"bbox_diag\": 1.5, \"polygons_ptr\": 1, \"vertices_ptr\": 1, \"normals_ptr\": 0, \"lights_ptr\": 0,"
         " \"morphs_ptr\": 0, \"material_refs_ptr\": 0}]}";
}
}  // namespace

TEST(model_library_review_later_json_and_zip_keep_their_materials) {
  for (bool zipped : {false, true}) {
    ModelLibraryTest test;
    const auto first = test.mod("first"), later = test.mod("later", true);
    model_archive(first / "zbd/mechlib.zbd", {{"mech_first.flt", "first"}}, {20});
    const std::string materials = "[{\"Colored\":{\"color\":{\"r\":70,\"g\":0,\"b\":0},\"alpha\":255}}]";
    if (zipped) {
      write_stored_zip((later / "zbd/mechlib.zip").string(),
                       {{"mech_json.flt.json", review_triangle_json("1")}, {"materials.json", materials}});
    } else {
      put(later / "zbd/mechlib/mech_json.flt.json", review_triangle_json("1"));
      put(later / "zbd/mechlib/materials.json", materials);
    }
    put(later / "mod.txt", "name=Later\nmech=jsonmech tech=any mass=20 class=light model=json\n");
    put(later / "zbd/dfn_jsonmech.zrd", "(version (2))\n");
    auto log = test.mount({"first", "later"});
    EXPECT(!contains(log, "no mech_json.flt"));
    expect_materials({{"mech_first.flt", 20}, {"mech_json.flt", 70}, {"mech_stock.flt", 1}});
    // A binary copy in the earlier source wins over a later JSON copy, too.
    model_archive(first / "zbd/mechlib.zbd", {{"mech_json.flt", "binary"}}, {20});
    test.mount({"first", "later"});
    expect_materials({{"mech_json.flt", 20}, {"mech_stock.flt", 1}});
  }
}

TEST(model_library_policy_missing_materials_inherit_only_base_slots) {
  for (int form = 0; form < 3; ++form) {
    ModelLibraryTest test;
    model_archive(test.install / "zbd/mechlib.zbd", {{"mech_stock.flt", "stock"}}, {10, 10}, 1);
    const auto extra = test.mod("extra"), inherited = test.mod("inherited");
    model_archive(extra / "zbd/mechlib.zbd", {{"mech_extra.flt", "extra"}}, {20, 30});
    std::vector<uint8_t> original;
    if (form == 0) {
      const auto path = inherited / "zbd/mechlib.zbd";
      model_archive(path, {{"mech_inherited.flt", "inherited"}}, {99}, 1);
      std::vector<mech3::ArchiveEntry> entries;
      EXPECT(mech3::archive_read_entries(path.generic_string(), &entries));
      entries.erase(entries.begin() + 2);
      original = entries.back().data;
      entries.push_back({"mech_outside.flt", model_tree("outside", 2)});
      replace_entries(path, entries);
    } else {
      std::string valid = review_triangle_json("1");
      const auto position = valid.find("\"material_index\": 0");
      EXPECT(position != std::string::npos);
      if (position == std::string::npos) return;
      valid.replace(position, 19, "\"material_index\": 1");
      std::string invalid = valid;
      invalid.replace(position, 19, "\"material_index\": 2");
      std::string why;
      EXPECT(zcls::mechlib_model_from_json(valid, &original, &why));
      if (form == 1) {
        put(inherited / "zbd/mechlib/mech_inherited.flt.json", valid);
        put(inherited / "zbd/mechlib/mech_outside.flt.json", invalid);
      } else {
        write_stored_zip((inherited / "zbd/mechlib.zip").string(),
                         {{"mech_inherited.flt.json", valid}, {"mech_outside.flt.json", invalid}});
      }
    }
    test.mount({"extra", "inherited"});
    const auto log = model_library_log();
    EXPECT(!contains(log, "entry mech_inherited.flt:"));
    EXPECT(contains(log, "entry mech_outside.flt:"));
    zcls::MechLib library;
    EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
    EXPECT(library.materials.size() == 4);  // two base slots plus the extra mod's two
    const int index = zutl_zar::find(library.archive, "mech_inherited.flt");
    EXPECT(index >= 0);
    if (index >= 0) {
      uint32_t size = 0;
      std::FILE* file = zutl_zar::seek(library.archive, index, &size);
      std::vector<uint8_t> bytes(size);
      EXPECT(file && std::fread(bytes.data(), 1, bytes.size(), file) == bytes.size());
      EXPECT(bytes == original);  // inherited indices, including duplicate slot 1, stay byte-for-byte intact
    }
    EXPECT(zutl_zar::find(library.archive, "mech_outside.flt") < 0);
    auto* node = zcls::mechlib_load(library, "mech_inherited.flt");
    EXPECT(node && node->model && node->model->polygons[0].material);
    if (node && node->model && node->model->polygons[0].material) {
      EXPECT(node->model->polygons[0].material_index == 1);
      EXPECT(node->model->polygons[0].material->r == 10);
    }
    zcls::mechlib_close(library);
    if (node) zcls::node_destroy(node);
  }
}

TEST(model_library_policy_unreadable_materials_do_not_inherit) {
  for (int form = 0; form < 3; ++form) {
    ModelLibraryTest test;
    const auto bad = test.mod("bad");
    if (form == 0) {
      const auto path = bad / "zbd/mechlib.zbd";
      model_archive(path, {{"mech_bad.flt", "bad"}});
      std::vector<mech3::ArchiveEntry> entries;
      EXPECT(mech3::archive_read_entries(path.generic_string(), &entries));
      entries[2].data = {255, 255, 255, 127};
      replace_entries(path, entries);
    } else if (form == 1) {
      put(bad / "zbd/mechlib/mech_bad.flt.json", review_triangle_json("1"));
      put(bad / "zbd/mechlib/materials.json", "[");
    } else {
      write_stored_zip((bad / "zbd/mechlib.zip").string(),
                       {{"mech_bad.flt.json", review_triangle_json("1")}, {"materials.json", "["}});
    }
    test.mount({"bad"});
    const auto log = model_library_log();
    EXPECT(contains(log, "bad/zbd/mechlib.zbd: entry mech_bad.flt:"));
    EXPECT(contains(log, "left out"));
    zutl_zar::Archive archive;
    EXPECT(mech3::model_library_open(archive, "zbd/mechlib.zbd"));
    EXPECT(zutl_zar::find(archive, "mech_bad.flt") < 0);
    mech3::model_library_close(archive);
    expect_materials({{"mech_stock.flt", 1}});
  }
}

TEST(model_library_policy_model_only_json_keeps_existing_override_behavior) {
  ModelLibraryTest test;
  const auto first = test.mod("first"), later = test.mod("later");
  put(later / "zbd/mechlib/tiny.flt.json", review_triangle_json("9"));
  test.mount({"first", "later"});
  const auto second_y = [&]() {
    zcls::MechLib library;
    float y = -1;
    EXPECT(zcls::mechlib_open(library, "zbd/mechlib.zbd"));
    auto* node = zcls::mechlib_load(library, "tiny.flt");
    if (node && node->model) y = node->model->vertices[4];
    zcls::mechlib_close(library);
    if (node) zcls::node_destroy(node);
    return y;
  };
  EXPECT(second_y() == 9);
  write_stored_zip((first / "zbd/mechlib.zip").string(), {{"TINY.FLT.JSON", review_triangle_json("3.5")}});
  EXPECT(second_y() == 3.5f);
  put(first / "zbd/mechlib/tiny.flt.json", review_triangle_json("4.25"));
  EXPECT(second_y() == 4.25f);
  put(first / "zbd/mechlib/tiny.flt.json", review_triangle_json("\"high\""));
  EXPECT(second_y() == -1);  // a refused earlier JSON must still block later JSON
  fs::remove_all(first / "zbd/mechlib");
  fs::remove(first / "zbd/mechlib.zip");
  model_archive(first / "zbd/mechlib.zbd", {{"mech_first.flt", "first"}});
  EXPECT(second_y() == 9);  // the archive lacks this entry, so later JSON remains visible
}

TEST(model_library_review_conflicts_and_multiplayer_source_bytes) {
  ModelLibraryTest test;
  const auto one = test.mod("one"), two = test.mod("two");
  model_archive(one / "zbd/mechlib.zbd", {{"mech_one.flt", "one"}}, {20});
  model_archive(two / "zbd/mechlib.zbd", {{"mech_two.flt", "two"}}, {30});
  auto listed = mech3::mods_list(test.files.write, {"one", "two"});
  EXPECT(listed.size() == 2);
  if (listed.size() == 2) EXPECT(listed[1].shadowed.empty());
  model_archive(two / "zbd/mechlib.zbd", {{"mech_one.flt", "other"}, {"mech_two.flt", "two"}}, {30});
  listed = mech3::mods_list(test.files.write, {"one", "two"});
  if (listed.size() == 2)
    EXPECT(listed[1].shadowed == std::vector<std::string>{"zbd/mechlib.zbd: mech_one.flt"});
  const std::string install = test.install.generic_string();
  const auto before = mech3::mods_gameplay_hash(test.files.write, {"one", "two"}, &install);
  std::string key, bytes;
  EXPECT(mech3::mp_mounted_part((one / "zbd/mechlib.zbd").generic_string(),
                               "zbd/mechlib.zbd", install, &key, &bytes));
  EXPECT(key == "zbd/mechlib.zbd" && bytes == read(one / "zbd/mechlib.zbd"));
  test.mount({"one", "two"});
  expect_materials({{"mech_one.flt", 20}, {"mech_two.flt", 30}});
  EXPECT(mech3::mods_gameplay_hash(test.files.write, {"one", "two"}, &install) == before);
}

TEST(model_library_review_json_decode_budget_counts_shared_geometry) {
  const std::string text = review_triangle_json("1");
  uint64_t size = 0;
  std::vector<uint8_t> converted;
  std::string why;
  EXPECT(mech3::model_library_json::decoded_size(text, &size));
  EXPECT(zcls::mechlib_model_from_json(text, &converted, &why));
  EXPECT(size == converted.size());
  std::string nodes, vertices;
  for (int i = 0; i < 1000; ++i) nodes += (i ? "," : "") + std::string("{\"model_index\":0}");
  for (int i = 0; i < 10000; ++i) vertices += (i ? "," : "") + std::string("{\"x\":0,\"y\":0,\"z\":0}");
  const std::string shared = "{\"nodes\":[" + nodes + "],\"models\":[{\"vertices\":[" +
                             vertices + "],\"polygons\":[],\"lights\":[]}]}";
  EXPECT(shared.size() < 1024 * 1024);
  EXPECT(!mech3::model_library_json::decoded_size(shared, &size));
}
