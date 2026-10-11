#pragma once
// Observe two admitted CALL sites. Tail-jump preserves the original internal ABI.
namespace hud_draw {
static unsigned target=0x55b1f0;
static bool enabled=false;
static unsigned count=0;
static SRWLOCK lock=SRWLOCK_INIT;
static std::ofstream log;
static HudTransitions transitions;
static void __stdcall record(unsigned image,int x,int y,unsigned flags,RECT *rectangle,unsigned object,unsigned caller) noexcept {
    State guard;
    if(!enabled || !live || completedScenes<=hud_text::skipScenes || (caller!=0x5a116e && caller!=0x5a1197))return;
    AcquireSRWLockExclusive(&lock);
    try {
        if(count<512) {
            unsigned ownedImage=0,fontHandle=0,dispatch=0,viewport[3]{};
            short dimensions[2]{};RECT rect{};LOGFONTA font{};
            bool valid=hud_text::read(reinterpret_cast<void *>(object+0x248),&ownedImage,4) && ownedImage==image &&
                hud_text::read(reinterpret_cast<void *>(image+4),dimensions,4) &&
                hud_text::read(rectangle,&rect,sizeof(rect)) &&
                hud_text::read(reinterpret_cast<void *>(object+0x258),&fontHandle,4) &&
                hud_text::read(reinterpret_cast<void *>(0x800824),&dispatch,4) &&
                hud_text::read(reinterpret_cast<void *>(0x8007cc),viewport,sizeof(viewport));
            unsigned char bytes[512]{};size_t size=0;
            for(;size<sizeof(bytes);++size) {
                if(!hud_text::read(reinterpret_cast<void *>(object+0x34+size),bytes+size,1)) {valid=false;break;}
                if(!bytes[size])break;
            }
            if(size==sizeof(bytes))valid=false;
            if(GetObjectA(reinterpret_cast<HFONT>(fontHandle),sizeof(font),&font)!=sizeof(font))valid=false;
            const auto signature=hud_text::hex(bytes,size)+":"+std::to_string(image)+":"+
                std::to_string(x)+":"+std::to_string(y)+":"+std::to_string(flags)+":"+
                hud_text::hex(reinterpret_cast<const unsigned char *>(dimensions),sizeof(dimensions))+":"+
                hud_text::hex(reinterpret_cast<const unsigned char *>(&rect),sizeof(rect))+":"+
                hud_text::hex(reinterpret_cast<const unsigned char *>(viewport),sizeof(viewport))+":"+
                std::to_string(dispatch)+":"+std::to_string(font.lfHeight);
            const auto key=std::to_string(caller)+":"+std::to_string(object);
            if(valid && !transitions.changed(key,signature)) {
                ReleaseSRWLockExclusive(&lock);return;
            }
            if(!log.is_open()) {
                const auto path=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-draw.jsonl";
                if(std::filesystem::exists(path))throw std::runtime_error("HUD draw log not fresh");
                log.open(path,std::ios::binary);
            }
            log<<"{\"seq\":"<<++count<<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()
               <<",\"sampling\":\"bounded_source_transitions\",\"per_source_limit\":16,\"caller\":"<<caller<<",\"object\":"<<object<<",\"image\":"<<image
               <<",\"valid\":"<<(valid?"true":"false")<<",\"text_hex\":\""<<hud_text::hex(bytes,size)<<"\""
               <<",\"x\":"<<x<<",\"y\":"<<y<<",\"flags\":"<<flags<<",\"image_size\":["<<dimensions[0]<<","<<dimensions[1]
               <<"],\"rectangle_argument\":["<<rect.left<<","<<rect.top<<","<<rect.right<<","<<rect.bottom
               <<"],\"viewport\":["<<viewport[0]<<","<<viewport[1]<<"],\"target_stride\":"<<viewport[2]
               <<",\"dispatch\":"<<dispatch<<",\"font_height\":"<<font.lfHeight
               <<",\"completed_scenes\":"<<completedScenes<<",\"successful_draws\":"<<successfulDraws<<"}\n";
            log.flush();if(!log)enabled=false;
        }
    } catch(...) {enabled=false;}
    ReleaseSRWLockExclusive(&lock);
}
static __declspec(naked) void bridge() {
    __asm {
        pushfd
        pushad
        mov eax,esp
        push dword ptr [eax+36] // Original CALL return site.
        push dword ptr [eax+4]  // Text object in caller ESI.
        push dword ptr [eax+48] // Rectangle stack argument.
        push dword ptr [eax+44] // Flags stack argument.
        push dword ptr [eax+40] // Y stack argument.
        push dword ptr [eax+20] // X in EDX.
        push dword ptr [eax+24] // Image in ECX.
        call record
        popad
        popfd
        jmp dword ptr [target]
    }
}
static unsigned __fastcall fake(unsigned image,int x,int y,unsigned flags,RECT *rect) {
    if(image!=37 || x!=-3 || y!=19 || flags!=5 || !rect || rect->right!=41)
        throw std::runtime_error("HUD draw register/stack forwarding");
    rect->right=43;SetLastError(0x76543210);return 71;
}
static void fixture() {
    const auto saved=target;target=reinterpret_cast<unsigned>(&fake);
    RECT rect{};rect.right=41;auto *pointer=&rect;unsigned result=0;
    __asm {
        push esi
        mov esi,123
        push pointer
        push 5
        push 19
        mov edx,-3
        mov ecx,37
        call bridge
        mov result,eax
        pop esi
    }
    target=saved;
    if(result!=71 || rect.right!=43 || GetLastError()!=0x76543210)
        throw std::runtime_error("HUD draw forwarding output");
    line("\"event\":\"hud_draw_fixture\",\"passed\":true");
}
static void install() {
    if(!std::filesystem::exists(std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-text.request"))return;
    for(unsigned address:{0x5a1169u,0x5a1192u}) {
        auto *code=reinterpret_cast<unsigned char *>(address);unsigned relative{};std::memcpy(&relative,code+1,4);
        if(code[0]!=0xe8 || address+5+relative!=0x55b1f0)throw std::runtime_error("HUD draw CALL identity mismatch");
    }
    for(unsigned address:{0x5a1169u,0x5a1192u}) {
        auto *code=reinterpret_cast<unsigned char *>(address);DWORD old{};
        if(!VirtualProtect(code,5,PAGE_EXECUTE_READWRITE,&old))throw std::runtime_error("HUD draw CALL protection");
        const unsigned relative=reinterpret_cast<unsigned>(&bridge)-(address+5);
        std::memcpy(code+1,&relative,4);DWORD ignored{};
        if(!VirtualProtect(code,5,old,&ignored) || !FlushInstructionCache(GetCurrentProcess(),code,5))
            throw std::runtime_error("HUD draw CALL publication");
    }
    enabled=true;line("\"event\":\"hud_draw_installed\",\"replacement_enabled\":false");
}
}
