#include "assets.hpp"
#include "../m4-startup/admission.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>

using namespace mw34::m4_assets;
namespace {
std::string quote(std::string_view input) {
    std::ostringstream out; out << '"';
    constexpr char hex[] = "0123456789abcdef";
    for (unsigned char c : input) {
        if (c == '"' || c == '\\') out << '\\' << char(c);
        else if (c >= 32 && c < 127) out << char(c);
        else out << "\\u00" << hex[c >> 4] << hex[c & 15];
    }
    out << '"'; return out.str();
}
std::string hex(std::span<const std::byte> input) {
    constexpr char digits[] = "0123456789abcdef";
    std::string out;
    for (auto value : input) {
        const auto byte = std::to_integer<unsigned char>(value);
        out.push_back(digits[byte >> 4]); out.push_back(digits[byte & 15]);
    }
    return out;
}
ByteView read(const std::filesystem::path &path) {
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    if (!stream) throw std::runtime_error("Missing asset input");
    const auto size = stream.tellg();
    if (size < 0 || static_cast<std::uint64_t>(size) > Limits{}.max_source_bytes)
        throw std::runtime_error("Asset file exceeds byte limit");
    stream.seekg(0);
    std::vector<std::byte> bytes(static_cast<std::size_t>(size));
    if (!bytes.empty() && !stream.read(reinterpret_cast<char *>(bytes.data()),
                                      static_cast<std::streamsize>(bytes.size())))
        throw std::runtime_error("Asset input read failed");
    return AssetStore::copy(bytes, path.string());
}
void identity(const ByteView &view) {
    const auto &id = view.identity();
    std::cout << "\"source\":{\"label\":" << quote(id.label)
              << ",\"sha256\":" << quote(id.sha256) << ",\"size_bytes\":" << id.size_bytes
              << "},\"view_offset\":" << view.source_offset()
              << ",\"view_bytes\":" << view.bytes().size();
}
void emit_document(const Document &document) {
    std::cout << '{'; identity(document.source());
    std::cout << ",\"payload_sha256\":" << quote(mw34::m4::sha256(document.source().bytes()))
              << ",\"nodes\":[";
    bool comma{};
    for (std::size_t i = 0; i < document.nodes().size(); ++i) {
        const auto &node = document.node(i);
        if (comma) std::cout << ',';
        comma = true;
        std::cout << "{\"index\":" << i << ",\"type\":" << static_cast<std::uint32_t>(node.type)
                  << ",\"offset\":" << node.source_offset << ",\"end\":" << node.source_end;
        if (node.type == TokenType::integer || node.type == TokenType::float_bits)
            std::cout << ",\"word\":" << node.word;
        else if (node.type == TokenType::string)
            std::cout << ",\"string_offset\":" << node.string_offset
                      << ",\"string_hex\":" << quote(hex(document.string_bytes(i)));
        else {
            std::cout << ",\"children\":[";
            for (std::size_t k = 0; k < node.children.size(); ++k) {
                if (k) std::cout << ',';
                std::cout << node.children[k];
            }
            std::cout << ']';
        }
        std::cout << '}';
    }
    std::cout << "]}";
}
} // namespace

int main(int argc, char **argv) {
    try {
        if (argc < 3) { std::cerr << "Usage: mw34_m4_assets --directory FILE | --document FILE ENTRY [LABEL]\n"; return 2; }
        const std::string mode = argv[1];
        if (!((mode == "--directory" && argc == 3) ||
              (mode == "--document" && (argc == 4 || argc == 5)))) {
            std::cerr << "Usage: mw34_m4_assets --directory FILE | --document FILE ENTRY [LABEL]\n"; return 2;
        }
        const auto archive = ReaderArchive::parse(read(argv[2]));
        if (mode == "--directory") {
            std::cout << '{'; identity(archive.source());
            std::cout << ",\"directory_offset\":" << archive.directory_offset() << ",\"entries\":[";
            for (std::size_t i = 0; i < archive.entries().size(); ++i) {
                const auto &entry = archive.entries()[i];
                if (i) std::cout << ',';
                std::cout << "{\"index\":" << i << ",\"directory_offset\":" << entry.directory_offset
                          << ",\"offset\":" << entry.payload_offset << ",\"bytes\":" << entry.payload_bytes
                          << ",\"name\":" << quote(entry.name) << ",\"opaque_word\":" << entry.opaque_word
                          << ",\"metadata_hex\":" << quote(hex(entry.metadata)) << '}';
            }
            std::cout << "]}\n";
        } else {
            const auto *entry = archive.find_ascii(argv[3]);
            if (!entry) throw std::runtime_error("Archive entry not found");
            std::size_t index{};
            while (&archive.entries()[index] != entry) ++index;
            const auto document = Document::parse(archive.payload(index));
            // Resolve a requested label before publishing any JSON.
            const Node *label = nullptr;
            if (argc == 5) {
                label = document.find_label(0, argv[4]);
                if (!label) throw std::runtime_error("Document label not found");
            }
            std::cout << "{\"document\":"; emit_document(document);
            if (label) std::cout << ",\"label_node\":" << document.index_of(*label);
            std::cout << ",\"original_x86_executed\":false,\"widgets_created\":false}\n";
        }
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
