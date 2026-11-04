#include "graphics/retained_texture_cache.hpp"

#include <cstdio>
#include <vector>

namespace {
struct Texture {
    std::vector<unsigned> pixels;
};

unsigned failures;
void check(bool condition, const char *message) {
    if (!condition) {
        std::fprintf(stderr, "%s\n", message);
        ++failures;
    }
}
} // namespace

int main() {
    mw34::graphics::RetainedTextureCache<Texture> cache;
    unsigned builds = 0;
    auto fetch = [&](unsigned key) {
        return cache.get(key, [&] {
            ++builds;
            return Texture{std::vector<unsigned>(4096, key)};
        });
    };

    auto first = fetch(0);
    std::weak_ptr<const Texture> first_lifetime = first;
    check(fetch(0) == first && builds == 1, "A cached recipe must not be rendered again.");
    auto second = fetch(1);
    std::weak_ptr<const Texture> unused;
    for (unsigned key = 2; key <= 512; ++key) {
        unused = fetch(key);
    }
    check(!unused.expired(), "The cache must own an unreferenced cached texture.");

    auto last = fetch(513); // Evict while earlier frame textures are retained.
    check(unused.expired(), "Eviction must release textures no frame needs.");
    check(!first_lifetime.expired(), "Eviction must not free a frame's texture.");
    for (unsigned index : {0u, 2048u, 4095u}) {
        check(first->pixels[index] == 0 && second->pixels[index] == 1 && last->pixels[index] == 513,
              "A frame must sample its original pixels after cache eviction.");
    }
    first.reset();
    check(first_lifetime.expired(), "Finishing the frame must release its evicted texture.");
    check(fetch(0)->pixels[0] == 0 && builds == 515,
          "A later frame must rebuild an evicted recipe.");
    return failures ? 1 : 0;
}
