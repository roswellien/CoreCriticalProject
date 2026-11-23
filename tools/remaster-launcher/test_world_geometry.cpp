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
int main(int argc, char **) {
    try {
        _putenv_s("MW34_GPU_MODELS","1");
        _putenv_s("MW34_REMASTER_WIDTH","");_putenv_s("MW34_REMASTER_HEIGHT","");
        _putenv_s("MW34_REMASTER_AA","");_putenv_s("MW34_REMASTER_AF","");
        _putenv_s("MW34_RENDER_SCALE","");
        Scene scene{};scene.width=scene.height=64;scene.has_depth=true;
        scene.color.assign(4096,0);scene.depth.assign(4096,0);
        // The game computes each scene's lighting before sending it (vdd.inc submit_scene).
        scene.environment=mw34::sun::current_settings(scene.detail_time);
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
