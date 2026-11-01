// Project-authored surface-material contract tests; no original assets required.
#include "surface_materials.hpp"
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace mw34::materials;

namespace {

struct VertexFixture {
    float x{}, y{}, z{};
    float nx{}, ny{}, nz{};
    float u{}, v{};
};

struct BatchFixture {
    std::vector<VertexFixture> vertices;
};

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

void write_f32(std::string &out, float value) { write_u32(out, std::bit_cast<std::uint32_t>(value)); }

void write_str(std::string &out, const std::string &value) {
    write_u32(out, static_cast<std::uint32_t>(value.size()));
    out.append(value);
}

std::vector<BatchFixture> make_batches() {
    std::vector<BatchFixture> batches(2);
    for (std::size_t b = 0; b < 2; ++b) {
        const float u_step = b == 0 ? 0.25f : 0.75f;
        for (int idx = 0; idx < 3; ++idx) {
            batches[b].vertices.push_back(VertexFixture{
                float(idx),
                float(idx + 1),
                float(idx + 2),
                0.0f,
                0.0f,
                1.0f,
                u_step * float(idx),
                0.5f * float(idx),
            });
        }
    }
    return batches;
}

std::string build_oracle_sidecar(std::uint64_t mesh_hash) {
    const std::array<unsigned char, 16> h_pixels{
        32, 0, 0, 255, 96, 0, 0, 255, 160, 0, 0, 255, 224, 0, 0, 255,
    };
    const std::array<unsigned char, 16> t_pixels{
        64, 0, 0, 255, 128, 0, 0, 255, 192, 0, 0, 255, 240, 0, 0, 255,
    };

    std::string out("BWSFM1\0\0", 8);
    write_u32(out, 1U);        // version
    write_u32(out, 2U);        // batch_count
    write_u32(out, 2U);        // record_count
    write_u32(out, 2U);        // image_count
    write_u64(out, mesh_hash); // mesh_uv_hash

    // Batch bindings: batch 0 ("canopy_glass") -> record 1, batch 1 ("armor_hull") -> record 0.
    write_u32(out, 1U);
    write_u32(out, 0U);

    // Record 0: ("bushwacker:close", "armor_hull")
    write_str(out, "bushwacker:close");
    write_str(out, "armor_hull");
    write_u32(out, 0U);               // height_image
    write_u32(out, no_surface_image); // thickness_image
    write_f32(out, 0.5f);             // height_reference
    write_f32(out, 0.25f);            // height_amplitude
    write_f32(out, 0.5f);             // max_displacement
    write_u32(out, 4U);               // tessellation_cap
    write_f32(out, 2.0f);             // uv_scale[0]
    write_f32(out, -2.0f);            // uv_scale[1]
    write_f32(out, 0.125f);           // uv_offset[0]
    write_f32(out, -0.25f);           // uv_offset[1]
    write_u32(out, surface_address_mirror);
    write_u32(out, surface_address_clamp);
    write_f32(out, 0.125f);
    write_f32(out, 0.25f);
    write_f32(out, 0.875f);
    write_f32(out, 0.75f);
    write_f32(out, 0.0f); // sss_participation
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f); // sss_radius
    write_f32(out, 0.0f); // thickness_scale

    // Record 1: ("bushwacker:close", "canopy_glass")
    write_str(out, "bushwacker:close");
    write_str(out, "canopy_glass");
    write_u32(out, no_surface_image);
    write_u32(out, 1U); // thickness_image
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_u32(out, 1U);
    write_f32(out, 1.0f);
    write_f32(out, 1.0f);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_u32(out, surface_address_wrap);
    write_u32(out, surface_address_wrap);
    write_f32(out, 0.0f);
    write_f32(out, 0.0f);
    write_f32(out, 1.0f);
    write_f32(out, 1.0f);
    write_f32(out, 0.5f); // sss_participation
    write_f32(out, 0.25f);
    write_f32(out, 0.5f);
    write_f32(out, 0.75f);
    write_f32(out, 0.125f); // sss_radius
    write_f32(out, 0.375f); // thickness_scale

    // Image 0: height_armor
    write_str(out, "height_armor");
    write_u32(out, surface_role_height);
    write_u32(out, 2U);
    write_u32(out, 2U);
    write_u64(out, normal_hash(h_pixels.data(), h_pixels.size()));
    out.append(reinterpret_cast<const char *>(h_pixels.data()), h_pixels.size());

    // Image 1: thick_canopy
    write_str(out, "thick_canopy");
    write_u32(out, surface_role_thickness);
    write_u32(out, 2U);
    write_u32(out, 2U);
    write_u64(out, normal_hash(t_pixels.data(), t_pixels.size()));
    out.append(reinterpret_cast<const char *>(t_pixels.data()), t_pixels.size());

    return out;
}

bool rejected(const std::string &bytes, const std::string &asset_id, std::uint64_t mesh_hash,
              const std::vector<std::string> &materials,
              std::uint64_t max_bytes = max_surface_sidecar_bytes) {
    try {
        std::istringstream stream(bytes);
        read_surface_materials(stream, asset_id, mesh_hash, materials, max_bytes);
        return false;
    } catch (const std::runtime_error &) {
        return true;
    }
}

} // namespace

