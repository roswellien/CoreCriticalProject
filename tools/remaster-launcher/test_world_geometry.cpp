// Authored GPU fixture; no game data. Compile against the private host snapshot
// after apply_world_geometry.py. Tests raw-position projection, separate TL
// attribute offsets, and restoration of ordinary TL vertex binding.
#define NOMINMAX
#include "vk_scene.hpp"
#include <iostream>

using namespace mw34::vkscene;
struct TlVertex { float x,y,z,rhw;std::uint32_t diffuse,specular;float u,v; };
static_assert(sizeof(TlVertex)==32);

static void add(Scene& scene,const TlVertex& vertex) {
    const auto* bytes=reinterpret_cast<const unsigned char*>(&vertex);
    scene.vertices.insert(scene.vertices.end(),bytes,bytes+sizeof(vertex));
}
static Draw draw(unsigned first,unsigned count) {
    Draw result{};result.first=first;result.count=count;result.texture=-1;
    result.key.cull=1;result.key.zfunc=4;
    result.push.target[0]=result.push.target[1]=64;result.push.target[2]=.5f;
    result.push.mode[0]=2;result.push.mode[1]=result.push.mode[2]=2;
    result.scissor={{0,0},{64,64}};
    return result;
}
static std::shared_ptr<ModelInstance> world(std::uint64_t key,float origin) {
    auto geometry=std::make_shared<ModelGeometry>();geometry->key=key;geometry->hash=key;
    geometry->vertices={{origin,origin,2,0,0,1,0,0},
                        {origin+1,origin,2,0,0,1,0,0},
                        {origin,origin+1,2,0,0,1,0,0}};
    auto result=std::make_shared<ModelInstance>();result->geometry=geometry;result->world=true;
    result->camera={1,0,0,0,0,1,0,0,0,0,1,0};
    result->projection={1,20,20,32,32,.1f};
    return result;
}
static void temporal_gpu_check(Renderer& renderer,Scene scene){
    using namespace mw34::temporal;
    auto require=[](bool good,const char* message){if(!good)throw std::runtime_error(message);};
    require(enabled(),"Temporal GPU fixture requires temporal inputs");
    Snapshot camera{};camera.view={1,2,3,0};camera.target=7;camera.attachment=8;camera.viewport=9;
    camera.camera[0]=camera.camera[4]=camera.camera[8]=std::bit_cast<unsigned>(1.f);
    camera.inverse=camera.camera;camera.projection={1,20,20,32,32,.1f};camera.far_clip=100;
    camera.viewport_rect={0,0,64,64};
    Clear clear{};clear.flags=3;clear.z=0;clear.color[3]=1;clear.rects={{{0,0},{64,64}}};
    scene.clears={clear};scene.order.insert(scene.order.begin(),{true,0});scene.temporal_target=7;
    // A zero-alpha source-over draw with depth writes disabled is an exact
    // no-op. It must not erase the metadata of the surface already visible.
    const auto transparent_first=unsigned(scene.vertices.size()/32);
    for(const auto& xy:std::array<std::array<float,2>,6>{{{0,0},{64,0},{0,64},{64,0},{64,64},{0,64}}})
        add(scene,{xy[0],xy[1],.99f,1,0x00000000,0,0,0});
    auto transparent=draw(transparent_first,6);
    transparent.key={1,5,6,1,7,0,1};transparent.push.mode[2]=2;
    scene.order.push_back({false,unsigned(scene.draws.size())});scene.draws.push_back(transparent);
    mw34::world::SnapshotCache<int> sources(16,1024);sources.put(1,{1,2,3},std::make_shared<const int>(1));
    auto capture=[&](unsigned frame,float x){
        camera.frame=frame;camera.camera[9]=std::bit_cast<unsigned>(x);scene.temporal_frame=frame;
        for(auto& draw:scene.draws)if(draw.model&&draw.model->world){
            auto model=std::make_shared<ModelInstance>(*draw.model);model->camera[3]=-x;
            draw.model=std::move(model);draw.key.zenable=draw.key.zwrite=1;draw.key.zfunc=7;
            draw.camera_view=std::make_shared<const Snapshot>(camera);
            auto source=std::make_shared<StaticSource>();source->frame=frame;source->previous_static=frame>2;
            source->node=unsigned(draw.model->geometry->key);source->polygon=source->node;
            source->mesh_bytes=source->node_bytes=sources.source(1);
            source->world={1,0,0,0,0,1,0,0,0,0,1,0};draw.temporal_source=source;
        }
    };
    renderer.complete_camera_history(1,7);
    capture(2,0);renderer.render(scene,true,false);renderer.complete_camera_history(2,7);
    auto first=renderer.capture_temporal(camera.view);
    require(first.width>0&&!first.history_valid,"First temporal frame inherited history");
    capture(3,.1f);renderer.render(scene,true,false);renderer.render(scene,false,false);
    renderer.complete_camera_history(3,7);
    auto result=renderer.capture_temporal(camera.view);
    require(result.history_valid&&result.width&&result.height,"No completed temporal input frame");
    const auto at=[&](unsigned x,unsigned y){return std::size_t(y*result.height/64)*result.width+x*result.width/64;};
    const auto pixel=at(22,22);
    require(result.validity[pixel]==255,"Static world coverage is all-invalid");
    require(std::abs(result.depth[pixel]-.05f)<=2e-6,"Sampled reversed infinite depth is incorrect");
    const float expected=result.width/64.f;
    require(std::abs(result.motion[pixel*2]-expected)<=.02f&&std::abs(result.motion[pixel*2+1])<=.02f,
            "Current-to-previous motion sign, scale, jitter or camera frame is incorrect");
    if(jitter_enabled()){
        const auto phase=jitter(1,renderer.camera_history.pairs().at(camera.view).current->sizes[2],result.width);
        require(result.jitter==phase,"Submissions advanced jitter more than once per real frame");
    }
    // A later original TL draw occludes static coverage without claiming motion.
    capture(4,.1f);
    Clear depth_only=clear;depth_only.flags=2;scene.clears.push_back(depth_only);
    scene.order.insert(scene.order.begin()+2,{true,1});
    for(unsigned vertex=6;vertex<12;++vertex){TlVertex v{};
        std::memcpy(&v,scene.vertices.data()+vertex*32,32);v.x+=12;v.y+=12;v.z=.75f;
        std::memcpy(scene.vertices.data()+vertex*32,&v,32);}
    scene.draws[1].key.zenable=scene.draws[1].key.zwrite=1;scene.draws[1].key.zfunc=7;
    renderer.render(scene,true,false);renderer.complete_camera_history(4,7);result=renderer.capture_temporal(camera.view);
    require(result.validity[at(22,22)]==0&&result.validity[at(27,21)]==255,
            "Unknown opaque coverage exposed static motion or invalidated the entire view");
    // The exact texture-alpha test restores only the holes in that occluder.
    capture(5,.1f);TextureRef alpha{};alpha.key=alpha.hash=987;alpha.width=2;alpha.height=1;
    alpha.format=TexFormat::rgba8888;alpha.pixels32={0x0000ff00,0xff00ff00};scene.textures={alpha};
    auto& overlay=scene.draws[1];overlay.texture=0;overlay.sampler=3U|(3U<<4)|(3U<<8);
    overlay.push.mode[0]|=4|32;overlay.push.mode[2]=2|(2<<8);overlay.push.mode[3]=5|(127<<8);
    for(unsigned vertex=6;vertex<12;++vertex){TlVertex v{};
        std::memcpy(&v,scene.vertices.data()+vertex*32,32);v.u=(v.x-20)/6;v.v=0;
        std::memcpy(scene.vertices.data()+vertex*32,&v,32);}
    renderer.render(scene,true,false);renderer.complete_camera_history(5,7);result=renderer.capture_temporal(camera.view);
    require(result.validity[at(21,22)]==255&&result.validity[at(24,22)]==0,
            "Temporal alpha rejection differs from original ordered visibility");
    // Nonzero source-over coverage and other blend equations are not no-ops.
    auto set_overlay_color=[&](unsigned color){for(unsigned i=0;i<6;++i){TlVertex v{};
        const auto offset=std::size_t(transparent_first+i)*32;
        std::memcpy(&v,scene.vertices.data()+offset,32);v.diffuse=color;
        std::memcpy(scene.vertices.data()+offset,&v,32);}};
    capture(6,.1f);set_overlay_color(0x80000000);
    renderer.render(scene,true,false);renderer.complete_camera_history(6,7);
    result=renderer.capture_temporal(camera.view);
    require(std::none_of(result.validity.begin(),result.validity.end(),[](auto v){return v!=0;}),
            "Nonzero-alpha unknown blend exposed static history");
    capture(7,.1f);set_overlay_color(0);scene.draws.back().key.src=2;scene.draws.back().key.dst=1;
    renderer.render(scene,true,false);renderer.complete_camera_history(7,7);
    result=renderer.capture_temporal(camera.view);
    require(std::none_of(result.validity.begin(),result.validity.end(),[](auto v){return v!=0;}),
            "Zero-alpha replacement blend was mistaken for source-over no-op");
    capture(8,.1f);scene.draws.back().key.src=5;scene.draws.back().key.dst=6;
    scene.draws.back().key.zwrite=1;
    renderer.render(scene,true,false);renderer.complete_camera_history(8,7);
    result=renderer.capture_temporal(camera.view);
    require(std::none_of(result.validity.begin(),result.validity.end(),[](auto v){return v!=0;}),
            "Depth-writing transparent geometry was incorrectly discarded");
    // Independent ray/plane oracle: a rotated, translated camera sees the same
    // world Z=2 surface. Recover its point from the raster sample and intersect
    // the plane analytically, rather than repeating the shader's divided motion.
    scene.draws={scene.draws.front()};scene.order={{true,0},{false,0}};
    capture(9,0);renderer.render(scene,true,false);renderer.complete_camera_history(9,7);
    capture(10,.1f);
    const double angle=.04,c=std::cos(angle),s=std::sin(angle),tx=.1,ty=-.05,tz=.1;
    const std::array<float,12> camera_world{float(c),0,float(-s),0,1,0,float(s),0,float(c),float(tx),float(ty),float(tz)};
    for(unsigned i=0;i<12;++i)camera.camera[i]=std::bit_cast<unsigned>(camera_world[i]);
    auto rotated=std::make_shared<ModelInstance>(*scene.draws[0].model);
    rotated->camera={float(c),0,float(-s),float(-c*tx+s*tz),0,1,0,float(-ty),float(s),0,float(c),float(-s*tx-c*tz)};
    scene.draws[0].model=rotated;scene.draws[0].camera_view=std::make_shared<const Snapshot>(camera);
    renderer.render(scene,true,false);renderer.complete_camera_history(10,7);result=renderer.capture_temporal(camera.view);
    unsigned samples=0;
    for(unsigned y=0;y<result.height;++y)for(unsigned x=0;x<result.width;++x){
        const auto i=std::size_t(y)*result.width+x;if(!result.validity[i])continue;
        const double sx=(x+.5-result.jitter[0])*64/result.width-.5;
        const double sy=(y+.5-result.jitter[1])*64/result.height-.5;
        const double rx=(sx-32)/20,ry=(sy-32)/20;
        const double z=(2-tz)/(c-s*rx);
        const double wx=(c*rx+s)*z+tx,wy=ry*z+ty;
        const double before_x=wx*10+32,before_y=wy*10+32;
        const double mx=(before_x-sx)*result.width/64,my=(before_y-sy)*result.height/64;
        require(std::abs(result.depth[i]-.1/z)<2e-6,"Rotated camera depth differs from ray/plane oracle");
        require(std::abs(result.motion[i*2]-mx)<.02&&std::abs(result.motion[i*2+1]-my)<.02,
                "Rotated XYZ camera motion differs from independent surface-point oracle");
        ++samples;
    }
    require(samples>10,"Rotation oracle has no genuine valid static samples");
    renderer.invalidate_camera_history(Reset::transition);
    require(renderer.capture_temporal(camera.view).width==0,"Reset exposed stale published temporal images");
    renderer.complete_camera_history(11,7);
    require(renderer.temporal_bytes()==0,"Missing view retained its GPU attachments");
    // Retire old views across more than eight distinct identities without leaking
    // the eight-slot live-view budget or inheriting a previous view's history.
    camera.camera={};camera.camera[0]=camera.camera[4]=camera.camera[8]=std::bit_cast<unsigned>(1.f);
    camera.inverse=camera.camera;scene.draws[0].model=world(0x5700000000000001ULL,-1.2f);
    for(unsigned frame=12;frame<=23;++frame){
        camera.view.node=frame+1000;capture(frame,0);renderer.render(scene,true,false);
        renderer.complete_camera_history(frame,7);result=renderer.capture_temporal(camera.view);
        require(result.width&&!result.history_valid,"New view inherited a retired view's history");
        require(renderer.temporal_bytes()==std::uint64_t(result.width)*result.height*17,
                "Retired view leaked diagnostic attachment capacity");
    }
    const auto main_view=camera.view;
    View zoom_view=main_view;zoom_view.node=9999;zoom_view.role=6;
    for(unsigned frame:{24U,25U}){
        scene.draws.resize(1);scene.order={{true,0},{false,0}};capture(frame,0);
        auto zoom=scene.draws.front();auto model=std::make_shared<ModelInstance>(*zoom.model);
        model->projection[3]+=4;zoom.model=model;
        auto snapshot=std::make_shared<Snapshot>(*zoom.camera_view);
        snapshot->view=zoom_view;snapshot->projection=model->projection;zoom.camera_view=snapshot;
        zoom.scissor={{26,20},{8,12}};
        scene.draws.push_back(zoom);scene.order.push_back({false,1});
        renderer.render(scene,true,false);renderer.complete_camera_history(frame,7);
    }
    result=renderer.capture_temporal(main_view);
    const auto zoom_pixels=renderer.capture_temporal(zoom_view);
    require(result.history_valid&&zoom_pixels.history_valid,"Main and zoom did not retain independent camera pairs");
    require(result.validity[at(22,22)]==255&&zoom_pixels.validity[at(29,22)]==255,
            "Main/zoom scissor or projection erased independent static coverage");
    require(zoom_pixels.validity[at(22,22)]==0,"Zoom inherited main-view coverage outside its scissor");
    renderer.complete_camera_history(26,0);
    require(renderer.capture_temporal(main_view).width==0&&renderer.temporal_bytes()==0,
            "Non-Flip publication retained stale diagnostic images");
    std::cout<<"Temporal GPU: signed pixel motion, sampled depth, phase, opaque/alpha validity on "
             <<renderer.device_name<<" at "<<result.width<<"x"<<result.height<<" pass\n";
}
int main(int argc, char **argv) {
    try {
        _putenv_s("MW34_GPU_MODELS","1");
        const bool temporal_test=argc>1&&std::string(argv[1])=="--temporal-inputs";
        _putenv_s("MW34_REMASTER_WIDTH",temporal_test?"640":"");_putenv_s("MW34_REMASTER_HEIGHT",temporal_test?"480":"");
        _putenv_s("MW34_REMASTER_AA","");_putenv_s("MW34_REMASTER_AF","");
        _putenv_s("MW34_RENDER_SCALE","");
        Scene scene{};scene.width=scene.height=64;scene.has_depth=true;
        scene.color.assign(4096,0);scene.depth.assign(4096,0);
        // Prefix poison catches accidental binding1 offset0. World TL positions
        // are deliberately offscreen: the raw geometry must supply positions.
        for(unsigned i=0;i<3;++i)add(scene,{5000,5000,.5f,.5f,0xffff00ff,0xff000000,0,0});
        for(unsigned i=0;i<3;++i)add(scene,{5000,5000,.5f,.5f,0xffff0000,0xff000000,0,0});
        for(const auto& p:std::array<std::array<float,2>,6>{{{8,8},{14,8},{8,14},{14,8},{14,14},{8,14}}})
            add(scene,{p[0],p[1],.5f,.5f,0xff00ff00,0xff000000,0,0});
        for(unsigned i=0;i<3;++i)add(scene,{5000,5000,.5f,.5f,0xff0000ff,0xff000000,0,0});
        auto red=draw(3,3);red.model=world(0x5700000000000001ULL,-1.2f);
        auto green=draw(6,6);
        auto blue=draw(12,3);blue.model=world(0x5700000000000002ULL,.2f);
        scene.draws={red,green,blue};scene.order={{false,0},{false,1},{false,2}};
        Renderer renderer;renderer.render(scene);
        auto check=[&](unsigned x,unsigned y,unsigned expected){
            if(scene.color[y*64+x]!=expected)throw std::runtime_error("World GPU fixture pixel mismatch at "+std::to_string(x)+","+std::to_string(y));
        };
        check(22,22,0xf800);check(10,10,0x07e0);check(36,36,0x001f);check(60,60,0);
        if(renderer.world_gpu_draws!=2||renderer.model_uploads!=2)throw std::runtime_error("World GPU fixture execution mismatch");
        renderer.render(scene);
        if(renderer.world_gpu_draws!=4||renderer.model_uploads!=2)throw std::runtime_error("World GPU fixture cache not reused");
        check(22,22,0xf800);check(10,10,0x07e0);check(36,36,0x001f);
        if(argc>1&&std::string(argv[1])=="--temporal-inputs"){
            temporal_gpu_check(renderer,scene);return 0;
        }
        if(argc>1){
            using namespace mw34::temporal;
            if(!enabled())throw std::runtime_error("Camera GPU fixture requires temporal diagnostics");
            Snapshot snapshot{};snapshot.view={1,2,3,0};snapshot.target=7;
            snapshot.attachment=8;snapshot.viewport=9;snapshot.far_clip=100;
            snapshot.camera[0]=snapshot.camera[4]=snapshot.camera[8]=std::bit_cast<unsigned>(1.f);
            snapshot.inverse=snapshot.camera;snapshot.projection={1,20,20,32,32,.1f};
            snapshot.viewport_rect={0,0,64,64};
            renderer.complete_camera_history(1,7);
            auto capture=[&](unsigned frame){snapshot.frame=frame;for(auto&d:scene.draws)
                if(d.model&&d.model->world)d.camera_view=std::make_shared<const Snapshot>(snapshot);};
            for(unsigned frame=2;frame<=3;++frame){capture(frame);renderer.render(scene,false,false);
                renderer.render(scene,false,false);renderer.complete_camera_history(frame,7);}
            if(!renderer.camera_history.pairs().at(snapshot.view).valid())
                throw std::runtime_error("Original world submissions did not retain one real-frame camera pair");
            Scene fill{};fill.width=fill.height=64;fill.has_depth=true;fill.guest_surface_write=true;
            Clear clear{};clear.flags=2;clear.rects={{{0,0},{64,64}}};
            fill.clears={clear};fill.order={{true,0}};
            renderer.render(fill,false,false);capture(4);renderer.render(scene,false,false);
            renderer.complete_camera_history(4,7);
            if(!renderer.camera_history.pairs().at(snapshot.view).valid())
                throw std::runtime_error("Normal frame initialization erased camera history");
            capture(5);renderer.render(scene,false,false);fill.clears[0].rects={{{10,10},{1,1}}};
            renderer.render(fill,false,false);renderer.complete_camera_history(5,7);
            if(!renderer.camera_history.pairs().empty())
                throw std::runtime_error("Interleaved guest fill committed camera history");
            snapshot.projection[1]=21;capture(6);renderer.render(scene,false,false);
            renderer.complete_camera_history(6,7);
            if(!renderer.camera_history.pairs().empty())
                throw std::runtime_error("Captured projection disagrees with actual world draw");
            std::cout<<"Camera GPU integration: original submissions, initialization, guest writes and projection validation pass\n";
        }
        std::cout<<"World GPU fixture: raw projection, attribute offsets, TL restoration and cache reuse pass on "<<renderer.device_name<<"\n";
    } catch(const std::exception& error) { std::cerr<<error.what()<<"\n";return 1; }
}
