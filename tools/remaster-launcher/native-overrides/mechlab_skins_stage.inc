// Extend the retail SKIN_LIST through its original list APIs. Extra choices
// retain a host-owned identity; no nonexistent retail skin index enters a
// loadout, preview-resource lookup or original save record.
struct MechLabSkinState {
    unsigned lab{},widget{},original_count{},rebuilding{};
    std::string chassis;
    std::vector<unsigned> additions;
    std::map<std::string,unsigned> names;
};
MechLabSkinState mechlab_skins;
unsigned mechlab_skin_call(unsigned target,unsigned object,std::initializer_list<unsigned> arguments) {
    const State saved=state;OverrideMxcsr fp;
    try {state.gpr.rcx.dword=object;
        const unsigned result=call_guest(target,arguments,true,"Mech Lab skin extension");state=saved;return result;
    }catch(...){state=saved;throw;}
}
unsigned mechlab_skin_configuration(unsigned lab) {
    const unsigned config=mechlab_skin_call(0x44e6a0,lab,{0});
    if(config&&!readable(config,0x18))throw std::runtime_error("Mech Lab: selected configuration is unavailable");
    return config;
}
std::string mechlab_skin_chassis(unsigned config) {
    const unsigned index=load(config+4);
    if(index>=19)return {}; // Original empty/unassigned selection has no skin additions.
    // The retail record stores its cached definition at +56; the inline name
    // begins at 5E6078 (the cache array indexed by 4846A0 begins at 5E60B0).
    const unsigned name=0x5e6078+60*index;
    if(!readable(name,32))throw std::runtime_error("Mech Lab: chassis name table is unavailable");
    std::string id;
    for(unsigned i=0;i<32;++i){const auto c=runtime.memory().load<std::uint8_t>({name+i});if(!c)return id;
        if(c<'a'||c>'z')throw std::runtime_error("Mech Lab: malformed chassis identity");id+=char(c);}
    throw std::runtime_error("Mech Lab: unterminated chassis identity");
}
unsigned mechlab_skin_count(unsigned widget) {
    if(!readable(widget,0x170)||load(widget)!=0x5c1448)throw std::runtime_error("Mech Lab: skin widget identity mismatch");
    const unsigned first=load(widget+0x15c),last=load(widget+0x160);
    if(last<first||(last-first)%4||(last-first)/4>256||(first&&!readable(first,last-first)))
        throw std::runtime_error("Mech Lab: invalid skin list storage");
    return (last-first)/4;
}
unsigned mechlab_skin_text(const mw34::skins::Addition& record) {
    auto& names=mechlab_skins.names;const auto found=names.find(record.id);if(found!=names.end())return found->second;
    // This retail bitmap-font UI uses byte characters, not the Windows font
    // renderer of the superseded shortcut window. Fail unsupported names.
    for(const unsigned char c:record.name)if(c<32||c>126)throw std::runtime_error("Mech Lab skin names require printable ASCII");
    const unsigned address=gheap_alloc(unsigned(record.name.size()+1),true,0x44cf70);
    if(!address)throw std::runtime_error("Mech Lab: unable to allocate skin name");
    write_bytes(address,record.name.c_str(),unsigned(record.name.size()+1));names.emplace(record.id,address);return address;
}
void mechlab_skin_save(const std::string& chassis) {
    auto& a=additional_skins;if(a.preferences.empty())return;
    std::filesystem::create_directories(std::filesystem::path(a.preferences).parent_path());
    const auto found=a.selected.find(chassis);
    const auto value=found==a.selected.end()?std::wstring{}:additional_skin_wide(a.records.at(found->second-8).id);
    if(!WritePrivateProfileStringW(L"MW3",additional_skin_wide(chassis).c_str(),value.c_str(),a.preferences.c_str()))
        throw std::runtime_error("Unable to save Mech Lab skin selection");
}
void mechlab_skin_populated(unsigned lab) {
    auto& ui=mechlab_skins;ui.lab=lab;ui.widget=lab+0x1803c;ui.additions.clear();
    ui.original_count=mechlab_skin_count(ui.widget);
    const unsigned config=mechlab_skin_configuration(lab);
    ui.chassis=config?mechlab_skin_chassis(config):std::string{};
    if(ui.chassis.empty())return;
    if(!ui.original_count)return;
    const unsigned first=load(ui.widget+0x15c),row=load(first);
    if(!readable(row,8))throw std::runtime_error("Mech Lab: original skin row is unavailable");
    const unsigned data=load(row+4); // List userdata is nonowning; names are copied by 48BAC0.
    auto& a=additional_skins;
    for(unsigned i=0;i<a.records.size();++i)if(a.records[i].chassis==ui.chassis){
        const unsigned index=mechlab_skin_call(0x48bac0,ui.widget,{mechlab_skin_text(a.records[i]),data});
        if(index!=ui.original_count+ui.additions.size())throw std::runtime_error("Mech Lab: appended skin displaced a retail row");
        const unsigned row=load(load(ui.widget+0x15c)+4*index);
        if(!row||!readable(row,8)||!load(row))throw std::runtime_error("Mech Lab: appended skin label allocation failed");
        ui.additions.push_back(i);
        std::fprintf(stderr,"Mech Lab skin registered: chassis=%s row=%u name=%s id=%s\n",ui.chassis.c_str(),index,a.records[i].name.c_str(),a.records[i].id.c_str());
    }
    const auto selected=a.selected.find(ui.chassis);
    if(selected!=a.selected.end())for(unsigned i=0;i<ui.additions.size();++i)if(selected->second==8+ui.additions[i])
        mechlab_skin_call(0x48b850,ui.widget,{ui.original_count+i});
    std::fprintf(stderr,"Mech Lab skin list: chassis=%s original=%u additions=%zu\n",ui.chassis.c_str(),ui.original_count,ui.additions.size());
}
void* mechlab_skin_body(State* s,unsigned target,void* p,Body body) {
    if(!std::getenv("MW34_ADDITIONAL_SKINS"))return body(s,target,p);
    additional_skins_read();auto& ui=mechlab_skins;
    if(target==0x44cf70){const unsigned lab=state.gpr.rcx.dword;++ui.rebuilding;void* result{};
        try{result=body(s,target,p);}catch(...){--ui.rebuilding;throw;}
        --ui.rebuilding;mechlab_skin_populated(lab);return result;
    }
    if(ui.rebuilding||state.gpr.rcx.dword!=ui.widget||ui.chassis.empty())return body(s,target,p);
    const unsigned stack=state.gpr.rsp.dword,requested=load(stack+4);
    if(requested==~0U)return body(s,target,p);
    const unsigned config=mechlab_skin_configuration(ui.lab);
    if(!config)return body(s,target,p);
    if(mechlab_skin_chassis(config)!=ui.chassis)throw std::runtime_error("Mech Lab: skin list and configuration disagree");
    auto& a=additional_skins;const auto previous=a.selected.find(ui.chassis);
    const auto prior=previous==a.selected.end()?std::optional<unsigned>{}:std::optional<unsigned>{previous->second};
    if(requested>=ui.original_count){
        const unsigned extra=requested-ui.original_count;if(extra>=ui.additions.size())throw std::runtime_error("Mech Lab: skin row outside the registered list");
        const unsigned original=load(config+0x10);if(original>=ui.original_count)throw std::runtime_error("Mech Lab: invalid underlying retail skin");
        a.selected[ui.chassis]=8+ui.additions[extra];store(stack+4,original);
    }else a.selected.erase(ui.chassis);
    void* result{};
    try{result=body(s,target,p);}catch(...){store(stack+4,requested);if(prior)a.selected[ui.chassis]=*prior;else a.selected.erase(ui.chassis);throw;}
    store(stack+4,requested);
    if(requested>=ui.original_count)mechlab_skin_call(0x48b850,ui.widget,{requested});
    a.announced.clear();mechlab_skin_save(ui.chassis);
    std::fprintf(stderr,"Mech Lab skin selected: chassis=%s row=%u id=%s retail_skin=%u\n",ui.chassis.c_str(),requested,
        a.selected.count(ui.chassis)?a.records.at(a.selected.at(ui.chassis)-8).id.c_str():"original",load(config+0x10));
    return result;
}
void mechlab_skin_closed() {
    auto& ui=mechlab_skins;ui.lab=ui.widget=ui.original_count=0;ui.chassis.clear();ui.additions.clear();
}
