// Project-authored Parallax Occlusion Mapping (POM) contract and math tests.
#include "parallax_materials.hpp"
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace mw34::materials;

namespace {

void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}

void write_u32(std::string &out, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i)
        out.push_back(static_cast<char>((value >> (i * 8)) & 0xffU));
}

void write_u64(std::string &out, std::uint64_t value) {
    write_u32(out, static_cast<std::uint32_t>(value));
    write_u32(out, static_cast<std::uint32_t>(value >> 32));
}

void write_f32(std::string &out, float value) {
    write_u32(out, std::bit_cast<std::uint32_t>(value));
}

void write_str(std::string &out, const std::string &value) {
    write_u32(out, static_cast<std::uint32_t>(value.size()));
    out.append(value);
}

PomUniformInput make_default_pom_uniform() {
    PomUniformInput u{};
    const std::uint32_t addr = surface_address_wrap | (surface_address_wrap << 4U);
    u.pom_params = {1.0f, 0.5f, 0.2f, 32.0f};
    u.pom_uv_transform = {1.0f, 1.0f, 0.0f, 0.0f};
    u.pom_atlas_rect = {0.0f, 0.0f, 1.0f, 1.0f};
    u.pom_fade = {static_cast<float>(addr), 78.0f, 120.0f, 0.0f};
    u.pom_eye = {-4.0f, 0.0f, 8.0f, 1.0f};
    return u;
}

void test_signed_height_geometry() {
    auto u = make_default_pom_uniform();
    u.pom_eye = {-3.f, 0.f, 6.f, 1.f};
    // A flat layer intersects the eye ray at P + V * height / dot(N,V).
    // dP/du = (10,0,0); these values come from geometry, not the marcher.
    for (float amplitude : {0.5f, -0.5f}) {
        u.pom_params = {1.f, 0.f, amplitude, 32.f};
        std::vector<float> sampled_u;
        const auto result = evaluate_pom(
            {0.5f, 0.5f}, {0.f, 0.f, 0.f}, {0.f, 0.f, 1.f},
            {0.01f, 0.f, 0.f}, {0.f, 0.01f, 0.f}, {0.001f, 0.f},
            {0.f, 0.001f}, u, 256U, 256U, [&](PomVec2 uv) {
                sampled_u.push_back(uv.x);
                return 0.75f;
            });
        const float expected_u = 0.5f + (-3.f / 6.f) * amplitude * 0.75f / 10.f;
        require(result.applied && std::abs(result.uv.x - expected_u) < 1e-6f,
                "Signed relief does not intersect the physical eye ray");
        const float first_u = amplitude > 0.f ? 0.475f : 0.5f;
        require(!sampled_u.empty() && std::abs(sampled_u.front() - first_u) < 1e-6f,
                "Relief marching did not start at the physically nearest layer");
    }
}

void test_zero_amplitude_equivalence() {
    auto u = make_default_pom_uniform();
    u.pom_params[2] = 0.0f; // zero height_amplitude
    u.pom_uv_transform = {2.0f, 3.0f, 0.2f, 0.1f};
    u.pom_atlas_rect = {0.25f, 0.25f, 0.5f, 0.5f};
    const PomVec2 base_uv{0.375f, 0.625f};
    const PomVec3 world_pos{0.0f, 0.0f, 0.0f};
    const PomVec3 N{0.0f, 0.0f, 1.0f};
    const PomVec3 dp1{0.01f, 0.0f, 0.0f};
    const PomVec3 dp2{0.0f, 0.01f, 0.0f};
    const PomVec2 duv1{0.001f, 0.0f};
    const PomVec2 duv2{0.0f, 0.001f};

    const auto res = evaluate_pom(base_uv, world_pos, N, dp1, dp2, duv1, duv2, u, 256U, 256U,
                                  [](PomVec2) { return 0.75f; });
    require(!res.applied, "Zero height_amplitude should not mark POM displacement active");
    const float max_abs_uv_delta =
        std::max(std::abs(res.uv.x - base_uv.x), std::abs(res.uv.y - base_uv.y));
    require(max_abs_uv_delta == 0.0f,
            "Zero height_amplitude did not preserve exact base UV coordinates");
}

