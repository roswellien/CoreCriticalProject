#include "world_binding.hpp"
#include "temporal_inputs.hpp"
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
        SnapshotCache<int> retained(3,6);
        retained.put(1,{1,2,3},std::make_shared<const int>(1));
        auto source=retained.source(1);
        retained.put(1,{4,5,6},std::make_shared<const int>(2));
        require(retained.bytes()==6 && source->bytes[0]==1,"Retained source bytes lost their charge or ownership");
        rejects([&]{retained.put(2,{7},std::make_shared<const int>(3));});
        source.reset();require(retained.bytes()==3,"Last source owner did not release its charge");
        auto proof=retained.retain({8,9});
        require(retained.bytes()==5,"Node proof escaped the shared source budget");
        rejects([&]{retained.retain({1,2});});
        proof.reset();require(retained.bytes()==3,"Node proof storage did not retire");
        mw34::temporal::StaticSource source_identity{};
        source_identity.node=1;source_identity.mesh=2;source_identity.polygon=3;
        source_identity.cell_owner=4;source_identity.cell=5;source_identity.record=6;
        source_identity.mesh_bytes=retained.source(1);source_identity.node_bytes=retained.source(1);
        require(source_identity.unchanged(source_identity),"Unchanged static placement rejected");
        auto other=source_identity;other.record++;
        require(!source_identity.unchanged(other),"Two placements of one mesh inherited source identity");
        other=source_identity;other.offset[0]=std::bit_cast<unsigned>(1.f);
        require(!source_identity.unchanged(other),"Cell tile translation inherited source identity");
        other=source_identity;other.world[3]=1;
        require(!source_identity.unchanged(other),"Changed placement matrix inherited static motion");
        other=source_identity;other.epoch++;
        require(!source_identity.unchanged(other),"Reused cell storage inherited lifetime");
        other=source_identity;other.node_bytes=retained.retain({4,5,6});
        require(!source_identity.unchanged(other),"Replaced source owner inherited static admission");
        const mw34::temporal::Matrix transform{0,-1,0,10,1,0,0,-4,0,0,1,3};
        const auto inverse=mw34::temporal::inverse_affine(transform);
        const mw34::temporal::Matrix expected_inverse{0,1,0,4,-1,0,0,10,0,0,1,-3};
        require(inverse==expected_inverse,"Camera inverse rotation/translation convention changed");
        const auto first=mw34::temporal::jitter(0,64,64),second=mw34::temporal::jitter(1,64,64);
        require(first[0]==0 && std::abs(first[1]+1.f/6)<1e-6 && second[0]==-.25f &&
                std::abs(second[1]-1.f/6)<1e-6,"Halton phase/pixel convention changed");
        require(first==mw34::temporal::jitter(8,64,64) &&
                first!=mw34::temporal::jitter(8,128,64) &&
                first==mw34::temporal::jitter(32,128,64),"Jitter phase ignores internal/output ratio");
        SnapshotCache<int> empty(0,0);rejects([&]{empty.put(1,{},std::make_shared<const int>(1));});
        require(polygon_slot(1000,3,1000)==0&&polygon_slot(1000,3,1072)==2,"First/last polygon binding");
        require(!polygon_slot(1000,3,1108),"One-past polygon must reject");
        require(!polygon_slot(1000,3,1001),"Misaligned polygon must reject");
        require(!polygon_slot(1000,3,964),"Foreign earlier polygon must reject");
        require(!polygon_slot(0xfffffff0U,3,0x14),"Wrapped address must reject");
        std::cout<<"World binding: stale address, mutation, capacity, rejection integrity and polygon bounds pass\n";
    }catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 1;}
}
