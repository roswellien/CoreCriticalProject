#pragma once
struct ReplayTexture {
    uint32_t width, height;
    std::vector<uint8_t> pixels;
};
struct ReplayDraw {
    uint32_t texture, count, shade, alpha, fog, blend, u, v, fogColor, filtering, depthWrite;
    std::vector<uint8_t> vertices;
};
struct ReplayScene {
    uint32_t width, height;
    std::vector<uint8_t> color, depth;
    std::vector<ReplayTexture> textures;
    std::vector<ReplayDraw> draws;
};
static ReplayScene readScene(const char *filename) {
    std::ifstream file(filename, std::ios::binary);
    auto read = [&](void *data, size_t size) {
        if (!file.read(static_cast<char *>(data), static_cast<std::streamsize>(size)))
            throw std::runtime_error("Truncated replay package");
    };
    char magic[8];
    read(magic, 8);
    const bool version2 = std::memcmp(magic, "MW34SCN2", 8) == 0;
    const bool version3 = std::memcmp(magic, "MW34SCN3", 8) == 0;
    if (!version2 && !version3 && std::memcmp(magic, "MW34SCN1", 8))
        throw std::runtime_error("Bad replay package magic");
    uint32_t header[4];
    read(header, 16);
    if (!header[0] || !header[1] || header[0] > 4096 || header[1] > 4096 || !header[2] ||
        header[2] > 1024 || !header[3] || header[3] > 2048)
        throw std::runtime_error("Replay package limits");
    ReplayScene scene{};
    scene.width = header[0];
    scene.height = header[1];
    size_t total = 0;
    auto bytes = [&](size_t size) {
        total += size;
        if (total > 128U * 1024U * 1024U)
            throw std::runtime_error("Replay payload budget");
        std::vector<uint8_t> data(size);
        read(data.data(), size);
        return data;
    };
    scene.color = bytes(static_cast<size_t>(scene.width) * scene.height * 4);
    scene.depth = bytes(scene.color.size());
    for (uint32_t i = 0; i < header[2]; ++i) {
        uint32_t wh[2];
        read(wh, 8);
        if (!wh[0] || !wh[1] || wh[0] > 4096 || wh[1] > 4096)
            throw std::runtime_error("Texture limits");
        scene.textures.push_back({wh[0], wh[1], bytes(static_cast<size_t>(wh[0]) * wh[1] * 4)});
    }
    for (uint32_t i = 0; i < header[3]; ++i) {
        uint32_t s[11]{};
        s[10] = 1;
        read(s, version3 ? 44 : (version2 ? 40 : 36));
        if (s[0] >= header[2] || !s[1] || s[1] > 196608 || s[1] % 3 || (s[2] != 1 && s[2] != 2) ||
            s[3] > 1 || s[4] > 1 || s[5] > 1 || (s[6] != 1 && s[6] != 3) ||
            (s[7] != 1 && s[7] != 3) || s[9] > 1 || s[10] > 1)
            throw std::runtime_error("Draw profile limits");
        scene.draws.push_back({s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10],
                               bytes(static_cast<size_t>(s[1]) * 32)});
    }
    if (file.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing replay data");
    return scene;
}
