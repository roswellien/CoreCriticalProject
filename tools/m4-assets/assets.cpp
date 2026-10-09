#include "assets.hpp"
#include "../m4-startup/admission.hpp"

#include <algorithm>
#include <bit>
#include <limits>
#include <utility>

namespace mw34::m4_assets {
namespace {
void require(bool condition, std::size_t offset, const char *reason) {
    if (!condition) throw AssetError(offset, reason);
}
std::uint32_t word(std::span<const std::byte> bytes, std::size_t offset,
                   std::size_t base) {
    require(offset <= bytes.size() && bytes.size() - offset >= 4, base + offset,
            "Truncated binary word");
    std::uint32_t value{};
    for (unsigned i = 0; i < 4; ++i)
        value |= std::uint32_t(std::to_integer<unsigned char>(bytes[offset + i])) << (i * 8);
    return value;
}
bool ascii(std::string_view value) {
    return std::all_of(value.begin(), value.end(), [](unsigned char c) { return c && c < 128; });
}
unsigned char fold(unsigned char c) { return c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c; }
bool equal_ascii(std::string_view left, std::string_view right) {
    return left.size() == right.size() && std::equal(left.begin(), left.end(), right.begin(),
        [](unsigned char a, unsigned char b) { return fold(a) == fold(b); });
}
} // namespace

AssetError::AssetError(std::size_t offset, std::string reason)
    : std::runtime_error(std::move(reason) + " at source offset " + std::to_string(offset)),
      offset_(offset) {}

struct ByteView::Source {
    std::vector<std::byte> bytes;
    SourceIdentity identity;
};
ByteView::ByteView(std::shared_ptr<const Source> source, std::size_t offset, std::size_t size)
    : source_(std::move(source)), offset_(offset), size_(size) {}
std::span<const std::byte> ByteView::bytes() const noexcept {
    return std::span<const std::byte>(source_->bytes).subspan(offset_, size_);
}
const SourceIdentity &ByteView::identity() const noexcept { return source_->identity; }
ByteView ByteView::subview(std::size_t offset, std::size_t count) const {
    require(offset <= size_ && count <= size_ - offset, offset_, "Asset view outside owned source");
    return ByteView(source_, offset_ + offset, count);
}
ByteView AssetStore::copy(std::span<const std::byte> bytes, std::string label, const Limits &limits) {
    require(bytes.size() <= limits.max_source_bytes, 0, "Asset source exceeds byte limit");
    auto source = std::make_shared<ByteView::Source>();
    source->bytes.assign(bytes.begin(), bytes.end());
    source->identity = {std::move(label), m4::sha256(source->bytes), source->bytes.size()};
    return ByteView(std::move(source), 0, bytes.size());
}

ReaderArchive ReaderArchive::parse(ByteView source, const Limits &limits) {
    const auto bytes = source.bytes();
    const auto base = source.source_offset();
    require(bytes.size() <= limits.max_source_bytes, base, "Archive exceeds byte limit");
    require(bytes.size() >= 8, base, "Truncated reader archive footer");
    // 0x5767E4 seeks -8; 0x5767FE/0x576812 read version then count.
    const auto footer = bytes.size() - 8;
    require(word(bytes, footer, base) == 1, base + footer, "Unsupported reader archive version");
    const auto count = word(bytes, footer + 4, base);
    require(count <= limits.max_entries && count <= 0x7fffffffU, base + footer + 4,
            "Reader archive entry count exceeds limit");
    constexpr std::size_t record_bytes = 0x94;
    require(count <= footer / record_bytes, base + footer, "Truncated reader archive directory");
    ReaderArchive result(std::move(source));
    result.directory_offset_ = footer - std::size_t(count) * record_bytes;
    result.entries_.reserve(count);
    for (std::size_t i = 0; i < count; ++i) {
        const auto offset = result.directory_offset_ + i * record_bytes;
        ArchiveEntry entry;
        entry.directory_offset = base + offset;
        entry.payload_offset = word(bytes, offset, base);
        entry.payload_bytes = word(bytes, offset + 4, base);
        require(entry.payload_offset <= result.directory_offset_ &&
                entry.payload_bytes <= result.directory_offset_ - entry.payload_offset,
                base + offset, "Archive payload overlaps directory or exceeds source");
        const auto name = bytes.subspan(offset + 8, 64);
        const auto end = std::find(name.begin(), name.end(), std::byte{0});
        require(end != name.end(), base + offset + 8, "Unterminated reader archive name");
        for (auto p = name.begin(); p != end; ++p)
            entry.name.push_back(char(std::to_integer<unsigned char>(*p)));
        entry.opaque_word = word(bytes, offset + 0x48, base);
        const auto metadata = bytes.subspan(offset + 0x4c, 72);
        entry.metadata.assign(metadata.begin(), metadata.end());
        result.entries_.push_back(std::move(entry));
    }
    return result;
}
const ArchiveEntry *ReaderArchive::find_ascii(std::string_view name) const {
    require(ascii(name), source_.source_offset(), "Archive lookup requires a non-NUL ASCII name");
    for (const auto &entry : entries_) {
        require(ascii(entry.name), entry.directory_offset + 8,
                "Non-ASCII archive names require a provider locale contract");
        if (equal_ascii(entry.name, name)) return &entry;
    }
    return nullptr;
}
ByteView ReaderArchive::payload(std::size_t index) const {
    require(index < entries_.size(), source_.source_offset(), "Invalid archive entry index");
    const auto &entry = entries_[index];
    return source_.subview(entry.payload_offset, entry.payload_bytes);
}

Document Document::parse(ByteView payload, const Limits &limits) {
    require(payload.bytes().size() <= limits.max_source_bytes, payload.source_offset(),
            "Binary document exceeds byte limit");
    require(limits.max_depth <= 512, payload.source_offset(), "Unsupported parser depth limit");
    Document result(std::move(payload));
    std::size_t cursor{};
    result.parse_node(cursor, 0, limits);
    require(cursor == result.source_.bytes().size(), result.source_.source_offset() + cursor,
            "Trailing bytes after binary document");
    return result;
}
std::size_t Document::parse_node(std::size_t &cursor, std::size_t depth, const Limits &limits) {
    const auto bytes = source_.bytes();
    const auto base = source_.source_offset();
    require(depth <= limits.max_depth, base + cursor, "Binary document depth limit exceeded");
    require(nodes_.size() < limits.max_nodes, base + cursor, "Binary document node limit exceeded");
    const auto begin = cursor;
    const auto type = word(bytes, cursor, base); cursor += 4;
    require(type >= 1 && type <= 4, base + begin, "Unknown binary token type");
    const auto index = nodes_.size();
    nodes_.push_back(Node{static_cast<TokenType>(type), base + begin, 0, 0, 0, 0, {}});
    const auto value = word(bytes, cursor, base); cursor += 4;
    if (type <= 2) {
        nodes_[index].word = value;
    } else if (type == 3) {
        require(value <= 0x7fffffffU && value <= limits.max_string_bytes,
                base + begin + 4, "Binary string length exceeds limit");
        require(cursor <= bytes.size() && value <= bytes.size() - cursor,
                base + cursor, "Truncated binary string");
        nodes_[index].string_offset = base + cursor;
        nodes_[index].string_bytes = value;
        cursor += value;
    } else {
        // 0x5571F3 creates a synthetic metadata token in slot 0; it is not on
        // the wire. The serialized count includes that slot, hence count - 1.
        require(value >= 1 && value <= 0x7fffffffU, base + begin + 4,
                "Invalid binary list count");
        const auto child_count = std::size_t(value) - 1;
        require(child_count <= limits.max_nodes - nodes_.size(), base + begin + 4,
                "Binary list count exceeds node limit");
        require(child_count <= (bytes.size() - cursor) / 8, base + begin + 4,
                "Truncated binary list children");
        nodes_[index].children.reserve(child_count);
        for (std::size_t i = 0; i < child_count; ++i) {
            const auto child = parse_node(cursor, depth + 1, limits);
            nodes_[index].children.push_back(child);
        }
    }
    nodes_[index].source_end = base + cursor;
    return index;
}
const Node &Document::node(std::size_t index) const {
    require(index < nodes_.size(), source_.source_offset(), "Invalid document node index");
    return nodes_[index];
}
std::span<const std::byte> Document::string_bytes(std::size_t index) const {
    const auto &value = node(index);
    require(value.type == TokenType::string, value.source_offset, "Document node is not a string");
    return source_.subview(value.string_offset - source_.source_offset(), value.string_bytes).bytes();
}
std::int32_t Document::integer(std::size_t index) const {
    const auto &value = node(index);
    require(value.type == TokenType::integer, value.source_offset, "Document node is not an integer");
    return std::bit_cast<std::int32_t>(value.word);
}
const Node *Document::find_label(std::size_t list, std::string_view label) const {
    require(label.find('\0') == std::string_view::npos, source_.source_offset(),
            "Label query must not contain NUL");
    return find_label_impl(list, label);
}
const Node *Document::find_label_impl(std::size_t list, std::string_view label) const {
    const auto &parent = node(list);
    if (parent.type != TokenType::list) return nullptr;
    for (std::size_t i = 0; i < parent.children.size(); ++i) {
        const auto child = parent.children[i];
        const auto &value = nodes_[child];
        if (value.type == TokenType::list) {
            if (const auto *found = find_label_impl(child, label)) return found;
        } else if (value.type == TokenType::string) {
            const auto text = string_bytes(child);
            const auto end = std::find(text.begin(), text.end(), std::byte{0});
            const auto length = std::size_t(end - text.begin());
            const bool same = label.size() == length && std::equal(text.begin(), end, label.begin(),
                [](std::byte a, char b) { return std::to_integer<unsigned char>(a) == static_cast<unsigned char>(b); });
            if (same) {
                require(i + 1 < parent.children.size(), value.source_offset,
                        "Matching label lacks an in-list successor");
                return &nodes_[parent.children[i + 1]];
            }
        }
    }
    return nullptr;
}
std::size_t Document::index_of(const Node &value) const {
    // Equality of actual element addresses avoids unrelated-pointer subtraction.
    for (std::size_t i = 0; i < nodes_.size(); ++i) if (&nodes_[i] == &value) return i;
    throw AssetError(source_.source_offset(), "Node is not owned by this document");
}

} // namespace mw34::m4_assets
