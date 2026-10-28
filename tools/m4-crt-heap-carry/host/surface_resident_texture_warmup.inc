// Prepare the largest already-resident guest textures at the first world scene.
// This supplements registered world materials; it never creates a draw or changes
// a binding. Full RGBA8 mip cost bounds extra residency to 256 MiB per process.
bool resident_texture_prewarmed{};
void surface_resident_texture_prewarm(mw34::vkscene::Scene& scene) {
    static const bool enabled=[] {
        const char* value=std::getenv("MW34_RESIDENT_TEXTURE_PREWARM");
        if(!value || !*value || std::strcmp(value,"0")==0)return false;
        if(std::strcmp(value,"1")==0)return true;
        throw std::runtime_error("MW34_RESIDENT_TEXTURE_PREWARM must be 0 or 1");
    }();
    if(!enabled || resident_texture_prewarmed || !surface_normals.loaded ||
       scene.frontend_canvas || !scene.world_eye_valid)return;
    namespace vs=mw34::vkscene;
    auto eligible=[&](const auto& surface) {
        if(!surface.guest || !surface.bytes || surface.locks || !surface.width || !surface.height ||
           surface.width>4096 || surface.height>4096 || surface.pitch<surface.width*2 ||
           std::uint64_t(surface.mem)+std::uint64_t(surface.pitch)*(surface.height-1)+surface.width*2>0x100000000ULL ||
           !host.com_object(surface.guest) || !(surface.caps&DDSCAPS_TEXTURE) || surface.bpp!=16 ||
           (surface.caps&(DDSCAPS_3DDEVICE|DDSCAPS_PRIMARYSURFACE|DDSCAPS_BACKBUFFER|DDSCAPS_ZBUFFER)))return false;
        const auto found=surface_normals.cache.find(surface.guest);
        if(found==surface_normals.cache.end())return false;
        const auto& proof=found->second;
        const unsigned format=surface.tex_masks[0]==0xf800?1:surface.tex_masks[0]==0x7c00?2:surface.tex_masks[0]==0x0f00?3:0;
        if(!format || proof.version!=surface.version || proof.width!=surface.width ||
           proof.height!=surface.height || proof.pitch!=surface.pitch || proof.memory!=surface.mem || proof.format!=format)return false;
        return !std::any_of(scene.textures.begin(),scene.textures.end(),[&](const vs::TextureRef& ref){return ref.key==surface.guest;}) &&
            !(host.sren && host.sren->current(surface.guest,surface.version,surface.width,surface.height));
    };
    struct Candidate {unsigned guest;std::uint64_t bytes,version;};
    std::vector<Candidate> candidates;
    for(const auto& surface:host.vsurfaces) {
        if(!eligible(surface))continue;
        std::uint64_t bytes=0;
        for(unsigned w=surface.width,h=surface.height;;w=std::max(1U,w/2),h=std::max(1U,h/2)) {
            bytes+=std::uint64_t(w)*h*4;if(w==1&&h==1)break;
        }
        candidates.push_back({surface.guest,bytes,surface.version});
    }
    // Allocation order previously spent the budget on small textures before the
    // large cockpit panels. Size ordering targets the costly first-use uploads.
    std::sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b){
        if(a.bytes!=b.bytes)return a.bytes>b.bytes;
        return a.version!=b.version?a.version>b.version:a.guest<b.guest;
    });
    std::uint64_t remaining=256ULL*1024*1024,preparedBytes=0;
    unsigned prepared=0,budgetSkipped=0;
    for(const auto& candidate:candidates) {
        if(candidate.bytes>remaining){++budgetSkipped;continue;}
        auto* surface=vsurface(candidate.guest);
        if(!surface || surface->version!=candidate.version || !eligible(*surface))continue;
        const auto version=surface->version;
        const unsigned width=surface->width,height=surface->height,pitch=surface->pitch,
            memory=surface->mem,format=surface->tex_masks[0];
        gpu_sync(surface->guest);
        // Synchronization can invalidate a cached content proof. Recheck every
        // identity component before reading or publishing the prepared pixels.
        surface=vsurface(candidate.guest);
        if(!surface || surface->version!=version || surface->width!=width || surface->height!=height ||
           surface->pitch!=pitch || surface->mem!=memory || surface->tex_masks[0]!=format || !eligible(*surface))continue;
        vs::TextureRef ref{};ref.key=surface->guest;ref.hash=surface->version;
        ref.width=surface->width;ref.height=surface->height;
        ref.format=surface->tex_masks[0]==0xf800?vs::TexFormat::rgb565:
            surface->tex_masks[0]==0x7c00?vs::TexFormat::argb1555:vs::TexFormat::argb4444;
        ref.pixels.resize(size_t(ref.width)*ref.height);
        for(unsigned y=0;y<ref.height;++y)
            surface_read(*surface,y*surface->pitch,ref.pixels.data()+size_t(y)*ref.width,ref.width*2);
        scene.textures.push_back(std::move(ref));remaining-=candidate.bytes;
        preparedBytes+=candidate.bytes;++prepared;
    }
    resident_texture_prewarmed=true;
    std::fprintf(stderr,"Large resident texture warmup: %u textures, %llu additional mip bytes; %u over budget\n",
        prepared,(unsigned long long)preparedBytes,budgetSkipped);
}
