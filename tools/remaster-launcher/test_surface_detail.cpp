// Reuse authored scene builders, then exercise the actual optional GPU paths.
#define main legacy_sun_fixture_main
#include "test_sun_lighting.cpp"
#undef main
struct DetailCaptureFixture:CaptureFixture {
    enum {WideWorld=1,WideZoom=2,D3DPT_POINTLIST=1,D3DRENDERSTATE_ZENABLE=7,
          D3DRENDERSTATE_ZWRITEENABLE=14,D3DRENDERSTATE_ALPHATESTENABLE=15,
          D3DRENDERSTATE_ALPHABLENDENABLE=27,D3DRENDERSTATE_FOGENABLE=28};
    struct D3DCmd {
        bool model{};unsigned hud_role{WideWorld},flags{4},texture{1};
        std::shared_ptr<const std::vector<unsigned>>state_snapshot;
        std::vector<unsigned char>vertices;
        std::shared_ptr<const mw34::sun::Tl>sun_tl,sky_view;
    };
    unsigned world_cell_depth{},role{3};
    struct VSurfaceRec{}surface;
    bool override_suppress_draw(){return false;}
    VSurfaceRec*vsurface(unsigned){return &surface;}
    unsigned surface_detail_role(VSurfaceRec&){return role;}
    bool surface_normal_registered(VSurfaceRec&){return true;}
    bool surface_world_normal_registered(VSurfaceRec&){return true;}
    bool sun_camera_world(OverrideMatrix&m){m=identity();return true;}
    float wide_float(unsigned){return 1;}
    #include "sun_tl_capture_stage.inc"
    void check(){
        D3DCmd d;auto rs=std::make_shared<std::vector<unsigned>>(256,0);
        (*rs)[D3DRENDERSTATE_ZENABLE]=(*rs)[D3DRENDERSTATE_ZWRITEENABLE]=1;d.state_snapshot=rs;
        Tl v{0,0,.5f,1,0xffffffff,0xff000000,0,0};
        auto*b=reinterpret_cast<unsigned char*>(&v);d.vertices.assign(b,b+sizeof(v));
        sun_capture_tl(d);require(!d.sun_tl,"Cloud registration must never admit the sky as opaque lit geometry");
        role=1;sun_capture_tl(d);require(bool(d.sun_tl),"Registered water must retain authenticated world lighting");
    }
};
int main(){try{
    _putenv_s("MW34_WATER_DETAIL","1");_putenv_s("MW34_CLOUD_DETAIL","1");
    _putenv_s("MW34_WATER_DETAIL_SCALE","0.2");
    _putenv_s("MW34_WATER_DETAIL_STRENGTH","1");_putenv_s("MW34_CLOUD_DETAIL_STRENGTH","1");
    require(legacy_sun_fixture_main()==0,"Existing sun fixtures failed");
    DetailCaptureFixture{}.check();
    Renderer r;
    auto image=[&](unsigned role,double time,bool mask,bool cloud=false,float uv_offset=0,bool split_mask=false){
        auto s=scene();s.detail_time=time;
        TextureRef tex{};tex.key=1000+(mask?1:0)+(split_mask?2:0);tex.hash=tex.key;tex.width=tex.height=64;tex.format=TexFormat::rgba8888;
        for(unsigned y=0;y<64;++y)for(unsigned x=0;x<64;++x){
            const int slope=int(std::lround(80*std::sin(x*6.283185307179586/64)));
            tex.pixels32.push_back(unsigned(128+slope)|128u<<8|255u<<16|((mask||(split_mask&&x<32))?0u:255u)<<24);
        }
        s.textures.push_back(tex);auto d=quad(s,true,false,true);d.detail_role=role;d.normal_texture=0;
        auto g=std::make_shared<ModelGeometry>(*d.model->geometry);g->key=100+unsigned(uv_offset)*100;g->hash=g->key;
        for(auto&v:g->vertices){v.u=(v.x+1)*.5f+uv_offset;v.v=(v.y+1)*.5f;}
        // The world bridge deliberately keeps UV/color from the original TL
        // stream; only replacement-model draws take attributes from geometry.
        for(size_t j=0;j<g->vertices.size();++j){std::memcpy(s.vertices.data()+j*32+24,&g->vertices[j].u,4);std::memcpy(s.vertices.data()+j*32+28,&g->vertices[j].v,4);}
        auto model=std::make_shared<ModelInstance>(*d.model);model->geometry=g;d.model=model;
        if(cloud){
            d.model.reset();d.sky=1;
            auto light=std::make_shared<mw34::sun::Tl>();
            light->camera_world={1,0,0,0,0,1,0,0,0,0,1,0};light->projection={1,40,-40,32,32,.1f};d.sun_tl=light;
            s.vertices.clear();
            for(auto p:std::array<std::array<float,2>,6>{{{0,0},{64,0},{64,64},{0,0},{64,64},{0,64}}}){
                Tl v{p[0],p[1],.9f,.1f,0xff808080,0xff000000,p[0]/64,p[1]/64};
                auto*b=reinterpret_cast<const unsigned char*>(&v);s.vertices.insert(s.vertices.end(),b,b+sizeof(v));
            }
        }
        s.draws[0]=d;r.render(s);return s.color;
    };
    const auto water=image(1,0,false),moving=image(1,100,false);
    if(mw34::materials::normal_maps_enabled()){
        require(water!=moving,"Water phase must move highlights");
        require(water==image(2,0,false),"Full-water surf must share the water field");
        const auto edge=image(2,0,false,false,2,true);
        require(water==edge,"Surf masks must clamp at atlas edges while ripple RGB repeats");
        require(image(2,0,true)==image(2,100,true),"Masked foam/sand must not animate");
        require(image(3,0,false,true)!=image(0,0,false,true),"Cloud relief must affect sky lighting");
        require(image(3,0,true,true)==image(0,0,true,true),"Zero cloud mask must preserve the original sky");
    }else{
        require(water==moving&&water==image(0,0,false),"Global maps-off must bypass water detail");
        require(image(3,0,false,true)==image(0,0,false,true),"Global maps-off must bypass cloud detail");
    }
    // Repeat wrap at a full integer tile period, including both counterflows.
    require(water==image(1,2000,false),"Long-session phase wrap must be seamless");
    std::cout<<"Surface detail GPU fixtures pass: phase, surf continuity, protected masks, cloud response and disabled controls\n";
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
