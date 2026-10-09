#include "assets.hpp"

#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

using namespace mw34::m4_assets;
namespace {
using Bytes = std::vector<std::byte>;
std::size_t controls{};
void check(bool value, const char *reason) {
    ++controls;
    if (!value) throw std::runtime_error(reason);
}
void append(Bytes &bytes, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) bytes.push_back(std::byte((value >> (8 * i)) & 255));
}
void patch(Bytes &bytes, std::size_t offset, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) bytes[offset + i] = std::byte((value >> (8 * i)) & 255);
}
Bytes scalar(std::uint32_t type, std::uint32_t word) { Bytes b; append(b,type); append(b,word); return b; }
Bytes text(std::string_view value) {
    auto b = scalar(3, static_cast<std::uint32_t>(value.size()));
    for (unsigned char c : value) b.push_back(std::byte(c));
    return b;
}
Bytes list(std::initializer_list<Bytes> children) {
    auto b = scalar(4, static_cast<std::uint32_t>(children.size() + 1));
    for (const auto &child : children) b.insert(b.end(),child.begin(),child.end());
    return b;
}
Bytes archive(Bytes payload, std::initializer_list<std::string> names = {"Demo.ZRD"}) {
    const auto size = static_cast<std::uint32_t>(payload.size());
    for (const auto &name : names) {
        const auto start = payload.size(); payload.resize(start + 148);
        patch(payload,start,0); patch(payload,start + 4,size);
        for (std::size_t i = 0; i < name.size(); ++i) payload[start + 8 + i] = std::byte(name[i]);
        patch(payload,start + 72,0xcafe);
    }
    append(payload,1); append(payload,static_cast<std::uint32_t>(names.size())); return payload;
}
ByteView view(const Bytes &b, const Limits &limits = {}) { return AssetStore::copy(b,"authored fixture",limits); }
template<class F> void rejects(F operation, std::string_view diagnostic) {
    try { operation(); } catch (const AssetError &error) {
        check(std::string_view(error.what()).find(diagnostic) != std::string_view::npos,
              "Wrong intended rejection diagnostic"); return;
    }
    throw std::runtime_error("Missing intended rejection");
}
} // namespace

