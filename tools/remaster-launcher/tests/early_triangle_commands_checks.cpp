#include "../native-overrides/early_triangle_commands.hpp"
#include <memory>
#include <stdexcept>
#include <vector>
struct Command {
    enum Kind { Clear, Draw } kind{Draw};
    unsigned flags{6}, prim{}, texture{1}, fixture_node{}, fixture_polygon{}, hud_role{};
    int override_texture{-1}, override_normal_texture{-1};
    bool zoom_anchor_known{}, condition_schematic{};
    std::vector<unsigned> rects;
    std::vector<unsigned short> indices;
    std::vector<unsigned char> vertices;
    std::shared_ptr<const unsigned> model, sun_tl, sky_view, state_snapshot;
};
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value) throw std::runtime_error("Early triangle command contract failed");
}
int main() {
    using namespace mw34::submission;
    Command a;
    a.sun_tl = std::make_shared<unsigned>(1);
    a.state_snapshot = std::make_shared<unsigned>(2);
    for (unsigned i = 0; i < 96; ++i) a.vertices.push_back(static_cast<unsigned char>(i));
    Command b = a;
    for (auto &x : b.vertices) x ^= 0x55;
    auto expected = a.vertices;
    expected.insert(expected.end(), b.vertices.begin(), b.vertices.end());
    auto merged = a;
    require(merge_triangle_command(merged, b) && merged.flags == 4 && merged.vertices == expected);
    for (unsigned flags : {4U, 5U, 6U}) {
        auto next = b; next.flags = flags; auto previous = a;
        require(merge_triangle_command(previous, next) && previous.vertices == expected);
    }
    auto rejects = [&](auto mutate) {
        auto next = b; mutate(next); auto previous = a;
        require(!merge_triangle_command(previous, next) && previous.vertices == a.vertices);
    };
    rejects([](auto &c) { c.kind = Command::Clear; });
    rejects([](auto &c) { c.flags = 2; });
    rejects([](auto &c) { c.vertices.resize(128); });
    rejects([](auto &c) { c.flags = 5; c.vertices.resize(192); });
    rejects([](auto &c) { c.vertices.clear(); });
    rejects([](auto &c) { c.model = c.sun_tl; });
    rejects([](auto &c) { c.sun_tl.reset(); });
    rejects([](auto &c) { c.sun_tl = std::make_shared<unsigned>(1); });
    rejects([](auto &c) { c.sky_view = c.sun_tl; });
    rejects([](auto &c) { c.state_snapshot = std::make_shared<unsigned>(2); });
    rejects([](auto &c) { c.texture = 2; });
    rejects([](auto &c) { c.override_texture = 2; });
    rejects([](auto &c) { c.override_normal_texture = 2; });
    rejects([](auto &c) { c.hud_role = 1; });
    rejects([](auto &c) { c.zoom_anchor_known = true; });
    rejects([](auto &c) { c.condition_schematic = true; });
    rejects([](auto &c) { c.fixture_node = 1; });
    rejects([](auto &c) { c.fixture_polygon = 1; });
    rejects([](auto &c) { c.indices = {0, 1, 2}; });
    rejects([](auto &c) { c.rects = {1}; });
    rejects([](auto &c) { c.prim = 1; });
    rejects([](auto &c) { c.flags = 4; c.vertices.resize(96 * 12000); });
    std::vector<Command> queue;
    for (unsigned i = 0; i < 1000; ++i) append_triangle_command(queue, Command(a));
    require(queue.size() == 1 && queue[0].vertices.size() == 96000);
    for (unsigned i = 0; i < 1000; ++i)
        for (unsigned j = 0; j < 96; ++j) require(queue[0].vertices[96 * i + j] == a.vertices[j]);
    Command clear; clear.kind = Command::Clear; queue.push_back(clear);
    append_triangle_command(queue, Command(a));
    require(queue.size() == 3);
    std::printf("%u early triangle command checks passed\n", checks);
}
