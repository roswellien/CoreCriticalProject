#pragma once
#include "material_normals.hpp"
#include <array>
#include <atomic>
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <istream>
#include <limits>
#include <memory>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::materials {

inline constexpr std::uint32_t no_surface_material = 0xffffffffU;
inline constexpr std::uint32_t no_surface_image = 0xffffffffU;

inline constexpr std::uint32_t surface_role_height = 1U;
inline constexpr std::uint32_t surface_role_thickness = 2U;

inline constexpr std::uint32_t surface_address_wrap = 1U;
inline constexpr std::uint32_t surface_address_mirror = 2U;
inline constexpr std::uint32_t surface_address_clamp = 3U;

inline constexpr std::size_t max_surface_batches = 4096U;
inline constexpr std::size_t max_surface_records = 4096U;
inline constexpr std::size_t max_surface_images = 2048U;
inline constexpr std::size_t max_surface_identifier_bytes = 4096U;
inline constexpr std::size_t max_surface_material_name_bytes = 31U;
inline constexpr std::uint32_t max_surface_dimension = 4096U;
inline constexpr std::uint64_t max_surface_sidecar_bytes = 512ULL * 1024ULL * 1024ULL;
inline constexpr float max_surface_world_amplitude = 16.0f;
inline constexpr float max_surface_uv_transform = 1024.0f;

class SurfaceDecodedReservation;
// Shared by source selection, prepared models and their queued immutable image
// owners. Replacing a selection cannot forget pixels still owned by old draws.
class SurfaceDecodedBudget {
  public:
    explicit SurfaceDecodedBudget(std::uint64_t limit = max_surface_sidecar_bytes) : limit_(limit) {
        if (limit > max_surface_sidecar_bytes)
            throw std::runtime_error("Surface decoded budget exceeds its format limit");
    }
    std::uint64_t used() const { return used_.load(std::memory_order_acquire); }
    std::uint64_t limit() const { return limit_; }
    std::uint64_t peak() const { return peak_.load(std::memory_order_acquire); }

  private:
    friend class SurfaceDecodedReservation;
    bool try_acquire(std::uint64_t bytes) {
        auto current = used_.load(std::memory_order_acquire);
        do {
            if (bytes > limit_ || current > limit_ - bytes)
                return false;
        } while (!used_.compare_exchange_weak(current, current + bytes,
                                              std::memory_order_acq_rel,
                                              std::memory_order_acquire));
        const auto admitted = current + bytes;
        auto peak = peak_.load(std::memory_order_relaxed);
        while (peak < admitted &&
               !peak_.compare_exchange_weak(peak, admitted, std::memory_order_release,
                                            std::memory_order_relaxed)) {
        }
        return true;
    }
    void release(std::uint64_t bytes) { used_.fetch_sub(bytes, std::memory_order_acq_rel); }
    const std::uint64_t limit_;
    std::atomic<std::uint64_t> used_{}, peak_{};
};
class SurfaceDecodedReservation {
  public:
    explicit SurfaceDecodedReservation(std::shared_ptr<SurfaceDecodedBudget> budget)
        : budget_(std::move(budget)) {
        if (!budget_)
            throw std::runtime_error("Surface decoded reservation has no budget owner");
    }
    SurfaceDecodedReservation(const SurfaceDecodedReservation &) = delete;
    SurfaceDecodedReservation &operator=(const SurfaceDecodedReservation &) = delete;
    ~SurfaceDecodedReservation() { budget_->release(bytes_); }
    void grow(std::uint64_t bytes) {
        if (!try_grow(bytes))
            throw std::runtime_error("Retained surface image owners exceed decoded budget");
    }
    bool try_grow(std::uint64_t bytes) {
        if (!budget_->try_acquire(bytes))
            return false;
        bytes_ += bytes;
        return true;
    }
    const std::shared_ptr<SurfaceDecodedBudget> &budget() const { return budget_; }

  private:
    std::shared_ptr<SurfaceDecodedBudget> budget_;
    std::uint64_t bytes_{};
};

