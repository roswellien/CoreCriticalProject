// Observation-only shared-list domain after actual carried prefix roots.
// Occurrence IDs identify a measured API invocation; they are not OS generations.
#pragma once
struct ConstructorOccurrence {
    unsigned version,serial,phase,api_index,kind,heap,requested,pointer,capacity,alive,predecessor_serial,initial_bytes;
};
static std::vector<ConstructorOccurrence> constructor_occurrences;
static unsigned constructor_serial{};
static void constructor_dump(const std::string&name,const void*bytes,std::size_t n){
    require(connected_writer!=nullptr,"Actual constructor prerequisite writer");
    connected_writer->append("constructor-prerequisites/"+name,bytes,n);
}
static ConstructorOccurrence*constructor_live(unsigned heap,unsigned pointer){
    ConstructorOccurrence*found{};
    for(auto&v:constructor_occurrences)if(v.alive&&v.heap==heap&&v.pointer==pointer){require(found==nullptr,"Unique live actual allocation occurrence");found=&v;}
    return found;
}
static unsigned constructor_capacity(unsigned heap,unsigned pointer){
    const auto capacity=reinterpret_cast<SIZE_T(WINAPI*)(HANDLE,DWORD,LPCVOID)>(registry_API_targets[2])(reinterpret_cast<HANDLE>(heap),0,reinterpret_cast<void*>(pointer));
    require(capacity!=SIZE_T(-1)&&capacity&&capacity<=65536,"Actual bounded whole prefix backing capacity");
    return static_cast<unsigned>(capacity);
}
static void constructor_collect(unsigned phase,const std::string&stem){
    require(registry_API_count<=256&&!fs_error,"Complete prefix ledger before owner export");
    for(unsigned i=0;i<registry_API_count;++i){
        const auto&e=registry_API_ledger[i];
        if(e.kind==0&&e.after.eax){
            require(constructor_occurrences.size()<1024,"Bounded actual allocation occurrences");
            require(constructor_live(e.args[0],e.after.eax)==nullptr,"No unretired same heap/address allocation");
            // Initial bytes were copied immediately after the genuine HeapAlloc
            // return by the inherited FP-preserving API observer, before guest writes.
            const auto initial=registry_initial_sizes[i];
            require(initial&&initial<=1024,"Genuine initial full HeapAlloc backing retained");
            ConstructorOccurrence v{1,++constructor_serial,phase,i,e.kind,e.args[0],e.args[2],e.after.eax,initial,1,0,initial};
            constructor_occurrences.push_back(v);
            const auto name=stem+"/allocation-"+std::to_string(v.serial);
            constructor_dump(name+"/occurrence.bin",&v,sizeof(v));
            constructor_dump(name+"/initial.bin",registry_initial_bytes[i],initial);
        }else if(e.kind==1&&e.after.eax){
            auto*v=constructor_live(e.args[0],e.args[2]);
            require(v!=nullptr,"Successful prefix HeapFree joins a measured live allocation");
            v->alive=0;
            const std::array<unsigned,4>event{phase,i,v->serial,e.args[2]};
            constructor_dump(stem+"/free-"+std::to_string(i)+".bin",event.data(),sizeof(event));
        }else if(e.kind==3&&e.after.eax){
            auto*old=constructor_live(e.args[0],e.args[2]);
            require(old!=nullptr,"Successful prefix HeapReAlloc joins a measured live allocation");
            const auto predecessor=old->serial;old->alive=0;
            require(constructor_live(e.args[0],e.after.eax)==nullptr&&constructor_occurrences.size()<1024,"Fresh actual reallocation revision");
            const auto capacity=constructor_capacity(e.args[0],e.after.eax);
            ConstructorOccurrence v{1,++constructor_serial,phase,i,e.kind,e.args[0],e.args[3],e.after.eax,capacity,1,predecessor,0};
            constructor_occurrences.push_back(v);
            constructor_dump(stem+"/reallocation-"+std::to_string(v.serial)+".bin",&v,sizeof(v));
            // No initial reallocation bytes were observed at the API return;
            // this complete phase endpoint is explicitly a later live backing.
        }
    }
    require(constructor_occurrences.size()<=1024,"Whole occurrence ledger bound before export");
    constructor_dump(stem+"/occurrences.bin",constructor_occurrences.data(),constructor_occurrences.size()*sizeof(ConstructorOccurrence));
}
static void constructor_graph(const std::string&stem){
    const auto header=dword(0x603fdc),counter=dword(0x603fe0),heap=dword(0x78035000);
    const std::array<unsigned,9>meta{1,0x603fdc,header,0x603fe0,counter,0x5f2a48,dword(0x5f2a48),dword(0x72c508),dword(0x72c2cc)};
    constructor_dump(stem+"/meta.bin",meta.data(),sizeof(meta));
    constructor_dump(stem+"/5F2000.bin",reinterpret_cast<void*>(0x5f2000),4096);
    if(!header){const unsigned count{};constructor_dump(stem+"/nodes-count.bin",&count,4);return;}
    std::vector<unsigned>seen;
    unsigned pointer=header,previous{};
    do{
        require(pointer&&seen.size()<256,"Bounded real linked-list traversal");
        for(const auto p:seen)require(p!=pointer,"No unexpected cyclic source list");
        auto*owner=constructor_live(heap,pointer);
        require(owner!=nullptr,"Current list pointer joins genuine prefix allocation occurrence");
        const auto capacity=constructor_capacity(heap,pointer);
        require(capacity>=12&&capacity==owner->capacity,"Whole current list owner capacity matches measured occurrence");
        std::vector<unsigned char>bytes(capacity);
        require(safe_read(reinterpret_cast<void*>(pointer),bytes.data(),capacity),"Whole actual list backing readable");
        const auto next=word<unsigned>(bytes.data()),prev=word<unsigned>(bytes.data()+4),payload=word<unsigned>(bytes.data()+8);
        const std::array<unsigned,10>row{1,static_cast<unsigned>(seen.size()),pointer,capacity,owner->serial,owner->phase,owner->api_index,next,prev,payload};
        const auto name=stem+"/node-"+std::to_string(seen.size());
        constructor_dump(name+"/meta.bin",row.data(),sizeof(row));constructor_dump(name+"/bytes.bin",bytes.data(),bytes.size());
        if(previous)require(prev==previous,"Measured adjacent list backward link");
        seen.push_back(pointer);previous=pointer;pointer=next;
    }while(pointer!=header);
    require(dword(header+4)==previous,"Measured full list terminal backward link");
    const auto count=static_cast<unsigned>(seen.size());constructor_dump(stem+"/nodes-count.bin",&count,4);
    constructor_dump(stem+"/occurrences.bin",constructor_occurrences.data(),constructor_occurrences.size()*sizeof(ConstructorOccurrence));
}
