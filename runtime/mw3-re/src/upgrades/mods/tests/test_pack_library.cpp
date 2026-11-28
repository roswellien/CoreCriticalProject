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
#include "mech3/mods.h"
#include "mech3/mech_names.h"
#include "mech3/mods_tables.h"
#include "mech3/mods_menu.h"
#include "upgrades/mods/mod_export.h"
#include "upgrades/mods/entry_archives.h"
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
// A real, minimal tree for the bounded model reader: one Object3d node with
// no geometry or children. Different root names identify the winning bytes.
std::vector<uint8_t> model_tree(const std::string& name) {
  std::vector<uint8_t> bytes(0xd0 + 0x90, 0);
  std::memcpy(bytes.data(), name.c_str(), name.size() + 1);
  const int32_t object_class = 5;
  std::memcpy(bytes.data() + 0x34, &object_class, 4);
  return bytes;
}

void model_archive(const fs::path& path,
                   const std::vector<std::pair<std::string, std::string>>& models) {
  fs::create_directories(path.parent_path());
  const bool confined = zutl::mounts().confined;
  zutl::mounts().confined = false;  // authored fixtures use host paths
  zutl_zar::Archive archive;
  zutl_zar::init(archive);
  EXPECT(zutl_zar::create(archive, path.string().c_str()));
  if (archive.file) {
    const uint32_t version = 27, format = 1;
    const uint32_t materials = 0;
    zutl_zar::add(archive, "version", &version, 4);
    zutl_zar::add(archive, "format", &format, 4);
    zutl_zar::add(archive, "materials", &materials, 4);
    for (const auto& model : models) {
      const auto bytes = model_tree(model.second);
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
  EXPECT(!fs::exists(fs::path(test.files.write) / "mod-merged"));
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
    EXPECT(!mech3::model_library_has(archive.generic_string(), "mech_bad.flt"));
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
