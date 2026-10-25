#include "../../../runtime/graphics/missile_exhaust.hpp"
#include <cstring>
#include <iostream>

namespace {
unsigned checks{};
void require(bool value) {
    ++checks;
    if (!value)
        throw std::runtime_error("Missile exhaust contract failed");
}
} // namespace
int main() {
    using namespace mw34::missiles;
    const auto atlas = texture();
    require(atlas.size() == 64 * 128);
    for (unsigned y = 0; y < 128; ++y) {
        require((atlas[y * 64] >> 24) == 0);
        require((atlas[y * 64 + 63] >> 24) == 0);
    }
    for (unsigned x = 0; x < 64; ++x)
        for (unsigned y : {0U, 63U, 64U, 127U})
            require((atlas[y * 64 + x] >> 24) == 0);
    const auto core = atlas[8 * 64 + 32], tip = atlas[57 * 64 + 32];
    require((core >> 24) > (tip >> 24));
    require((core >> 24) > 200); // Stronger additive flame core, with unchanged transparent edges.
    require(((core >> 8) & 255) > ((tip >> 8) & 255));
    const Matrix matrix{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 10};
    const Projection p{1, 100, 100, 320, 240, .1f};
    const auto vertices = flame(matrix, p, -.04, .06, 1.27, 1, 123);
    require(vertices.size() == 18);
    // Recover actual local geometry from projection: the nozzle stays fixed,
    // while the width and animated plume length are twice the previous effect.
    const auto local_z = [&](const Vertex &v) { return p[0] / v.rhw - matrix[11]; };
    const auto local_x = [&](const Vertex &v) { return (v.x - p[3]) / (p[1] * v.rhw); };
    require(std::abs(local_z(vertices[0]) - (-.04)) < 1e-5);
    require(std::abs(local_x(vertices[0]) - (-.264)) < 1e-5);
    const double previous_length = 1.27 * 2.15 * (1 + .075 * std::sin(89. + 123.));
    require(std::abs((local_z(vertices[2]) - local_z(vertices[0])) / previous_length - 2) < 1e-5);
    for (const auto &v : vertices) {
        require(std::isfinite(v.x) && std::isfinite(v.y) && v.z > 0 && v.z <= 10);
        require(v.z == v.rhw && v.color == 0xffffffffU);
    }
    // The flight nose is -Z. Thrust ends farther along +Z, behind the nozzle.
    require(vertices[2].z < vertices[0].z);
    require(vertices[0].v < .5f && vertices[2].v < .5f && vertices.back().v > .5f);
    require(std::memcmp(vertices.data(), flame(matrix, p, -.04, .06, 1.27, 1, 123).data(),
                        vertices.size() * sizeof(Vertex)) == 0);
    auto behind = matrix;
    behind[11] = -10;
    require(flame(behind, p, -.04, .06, 1.27, 1, 123).empty());
    auto crossing = matrix;
    crossing[11] = -.2;
    for (const auto &v : flame(crossing, p, -.04, .06, 1.27, 1, 123))
        require(v.z <= 10.0001f && v.z > 0 && std::isfinite(v.x));
    for (unsigned i = 0; i < 1000; ++i) {
        const auto frame = flame(matrix, p, -.04, .06, 1.27, i * .016, 123);
        require(frame.size() == 18);
        for (const auto &v : frame)
            require(std::isfinite(v.x) && std::isfinite(v.y) && v.z > 0);
    }
    std::cout << checks << " missile exhaust checks passed\n";
}
