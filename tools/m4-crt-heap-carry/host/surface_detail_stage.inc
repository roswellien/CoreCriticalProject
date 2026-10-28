// Optional exact-pixel registrations. Upgrade-derived data stays outside game
// banks; no original pixels, UVs, alpha planes or animation frames are changed.
void surface_detail_load() {
    // Roles 1/2/3 select water, surf and cloud catalogs. Disabled roles require
    // no input; an enabled role must have a bounded, readable configured pack.
    auto &normal_state = surface_normals;
    for (unsigned role = 1; role <= 3; ++role) {
        if (!mw34::detail::enabled(role))
            continue;
        const char *name = role == 1   ? "MW34_WATER_NORMALS"
                           : role == 2 ? "MW34_SURF_NORMALS"
                                       : "MW34_CLOUD_NORMALS";
        const char *catalog_path = std::getenv(name);
        if (!catalog_path || !*catalog_path)
            throw std::runtime_error(std::string("Enabled surface detail requires ") + name);
        if (std::filesystem::file_size(catalog_path) > 16ULL * 1024 * 1024)
            throw std::runtime_error("Surface detail pack exceeds 16 MiB budget");
        std::ifstream file(catalog_path, std::ios::binary);
        if (!file)
            throw std::runtime_error("Configured surface detail pack is missing");
        if (!mw34::materials::normal_maps_enabled()) {
            // Keep role/identity registration while skipping image payload decoding.
            // An image index of -1 here means maps are disabled, not an unknown role.
            for (const auto &[key, page_normal_index] :
                 mw34::materials::read_surface_normal_header(file)) {
                if (normal_state.authored.count(key) ||
                    !normal_state.detail_roles.emplace(key, role).second)
                    throw std::runtime_error("Conflicting surface detail registration");
                normal_state.bindings[key] = -1;
                normal_state.authored.insert(key);
            }
        } else {
            auto parsed = mw34::materials::read_surface_normals(file);
            auto &overrides = override_state();
            // Sidecar indices are local to this pack; append images once and translate
            // bindings into the host texture list. Active detail rejects absent images.
            const size_t texture_base_index = overrides.normal_textures.size();
            if (texture_base_index + parsed.pack.images.size() >
                size_t(std::numeric_limits<int>::max()))
                throw std::runtime_error("Surface detail index overflow");
            for (const auto &[key, page_normal_index] : parsed.bindings) {
                if (page_normal_index == mw34::materials::no_normal ||
                    normal_state.authored.count(key) ||
                    !normal_state.detail_roles.emplace(key, role).second)
                    throw std::runtime_error("Conflicting or empty surface detail registration");
                normal_state.bindings[key] = int(texture_base_index + page_normal_index);
                normal_state.authored.insert(key);
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
                overrides.log << "{\"event\":\"surface_detail_loaded\",\"role\":" << role
                              << ",\"bindings\":" << parsed.bindings.size()
                              << ",\"images\":" << parsed.pack.images.size() << "}\n";
        }
    }
}
unsigned surface_detail_role(VSurfaceRec &surface) {
    // Resolve the current surface version first. Role metadata belongs to the
    // same cache entry as its exact-pixel normal binding, not merely its address.
    surface_normal_binding(surface);
    const auto cached_surface = surface_normals.cache.find(surface.guest);
    return cached_surface == surface_normals.cache.end() ? 0 : cached_surface->second.detail;
}
