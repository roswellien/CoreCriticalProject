// Authored fixtures only: normal math, directional light, fog and GPU binding.
#define NOMINMAX
#include "vk_scene.hpp"
#include "material_normals.hpp"
#include "sun_camera_binding.hpp"
#include "campaign_lighting.hpp"
#include <iostream>
#include <set>

using namespace mw34::vkscene;
static void require(bool value,const char* what){if(!value)throw std::runtime_error(what);}
static std::array<double,16> identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};}
// Exercise the actual capture adapter with authored memory/camera contracts.
// The original distance-camera authentication is mocked here; it has its own fixture.
struct CaptureFixture {
    using OverrideMatrix=std::array<double,16>;
    std::map<unsigned,unsigned> words;
    bool preview{},worldCamera{true},zoomCamera{};unsigned zoomOwner{};
    bool readable(unsigned,unsigned)const{return true;}
    unsigned load(unsigned a){auto p=words.find(a);if(p==words.end())throw std::runtime_error("Unexpected guest read in sun capture fixture");return p->second;}
    bool frontend_on()const{return preview;}
    bool override_status_preview()const{return false;}
    bool distance_world(unsigned,unsigned)const{return worldCamera;}
    unsigned distance_zoom_owner()const{return zoomOwner;}
    bool distance_zoom(unsigned,unsigned)const{return zoomCamera;}
    static OverrideMatrix override_identity(){return identity();}
    static OverrideMatrix override_product(const OverrideMatrix&a,const OverrideMatrix&b){OverrideMatrix c{};for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)for(unsigned k=0;k<4;++k)c[i*4+j]+=a[i*4+k]*b[k*4+j];return c;}
    OverrideMatrix override_matrix(unsigned a){OverrideMatrix m=identity();for(unsigned row=0;row<3;++row)for(unsigned col=0;col<4;++col){const unsigned bits=load(a+4*(col*3+row));float value;std::memcpy(&value,&bits,4);m[row*4+col]=value;}return m;}
    #include "sun_lighting_stage.inc"
    void activate(){
        words={{0x7402f4,0x1000},{0x5f4c8c,0x2000},{0x2004,0x3000},{0x3034,1},{0x3038,0x1000}};
        const std::array<float,12> camera{0,1,0,-1,0,0,0,0,1,0,0,0};
        for(unsigned j=0;j<12;++j){unsigned bits;std::memcpy(&bits,&camera[j],4);words[0x1044+4*j]=bits;}
        for(unsigned j=0;j<12;++j){unsigned bits=words.at(0x1044+4*j);if(j>=3&&j<9)bits^=0x80000000U;words[0x73fc00+4*j]=bits;}
        for(unsigned j=0;j<12;++j)words[0x73fbc0+4*j]=words.at(0x73fc00+4*j);
        sun_view_binding.capture(0x1044,sun_view_words(0x1044),sun_view_words(0x73fc00),sun_view_words(0x73fbc0));
    }
    void camera_only(){
        activate();
        require(sun_view_capture_enabled(),"Independent camera activation was disabled");
        const auto original=words;
        ::SetLastError(5432);const unsigned saved=_mm_getcsr();_mm_setcsr(0x5f81);
        OverrideMatrix matrix{};
        {SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
         require(sun_camera_world(matrix),"Authenticated lighting-Off view was rejected");}
        require(words==original&&::GetLastError()==5432&&_mm_getcsr()==0x5f81,"Camera observation changed guest inputs or FP/LastError");
        _mm_setcsr(saved);
        auto changed=sun_view_words(0x73fbc0);changed[0]^=1;
        bool rejected=false;try{sun_view_binding.validate(changed);}catch(...){rejected=true;}
        require(rejected,"Independent capture accepted changed inverse words");
    }
    void run(){
        activate();
        auto worldBinding=sun_view_binding;sun_view_binding.source=0x9000;
        ModelInstance effect{};sun_capture_world(effect,0);require(!effect.sun_eligible,"Temporary original effect camera receives no world light");sun_view_binding=worldBinding;
        auto changed=sun_view_words(0x73fc00);changed[0]^=1;
        bool badCopy=false;try{mw34::sun::CameraBinding bad;bad.capture(0x1044,sun_view_words(0x1044),changed,sun_view_words(0x73fbc0));}catch(...){badCopy=true;}
        require(badCopy,"One-bit original camera copy mismatch accepted");
        // Only activation from the authenticated world camera receives world light.
        // The source camera remains mutable after renderer activation. A later
        // one-ULP node update cannot change the already activated view matrix.
        words[0x1044+4]^=1;
        words[0x73fc00+4]^=1;
        auto before=words;ModelInstance i{};i.camera={0,1,0,0,1,0,0,0,0,0,-1,0};
        ::SetLastError(5432);const unsigned mxcsr=_mm_getcsr();_mm_setcsr(0x5f81);
        sun_capture_world(i,0xdead);require(i.sun_eligible&&i.sun_normal==mw34::sun::normal_matrix(identity()),"Actual capture cancels camera rotation");
        require(_mm_getcsr()==0x5f81&&::GetLastError()==5432,"Sun capture preserves FP rounding/flags and LastError");_mm_setcsr(mxcsr);
        require(words==before,"Sun capture does not modify guest memory or request node cache");
        words[0x73fbc0+4]^=1;bool rejected=false;
        try{sun_capture_world(i,0);}catch(...){rejected=true;}
        require(rejected,"One-ULP inverse-view alteration bypassed exact activation check");
        words[0x73fbc0+4]^=1;
        i.sun_eligible=false;worldCamera=false;sun_capture_world(i,0);require(!i.sun_eligible,"Unauthenticated camera rejected");
        zoomOwner=0x4000;zoomCamera=true;words[0x4038]=0x5000;words[0x5038]=0x1000;
        sun_capture_world(i,0);require(i.sun_eligible,"Authenticated zoom uses bound camera");
        i.sun_eligible=false;preview=true;sun_capture_model(i,0,identity(),identity());require(!i.sun_eligible,"Frontend model excluded");
    }
};
static void math(){
    auto m=identity();auto n=mw34::sun::normal_matrix(m);require(n[0]==1&&n[5]==1&&n[10]==1,"Identity normal matrix");
    m[0]=2;m[5]=3;m[10]=4;n=mw34::sun::normal_matrix(m);
    require(n[0]==.5f&&std::abs(n[5]-1.f/3)<1e-7&&n[10]==.25f,"Inverse-transpose scale");
    m=identity();m[1]=2;n=mw34::sun::normal_matrix(m);
    require(n[0]==1&&n[4]==-2&&n[5]==1,"Shear inverse transpose");
    m=identity();m[0]=-1;n=mw34::sun::normal_matrix(m);require(n[0]==-1,"Mirrored normal transform");
    m[0]=0;bool rejected=false;try{mw34::sun::normal_matrix(m);}catch(...){rejected=true;}require(rejected,"Singular normal matrix rejected");
    mw34::sun::Settings s;s.azimuth=0;s.elevation=30;s.normals=true;
    const auto u=mw34::sun::uniform(n,s);require(std::abs(u.direction[1]-.5f)<1e-6,"Sun uses world +Y up");
    require(u.ambient[3]==0.f,"Normal mapping must not replace textured colour with normal diagnostics");
}
struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};
static Scene scene(){Scene s{};s.width=s.height=64;s.has_depth=true;s.color.assign(4096,0);s.depth.assign(4096,0);return s;}
static Draw quad(Scene& s,bool world,bool rotate,bool faceSun,bool fog=false){
    auto g=std::make_shared<ModelGeometry>();g->key=world?11:12;g->hash=g->key;
    g->vertices={{-1,-1,2,0,1,0,0,0},{1,-1,2,0,1,0,0,0},{1,1,2,0,1,0,0,0},
                 {-1,-1,2,0,1,0,0,0},{1,1,2,0,1,0,0,0},{-1,1,2,0,1,0,0,0}};
    auto i=std::make_shared<ModelInstance>();i->geometry=g;i->world=world;i->color=0xffffffff;
    i->camera=rotate?std::array<float,12>{0,-1,0,0,1,0,0,0,0,0,1,0}:std::array<float,12>{1,0,0,0,0,1,0,0,0,0,1,0};
    i->projection={1,40,40,32,32,.1f};i->sun_normal=mw34::sun::normal_matrix(identity());
    if(!faceSun)i->sun_normal[5]=-1;i->sun_eligible=true;
    Draw d{};d.count=6;d.texture=-1;d.model=i;d.scissor={{0,0},{64,64}};d.key.cull=1;d.key.zfunc=4;
    d.push.target[0]=d.push.target[1]=64;d.push.factor[0]=d.push.factor[1]=d.push.factor[2]=d.push.factor[3]=1;
    d.push.mode[0]=2|4|(fog?16:0);d.push.mode[1]=0x00000204; // texture * diffuse
    d.push.mode[2]=2;d.push.fog[2]=1;
    for(unsigned j=0;j<6;++j){Tl v{9000,9000,.5f,.5f,0xffff0000,fog?0u:0xff000000,0,0};
        const auto*p=reinterpret_cast<const unsigned char*>(&v);s.vertices.insert(s.vertices.end(),p,p+sizeof(v));}
    s.draws.push_back(d);s.order.push_back({false,0});return d;
}
#include "tests/temporal_source_fixture.inc"
int main(int argc,char**argv){try{
    if(argc>1&&std::string(argv[1])=="--temporal-source"){temporal_source_checks();return 0;}
    if(argc>1&&std::string(argv[1])=="--capture-only"){
        CaptureFixture{}.camera_only();std::cout<<"Independent camera authentication and FP preservation pass\n";return 0;
    }
    math();_putenv_s("MW34_GPU_MODELS","1");_putenv_s("MW34_SUN","1");_putenv_s("MW34_SUN_NORMALS","1");
    _putenv_s("MW34_SUN_AZIMUTH","0");_putenv_s("MW34_SUN_ELEVATION","30");
    _putenv_s("MW34_SUN_STRENGTH","1");_putenv_s("MW34_SUN_AMBIENT","0.25");
    CaptureFixture{}.run();
    _putenv_s("MW34_REMASTER_WIDTH","");_putenv_s("MW34_REMASTER_HEIGHT","");_putenv_s("MW34_REMASTER_AA","");_putenv_s("MW34_REMASTER_AF","");
    Renderer r;
    auto render=[&](bool world,bool rotate,bool facing,bool fog=false){auto s=scene();quad(s,world,rotate,facing,fog);r.render(s);return s.color[32*64+32];};
    const auto lit=render(true,false,true),rolled=render(true,true,true),dark=render(true,false,false);
    require(lit==rolled,"World sunlight must not rotate with the camera");
    require((lit&31)>(dark&31)+5,"Opposite normal receives ambient only");
    require(render(false,false,true)==lit,"Replacement model and world share the sun");
    require(render(true,false,true,true)==0x001f,"Fog follows sunlight");
    auto terrain=[&](bool turn,bool fog){auto s=scene();
        Draw d{};d.count=6;d.texture=-1;d.scissor={{0,0},{64,64}};d.key.cull=1;d.key.zfunc=4;
        d.push.target[0]=d.push.target[1]=64;d.push.target[2]=.5f;d.push.fog[2]=1;
        d.push.mode[0]=2|4|(fog?16:0);d.push.mode[1]=0x00000204;d.push.mode[2]=2;
        auto light=std::make_shared<mw34::sun::Tl>();light->projection={1,40,40,32,32,.1f};
        light->camera_world=turn?std::array<float,12>{0,-1,0,0,0,0,-1,10,1,0,0,0}:std::array<float,12>{1,0,0,0,0,0,-1,10,0,1,0,0};
        d.sun_tl=light;
        for(const auto& p:std::array<std::array<float,2>,6>{{{12,12},{52,12},{52,52},{12,12},{52,52},{12,52}}}){
            Tl v{p[0],p[1],.5f,.5f,0xffff0000,fog?0u:0xff000000,0,0};const auto* bytes=reinterpret_cast<const unsigned char*>(&v);s.vertices.insert(s.vertices.end(),bytes,bytes+sizeof(v));}
        s.draws.push_back(d);s.order.push_back({false,0});r.render(s);return s.color[32*64+32];};
    require(terrain(false,false)==lit&&terrain(true,false)==lit,"TL terrain derives world-up normals across camera turns");
    require(terrain(false,true)==0x001f,"TL terrain preserves fog");
    auto hud=scene();quad(hud,true,false,true);hud.hud=true;r.render(hud);require(hud.color[32*64+32]==0xf800,"HUD scene retains original world shading");
    require(r.sun_world_draws==4&&r.sun_model_draws==1,"Actual sunlight draw counters");
    require(r.sun_tl_draws==3,"Actual TL sunlight draw counters");
    require(r.model_uploads==2,"Static geometry reused");
    auto normal_test = [&](int normal_tex) {
        auto s = scene();
        if (normal_tex >= 0) {
            TextureRef tex{}; tex.key = 0x42574e524d000001ULL + normal_tex; tex.hash = 1 + normal_tex; tex.width = 1; tex.height = 1; tex.format = TexFormat::rgba8888;
            if (normal_tex == 0) tex.pixels32 = {0xffff8080u}; // Flat normal (128, 128, 255, 255)
            else if (normal_tex == 1) tex.pixels32 = {0xff8080ffu}; // Tilted normal
            s.textures.push_back(tex);
        }
        auto d = quad(s, false, false, true);
        auto geometry=std::make_shared<ModelGeometry>(*d.model->geometry);
        geometry->key=13;geometry->hash=13;
        // An actual UV gradient and a surface-consistent +Z normal exercise
        // the tangent frame; constant UVs would silently test only fallback.
        for(auto& vertex:geometry->vertices){vertex.nx=0;vertex.ny=0;vertex.nz=1;
            vertex.u=(vertex.x+1)*.5f;vertex.v=(vertex.y+1)*.5f;}
        auto instance=std::make_shared<ModelInstance>(*d.model);instance->geometry=geometry;d.model=instance;
        d.normal_texture = (normal_tex >= 0) ? 0 : -1;
        s.draws[0] = d;
        r.render(s);
        return s.color[32*64+32];
    };
    const auto flat_default = normal_test(-1);
    const auto flat_bound = normal_test(0);
    require(flat_default == flat_bound, "Authored flat normal map must equal unperturbed flat normal");
    if(mw34::materials::normal_maps_enabled())
        require(normal_test(1)!=flat_default,"Tilted normal must visibly change directional lighting with valid UVs");
    else
        require(normal_test(1)==flat_default,"Disabled normal mapping must preserve geometric lighting");
    std::cout<<"Sun fixture passes: inverse transpose, camera invariance, ambient, models, fog, HUD, normal equivalence and cache on "<<r.device_name<<"\n";
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
