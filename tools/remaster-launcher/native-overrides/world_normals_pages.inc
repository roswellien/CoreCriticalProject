// Optional automatic world normals reuse validated BWSNR2 pages. Header keys
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
        if (size > 16 * 1024 * 1024 || package_bytes > 512 * 1024 * 1024)
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
void surface_normals_load_page(size_t page_index) {
    // Reopen on first use and verify the full key set against the admitted header.
    // This catches changed key membership, not a cryptographic pin of image bytes.
    auto &normal_state = surface_normals;
    auto &page = normal_state.pages.at(page_index);
    if (page.loaded)
        return;
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
    if (normal_state.world_bytes + page_pixel_bytes > 512 * 1024 * 1024)
        throw std::runtime_error("Resident automatic normals exceed budget");
    auto &overrides = override_state();
    const auto texture_base_index = overrides.normal_textures.size();
    // Catalog indices are page-local. Offset them into the host's append-only
    // normal-texture list while preserving the explicit no_normal sentinel.
    if (texture_base_index + parsed.pack.images.size() > size_t(std::numeric_limits<int>::max()))
        throw std::runtime_error("World-normal index overflow");
    for (auto &image : parsed.pack.images) {
        OverrideTexture texture{};
        texture.name = std::move(image.name);
        texture.width = image.width;
        texture.height = image.height;
        texture.hash = image.hash;
        texture.pixels32 = std::move(image.pixels);
        overrides.normal_textures.push_back(std::move(texture));
    }
    for (const auto &[key, normal_index] : parsed.bindings) {
        // A stock authored binding remains authoritative even if this page contains
        // an automatic estimate of the same texture. Explicit authored exclusions win.
        if (!normal_state.authored.count(key))
            normal_state.bindings.at(key) = normal_index == mw34::materials::no_normal
                                                ? -1
                                                : int(texture_base_index + normal_index);
    }
    normal_state.world_bytes += page_pixel_bytes;
    page.loaded = true;
    if (overrides.log.is_open())
        overrides.log << "{\"event\":\"world_normal_page_loaded\",\"page\":" << page_index
                      << ",\"images\":" << parsed.pack.images.size()
                      << ",\"resident_bytes\":" << normal_state.world_bytes << "}\n";
}
