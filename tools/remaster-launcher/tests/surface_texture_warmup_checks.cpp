#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>
#include <vector>

// Authored provider fixtures exercise the production preparation adapter without
// game media, guest execution or a Vulkan device. They grant no gameplay credit.
constexpr unsigned DDSCAPS_TEXTURE = 1, DDSCAPS_3DDEVICE = 2,
    DDSCAPS_PRIMARYSURFACE = 4, DDSCAPS_BACKBUFFER = 8, DDSCAPS_ZBUFFER = 16;

namespace mw34::vkscene {
enum class TexFormat { rgb565, argb1555, argb4444, rgba8888 };
struct TextureRef {
    std::uint64_t key{}, hash{};
    unsigned width{}, height{};
    TexFormat format{};
    std::vector<std::uint16_t> pixels;
    std::vector<std::uint32_t> pixels32;
};
struct Scene {
    bool frontend_canvas{}, world_eye_valid{true};
    std::vector<TextureRef> textures;
};
}

struct Surface {
    unsigned guest{1}, mem{0x4000000}, locks{}, caps{DDSCAPS_TEXTURE}, bpp{16};
    unsigned width{4}, height{4}, pitch{8};
    std::uint64_t version{1};
    bool alive{true};
    std::array<unsigned, 4> tex_masks{0xf800, 0x07e0, 0x001f, 0};
};
struct Proof {
    bool registered{true}, world{true};
    std::uint64_t version{1};
    unsigned width{4}, height{4}, pitch{8}, memory{0x4000000}, format{1};
    int index{};
};
struct Renderer {
    std::map<std::uint64_t, std::tuple<std::uint64_t, unsigned, unsigned>> resident;
    bool current(std::uint64_t key, std::uint64_t hash, unsigned w, unsigned h) {
        const auto found = resident.find(key);
        return found != resident.end() && found->second == std::tuple{hash, w, h};
    }
};
struct NormalTexture {
    unsigned width{4}, height{4};
    std::uint64_t hash{17};
    std::vector<std::uint32_t> pixels32 = std::vector<std::uint32_t>(16, 0x80402010);
};
struct Fixture {
    Renderer renderer;
    struct Host {
        std::vector<Surface> vsurfaces{Surface{}};
        Renderer* sren{};
        void* com_object(unsigned id) {
            for (auto& surface : vsurfaces)
                if (surface.guest == id && surface.alive) return &surface;
            return nullptr;
        }
    } host;
    struct NormalState {
        bool loaded{true}, gpu_prewarmed{};
        std::map<unsigned, Proof> cache{{1, Proof{}}};
    } surface_normals;
    struct Overrides { std::vector<NormalTexture> normal_textures{NormalTexture{}}; } overrides;
    unsigned reads{}, synchronizations{};
    bool change_during_sync{};

    Fixture() { host.sren = &renderer; }
    Overrides& override_state() { return overrides; }
    void gpu_sync(unsigned id) {
        ++synchronizations;
        if (change_during_sync)
            for (auto& surface : host.vsurfaces)
                if (surface.guest == id) ++surface.version;
    }
    void get_bytes(unsigned address, void* out, unsigned bytes) {
        bool valid = false;
        for (const auto& surface : host.vsurfaces)
            if (address >= surface.mem && std::uint64_t(address) + bytes <=
                    std::uint64_t(surface.mem) + std::uint64_t(surface.height) * surface.pitch)
                valid = true;
        assert(valid);
        ++reads;
        std::memset(out, 0x5a, bytes);
    }
#include "../native-overrides/surface_texture_warmup.inc"
};

