// The authored world-warmup fixture supplies the same observed surface contracts.
#define main world_texture_fixture_main
#include "surface_texture_warmup_checks.cpp"
#undef main
struct ResidentFixture:Fixture {
    Surface* vsurface(unsigned guest){for(auto& s:host.vsurfaces)if(s.guest==guest && s.alive)return &s;return nullptr;}
#include "../native-overrides/surface_resident_texture_warmup.inc"
};
int main(int argc,char** argv){
    const bool off=argc>1 && std::strcmp(argv[1],"off")==0;
    const bool invalid=argc>1 && std::strcmp(argv[1],"invalid")==0;
    _putenv_s("MW34_RESIDENT_TEXTURE_PREWARM",off?"0":invalid?"2":"1");
    using mw34::vkscene::Scene;
    if(off||invalid){ResidentFixture f;Scene scene;bool rejected=false;
        try{f.surface_resident_texture_prewarm(scene);}catch(const std::runtime_error&){rejected=true;}
        assert(rejected==invalid && scene.textures.empty() && f.reads==0);return 0;}
    {ResidentFixture f;Scene scene;f.surface_normals.cache[1].world=false;f.surface_normals.cache[1].registered=false;
        f.surface_resident_texture_prewarm(scene);assert(scene.textures.size()==1 && f.reads==4);
        assert(scene.textures[0].pixels==std::vector<std::uint16_t>(16,0x5a5a));
        Scene next;f.surface_resident_texture_prewarm(next);assert(next.textures.empty());}
    for(unsigned change=0;change<22;++change){ResidentFixture f;Scene scene;auto& s=f.host.vsurfaces[0];
        switch(change){
        case 0:s.locks=1;break;case 1:s.alive=false;break;case 2:s.caps|=DDSCAPS_3DDEVICE;break;
        case 3:s.caps|=DDSCAPS_PRIMARYSURFACE;break;case 4:s.caps|=DDSCAPS_BACKBUFFER;break;case 5:s.caps|=DDSCAPS_ZBUFFER;break;
        case 6:s.bpp=32;break;case 7:++s.version;break;case 8:++s.width;break;case 9:++s.height;break;
        case 10:++s.pitch;break;case 11:++s.mem;break;case 12:s.tex_masks[0]=0;break;
        case 13:f.surface_normals.cache.clear();break;case 14:s.width=0;break;case 15:s.height=0;break;
        case 16:s.guest=0;break;case 17:s.mem=0;break;case 18:s.pitch=1;break;case 19:s.mem=0xfffffff8;break;
        case 20:s.width=4097;break;case 21:s.caps=0;break;
        }
        f.surface_resident_texture_prewarm(scene);assert(scene.textures.empty() && f.reads==0 && f.synchronizations==0);
    }
    {ResidentFixture f;Scene scene;f.change_during_sync=true;f.surface_resident_texture_prewarm(scene);
        assert(scene.textures.empty() && f.reads==0);}
    {ResidentFixture f;Scene scene;f.renderer.resident[1]={1,4,4};f.surface_resident_texture_prewarm(scene);
        assert(scene.textures.empty() && f.reads==0);}
    {ResidentFixture f;Scene scene;scene.textures.push_back({1});f.surface_resident_texture_prewarm(scene);
        assert(scene.textures.size()==1 && f.reads==0);}
    {ResidentFixture f;Scene scene;scene.frontend_canvas=true;f.surface_resident_texture_prewarm(scene);
        assert(!f.resident_texture_prewarmed);scene.frontend_canvas=false;scene.world_eye_valid=false;
        f.surface_resident_texture_prewarm(scene);assert(!f.resident_texture_prewarmed);scene.world_eye_valid=true;
        f.surface_resident_texture_prewarm(scene);assert(scene.textures.size()==1);}
    // Full mip accounting: three 4096-square images and a 1x1 consume exactly
    // 256 MiB. Newer versions win equal-size ties; neither the fourth large
    // image nor an extra 2048-square image may exceed that budget.
    {ResidentFixture f;Scene scene;f.host.vsurfaces.clear();f.surface_normals.cache.clear();
        for(unsigned id=1;id<=6;++id){Surface s;s.guest=id;s.mem=id*0x4000000;s.version=id;
            s.width=s.height=id==1?2048:id==6?1:4096;s.pitch=s.width*2;f.host.vsurfaces.push_back(s);
            Proof p;p.width=s.width;p.height=s.height;p.pitch=s.pitch;p.memory=s.mem;p.version=id;f.surface_normals.cache[id]=p;}
        f.surface_resident_texture_prewarm(scene);assert(scene.textures.size()==4);
        assert(scene.textures[0].key==5 && scene.textures[1].key==4 && scene.textures[2].key==3 && scene.textures[3].key==6);
        assert(f.reads==3*4096+1);}
    std::puts("Resident texture contracts: ownership, exclusions, budget and largest-first ordering pass");
}
