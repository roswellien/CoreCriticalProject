// Optional environment admission: bounded metadata and streaming file
// integrity.
#include "platform/prepared_environment_bank.hpp"
#include "platform/sha256.hpp"
#include "platform/verified_digest.hpp"
#include <algorithm>
#include <cfenv>
#include <cmath>
#include <fstream>
#include <nlohmann-json/json.hpp>
#include <regex>
#include <sstream>
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

namespace platform::prepared {
namespace {
namespace efs = std::filesystem;
using EJson = nlohmann::json;
constexpr std::uint64_t env_json_limit = 2ULL * 1024 * 1024;
constexpr std::uint64_t env_total_limit = 16ULL * 1024 * 1024 * 1024;
constexpr std::uint64_t env_world_limit = 4096ULL * 1024 * 1024;
constexpr std::uint64_t env_page_limit = 16ULL * 1024 * 1024;
constexpr std::size_t env_world_page_limit = 512;
constexpr std::uint64_t env_target_limit = 4ULL * 1024 * 1024;
constexpr std::uint64_t env_stream_limit = 32ULL * 1024 * 1024;
[[noreturn]] void env_fail(const std::string &message) {
  throw std::runtime_error("Environment pack: " + message);
}
std::string env_lower(std::string text) {
  for (auto &c : text)
    if (c >= 'A' && c <= 'Z')
      c += 'a' - 'A';
  return text;
}
std::uint64_t env_uint(const EJson &j) {
  if (!j.is_number_integer() ||
      (j.is_number_integer() && !j.is_number_unsigned() &&
       j.get<std::int64_t>() < 0))
    env_fail("expected unsigned integer");
  return j.get<std::uint64_t>();
}
std::string env_text(const EJson &j) {
  if (!j.is_string())
    env_fail("expected string");
  const auto value = j.get<std::string>();
  if (value.empty() || value.find('\0') != std::string::npos)
    env_fail("empty/NUL string");
  return value;
}
std::string env_read_text(const efs::path &path, std::uint64_t limit = env_json_limit) {
  if (efs::file_size(path) > limit)
    env_fail("metadata/text size limit");
  std::ifstream input(path, std::ios::binary);
  if (!input)
    env_fail("cannot open " + path.u8string());
  // Bound the read itself: a file may grow after file_size was checked.
  std::string text(static_cast<std::size_t>(limit) + 1, '\0');
  input.read(text.data(), static_cast<std::streamsize>(text.size()));
  const auto count = input.gcount();
  if (input.bad() || (input.fail() && !input.eof()))
    env_fail("text read failed");
  if (count > static_cast<std::streamsize>(limit))
    env_fail("text grew during read");
  text.resize(static_cast<std::size_t>(count));
  return text;
}
EJson env_json(const efs::path &path, std::uint64_t limit = env_json_limit,
               const std::string &digest = {}) {
  const auto text = env_read_text(path, limit);
  if (!digest.empty()) {
    integrity::Sha256 actual;
    actual.update(text.data(), text.size());
    if (actual.hex() != digest)
      env_fail("JSON integrity failure");
  }
  const std::size_t event_limit =
      limit == env_stream_limit ? 8000000U : limit == env_target_limit ? 1000000U : 100000U;
  std::vector<std::set<std::string>> keys;
  std::size_t events = 0;
  try {
    return EJson::parse(
        text, [&](int depth, EJson::parse_event_t event, EJson &value) {
          if (depth > 32 || ++events > event_limit)
            env_fail("JSON complexity limit");
          if (event == EJson::parse_event_t::object_start)
            keys.emplace_back();
          if (event == EJson::parse_event_t::key &&
              !keys.back().insert(value.get<std::string>()).second)
            env_fail("duplicate JSON key");
          if (event == EJson::parse_event_t::object_end)
            keys.pop_back();
          return true;
        });
  } catch (const EJson::exception &error) {
    env_fail(std::string("invalid JSON: ") +
             std::string(error.what()).substr(0, 512));
  }
}
bool env_link(const efs::path &path) {
#if defined(_WIN32)
  const auto attributes = GetFileAttributesW(path.c_str());
  if (attributes != INVALID_FILE_ATTRIBUTES &&
      (attributes & FILE_ATTRIBUTE_REPARSE_POINT))
    return true;
#endif
  return efs::is_symlink(efs::symlink_status(path));
}
efs::path env_root(const std::string &name) {
  if (name.empty() || name.size() > 32768 ||
      name.find('\0') != std::string::npos)
    env_fail("invalid pack root");
  auto path = efs::absolute(efs::u8path(name)).lexically_normal();
  for (auto part = path; !part.empty();) {
    if (env_link(part))
      env_fail("linked pack root/ancestor");
    const auto parent = part.parent_path();
    if (parent == part)
      break;
    part = parent;
  }
  if (!efs::is_directory(path))
    env_fail("pack directory is missing");
  return efs::canonical(path);
}
efs::path env_member(const efs::path &root, const std::string &name) {
  if (name.empty() || name.size() > 240 || name.find('\\') != std::string::npos)
    env_fail("unsafe member path");
  efs::path path = root;
  std::istringstream parts(name);
  std::string part;
  if (name.back() == '/')
    env_fail("empty path component");
  while (std::getline(parts, part, '/')) {
    if (part.empty() || part == "." || part == ".." || part.back() == '.' ||
        part.back() == ' ')
      env_fail("unsafe path component");
    for (unsigned char c : part)
      if (c < 32 || c == '<' || c == '>' || c == ':' || c == '"' || c == '|' ||
          c == '?' || c == '*')
        env_fail("unsafe path character");
    const auto base = env_lower(part.substr(0, part.find('.')));
    if (base == "con" || base == "conin$" || base == "conout$" ||
        base == "prn" || base == "aux" || base == "nul" ||
        (base.size() == 4 &&
         (base.substr(0, 3) == "com" || base.substr(0, 3) == "lpt") &&
         base[3] >= '0' && base[3] <= '9') ||
        base == "com\xc2\xb9" || base == "com\xc2\xb2" ||
        base == "com\xc2\xb3" || base == "lpt\xc2\xb9" ||
        base == "lpt\xc2\xb2" || base == "lpt\xc2\xb3")
      env_fail("reserved member path");
    path /= efs::u8path(part);
    if (env_link(path))
      env_fail("linked pack member");
  }
  if (!efs::is_regular_file(path))
    env_fail("member is missing: " + name);
  const auto canonical = efs::canonical(path),
             relative = canonical.lexically_relative(root);
  if (relative.empty() || relative.is_absolute() || *relative.begin() == "..")
    env_fail("member escapes pack");
  return canonical;
}
const std::vector<std::string> env_regions = {"operation1", "operation2",
                                              "operation3", "operation4",
                                              "training",   "shared-mechs"};
std::set<std::string> env_banks(const std::string &region) {
  if (region == "shared-mechs")
    return {"zbd/rmechtex.zbd", "zbd/rmechtex16.zbd"};
  std::vector<std::string> dirs = {
      region == "training" ? "t1" : "c" + region.substr(9)};
  if (region == "operation4")
    dirs.push_back("c4b");
  std::set<std::string> result;
  for (const auto &dir : dirs)
    for (const char *name : {"rtexture", "rtexture2", "rtexture3", "texture",
                             "texture1", "texture2"})
      result.insert("zbd/" + dir + "/" + name + ".zbd");
  return result;
}
struct EnvPin {
  std::string path, digest, format;
  std::uint64_t bytes{};
};
struct EnvPack {
  std::string id, region, root, manifest_digest;
  EJson registry;
  std::map<std::string, EnvPin> pins;
  bool material_targets_declared{};
  bool streamed_heights_declared{}, raw_heights_declared{};
  bool surface_materials_declared{};
};
float env_float(const EJson &j, double min_val, double max_val) {
  if (j.is_boolean() || !j.is_number())
    env_fail("expected finite number");
  const double value = j.get<double>();
  if (!std::isfinite(value) || value < min_val || value > max_val)
    env_fail("number out of range");
  return static_cast<float>(value);
}
bool env_region_mission(const std::string &region, const std::string &mission) {
  if (region.size() != 10 || region.substr(0, 9) != "operation")
    return false;
  const char op = region[9];
  return mission.size() == 4 && mission[0] == 'c' && mission[1] == op &&
         mission[2] == 'm' && mission[3] >= '1' &&
         mission[3] <= (op < '3' ? '4' : '6');
}
void env_lighting(const efs::path &path, const std::string &region,
                  EnvironmentSelection *selected = nullptr) {
  const auto lighting = env_json(path);
  if (!lighting.is_object() || env_uint(lighting.at("schema_version")) != 1 ||
      (lighting.contains("missions") && !lighting["missions"].is_object()) ||
      (lighting.contains("maps") && !lighting["maps"].is_object()))
    env_fail("invalid lighting object");
  if (!lighting.contains("missions"))
    return;
  for (const auto &item : lighting["missions"].items()) {
    if (!region.empty() && !env_region_mission(region, item.key()))
      env_fail("invalid lighting mission key: " + item.key());
    if (!item.value().is_object())
      env_fail("invalid lighting mission entry");
    const auto &entry = item.value();
    const bool has_rgb = entry.contains("ambient_color");
    const bool has_strength = entry.contains("ambient_strength");
    if (has_rgb != has_strength)
      env_fail("incomplete mission ambient override");
    if (has_rgb) {
      const auto &rgb_json = entry["ambient_color"];
      if (!rgb_json.is_array() || rgb_json.size() != 3)
        env_fail("invalid mission ambient_color");
      std::array<float, 3> rgb{};
      for (std::size_t i = 0; i < 3; ++i)
        rgb[i] = env_float(rgb_json[i], 0.0, 4.0);
      const float strength = env_float(entry["ambient_strength"], 0.0, 2.0);
      if (selected)
        selected->mission_ambient.emplace(item.key(),
                                          MissionAmbientOverride{rgb, strength});
    }
    const bool has_tint = entry.contains("sky_tint");
    const bool has_brightness = entry.contains("sky_brightness");
    if (has_tint != has_brightness)
      env_fail("incomplete mission sky override");
    if (has_tint) {
      const auto &tint_json = entry["sky_tint"];
      if (!tint_json.is_array() || tint_json.size() != 3)
        env_fail("invalid mission sky_tint");
      std::array<float, 3> tint{};
      for (std::size_t i = 0; i < 3; ++i)
        tint[i] = env_float(tint_json[i], 0.0, 4.0);
      const float brightness = env_float(entry["sky_brightness"], 0.0, 4.0);
      if (selected)
        selected->mission_sky.emplace(item.key(),
                                      MissionSkyOverride{tint, brightness});
    }
    const bool has_glow_color = entry.contains("sky_glow_color");
    const bool has_glow_strength = entry.contains("sky_glow_strength");
    const bool has_glow_focus = entry.contains("sky_glow_focus");
    if (has_glow_color != has_glow_strength ||
        has_glow_color != has_glow_focus)
      env_fail("incomplete mission sky glow override");
    if (has_glow_color) {
      const auto &glow_json = entry["sky_glow_color"];
      if (!glow_json.is_array() || glow_json.size() != 3)
        env_fail("invalid mission sky_glow_color");
      std::array<float, 3> glow_color{};
      for (std::size_t i = 0; i < 3; ++i)
        glow_color[i] = env_float(glow_json[i], 0.0, 4.0);
      const float glow_strength =
          env_float(entry["sky_glow_strength"], 0.0, 4.0);
      const float glow_focus = env_float(entry["sky_glow_focus"], 0.0, 20.0);
      if (selected)
        selected->mission_sky_glow.emplace(
            item.key(),
            MissionSkyGlowOverride{glow_color, glow_strength, glow_focus});
    }
    const bool has_horizon_low = entry.contains("horizon_low");
    const bool has_horizon_high = entry.contains("horizon_high");
    if (has_horizon_low != has_horizon_high)
      env_fail("incomplete mission horizon override");
    if (has_horizon_low) {
      const float horizon_low = env_float(entry["horizon_low"], 0.0, 0.9);
      const float horizon_high = env_float(entry["horizon_high"], 0.0, 1.0);
      const bool interior_sentinel =
          entry.contains("is_interior") &&
          entry["is_interior"].is_boolean() &&
          entry["is_interior"].get<bool>() && horizon_low == 0.0f &&
          horizon_high == 0.0f;
      if (!interior_sentinel) {
        if (!(horizon_low < horizon_high))
          env_fail("invalid mission horizon range");
        if (selected)
          selected->mission_horizon.emplace(
              item.key(), MissionHorizonOverride{horizon_low, horizon_high});
      }
    }
  }
}
void env_header(const EnvPin &pin) {
  std::ifstream input(efs::u8path(pin.path), std::ios::binary);
  char head[24]{};
  input.read(head, sizeof head);
  const auto count = input.gcount();
  const std::map<std::string, std::string> magic = {
      {"BWSNR2", std::string("BWSNR2\0\0", 8)},
      {"BWSNR3", std::string("BWSNR3\0\0", 8)},
      {"BWSFM1", std::string("BWSFM1\0\0", 8)},
      {"MWFX1", std::string("MWFX1\0\0\0", 8)},
      {"MW34SNA1", "MW34SNA1"},
      {"MW34SNP1", "MW34SNP1"}};
  if (pin.format == "ZBD-texture-v1") {
    detail::validate_environment_bank(efs::u8path(pin.path), pin.bytes);
  } else if (pin.format == "MW34-lighting-v1") {
    env_lighting(efs::u8path(pin.path), {});
  } else if (pin.format == "MW34-c1-height-stream-v1") {
    if (!pin.bytes || pin.bytes > env_stream_limit)
      env_fail("streamed height metadata byte limit");
  } else if (pin.format == "MW34-height-r8-v1") {
    if (!pin.bytes || pin.bytes > 4096ULL * 4096)
      env_fail("streamed height image byte limit");
  } else if (pin.format == "MW34-surface-targets-v1") {
    if (pin.bytes > env_target_limit)
      env_fail("material target metadata byte limit");
  } else {
    const auto it = magic.find(pin.format);
    if (it == magic.end() || count < 8 ||
        std::memcmp(head, it->second.data(), 8))
      env_fail("unsupported/mislabeled resource format");
    if (pin.format == "BWSNR2" || pin.format == "BWSNR3") {
      input.clear();
      input.seekg(0, std::ios::beg);
      (void)mw34::materials::read_surface_normal_header(input);
    }
  }
}
void env_fields(const EJson &value, const std::set<std::string> &fields) {
  if (!value.is_object() || value.size() != fields.size())
    env_fail("invalid material target fields");
  for (const auto &item : value.items())
    if (!fields.count(item.key()))
      env_fail("unknown material target field");
}
std::uint64_t env_hex(const EJson &value, std::size_t digits) {
  const auto text = env_text(value);
  if (text.size() != digits ||
      text.find_first_not_of("0123456789abcdef") != std::string::npos)
    env_fail("invalid material target hash");
  return std::stoull(text, nullptr, 16);
}
using EnvSurfaceCache = std::map<std::pair<std::string, std::string>,
                                 std::weak_ptr<const mw34::materials::SurfaceMaterialPack>>;
MaterialTarget env_material_target_identity(
    const EJson &entry, const std::set<std::string> &owned_members,
    std::set<std::pair<std::string, std::uint32_t>> &sources) {
  MaterialTarget target;
  target.asset_id = env_text(entry.at("asset_id"));
  if (!mw34::materials::valid_surface_identifier(
          target.asset_id, mw34::materials::max_surface_identifier_bytes, true))
    env_fail("invalid material target asset ID");
  const auto &source = entry.at("source");
  env_fields(source, {"kind", "member", "sha256", "bytes", "model_slot"});
  target.source.kind = env_text(source.at("kind"));
  target.source.member = env_text(source.at("member"));
  target.source.sha256 = env_text(source.at("sha256"));
  target.source.bytes = env_uint(source.at("bytes"));
  const auto slot = env_uint(source.at("model_slot"));
  if (target.source.kind != "gamez-zbd-v27" || !owned_members.count(target.source.member) ||
      target.source.sha256.size() != 64 ||
      target.source.sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
      !target.source.bytes || target.source.bytes > env_total_limit || slot >= 1048576)
    env_fail("invalid/cross-region material source");
  target.source.model_slot = std::uint32_t(slot);
  if (!sources.emplace(target.source.member, target.source.model_slot).second)
    env_fail("duplicate material source target");
  target.mesh_uv_hash = env_hex(entry.at("mesh_uv_hash"), 16);
  const auto &materials = entry.at("polygon_materials");
  const auto &keys = entry.at("surface_keys");
  if (!target.mesh_uv_hash || !materials.is_array() || materials.empty() ||
      materials.size() > 4096 || !keys.is_array() || keys.size() != materials.size())
    env_fail("invalid target polygon/material list");
  for (std::size_t polygon = 0; polygon < materials.size(); ++polygon) {
    const auto name = env_text(materials[polygon]);
    if (!mw34::materials::valid_surface_identifier(name, 31, false))
      env_fail("invalid target material name");
    target.polygon_materials.push_back(name);
    if (keys[polygon].is_null()) {
      if (name != "untextured")
        env_fail("missing target source image identity");
      target.surface_keys.emplace_back();
      continue;
    }
    const auto &image = keys[polygon];
    env_fields(image, {"width", "height", "format", "hash"});
    const auto width = env_uint(image.at("width")), height = env_uint(image.at("height")),
               format = env_uint(image.at("format")), hash = env_hex(image.at("hash"), 16);
    if (!width || width > 4096 || !height || height > 4096 || format < 1 || format > 3 || !hash)
      env_fail("invalid target source image identity");
    target.surface_keys.push_back(mw34::materials::SurfaceKey{
        std::uint32_t(width), std::uint32_t(height), std::uint32_t(format), hash});
  }
  return target;
}
std::vector<MaterialTarget> env_material_targets(
    const EnvPack &pack, std::set<std::string> &references,
    std::uint64_t &encoded_bytes,
    std::map<std::string, std::shared_ptr<const mw34::materials::SurfaceMaterialPack>> &cache,
    EnvSurfaceCache &reusable, const std::shared_ptr<mw34::materials::SurfaceDecodedBudget> &budget) {
  const auto member = env_text(pack.registry.at("material_targets"));
  const auto pin = pack.pins.find(member);
  if (pack.region == "shared-mechs" || pin == pack.pins.end() ||
      pin->second.format != "MW34-surface-targets-v1")
    env_fail("undeclared or out-of-region material targets");
  references.insert(member);
  const auto document = env_json(efs::u8path(pin->second.path), env_target_limit);
  env_fields(document, {"schema_version", "targets"});
  if (env_uint(document.at("schema_version")) != 1 ||
      !document.at("targets").is_array() || document["targets"].empty() ||
      document["targets"].size() > 4096)
    env_fail("invalid material target document");
  std::set<std::pair<std::string, std::uint32_t>> sources;
  std::set<std::string> owned_members;
  for (const auto &bank : env_banks(pack.region))
    owned_members.insert(bank.substr(0, bank.find_last_of('/')) + "/gamez.zbd");
  std::vector<MaterialTarget> result;
  for (const auto &entry : document["targets"]) {
    env_fields(entry, {"surface_materials", "asset_id", "source", "mesh_uv_hash",
                       "polygon_materials", "surface_keys"});
    auto target = env_material_target_identity(entry, owned_members, sources);
    const auto sidecar = env_text(entry.at("surface_materials"));
    const auto image_pin = pack.pins.find(sidecar);
    if (image_pin == pack.pins.end() || image_pin->second.format != "BWSFM1")
      env_fail("undeclared target surface-material member");
    references.insert(sidecar);
    target.sidecar_path = image_pin->second.path;
    target.sidecar_sha256 = image_pin->second.digest;
    const auto found = cache.find(target.sidecar_path);
    if (found == cache.end()) {
      if (image_pin->second.bytes > mw34::materials::max_surface_sidecar_bytes - encoded_bytes)
        env_fail("combined target sidecars exceed decoded budget");
      encoded_bytes += image_pin->second.bytes;
      const auto identity = std::make_pair(target.sidecar_path, target.sidecar_sha256);
      const auto prior = reusable.find(identity);
      if (prior != reusable.end())
        target.pack = prior->second.lock();
      if (!target.pack) {
        std::ifstream input(efs::u8path(target.sidecar_path), std::ios::binary);
        auto parsed = mw34::materials::read_surface_materials(
            input, target.asset_id, target.mesh_uv_hash, target.polygon_materials,
            image_pin->second.bytes, mw34::materials::max_surface_sidecar_bytes, budget);
        target.pack = std::make_shared<const mw34::materials::SurfaceMaterialPack>(std::move(parsed));
        // At most five non-shared regions can own 4096 targets each. Weak
        // entries never extend pixel lifetime; expired entries are pruned on
        // resolve, and declining an extra reuse entry cannot evade admission.
        if (reusable.size() < 5 * mw34::materials::max_surface_records || prior != reusable.end())
          reusable[identity] = target.pack;
      }
      cache.emplace(target.sidecar_path, target.pack);
    } else {
      target.pack = found->second;
    }
    const auto &parsed = *target.pack;
    if (!parsed.decoded_reservation || parsed.decoded_reservation->budget() != budget)
      env_fail("foreign cached surface ownership domain");
    if (parsed.mesh_uv_hash != target.mesh_uv_hash ||
        parsed.bindings.size() != target.polygon_materials.size())
      env_fail("shared sidecar source identity mismatch");
    for (const auto &record : parsed.records)
      if (record->asset_id != target.asset_id)
        env_fail("shared sidecar asset identity mismatch");
    for (std::size_t polygon = 0; polygon < parsed.bindings.size(); ++polygon) {
      const auto index = parsed.bindings[polygon];
      if (index == mw34::materials::no_surface_material)
        continue;
      const auto &record = *parsed.records.at(index);
      if (record.material_name != target.polygon_materials[polygon] ||
          (!target.surface_keys[polygon] && record.height_image != mw34::materials::no_surface_image))
        env_fail("shared sidecar polygon/image identity mismatch");
    }
    result.push_back(std::move(target));
  }
  return result;
}
std::vector<MaterialTarget> env_streamed_heights(
    const EnvPack &pack, std::set<std::string> &references, StreamedHeightIndex &index) {
  const auto member = env_text(pack.registry.at("streamed_height_materials"));
  const auto pin = pack.pins.find(member);
  if (pack.region != "operation1" || !pack.streamed_heights_declared ||
      !pack.raw_heights_declared || pin == pack.pins.end() ||
      pin->second.format != "MW34-c1-height-stream-v1")
    env_fail("undeclared or out-of-region streamed height index");
  references.insert(member);
  const auto document = env_json(efs::u8path(pin->second.path), env_stream_limit, pin->second.digest);
  env_fields(document, {"schema_version", "images", "subsets", "targets"});
  const auto &images = document.at("images");
  const auto &subsets = document.at("subsets");
  const auto &targets = document.at("targets");
  if (env_uint(document.at("schema_version")) != 1 ||
      !images.is_array() || images.empty() || images.size() > 512 ||
      !subsets.is_array() || subsets.empty() || subsets.size() > 65536 ||
      !targets.is_array() || targets.empty() || targets.size() > 4096)
    env_fail("invalid streamed height index");
  std::set<std::tuple<std::string, std::uint64_t, std::uint64_t>> identities;
  for (const auto &image : images) {
    env_fields(image, {"member", "width", "height"});
    const auto name = env_text(image.at("member"));
    const auto file = pack.pins.find(name);
    const auto width = env_uint(image.at("width"));
    const auto height = env_uint(image.at("height"));
    if (!width || width > 4096 || !height || height > 4096 ||
        file == pack.pins.end() || file->second.format != "MW34-height-r8-v1" ||
        file->second.bytes != width * height || !references.insert(name).second ||
        !identities.emplace(file->second.digest, width, height).second)
      env_fail("invalid streamed height image pin");
    index.images.push_back({efs::u8path(file->second.path), file->second.digest,
                            std::uint32_t(width), std::uint32_t(height), file->second.bytes});
  }
  std::set<std::uint32_t> scheduled;
  for (const auto &subset : subsets) {
    env_fields(subset, {"world", "x", "z", "images"});
    const auto world = env_uint(subset.at("world"));
    const auto x = env_uint(subset.at("x")), z = env_uint(subset.at("z"));
    const auto &ids = subset.at("images");
    if (world > INT32_MAX || x > INT32_MAX || z > INT32_MAX ||
        !ids.is_array() || ids.empty() || ids.size() > index.images.size())
      env_fail("invalid streamed height subset");
    std::set<std::uint32_t> sorted;
    for (const auto &entry : ids) {
      const auto id = env_uint(entry);
      if (id >= index.images.size() || !sorted.insert(std::uint32_t(id)).second)
        env_fail("invalid streamed subset image");
    }
    scheduled.insert(sorted.begin(), sorted.end());
    if (!index.subsets.emplace(
            std::make_tuple(std::uint32_t(world), std::int32_t(x), std::int32_t(z)),
            std::vector<std::uint32_t>(sorted.begin(), sorted.end())).second)
      env_fail("duplicate streamed height subset");
  }
  std::set<std::pair<std::string, std::uint32_t>> sources;
  std::set<std::uint32_t> bound;
  std::vector<MaterialTarget> result;
  for (const auto &entry : targets) {
    env_fields(entry, {"asset_id", "source", "mesh_uv_hash", "polygon_materials",
                       "surface_keys", "height_bindings"});
    auto target = env_material_target_identity(entry, {"zbd/c1/gamez.zbd"}, sources);
    target.sidecar_sha256 = pin->second.digest;
    const auto &bindings = entry.at("height_bindings");
    if (!bindings.is_array() || bindings.size() != target.surface_keys.size())
      env_fail("invalid streamed height binding list");
    for (std::size_t polygon = 0; polygon < bindings.size(); ++polygon) {
      const auto &binding = bindings[polygon];
      if (binding.is_null()) {
        target.streamed_bindings.emplace_back();
        continue;
      }
      env_fields(binding, {"image", "amplitude"});
      const auto id = env_uint(binding.at("image"));
      const auto &key = target.surface_keys[polygon];
      const auto &value = binding.at("amplitude");
      const auto amplitude = value.is_number() ? value.get<double>() : -1.0;
      const auto name = env_lower(target.polygon_materials[polygon]);
      if (id >= index.images.size() || !key || !(amplitude >= 0.0 && amplitude <= 1.0) ||
          ((name == "txwall01" || name == "txwall06") && amplitude != 0.8) ||
          key->format != 1 || key->width != index.images[id].width || key->height != index.images[id].height)
        env_fail("invalid streamed polygon height identity");
      bound.insert(std::uint32_t(id));
      target.streamed_bindings.push_back(StreamedHeightBinding{std::uint32_t(id), float(amplitude)});
    }
    result.push_back(std::move(target));
  }
  if (bound != scheduled || bound.size() != index.images.size())
    env_fail("streamed height inventory contains unbound or unscheduled images");
  return result;
}
void env_catalog(const EnvPack &pack, const char *role, const char *magic,
                 std::set<std::string> &references, std::uint64_t &bytes,
                 std::size_t &pages) {
  if (!pack.registry.contains(role) || !pack.registry[role].is_array())
    env_fail("normal page list is missing");
  const auto manifest =
      env_text(pack.registry.at(std::string(role) + "_manifest"));
  if (!pack.pins.count(manifest) || pack.pins.at(manifest).format != magic)
    env_fail("undeclared normal manifest");
  references.insert(manifest);
  std::string expected = std::string(magic) + "\n";
  if (pack.registry[role].empty())
    env_fail("empty normal page list");
  for (const auto &entry : pack.registry[role]) {
    const auto name = env_text(entry);
    const auto it = pack.pins.find(name);
    if (it == pack.pins.end() ||
        (it->second.format != "BWSNR2" &&
         (std::string(role) != "world" || it->second.format != "BWSNR3")))
      env_fail("undeclared/mislabeled normal page");
    if (!references.insert(name).second)
      env_fail("duplicate resource role");
    const auto relative =
        efs::u8path(name)
            .lexically_relative(efs::u8path(manifest).parent_path())
            .generic_u8string();
    if (relative.empty() || relative.find('/') != std::string::npos ||
        relative == ".." ||
        relative.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ"
                                   "RSTUVWXYZ0123456789-_.") !=
            std::string::npos ||
        relative.size() > (std::string(role) == "world" ? 80U : 512U))
      env_fail("normal page outside manifest directory");
    expected += relative + "\n";
    bytes += it->second.bytes;
    ++pages;
    const bool world = std::string(role) == "world";
    if ((world && (it->second.bytes > env_page_limit ||
                   bytes > env_world_limit || pages > env_world_page_limit)) ||
        (!world && (bytes > 1536ULL * 1024 * 1024 || pages > 16)))
      env_fail("normal catalog budget exceeded");
  }
  auto actual = env_read_text(efs::u8path(pack.pins.at(manifest).path));
  std::string normalized;
  std::istringstream lines(actual);
  std::string line;
  while (std::getline(lines, line)) {
    if (!line.empty() && line.back() == '\r')
      line.pop_back();
    normalized += line + "\n";
  }
  actual = std::move(normalized);
  if (!actual.empty() && actual.back() != '\n')
    actual += '\n';
  if (actual != expected)
    env_fail("manifest differs from declared pages");
}
} // namespace

