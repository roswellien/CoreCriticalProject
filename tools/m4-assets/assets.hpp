#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace mw34::m4_assets {

class AssetError : public std::runtime_error {
  public:
    AssetError(std::size_t source_offset, std::string reason);
    [[nodiscard]] std::size_t source_offset() const noexcept { return offset_; }
  private:
    std::size_t offset_;
};

struct Limits {
    std::size_t max_source_bytes = 128U * 1024U * 1024U;
    std::size_t max_entries = 65536;
    std::size_t max_nodes = 1000000;
    std::size_t max_depth = 128;
    std::size_t max_string_bytes = 16U * 1024U * 1024U;
};

struct SourceIdentity {
    std::string label;
    std::string sha256;
    std::size_t size_bytes{};
};

// Host-only immutable storage. Views retain shared ownership of a private copy;
// none of these addresses or references are guest pointers or file HANDLEs.
class ByteView {
  public:
    [[nodiscard]] std::span<const std::byte> bytes() const noexcept;
    [[nodiscard]] const SourceIdentity &identity() const noexcept;
    [[nodiscard]] std::size_t source_offset() const noexcept { return offset_; }
    [[nodiscard]] ByteView subview(std::size_t offset, std::size_t count) const;
  private:
    struct Source;
    friend class AssetStore;
    ByteView(std::shared_ptr<const Source> source, std::size_t offset, std::size_t size);
    std::shared_ptr<const Source> source_;
    std::size_t offset_, size_;
};

class AssetStore {
  public:
    [[nodiscard]] static ByteView copy(std::span<const std::byte> bytes,
                                       std::string label, const Limits &limits = {});
};

struct ArchiveEntry {
    std::size_t directory_offset{};
    std::uint32_t payload_offset{}, payload_bytes{};
    std::string name;
    std::uint32_t opaque_word{};
    // Preserved opaque metadata. No compression/path/timestamp interpretation.
    std::vector<std::byte> metadata;
};

class ReaderArchive {
  public:
    [[nodiscard]] static ReaderArchive parse(ByteView source, const Limits &limits = {});
    [[nodiscard]] const ByteView &source() const noexcept { return source_; }
    [[nodiscard]] std::size_t directory_offset() const noexcept {
        return source_.source_offset() + directory_offset_;
    }
    [[nodiscard]] const std::vector<ArchiveEntry> &entries() const noexcept { return entries_; }
    // The reached original uses _stricmp at 0x576A9E. This bounded interface
    // implements the ASCII subset only; locale-dependent non-ASCII is rejected.
    [[nodiscard]] const ArchiveEntry *find_ascii(std::string_view name) const;
    [[nodiscard]] ByteView payload(std::size_t index) const;
  private:
    explicit ReaderArchive(ByteView source) : source_(std::move(source)) {}
    ByteView source_;
    std::size_t directory_offset_{};
    std::vector<ArchiveEntry> entries_;
};

enum class TokenType : std::uint32_t { integer = 1, float_bits = 2, string = 3, list = 4 };
struct Node {
    TokenType type;
    std::size_t source_offset{}, source_end{};
    std::uint32_t word{};
    std::size_t string_offset{}, string_bytes{};
    std::vector<std::size_t> children;
};

// Lossless binary tokens only. Numeric words stay bit patterns; there is no
// host float conversion, textual-ZRD fallback, widget creation or guest layout.
class Document {
  public:
    [[nodiscard]] static Document parse(ByteView payload, const Limits &limits = {});
    [[nodiscard]] const ByteView &source() const noexcept { return source_; }
    [[nodiscard]] const std::vector<Node> &nodes() const noexcept { return nodes_; }
    [[nodiscard]] const Node &node(std::size_t index) const;
    [[nodiscard]] std::span<const std::byte> string_bytes(std::size_t index) const;
    [[nodiscard]] std::int32_t integer(std::size_t index) const;
    // Depth-first, case-sensitive C-string label comparison, returns the next
    // child. Matches 0x556930 for well-formed labels with an in-list successor.
    // A terminal matching label is an explicit malformed-data error.
    [[nodiscard]] const Node *find_label(std::size_t list, std::string_view label) const;
    [[nodiscard]] std::size_t index_of(const Node &node) const;
  private:
    explicit Document(ByteView source) : source_(std::move(source)) {}
    ByteView source_;
    std::vector<Node> nodes_;
    std::size_t parse_node(std::size_t &cursor, std::size_t depth, const Limits &limits);
    const Node *find_label_impl(std::size_t list, std::string_view label) const;
};

} // namespace mw34::m4_assets