int main(int argc, char** argv) {
    const bool off = argc > 1 && std::strcmp(argv[1], "off") == 0;
    const bool invalid = argc > 1 && std::strcmp(argv[1], "invalid") == 0;
    _putenv_s("MW34_TEXTURE_PREWARM", off ? "0" : invalid ? "2" : "1");
    using mw34::vkscene::Scene;
    if (off || invalid) {
        Fixture f; Scene scene; bool rejected = false;
        try { f.surface_texture_prewarm(scene); }
        catch (const std::runtime_error&) { rejected = true; }
        assert(rejected == invalid && f.reads == 0 && scene.textures.empty());
        return 0;
    }
    {
        Fixture f; Scene scene; f.surface_texture_prewarm(scene);
        assert(scene.textures.size() == 2 && f.reads == 4 && f.synchronizations == 1);
        assert(scene.textures[0].key == 1 && scene.textures[0].hash == 1);
        assert(scene.textures[0].pixels == std::vector<std::uint16_t>(16, 0x5a5a));
        assert(scene.textures[1].key == 0x42574e524d000000ULL);
        assert(scene.textures[1].pixels32 == f.overrides.normal_textures[0].pixels32);
        Scene next; f.surface_texture_prewarm(next);
        assert(next.textures.empty() && f.reads == 4);
    }
    // Every observed surface identity component must remain valid before reads.
    for (unsigned changed = 0; changed < 15; ++changed) {
        Fixture f; Scene scene; auto& s = f.host.vsurfaces[0];
        switch (changed) {
        case 0: s.locks = 1; break;
        case 1: s.alive = false; break;
        case 2: s.caps |= DDSCAPS_3DDEVICE; break;
        case 3: s.caps |= DDSCAPS_BACKBUFFER; break;
        case 4: s.caps |= DDSCAPS_PRIMARYSURFACE; break;
        case 5: s.caps |= DDSCAPS_ZBUFFER; break;
        case 6: s.bpp = 32; break;
        case 7: ++s.version; break;
        case 8: ++s.width; break;
        case 9: ++s.height; break;
        case 10: ++s.pitch; break;
        case 11: ++s.mem; break;
        case 12: s.tex_masks[0] = 0x7c00; break;
        case 13: f.surface_normals.cache[1].world = false; break;
        case 14: f.surface_normals.cache[1].registered = false; break;
        }
        f.surface_texture_prewarm(scene);
        assert(scene.textures.empty() && f.reads == 0 && f.synchronizations == 0);
    }
    {
        Fixture f; Scene scene; scene.frontend_canvas = true;
        f.surface_texture_prewarm(scene);
        assert(!f.surface_normals.gpu_prewarmed && f.reads == 0);
        scene.frontend_canvas = false; scene.world_eye_valid = false;
        f.surface_texture_prewarm(scene);
        assert(!f.surface_normals.gpu_prewarmed && f.reads == 0);
        scene.world_eye_valid = true; f.surface_texture_prewarm(scene);
        assert(scene.textures.size() == 2);
    }
    {
        Fixture f; Scene scene;
        f.renderer.resident[1] = {1, 4, 4};
        f.renderer.resident[0x42574e524d000000ULL] = {17, 4, 4};
        f.surface_texture_prewarm(scene);
        assert(scene.textures.empty() && f.reads == 0);
    }
    {
        Fixture f; Scene scene; f.change_during_sync = true;
        f.surface_texture_prewarm(scene);
        assert(f.reads == 0);
        for (const auto& ref : scene.textures) assert(ref.key != 1);
    }
    {
        Fixture f; Scene scene; f.surface_normals.cache[1].index = 99;
        bool rejected = false;
        try { f.surface_texture_prewarm(scene); }
        catch (const std::runtime_error&) { rejected = true; }
        assert(rejected);
    }
    {
        Fixture f; Scene scene; f.host.vsurfaces.clear(); f.surface_normals.cache.clear();
        for (unsigned id = 1; id <= 5; ++id) {
            Surface s; s.guest = id; s.mem = id * 0x4000000;
            s.width = s.height = id == 5 ? 1 : 4096; s.pitch = s.width * 2;
            f.host.vsurfaces.push_back(s);
            Proof proof; proof.width = s.width; proof.height = s.height;
            proof.pitch = s.pitch; proof.memory = s.mem; proof.index = -1;
            f.surface_normals.cache[id] = proof;
        }
        f.surface_texture_prewarm(scene);
        // Three full 4096-square mip chains plus one 1x1 fit exactly 256 MiB.
        assert(scene.textures.size() == 4 && scene.textures.back().key == 5);
        assert(f.reads == 3 * 4096 + 1);
        for (const auto& ref : scene.textures) assert(ref.key != 4);
    }
}
