#include "native-overrides/world_binding.hpp"
#include <iostream>

static void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F> static void rejects(F&& action){bool caught=false;try{action();}catch(const std::runtime_error&){caught=true;}require(caught,"Expected rejection");}
int main(){
    try{
        using mw34::world::SnapshotCache;
        using mw34::world::polygon_slot;
        SnapshotCache<int> cache(2,4);
        cache.put(100,{1,2},std::make_shared<const int>(7));
        require(*cache.find(100,{1,2})==7,"Exact source snapshot must hit");
        require(!cache.find(100,{1,3}),"Changed bytes at reused address must miss");
        require(!cache.find(200,{1,2}),"Another source address must miss");
        cache.put(200,{3,4},std::make_shared<const int>(8));
        require(cache.bytes()==4&&cache.size()==2,"Full budget accounting");
        rejects([&]{cache.put(300,{5},std::make_shared<const int>(9));});
        rejects([&]{cache.put(100,{1,2,3},std::make_shared<const int>(9));});
        require(*cache.find(100,{1,2})==7&&cache.bytes()==4,"Rejected insertion must preserve prior value/budget");
        cache.put(100,{9},std::make_shared<const int>(10));
        require(!cache.find(100,{1,2})&&*cache.find(100,{9})==10,"Replacement must invalidate old snapshot");
        require(cache.bytes()==3,"Replacement must release old byte budget");
        cache.put(200,{6,7,8},std::make_shared<const int>(11));
        require(cache.bytes()==4,"Reclaimed byte capacity must be reusable");
        rejects([&]{cache.put(200,{6,7,8},{});});
        SnapshotCache<int> empty(0,0);rejects([&]{empty.put(1,{},std::make_shared<const int>(1));});
        require(polygon_slot(1000,3,1000)==0&&polygon_slot(1000,3,1072)==2,"First/last polygon binding");
        require(!polygon_slot(1000,3,1108),"One-past polygon must reject");
        require(!polygon_slot(1000,3,1001),"Misaligned polygon must reject");
        require(!polygon_slot(1000,3,964),"Foreign earlier polygon must reject");
        require(!polygon_slot(0xfffffff0U,3,0x14),"Wrapped address must reject");
        std::cout<<"World binding: stale address, mutation, capacity, rejection integrity and polygon bounds pass\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