// Owns decoded linear 8-bit scalar height or thickness pixels. Normal-map alpha
// is never modified or repurposed for these channels.
struct SurfaceMaterialImage {
    std::string name;
    std::uint32_t role{};
    std::uint32_t width{}, height{};
    std::uint64_t hash{};
    std::vector<std::uint8_t> pixels;
};

// Immutable validated surface-material parameters in native host world units.
// Shared from OverrideBatch into ModelInstance and Draw without changing the
// existing vertex or push-constant ABI until rendering stages are enabled.
struct SurfaceMaterialRecord {
    std::string asset_id;
    std::string material_name;
    std::uint32_t height_image{no_surface_image};
    std::uint32_t thickness_image{no_surface_image};
    float height_reference{0.0f};
    float height_amplitude{0.0f};
    float max_displacement{0.0f};
    std::uint32_t tessellation_cap{1U};
    std::array<float, 2> uv_scale{1.0f, 1.0f};
    std::array<float, 2> uv_offset{0.0f, 0.0f};
    std::uint32_t address_mode_u{surface_address_wrap};
    std::uint32_t address_mode_v{surface_address_wrap};
    std::array<float, 4> atlas_rect{0.0f, 0.0f, 1.0f, 1.0f};
    float sss_participation{0.0f};
    std::array<float, 3> sss_tint{0.0f, 0.0f, 0.0f};
    float sss_radius{0.0f};
    float thickness_scale{0.0f};
    float roughness{0.7f};
    float reflectivity{0.04f};
    float metallic{0.0f};
    // Resolved host-wide image table indices (-1 when absent).
    int host_height_texture{-1};
    int host_thickness_texture{-1};
    bool operator==(const SurfaceMaterialRecord &other) const {
        return std::tie(asset_id, material_name, height_image, thickness_image, height_reference,
                        height_amplitude, max_displacement, tessellation_cap, uv_scale, uv_offset,
                        address_mode_u, address_mode_v, atlas_rect, sss_participation, sss_tint,
                        sss_radius, thickness_scale, roughness, reflectivity, metallic,
                        host_height_texture, host_thickness_texture) ==
               std::tie(other.asset_id, other.material_name, other.height_image,
                        other.thickness_image, other.height_reference, other.height_amplitude,
                        other.max_displacement, other.tessellation_cap, other.uv_scale,
                        other.uv_offset, other.address_mode_u, other.address_mode_v,
                        other.atlas_rect, other.sss_participation, other.sss_tint, other.sss_radius,
                        other.thickness_scale, other.roughness, other.reflectivity, other.metallic,
                        other.host_height_texture, other.host_thickness_texture);
    }
};

struct SurfaceMaterialPack {
    SurfaceMaterialPack() = default;
    // Copying the pixel vectors would create unreserved decoded allocations.
    // Consumers share an immutable owner or move a freshly decoded pack.
    SurfaceMaterialPack(const SurfaceMaterialPack &) = delete;
    SurfaceMaterialPack &operator=(const SurfaceMaterialPack &) = delete;
    SurfaceMaterialPack(SurfaceMaterialPack &&) = default;
    SurfaceMaterialPack &operator=(SurfaceMaterialPack &&) = delete;
    std::uint32_t version{1U};
    std::uint64_t mesh_uv_hash{};
    // Declared before pixels so destruction frees images before returning the
    // reservation. Image aliases retain this complete pack through retirement.
    std::shared_ptr<SurfaceDecodedReservation> decoded_reservation;
    std::vector<std::uint32_t> bindings;
    std::vector<std::shared_ptr<SurfaceMaterialRecord>> records;
    std::vector<SurfaceMaterialImage> images;
};

// A draw owns the validated image through an aliasing immutable shared pointer.
// The image index in BWSFM1 is meaningful only inside its source pack; it must
// never be interpreted as a renderer-wide texture handle.
struct HeightWorldSource {
    std::string kind, member;
    std::uint64_t bytes{}, load_epoch{};
    std::uint32_t model_slot{};
    bool operator==(const HeightWorldSource &other) const {
        return std::tie(kind, member, bytes, load_epoch, model_slot) ==
               std::tie(other.kind, other.member, other.bytes, other.load_epoch, other.model_slot);
    }
};

