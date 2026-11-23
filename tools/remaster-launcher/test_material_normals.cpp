// Project-authored normal material contract; no original assets required.
#include "material_normals.hpp"
#include <array>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>

using namespace mw34::materials;
namespace mw34::detail {
struct FixtureSettings {
    bool water{}, clouds{};
};
inline const FixtureSettings &settings() {
    static FixtureSettings value;
    return value;
}
inline bool enabled(unsigned) { return false; }
} // namespace mw34::detail
namespace mw34::sun {
struct FixtureSettings {
    bool enabled{true};
};
inline const FixtureSettings &settings() {
    static FixtureSettings value;
    return value;
}
} // namespace mw34::sun
// Exercise the actual stage/cache with authored surface versions and memory.
struct SurfaceFixture {
    struct VSurfaceRec {
        unsigned guest{77}, width{5}, height{1}, pitch{10}, mem{8}, bpp{16};
        unsigned bytes{10}, locks{}, caps{1};
        std::uint64_t version{1};
        std::array<unsigned, 4> tex_masks{0xf800, 0, 0, 0};
    };
    static constexpr unsigned DDSCAPS_TEXTURE = 1;
    struct Host {
        std::vector<VSurfaceRec> vsurfaces;
        bool com_object(unsigned) { return true; }
    } host;
    struct OverrideTexture {
        std::string name;
        unsigned width{}, height{};
        std::uint64_t hash{};
        std::vector<std::uint32_t> pixels32;
    };
    struct State {
        std::vector<OverrideTexture> normal_textures;
        std::ofstream log;
    } override_data;
    std::array<unsigned char, 64> memory{};
    unsigned synchronizations{};
    State &override_state() { return override_data; }
    void gpu_sync(unsigned) { ++synchronizations; }
    void get_bytes(unsigned address, void *out, unsigned size) {
        if (std::uint64_t(address) + size > memory.size())
            throw std::runtime_error("Fixture read out of bounds");
        std::memcpy(out, memory.data() + address, size);
    }
    void surface_read(const VSurfaceRec &surface, unsigned offset, void *out, unsigned size) {
        if (std::uint64_t(surface.mem) + offset > memory.size())
            throw std::runtime_error("Fixture surface offset out of bounds");
        get_bytes(surface.mem + offset, out, size);
    }
#include "../m4-crt-heap-carry/host/surface_normals_stage.inc"
};

