#include "mech3/arena_catalog.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <map>
#include <vector>

#include <nlohmann-json/json.hpp>

#include "gamez/zimage/zimg_library.h"
#include "gamez/zreader/zreader.h"
#include "gamez/zutil/zutl_msg.h"
#include "gamez/zutil/zutl_msgdll.h"
#include "gamez/zutil/zutl_path.h"
#include "mech3/arena_setup.h"
#include "mech3/mech_config.h"
#include "mech3/mech_data.h"
#include "mech3/mech_names.h"
#include "mech3/mech_reader.h"
#include "mech3/replay_terrain.h"
#include "mech3/zrdraiv.h"

namespace mech3 {
// From mission.h, which can't be included beside mech_data.h: the two define
// different Handle types.
const char* mission_dir(int32_t index);
int32_t mission_dir_count();
}  // namespace mech3

namespace mech3::arena {

namespace {

using Json = nlohmann::json;

constexpr int kCatalogVersion = 1;
constexpr int kTerrainMaxPixels = 1024;  // the long side of a map picture
// Reader names tried per world: campaign missions, Instant Action and
// multiplayer. The shipped worlds stay well inside these (docs/ai.md: 48
// readers in all); a missing one costs only a failed open.
constexpr int kMaxCampaignMission = 30, kMaxInstantAction = 10, kMaxMultiplayerMap = 9;
// What a picture's see-through pixels are drawn on: the runner's dark panel.
constexpr uint8_t kBackdrop = 40;

// A message's text by id, or `fallback` when the table has none (no
// Mech3Msg.dll table loaded, or an id it lacks).
std::string message_text(int32_t id, const char* fallback) {
  const zutl::Messages& m = zutl::messages();
  const char* text = id > 0 && m.get_text ? m.get_text(id) : nullptr;
  return text && *text ? text : fallback ? fallback : "";
}

const char* part_message(void*, int32_t id) {
  const zutl::Messages& m = zutl::messages();
  return m.get_text ? m.get_text(id) : nullptr;
}

bool write_ppm(const std::filesystem::path& path, int width, int height, const std::vector<uint8_t>& rgb) {
  std::ofstream f(path, std::ios::binary);
  if (!f) return false;
  f << "P6\n" << width << " " << height << "\n255\n";
  f.write(reinterpret_cast<const char*>(rgb.data()), static_cast<std::streamsize>(rgb.size()));
  return static_cast<bool>(f);
}

// --- maps ---------------------------------------------------------------

// The lobby's names for the shipped eight (mp_lobby.cpp: messages 0x320 on,
// c1mp1 first, then the kShipped order).
std::string shipped_map_name(const std::string& dir, int number) {
  static const char* const kOrder[] = {"c1mp1", "c1mp2", "c2mp1", "c2mp2", "c3mp1", "c3mp2", "c4mp1", "c4mp2"};
  const std::string id = dir + "mp" + std::to_string(number);
  for (int i = 0; i < 8; ++i)
    if (id == kOrder[i]) return message_text(0x320 + i, "");
  return {};
}

// An add-on map's name: its mpinfo.zrd db_name, as the lobby reads it.
std::string addon_map_name(const std::string& reader) {
  if (!zrdr::state().archives.empty()) return {};  // only on a reader of our own (see arena_mech_dfn)
  zrdr::init();
  if (!zrdr::open_archive(reader.c_str(), false)) return {};
  std::string name;
  if (zrdr::Node* info = zrdr::load("mpinfo.zrd")) {
    if (const char* s = zrdr::get_string(info, "db_name")) name = s;
    zrdr::free_node(info);
  }
  zrdr::close_archives(true);
  return name;
}

bool write_terrain(const std::string& map, const std::filesystem::path& dir, std::string* error) {
  const float whole[4] = {1, 1, 0, 0};  // min > max: the whole world
  replay::Terrain t = replay::build_terrain(map, whole);
  if (!t.error.empty() || t.width <= 0) {
    *error = map + ": " + (t.error.empty() ? "no terrain" : t.error);
    return false;
  }
  replay::darken_outline(&t);
  // Shrunk by a whole number of cells, nearest cell, so it stays placed.
  const int step = std::max(1, (std::max(t.width, t.height) + kTerrainMaxPixels - 1) / kTerrainMaxPixels);
  const int w = (t.width + step - 1) / step, h = (t.height + step - 1) / step;
  std::vector<uint8_t> rgb(static_cast<size_t>(w) * h * 3);
  for (int row = 0; row < h; ++row)
    for (int col = 0; col < w; ++col) {
      const size_t from = (static_cast<size_t>(row) * step * t.width + static_cast<size_t>(col) * step) * 4;
      const size_t to = (static_cast<size_t>(row) * w + col) * 3;
      for (int c = 0; c < 3; ++c) rgb[to + c] = t.rgba[from + c];
    }
  if (!write_ppm(dir / (map + ".ppm"), w, h, rgb)) {
    *error = "cannot write " + (dir / (map + ".ppm")).string();
    return false;
  }
  const Json place = {{"x0", t.x0}, {"z_top", t.z_top}, {"cell", t.cell * step}, {"width", w}, {"height", h}};
  std::ofstream f(dir / (map + ".json"));
  f << place.dump(1);
  if (!f) {
    *error = "cannot write " + (dir / (map + ".json")).string();
    return false;
  }
  return true;
}

Json catalog_maps(const std::filesystem::path& terrain_dir, std::string* error) {
  Json maps = Json::array();
  for (int d = 0; d < mission_dir_count(); ++d) {
    const std::string dir = mission_dir(d);
    for (int n = 1; n <= kMaxMultiplayerMap; ++n) {
      const std::string reader = reader_path(dir, "mp" + std::to_string(n));
      AivTree tree;
      if (!tree.read(reader)) continue;
      bool spots = true;
      for (int spot = 0; spot < kSpawnSpots && spots; ++spot)
        spots = tree.find(("remote_" + std::to_string(spot)).c_str()) != nullptr;
      if (!spots) continue;  // the arena's own check (read_arena_game_files)
      const std::string id = dir + "mp" + std::to_string(n);
      std::string name = shipped_map_name(dir, n);
      if (name.empty()) name = addon_map_name(reader);
      if (name.empty()) name = id;
      if (!write_terrain(id, terrain_dir, error)) return nullptr;
      maps.push_back({{"id", id}, {"name", name}});
    }
  }
  return maps;
}

// --- mechs and loadouts -------------------------------------------------

Json loadout_record(int32_t mech, int index, const Config& c) {
  // Each weapon by where it sits, counted; each weapon's rounds summed.
  std::map<std::pair<std::string, std::string>, int> weapons;
  std::map<int32_t, int> rounds;
  for (const ConfigItem* item : c.items) {
    if (item->kind() == 1) {
      const auto* w = static_cast<const WeaponItem*>(item);
      const std::string name = message_text(weapon_name_message(w->weapon), weapon_name(w->weapon));
      // The player's name for the part, or the file's ("larm") with no message table.
      const int32_t part = w->location(mech);
      const char* shown = part_display_name(part, part_message, nullptr);
      const std::string where = shown ? shown : part_name(part);
      ++weapons[{name, where}];
    } else if (item->kind() == 2) {
      rounds[static_cast<const AmmoItem*>(item)->weapon] += item->count;
    }
  }
  Json list = Json::array();
  for (const auto& [key, count] : weapons) list.push_back({{"weapon", key.first}, {"where", key.second}, {"count", count}});
  Json ammo = Json::array();
  for (const auto& [weapon, count] : rounds)
    ammo.push_back({{"weapon", message_text(weapon_name_message(weapon), weapon_name(weapon))}, {"rounds", count}});
  int armor = 0;
  for (int32_t a : c.armor) armor += a;
  const float most = static_cast<float>(c.weight(8));  // the chassis' tons, as the lab's speeds use
  return {{"index", index},
          {"name", c.name ? c.name : ""},
          {"weapons", list},
          {"ammo", ammo},
          {"armor", armor},
          {"walk_kph", std::round(engine_kph(c.engine, most, false))},
          {"run_kph", std::round(engine_kph(c.engine, most, true))},
          {"heat_sinks", c.sinks},
          {"double_sinks", c.double_sinks != 0},
          {"jump_jets", c.jump_jets()}};
}

// The mech lab's picture (mech_icon, debriefing.cpp): 16-bit 565 colors or
// palette indices, see-through pixels drawn on the runner's backdrop.
bool write_mech_picture(const std::string& mech, const std::filesystem::path& dir) {
  zimg::Texture* t = zimg::find_in_list(1, ("icon_" + mech + "_green").c_str());
  if (!t || t->width <= 0 || t->height <= 0 || !t->pixels) return false;
  const int w = t->width, h = t->height;
  std::vector<uint8_t> rgb(static_cast<size_t>(w) * h * 3);
  for (int i = 0; i < w * h; ++i) {
    const uint16_t p = t->palette_count ? t->palette[static_cast<const uint8_t*>(t->pixels)[i]]
                                        : static_cast<const uint16_t*>(t->pixels)[i];
    const int r = (p >> 11) * 255 / 31, g = ((p >> 5) & 63) * 255 / 63, b = (p & 31) * 255 / 31;
    const int a = t->alpha ? t->alpha[i] : 255;
    const auto mix = [a](int c) { return static_cast<uint8_t>((c * a + kBackdrop * (255 - a)) / 255); };
    rgb[i * 3] = mix(r), rgb[i * 3 + 1] = mix(g), rgb[i * 3 + 2] = mix(b);
  }
  zimg::free_texture(t);
  return write_ppm(dir / (mech + ".ppm"), w, h, rgb);
}

Json catalog_mechs(const std::filesystem::path& picture_dir) {
  zimg::register_image_library(1);  // rimage.zbd, where the menus find the icons
  Json mechs = Json::array();
  for (int32_t m = 0; m < mech_count(); ++m) {
    if (m == kNoMech) continue;
    const MechDfn* dfn = arena_mech_dfn(m);
    const int32_t stock = stock_loadout_count(m);
    if (!dfn || stock <= 0) continue;
    Json loadouts = Json::array();
    for (int32_t i = 0; i < stock; ++i) loadouts.push_back(loadout_record(m, i, *dfn->configs->configs[i]));
    const bool picture = write_mech_picture(mech_name(m), picture_dir);
    mechs.push_back({{"id", mech_name(m)},
                     {"name", message_text(mech_name_message(m), mech_name(m))},
                     {"tons", max_mass(m)},
                     {"picture", picture},
                     {"loadouts", loadouts}});
  }
  zimg::free_all(1);
  return mechs;
}

// --- pilot presets ------------------------------------------------------

// What the runner's one-line summary is built from, in meters and seconds
// (the ranges are kept squared, zai_params.cpp; docs/ai.md's table).
Json preset_numbers(const ai::AivRecord& r) {
  const uint8_t flags = r.raw[0xcc];
  const auto root = [&](int off) { return std::round(std::sqrt(std::max(0.0f, r.get<float>(off)))); };
  const auto plain = [&](int off) { return std::round(r.get<float>(off) * 100) / 100; };  // two places
  Json n = {{"sight_m", root(0x1c)},
            {"attack_m", root(0x20)},
            {"burst_s", plain(0x34)},
            {"rest_s", plain(0x38)},
            {"aim_error", plain(0xb8)},
            {"attack_mode", r.get<int32_t>(0x40)},
            {"loadout", r.get<int32_t>(0xbc)}};
  // Break-off rules, each on only with its +0xcc bit (zai_brain.cpp engage_checks).
  if (flags & 2) n["attack_for_s"] = plain(0x4c);
  if (flags & 4) n["breaks_off_below_health"] = plain(0x50);
  if (flags & 8) n["breaks_off_after_damage"] = plain(0xb4);
  return n;
}

Json catalog_presets() {
  Json presets = Json::array();
  for (int d = 0; d < mission_dir_count(); ++d) {
    const std::string world = mission_dir(d);
    std::vector<std::string> missions;
    for (int i = 1; i <= kMaxCampaignMission; ++i) missions.push_back("m" + std::to_string(i));
    for (int i = 1; i <= kMaxInstantAction; ++i) missions.push_back("ia" + std::to_string(i));
    for (int i = 1; i <= kMaxMultiplayerMap; ++i) missions.push_back("mp" + std::to_string(i));
    for (const std::string& mission : missions) {
      AivTree tree;
      if (!tree.read(reader_path(world, mission))) continue;
      // A record is a name followed by its list, possibly inside nested
      // lists, as zrdr::find walks them (the way a mission finds one). Only
      // names zrdr::find answers with that same list are records here.
      std::vector<const zrdr::Node*> lists = {tree.root};
      while (!lists.empty()) {
        const zrdr::Node* list = lists.back();
        lists.pop_back();
        const int count = list->list[0].i;
        for (int i = 1; i < count; ++i) {
          const zrdr::Node& item = list->list[i];
          if (item.type == zrdr::List) {
            lists.push_back(&item);
            continue;
          }
          if (item.type != zrdr::String || !item.s || i + 1 >= count || list->list[i + 1].type != zrdr::List) continue;
          if (tree.find(item.s) != &list->list[i + 1]) continue;  // a name used twice: the first is the record
          ai::AivRecord record;
          record.parse(&list->list[i + 1], item.s);
          if (record.team() != 2 || record.mech() < 0) continue;  // enemies in mechs only
          presets.push_back({{"world", world},
                             {"mission", mission},
                             {"record", item.s},
                             {"mech", mech_name(record.mech())},
                             {"numbers", preset_numbers(record)}});
          ++i;  // its list is the record, not a list of more records
        }
      }
    }
  }
  return presets;
}

}  // namespace

namespace {
bool write_files(const std::string& dir, std::string* error) {
  const std::filesystem::path root(dir), terrain = root / "terrain", pictures = root / "mechs";
  std::error_code ec;
  std::filesystem::create_directories(terrain, ec);
  std::filesystem::create_directories(pictures, ec);
  if (ec) {
    *error = "cannot make " + dir + ": " + ec.message();
    return false;
  }
  Json maps = catalog_maps(terrain, error);
  if (maps.is_null()) return false;
  const Json catalog = {{"version", kCatalogVersion},
                        {"maps", maps},
                        {"mechs", catalog_mechs(pictures)},
                        {"presets", catalog_presets()}};
  std::ofstream f(root / "catalog.json");
  f << catalog.dump(1);
  if (!f) {
    *error = "cannot write " + (root / "catalog.json").string();
    return false;
  }
  return true;
}
}  // namespace

bool write_arena_catalog(const std::string& dir, std::string* error) {
  // The names come from Mech3Msg.dll, which the engine loads only when the
  // game starts (GameEngine::message_dll_load); the catalog runs before, so
  // it reads the table itself. Missing, the file's own names are written.
  zutl::MessageDll table;
  bool installed = false;
  if (!zutl::messages().get_text) {
    const std::string path = zutl::find("Mech3Msg.dll");
    if (!path.empty() && zutl::read_message_dll(path, table)) zutl::install_messages(&table), installed = true;
  }
  const bool written = write_files(dir, error);
  if (installed) zutl::install_messages(nullptr);  // the table dies here; leave none pointing at it
  return written;
}

}  // namespace mech3::arena
