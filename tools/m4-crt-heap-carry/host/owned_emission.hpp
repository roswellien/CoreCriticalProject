#pragma once

#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <istream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace mw34::emission {

using Point = std::array<float, 3>;
using Region = std::array<float, 4>;
struct Binding {
    std::string owner, material;
    std::uint32_t width{}, height{};
    std::uint64_t hash{};
    Point low{}, high{};
    bool rigid{true};
};
struct Anchor {
    std::string id;
    Point position{}, color{};
    float radius{}, intensity{};
};
struct Record {
    std::string id;
    std::uint32_t batch{};
    float strength{};
    std::vector<Region> regions;
    std::vector<Anchor> anchors;
};

// A draw owns a value snapshot of its source pose. No guest pointers or light
// observations survive into another scene or frame.
struct Instance {
    std::shared_ptr<const Record> material;
    std::uint32_t root{};
    std::string owner;
    std::array<float, 12> world{};
};

// Files contain no image payloads. Bound the input before allocating records;
// all identities refer to independently authenticated mesh and color data.
class Reader {
  public:
    explicit Reader(std::istream &input) : bytes_(1024 * 1024 + 1) {
        input.read(bytes_.data(), std::streamsize(bytes_.size()));
        const auto size = input.gcount();
        if (input.bad() || size < 20 || size > 1024 * 1024)
            fail("Invalid owned emission size");
        bytes_.resize(std::size_t(size));
    }
    static void fail(const char *message) { throw std::runtime_error(message); }
    std::uint32_t number() {
        require(4);
        std::uint32_t value{};
        for (unsigned shift = 0; shift < 32; shift += 8)
            value |= std::uint32_t(static_cast<unsigned char>(bytes_[offset_++])) << shift;
        return value;
    }
    std::uint64_t identity() {
        const auto low = number();
        return low | (std::uint64_t(number()) << 32);
    }
    float scalar(float low, float high) {
        const float value = std::bit_cast<float>(number());
        if (!std::isfinite(value) || value < low || value > high)
            fail("Invalid emission floating point value");
        return value;
    }
    std::string name() {
        require(32);
        std::string result;
        bool ended{};
        for (unsigned i = 0; i < 32; ++i) {
            const unsigned char value = bytes_[offset_++];
            if (!value) {
                ended = true;
                continue;
            }
            const bool valid = (value >= 'a' && value <= 'z') || (value >= 'A' && value <= 'Z') ||
                               (value >= '0' && value <= '9') || value == '_' || value == '.' ||
                               value == '-';
            if (ended || !valid)
                fail("Invalid emission name");
            result.push_back(char(value));
        }
        if (!ended || result.empty())
            fail("Invalid emission name");
        return result;
    }
    void magic() {
        require(8);
        if (std::string(bytes_.data(), 8) != std::string("BWMEM1\0\0", 8))
            fail("Unsupported owned emission format");
        offset_ += 8;
    }
    void finish() const {
        if (offset_ != bytes_.size())
            fail("Trailing owned emission bytes");
    }

  private:
    void require(std::size_t size) const {
        if (size > bytes_.size() - offset_)
            fail("Truncated owned emission");
    }
    std::vector<char> bytes_;
    std::size_t offset_{};
};

inline std::vector<Record> read(std::istream &input, std::uint64_t mesh_hash,
                                const std::vector<Binding> &bindings) {
    Reader reader(input);
    reader.magic();
    const auto count = reader.number();
    if (!count || count > 64 || reader.identity() != mesh_hash)
        Reader::fail("Emission mesh identity/count mismatch");
    std::set<std::string> ids;
    std::set<std::uint32_t> batches;
    std::vector<Record> records;
    for (unsigned index = 0; index < count; ++index) {
        Record record;
        record.id = reader.name();
        record.batch = reader.number();
        const auto owner = reader.name(), material = reader.name();
        const auto width = reader.number(), height = reader.number();
        const auto hash = reader.identity();
        if (!ids.insert(record.id).second || !batches.insert(record.batch).second ||
            record.batch >= bindings.size())
            Reader::fail("Duplicate or invalid emission binding");
        const auto &binding = bindings[record.batch];
        if (!binding.rigid)
            Reader::fail("Emission version 1 requires a rigid batch");
        if (owner != binding.owner || material != binding.material || width != binding.width ||
            height != binding.height || hash != binding.hash)
            Reader::fail("Emission material identity mismatch");
        for (unsigned axis = 0; axis < 3; ++axis)
            if (!std::isfinite(binding.low[axis]) || !std::isfinite(binding.high[axis]) ||
                binding.low[axis] > binding.high[axis])
                Reader::fail("Invalid emission mesh bounds");
        record.strength = reader.scalar(0, 2);
        const auto regions = reader.number(), anchors = reader.number();
        if (!regions || regions > 32 || anchors > 8)
            Reader::fail("Invalid emission region/anchor count");
        for (unsigned region = 0; region < regions; ++region) {
            Region rectangle{};
            for (auto &coordinate : rectangle)
                coordinate = reader.scalar(0, 1);
            if (rectangle[0] >= rectangle[2] || rectangle[1] >= rectangle[3])
                Reader::fail("Empty emission UV rectangle");
            record.regions.push_back(rectangle);
        }
        std::set<std::string> anchor_ids;
        for (unsigned anchor_index = 0; anchor_index < anchors; ++anchor_index) {
            Anchor anchor;
            anchor.id = reader.name();
            for (unsigned axis = 0; axis < 3; ++axis)
                anchor.position[axis] = reader.scalar(-1e6f, 1e6f);
            for (auto &component : anchor.color)
                component = reader.scalar(0, 1);
            anchor.radius = reader.scalar(0, 4);
            anchor.intensity = reader.scalar(0, 2);
            if (!anchor_ids.insert(anchor.id).second)
                Reader::fail("Duplicate emission anchor");
            for (unsigned axis = 0; axis < 3; ++axis)
                if (anchor.position[axis] < binding.low[axis] - 4 ||
                    anchor.position[axis] > binding.high[axis] + 4)
                    Reader::fail("Out-of-bounds emission anchor");
            record.anchors.push_back(std::move(anchor));
        }
        records.push_back(std::move(record));
    }
    reader.finish();
    return records;
}
} // namespace mw34::emission
