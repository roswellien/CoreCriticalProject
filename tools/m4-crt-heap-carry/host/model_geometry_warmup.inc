// Move immutable replacement geometry uploads into the first world scene.
// No extra draw, pose, texture binding or guest call is introduced.
bool model_geometry_prewarmed{};
void model_geometry_prewarm(mw34::vkscene::Scene& scene) {
    static const bool enabled=[] {
        const char* value=std::getenv("MW34_MODEL_GEOMETRY_PREWARM");
        if(!value || !*value || !std::strcmp(value,"1"))return true;
        if(!std::strcmp(value,"0"))return false;
        throw std::runtime_error("MW34_MODEL_GEOMETRY_PREWARM must be 0 or 1");
    }();
    const auto& models=override_state();
    if(!enabled || model_geometry_prewarmed || !models.loaded ||
       !mw34::vkscene::Renderer::gpu_models() || scene.frontend_canvas ||
       scene.hud || !scene.world_eye_valid)return;
    constexpr std::uint64_t budget=64ULL*1024*1024;
    std::uint64_t bytes=0;
    unsigned skipped=0;
    for(const auto& batch:models.batches) {
        if(!batch.geometry)continue; // Animated donor geometry retains its live path.
        const auto required=std::uint64_t(batch.geometry->vertices.size())*
            sizeof(mw34::vkscene::ModelVertex);
        if(required>budget-bytes){++skipped;continue;}
        scene.model_warmup.push_back(batch.geometry);
        bytes+=required;
    }
    model_geometry_prewarmed=true;
    std::fprintf(stderr,"Model geometry warmup: %zu immutable batches, %llu bytes; %u over budget\n",
        scene.model_warmup.size(),(unsigned long long)bytes,skipped);
}