struct HeightBinding {
    SurfaceMaterialRecord material;
    std::shared_ptr<const SurfaceMaterialImage> image;
    std::string source_sha256, sidecar_sha256;
    // Models without world provenance retain the existing absent snapshot.
    std::optional<HeightWorldSource> world_source;
    std::string sidecar_path;
    std::uint64_t mesh_uv_hash{}, image_version{}, producer_epoch{}, texture_version{};
    SurfaceKey albedo;
    std::uint32_t normal_width{}, normal_height{};
    std::uint64_t normal_hash{};
    std::uint64_t retained_decoded_bytes{};
    std::uint32_t source_batch{};
    bool streamed_image{};

    bool operator==(const HeightBinding &other) const {
        return material == other.material && image == other.image &&
               source_sha256 == other.source_sha256 && sidecar_sha256 == other.sidecar_sha256 &&
               world_source == other.world_source && sidecar_path == other.sidecar_path &&
               mesh_uv_hash == other.mesh_uv_hash &&
               image_version == other.image_version && producer_epoch == other.producer_epoch &&
               texture_version == other.texture_version && !(albedo < other.albedo) &&
               !(other.albedo < albedo) && normal_width == other.normal_width &&
               normal_height == other.normal_height && normal_hash == other.normal_hash &&
               source_batch == other.source_batch && streamed_image == other.streamed_image &&
               retained_decoded_bytes == other.retained_decoded_bytes;
    }
};

inline std::size_t height_binding_metadata_bytes(const HeightBinding &binding) {
    std::size_t bytes = sizeof(binding);
    const auto add = [&](std::size_t count) {
        if (count > std::numeric_limits<std::size_t>::max() - bytes)
            throw std::runtime_error("Height snapshot byte count overflow");
        bytes += count;
    };
    add(binding.source_sha256.capacity());
    add(binding.sidecar_sha256.capacity());
    add(binding.sidecar_path.capacity());
    add(binding.material.asset_id.capacity());
    add(binding.material.material_name.capacity());
    if (binding.world_source) {
        add(binding.world_source->kind.capacity());
        add(binding.world_source->member.capacity());
    }
    return bytes;
}

// Producer-only replay validation. Queued frames retain their immutable values
// and must not consult these mutable producer stamps on a worker thread.
inline bool height_binding_stamps_match(const HeightBinding &binding,
                                       std::uint64_t source_epoch,
                                       std::uint64_t group_epoch,
                                       std::uint64_t texture_version,
                                       const SurfaceKey &key) {
    return binding.world_source && binding.world_source->load_epoch == source_epoch &&
           binding.producer_epoch == group_epoch && binding.texture_version == texture_version &&
           binding.albedo == key;
}

inline bool same_height_binding(const std::shared_ptr<const HeightBinding> &left,
                                const std::shared_ptr<const HeightBinding> &right) {
    return left == right || (left && right && *left == *right);
}

// Unique image ownership is charged before a packet can be queued. A repeated
// material may share its immutable image; a replacement image is a new owner
// even when its non-cryptographic format hash happens to collide.
inline std::uint64_t height_binding_bytes(
    const std::vector<std::shared_ptr<const HeightBinding>> &bindings,
    std::uint64_t limit = max_surface_sidecar_bytes) {
    std::set<std::shared_ptr<const SurfaceMaterialImage>,
             std::owner_less<std::shared_ptr<const SurfaceMaterialImage>>> seen;
    std::uint64_t bytes{};
    for (const auto &binding : bindings) {
        if (!binding || !binding->image || !seen.insert(binding->image).second)
            continue;
        // Aliasing an image retains its complete immutable decoded pack. Charge
        // that allocation once, including unused height/thickness images.
        const auto size = binding->retained_decoded_bytes;
        if (size > limit || bytes > limit - size)
            throw std::runtime_error("Height image ownership exceeds decoded budget");
        bytes += size;
    }
    return bytes;
}

