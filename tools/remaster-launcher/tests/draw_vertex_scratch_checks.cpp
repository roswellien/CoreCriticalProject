#include "../native-overrides/early_triangle_commands.hpp"
#include <cstring>

using mw34::submission::DrawVertexScratch;
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("Draw vertex storage ownership failed");
}
int main() {
    DrawVertexScratch scratch;
    std::vector<std::vector<unsigned char>> queued, expected;
    for (unsigned frame = 0; frame < 4000; ++frame) {
        const std::size_t count = frame % 19 == 0 ? 0 : frame % 17 == 0 ? 4096 : 96;
        std::vector<unsigned char> input, source(count);
        for (std::size_t i = 0; i < count; ++i)
            source[i] = static_cast<unsigned char>(frame * 31 + i * 97);
        scratch.prepare(input, count);
        if (count)
            std::memcpy(input.data(), source.data(), count);
        require(input == source);
        if (frame % 13 == 0) {
            queued.push_back(std::move(input));
            expected.push_back(source);
        }
        scratch.recycle(input);
        for (std::size_t i = 0; i < queued.size(); ++i)
            require(queued[i] == expected[i]);
        if (queued.size() == 31) {
            queued.clear();
            expected.clear();
        }
    }
    std::vector<unsigned char> outer;
    scratch.prepare(outer, 4096);
    outer.assign(4096, 17);
    std::vector<unsigned char> inner;
    scratch.prepare(inner, 96);
    inner.assign(96, 93);
    scratch.recycle(inner);
    require(outer == std::vector<unsigned char>(4096, 17));
    scratch.recycle(outer);
    std::vector<unsigned char> next;
    scratch.prepare(next, 4096);
    require(next.size() == 4096);
    bool threw = false;
    try {
        scratch.prepare(next, 96);
    } catch (const std::logic_error &) {
        threw = true;
    }
    require(threw);
    scratch.recycle(next);
    std::printf("%u draw byte, queued-owner, nested-capture and reuse checks passed\n", checks);
}
