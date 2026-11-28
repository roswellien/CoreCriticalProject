// Asset-free integration tests for the pack library's use of the existing mod engine.
#include "check.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

#include "gamez/zutil/zutl_path.h"
#include "mech3/mods.h"
#include "mech3/mods_tables.h"
#include "upgrades/mods/campaign_entries.h"
#include "upgrades/mods/mods_delete.h"

namespace {
namespace fs = std::filesystem;

struct PackTest {
  const std::string library_before = mech3::mods_pack_library();
  const zutl::Mounts mounts_before = zutl::mounts();
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
  const fs::path pack = test.library / "gameplay-only";
  fs::copy(fixture, pack, fs::copy_options::recursive);
  return pack;
}
}  // namespace

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
  manifest(test.library / "pack", "example-pack");
  put(test.library / "pack/mod/mod.txt", "name=Pack\n");
  put(test.library / "pack/mod/zbd/order.zrd", "pack");
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
  manifest(test.library / "pack", "example-pack");
  put(test.library / "pack/mod/mod.txt", "name=Pack\ncampaign=story.txt\n");
  put(test.library / "pack/mod/story.txt", "id=story\nname=Story\nmission=c1 1\n");
  put(test.library / "pack/mod/zbd/test.zrd", "pack data");
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
  for (const char* root : {"../outside", "/outside", "mod//data", "mod/", "mod.", "mod ", "NUL"}) {
    manifest(test.library / "unsafe", "unsafe", root);
    std::vector<std::string> log;
    EXPECT(mech3::mods_found(test.write, &log).empty());
    EXPECT(contains(log, "gameplay-root-invalid"));
  }
  mech3::mods_pack_library() = (test.root / "missing-library").generic_string();
  std::vector<std::string> log;
  EXPECT(mech3::mods_found(test.write, &log).empty());
  EXPECT(contains(log, "cannot read pack library"));
}
