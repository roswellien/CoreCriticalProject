// Optional first-world GPU preparation from already validated resident materials.
// It changes resource readiness only: no new draw or material binding is emitted.
void surface_texture_prewarm(mw34::vkscene::Scene& scene) {
    static const bool enabled = [] {
        const char* value=std::getenv("MW34_TEXTURE_PREWARM");
        if(!value || !*value || std::strcmp(value,"0")==0)return false;
        if(std::strcmp(value,"1")==0)return true;
        throw std::runtime_error("MW34_TEXTURE_PREWARM must be 0 or 1");
    }();
    if(!enabled || !surface_normals.loaded || surface_normals.gpu_prewarmed ||
       scene.frontend_canvas || !scene.world_eye_valid)return;
    namespace vs=mw34::vkscene;
    // Full RGBA8 mip-chain cost bounds additional preparations, including AF1.
    // Visible scene textures retain their existing allocation/upload path.
    std::uint64_t remaining=256ULL*1024*1024,preparedBytes=0;
    unsigned albedos=0,normals=0,budgetSkipped=0;
    std::set<int> normalIndices;
    auto already_bound=[&](std::uint64_t key){return std::any_of(scene.textures.begin(),scene.textures.end(),
        [&](const vs::TextureRef& ref){return ref.key==key;});};
    auto cost=[](unsigned w,unsigned h){std::uint64_t bytes=0;
        for(;;){bytes+=std::uint64_t(w)*h*4;if(w==1&&h==1)return bytes;w=std::max(1U,w/2);h=std::max(1U,h/2);}};
    for(auto& surface:host.vsurfaces){
        if(!surface.guest || !surface.bytes || surface.locks || !host.com_object(surface.guest) ||
           !(surface.caps&DDSCAPS_TEXTURE) || (surface.caps&(DDSCAPS_3DDEVICE|DDSCAPS_PRIMARYSURFACE|DDSCAPS_BACKBUFFER|DDSCAPS_ZBUFFER)) || surface.bpp!=16)continue;
        auto found=surface_normals.cache.find(surface.guest);
        if(found==surface_normals.cache.end())continue;
        const auto& proof=found->second;
        const unsigned format=surface.tex_masks[0]==0xf800?1:surface.tex_masks[0]==0x7c00?2:surface.tex_masks[0]==0x0f00?3:0;
        if(!proof.world || !proof.registered || !format || proof.version!=surface.version ||
           proof.width!=surface.width || proof.height!=surface.height || proof.pitch!=surface.pitch ||
           proof.memory!=surface.mem || proof.format!=format)continue;
        if(proof.index>=0)normalIndices.insert(proof.index);
        if(already_bound(surface.guest) || (host.sren&&host.sren->sent_current(surface.guest,surface.version,surface.width,surface.height)))continue;
        const auto bytes=cost(surface.width,surface.height);
        if(bytes>remaining){++budgetSkipped;continue;}
        gpu_sync(surface.guest);
        if(proof.version!=surface.version)continue;
        vs::TextureRef ref{};ref.key=surface.guest;ref.hash=surface.version;ref.width=surface.width;ref.height=surface.height;
        ref.format=format==1?vs::TexFormat::rgb565:format==2?vs::TexFormat::argb1555:vs::TexFormat::argb4444;
        ref.pixels.resize(size_t(surface.width)*surface.height);
        for(unsigned y=0;y<surface.height;++y)
            surface_read(surface,y*surface.pitch,ref.pixels.data()+size_t(y)*surface.width,surface.width*2);
        scene.textures.push_back(std::move(ref));remaining-=bytes;preparedBytes+=bytes;++albedos;
    }
    const auto& overrides=override_state();
    for(int index:normalIndices){
        if(size_t(index)>=overrides.normal_textures.size())throw std::runtime_error("Prepared world normal index outside its catalog");
        const auto& texture=overrides.normal_textures[size_t(index)];
        const std::uint64_t key=0x42574e524d000000ULL+unsigned(index);
        if(already_bound(key) || (host.sren&&host.sren->sent_current(key,texture.hash,texture.width,texture.height)))continue;
        const auto bytes=cost(texture.width,texture.height);
        if(bytes>remaining){++budgetSkipped;continue;}
        surface_normals_require_image(index);
        vs::TextureRef ref{};ref.key=key;ref.hash=texture.hash;ref.width=texture.width;ref.height=texture.height;
        ref.format=vs::TexFormat::rgba8888;ref.pixels32=texture.pixels32;
        scene.textures.push_back(std::move(ref));remaining-=bytes;preparedBytes+=bytes;++normals;
    }
    surface_normals.gpu_prewarmed=true;
    std::fprintf(stderr,"Texture warmup: %u albedo, %u normal, %llu additional mip bytes at first world scene; %u over budget\n",
        albedos,normals,(unsigned long long)preparedBytes,budgetSkipped);
}