void test_analytic_ramp_intersection() {
    // Planar quad in XY plane (Z=0, N=(0,0,1)), dP/du = (10,0,0), dP/dv = (0,10,0).
    // Height field h(u, v) = u (linear ramp in [0, 1]), reference = 0.0, amplitude = 0.5 world units.
    // At base_uv = (0.5, 0.5), world_pos = (0, 0, 0), eye = (-3, 0, 6) -> V = normalize(-1, 0, 2).
    // The eye ray at normalized height h has u = 0.5 - 0.025*h.
    // Solving h=u gives u=0.5/1.025, toward the eye for positive relief.
    auto u = make_default_pom_uniform();
    u.pom_params = {1.0f, 0.0f, 0.5f, 32.0f};
    const std::uint32_t addr = surface_address_clamp | (surface_address_clamp << 4U);
    u.pom_fade[0] = static_cast<float>(addr);
    u.pom_eye = {-3.0f, 0.0f, 6.0f, 1.0f};

    const PomVec2 base_uv{0.5f, 0.5f};
    const PomVec3 world_pos{0.0f, 0.0f, 0.0f};
    const PomVec3 N{0.0f, 0.0f, 1.0f};
    const PomVec3 dp1{0.01f, 0.0f, 0.0f};
    const PomVec3 dp2{0.0f, 0.01f, 0.0f};
    const PomVec2 duv1{0.001f, 0.0f};
    const PomVec2 duv2{0.0f, 0.001f};

    const auto res = evaluate_pom(base_uv, world_pos, N, dp1, dp2, duv1, duv2, u, 1024U, 1024U,
                                  [](PomVec2 sample_uv) { return sample_uv.x; });
    require(res.applied, "Analytic ramp POM evaluation was not applied");
    const float expected_u = 0.5f / 1.025f;
    const float uv_err = std::max(std::abs(res.uv.x - expected_u), std::abs(res.uv.y - 0.5f));
    require(uv_err <= 1.5e-3f, "Analytic ramp POM intersection exceeded 1.5e-3 UV tolerance");
}

void test_mirrored_uv_parity_and_degenerate_guards() {
    auto u = make_default_pom_uniform();
    u.pom_params = {1.0f, 0.0f, 0.5f, 32.0f};
    const std::uint32_t addr = surface_address_clamp | (surface_address_clamp << 4U);
    u.pom_fade[0] = static_cast<float>(addr);
    u.pom_eye = {-3.0f, -2.0f, 6.0f, 1.0f};

    const PomVec2 base_uv{0.5f, 0.5f};
    const PomVec3 world_pos{0.0f, 0.0f, 0.0f};
    const PomVec3 N{0.0f, 0.0f, 1.0f};
    const PomVec3 dp1{0.01f, 0.0f, 0.0f};
    const PomVec3 dp2{0.0f, 0.01f, 0.0f};

    // Unmirrored: u increases along +X, v increases along +Y.
    const auto unmirrored = evaluate_pom(
        base_uv, world_pos, N, dp1, dp2, {0.001f, 0.0f}, {0.0f, 0.001f}, u, 512U, 512U,
        [](PomVec2) { return 0.25f; });
    // Mirrored U: u decreases along +X (duv1.x = -0.001f), v increases along +Y.
    const auto mirrored = evaluate_pom(
        base_uv, world_pos, N, dp1, dp2, {-0.001f, 0.0f}, {0.0f, 0.001f}, u, 512U, 512U,
        [](PomVec2) { return 0.25f; });

    require(unmirrored.applied && mirrored.applied, "Mirrored or unmirrored POM failed to apply");
    const float du_unmirrored = unmirrored.uv.x - base_uv.x;
    const float du_mirrored = mirrored.uv.x - base_uv.x;
    const float dv_unmirrored = unmirrored.uv.y - base_uv.y;
    const float dv_mirrored = mirrored.uv.y - base_uv.y;
    require(std::abs(du_unmirrored + du_mirrored) <= 1e-6f,
            "Mirrored U handedness did not invert U displacement parity");
    require(std::abs(dv_unmirrored - dv_mirrored) <= 1e-6f,
            "Mirrored U handedness unexpectedly altered V displacement");

    const auto reversed_screen = evaluate_pom(
        base_uv, world_pos, N, dp1, {-dp2.x, -dp2.y, -dp2.z}, {0.001f, 0.0f},
        {0.0f, -0.001f}, u, 512U, 512U, [](PomVec2) { return 0.25f; });
    require(reversed_screen.applied &&
                std::abs(reversed_screen.uv.x - unmirrored.uv.x) < 1e-6f &&
                std::abs(reversed_screen.uv.y - unmirrored.uv.y) < 1e-6f,
            "Equivalent reversed screen derivatives changed the UV displacement");

    // Degenerate zero-area UV triangle must bypass ray marching cleanly without NaN/Inf.
    u.pom_fade[3] = 1.0f; // enable debug mode
    const auto degen = evaluate_pom(base_uv, world_pos, N, dp1, dp2, {0.0f, 0.0f}, {0.0f, 0.0f}, u,
                                    512U, 512U, [](PomVec2) { return 0.5f; });
    require(std::isfinite(degen.uv.x) && std::isfinite(degen.uv.y),
            "Degenerate UV produced non-finite coordinates");
    require(degen.uv.x == base_uv.x && degen.uv.y == base_uv.y,
            "Degenerate UV did not preserve base UV");
    require(degen.applied && degen.debug_color.x > 0.9f && degen.debug_color.y < 0.3f,
            "Degenerate UV debug mode did not report orange/red fallback indicator");

    // Grazing angle (ndotv <= 0.08) must bypass ray marching cleanly.
    u.pom_eye = {-100.0f, 0.0f, 1.0f, 1.0f};
    const auto grazing = evaluate_pom(
        base_uv, world_pos, N, dp1, dp2, {0.001f, 0.0f}, {0.0f, 0.001f}, u, 512U, 512U,
        [](PomVec2) { return 0.5f; });
    require(grazing.uv.x == base_uv.x && grazing.uv.y == base_uv.y,
            "Grazing angle did not preserve base UV");
    require(grazing.applied && grazing.debug_color.z > 0.9f,
            "Grazing angle debug mode did not report blue fallback indicator");
}