std::string environment_region(const std::string &mission) {
  if (mission.size() == 4 && mission[2] == 'm' && mission[3] >= '1' &&
      mission[3] <= '6') {
    if (mission.substr(0, 2) == "t1" && mission[3] <= '4')
      return "training";
    if (mission[0] == 'c' && mission[1] >= '1' && mission[1] <= '4' &&
        (mission[1] >= '3' || mission[3] <= '4'))
      return "operation" + mission.substr(1, 1);
  }
  if (mission.size() == 5 && mission.substr(0, 4) == "c4bm" &&
      mission[4] >= '4' && mission[4] <= '6')
    return "operation4";
  env_fail("unknown stock mission region");
}
static EnvironmentSelection load_environment_packs_impl(
    const std::vector<std::string> &roots,
    const std::shared_ptr<mw34::materials::SurfaceDecodedBudget> &budget,
    EnvSurfaceCache &reusable) {
  struct FloatScope {
    std::fenv_t saved{};
    FloatScope() {
      if (std::feholdexcept(&saved) != 0)
        env_fail("cannot preserve floating-point environment");
    }
    ~FloatScope() { std::fesetenv(&saved); }
  } preserve;
  if (roots.size() > 32)
    env_fail("too many pack roots");
  std::vector<EnvPack> packs;
  std::set<std::string> ids, regions, canonical_roots;
  integrity::Sha256 identity;
  auto fold = [&](const std::string &value) {
    const auto n = std::to_string(value.size()) + ":";
    identity.update(n.data(), n.size());
    identity.update(value.data(), value.size());
  };
  try {
    for (const auto &directory : roots) {
      const auto root = env_root(directory);
      EnvPack pack;
      pack.root = root.u8string();
      if (!canonical_roots.insert(pack.root).second)
        env_fail("duplicate pack root");
      const auto manifest_path = env_member(root, "pack.json");
      const auto manifest = env_json(manifest_path);
      pack.manifest_digest = integrity::sha256_file(manifest_path);
      pack.id = env_text(manifest.at("id"));
      if (!std::regex_match(pack.id,
                            std::regex("[a-z0-9][a-z0-9._-]{0,127}")) ||
          !ids.insert(pack.id).second)
        env_fail("invalid/duplicate pack ID");
      const auto &payload = manifest.at("native_payload");
      if (env_uint(manifest.at("schema_version")) != 2 ||
          payload.at("profile") != "prepared-environment-v1" ||
          payload.at("registry") != "environment/environment.json" ||
          payload.at("path_base") != "pack-root")
        env_fail("unsupported contract");
      if ((manifest.contains("dependencies") &&
           !manifest["dependencies"].empty()) ||
          (manifest.contains("conflicts") && !manifest["conflicts"].empty()))
        env_fail("unsupported dependencies/conflicts");
      if (payload.contains("required_capabilities"))
        for (const auto &cap : payload["required_capabilities"].items())
          if ((cap.key() != "environment-resources" &&
               cap.key() != "surface-materials") ||
              env_uint(cap.value()) != 1)
            env_fail("unsupported required capability");
      const std::set<std::string> formats = {
          "ZBD-texture-v1", "BWSNR2",   "BWSNR3",   "BWSFM1",
          "MWFX1",          "MW34SNA1", "MW34SNP1", "MW34-lighting-v1",
          "MW34-surface-targets-v1", "MW34-c1-height-stream-v1", "MW34-height-r8-v1"};
      if (!payload.at("required_formats").is_array())
        env_fail("required formats must be an array");
      for (const auto &format : payload["required_formats"]) {
        if (!formats.count(env_text(format)))
          env_fail("unsupported required format");
        if (format == "MW34-surface-targets-v1")
          pack.material_targets_declared = true;
        if (format == "MW34-c1-height-stream-v1")
          pack.streamed_heights_declared = true;
        if (format == "MW34-height-r8-v1")
          pack.raw_heights_declared = true;
        if (format == "BWSFM1")
          pack.surface_materials_declared = true;
      }
      const auto &files = manifest.at("files");
      if (!files.is_object() || files.empty() || files.size() > 10000)
        env_fail("invalid file table");
      std::set<std::string> names = {"pack.json"};
      std::uint64_t total = 0;
      for (const auto &item : files.items()) {
        if (!names.insert(env_lower(item.key())).second)
          env_fail("case-colliding member name");
        EnvPin pin;
        pin.path = env_member(root, item.key()).u8string();
        pin.bytes = env_uint(item.value().at("bytes"));
        pin.digest = env_text(item.value().at("sha256"));
        if (pin.digest.size() != 64 ||
            !std::all_of(pin.digest.begin(), pin.digest.end(),
                         [](char c) {
                           return (c >= '0' && c <= '9') ||
                                  (c >= 'a' && c <= 'f');
                         }) ||
            pin.bytes > env_total_limit || total > env_total_limit - pin.bytes)
          env_fail("invalid integrity pin/budget");
        total += pin.bytes;
        if (efs::file_size(efs::u8path(pin.path)) != pin.bytes)
          env_fail("member size mismatch: " + item.key());
        if (item.value().contains("format")) {
          pin.format = env_text(item.value()["format"]);
          if (pin.format == "BWSNR3" && pin.bytes > env_page_limit)
            env_fail("world page byte limit");
          if ((pin.format == "BWSFM1" || pin.format == "MW34-c1-height-stream-v1") &&
              (!payload.contains("required_capabilities") ||
               !payload["required_capabilities"].contains(
                   "surface-materials") ||
               env_uint(
                   payload["required_capabilities"]["surface-materials"]) != 1))
            env_fail("surface-materials capability required");
          if (pin.format == "BWSFM1" && pin.bytes > 512ULL * 1024 * 1024)
            env_fail("surface-material sidecar byte limit");
          if (pin.format == "BWSNR2" && pin.bytes > 256ULL * 1024 * 1024)
            env_fail("sidecar byte limit");
          env_header(pin);
        }
        pack.pins.emplace(item.key(), std::move(pin));
      }
      const auto registry = pack.pins.find("environment/environment.json");
      if (registry == pack.pins.end())
        env_fail("undeclared registry");
      pack.registry = env_json(efs::u8path(registry->second.path));
      pack.region = env_text(pack.registry.at("operation"));
      if (env_uint(pack.registry.at("schema_version")) != 2 ||
          pack.registry.at("payload_profile") != "prepared-environment-v1" ||
          std::find(env_regions.begin(), env_regions.end(), pack.region) ==
              env_regions.end())
        env_fail("unsupported registry");
      // [WP03B R10: bypass only duplicate region ownership rejection.]
      if (!env_claim_region(regions, pack.region))
        env_fail("conflicting region ownership: " + pack.region);

      packs.push_back(std::move(pack));
    }
    std::sort(packs.begin(), packs.end(), [](const auto &a, const auto &b) {
      return std::find(env_regions.begin(), env_regions.end(), a.region) <
             std::find(env_regions.begin(), env_regions.end(), b.region);
    });
    EnvironmentSelection selected;
    selected.surface_budget = budget;
    std::uint64_t world_bytes = 0, authored_bytes = 0;
    std::size_t world_pages = 0, authored_pages = 0;
    std::map<std::string, std::string> common;
    std::uint64_t target_encoded_bytes{};
    std::map<std::string, std::shared_ptr<const mw34::materials::SurfaceMaterialPack>> target_cache;
    for (const auto &pack : packs) {
      std::set<std::string> refs = {"environment/environment.json"}, banks;
      for (const auto &entry : pack.registry.at("banks").items()) {
        banks.insert(entry.key());
        const auto name = env_text(entry.value());
        const auto pin = pack.pins.find(name);
        if (pin == pack.pins.end() || pin->second.format != "ZBD-texture-v1")
          env_fail("undeclared bank");
        refs.insert(name);
        selected.banks.emplace(entry.key(), pin->second.path);
      }
      if (banks != env_banks(pack.region))
        env_fail("incomplete/out-of-region banks");
      env_catalog(pack, "authored", "MW34SNA1", refs, authored_bytes,
                  authored_pages);
      selected.authored_manifests.push_back(
          pack.pins.at(env_text(pack.registry["authored_manifest"])).path);
      if (pack.region != "shared-mechs") {
        env_catalog(pack, "world", "MW34SNP1", refs, world_bytes, world_pages);
        selected.world_manifests.push_back(
            pack.pins.at(env_text(pack.registry["world_manifest"])).path);
        const auto detail = pack.registry.value("detail", EJson::object());
        if (!detail.is_object() || detail.size() > 3)
          env_fail("invalid detail resource table");
        for (const auto &entry : detail.items()) {
          if (entry.key() != "water" && entry.key() != "surf" &&
              entry.key() != "cloud")
            env_fail("unknown detail role");
          const auto name = env_text(entry.value());
          if (!pack.pins.count(name) || pack.pins.at(name).format != "BWSNR2")
            env_fail("invalid detail role");
          refs.insert(name);
          const auto role = entry.key() == "water"  ? EnvironmentRole::water
                            : entry.key() == "surf" ? EnvironmentRole::surf
                                                    : EnvironmentRole::cloud;
          selected.resources[pack.region][role] = pack.pins.at(name).path;
          const auto &digest = pack.pins.at(name).digest;
          if (common.count(entry.key()) && common[entry.key()] != digest)
            env_fail("conflicting shared detail resource");
          common[entry.key()] = digest;
          selected.detail_digests[role] = digest;
        }
        const auto name = env_text(pack.registry.at("effects"));
        if (!pack.pins.count(name) || pack.pins.at(name).format != "MWFX1")
          env_fail("invalid effects role");
        refs.insert(name);
        selected.resources[pack.region][EnvironmentRole::effects] =
            pack.pins.at(name).path;
        const auto &digest = pack.pins.at(name).digest;
        if (common.count("effects") && common["effects"] != digest)
          env_fail("conflicting shared effects");
        common["effects"] = digest;
      }
      for (const char *role :
           {"lighting", "ground_surface_materials", "surface_materials"})
        if (pack.registry.contains(role)) {
          const auto name = env_text(pack.registry[role]);
          if (!pack.pins.count(name) ||
              pack.pins.at(name).format != (std::string(role) == "lighting"
                                                ? "MW34-lighting-v1"
                                                : "BWSFM1"))
            env_fail("invalid optional resource role");
          refs.insert(name);
          if (std::string(role) == "lighting")
            env_lighting(efs::u8path(pack.pins.at(name).path), pack.region,
                         &selected);
          const auto role_enum = std::string(role) == "lighting"
                                     ? EnvironmentRole::lighting
                                 : std::string(role) == "ground_surface_materials"
                                     ? EnvironmentRole::ground_materials
                                     : EnvironmentRole::surface_materials;
          selected.resources[pack.region][role_enum] = pack.pins.at(name).path;
          if (role_enum == EnvironmentRole::surface_materials ||
              (role_enum == EnvironmentRole::ground_materials &&
               !selected.resources.at(pack.region).count(EnvironmentRole::surface_materials)))
            selected.surface_material_digests[pack.region] = pack.pins.at(name).digest;
        }
      const bool streamed = pack.registry.contains("streamed_height_materials");
      const bool legacy_targets = pack.registry.contains("material_targets");
      if (streamed && legacy_targets)
        env_fail("streamed and legacy target registries cannot coexist in one region");
      if (streamed || legacy_targets) {
        const std::set<std::string> allowed = {
            "schema_version", "payload_profile", "operation", "banks", "detail",
            "authored", "authored_manifest", "world", "world_manifest", "effects",
            "lighting", "ground_surface_materials", "surface_materials", "material_targets",
            "streamed_height_materials"};
        for (const auto &field : pack.registry.items())
          if (!allowed.count(field.key()))
            env_fail("unknown material-target environment registry field");
        if (streamed) {
          auto index = std::make_shared<StreamedHeightIndex>();
          selected.material_targets.emplace(pack.region, env_streamed_heights(pack, refs, *index));
          selected.streamed_heights = std::move(index);
        } else {
          if (!pack.material_targets_declared || !pack.surface_materials_declared)
            env_fail("material target format is not declared");
          selected.material_targets.emplace(
              pack.region, env_material_targets(pack, refs, target_encoded_bytes, target_cache,
                                                 reusable, budget));
        }
      }
      if (refs.size() != pack.pins.size())
        env_fail("unused environment member");
      selected.regions.push_back(pack.region);
    }
    // Shape, ownership and global budgets are admitted before expensive
    // hashing.
    for (const auto &pack : packs) {
      fold(pack.root);
      fold(pack.manifest_digest);
      for (const auto &member : pack.pins) {
        const auto &pin = member.second;
        const auto path = efs::u8path(pin.path);
        if (efs::file_size(path) != pin.bytes ||
            verified_digest::sha256_file(path, pin.bytes) != pin.digest ||
            efs::file_size(path) != pin.bytes)
          env_fail("member integrity failure: " + member.first);
        fold(member.first);
        fold(pin.digest);
      }
    }
    selected.identity = roots.empty() ? std::string{} : identity.hex();
    return selected;
  } catch (const EJson::exception &error) {
    env_fail(std::string("schema mismatch: ") +
             std::string(error.what()).substr(0, 512));
  }
}
EnvironmentSelection load_environment_packs(const std::vector<std::string> &roots) {
  EnvSurfaceCache reusable;
  return load_environment_packs_impl(
      roots, std::make_shared<mw34::materials::SurfaceDecodedBudget>(), reusable);
}
const EnvironmentSelection &
EnvironmentPackCache::resolve(const std::vector<std::string> &roots) {
  try {
    for (auto entry = surface_cache_.begin(); entry != surface_cache_.end();)
      if (entry->second.expired())
        entry = surface_cache_.erase(entry);
      else
        ++entry;
    auto candidate = load_environment_packs_impl(roots, surface_budget_, surface_cache_);
    if (candidate.identity == selection_.identity) {
      ++hits_;
      return selection_;
    }
    selection_ = std::move(candidate);
    ++generation_;
    return selection_;
  } catch (...) {
    selection_ = {};
    selection_.surface_budget = surface_budget_;
    ++generation_;
    throw;
  }
}
} // namespace platform::prepared