int main() {
    try {
        const auto batches = make_batches();
        const auto mesh_hash = compute_mesh_uv_hash(batches, 0, batches.size());
        // Must match Python surface_materials.mesh_uv_identity() on the same vertex stream.
        require(mesh_hash == 1335280070564434920ULL,
                "C++ and Python mesh_uv_hash disagreed on identical geometry/UV fixture");

        auto altered_batches = batches;
        altered_batches[1].vertices[2].v = 0.875f;
        require(compute_mesh_uv_hash(altered_batches, 0, altered_batches.size()) != mesh_hash,
                "Modified UV coordinate did not change compute_mesh_uv_hash");

        const std::vector<std::string> materials{"canopy_glass", "armor_hull"};
        const auto valid = build_oracle_sidecar(mesh_hash);
        {
            std::istringstream stream(valid);
            const auto pack =
                read_surface_materials(stream, "bushwacker:close", mesh_hash, materials);
            require(pack.version == 1U && pack.mesh_uv_hash == mesh_hash, "Header mismatch");
            require(pack.bindings.size() == 2 && pack.bindings[0] == 1U && pack.bindings[1] == 0U,
                    "Batch bindings mismatch");
            require(pack.records.size() == 2 && pack.images.size() == 2,
                    "Record or image count mismatch");

            const auto &armor = *pack.records[0];
            require(armor.asset_id == "bushwacker:close" && armor.material_name == "armor_hull",
                    "Record 0 identity mismatch");
            require(armor.height_image == 0U && armor.thickness_image == no_surface_image,
                    "Record 0 image indices mismatch");
            require(armor.height_reference == 0.5f && armor.height_amplitude == 0.25f &&
                        armor.max_displacement == 0.5f && armor.tessellation_cap == 4U,
                    "Record 0 height/displacement mismatch");
            require(armor.uv_scale[0] == 2.0f && armor.uv_scale[1] == -2.0f &&
                        armor.uv_offset[0] == 0.125f && armor.uv_offset[1] == -0.25f &&
                        armor.address_mode_u == surface_address_mirror &&
                        armor.address_mode_v == surface_address_clamp,
                    "Record 0 UV transform/addressing mismatch");
            require(armor.sss_participation == 0.0f && armor.sss_radius == 0.0f &&
                        armor.thickness_scale == 0.0f,
                    "Opaque armor record did not keep zero SSS participation");

            const auto &canopy = *pack.records[1];
            require(canopy.material_name == "canopy_glass" && canopy.thickness_image == 1U &&
                        canopy.sss_participation == 0.5f && canopy.sss_radius == 0.125f &&
                        canopy.thickness_scale == 0.375f,
                    "Record 1 SSS fields mismatch");

            require(pack.images[0].name == "height_armor" &&
                        pack.images[0].role == surface_role_height &&
                        (pack.images[0].pixels[0] & 0xffU) == 32U,
                    "Height image red channel was not preserved");
            require(pack.images[1].name == "thick_canopy" &&
                        pack.images[1].role == surface_role_thickness &&
                        (pack.images[1].pixels[0] & 0xffU) == 64U,
                    "Thickness image red channel was not preserved");
        }

        // Truncation at every byte offset must fail cleanly.
        for (std::size_t cutoff = 0; cutoff < valid.size(); ++cutoff) {
            require(rejected(valid.substr(0, cutoff), "bushwacker:close", mesh_hash, materials),
                    "Truncated surface-material sidecar was accepted");
        }

        // Trailing bytes rejected.
        require(rejected(valid + "x", "bushwacker:close", mesh_hash, materials),
                "Trailing byte was accepted");

        // Wrong magic or version rejected.
        auto bad = valid;
        bad[5] = '2';
        require(rejected(bad, "bushwacker:close", mesh_hash, materials),
                "Unsupported magic was accepted");
        bad = valid;
        bad[8] = 2;
        require(rejected(bad, "bushwacker:close", mesh_hash, materials),
                "Unsupported version was accepted");

        // Compatibility identity mismatches rejected.
        require(rejected(valid, "shadowcat:close", mesh_hash, materials),
                "Mismatched asset_id was accepted");
        require(rejected(valid, "bushwacker:close", mesh_hash ^ 1ULL, materials),
                "Mismatched mesh_uv_hash was accepted");
        require(rejected(valid, "bushwacker:close", mesh_hash, {"armor_hull", "canopy_glass"}),
                "Swapped batch material binding was accepted");
        require(rejected(valid, "bushwacker:close", mesh_hash, {"canopy_glass"}),
                "Mismatched batch count was accepted");

        // Budget enforcement rejected before reading full stream.
        require(rejected(valid, "bushwacker:close", mesh_hash, materials, valid.size() - 1),
                "Sidecar exceeding max_bytes budget was accepted");

        // Corrupted image pixel rejected by FNV-1a hash check.
        bad = valid;
        bad.back() = static_cast<char>(static_cast<unsigned char>(bad.back()) ^ 0xffU);
        require(rejected(bad, "bushwacker:close", mesh_hash, materials),
                "Corrupted image pixel was accepted");

        // Swapping image role (making image 0 a thickness map while referenced as height_image)
        // must be rejected.
        bad = valid;
        const auto img0_pos = bad.find("height_armor");
        require(img0_pos != std::string::npos, "Could not locate height_armor in oracle");
        bad[img0_pos + 12] = static_cast<char>(surface_role_thickness);
        require(rejected(bad, "bushwacker:close", mesh_hash, materials),
                "Mismatched height_image role was accepted");

        // Non-finite float in height_reference (offset: header 32 + bindings 8 + asset_id 20 +
        // material_name 14 + height_image 4 + thickness_image 4 = 82) must be rejected.
        bad = valid;
        const auto nan_bits = std::bit_cast<std::uint32_t>(std::numeric_limits<float>::quiet_NaN());
        for (unsigned i = 0; i < 4; ++i)
            bad[82 + i] = static_cast<char>((nan_bits >> (i * 8)) & 0xffU);
        require(rejected(bad, "bushwacker:close", mesh_hash, materials),
                "NaN float parameter was accepted");

        std::cout << "Surface materials: wire oracle, mesh/UV compatibility, bounds, and "
                     "corruption checks pass\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
