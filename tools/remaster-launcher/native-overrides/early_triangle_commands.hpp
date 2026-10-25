#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <utility>
#include <vector>

namespace mw34::submission {
// A merged/suppressed input no longer owns queued geometry. Keep its storage
// for the next complete guest-vertex copy; queued commands retain ownership.
class DrawVertexScratch {
    std::vector<unsigned char> spare;
    std::uint64_t reuses{}, growths{};

  public:
    void prepare(std::vector<unsigned char> &output, std::size_t bytes) {
        if (!output.empty() || output.capacity())
            throw std::logic_error("Draw vertex scratch requires a fresh input owner");
        if (bytes && spare.capacity() >= bytes)
            ++reuses;
        else if (bytes)
            ++growths;
        output.swap(spare);
        output.resize(bytes);
    }
    void recycle(std::vector<unsigned char> &input) {
        constexpr std::size_t limit = 4 * 1024 * 1024;
        if (input.capacity() <= limit && input.capacity() > spare.capacity())
            input.swap(spare);
    }
    ~DrawVertexScratch() {
        if (reuses || growths)
            std::fprintf(
                stderr,
                "Draw vertex scratch: %llu reused buffers, %llu growths, %zu retained bytes\n",
                (unsigned long long)reuses, (unsigned long long)growths, spare.capacity());
    }
};

// Called after all original per-call logging, capture, validation and suppression.
// Only lit, non-indexed world triangles with identical immutable bindings join.
// Scene boundaries, clears, models, HUD/zoom and unlit atmosphere routing remain
// barriers. The original per-vertex bytes and triangle order are copied exactly.
struct TriangleCommandCounters {
    std::uint64_t admitted{}, merged{};
    ~TriangleCommandCounters() {
        if (admitted)
            std::fprintf(stderr, "Early triangle commands: %llu admitted, %llu merged\n",
                         (unsigned long long)admitted, (unsigned long long)merged);
    }
};
inline TriangleCommandCounters &triangle_command_counters() {
    static TriangleCommandCounters counters;
    return counters;
}
template <class Command> bool ordinary_triangle_command(const Command &c) {
    if (c.kind != Command::Draw || c.model || !c.sun_tl || !c.state_snapshot || c.hud_role ||
        c.zoom_anchor_known || c.condition_schematic || c.fixture_node || c.fixture_polygon ||
        !c.indices.empty() || !c.rects.empty())
        return false;
    const auto bytes = c.vertices.size();
    // Direct3D triangle list=4, strip=5, fan=6. A three-vertex strip/fan is one
    // triangle with the same first vertex and winding as a triangle list.
    return bytes &&
           ((c.flags == 4 && bytes % 96 == 0) || ((c.flags == 5 || c.flags == 6) && bytes == 96));
}
template <class Command> bool merge_triangle_command(Command &previous, const Command &next) {
    constexpr std::size_t limit = 1024 * 1024;
    if (!ordinary_triangle_command(previous) || !ordinary_triangle_command(next) ||
        previous.state_snapshot != next.state_snapshot || previous.texture != next.texture ||
        previous.sun_tl != next.sun_tl || previous.sky_view != next.sky_view ||
        previous.override_texture != next.override_texture ||
        previous.override_normal_texture != next.override_normal_texture ||
        previous.prim != next.prim || next.vertices.size() > limit ||
        previous.vertices.size() > limit - next.vertices.size())
        return false;
    previous.vertices.insert(previous.vertices.end(), next.vertices.begin(), next.vertices.end());
    previous.flags = 4;
    return true;
}
template <class Commands, class Command>
void append_triangle_command(Commands &commands, Command &&next) {
    auto &counters = triangle_command_counters();
    ++counters.admitted;
    if (!commands.empty() && merge_triangle_command(commands.back(), next)) {
        ++counters.merged;
        return;
    }
    commands.push_back(std::forward<Command>(next));
}
} // namespace mw34::submission
