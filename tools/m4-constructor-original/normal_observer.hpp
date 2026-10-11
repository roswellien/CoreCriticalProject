// Genuine constructor boundaries and current live owners. No expected values.
#pragma once
#pragma pack(push,1)
struct ConstructorNormalSnapshot {
    unsigned metadata[12];
    CPU cpu;
    unsigned char fx[512],env[28],frame[64],pages[46*4096];
};
#pragma pack(pop)
static_assert(sizeof(ConstructorNormalSnapshot)==189108);
extern "C" {
alignas(16) CPU ctor_cpu{};
alignas(16) unsigned char ctor_fx[512]{};
unsigned char ctor_env[28]{};
unsigned ctor_kind{},ctor_source_head{},ctor_MFC_target{};
void ctor_MFC_entry();
void ctor_getter_bridge();
void ctor_observe();
}
static unsigned constructor_normal_count{};
static ConstructorNormalSnapshot constructor_normal_records[256]{};
static bool constructor_is_root(unsigned entry){return entry==0x4103f0||entry==0x410440||entry==0x459b40;}
extern "C" void ctor_observe(){
    if(!constructor_is_root(fs_phase_root)||constructor_normal_count>=256){fs_error=1;return;}
    const unsigned F=ctor_cpu.esp;
    if(F<0x20001000||F+64>0x20002000){fs_error=1;return;}
    auto&s=constructor_normal_records[constructor_normal_count];s={};
    const unsigned ret=dword(F);
    if(ctor_kind==0){
        bool matched=false;for(const auto&b:constructor_alloc_sites)if(b.return_PC==ret)matched=true;
        if(!matched||ctor_cpu.pc!=ctor_MFC_target){fs_error=1;return;}
    }else if(ctor_kind<10){
        if(ctor_kind>constructor_alloc_sites.size()||ctor_cpu.pc!=constructor_alloc_sites[ctor_kind-1].return_PC){fs_error=1;return;}
    }else{
        if(ctor_kind>11||ret!=0x58b186||!ctor_cpu.ecx){fs_error=1;return;}
        const unsigned vptr=dword(ctor_cpu.ecx);
        if((vptr!=0x5bcc68&&vptr!=0x5cab60&&vptr!=0x5ca6d8)||dword(vptr+0x18)!=0x40a850){fs_error=1;return;}
    }
    s.metadata[0]=1;s.metadata[1]=constructor_normal_count;s.metadata[2]=fs_phase_root;s.metadata[3]=ctor_kind;
    s.metadata[4]=ctor_cpu.pc;s.metadata[5]=F;s.metadata[6]=ctor_MFC_target;s.metadata[7]=dword(0x603fdc);
    s.metadata[8]=dword(0x603fe0);s.metadata[9]=ctor_source_head;s.metadata[10]=registry_API_count;s.metadata[11]=ctor_cpu.ecx;
    s.cpu=ctor_cpu;std::memcpy(s.fx,ctor_fx,512);std::memcpy(s.env,ctor_env,28);std::memcpy(s.frame,reinterpret_cast<void*>(F),64);
    for(unsigned i=0;i<observed_page_count;++i)std::memcpy(s.pages+i*4096,reinterpret_cast<void*>(observed_pages[i]),4096);
    unsigned i=43;for(unsigned p:{0x5cd000U,0x5e3000U,0x5e9000U})std::memcpy(s.pages+(i++)*4096,reinterpret_cast<void*>(p),4096);
    ++constructor_normal_count;
}
static void constructor_whole_live_owners(const std::string&stem){
    for(const auto&v:constructor_occurrences)if(v.alive){
        const unsigned capacity=constructor_capacity(v.heap,v.pointer);
        require(capacity==v.capacity,"Actual current whole owner capacity, no predicted extent");
        std::vector<unsigned char> bytes(capacity);
        require(safe_read(reinterpret_cast<void*>(v.pointer),bytes.data(),capacity),"Actual complete current owner bytes");
        const auto name=stem+"/live-"+std::to_string(v.serial);
        constructor_dump(name+"/meta.bin",&v,sizeof(v));constructor_dump(name+"/bytes.bin",bytes.data(),bytes.size());
    }
}
static void constructor_member_graph(const std::string&stem){
    const auto header=dword(0x605ae4),counter=dword(0x605ae8),heap=dword(0x78035000);
    const std::array<unsigned,5>meta{1,0x605ae4,header,0x605ae8,counter};constructor_dump(stem+"/meta.bin",meta.data(),sizeof(meta));
    if(!header){const unsigned n{};constructor_dump(stem+"/nodes-count.bin",&n,4);return;}
    std::vector<unsigned>seen;unsigned pointer=header,previous{};
    do{
        require(pointer&&seen.size()<256&&std::find(seen.begin(),seen.end(),pointer)==seen.end(),"Actual bounded member-list traversal");
        auto*owner=constructor_live(heap,pointer);require(owner!=nullptr,"Member-list node joins measured live allocator occurrence");
        const auto capacity=constructor_capacity(heap,pointer);require(capacity>=12&&capacity==owner->capacity,"Full actual member-list owner capacity");
        std::vector<unsigned char>bytes(capacity);require(safe_read(reinterpret_cast<void*>(pointer),bytes.data(),capacity),"Whole actual member-list backing");
        const unsigned next=word<unsigned>(bytes.data()),prev=word<unsigned>(bytes.data()+4),payload=word<unsigned>(bytes.data()+8);
        const std::array<unsigned,10>row{1,static_cast<unsigned>(seen.size()),pointer,capacity,owner->serial,owner->phase,owner->api_index,next,prev,payload};
        const auto name=stem+"/node-"+std::to_string(seen.size());constructor_dump(name+"/meta.bin",row.data(),sizeof(row));constructor_dump(name+"/bytes.bin",bytes.data(),bytes.size());
        if(previous)require(prev==previous,"Measured adjacent member-list backward link");seen.push_back(pointer);previous=pointer;pointer=next;
    }while(pointer!=header);
    require(dword(header+4)==previous,"Measured member-list terminal backward link");const auto n=static_cast<unsigned>(seen.size());constructor_dump(stem+"/nodes-count.bin",&n,4);
}
static void constructor_normal_dump(const std::string&stem){
    require(constructor_normal_count<=256&&!fs_error,"Bounded normal observation before export");
    constructor_dump(stem+"/normal-count.bin",&constructor_normal_count,4);
    constructor_dump(stem+"/normal-records.bin",constructor_normal_records,constructor_normal_count*sizeof(ConstructorNormalSnapshot));
}