inline std::shared_ptr<const HeightBinding> resolve_height_binding(
    const std::shared_ptr<const SurfaceMaterialPack> &pack, std::size_t batch,
    const std::string &source_sha256, const std::string &sidecar_sha256, const SurfaceKey &albedo,
    std::uint32_t normal_width = 0, std::uint32_t normal_height = 0,
    std::uint64_t normal_hash = 0) {
    if (!pack || batch >= pack->bindings.size())
        return {};
    const auto index = pack->bindings[batch];
    if (index == no_surface_material)
        return {};
    const auto &record = *pack->records.at(index);
    if (record.height_image == no_surface_image)
        return {};
    const auto &image = pack->images.at(record.height_image);
    if (source_sha256.size() != 64 || source_sha256.find_first_not_of("0123456789abcdef") !=
                                              std::string::npos ||
        !pack->mesh_uv_hash || image.role != surface_role_height || !image.width ||
        !image.height || image.pixels.size() != std::uint64_t(image.width) * image.height ||
        sidecar_sha256.size() != 64 ||
        sidecar_sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
        normal_hash == 0 || !normal_width || !normal_height || !albedo.hash)
        throw std::runtime_error("Height binding requires complete source/image identity");
    auto binding = std::make_shared<HeightBinding>();
    binding->material = record;
    binding->image = std::shared_ptr<const SurfaceMaterialImage>(pack, &image);
    binding->source_sha256 = source_sha256;
    binding->sidecar_sha256 = sidecar_sha256;
    binding->mesh_uv_hash = pack->mesh_uv_hash;
    binding->image_version = pack->version;
    binding->albedo = albedo;
    binding->normal_width = normal_width;
    binding->normal_height = normal_height;
    binding->normal_hash = normal_hash;
    for (const auto &retained : pack->images)
        binding->retained_decoded_bytes += retained.pixels.size();
    binding->source_batch = std::uint32_t(batch);
    return binding;
}

inline std::shared_ptr<const HeightBinding> resolve_catalog_height_binding(
    const std::shared_ptr<const SurfaceMaterialPack> &pack, std::size_t record_index,
    const std::string &sidecar_sha256, const SurfaceKey &albedo, std::uint32_t normal_width,
    std::uint32_t normal_height, std::uint64_t normal_hash) {
    if (!pack || record_index >= pack->records.size())
        return {};
    const auto &record = *pack->records[record_index];
    if (record.height_image == no_surface_image || record.height_amplitude == 0.0f)
        return {};
    const auto &image = pack->images.at(record.height_image);
    if (sidecar_sha256.size() != 64 ||
        sidecar_sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
        image.role != surface_role_height || !image.width || !image.height ||
        image.pixels.size() != std::uint64_t(image.width) * image.height || normal_hash == 0 ||
        !normal_width || !normal_height || !albedo.hash || !albedo.width || !albedo.height ||
        albedo.format != 1U)
        throw std::runtime_error("Catalog height binding requires complete source/image identity");
    auto binding = std::make_shared<HeightBinding>();
    binding->material = record;
    binding->image = std::shared_ptr<const SurfaceMaterialImage>(pack, &image);
    binding->source_sha256 = sidecar_sha256;
    binding->sidecar_sha256 = sidecar_sha256;
    // Use the height image's own content hash so multiple albedos sharing the
    // same normal/height map share one GPU HeightImage allocation.
    binding->mesh_uv_hash = image.hash ? image.hash : albedo.hash;
    binding->image_version = pack->version;
    binding->albedo = albedo;
    binding->normal_width = normal_width;
    binding->normal_height = normal_height;
    binding->normal_hash = normal_hash;
    for (const auto &retained : pack->images)
        binding->retained_decoded_bytes += retained.pixels.size();
    binding->source_batch = std::uint32_t(record_index);
    return binding;
}

inline bool valid_surface_identifier(const std::string &value, std::size_t max_bytes,
                                     bool allow_colon) {
    if (value.empty() || value.size() > max_bytes || value.find("..") != std::string::npos)
        return false;
    for (char raw : value) {
        const auto c = static_cast<unsigned char>(raw);
        const bool alpha = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
        const bool digit = (c >= '0' && c <= '9');
        const bool symbol = c == '_' || c == '.' || c == '-' || (allow_colon && c == ':');
        if (!alpha && !digit && !symbol)
            return false;
    }
    return true;
}

