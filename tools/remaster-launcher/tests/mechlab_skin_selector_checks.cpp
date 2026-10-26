// Authored guest-boundary fixture. Exercise the actual selector adapter without
// original game code, assets, a graphics backend or a native game build.
#include "../native-overrides/additional_skins.hpp"
#include "../native-overrides/additional_chassis.hpp"
namespace mw34::chassis { std::vector<Registration> fixture_records;
const std::vector<Registration>& fixture_catalog(){return fixture_records;} }
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <initializer_list>
#include <map>
#include <set>

namespace {
std::vector<unsigned char> memory(0x700000);
unsigned heap=0x200000;
unsigned slots[4]{0x10000,0x11000,0x12000,0x13000};
constexpr unsigned lab=0x100000,widget=lab+0x1803c,stack=0x500000;
bool fail_getter{},fail_clear{};
unsigned getter_argument{};
void check(bool value,const char* message) { if(!value)throw std::runtime_error(message); }
bool readable(unsigned at,unsigned size) { return at<=memory.size()&&size<=memory.size()-at; }
unsigned load(unsigned at) { check(readable(at,4),"Unreadable fixture word");unsigned value;std::memcpy(&value,memory.data()+at,4);return value; }
void store(unsigned at,unsigned value) { check(readable(at,4),"Unwritable fixture word");std::memcpy(memory.data()+at,&value,4); }
void write_bytes(unsigned at,const char* bytes,unsigned size) { check(readable(at,size),"Unwritable fixture text");std::memcpy(memory.data()+at,bytes,size); }
unsigned gheap_alloc(unsigned size,bool,unsigned=0) { unsigned result=heap;heap+=size+16;check(readable(result,size),"Fixture heap exhausted");return result; }
struct Register { unsigned dword{}; };
struct State { struct {Register rcx,rsp,rax;} gpr; } state;
struct OverrideMxcsr {};
using Body=void*(*)(State*,unsigned,void*);
struct Memory {
    struct Address { unsigned value; };
    template<class T>T load(Address at) { check(readable(at.value,sizeof(T)),"Unreadable fixture byte");T result;std::memcpy(&result,memory.data()+at.value,sizeof(T));return result; }
};
struct Runtime { Memory storage;Memory& memory(){return storage;} } runtime;
struct SkinState {
    std::vector<mw34::skins::Addition> records;
    std::map<std::string,unsigned> selected;
    std::wstring preferences;
    std::set<unsigned> announced;
} additional_skins;
void additional_skins_read() {}
std::wstring additional_skin_wide(const std::string& text) {return {text.begin(),text.end()};}
int WritePrivateProfileStringW(const wchar_t*,const wchar_t*,const wchar_t*,const wchar_t*) {throw std::runtime_error("Fixture must not persist skins");}

unsigned call_guest(unsigned target,std::initializer_list<unsigned> args,bool,const char*) {
    auto first=args.begin();
    if(target==0x44e680)return slots[load(0x605a28)];
    if(target==0x44e6a0)return slots[*first];
    if(target==0x48bda0) {
        if(fail_clear)throw std::runtime_error("Authored clear failure");
        const unsigned w=state.gpr.rcx.dword;
        for(unsigned p=load(w+0x15c);p<load(w+0x160);p+=4) {
            const unsigned row=load(p),label=load(row);
            if(label)memory[label]=0;store(row,0);store(row+4,0);
        }
        store(w+0x160,load(w+0x15c));store(w+0x16c,~0U);return 0;
    }
    if(target==0x48b850) {store(state.gpr.rcx.dword+0x16c,*first);return 0;}
    if(target==0x48bac0) {
        const unsigned w=state.gpr.rcx.dword,row=(load(w+0x160)-load(w+0x15c))/4;
        const unsigned item=gheap_alloc(8,true);
        const char* source=reinterpret_cast<const char*>(memory.data()+*first);
        const unsigned size=unsigned(std::strlen(source)+1),copy=gheap_alloc(size,true);
        write_bytes(copy,source,size);store(item,copy);store(item+4,*(first+1));
        store(load(w+0x160),item);store(w+0x160,load(w+0x160)+4);return row;
    }
    throw std::runtime_error("Unexpected guest call in selector fixture");
}

#define configured_catalog fixture_catalog
#include "../native-overrides/mechlab_skins_stage.inc"
#undef configured_catalog

void* getter(State*,unsigned,void*) {
    getter_argument=load(state.gpr.rsp.dword+4);
    if(fail_getter)throw std::runtime_error("Authored getter failure");
    state.gpr.rax.dword=slots[getter_argument];state.gpr.rsp.dword+=8;return nullptr;
}
unsigned callback_getter() {
    const State before=state;state.gpr.rsp.dword=stack-32;store(stack-28,0);
    try {
        mechlab_skin_body(&state,0x44e6a0,nullptr,getter);
        check(load(stack-28)==0,"Scoped getter argument was not restored");
        check(state.gpr.rsp.dword==stack-24,"Original getter return ABI changed");
        const unsigned result=state.gpr.rax.dword;state=before;return result;
    } catch(...) {state=before;throw;}
}
void* skin_callback(State*,unsigned,void*) {
    const unsigned requested=load(state.gpr.rsp.dword+4);
    store(widget+0x16c,requested);
    // Original callback obtains slot zero before writing its retail skin.
    // The adapter must direct this query to the visible teammate only while
    // that callback executes, never changing ordinary slot-zero queries.
    const unsigned config=callback_getter();store(config+0x10,requested);return nullptr;
}
void stock_rows() {
    store(widget,0x5c1448);store(widget+0x15c,0x300000);store(widget+0x160,0x300020);
    for(unsigned i=0;i<8;++i) {unsigned row=gheap_alloc(8,true);unsigned label=gheap_alloc(8,true);write_bytes(label,"Retail",7);store(row,label);store(row+4,100+i);store(0x300000+i*4,row);}
}
void* populate(State*,unsigned,void*) {stock_rows();return nullptr;}
void choose(unsigned row) {
    state.gpr.rcx.dword=widget;state.gpr.rsp.dword=stack;store(stack+4,row);
    mechlab_skin_body(&state,0x44b1c0,nullptr,skin_callback);
    check(load(stack+4)==row,"Callback input was not restored");
    check(mechlab_skins.selecting==0,"Selection scope leaked");
}
void open_selected() {
    state.gpr.rcx.dword=lab;state.gpr.rsp.dword=stack;
    mechlab_skin_body(&state,0x44cf70,nullptr,populate);
}
}

