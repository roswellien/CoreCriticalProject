#include "../native-overrides/wide_lighting_reuse.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <stdexcept>
#include <vector>
#include <cstdio>
struct View {std::array<float,12> camera_world{};std::array<float,6> projection{};};
static_assert(sizeof(View)==72);
unsigned checks{};
void require(bool good){++checks;if(!good)throw std::runtime_error("Widescreen lighting ownership check failed");}
int main(){
    using Cache=mw34::submission::WideLightingViews<View>;
    Cache cache;View v;v.projection={1,2,3,4,5,6};
    auto original=cache.capture(v,false);
    for(unsigned i=0;i<10000;++i)require(cache.capture(v,false)==original);
    require(cache.allocations==1 && cache.captures==10001);
    auto sky=cache.capture(v,true);require(sky!=original);
    require(cache.capture(v,false)==original && cache.capture(v,true)==sky);
    // Byte identity preserves signed zero, NaN payloads and every camera word.
    for(unsigned word=0;word<18;++word){
        for(std::uint32_t bits:{0U,0x80000000U,0x7fc12345U,0xffc54321U,0x3f800001U}){
            View pending=v;std::memcpy(reinterpret_cast<unsigned char*>(&pending)+word*4,&bits,4);
            auto next=cache.capture(pending,false);
            require(!std::memcmp(next.get(),&pending,sizeof(pending)));
            require(cache.capture(pending,false)==next);
            require(!std::memcmp(original.get(),&v,sizeof(v)));
        }
    }
    std::vector<std::shared_ptr<const View>> held;
    for(unsigned i=0;i<1000;++i){View pending=v;pending.camera_world[0]=float(i);held.push_back(cache.capture(pending,false));}
    for(unsigned i=0;i<1000;++i)require(held[i]->camera_world[0]==float(i));
    auto moved=std::move(cache);require(moved.capture(*held.back(),false)==held.back());
    auto copy=moved;View changed=v;changed.projection[0]=7;copy.capture(changed,false);
    require(moved.capture(*held.back(),false)==held.back());
    std::shared_ptr<const View> escaped;
    {Cache temporary;escaped=temporary.capture(changed,true);}
    require(!std::memcmp(escaped.get(),&changed,sizeof(changed)));
    // Original and cached paths perform the same adjustment before capture.
    for(float factor:{1.f,1.3333333f,1.5f,2.f})for(float anchor:{0.f,160.f,320.f,640.f}){
        auto previous=std::make_shared<View>(v);previous->projection[1]/=factor;
        previous->projection[3]=anchor+(previous->projection[3]+.5f-anchor)/factor-.5f;
        auto pending=v;pending.projection[1]/=factor;
        pending.projection[3]=anchor+(pending.projection[3]+.5f-anchor)/factor-.5f;
        require(!std::memcmp(moved.capture(pending,false).get(),previous.get(),sizeof(View)));
    }
    std::printf("%u immutable widescreen-lighting checks passed\n",checks);
}
