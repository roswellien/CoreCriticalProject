#pragma once
#include "hud_sampling.hpp"
// Observe the identity-bound generic text cache, without assigning HUD semantics.
namespace hud_text {
using DrawText = int(WINAPI *)(HDC,LPSTR,int,LPRECT,UINT);
static DrawText original{};
static bool enabled=false;
static unsigned count=0;
static unsigned skipScenes=0;
static SRWLOCK lock=SRWLOCK_INIT;
static std::ofstream log;
static HudTransitions transitions(8);
static bool read(const void *source,void *target,size_t bytes) noexcept {
    SIZE_T copied{};
    return source && ReadProcessMemory(GetCurrentProcess(),source,target,bytes,&copied) && copied==bytes;
}
static std::string hex(const unsigned char *bytes,size_t length) {
    static const char digits[]="0123456789abcdef";
    std::string result;result.reserve(length*2);
    for(size_t i=0;i<length;++i) {result+=digits[bytes[i]>>4];result+=digits[bytes[i]&15];}
    return result;
}
static int WINAPI observe(HDC dc,LPSTR text,int length,LPRECT rectangle,UINT flags) {
    const auto caller=reinterpret_cast<unsigned>(_ReturnAddress());
    bool selected=false,valid=false;
    std::string value,fontFace,capturedText;
    RECT before{};LOGFONTA font{};COLORREF color=CLR_INVALID;UINT codepage=0;
    {
        State guard;
        selected=enabled && live && completedScenes>skipScenes &&
            (caller==0x5a0895 || caller==0x5a0b48 || caller==0x5a0bb8);
        if(selected) {
            try {
                unsigned char bytes[512]{};size_t size=0;
                valid=read(rectangle,&before,sizeof(before));
                if(length>=0 && length<=512) {size=static_cast<size_t>(length);valid=valid && (!size || read(text,bytes,size));}
                else if(length==-1) {
                    for(;size<sizeof(bytes);++size) {if(!read(text+size,bytes+size,1)) {valid=false;break;}if(!bytes[size])break;}
                    if(size==sizeof(bytes))valid=false;
                } else valid=false;
                if(valid) {value=hex(bytes,size);capturedText.assign(reinterpret_cast<const char *>(bytes),size);}
                const auto object=GetCurrentObject(dc,OBJ_FONT);
                if(GetObjectA(object,sizeof(font),&font)!=sizeof(font))valid=false;
                size_t faceLength=0;while(faceLength<LF_FACESIZE && font.lfFaceName[faceLength])++faceLength;
                fontFace=hex(reinterpret_cast<unsigned char *>(font.lfFaceName),faceLength);
                color=GetTextColor(dc);codepage=GetACP();
            } catch(...) {valid=false;}
        }
    }
    const int result=original(dc,text,length,rectangle,flags);
    if(selected) {
        State guard;
        AcquireSRWLockExclusive(&lock);
        try {
            if(count<256) {
                RECT after{};valid=valid && read(rectangle,&after,sizeof(after));
                const auto signature=value+":"+fontFace+":"+std::to_string(font.lfHeight)+":"+
                    std::to_string(font.lfWeight)+":"+std::to_string(font.lfQuality)+":"+
                    std::to_string(color)+":"+std::to_string(flags)+":"+std::to_string(result)+":"+
                    hex(reinterpret_cast<const unsigned char *>(&before),sizeof(before))+":"+
                    hex(reinterpret_cast<const unsigned char *>(&after),sizeof(after));
                // Pattern buckets separate changing range text from numeric counters
                // even when the original cache reuses a DC. No gameplay meaning is assigned.
                const auto key=std::to_string(caller)+":"+std::to_string(reinterpret_cast<unsigned>(dc))+":"+
                    HudTransitions::pattern(capturedText);
                if(valid && !transitions.changed(key,signature)) {
                    ReleaseSRWLockExclusive(&lock);return result;
                }
                if(!log.is_open()) {
                    const auto path=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-text.jsonl";
                    if(std::filesystem::exists(path))throw std::runtime_error("HUD text log not fresh");
                    log.open(path,std::ios::binary);
                }
                log<<"{\"seq\":"<<++count<<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()
                   <<",\"sampling\":\"bounded_source_transitions\",\"per_source_limit\":8,\"caller\":"<<caller<<",\"completed_scenes\":"<<completedScenes<<",\"successful_draws\":"<<successfulDraws
                   <<",\"valid\":"<<(valid?"true":"false")<<",\"text_hex\":\""<<value<<"\",\"codepage\":"<<codepage
                   <<",\"font_face_hex\":\""<<fontFace<<"\",\"font_height\":"<<font.lfHeight<<",\"font_weight\":"<<font.lfWeight
                   <<",\"font_quality\":"<<static_cast<unsigned>(font.lfQuality)<<",\"text_color\":"<<color
                   <<",\"flags\":"<<flags<<",\"result\":"<<result
                   <<",\"rect_before\":["<<before.left<<","<<before.top<<","<<before.right<<","<<before.bottom
                   <<"],\"rect_after\":["<<after.left<<","<<after.top<<","<<after.right<<","<<after.bottom<<"]}\n";
                log.flush();if(!log)enabled=false;
            }
        } catch(...) {enabled=false;}
        ReleaseSRWLockExclusive(&lock);
    }
    return result;
}
static int WINAPI fake(HDC,LPSTR text,int length,LPRECT rectangle,UINT flags) {
    if(length!=3 || flags!=DT_MODIFYSTRING)throw std::runtime_error("HUD text forwarding arguments");
    text[0]='X';rectangle->right=37;SetLastError(0x1234abcd);return 19;
}
static void fixture() {
    HudTransitions sample;
    if(!sample.changed("1","A") || sample.changed("1","A") || !sample.changed("1","B") ||
       !sample.changed("1","A") || !sample.changed("2","A"))
        throw std::runtime_error("HUD transition sampling fixture failed");
    HudTransitions bounded(2);
    if(!bounded.changed("range","1") || !bounded.changed("range","2") || bounded.changed("range","3") ||
       !bounded.changed("counter","200") || !bounded.changed("counter","199") ||
       HudTransitions::pattern("Target (784m)")!=HudTransitions::pattern("Target (20m)"))
        throw std::runtime_error("HUD per-source isolation fixture failed");
    const auto saved=original;original=fake;
    char text[8]="abc";RECT rectangle{};
    const auto result=observe(nullptr,text,3,&rectangle,DT_MODIFYSTRING);
    original=saved;
    if(result!=19 || text[0]!='X' || rectangle.right!=37 || GetLastError()!=0x1234abcd)
        throw std::runtime_error("HUD text forwarding fixture failed");
    line("\"event\":\"hud_text_fixture\",\"passed\":true");
}
static void install() {
    const auto request=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-text.request";
    if(!std::filesystem::exists(request))return;
    std::ifstream selection(request);unsigned requested=0;
    if(selection>>requested) {
        if(requested>36000)throw std::runtime_error("HUD scene delay exceeds budget");
        skipScenes=requested;
    }
    auto **slot=reinterpret_cast<void **>(0x5bb6f8);
    original=reinterpret_cast<DrawText>(*slot);
    if(reinterpret_cast<void *>(original)!=reinterpret_cast<void *>(GetProcAddress(GetModuleHandleW(L"user32.dll"),"DrawTextA")))
        throw std::runtime_error("Unsupported DrawTextA provider");
    DWORD old{};if(!VirtualProtect(slot,4,PAGE_READWRITE,&old))throw std::runtime_error("HUD text IAT protection");
    auto *previous=InterlockedExchangePointer(slot,reinterpret_cast<void *>(&observe));DWORD ignored{};
    if(previous!=reinterpret_cast<void *>(original) || !VirtualProtect(slot,4,old,&ignored))throw std::runtime_error("HUD text IAT publication");
    enabled=true;
    line("\"event\":\"hud_text_installed\",\"iat_va\":6010616,\"semantic_telemetry_recovered\":false");
}
}
