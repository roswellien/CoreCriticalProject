// Authored material data exercises the production reader without game assets.
#include "../m4-crt-heap-carry/host/owned_emission.hpp"
#include <fstream>
#include <iostream>
#include <sstream>

namespace {
using namespace mw34::emission;
void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}
void integer(std::string &bytes, std::uint32_t value) {
    for (unsigned shift = 0; shift < 32; shift += 8)
        bytes.push_back(char(value >> shift));
}
void scalar(std::string &bytes, float value) {
    integer(bytes, std::bit_cast<std::uint32_t>(value));
}
void name(std::string &bytes, const std::string &value) {
    bytes += value;
    bytes.append(32 - value.size(), '\0');
}
std::vector<Binding> bindings() {
    return {{"torso", "Glass", 16, 8, 12345, {-1, -1, -1}, {1, 1, 1}}};
}
std::string fixture() {
    std::string bytes("BWMEM1\0\0", 8);
    integer(bytes, 1);
    integer(bytes, 77);
    integer(bytes, 0);
    name(bytes, "eyes");
    integer(bytes, 0);
    name(bytes, "torso");
    name(bytes, "Glass");
    integer(bytes, 16);
    integer(bytes, 8);
    integer(bytes, 12345);
    integer(bytes, 0);
    scalar(bytes, .35f);
    integer(bytes, 1);
    integer(bytes, 2);
    for (float value : {0.f, .2f, .3f, .7f})
        scalar(bytes, value);
    for (const std::string id : {"left", "right"}) {
        name(bytes, id);
        for (float value : {id == "left" ? -.3f : .3f, 0.f, .2f, 1.f, .01f, .01f, 1.2f, .1f})
            scalar(bytes, value);
    }
    return bytes;
}
std::vector<Record> parse(const std::string &bytes, std::uint64_t hash = 77,
                          const std::vector<Binding> &expected = bindings()) {
    std::istringstream stream(bytes);
    return read(stream, hash, expected);
}
void rejected(const std::string &bytes, const std::vector<Binding> &expected = bindings()) {
    bool failed{};
    try {
        parse(bytes, 77, expected);
    } catch (const std::runtime_error &) {
        failed = true;
    }
    require(failed, "Corrupt emission descriptor was accepted");
}
void changed_word(const std::string &source, std::size_t offset, std::uint32_t value) {
    auto changed = source;
    std::string word;
    integer(word, value);
    changed.replace(offset, 4, word);
    rejected(changed);
}
} // namespace

int main(int argc, char **argv) {
    try {
        if (argc == 2) {
            std::ifstream stream(argv[1], std::ios::binary);
            const auto records = mw34::emission::read(stream, 77, bindings());
            require(records.size() == 1 && records[0].id == "eyes" &&
                        records[0].anchors.size() == 2,
                    "Cross-language descriptor differs");
            std::cout << records[0].id << " " << records[0].anchors[0].id << " "
                      << records[0].anchors[1].id << "\n";
            return 0;
        }
        const auto bytes = fixture();
        const auto records = parse(bytes);
        auto weighted = bindings();
        weighted[0].rigid = false;
        rejected(bytes, weighted);
        require(records.size() == 1 && records[0].batch == 0 && records[0].strength == .35f &&
                    records[0].regions[0][2] == .3f && records[0].anchors.size() == 2 &&
                    records[0].anchors[1].id == "right" && records[0].anchors[1].position[0] == .3f,
                "Emission fixture fields changed");
        for (std::size_t length : {0U, 19U, 20U, 147U, 163U, 291U})
            rejected(bytes.substr(0, length));
        rejected(bytes + "x");
        rejected(std::string(1024 * 1024 + 1, 'x'));
        auto wrong = bytes;
        wrong[0] = 'X';
        rejected(wrong);
        wrong = bytes;
        wrong[25] = 'A';
        rejected(wrong);
        for (const auto &[offset, value] :
             std::vector<std::pair<std::size_t, std::uint32_t>>{{8, 65},
                                                                {12, 78},
                                                                {52, 1},
                                                                {120, 32},
                                                                {124, 16},
                                                                {128, 1},
                                                                {140, 0},
                                                                {140, 33},
                                                                {144, 9}})
            changed_word(bytes, offset, value);
        for (const auto &[offset, value] : std::vector<std::pair<std::size_t, float>>{{136, -1.f},
                                                                                      {136, 3.f},
                                                                                      {136, NAN},
                                                                                      {148, .5f},
                                                                                      {196, 6.f},
                                                                                      {208, -1.f},
                                                                                      {220, 5.f},
                                                                                      {224, -1.f}})
            changed_word(bytes, offset, std::bit_cast<std::uint32_t>(value));
        wrong = bytes;
        wrong.replace(228, 32, bytes.substr(164, 32));
        rejected(wrong);
        wrong = bytes;
        std::string zero;
        scalar(zero, 0);
        for (std::size_t offset : {136U, 224U, 288U})
            wrong.replace(offset, 4, zero);
        require(parse(wrong)[0].strength == 0, "Zero-emission control was rejected");
        std::cout << "Owned emission contract passed\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << "\n";
        return 1;
    }
}