int main() {
    try {
        auto binary = list({text("KEY"),scalar(1,0xffffffff),text("FLOAT"),scalar(2,0x7fc12345),
                            text("BYTES"),text(std::string_view("A\0B",3))});
        auto source = archive(binary,{"Demo.ZRD","dEmO.zrd"});
        auto ar = ReaderArchive::parse(view(source));
        check(ar.entries().size() == 2 && ar.directory_offset() == binary.size(), "Directory layout");
        check(ar.find_ascii("DEMO.ZRD") == &ar.entries()[0], "First ASCII-insensitive match");
        check(ar.find_ascii("missing") == nullptr, "No lookup default");
        check(ar.entries()[0].opaque_word == 0xcafe && ar.entries()[0].metadata.size() == 72, "Opaque metadata");
        source[0] = std::byte{0}; // A host view retains a private snapshot.
        auto doc = Document::parse(ar.payload(0));
        check(doc.nodes().size() == 7 && doc.node(0).children.size() == 6, "Count includes synthetic metadata slot");
        auto value = doc.find_label(0,"KEY");
        check(value && doc.integer(doc.index_of(*value)) == -1, "Lossless signed integer");
        value = doc.find_label(0,"FLOAT");
        check(value && value->word == 0x7fc12345, "Preserved NaN payload");
        value = doc.find_label(0,"BYTES");
        check(value && doc.string_bytes(doc.index_of(*value)).size() == 3, "Embedded NUL bytes preserved");
        check(doc.find_label(0,"key") == nullptr, "Case-sensitive document label");
        auto nested = Document::parse(view(list({list({text("SAME"),scalar(1,7)}),text("SAME"),scalar(1,9)})));
        value = nested.find_label(0,"SAME"); check(value && value->word == 7, "Depth-first first matching successor");
        auto nul = Document::parse(view(list({text(std::string_view("TAG\0tail",8)),scalar(1,3)})));
        check(nul.find_label(0,"TAG")->word == 3, "Original comparison stops at NUL");
        auto temporary = [] { return ReaderArchive::parse(view(archive(scalar(1,42)))).payload(0); }();
        check(Document::parse(temporary).node(0).word == 42, "View outlives original store/archive");
        Bytes prefixed(13); auto content = archive(scalar(1,2)); prefixed.insert(prefixed.end(),content.begin(),content.end());
        auto shifted = ReaderArchive::parse(view(prefixed).subview(13,content.size()));
        check(shifted.directory_offset() == 21 && shifted.entries()[0].directory_offset == 21,
              "Nested view absolute provenance");
        check(Document::parse(shifted.payload(0)).node(0).source_offset == 13, "Payload absolute provenance");
        check(ReaderArchive::parse(view(archive({},{}))).entries().empty(), "Empty reader directory");
        check(Document::parse(view(list({}))).node(0).children.empty(), "Empty binary list");
        check(Document::parse(view(text(""))).string_bytes(0).empty(), "Empty binary string");
        rejects([&] { ar.payload(2); },"Invalid archive entry index");
        rejects([&] { temporary.subview(7,2); },"outside owned source");
        rejects([&] { ar.find_ascii(std::string_view("A\0B",3)); },"ASCII name");
        rejects([&] { doc.integer(0); },"not an integer");
        rejects([&] { doc.string_bytes(0); },"not a string");
        rejects([&] { doc.node(1000); },"Invalid document node index");
        rejects([&] { doc.index_of(nested.node(0)); },"not owned");
        rejects([&] { doc.find_label(0,std::string_view("A\0B",3)); },"must not contain NUL");
        auto terminal = Document::parse(view(list({text("LAST")})));
        rejects([&] { terminal.find_label(0,"LAST"); },"lacks an in-list successor");
        auto invalid = archive(scalar(1,1)); patch(invalid,invalid.size()-8,2);
        rejects([&] { ReaderArchive::parse(view(invalid)); },"Unsupported reader archive version");
        invalid = archive(scalar(1,1)); patch(invalid,invalid.size()-4,0xffffffff);
        rejects([&] { ReaderArchive::parse(view(invalid)); },"entry count exceeds limit");
        invalid = archive(scalar(1,1)); patch(invalid,invalid.size()-4,2);
        rejects([&] { ReaderArchive::parse(view(invalid)); },"Truncated reader archive directory");
        invalid = archive(scalar(1,1)); patch(invalid,8,9);
        rejects([&] { ReaderArchive::parse(view(invalid)); },"payload overlaps directory");
        invalid = archive(scalar(1,1)); patch(invalid,12,0xffffffff);
        rejects([&] { ReaderArchive::parse(view(invalid)); },"payload overlaps directory");
        invalid = archive(scalar(1,1)); std::fill(invalid.begin()+16,invalid.begin()+80,std::byte{'X'});
        rejects([&] { ReaderArchive::parse(view(invalid)); },"Unterminated reader archive name");
        rejects([&] { ReaderArchive::parse(view(Bytes(7))); },"Truncated reader archive footer");
        rejects([&] { Document::parse(view(scalar(5,0))); },"Unknown binary token type");
        rejects([&] { Document::parse(view(Bytes(7))); },"Unknown binary token type");
        invalid = scalar(1,0); invalid.pop_back();
        rejects([&] { Document::parse(view(invalid)); },"Truncated binary word");
        rejects([&] { Document::parse(view(scalar(4,0))); },"Invalid binary list count");
        rejects([&] { Document::parse(view(scalar(4,0xffffffff))); },"Invalid binary list count");
        rejects([&] { Document::parse(view(scalar(4,3))); },"Truncated binary list children");
        rejects([&] { Document::parse(view(scalar(3,0x80000000))); },"string length exceeds limit");
        rejects([&] { Document::parse(view(scalar(3,1))); },"Truncated binary string");
        invalid = scalar(1,1); invalid.push_back(std::byte{0});
        rejects([&] { Document::parse(view(invalid)); },"Trailing bytes");
        auto limits = Limits{}; limits.max_nodes = 2;
        rejects([&] { Document::parse(view(binary),limits); },"list count exceeds node limit");
        limits.max_nodes = 0;
        rejects([&] { Document::parse(view(scalar(1,1)),limits); },"node limit exceeded");
        limits = Limits{}; limits.max_depth = 0;
        rejects([&] { Document::parse(view(list({scalar(1,2)})),limits); },"depth limit exceeded");
        limits.max_depth = 513;
        rejects([&] { Document::parse(view(binary),limits); },"Unsupported parser depth limit");
        limits = Limits{}; limits.max_string_bytes = 2;
        rejects([&] { Document::parse(view(text("abc")),limits); },"string length exceeds limit");
        limits = Limits{}; limits.max_source_bytes = 7;
        rejects([&] { view(scalar(1,1),limits); },"source exceeds byte limit");
        rejects([&] { Document::parse(temporary,limits); },"document exceeds byte limit");
        rejects([&] { ReaderArchive::parse(ar.source(),limits); },"Archive exceeds byte limit");
        auto nonascii = ReaderArchive::parse(view(archive(scalar(1,1),{std::string(1,char(0xe9))})));
        rejects([&] { nonascii.find_ascii("missing"); },"provider locale contract");
        std::cout << "Authored asset controls passed: " << controls << '\n';
    } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