// Compute the 64-bit FNV-1a geometry/UV compatibility hash over an in-memory
// sequence of batches, matching Python surface_materials.mesh_uv_identity().
template <typename BatchRange>
inline std::uint64_t compute_mesh_uv_hash(const BatchRange &batches, std::size_t first,
                                          std::size_t end) {
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    auto fold = [&](const void *data, std::size_t size) {
        const auto *bytes = static_cast<const unsigned char *>(data);
        for (std::size_t i = 0; i < size; ++i) {
            hash ^= bytes[i];
            hash *= 0x100000001b3ULL;
        }
    };
    const auto count = static_cast<std::uint32_t>(end - first);
    fold(&count, sizeof(count));
    for (std::size_t at = first; at < end; ++at) {
        const auto &vertices = batches[at].vertices;
        const auto vertex_count = static_cast<std::uint32_t>(vertices.size());
        fold(&vertex_count, sizeof(vertex_count));
        if (!vertices.empty())
            fold(vertices.data(), vertices.size() * sizeof(vertices[0]));
    }
    return hash;
}

inline SurfaceMaterialPack
read_surface_materials_impl(std::istream &input, const std::string &expected_asset_id,
                            std::uint64_t expected_mesh_uv_hash,
                            const std::vector<std::string> *expected_batch_materials,
                            std::uint64_t max_bytes, std::uint64_t max_decoded_bytes,
                            std::shared_ptr<SurfaceDecodedBudget> budget) {
    auto fail = [] { throw std::runtime_error("Invalid surface-material sidecar"); };
    if (!max_bytes || max_bytes > max_surface_sidecar_bytes ||
        max_decoded_bytes > max_surface_sidecar_bytes)
        fail();
    if (expected_batch_materials &&
        (expected_batch_materials->empty() ||
         expected_batch_materials->size() > max_surface_batches))
        fail();
    if (!expected_asset_id.empty() &&
        !valid_surface_identifier(expected_asset_id, max_surface_identifier_bytes, true))
        fail();
    if (expected_batch_materials) {
        for (const auto &mat_name : *expected_batch_materials) {
            if (!valid_surface_identifier(mat_name, max_surface_material_name_bytes, false))
                fail();
        }
    }

    std::uint64_t consumed_bytes = 0;
    auto bytes = [&](void *out, std::size_t count) {
        if (count > max_bytes - consumed_bytes)
            fail();
        if (!input.read(static_cast<char *>(out), static_cast<std::streamsize>(count)))
            fail();
        consumed_bytes += count;
    };
    auto u32 = [&] {
        unsigned char b[4];
        bytes(b, 4);
        return std::uint32_t(b[0]) | (std::uint32_t(b[1]) << 8) | (std::uint32_t(b[2]) << 16) |
               (std::uint32_t(b[3]) << 24);
    };
    auto u64 = [&] {
        const auto lo = u32();
        return std::uint64_t(lo) | (std::uint64_t(u32()) << 32);
    };
    auto f32 = [&](float low, float high) {
        const auto bits = u32();
        float value;
        std::memcpy(&value, &bits, sizeof value);
        if (!std::isfinite(value) || value < low || value > high)
            fail();
        return value;
    };
    auto text = [&](std::size_t max_len, bool allow_colon) {
        const auto len = u32();
        if (!len || len > max_len)
            fail();
        std::string value(len, '\0');
        bytes(value.data(), len);
        if (!valid_surface_identifier(value, max_len, allow_colon))
            fail();
        return value;
    };

    char magic[8];
    bytes(magic, 8);
    if (std::memcmp(magic, "BWSFM1\0\0", 8) != 0)
        fail();

    SurfaceMaterialPack pack;
    if (!budget)
        budget = std::make_shared<SurfaceDecodedBudget>(max_decoded_bytes);
    pack.decoded_reservation = std::make_shared<SurfaceDecodedReservation>(std::move(budget));
    pack.version = u32();
    const auto batch_count = u32();
    const auto record_count = u32();
    const auto image_count = u32();
    pack.mesh_uv_hash = u64();

    const bool batch_count_valid =
        expected_batch_materials ? (batch_count == expected_batch_materials->size())
                                 : (batch_count >= 1U && batch_count <= max_surface_batches);
    if ((pack.version != 1U && pack.version != 2U) || !batch_count_valid ||
        record_count > max_surface_records || image_count > max_surface_images ||
        pack.mesh_uv_hash != expected_mesh_uv_hash)
        fail();

    pack.bindings.reserve(batch_count);
    for (std::uint32_t i = 0; i < batch_count; ++i) {
        const auto index = u32();
        if (index != no_surface_material && index >= record_count)
            fail();
        pack.bindings.push_back(index);
    }

    pack.records.reserve(record_count);
    std::pair<std::string, std::string> previous_key;
    bool has_previous_key = false;
    for (std::uint32_t i = 0; i < record_count; ++i) {
        auto record_ptr = std::make_shared<SurfaceMaterialRecord>();
        auto &record = *record_ptr;
        record.asset_id = text(max_surface_identifier_bytes, true);
        if (!expected_asset_id.empty() && record.asset_id != expected_asset_id)
            fail();
        record.material_name = text(max_surface_material_name_bytes, false);

        const std::pair<std::string, std::string> key{record.asset_id, record.material_name};
        if (has_previous_key && key <= previous_key)
            fail();
        previous_key = key;
        has_previous_key = true;

        record.height_image = u32();
        record.thickness_image = u32();
        if (record.height_image != no_surface_image && record.height_image >= image_count)
            fail();
        if (record.thickness_image != no_surface_image && record.thickness_image >= image_count)
            fail();

        record.height_reference = f32(0.0f, 1.0f);
        record.height_amplitude = f32(-max_surface_world_amplitude, max_surface_world_amplitude);
        record.max_displacement = f32(0.0f, max_surface_world_amplitude);
        if (record.max_displacement < std::abs(record.height_amplitude))
            fail();
        if (record.height_image == no_surface_image &&
            (record.height_amplitude != 0.0f || record.max_displacement != 0.0f))
            fail();

        record.tessellation_cap = u32();
        if (record.tessellation_cap < 1U || record.tessellation_cap > 8U ||
            (record.height_image == no_surface_image && record.tessellation_cap != 1U))
            fail();

        record.uv_scale[0] = f32(-max_surface_uv_transform, max_surface_uv_transform);
        record.uv_scale[1] = f32(-max_surface_uv_transform, max_surface_uv_transform);
        if (std::abs(record.uv_scale[0]) < 1e-6f || std::abs(record.uv_scale[1]) < 1e-6f)
            fail();
        record.uv_offset[0] = f32(-max_surface_uv_transform, max_surface_uv_transform);
        record.uv_offset[1] = f32(-max_surface_uv_transform, max_surface_uv_transform);

        record.address_mode_u = u32();
        record.address_mode_v = u32();
        if (record.address_mode_u < surface_address_wrap ||
            record.address_mode_u > surface_address_clamp ||
            record.address_mode_v < surface_address_wrap ||
            record.address_mode_v > surface_address_clamp)
            fail();

        for (float &v : record.atlas_rect)
            v = f32(0.0f, 1.0f);
        if (!(record.atlas_rect[0] < record.atlas_rect[2] &&
              record.atlas_rect[1] < record.atlas_rect[3]))
            fail();

        record.sss_participation = f32(0.0f, 1.0f);
        for (float &v : record.sss_tint)
            v = f32(0.0f, 1.0f);
        record.sss_radius = f32(0.0f, max_surface_world_amplitude);
        record.thickness_scale = f32(0.0f, max_surface_world_amplitude);
        if (record.sss_participation == 0.0f &&
            (record.sss_radius != 0.0f || record.thickness_scale != 0.0f ||
             record.thickness_image != no_surface_image))
            fail();

        record.roughness = f32(0.0f, 1.0f);
        record.reflectivity = f32(0.0f, 1.0f);
        record.metallic = f32(0.0f, 1.0f);

        pack.records.push_back(std::move(record_ptr));
    }

    pack.images.reserve(image_count);
    std::string previous_image_name;
    bool has_previous_image = false;
    std::uint64_t decoded_image_bytes = 0;
    for (std::uint32_t i = 0; i < image_count; ++i) {
        SurfaceMaterialImage image;
        image.name = text(max_surface_identifier_bytes, true);
        if (has_previous_image && image.name <= previous_image_name)
            fail();
        previous_image_name = image.name;
        has_previous_image = true;

        image.role = u32();
        image.width = u32();
        image.height = u32();
        image.hash = u64();
        if ((image.role != surface_role_height && image.role != surface_role_thickness) ||
            !image.width || !image.height || image.width > max_surface_dimension ||
            image.height > max_surface_dimension)
            fail();

        const auto pixel_count = std::uint64_t(image.width) * image.height;
        const auto stored_pixel_bytes = pixel_count * (pack.version == 1U ? 4ULL : 1ULL);
        if (stored_pixel_bytes > max_bytes - consumed_bytes ||
            pixel_count > max_decoded_bytes - decoded_image_bytes)
            fail();
        decoded_image_bytes += pixel_count;

        pack.decoded_reservation->grow(pixel_count);
        if (pack.version == 1U) {
            std::vector<std::uint8_t> rgba(static_cast<std::size_t>(stored_pixel_bytes));
            bytes(rgba.data(), rgba.size());
            if (normal_hash(rgba.data(), rgba.size()) != image.hash)
                fail();
            image.pixels.resize(static_cast<std::size_t>(pixel_count));
            for (std::size_t pixel = 0; pixel < image.pixels.size(); ++pixel)
                image.pixels[pixel] = rgba[pixel * 4];
        } else {
            image.pixels.resize(static_cast<std::size_t>(pixel_count));
            bytes(image.pixels.data(), image.pixels.size());
            if (normal_hash(image.pixels.data(), image.pixels.size()) != image.hash)
                fail();
        }
        image.hash = normal_hash(image.pixels.data(), image.pixels.size());
        pack.images.push_back(std::move(image));
    }

    if (input.peek() != std::char_traits<char>::eof())
        fail();

    for (const auto &rec_ptr : pack.records) {
        const auto &record = *rec_ptr;
        if (record.height_image != no_surface_image &&
            pack.images[record.height_image].role != surface_role_height)
            fail();
        if (record.thickness_image != no_surface_image &&
            pack.images[record.thickness_image].role != surface_role_thickness)
            fail();
    }

    if (expected_batch_materials) {
        for (std::uint32_t i = 0; i < batch_count; ++i) {
            const auto rec_index = pack.bindings[i];
            if (rec_index == no_surface_material)
                continue;
            if (pack.records[rec_index]->material_name != (*expected_batch_materials)[i])
                fail();
        }
    }

    return pack;
}

