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
    std::vector<std::array<uint32_t,10>> commands;
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
    const bool version4 = std::memcmp(magic, "MW34SCN4", 8) == 0;
    if (!version2 && !version3 && !version4 && std::memcmp(magic, "MW34SCN1", 8))
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
        read(s, (version3 || version4) ? 44 : (version2 ? 40 : 36));
        if (s[0] >= header[2] || !s[1] || s[1] > 196608 || s[1] % 3 || (s[2] != 1 && s[2] != 2) ||
            s[3] > 1 || s[4] > 1 || s[5] > 1 || (s[6] != 1 && s[6] != 3) ||
            (s[7] != 1 && s[7] != 3) || s[9] > 1 || s[10] > 1)
            throw std::runtime_error("Draw profile limits");
        scene.draws.push_back({s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10],
                               bytes(static_cast<size_t>(s[1]) * 32)});
    }
    if(version4) {
        uint32_t count{};read(&count,4);
        if(!count || count>8192)throw std::runtime_error("Command count limits");
        std::vector<bool> seen(scene.draws.size(),false);
        auto rectangle=[](uint32_t x,uint32_t y,uint32_t w,uint32_t h,uint32_t width,uint32_t height) {
            return w && h && x<width && y<height && w<=width-x && h<=height-y;
        };
        for(uint32_t i=0;i<count;++i) {
            std::array<uint32_t,10> c{};read(c.data(),40);
            if(c[0]==1) {
                if(c[1]>=seen.size() || seen[c[1]])throw std::runtime_error("Repeated/invalid ordered draw");
                for(size_t j=2;j<10;++j)if(c[j])throw std::runtime_error("Draw command reserved fields");
                seen[c[1]]=true;
            } else if(c[0]==2) {
                float depth{};std::memcpy(&depth,&c[7],4);
                if(!c[1] || (c[1]&~3U) || !rectangle(c[2],c[3],c[4],c[5],scene.width,scene.height) ||
                   !std::isfinite(depth) || depth<0 || depth>1 || c[8] || c[9])
                    throw std::runtime_error("Clear command limits");
            } else if(c[0]==3) {
                if(c[1]>=scene.textures.size() || c[8] || c[9])throw std::runtime_error("Copy command limits");
                const auto &t=scene.textures[c[1]];
                if(!rectangle(c[2],c[3],c[6],c[7],t.width,t.height) ||
                   !rectangle(c[4],c[5],c[6],c[7],scene.width,scene.height))
                    throw std::runtime_error("Copy rectangle limits");
            } else throw std::runtime_error("Unknown replay command");
            scene.commands.push_back(c);
        }
        for(bool used:seen)if(!used)throw std::runtime_error("Omitted ordered draw");
    } else {
        for(uint32_t i=0;i<header[3];++i)scene.commands.push_back({1,i,0,0,0,0,0,0,0,0});
    }
    if (file.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing replay data");
    return scene;
}
