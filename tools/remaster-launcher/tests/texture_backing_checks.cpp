#include "../native-overrides/texture_backing.hpp"
#include "../native-overrides/surface_page_pool.hpp"
#include <array>
#include <limits>
#include <iostream>

int main() {
    using mw34::textures::Backing;
    Backing source;
    source.resize(32);
    std::array<unsigned char, 32> pixels{};
    source.read(0, pixels.data(), pixels.size());
    for (auto x : pixels) if (x) return 1;
    pixels.fill(0x6a);
    source.write(0, pixels.data(), pixels.size());
    Backing destination = source; // Texture2::Load shares immutable pixels.
    unsigned char changed = 0xb1, actual{};
    source.write(9, &changed, 1);
    destination.read(9, &actual, 1);
    if (actual != 0x6a) return 2;
    destination.write(4, &changed, 1);
    source.read(4, &actual, 1);
    if (actual != 0x6a) return 3;
    source.clear();
    destination.read(9, &actual, 1);
    if (actual != 0x6a || !source.empty()) return 4;
    for (auto offset : {std::size_t(32), std::numeric_limits<std::size_t>::max()}) {
        bool rejected = false;
        try { destination.write(offset, &changed, 1); }
        catch (const std::out_of_range&) { rejected = true; }
        if (!rejected) return 5;
    }
    // Lock views recycle guest pages regardless of aggregate texture size.
    mw34::surface_pages::FreeList views;
    constexpr unsigned bytes = 16 * 1024 * 1024, address = 0x40000000;
    views.put(address, bytes);
    std::uint64_t cumulative{};
    for (unsigned i = 0; i < 256; ++i) {
        auto mapped = views.take(bytes);
        if (mapped != address) return 6;
        views.put(mapped, bytes);
        cumulative += bytes;
    }
    if (cumulative != 0x100000000ULL) return 7;
    std::cout << "Texture ownership, copy-on-write, range and 4 GiB lock-view recycling checks passed\n";
}