inline SurfaceMaterialPack
read_surface_materials(std::istream &input, const std::string &expected_asset_id,
                       std::uint64_t expected_mesh_uv_hash,
                       const std::vector<std::string> &expected_batch_materials,
                       std::uint64_t max_bytes = max_surface_sidecar_bytes,
                       std::uint64_t max_decoded_bytes = max_surface_sidecar_bytes,
                       std::shared_ptr<SurfaceDecodedBudget> budget = {}) {
    return read_surface_materials_impl(input, expected_asset_id, expected_mesh_uv_hash,
                                       &expected_batch_materials, max_bytes, max_decoded_bytes,
                                       std::move(budget));
}

// Read a region-level BWSFM1 surface-material catalog (mesh_uv_hash == 0) whose
// records bind to authenticated environment surfaces by material_name.
inline SurfaceMaterialPack
read_surface_material_catalog(std::istream &input, const std::string &expected_asset_id,
                              std::uint64_t max_bytes = max_surface_sidecar_bytes,
                              std::uint64_t max_decoded_bytes = max_surface_sidecar_bytes,
                              std::shared_ptr<SurfaceDecodedBudget> budget = {}) {
    return read_surface_materials_impl(input, expected_asset_id, 0ULL, nullptr, max_bytes,
                                       max_decoded_bytes, std::move(budget));
}

} // namespace mw34::materials

namespace mw34::surface_materials {
using namespace mw34::materials;
} // namespace mw34::surface_materials
