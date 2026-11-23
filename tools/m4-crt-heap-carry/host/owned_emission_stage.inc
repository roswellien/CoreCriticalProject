void override_load_emission(const OverrideModel &model, size_t first, size_t end) {
    std::string environment;
    if (model.resource && *model.resource) {
        environment = "MW34_CHASSIS_" + std::string(model.resource);
        for (char &letter : environment)
            if (letter >= 'a' && letter <= 'z')
                letter = char(letter - 'a' + 'A');
        environment += model.lod ? "_LOD1_EMISSION" : "_EMISSION";
    } else if (model.texture_env && std::strlen(model.texture_env) >= 9) {
        environment = std::string(model.texture_env).substr(0, std::strlen(model.texture_env) - 9) +
                      "_EMISSION";
    } else {
        return;
    }
    const char *path = std::getenv(environment.c_str());
    if (!path || !*path)
        return;
    std::ifstream input(std::filesystem::path(additional_skin_wide(path)), std::ios::binary);
    if (!input)
        throw std::runtime_error("Selected owned emission sidecar is missing: " + environment);
    auto &state = override_state();
    std::vector<mw34::emission::Binding> bindings;
    for (size_t index = first; index < end; ++index) {
        const auto &batch = state.batches[index];
        if (batch.texture < 0 || size_t(batch.texture) >= state.textures.size())
            throw std::runtime_error("Owned emission requires its color binding");
        const auto &texture = state.textures[size_t(batch.texture)];
        bindings.push_back({batch.owner, texture.name, texture.width, texture.height,
                            mw34::materials::normal_hash(
                                reinterpret_cast<const unsigned char *>(texture.pixels.data()),
                                texture.pixels.size() * 2),
                            batch.lo, batch.hi, batch.vertex_bones.empty()});
    }
    auto records = mw34::emission::read(
        input, mw34::materials::compute_mesh_uv_hash(state.batches, first, end), bindings);
    const auto count = records.size();
    for (auto &record : records) {
        auto &batch = state.batches.at(first + record.batch);
        batch.emission_texture = batch.texture;
        batch.emission = std::make_shared<const mw34::emission::Record>(std::move(record));
    }
    state.log << "{\"event\":\"owned_emission_loaded\",\"model\":\"" << model.id
              << "\",\"lod\":" << model.lod << ",\"records\":" << count << "}\n";
}
