// Genuine constructor boundaries and current live owners. No expected values.
#pragma once
#pragma pack(push,1)
struct ConstructorNormalSnapshot {
    unsigned metadata[12];
    Cpu cpu;
    unsigned char fx[512],env[28],frame[64],pages[46*4096];
};
#pragma pack(pop)
static_assert(sizeof(ConstructorNormalSnapshot)==189108);
extern "C" {
alignas(16) Cpu ctor_cpu{};
alignas(16) unsigned char ctor_fx[512]{};
unsigned char ctor_env[28]{};
unsigned ctor_kind{},ctor_source_head{},ctor_MFC_target{};
void ctor_MFC_entry();
void ctor_getter_bridge();
void ctor_observe();
}
static unsigned constructor_normal_count{};
static std::array<unsigned,10>constructor_getter_backings[256]{};
static ConstructorNormalSnapshot constructor_normal_records[256]{};
static bool constructor_is_root(unsigned entry){return entry==0x4103f0||entry==0x410440||entry==0x459b40;}
extern "C" void ctor_observe(){
    if(!constructor_is_root(fs_phase_root)||constructor_normal_count>=256){ctor_record_fs_failure(__LINE__,__FILE__);return;}
    const unsigned F=ctor_cpu.esp;
    if(F<0x20001000||F+64>0x20002000){ctor_record_fs_failure(__LINE__,__FILE__);return;}
    auto&s=constructor_normal_records[constructor_normal_count];s={};
    const unsigned ret=dword(F);
    if(ctor_kind==0){
        bool matched=false;for(const auto&b:constructor_alloc_sites)if(b.return_PC==ret)matched=true;
        if(!matched||ctor_cpu.pc!=ctor_MFC_target){ctor_record_fs_failure(__LINE__,__FILE__);return;}
    }else if(ctor_kind<10){
        if(ctor_kind>constructor_alloc_sites.size()||ctor_cpu.pc!=constructor_alloc_sites[ctor_kind-1].return_PC){ctor_record_fs_failure(__LINE__,__FILE__);return;}
    }else{
        if(ctor_kind>11||ret!=0x58b186||!ctor_cpu.ecx){ctor_record_fs_failure(__LINE__,__FILE__);return;}
        const unsigned vptr=dword(ctor_cpu.ecx);
        bool receiver_page=false,vptr_page=false;
        for(unsigned p:observed_pages){if((ctor_cpu.ecx&~4095U)==p)receiver_page=true;if((vptr&~4095U)==p)vptr_page=true;}
        MEMORY_BASIC_INFORMATION receiver_region{},vptr_region{};
        const bool geometry=receiver_page&&vptr_page&&(ctor_cpu.ecx&4095U)+8<=4096&&(vptr&4095U)+0x1c<=4096;
        if(!geometry||VirtualQuery(reinterpret_cast<void*>(ctor_cpu.ecx),&receiver_region,sizeof(receiver_region))!=sizeof(receiver_region)||VirtualQuery(reinterpret_cast<void*>(vptr),&vptr_region,sizeof(vptr_region))!=sizeof(vptr_region)||receiver_region.State!=MEM_COMMIT||vptr_region.State!=MEM_COMMIT||receiver_region.Protect!=PAGE_READWRITE||vptr_region.Protect!=PAGE_READONLY||ctor_cpu.edx!=vptr||dword(vptr+0x18)!=0x40a850){ctor_record_fs_failure(__LINE__,__FILE__);return;}
        // The receiver is source-owned PE memory retained as a whole page.
        // Its actual publication is a payload in the genuine current list.
        bool published=false;const unsigned header=dword(0x603fdc);unsigned node=header;
        for(unsigned n=0;node&&n<256;++n){unsigned raw[3]{};if(!safe_read(reinterpret_cast<void*>(node),raw,sizeof(raw))){ctor_record_fs_failure(__LINE__,__FILE__);return;}if(raw[2]==ctor_cpu.ecx)published=true;node=raw[0];if(node==header)break;if(n==255){ctor_record_fs_failure(__LINE__,__FILE__);return;}}
        if(!published){ctor_record_fs_failure(__LINE__,__FILE__);return;}
        constructor_getter_backings[constructor_normal_count]={1,constructor_normal_count,ctor_cpu.ecx,ctor_cpu.ecx&~4095U,vptr,vptr&~4095U,vptr+0x18,dword(vptr+0x18),receiver_region.Protect,vptr_region.Protect};
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
        auto*member_owner=constructor_live(heap,pointer);require(member_owner!=nullptr,"Member-list node joins measured live allocator occurrence");
        const auto capacity=constructor_capacity(heap,pointer);require(capacity>=12&&capacity==member_owner->capacity,"Full actual member-list owner capacity");
        std::vector<unsigned char>bytes(capacity);require(safe_read(reinterpret_cast<void*>(pointer),bytes.data(),capacity),"Whole actual member-list backing");
        const unsigned next=word<unsigned>(bytes.data()),prev=word<unsigned>(bytes.data()+4),payload=word<unsigned>(bytes.data()+8);
        const std::array<unsigned,10>row{1,static_cast<unsigned>(seen.size()),pointer,capacity,member_owner->serial,member_owner->phase,member_owner->api_index,next,prev,payload};
        const auto name=stem+"/node-"+std::to_string(seen.size());constructor_dump(name+"/meta.bin",row.data(),sizeof(row));constructor_dump(name+"/bytes.bin",bytes.data(),bytes.size());
        if(previous)require(prev==previous,"Measured adjacent member-list backward link");seen.push_back(pointer);previous=pointer;pointer=next;
    }while(pointer!=header);
    require(dword(header+4)==previous,"Measured member-list terminal backward link");const auto n=static_cast<unsigned>(seen.size());constructor_dump(stem+"/nodes-count.bin",&n,4);
}
static void constructor_normal_dump(const std::string&stem){
    require(constructor_normal_count<=256&&!fs_error,"Bounded normal observation before export");
    constructor_dump(stem+"/normal-count.bin",&constructor_normal_count,4);
    constructor_dump(stem+"/normal-records.bin",constructor_normal_records,constructor_normal_count*sizeof(ConstructorNormalSnapshot));
    constructor_dump(stem+"/getter-backings.bin",constructor_getter_backings,constructor_normal_count*sizeof(constructor_getter_backings[0]));
}
