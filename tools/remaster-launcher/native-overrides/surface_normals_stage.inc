// Full-content material matching for original textured geometry on any map.
// Cache lifetime follows the same observed VSurface version as albedo uploads;
// dimensions, pixel format, pitch and backing address also guard handle reuse.
struct SurfaceNormalState {
    // This stage is included inside the owning host. Its render-thread state has
    // no internal locking; surface versions must advance when source pixels change.
    bool loaded{};
    std::map<mw34::materials::SurfaceKey, int> bindings;
    std::set<mw34::materials::SurfaceKey> authored;
    struct Page {
        std::filesystem::path path;
        std::set<mw34::materials::SurfaceKey> keys;
        bool loaded{};
    };
    std::vector<Page> pages;
    std::map<mw34::materials::SurfaceKey, size_t> world_bindings;
    std::uint64_t world_bytes{};
    struct Cached {
        std::uint64_t version{};
        unsigned width{}, height{}, pitch{}, memory{}, format{};
        int index{-1};
        bool registered{}, world{};
    };
    std::map<unsigned, Cached> cache;
} surface_normals;
#include "world_normals_pages.inc"
static bool surface_normals_enabled() {
    static const bool enabled = [] {
        const char *p = std::getenv("MW34_SURFACE_NORMALS"), *w = std::getenv("MW34_WORLD_NORMALS");
        return mw34::sun::settings().enabled && ((p && *p) || (w && *w));
    }();
    return enabled;
}
// Load configured authored catalogs first, then register lazy world-page keys.
// Authored exclusions are bindings too: registered=true with image index -1
// prevents automatic world relief from overriding an intentionally flat surface.
void surface_normals_load() {
    auto &normal_state = surface_normals;
    if (normal_state.loaded)
        return;
    const char *path = std::getenv("MW34_SURFACE_NORMALS");
    if (path && *path) {
        std::uint64_t authored_bytes{};
        for (const auto &catalog_path : mw34::materials::surface_normal_catalog_paths(path)) {
            std::ifstream file(catalog_path, std::ios::binary);
            if (!file)
                throw std::runtime_error("Configured surface normal page is missing");
            if (!mw34::materials::normal_maps_enabled()) {
                // Retain registration without decoding pixels when maps are disabled. Other
                // rendering decisions can still distinguish known surfaces from unknown ones.
                for (const auto &entry : mw34::materials::read_surface_normal_header(file)) {
                    if (!normal_state.authored.insert(entry.first).second)
                        throw std::runtime_error("Duplicate authored surface normal key");
                    normal_state.bindings.emplace(entry.first, -1);
                }
                if (override_state().log.is_open())
                    override_state().log << "{\"event\":\"surface_normals_loaded\",\"bindings\":"
                                         << normal_state.bindings.size() << ",\"images\":0}\n";
            } else {
                auto parsed = mw34::materials::read_surface_normals(file);
                for (const auto &image : parsed.pack.images)
                    authored_bytes += std::uint64_t(image.pixels.size()) * 4;
                if (authored_bytes > mw34::materials::authored_normal_budget)
                    throw std::runtime_error(
                        "Resident authored surface normals exceed byte budget");
                auto &overrides = override_state();
                const size_t texture_base_index = overrides.normal_textures.size();
                if (texture_base_index + parsed.pack.images.size() >
                    size_t(std::numeric_limits<int>::max()))
                    throw std::runtime_error("Surface normal image index overflow");
                for (const auto &[key, index] : parsed.bindings) {
                    if (!normal_state.authored.insert(key).second)
                        throw std::runtime_error("Duplicate authored surface normal key");
                    normal_state.bindings.emplace(key, index == mw34::materials::no_normal
                                                           ? -1
                                                           : int(texture_base_index + index));
                }
                for (auto &image : parsed.pack.images) {
                    OverrideTexture texture{};
                    texture.name = std::move(image.name);
                    texture.width = image.width;
                    texture.height = image.height;
                    texture.hash = image.hash;
                    texture.pixels32 = std::move(image.pixels);
                    overrides.normal_textures.push_back(std::move(texture));
                }
                if (overrides.log.is_open())
                    overrides.log << "{\"event\":\"surface_normals_loaded\",\"bindings\":"
                                  << normal_state.bindings.size()
                                  << ",\"images\":" << parsed.pack.images.size()
                                  << ",\"first_normal_index\":" << texture_base_index << "}\n";
            }
        }
    }
    surface_normals_load_world();
    normal_state.loaded = true;
}
std::pair<bool, int> surface_normal_binding(VSurfaceRec &surface) {
    // Return (registered, global normal-texture index). An absent normal image
    // does not mean that the surface identity was absent from the catalogs.
    if (!surface_normals_enabled())
        return {false, -1};
    surface_normals_load();
    const unsigned format = surface.tex_masks[0] == 0xf800   ? 1
                            : surface.tex_masks[0] == 0x7c00 ? 2
                            : surface.tex_masks[0] == 0x0f00 ? 3
                                                             : 0;
    if (surface.bpp != 16 || !format || !surface.width || !surface.height || surface.width > 4096 ||
        surface.height > 4096 || surface.pitch < surface.width * 2)
        return {false, -1};
    if (std::uint64_t(surface.mem) + std::uint64_t(surface.pitch) * (surface.height - 1) +
            std::uint64_t(surface.width) * 2 >
        0x100000000ULL)
        return {false, -1};
    auto &cache = surface_normals.cache;
    auto cached_surface = cache.find(surface.guest);
    if (cached_surface != cache.end()) {
        const auto &entry = cached_surface->second;
        if (entry.version == surface.version && entry.width == surface.width &&
            entry.height == surface.height && entry.pitch == surface.pitch &&
            entry.memory == surface.mem && entry.format == format)
            return {entry.registered, entry.index};
    }
    // Synchronize resident producers before inspecting the exact colour bytes.
    gpu_sync(surface.guest);
    // Hash only active 16-bit pixels, row by row. Pitch padding is deliberately
    // excluded so differently pitched copies of the same image share one key.
    std::vector<unsigned char> pixels(size_t(surface.width) * surface.height * 2);
    for (unsigned y = 0; y < surface.height; ++y)
        get_bytes(surface.mem + y * surface.pitch, pixels.data() + size_t(y) * surface.width * 2,
                  surface.width * 2);
    const mw34::materials::SurfaceKey key{
        surface.width, surface.height, format,
        mw34::materials::normal_hash(pixels.data(), pixels.size())};
    const auto page = surface_normals.world_bindings.find(key);
    const bool world = page != surface_normals.world_bindings.end();
    if (world && !surface_normals.authored.count(key) && mw34::materials::normal_maps_enabled())
        surface_normals_load_page(page->second);
    const auto binding = surface_normals.bindings.find(key);
    const int index = binding == surface_normals.bindings.end() ? -1 : binding->second;
    const bool registered = binding != surface_normals.bindings.end();
    cache[surface.guest] = {surface.version, surface.width, surface.height,
                            surface.pitch,   surface.mem,   format,
                            index,           registered,    world};
    static const bool trace = [] {
        const char *p = std::getenv("MW34_SURFACE_NORMAL_TRACE");
        return p && std::string(p) == "1";
    }();
    if ((index >= 0 || trace) && override_state().log.is_open())
        override_state().log << "{\"event\":\"surface_normal_bound\",\"texture\":" << surface.guest
                             << ",\"version\":" << surface.version << ",\"normal_index\":" << index
                             << ",\"source_width\":" << key.width
                             << ",\"source_height\":" << key.height
                             << ",\"source_format\":" << key.format
                             << ",\"source_hash\":" << key.hash
                             << ",\"automatic_world\":" << (world ? "true" : "false") << "}\n";
    return {registered, index};
}
int surface_normal_index(VSurfaceRec &surface) { return surface_normal_binding(surface).second; }
bool surface_normal_registered(VSurfaceRec &surface) {
    return surface_normal_binding(surface).first;
}
bool surface_world_normal_registered(VSurfaceRec &surface) {
    // World membership and authored precedence are separate: a key may appear in
    // both catalogs while its authored image or flat exclusion remains authoritative.
    const auto binding = surface_normal_binding(surface);
    if (!binding.first)
        return false;
    const auto cached = surface_normals.cache.find(surface.guest);
    return cached != surface_normals.cache.end() && cached->second.world;
}