static void environment(const char *name, const char *value) {
#ifdef _WIN32
    _putenv_s(name, value);
#else
    setenv(name, value, 1);
#endif
}
static void require(bool value, const char *message) {
    if (!value)
        throw std::runtime_error(message);
}
static void u32(std::string &out, std::uint32_t value) {
    for (unsigned i = 0; i < 4; ++i)
        out.push_back(char(value >> (i * 8)));
}
static std::string pack(const std::string &material, bool legacy = false) {
    std::string out(legacy ? "BWNRM1\0\0" : "BWNRM2\0\0", 8);
    u32(out, 2);
    u32(out, 1);
    u32(out, 0);
    u32(out, legacy ? 0 : no_normal);
    out += material;
    out.resize(56, 0);
    u32(out, 1);
    u32(out, 1);
    const unsigned char pixel[]{128, 128, 255, 255};
    auto hash = normal_hash(pixel, 4);
    u32(out, std::uint32_t(hash));
    u32(out, std::uint32_t(hash >> 32));
    out.append(reinterpret_cast<const char *>(pixel), 4);
    return out;
}
static NormalPack read(const std::string &bytes, const std::vector<std::string> &names) {
    std::istringstream stream(bytes);
    return read_normals(stream, names);
}
static bool rejected(const std::string &bytes, const std::vector<std::string> &names) {
    try {
        read(bytes, names);
        return false;
    } catch (const std::runtime_error &) {
        return true;
    }
}
int main(int argc, char **argv) {
    try {
        {
            auto compressed = pack("Armor");
            compressed[5] = '3';
            compressed.resize(compressed.size() - 4);
            u32(compressed, 5);
            u32(compressed, 0);
            const unsigned char encoded[]{3, 128, 128, 255, 255};
            compressed.append(reinterpret_cast<const char *>(encoded), sizeof encoded);
            auto decoded = read(compressed, {"Armor", "Glass"});
            require(decoded.images[0].pixels[0] == 0xffff8080U &&
                        decoded.bindings[1] == no_normal,
                    "Compressed normal changed channels/exclusions");
            for (std::size_t size = 0; size < compressed.size(); ++size)
                require(rejected(compressed.substr(0, size), {"Armor", "Glass"}),
                        "Compressed truncation accepted");
            auto invalid = compressed;
            invalid[80] = '\xff';
            require(rejected(invalid, {"Armor", "Glass"}), "Oversized run accepted");
            invalid = compressed;
            invalid.back() = 0;
            require(rejected(invalid, {"Armor", "Glass"}), "Decoded hash mismatch accepted");
            require(rejected(compressed + "x", {"Armor", "Glass"}),
                    "Compressed trailing bytes accepted");
        }
        if (argc == 3 && std::string(argv[1]) == "--world-catalog-cache") {
            environment("MW34_SURFACE_NORMALS", "");
            environment("MW34_WORLD_NORMALS", argv[2]);
            environment("MW34_NORMAL_MAPS", "1");
            SurfaceFixture fixture;
            fixture.surface_normals_load();
            std::uint64_t peak{};
            size_t slots{}, evictions{};
            for (unsigned pass = 0; pass < 2; ++pass) {
                for (size_t page = 0; page < fixture.surface_normals.pages.size(); ++page) {
                    std::vector<bool> loaded;
                    for (const auto &entry : fixture.surface_normals.pages)
                        loaded.push_back(entry.loaded);
                    fixture.surface_normals_load_page(page);
                    std::uint64_t retained{};
                    for (size_t i = 0; i < fixture.surface_normals.pages.size(); ++i) {
                        const auto &entry = fixture.surface_normals.pages[i];
                        if (loaded[i] && !entry.loaded)
                            ++evictions;
                        for (int index : entry.normal_indices) {
                            const auto &texture = fixture.override_data.normal_textures.at(size_t(index));
                            require(texture.pixels32.size() == (entry.loaded ?
                                        size_t(texture.width) * texture.height : 0),
                                    "Page state and retained normal pixels disagree");
                            retained += texture.pixels32.size() * 4;
                        }
                    }
                    require(retained == fixture.surface_normals.world_bytes &&
                                retained <= 512ULL * 1024 * 1024,
                            "Retained world normal cache exceeded its fixed budget");
                    peak = std::max(peak, retained);
                }
                if (!pass)
                    slots = fixture.override_data.normal_textures.size();
                else
                    require(slots == fixture.override_data.normal_textures.size(),
                            "Second catalog traversal appended normal slots");
            }
            std::cout << "World CPU cache: pages " << fixture.surface_normals.pages.size()
                      << " traversals 2 slots " << slots << " evictions " << evictions
                      << " peak retained bytes " << peak << '\n';
            return 0;
        }
        if (argc == 3 && std::string(argv[1]) == "--surface-file") {
            std::ifstream input(argv[2], std::ios::binary);
            const auto surface = read_surface_normals(input);
            std::cout << "Decoded bindings " << surface.bindings.size() << " images "
                      << surface.pack.images.size() << '\n';
            for (const auto &image : surface.pack.images)
                std::cout << image.width << 'x' << image.height << " hash " << image.hash << '\n';
            return 0;
        }
        if (argc == 2 && (std::string(argv[1]) == "--world-pages" ||
                          std::string(argv[1]) == "--world-pages-compressed" ||
                          std::string(argv[1]) == "--world-pages-off")) {
            const bool disabled = std::string(argv[1]) == "--world-pages-off";
            const bool compressed = std::string(argv[1]) == "--world-pages-compressed";
            const auto folder =
                std::filesystem::temp_directory_path() /
                ("mw34-world-normals-" +
                 std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
            std::filesystem::create_directory(folder);
            struct RemoveFolder {
                std::filesystem::path path;
                ~RemoveFolder() {
                    std::error_code error;
                    std::filesystem::remove_all(path, error);
                }
            } remove{folder};
            unsigned char colour[10]{};
            const auto source_hash = normal_hash(colour, sizeof colour);
            auto page = [&](std::uint64_t first) {
                std::string out(compressed ? "BWSNR3\0\0" : "BWSNR2\0\0", 8);
                u32(out, 2);
                for (unsigned i = 0; i < 2; ++i) {
                    u32(out, 5);
                    u32(out, 1);
                    u32(out, 1);
                    u32(out, std::uint32_t(first + i));
                    u32(out, std::uint32_t((first + i) >> 32));
                    std::string name = i ? "Glass" : "Armor";
                    name.resize(32, 0);
                    out += name;
                }
                auto pixels = pack("Armor");
                if (compressed) {
                    pixels[5] = '3';
                    pixels.resize(pixels.size() - 4);
                    u32(pixels, 5);
                    u32(pixels, 0);
                    const unsigned char encoded[]{3, 128, 128, 255, 255};
                    pixels.append(reinterpret_cast<const char *>(encoded), sizeof encoded);
                }
                return out + pixels;
            };
            auto write = [&](const std::filesystem::path &name, const std::string &data) {
                std::ofstream file(folder / name, std::ios::binary);
                file.write(data.data(), std::streamsize(data.size()));
            };
            write("page-0.bin", page(source_hash));
            write("page-1.bin", page(source_hash + 2));
            write("world.txt", "MW34SNP1\npage-0.bin\npage-1.bin\n");
            environment("MW34_SURFACE_NORMALS", "");
            environment("MW34_WORLD_NORMALS", (folder / "world.txt").string().c_str());
            environment("MW34_NORMAL_MAPS", disabled ? "0" : "1");
            SurfaceFixture fixture;
            SurfaceFixture::VSurfaceRec surface;
            fixture.surface_normals_load();
            require(fixture.surface_normals.bindings.size() == 4 &&
                        fixture.override_data.normal_textures.empty(),
                    "World registration eagerly allocated images");
            require(fixture.surface_world_normal_registered(surface), "World key not admitted");
            require(fixture.surface_normal_index(surface) == (disabled ? -1 : 0),
                    "Lazy normal index mismatch");
            require(fixture.override_data.normal_textures.size() == (disabled ? 0U : 1U),
                    "Wrong lazy allocation count");
            require(!fixture.surface_normals.pages[1].loaded,
                    "Unreferenced normal page was loaded");
            require(fixture.synchronizations == 1, "World identity was rehashed per draw");
            if (!disabled) {
                SurfaceFixture cache;
                require(cache.surface_normal_index(surface) == 0, "Initial cached normal missing");
                cache.surface_normals_load_page(1, 4);
                require(cache.surface_normals.world_bytes == 4 &&
                            !cache.surface_normals.pages[0].loaded &&
                            cache.override_data.normal_textures[0].pixels32.empty(),
                        "Retained CPU normal pixels were not evicted");
                // A valid replacement payload with different pixels/hash must
                // not silently change a stable slot following eviction.
                auto replacement = page(source_hash);
                replacement[replacement.size() - 4] ^= 1;
                const unsigned char changed_pixel[]{129, 128, 255, 255};
                const auto changed_hash = normal_hash(changed_pixel, 4);
                for (unsigned i = 0; i < 8; ++i)
                    replacement[180 + i] = char(changed_hash >> (i * 8));
                write("page-0.bin", replacement);
                require(cache.surface_normal_index(surface) == 0 &&
                            !cache.surface_normals.pages[0].loaded &&
                            cache.surface_normals.world_bytes == 4,
                        "Identity-only lookup needlessly reloaded an evicted page");
                bool reload_refused = false;
                try { cache.surface_normals_require_image(0); }
                catch (const std::runtime_error &) { reload_refused = true; }
                require(reload_refused && cache.surface_normals.world_bytes == 4 &&
                            cache.override_data.normal_textures.size() == 2,
                        "Changed normal payload accepted during cache reload");
                write("page-0.bin", page(source_hash));
                cache.surface_normals_require_image(0);
                require(cache.surface_normal_index(surface) == 0 &&
                            cache.override_data.normal_textures.size() == 2 &&
                            cache.override_data.normal_textures[0].pixels32[0] == 0xffff8080U &&
                            cache.synchronizations == 1,
                        "Cached surface did not restore its exact stable normal slot");

                write("page-2.bin", page(source_hash + 4));
                write("world.txt", "MW34SNP1\npage-0.bin\npage-1.bin\npage-2.bin\n");
                SurfaceFixture lru;
                lru.surface_normals_load();
                lru.surface_normals_load_page(0, 8);
                lru.surface_normals_load_page(1, 8);
                lru.surface_normals_load_page(0, 8); // Touch the first page.
                lru.surface_normals_load_page(2, 8);
                require(lru.surface_normals.world_bytes == 8 &&
                            lru.surface_normals.pages[0].loaded &&
                            !lru.surface_normals.pages[1].loaded &&
                            lru.surface_normals.pages[2].loaded,
                        "World normal eviction did not retain the recently used page");
                lru.surface_normals_load_page(1, 8);
                require(lru.surface_normals.world_bytes == 8 &&
                            lru.override_data.normal_textures.size() == 3 &&
                            lru.surface_normals.pages[1].normal_indices[0] == 1,
                        "Reload appended or reassigned a normal slot");
                write("world.txt", "MW34SNP1\npage-0.bin\npage-1.bin\n");
                auto authored = page(source_hash);
                for (unsigned i = 0; i < 4; ++i)
                    authored[132 + i] = char(-1); // explicit first-material exclusion
                write("authored.bin", authored);
                environment("MW34_SURFACE_NORMALS", (folder / "authored.bin").string().c_str());
                SurfaceFixture precedence;
                require(precedence.surface_normal_index(surface) == -1 &&
                            !precedence.surface_normals.pages[0].loaded,
                        "Automatic normal replaced an authored exclusion");
                environment("MW34_SURFACE_NORMALS", "");
                auto corrupted = page(source_hash);
                corrupted.back() ^= 1;
                write("page-0.bin", corrupted);
                bool refused = false;
                try {
                    SurfaceFixture broken;
                    broken.surface_normal_index(surface);
                } catch (...) {
                    refused = true;
                }
                require(refused, "Corrupted lazy normal accepted");
            }
            write("world.txt", "MW34SNP1\n../page-0.bin\n");
            bool refused = false;
            try {
                SurfaceFixture broken;
                broken.surface_normals_load();
            } catch (...) {
                refused = true;
            }
            require(refused, "World manifest escaped its page directory");
            std::cout << "World pages: lazy allocation, disabled admission, authored precedence "
                         "and corruption controls pass\n";
            return 0;
        }
        if (argc == 2 && std::string(argv[1]) == "--maps-off") {
            std::string header("BWSNR2\0\0", 8);
            u32(header, 1);
            u32(header, 5);
            u32(header, 1);
            u32(header, 1);
            const unsigned char colour[10]{};
            const auto hash = normal_hash(colour, sizeof colour);
            u32(header, std::uint32_t(hash));
            u32(header, std::uint32_t(hash >> 32));
            std::string name = "Armor";
            name.resize(32, 0);
            header += name;
            const auto path =
                std::filesystem::temp_directory_path() /
                ("mw34-normal-header-" +
                 std::to_string(
                     std::chrono::high_resolution_clock::now().time_since_epoch().count()) +
                 ".bin");
            struct Remove {
                std::filesystem::path path;
                ~Remove() {
                    std::error_code error;
                    std::filesystem::remove(path, error);
                }
            } remove{path};
            {
                std::ofstream output(path, std::ios::binary);
                output.write(header.data(), std::streamsize(header.size()));
            }
            environment("MW34_SURFACE_NORMALS", path.string().c_str());
            environment("MW34_NORMAL_MAPS", "0");
            SurfaceFixture fixture;
            SurfaceFixture::VSurfaceRec surface;
            require(fixture.surface_normal_registered(surface),
                    "Mapping disabled also disabled material lighting admission");
            require(fixture.surface_normal_index(surface) == -1 &&
                        fixture.override_data.normal_textures.empty(),
                    "Disabled mapping loaded normal pixels");
            require(fixture.synchronizations == 1, "Material registration was not cached");
            std::cout << "Normal mapping off: material admission retained without loading image "
                         "payload\n";
            return 0;
        }
        const auto valid = pack("Armor");
        auto parsed = read(valid, {"Armor", "Glass"});
        require(parsed.bindings[0] == 0 && parsed.bindings[1] == no_normal,
                "Explicit disabled material");
        require(parsed.images[0].pixels[0] == 0xffff8080U, "RGBA channel bytes preserved");
        for (std::size_t n = 0; n < valid.size(); ++n)
            require(rejected(valid.substr(0, n), {"Armor", "Glass"}), "Truncation accepted");
        require(rejected(valid + "x", {"Armor", "Glass"}), "Trailing bytes accepted");
        require(rejected(valid, {"Other", "Glass"}), "Reordered albedo material accepted");
        require(rejected(valid, {"Armor"}), "Wrong batch count accepted");
        auto corrupt = valid;
        corrupt.back() ^= 1;
        require(rejected(corrupt, {"Armor", "Glass"}), "Corrupt pixel hash accepted");
        corrupt = valid;
        corrupt[16] = 1;
        require(rejected(corrupt, {"Armor", "Glass"}), "Invalid material index accepted");
        corrupt = valid;
        corrupt[56] = 0;
        require(rejected(corrupt, {"Armor", "Glass"}), "Zero width accepted");
        corrupt = valid;
        corrupt[24] = 0;
        require(rejected(corrupt, {"Armor", "Glass"}), "Empty name accepted");
        auto glass = read(pack("Window", true), {"Window", "Window"});
        require(glass.bindings[0] == no_normal && glass.bindings[1] == no_normal,
                "Legacy glass must be identified by name");
        auto armor = read(pack("strider03", true), {"strider03", "strider03"});
        require(armor.bindings[0] == 0, "Legacy ordinary material lost its normal map");
        std::string surfaces("BWSNR2\0\0", 8);
        u32(surfaces, 2);
        for (const auto &name : std::vector<std::string>{"Armor", "Glass"}) {
            u32(surfaces, 1);
            u32(surfaces, 1);
            u32(surfaces, 1);
            u32(surfaces, name == "Armor" ? 123 : 456);
            u32(surfaces, 0);
            std::string field = name;
            field.resize(32, 0);
            surfaces += field;
        }
        surfaces += valid;
        std::istringstream input(surfaces);
        auto mapping = read_surface_normals(input);
        require(mapping.bindings.at({1, 1, 1, 123}) == 0, "Surface content identity missing");
        require(mapping.bindings.at({1, 1, 1, 456}) == no_normal, "Surface exclusion lost");
        require(!mapping.bindings.count({1, 1, 2, 123}) && !mapping.bindings.count({1, 1, 1, 124}),
                "Surface format/content aliases");
        for (std::size_t n = 0; n < surfaces.size(); ++n) {
            bool refused = false;
            try {
                std::istringstream truncated(surfaces.substr(0, n));
                read_surface_normals(truncated);
            } catch (...) {
                refused = true;
            }
            require(refused, "Truncated surface binding accepted");
        }
        auto duplicate = surfaces;
        for (unsigned i = 0; i < 20; ++i)
            duplicate[12 + 52 + i] = surfaces[12 + i];
        bool refused = false;
        try {
            std::istringstream bad(duplicate);
            read_surface_normals(bad);
        } catch (...) {
            refused = true;
        }
        require(refused, "Duplicate surface identity accepted");
        std::string expanded("BWSNR2\0\0", 8);
        u32(expanded, 256);
        for (unsigned i = 0; i < 256; ++i) {
            u32(expanded, 1);
            u32(expanded, 1);
            u32(expanded, 1);
            u32(expanded, i);
            u32(expanded, 0);
            std::string name = "Armor";
            name.resize(32, 0);
            expanded += name;
        }
        expanded.append("BWNRM2\0\0", 8);
        u32(expanded, 256);
        u32(expanded, 1);
        for (unsigned i = 0; i < 256; ++i)
            u32(expanded, 0);
        expanded += valid.substr(24);
        std::istringstream expanded_input(expanded);
        auto expanded_mapping = read_surface_normals(expanded_input);
        require(expanded_mapping.bindings.size() == 256 && expanded_mapping.pack.images.size() == 1,
                "Surface aliases did not share one normal image");
        expanded[8] = 1;
        expanded[9] = 1; // 257 bindings exceeds the bounded contract.
        refused = false;
        try {
            std::istringstream too_many(expanded);
            read_surface_normals(too_many);
        } catch (const std::runtime_error &) {
            refused = true;
        }
        require(refused, "Oversized surface catalog accepted");
        std::string first(10, 0), second(10, 0);
        second[9] = 1;
        std::string cache_pack("BWSNR2\0\0", 8);
        u32(cache_pack, 2);
        for (const auto &colour : std::vector<std::string>{first, second}) {
            u32(cache_pack, 5);
            u32(cache_pack, 1);
            u32(cache_pack, 1);
            const auto hash = normal_hash(colour.data(), colour.size());
            u32(cache_pack, std::uint32_t(hash));
            u32(cache_pack, std::uint32_t(hash >> 32));
            std::string name = colour == first ? "Armor" : "Glass";
            name.resize(32, 0);
            cache_pack += name;
        }
        cache_pack += valid;
        struct Temporary {
            std::filesystem::path path =
                std::filesystem::temp_directory_path() /
                ("mw34-surface-normal-" +
                 std::to_string(
                     std::chrono::high_resolution_clock::now().time_since_epoch().count()) +
                 ".bin");
            ~Temporary() {
                std::error_code error;
                std::filesystem::remove(path, error);
            }
        } temporary;
        {
            std::ofstream output(temporary.path, std::ios::binary);
            output.write(cache_pack.data(), std::streamsize(cache_pack.size()));
        }
        const auto filename = temporary.path.string();
        environment("MW34_SURFACE_NORMALS", filename.c_str());
        environment("MW34_NORMAL_MAPS", "1");
        SurfaceFixture fixture;
        SurfaceFixture::VSurfaceRec surface;
        require(fixture.surface_normal_index(surface) == 0 && fixture.synchronizations == 1,
                "Initial surface identity not bound");
        const std::vector<unsigned short> replacement(5, 0);
        require(fixture.replacement_surface_normal_index(0, 5, 1, replacement) == 0,
                "Replacement RGB565 pixels did not bind authored normal");
        require(fixture.synchronizations == 1, "Replacement pixels read a guest surface");
        auto changed = replacement;
        changed.back() = 1;
        require(fixture.replacement_surface_normal_index(1, 5, 1, changed) == -1,
                "Replacement same-prefix pixels bound a foreign normal");
        require(fixture.replacement_surface_normal_index(2, 1, 5, replacement) == -1,
                "Replacement dimensions ignored in full-content key");
        require(fixture.surface_normal_index(surface) == 0 && fixture.synchronizations == 1,
                "Unchanged texture rehashed per draw");
        fixture.memory[17] = 1;
        ++surface.version;
        require(fixture.surface_normal_index(surface) == -1 && fixture.synchronizations == 2,
                "Same-prefix changed texture retained old normal");
        require(fixture.surface_normal_registered(surface),
                "Explicit unperturbed material lost geometric lighting admission");
        fixture.memory[17] = 0;
        ++surface.version;
        require(fixture.surface_normal_index(surface) == 0 && fixture.synchronizations == 3,
                "Restored texture version did not rebind");
        surface.width = 1;
        surface.height = 5;
        surface.pitch = 2;
        require(fixture.surface_normal_index(surface) == -1 && fixture.synchronizations == 4,
                "Reused dimensions retained old normal");
        surface.width = 5;
        surface.height = 1;
        surface.pitch = 10;
        surface.tex_masks[0] = 0x7c00;
        require(fixture.surface_normal_index(surface) == -1 && fixture.synchronizations == 5,
                "Pixel format change retained old normal");
        surface.tex_masks[0] = 0xf800;
        surface.mem = 20;
        require(fixture.surface_normal_index(surface) == 0 && fixture.synchronizations == 6,
                "Changed backing address not inspected");
        surface.pitch = 12;
        require(fixture.surface_normal_index(surface) == 0 && fixture.synchronizations == 7,
                "Changed pitch not inspected");
        surface.mem = 0xfffffffeU;
        surface.height = 2;
        require(fixture.surface_normal_index(surface) == -1 && fixture.synchronizations == 7,
                "Wrapped guest pixel span read");
        Temporary additional, manifest;
        {
            std::ofstream output(additional.path, std::ios::binary);
            output.write(surfaces.data(), std::streamsize(surfaces.size()));
        }
        auto write_manifest = [&](const std::string &pages) {
            std::ofstream output(manifest.path, std::ios::binary);
            output << "MW34SNA1\n" << pages;
        };
        write_manifest(temporary.path.filename().string() + "\n" +
                       additional.path.filename().string() + "\n");
        write_manifest(temporary.path.string() + "\n" + additional.path.string() + "\n");
        const auto absolute_pages = surface_normal_catalog_paths(manifest.path);
        require(absolute_pages.size() == 2 && absolute_pages[0] == temporary.path,
                "Explicit absolute authored page paths were rejected");
        write_manifest(temporary.path.string() + "\n" + temporary.path.filename().string() + "\n");
        refused = false;
        try { surface_normal_catalog_paths(manifest.path); }
        catch (const std::exception &) { refused = true; }
        require(refused, "Absolute/relative aliases of the same page were accepted");
        write_manifest(temporary.path.filename().string() + "\n" + additional.path.filename().string() + "\n");
        const auto manifest_name = manifest.path.string();
        environment("MW34_SURFACE_NORMALS", manifest_name.c_str());
        SurfaceFixture paged;
        paged.surface_normals_load();
        require(paged.override_data.normal_textures.size() == 2 &&
                    paged.surface_normals.bindings.at({1, 1, 1, 123}) == 1 &&
                    paged.surface_normals.authored.size() == 4,
                "Paged authored normal offsets or precedence lost");
        {
            std::ofstream output(additional.path, std::ios::binary);
            output.write(cache_pack.data(), std::streamsize(cache_pack.size()));
        }
        refused = false;
        try {
            SurfaceFixture duplicated;
            duplicated.surface_normals_load();
        } catch (const std::runtime_error &) { refused = true; }
        require(refused, "Duplicate key across authored pages accepted");
        for (const auto &bad : {std::string("../escape.bin\n"),
                                temporary.path.filename().string() + "\n" +
                                    temporary.path.filename().string() + "\n",
                                std::string("missing-page.bin\n"), std::string()}) {
            write_manifest(bad);
            refused = false;
            try { surface_normal_catalog_paths(manifest.path); }
            catch (const std::exception &) { refused = true; }
            require(refused, "Invalid authored page list accepted");
        }
        write_manifest(additional.path.filename().string() + "\n");
        std::filesystem::resize_file(additional.path, 256ULL * 1024 * 1024 + 1);
        refused = false;
        try { surface_normal_catalog_paths(manifest.path); }
        catch (const std::exception &) { refused = true; }
        require(refused, "Authored aggregate byte budget exceeded");
        std::vector<Temporary> budget_pages(9);
        for (const auto &page : budget_pages) {
            std::ofstream output(page.path, std::ios::binary); output.close();
            std::filesystem::resize_file(page.path, 180ULL * 1024 * 1024);
        }
        write_manifest(budget_pages[0].path.string() + "\n" + budget_pages[1].path.string() + "\n");
        require(surface_normal_catalog_paths(manifest.path).size() == 2,
                "Current enhanced material catalog size was rejected");
        write_manifest(budget_pages[0].path.string() + "\n" + budget_pages[1].path.string() + "\n" +
                       budget_pages[2].path.string() + "\n");
        require(surface_normal_catalog_paths(manifest.path).size() == 3,
                "Authored catalogs above 512 MiB were rejected");
        std::string over_budget;
        for (const auto &page : budget_pages)
            over_budget += page.path.string() + "\n";
        write_manifest(over_budget);
        refused = false;
        try { surface_normal_catalog_paths(manifest.path); }
        catch (const std::exception &) { refused = true; }
        require(refused, "Enhanced 1536 MiB catalog budget was not enforced");
        std::cout << "Material normals: truncation, bounds, identity, explicit exclusions, legacy "
                     "glass and channel checks pass\n";
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