void test_skewed_uv_chart() {
    auto u = make_default_pom_uniform();
    u.pom_params = {1.0f, 0.0f, 0.5f, 32.0f};
    u.pom_fade[0] = static_cast<float>(surface_address_clamp |
                                       (surface_address_clamp << 4U));
    u.pom_eye = {-3.0f, 0.0f, 6.0f, 1.0f};
    // dP/du=(10,0,0), dP/dv=(5,10,0): the X-directed ray has no V component.
    const auto result = evaluate_pom(
        {0.5f, 0.5f}, {0.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.0f},
        {0.01f, 0.0f, 0.0f}, {0.005f, 0.01f, 0.0f}, {0.001f, 0.0f},
        {0.0f, 0.001f}, u, 1024U, 1024U,
        [](PomVec2 sample_uv) { return sample_uv.x; });
    require(result.applied && std::abs(result.uv.x - 0.5f / 1.025f) < 1.5e-3f &&
                std::abs(result.uv.y - 0.5f) < 1e-6f,
            "Skewed UV chart sheared the ray across V");
}

void test_atlas_footprint() {
    auto u = make_default_pom_uniform();
    u.pom_params = {1.0f, 0.0f, 0.5f, 32.0f};
    u.pom_atlas_rect = {0.25f, 0.25f, 0.375f, 0.375f};
    u.pom_eye = {-3.0f, 0.0f, 6.0f, 1.0f};
    const auto result = evaluate_pom(
        {0.5f, 0.5f}, {0.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.0f},
        {0.1f, 0.0f, 0.0f}, {0.0f, 0.01f, 0.0f}, {0.01f, 0.0f},
        {0.0f, 0.001f}, u, 1024U, 1024U,
        [](PomVec2) { return 0.25f; });
    require(result.applied && result.uv.x < 0.5f,
            "Atlas tile span was omitted from height-map footprint fade");
}

void test_atlas_rect_containment() {
    auto u = make_default_pom_uniform();
    u.pom_params = {1.0f, 0.5f, 1.5f, 32.0f};
    u.pom_atlas_rect = {0.25f, 0.25f, 0.5f, 0.5f};
    const std::uint32_t addr = surface_address_wrap | (surface_address_wrap << 4U);
    u.pom_fade[0] = static_cast<float>(addr);
    u.pom_eye = {-8.0f, -8.0f, 2.0f, 1.0f};

    const PomVec3 world_pos{0.0f, 0.0f, 0.0f};
    const PomVec3 N{0.0f, 0.0f, 1.0f};
    const PomVec3 dp1{0.01f, 0.0f, 0.0f};
    const PomVec3 dp2{0.0f, 0.01f, 0.0f};
    const PomVec2 duv1{0.001f, 0.0f};
    const PomVec2 duv2{0.0f, 0.001f};

    constexpr std::uint32_t tex_dim = 128U;
    const float half_texel = 0.5f / static_cast<float>(tex_dim);
    const float min_allowed = 0.25f + half_texel;
    const float max_allowed = 0.5f - half_texel;

    for (int i = 0; i <= 16; ++i) {
        const float f = static_cast<float>(i) / 16.0f;
        const auto res = evaluate_pom({f, 1.0f - f}, world_pos, N, dp1, dp2, duv1, duv2, u, tex_dim,
                                      tex_dim, [&](PomVec2 sample_uv) {
                                          require(sample_uv.x >= min_allowed - 1e-6f &&
                                                      sample_uv.x <= max_allowed + 1e-6f &&
                                                      sample_uv.y >= min_allowed - 1e-6f &&
                                                      sample_uv.y <= max_allowed + 1e-6f,
                                                  "POM ray march sampled outside atlas_rect inset");
                                          return 0.3f;
                                      });
        require(res.applied, "Atlas-clamped POM evaluation was not applied");
        require(std::abs(res.uv.x - f) <= 0.125f &&
                    std::abs(res.uv.y - (1.0f - f)) <= 0.125f,
                "Final displaced UV must remain in raw draw UV coordinates");
    }
}

