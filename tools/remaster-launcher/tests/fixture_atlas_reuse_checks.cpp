#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <type_traits>
#include <vector>

namespace mw34::effects {
inline constexpr unsigned capacity=64;
struct Light {std::array<float,4> start{},end{},color{};};
struct Uniform {std::array<float,4> params{};std::array<Light,64> lights{};std::array<std::array<float,4>,64> shadow{};};
}
namespace {
unsigned checks{};
void require(bool value){++checks;if(!value)throw std::runtime_error("Atlas identity fixture failed");}
template<class T>T handle(std::uintptr_t x){if constexpr(std::is_pointer_v<T>)return reinterpret_cast<T>(x);else return T(x);}
struct ModelVertex {float x,y,z,nx,ny,nz,u,v;};
static_assert(sizeof(ModelVertex)==32);
struct Texture {
    VkImage image=handle<VkImage>(2);VkImageView view=handle<VkImageView>(3);
    std::uint64_t hash=44;bool valid=true;unsigned width=128,height=256,levels=8;
};
struct Caster {
    VkBuffer buffer=handle<VkBuffer>(4);unsigned first=0,count=3;
    std::array<float,12> world{};std::array<float,4> alpha{};
    struct Bounds {std::array<float,3> low{},high{};} bounds;
    Texture* texture{};unsigned sampler=0x113;std::uint64_t geometry_key{};
    std::vector<ModelVertex> tl{{1,2,3,0,0,0,.25f,.5f}};
    VkDescriptorSet set=handle<VkDescriptorSet>(5);
};
struct Renderer {
    using FixtureCaster=Caster;
    std::uint64_t uploads{},model_uploads{},mip_levels_uploaded{};
    struct Buffer {VkBuffer buffer=handle<VkBuffer>(20);} fixtureTlBuffer;
    std::uint64_t fixtureGeneration=9,fixtureContext=10;
    unsigned fixtureTile=256,fixtureAtlasWidth=4096,fixtureAtlasHeight=6144;
    VkImage fixtureShadowImage=handle<VkImage>(6);
    VkPipeline fixtureShadowPipeline=handle<VkPipeline>(7);
    std::vector<Caster*> fixtureFrameCasters;
    struct Geometry {std::uint64_t hash=50;unsigned count=3;bool uploaded=true;};
    std::map<std::uint64_t,Geometry> model_buffers;
#include "../native-overrides/fixture_atlas_reuse.inc"
};
}
int main(int argc,char**argv){
    try{
        _putenv_s("MW34_FIXTURE_ATLAS_REUSE",argc>1?argv[1]:"1");
        _putenv_s("MW34_FIXTURE_ATLAS_TRACKED",argc>2?argv[2]:"0");
        _putenv_s("MW34_FIXTURE_ATLAS_AUDIT",argc>3?argv[3]:"0");
        Renderer r;Texture texture,otherTexture=texture;Caster caster;caster.texture=&texture;
        r.fixtureFrameCasters={&caster};r.fixtureAtlasFrame=1200;
        mw34::effects::Uniform lights;lights.params[0]=1;lights.lights[0].start={0,1,2,32};lights.shadow[0]={1,.1f,32,.025f};
        if(argc>1&&!std::strcmp(argv[1],"0")){
            require(!r.fixture_atlas_unchanged(lights));r.fixture_atlas_submitted();
            require(!r.fixtureAtlasValid&&r.fixtureAtlasIdentity.empty());
        }else if(argc>1&&std::strcmp(argv[1],"1")){
            bool failed=false;try{r.fixture_atlas_unchanged(lights);}catch(const std::runtime_error&){failed=true;}
            require(failed);
        }else if(argc>2&&!std::strcmp(argv[2],"1")){
            require(!r.fixture_atlas_unchanged(lights));r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();
            require(r.fixture_atlas_unchanged(lights));
            // Every captured float bit (including signed zero) must invalidate
            // before the next assignment can replace a submitted dependency.
            auto capture_change=[&](auto mutate){
                auto candidate=caster;mutate(candidate);
                require(r.fixture_atlas_capture_changed(false,caster,candidate));
            };
            for(unsigned i=0;i<caster.world.size();++i)capture_change([&](auto& c){c.world[i]=-0.f;});
            for(unsigned i=0;i<caster.alpha.size();++i)capture_change([&](auto& c){c.alpha[i]=-0.f;});
            for(unsigned i=0;i<caster.bounds.low.size();++i)capture_change([&](auto& c){c.bounds.low[i]=-0.f;});
            for(unsigned i=0;i<caster.bounds.high.size();++i)capture_change([&](auto& c){c.bounds.high[i]=-0.f;});
            for(unsigned word=0;word<8;++word)capture_change([&](auto& c){
                auto bits=std::bit_cast<std::array<std::uint32_t,8>>(c.tl[0]);
                bits[word]^=0x80000000U;c.tl[0]=std::bit_cast<ModelVertex>(bits);
            });
            capture_change([&](auto& c){c.texture=&otherTexture;});
            capture_change([](auto& c){++c.sampler;});
            capture_change([](auto& c){++c.count;});
            capture_change([](auto& c){++c.geometry_key;});
            capture_change([](auto& c){c.tl.push_back(c.tl[0]);});
            require(r.fixture_atlas_capture_changed(true,caster,caster));
            auto next=caster;next.tl[0].u=.75f;
            require(!r.fixture_atlas_same_caster(caster,next));
            require(r.fixture_atlas_capture_changed(false,caster,next));
            r.fixture_atlas_touch();caster=next;
            require(!r.fixture_atlas_unchanged(lights));
            next.world[0]=-0.f;
            require(!r.fixture_atlas_capture_changed(false,caster,next)); // Already dirty.
            r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();
            require(r.fixture_atlas_unchanged(lights));
            auto unchanged=caster;unchanged.set=handle<VkDescriptorSet>(99);
            require(r.fixture_atlas_same_caster(caster,unchanged));
            if(argc>3&&!std::strcmp(argv[3],"1")){
                texture.hash=45;
                bool failed=false;try{r.fixture_atlas_unchanged(lights);}catch(const std::runtime_error&){failed=true;}
                require(failed); // Deliberately omit the required upload revision.
                ++r.uploads;require(!r.fixture_atlas_unchanged(lights));
                r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();
                require(r.fixture_atlas_unchanged(lights)&&r.fixtureAtlasAudits>0);
            }else{
                ++texture.hash;++r.uploads;require(!r.fixture_atlas_unchanged(lights));
                r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();require(r.fixture_atlas_unchanged(lights));
            }
            ++r.model_uploads;require(!r.fixture_atlas_unchanged(lights));
            r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();require(r.fixture_atlas_unchanged(lights));
            ++r.mip_levels_uploaded;require(!r.fixture_atlas_unchanged(lights));
            r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();require(r.fixture_atlas_unchanged(lights));
            r.fixture_atlas_touch();r.fixtureFrameCasters.clear();require(!r.fixture_atlas_unchanged(lights));
            ++r.fixtureAtlasFrame;require(!r.fixture_atlas_unchanged(lights));
        }else{
            require(!r.fixture_atlas_unchanged(lights));
            r.fixture_atlas_submitted();require(!r.fixtureAtlasValid);
            r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();
            require(r.fixtureAtlasBuilds==1&&r.fixture_atlas_unchanged(lights));
            const auto retained=r.fixtureAtlasIdentity;
            auto changed=[&](auto& value,auto next){
                const auto old=value;value=next;
                require(!r.fixture_atlas_unchanged(lights));
                require(r.fixtureAtlasIdentity==retained);
                value=old;require(r.fixture_atlas_unchanged(lights));
            };
            changed(r.fixtureAtlasFrame,std::uint64_t(1201));
            changed(r.fixtureGeneration,std::uint64_t(11));changed(r.fixtureContext,std::uint64_t(12));
            changed(r.fixtureTile,512U);changed(r.fixtureAtlasWidth,8192U);changed(r.fixtureAtlasHeight,12288U);
            changed(r.fixtureShadowImage,handle<VkImage>(8));changed(r.fixtureShadowPipeline,handle<VkPipeline>(9));
            changed(caster.buffer,handle<VkBuffer>(10));changed(caster.first,3U);changed(caster.count,6U);
            for(auto& value:caster.world)changed(value,-0.f);
            for(auto& value:caster.alpha)changed(value,-0.f);
            for(auto& value:caster.bounds.low)changed(value,-0.f);
            for(auto& value:caster.bounds.high)changed(value,-0.f);
            changed(caster.texture,&otherTexture);changed(caster.sampler,0x114U);
            changed(texture.image,handle<VkImage>(11));changed(texture.view,handle<VkImageView>(12));
            changed(texture.hash,std::uint64_t(45));changed(texture.valid,false);
            changed(texture.width,256U);changed(texture.height,512U);changed(texture.levels,9U);
            for(unsigned word=0;word<8;++word){
                auto old=caster.tl[0];auto bits=std::bit_cast<std::array<std::uint32_t,8>>(old);
                bits[word]^=0x80000000U;caster.tl[0]=std::bit_cast<ModelVertex>(bits);
                require(!r.fixture_atlas_unchanged(lights));caster.tl[0]=old;
                require(r.fixture_atlas_unchanged(lights));
            }
            caster.tl.push_back(caster.tl[0]);require(!r.fixture_atlas_unchanged(lights));
            caster.tl.pop_back();require(r.fixture_atlas_unchanged(lights));
            changed(lights.params[0],2.f);changed(lights.lights[0].start[3],64.f);
            changed(lights.shadow[0][1],.2f);
            lights.lights[0].color[0]=1.f;lights.lights[0].end[0]=5.f;
            require(r.fixture_atlas_unchanged(lights)); // Unused by depth rendering.
            caster.set=handle<VkDescriptorSet>(99);
            require(r.fixture_atlas_unchanged(lights)); // Same effective descriptor inputs.
            r.fixtureFrameCasters.clear();require(!r.fixture_atlas_unchanged(lights));
            r.fixtureFrameCasters={&caster};require(r.fixture_atlas_unchanged(lights));
            // A changed model's backing data invalidates even if its VkBuffer stays the same.
            caster.tl.clear();caster.geometry_key=77;r.model_buffers.emplace(77,Renderer::Geometry{});
            require(!r.fixture_atlas_unchanged(lights));r.fixtureAtlasRecorded=true;r.fixture_atlas_submitted();
            require(r.fixture_atlas_unchanged(lights));
            auto& model=r.model_buffers.at(77);model.hash=51;require(!r.fixture_atlas_unchanged(lights));
            model.hash=50;model.count=6;require(!r.fixture_atlas_unchanged(lights));
            model.count=3;model.uploaded=false;require(!r.fixture_atlas_unchanged(lights));
            model.uploaded=true;require(r.fixture_atlas_unchanged(lights));
            r.fixtureAtlasValid=false;require(!r.fixture_atlas_unchanged(lights));
        }
        std::cout<<"Fixture atlas identity checks="<<checks<<" failures=0\n";
    }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
