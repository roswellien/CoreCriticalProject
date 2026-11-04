// Optional world normals use validated BWSNR2/3 pages. Header keys
// register geometry without allocating pixels; each page is read on first use.
void surface_normals_load_world() {
    // Admit bounded page names and source keys at startup, without loading normal
    // pixels. The overall file-size budget is separate from resident image bytes.
    const char *configured = std::getenv("MW34_WORLD_NORMALS");
    if (!configured || !*configured)
        return;
    auto &normal_state = surface_normals;
    const std::filesystem::path manifest(configured);
    std::ifstream list(manifest);
    if (!list)
        throw std::runtime_error("Configured world-normal manifest is missing");
    std::string line;
    if (!std::getline(list, line))
        throw std::runtime_error("Empty world-normal manifest");
    if (!line.empty() && line.back() == '\r')
        line.pop_back();
    if (line != "MW34SNP1")
        throw std::runtime_error("Invalid world-normal manifest version");
    std::set<std::string> page_names;
    std::set<mw34::materials::SurfaceKey> registered_keys;
    std::uint64_t package_bytes{};
    while (std::getline(list, line)) {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        if (line.empty() || line.size() > 80 || line == "." || line == ".." ||
            line.find_first_not_of(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.") !=
                std::string::npos ||
            !page_names.insert(line).second || page_names.size() > 256)
            throw std::runtime_error("Invalid world-normal page name/count");
        SurfaceNormalState::Page page;
        page.path = manifest.parent_path() / line;
        const auto size = std::filesystem::file_size(page.path);
        package_bytes += size;
        if (size > 16 * 1024 * 1024 ||
            package_bytes > mw34::materials::world_normal_catalog_budget)
            throw std::runtime_error("World-normal package exceeds byte budget");
        std::ifstream input(page.path, std::ios::binary);
        if (!input)
            throw std::runtime_error("World-normal page is missing");
        auto header = mw34::materials::read_surface_normal_header(input);
        for (const auto &entry : header) {
            if (!registered_keys.insert(entry.first).second || registered_keys.size() > 16384)
                throw std::runtime_error("Duplicate/excess world-normal texture keys");
            page.keys.insert(entry.first);
            normal_state.world_bindings.emplace(entry.first, normal_state.pages.size());
            normal_state.bindings.emplace(entry.first,
                                          -1); // Authored catalog indices take precedence.
        }
        normal_state.pages.push_back(std::move(page));
    }
    if (!list.eof() || normal_state.pages.empty())
        throw std::runtime_error("Incomplete world-normal manifest");
    auto &log = override_state().log;
    if (log.is_open())
        log << "{\"event\":\"world_normal_catalog_loaded\",\"pages\":" << normal_state.pages.size()
            << ",\"bindings\":" << registered_keys.size()
            << ",\"images\":0,\"method\":\"automatic color-derived preview; lazy pages\"}\n";
}
void surface_normals_load_page(size_t page_index,
                               std::uint64_t pixel_budget = 512ULL * 1024 * 1024) {
    // Reopen on first use and verify the full key set against the admitted header.
    // This catches changed key membership, not a cryptographic pin of image bytes.
    auto &normal_state = surface_normals;
    auto &page = normal_state.pages.at(page_index);
    page.last_use = ++normal_state.world_clock;
    if (pixel_budget > 512ULL * 1024 * 1024)
        throw std::runtime_error("World-normal resident pixel budget exceeds limit");
    if (page.loaded) {
        if (normal_state.world_bytes > pixel_budget)
            throw std::runtime_error("Loaded world normals exceed requested pixel budget");
        return;
    }
    std::ifstream input(page.path, std::ios::binary);
    if (!input)
        throw std::runtime_error("World-normal page disappeared");
    auto parsed = mw34::materials::read_surface_normals(input);
    if (parsed.bindings.size() != page.keys.size())
        throw std::runtime_error("World-normal page keys changed");
    for (const auto &entry : parsed.bindings)
        if (!page.keys.count(entry.first))
            throw std::runtime_error("World-normal page identity changed");
    std::uint64_t page_pixel_bytes{};
    for (const auto &image : parsed.pack.images)
        page_pixel_bytes += image.pixels.size() * 4;
    auto &overrides = override_state();
    if (page.initialized) {
        if (page.normal_indices.size() != parsed.pack.images.size() ||
            page.pixel_bytes != page_pixel_bytes)
            throw std::runtime_error("World-normal page payload changed after eviction");
        for (size_t i = 0; i < parsed.pack.images.size(); ++i) {
            const auto &before = overrides.normal_textures.at(size_t(page.normal_indices[i]));
            const auto &after = parsed.pack.images[i];
            if (before.name != after.name || before.width != after.width ||
                before.height != after.height || before.hash != after.hash)
                throw std::runtime_error("World-normal image changed after eviction");
        }
        for (const auto &[key, index] : parsed.bindings)
            if (page.local_bindings.at(key) != index)
                throw std::runtime_error("World-normal binding changed after eviction");
    }
    if (pixel_budget > 512ULL * 1024 * 1024 || page_pixel_bytes > pixel_budget)
        throw std::runtime_error("World-normal page exceeds resident pixel budget");
    // Bound retained CPU pixels. Scene TextureRef values own their upload copies;
    // GPU resources/fences are managed separately by the renderer. Do not erase
    // slots or alter hashes/indices already captured by a scene or descriptor.
    while (normal_state.world_bytes > pixel_budget - page_pixel_bytes) {
        size_t victim = normal_state.pages.size();
        for (size_t i = 0; i < normal_state.pages.size(); ++i) {
            const auto &candidate = normal_state.pages[i];
            if (i != page_index && candidate.loaded && candidate.pixel_bytes &&
                (victim == normal_state.pages.size() ||
                 candidate.last_use < normal_state.pages[victim].last_use))
                victim = i;
        }
        if (victim == normal_state.pages.size())
            throw std::runtime_error("World-normal resident byte accounting is inconsistent");
        auto &old = normal_state.pages[victim];
        for (int index : old.normal_indices)
            std::vector<std::uint32_t>().swap(overrides.normal_textures.at(size_t(index)).pixels32);
        normal_state.world_bytes -= old.pixel_bytes;
        old.loaded = false;
        if (overrides.log.is_open())
            overrides.log << "{\"event\":\"world_normal_page_evicted\",\"page\":" << victim
                          << ",\"resident_bytes\":" << normal_state.world_bytes << "}\n";
    }
    if (!page.initialized) {
        if (overrides.normal_textures.size() + parsed.pack.images.size() >
            size_t(std::numeric_limits<int>::max()))
            throw std::runtime_error("World-normal index overflow");
        for (const auto &image : parsed.pack.images) {
            const int index = int(overrides.normal_textures.size());
            OverrideTexture texture{};
            texture.name = image.name;
            texture.width = image.width;
            texture.height = image.height;
            texture.hash = image.hash;
            overrides.normal_textures.push_back(std::move(texture));
            page.normal_indices.push_back(index);
            normal_state.world_images.emplace(index, page_index);
        }
        page.local_bindings = parsed.bindings;
        page.pixel_bytes = page_pixel_bytes;
        page.initialized = true;
    }
    for (size_t i = 0; i < parsed.pack.images.size(); ++i)
        overrides.normal_textures.at(size_t(page.normal_indices[i])).pixels32 =
            std::move(parsed.pack.images[i].pixels);
    for (const auto &[key, normal_index] : parsed.bindings) {
        // A stock authored binding remains authoritative even if this page contains
        // an automatic estimate of the same texture. Explicit authored exclusions win.
        if (!normal_state.authored.count(key))
            normal_state.bindings.at(key) = normal_index == mw34::materials::no_normal
                                                ? -1
                                                : page.normal_indices.at(normal_index);
    }
    normal_state.world_bytes += page_pixel_bytes;
    page.loaded = true;
    if (overrides.log.is_open())
        overrides.log << "{\"event\":\"world_normal_page_loaded\",\"page\":" << page_index
                      << ",\"images\":" << parsed.pack.images.size()
                      << ",\"resident_bytes\":" << normal_state.world_bytes << "}\n";
}

void surface_normals_require_image(int index) {
    if (index < 0 || !mw34::materials::normal_maps_enabled())
        return;
    const auto found = surface_normals.world_images.find(index);
    if (found != surface_normals.world_images.end())
        surface_normals_load_page(found->second);
}