void test_environment_surface_materials_loader() {
    const std::array<unsigned char, 16> h_pixels{
        16, 0, 0, 255, 64, 0, 0, 255, 128, 0, 0, 255, 255, 0, 0, 255,
    };
    std::string raw("BWSFM1\0\0", 8);
    write_u32(raw, 1U);   // version
    write_u32(raw, 1U);   // batch_count
    write_u32(raw, 1U);   // record_count
    write_u32(raw, 1U);   // image_count
    write_u64(raw, 42ULL); // mesh_uv_hash (environment sidecars do not require mech batch-hash match)
    write_u32(raw, 0U);   // binding 0 -> record 0

    write_str(raw, "region-1");
    write_str(raw, "ground_sand");
    write_u32(raw, 0U);
    write_u32(raw, no_surface_image);
    write_f32(raw, 0.5f);
    write_f32(raw, 0.15f);
    write_f32(raw, 0.25f);
    write_u32(raw, 2U);
    write_f32(raw, 1.0f);
    write_f32(raw, 1.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_u32(raw, surface_address_wrap);
    write_u32(raw, surface_address_wrap);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 1.0f);
    write_f32(raw, 1.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.0f);
    write_f32(raw, 0.7f);
    write_f32(raw, 0.04f);
    write_f32(raw, 0.0f);

    write_str(raw, "ground_sand_h");
    write_u32(raw, surface_role_height);
    write_u32(raw, 2U);
    write_u32(raw, 2U);
    write_u64(raw, normal_hash(h_pixels.data(), h_pixels.size()));
    raw.append(reinterpret_cast<const char *>(h_pixels.data()), h_pixels.size());

    {
        std::istringstream stream(raw);
        const auto pack = read_environment_surface_materials(stream, "region-1");
        require(pack.records.size() == 1U && pack.images.size() == 1U,
                "Environment BWSFM1 record/image count mismatch");
        require(pack.records[0]->material_name == "ground_sand" &&
                    pack.records[0]->height_amplitude == 0.15f,
                "Environment BWSFM1 record fields mismatch");
        const float sampled = sample_height_bilinear(pack.images[0], {0.75f, 0.75f});
        require(sampled > 0.8f && sampled <= 1.0f, "Bilinear height sample out of expected range");
    }

    // A valid but unbound record must not become the primary ground material.
    auto unbound = raw;
    unbound[12] = '\x02'; // two batch bindings
    unbound.replace(32, 4, 4, '\xff');
    unbound.insert(36, 4, '\0'); // second batch binds the only record
    {
        std::istringstream stream(unbound);
        const auto pack = read_environment_surface_materials(stream, "region-1");
        require(pack.records.size() == 1U && pack.bindings[0] == no_surface_material &&
                    pack.bindings[1] == 0U,
                "Explicitly absent primary ground binding was not preserved");
    }

    // Mismatched expected_asset_id must still fail.
    bool threw = false;
    try {
        std::istringstream stream(raw);
        (void)read_environment_surface_materials(stream, "region-2");
    } catch (const std::runtime_error &) {
        threw = true;
    }
    require(threw, "Environment BWSFM1 loader accepted mismatched asset_id");
}

} // namespace

int main() {
    try {
        test_signed_height_geometry();
        test_zero_amplitude_equivalence();
        test_analytic_ramp_intersection();
        test_mirrored_uv_parity_and_degenerate_guards();
        test_skewed_uv_chart();
        test_atlas_footprint();
        test_atlas_rect_containment();
        test_environment_surface_materials_loader();
        std::cout << "Parallax materials: raw UV identity, analytic/skewed ramps, mirrored and "
                     "reversed derivatives, atlas footprint/containment, and BWSFM1 checks pass\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