int main() {
#ifdef _WIN32
    _putenv_s("MW34_ADDITIONAL_SKINS","authored-selector-fixture");
#else
    setenv("MW34_ADDITIONAL_SKINS","authored-selector-fixture",1);
#endif
    write_bytes(0x5e6078+60*3,"bushwacker",11);
    additional_skins.records.push_back({"community.example:sommerset","Sommerset","bushwacker","close","distance"});
    store(slots[0]+4,32);store(slots[0]+0x10,5); // Added Commander, unrelated to ally.
    store(slots[1]+4,3);store(slots[1]+0x10,2);store(0x605a28,1);
    open_selected();
    check(mechlab_skins.chassis=="bushwacker","Ally skin list used Commander's chassis");
    check(mechlab_skin_count(widget)==9,"Sommerset was not appended for Bushwacker ally");
    choose(8);
    check(additional_skins.selected.at("bushwacker")==8,"Added skin identity was not selected");
    check(load(widget+0x16c)==8,"Added label was not retained");
    check(load(slots[1]+0x10)==2,"Added skin entered original save field");
    check(load(slots[0]+0x10)==5,"Ally skin changed Commander");
    choose(4);
    check(!additional_skins.selected.count("bushwacker"),"Retail choice retained added appearance");
    check(load(slots[1]+0x10)==4&&load(slots[0]+0x10)==5,"Retail ally choice targeted wrong slot");
    additional_skins.selected["bushwacker"]=8;fail_getter=true;
    bool threw{};try {choose(3);}catch(const std::runtime_error&){threw=true;}
    check(threw,"Authored getter fault was hidden");
    check(load(stack-28)==0&&load(stack+4)==3,"Fault did not restore guest arguments");
    check(mechlab_skins.selecting==0&&additional_skins.selected.at("bushwacker")==8,"Fault leaked selection scope or preference");
    fail_getter=false;
    state.gpr.rsp.dword=stack;store(stack+4,0);
    mechlab_skin_body(&state,0x44e6a0,nullptr,getter);
    check(state.gpr.rax.dword==slots[0]&&getter_argument==0,"Ordinary Commander getter was redirected");
    state.gpr.rsp.dword=stack;store(stack+4,2);mechlab_skins.selecting=1;
    mechlab_skin_body(&state,0x44e6a0,nullptr,getter);mechlab_skins.selecting=0;
    check(state.gpr.rax.dword==slots[2]&&load(stack+4)==2,"Explicit teammate getter was redirected");
    store(slots[0]+4,3);store(0x605a28,0);open_selected();
    check(mechlab_skins.chassis=="bushwacker"&&mechlab_skin_count(widget)==9,"Commander Bushwacker lost Sommerset");
    choose(8);check(load(slots[0]+0x10)==5,"Commander added skin changed original save field");
    mw34::chassis::Registration registration;registration.id="fixture:mech";registration.base_skin_name="Olive Drab";
    mw34::chassis::fixture_records.push_back(registration);
    stock_rows();store(widget+0x16c,3);store(slots[0]+4,32);mechlab_skins.original_count=8;
    mechlab_skin_base_name(slots[0]);
    check(mechlab_skin_count(widget)==8&&load(widget+0x16c)==3,"Default rename changed row count or selection");
    for(unsigned i=0;i<8;++i) {
        const unsigned row=load(load(widget+0x15c)+i*4),label=load(row);
        check(load(row+4)==100+i,"Default rename changed original userdata");
        check(std::strcmp(reinterpret_cast<const char*>(memory.data()+label),i?"Retail":"Olive Drab")==0,"Default rename changed wrong row");
    }
    check(mechlab_skins.rebuilding==0,"Default rename leaked callback guard");
    fail_clear=true;threw=false;
    try {mechlab_skin_base_name(slots[0]);}catch(const std::runtime_error&){threw=true;}
    check(threw&&mechlab_skins.rebuilding==0,"Rename fault hidden or callback guard leaked");
    std::puts("Mech Lab selector checks passed: active teammate/Commander, original save identity, callback ABI and fault cleanup.");
}
