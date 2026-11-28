#pragma once

#include <algorithm>
#include <charconv>
#include <filesystem>
#include <fstream>
#include <map>
#include <set>

#include "gamez/zclass/cls_mechlib_json.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zutil/zutl_zip.h"
#include "gamez/zutil/zutl_json.h"
#include "upgrades/mods/entry_archives.h"
#include "upgrades/mods/model_library_data.h"

namespace mech3::model_library_json {
namespace fs = std::filesystem;
// Eager source enumeration must not turn compressed JSON or a directory of
// entries into an unbounded allocation. Binary archives have their own data-
// area budget. JSON permits 16 MiB per entry and 64 MiB per source, before decode.
constexpr uint64_t kEntryLimit = 16 * 1024 * 1024;
constexpr uint64_t kSourceLimit = 64 * 1024 * 1024;

inline std::string lower(std::string text) {
  for (char& c : text) if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
  return text;
}
inline std::string entry_name(const std::string& file) {
  const std::string name = lower(file);
  if (name == "materials.json") return "materials";
  if (name.size() > 9 && name.find_first_of("/\\") == std::string::npos &&
      name.compare(name.size() - 9, 9, ".flt.json") == 0 && name.size() < 69)
    return name.substr(0, name.size() - 5);
  return {};
}

inline uint64_t array_bytes(const zutl_json::Value* value, uint64_t stride) {
  return value && value->kind == zutl_json::Value::Array ? value->items.size() * stride : 0;
}

inline bool decoded_size(const std::string& text, uint64_t* size) {
  zutl_json::Value document;
  std::string why;
  if (!zutl_json::parse(text, &document, &why)) return false;
  *size = 0;
  if (document.kind == zutl_json::Value::Array) {
    *size = 4;
    for (const auto& material : document.items) {
      *size += 0x28;
      if (const auto* textured = material.get("Textured"))
        if (const auto* name = textured->get("texture_name")) *size += 4 + name->text.size();
    }
    return *size <= kSourceLimit;
  }
  const auto* nodes = document.get("nodes");
  const auto* models = document.get("models");
  if (!nodes || !models) return false;
  std::vector<uint64_t> model_sizes;
  // Mirror the existing JSON writer's emitted spans, not its pointer values.
  // A shared model_index can duplicate one large geometry block at every node;
  // text-size limits alone would not bound that expansion.
  for (const auto& model : models->items) {
    uint64_t bytes = 0x5c + array_bytes(model.get("vertices"), 12) +
                     array_bytes(model.get("normals"), 12) + array_bytes(model.get("morphs"), 12);
    const auto* polygons = model.get("polygons");
    if (!polygons || array_bytes(model.get("lights"), 1)) return false;
    bytes += polygons->items.size() * 0x24;
    for (const auto& polygon : polygons->items) {
      bytes += array_bytes(polygon.get("vertex_indices"), 4) +
               array_bytes(polygon.get("normal_indices"), 4) + array_bytes(polygon.get("vertex_colors"), 12);
      if (const auto* materials = polygon.get("materials"); materials && !materials->items.empty())
        bytes += array_bytes(materials->items.front().get("uv_coords"), 8);
    }
    model_sizes.push_back(bytes);
  }
  for (const auto& node : nodes->items) {
    *size += 0xd0 + 0x90;
    const auto* index = node.get("model_index");
    if (!index) return false;
    if (index->kind == zutl_json::Value::Null || index->text == "-1") continue;
    uint32_t number = 0;
    const auto parsed = std::from_chars(index->text.data(), index->text.data() + index->text.size(), number);
    if (parsed.ec != std::errc{} || parsed.ptr != index->text.data() + index->text.size() ||
        number >= model_sizes.size()) return false;
    *size += model_sizes[number];
    if (*size > kSourceLimit) return false;
  }
  return *size <= kSourceLimit;
}

template <typename Say>
void read(const std::string& root, std::map<std::string, ArchiveEntry>* entries, Say say,
          bool* materials_present, std::set<std::string>* refused_models) {
  uint64_t used = 0;
  uint64_t decoded = 0;
  std::set<std::string> folder_names;
  const auto refuse = [&](const std::string& name, const std::string& message) {
    // Legacy JSON errors fall back to binary entries, not to a later mod's
    // JSON. Retain that refusal even when conversion produced no entry bytes.
    if (name != "materials") refused_models->insert(name);
    say(message);
  };
  const auto convert = [&](const std::string& name, const std::string& text, const std::string& source) {
    uint64_t size;
    if (!decoded_size(text, &size) || size > kSourceLimit - decoded) {
      refuse(name, "mods: " + source + ": invalid JSON or decoded model source exceeds 64 MiB, entry left out");
      return;
    }
    decoded += size;
    ArchiveEntry converted;
    converted.name = name;
    std::string why;
    const bool valid = name == "materials"
        ? zcls::mechlib_materials_from_json(text, &converted.data, &why)
        : zcls::mechlib_model_from_json(text, &converted.data, &why);
    if (valid) (*entries)[name] = std::move(converted);
    else refuse(name, "mods: " + source + ": " + why + ", JSON entry left out");
  };
  std::error_code error;
  const std::string folder = zutl::any_case(root, "zbd/mechlib");
  if (!folder.empty()) {
    std::vector<fs::path> files;
    for (fs::directory_iterator it(folder, error), end; !error && it != end; it.increment(error))
      if (it->is_regular_file(error)) files.push_back(it->path());
    if (error) say("mods: " + folder + ": cannot enumerate model JSON, left out");
    std::sort(files.begin(), files.end());
    for (const auto& file : files) {
      const std::string name = entry_name(file.filename().string());
      if (name.empty()) continue;
      // Existence is distinct from successful decoding: broken materials
      // must not silently turn a source into a base-table inheritor.
      if (name == "materials") *materials_present = true;
      else if (refused_models->count(name)) continue;
      if (!folder_names.insert(name).second) {
        say("mods: " + folder + ": repeated JSON entry " + name + ", first occurrence used");
        continue;
      }
      const uint64_t size = fs::file_size(file, error);
      if (error || size > kEntryLimit || size > kSourceLimit - used) {
        refuse(name, "mods: " + file.generic_string() + ": unreadable or oversized model JSON, left out");
        continue;
      }
      used += size;
      std::ifstream stream(file, std::ios::binary);
      std::string text(static_cast<size_t>(size), '\0');
      stream.read(text.data(), static_cast<std::streamsize>(size));
      if (!stream || stream.peek() != std::char_traits<char>::eof()) {
        refuse(name, "mods: " + file.generic_string() + ": model JSON changed or cannot be read, left out");
        continue;
      }
      convert(name, text, file.generic_string());
    }
  }
  const std::string path = zutl::any_case(root, "zbd/mechlib.zip");
  if (path.empty()) return;
  const auto bad_zip = [&] { say("mods: " + path + ": unreadable or oversized model JSON zip, left out"); };
  const uint64_t size = fs::file_size(path, error);
  if (error || size < 22 || size > kSourceLimit) { bad_zip(); return; }
  // Zip::open allocates its central-directory size from EOCD. Check that size
  // against the real file first, before passing untrusted metadata to it.
  const size_t tail_size = static_cast<size_t>(std::min<uint64_t>(size, 65557));
  model_library_data::Bytes tail(tail_size);
  std::ifstream input(path, std::ios::binary);
  input.seekg(static_cast<std::streamoff>(size - tail_size));
  input.read(reinterpret_cast<char*>(tail.data()), static_cast<std::streamsize>(tail.size()));
  bool bounded = false;
  for (size_t offset = tail_size - 22 + 1; input && offset-- > 0;) {
    if (model_library_data::word(tail, offset) == 0x06054b50) {
      bounded = model_library_data::word(tail, offset + 12) <= size - tail_size + offset;
      break;
    }
  }
  zutl_zip::Zip zip;
  if (!bounded || !zip.open(path)) { bad_zip(); return; }
  std::set<std::string> zip_names;
  for (const auto& entry : zip.entries) {
    const std::string name = entry_name(entry.name);
    if (name.empty() || folder_names.count(name)) continue;
    if (name == "materials") *materials_present = true;
    else if (refused_models->count(name)) continue;
    if (!zip_names.insert(name).second) {
      say("mods: " + path + ": repeated JSON entry " + name + ", first occurrence used");
      continue;
    }
    if (!entry.usize || entry.usize > kEntryLimit || entry.csize > size ||
        entry.usize > kSourceLimit - used) {
      refuse(name, "mods: " + path + ": " + entry.name + ": empty or oversized JSON entry, left out");
      continue;
    }
    used += entry.usize;
    std::vector<uint8_t> bytes;
    std::string why;
    if (!zip.read(entry, &bytes, &why) || bytes.size() > kEntryLimit) {
      refuse(name, "mods: " + path + ": " + entry.name + ": unreadable JSON entry, left out");
      continue;
    }
    convert(name, std::string(bytes.begin(), bytes.end()), path + ":" + entry.name);
  }
}
}  // namespace mech3::model_library_json
