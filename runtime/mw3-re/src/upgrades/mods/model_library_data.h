#pragma once

#include <cstdint>
#include <cstring>
#include <string>
#include <utility>
#include <vector>

// The binary layouts below are the ones consumed by cls_mechlib.cpp's
// read_material, read_node, read_model and read_tree, and emitted by
// cls_mechlib_json.cpp's materials/model/tree writers. This bounded walk only
// locates material indices; it does not allocate engine nodes or resolve textures.
namespace mech3::model_library_data {
using Bytes = std::vector<uint8_t>;

inline uint32_t word(const Bytes& bytes, size_t offset) {
  uint32_t value;
  std::memcpy(&value, bytes.data() + offset, 4);
  return value;
}
inline void put_word(Bytes& bytes, size_t offset, uint32_t value) {
  std::memcpy(bytes.data() + offset, &value, 4);
}

struct Cursor {
  const Bytes& bytes;
  size_t position = 0;
  bool take(uint64_t length, size_t* start = nullptr) {
    if (length > bytes.size() - position) return false;
    if (start) *start = position;
    position += static_cast<size_t>(length);
    return true;
  }
  bool number(uint32_t* value) {
    size_t start;
    if (!take(4, &start)) return false;
    *value = word(bytes, start);
    return true;
  }
};

inline bool materials(const Bytes& bytes, std::vector<Bytes>* records) {
  records->clear();
  Cursor cursor{bytes};
  uint32_t count;
  if (!cursor.number(&count) || count > (bytes.size() - 4) / 0x28) return false;
  for (uint32_t i = 0; i < count; ++i) {
    size_t start;
    if (!cursor.take(0x28, &start)) return false;
    // read_material: +0x10 is only a presence marker for a counted texture
    // name immediately after this 0x28-byte record (zutl_zar::read_string).
    if (word(bytes, start + 0x10)) {
      uint32_t length;
      if (!cursor.number(&length) || !cursor.take(length)) return false;
    }
    records->emplace_back(bytes.begin() + start, bytes.begin() + cursor.position);
  }
  return cursor.position == bytes.size();
}

inline Bytes material_key(Bytes record) {
  // Pointer values do not change the material's content. Keep all other record
  // bytes and the counted texture name in the comparison, including its length.
  if (word(record, 0x10)) put_word(record, 0x10, 1);
  return record;
}

class ModelWalk {
 public:
  ModelWalk(const Bytes& bytes, const std::vector<uint32_t>& mapping)
      : cursor{bytes}, mapping(mapping) {}

  bool tree(unsigned depth = 1) {
    size_t node;
    // read_node: 0xd0 node record, then 0x90 Object3d data; only class 5.
    if (depth > 64 || !cursor.take(0xd0 + 0x90, &node)) return fail("truncated or too deeply nested node");
    if (!std::memchr(cursor.bytes.data() + node, 0, 36) ||
        word(cursor.bytes, node + 0x34) != 5) return fail("invalid Object3d node");
    // read_tree: +0x3c says a model follows; +0x5c is the child count.
    if (word(cursor.bytes, node + 0x3c) && !model()) return false;
    const uint32_t children = word(cursor.bytes, node + 0x5c);
    if (children > (cursor.bytes.size() - cursor.position) / (0xd0 + 0x90))
      return fail("child count exceeds the model entry");
    for (uint32_t i = 0; i < children; ++i)
      if (!tree(depth + 1)) return false;
    return true;
  }

  bool complete() const { return cursor.position == cursor.bytes.size(); }
  std::string why;
  std::vector<std::pair<size_t, uint32_t>> patches;

 private:
  Cursor cursor;
  const std::vector<uint32_t>& mapping;

  bool fail(const char* message) { why = message; return false; }

  bool indices(uint32_t count, uint32_t limit) {
    size_t start;
    if (!cursor.take(uint64_t{count} * 4, &start)) return false;
    for (uint32_t i = 0; i < count; ++i)
      if (word(cursor.bytes, start + i * 4) >= limit) return false;
    return true;
  }

  bool model() {
    size_t header;
    if (!cursor.take(0x5c, &header)) return fail("truncated model header");
    // read_model: counts at +0x10/+0x14/+0x18/+0x1c, followed by the
    // vertices, normals and morphs (12 bytes each). Mechlib has no lights;
    // the JSON writer likewise refuses them, unlike the gamez model format.
    const uint32_t polygons = word(cursor.bytes, header + 0x10);
    const uint32_t vertices = word(cursor.bytes, header + 0x14);
    const uint32_t normals = word(cursor.bytes, header + 0x18);
    const uint32_t morphs = word(cursor.bytes, header + 0x1c);
    if (polygons > INT32_MAX || vertices > INT32_MAX || normals > INT32_MAX ||
        morphs > INT32_MAX || word(cursor.bytes, header + 0x20) != 0)
      return fail("unsupported model counts or lights");
    if (!cursor.take((uint64_t{vertices} + normals + morphs) * 12))
      return fail("truncated model arrays");
    size_t records;
    if (!cursor.take(uint64_t{polygons} * 0x24, &records)) return fail("truncated polygon records");
    for (uint32_t i = 0; i < polygons; ++i) {
      const size_t polygon = records + i * 0x24;
      // read_model: each 0x24 polygon stores material_index at +0x1c.
      const uint32_t material = word(cursor.bytes, polygon + 0x1c);
      if (material >= mapping.size()) return fail("material index outside its source table");
      patches.emplace_back(polygon + 0x1c, mapping[material]);
      const uint32_t flags = word(cursor.bytes, polygon);
      const uint32_t count = flags & 0xff;
      // The reader always takes vertex indices. Normal indices need flag
      // 0x200 and +0x0c; +0x10/+0x14 mark UV/color arrays (8/12 bytes each).
      if (!indices(count, vertices)) return fail("invalid vertex indices");
      if ((flags & 0x200) && word(cursor.bytes, polygon + 0x0c) && !indices(count, normals))
        return fail("invalid normal indices");
      if (word(cursor.bytes, polygon + 0x10) && !cursor.take(uint64_t{count} * 8))
        return fail("truncated polygon UVs");
      if (word(cursor.bytes, polygon + 0x14) && !cursor.take(uint64_t{count} * 12))
        return fail("truncated polygon colors");
    }
    return true;
  }
};

inline bool rewrite(Bytes* bytes, const std::vector<uint32_t>& mapping, std::string* why,
                    bool relocate = true) {
  ModelWalk walk(*bytes, mapping);
  if (!walk.tree()) { *why = walk.why; return false; }
  if (!walk.complete()) { *why = "unparsed bytes after the model tree"; return false; }
  // Nothing is modified until the entire tree and every index passed validation.
  // Models inheriting the base table are validated without rewriting any bytes.
  if (relocate)
    for (const auto& patch : walk.patches) put_word(*bytes, patch.first, patch.second);
  return true;
}
}  // namespace mech3::model_library_data
