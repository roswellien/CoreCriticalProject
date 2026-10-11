#pragma once
// Identity-bound heat display CALL observer. Original function executes unchanged.
namespace hud_heat {
static unsigned target=0x4455e0;
static bool enabled=false;
static unsigned count=0,lastScene=0;
static SRWLOCK lock=SRWLOCK_INIT;
static std::ofstream log;
static void __stdcall record(unsigned object,unsigned first,unsigned second,unsigned caller) noexcept {
    State guard;
    if(!enabled || !live || !completedScenes || caller!=0x43c537)return;
    AcquireSRWLockExclusive(&lock);
    try {
        if(count<256 && (!count || completedScenes-lastScene>=60)) {
            RECT crop{};int arrowY=0;unsigned viewport[3]{},barImage=0,meterImage=0;
            short barSize[2]{},meterSize[2]{};
            bool valid=hud_text::read(reinterpret_cast<void *>(object+0x1440),&crop,sizeof(crop)) &&
                hud_text::read(reinterpret_cast<void *>(object+0x15cc+0x18),&arrowY,4) &&
                hud_text::read(reinterpret_cast<void *>(object+0x148c),&barImage,4) &&
                hud_text::read(reinterpret_cast<void *>(object+0x154c),&meterImage,4) &&
                hud_text::read(reinterpret_cast<void *>(barImage+4),barSize,sizeof(barSize)) &&
                hud_text::read(reinterpret_cast<void *>(meterImage+4),meterSize,sizeof(meterSize)) &&
                hud_text::read(reinterpret_cast<void *>(0x8007cc),viewport,sizeof(viewport));
            if(!log.is_open()) {
                const auto path=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-heat.jsonl";
                if(std::filesystem::exists(path))throw std::runtime_error("Heat log not fresh");
                log.open(path,std::ios::binary);
            }
            log<<"{\"seq\":"<<++count<<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()
               <<",\"caller\":"<<caller<<",\"object\":"<<object<<",\"valid\":"<<(valid?"true":"false")
               <<",\"argument_float_bits\":["<<first<<","<<second<<"],\"completed_scenes\":"<<completedScenes
               <<",\"sampling\":\"minimum_60_scenes\",\"phase\":\"after_original_update\",\"result_crop\":["
               <<crop.left<<","<<crop.top<<","<<crop.right<<","<<crop.bottom<<"],\"result_arrow_y\":"<<arrowY
               <<",\"bar_size\":["<<barSize[0]<<","<<barSize[1]<<"],\"meter_size\":["<<meterSize[0]<<","<<meterSize[1]
               <<"],\"viewport\":["<<viewport[0]<<","<<viewport[1]<<"],\"target_stride\":"<<viewport[2]<<"}\n";
            log.flush();lastScene=completedScenes;if(!log)enabled=false;
        }
    } catch(...) {enabled=false;}
    ReleaseSRWLockExclusive(&lock);
}
using Update=unsigned(__fastcall *)(unsigned,int,unsigned,unsigned);
static unsigned __fastcall bridge(unsigned object,int edx,unsigned first,unsigned second) {
    const auto caller=reinterpret_cast<unsigned>(_ReturnAddress());
    const auto result=reinterpret_cast<Update>(target)(object,edx,first,second);
    // Integer-only typed wrapper preserves the admitted ABI. State guards only
    // observation, preserving the original function's FP state and LastError.
    record(object,first,second,caller);
    return result;
}
static unsigned __fastcall fake(unsigned object,int edx,unsigned first,unsigned second) {
    if(object!=37 || edx!=-3 || first!=0x3f000000 || second!=0xbe800000)
        throw std::runtime_error("Heat ABI forwarding arguments");
    SetLastError(0x2468abcd);return 71;
}
static void fixture() {
    const auto saved=target;target=reinterpret_cast<unsigned>(&fake);unsigned result=0;
    __asm {
        push 0xbe800000
        push 0x3f000000
        mov ecx,37
        mov edx,-3
        call bridge
        mov result,eax
    }
    target=saved;
    if(result!=71 || GetLastError()!=0x2468abcd)throw std::runtime_error("Heat ABI forwarding result");
    line("\"event\":\"hud_heat_fixture\",\"passed\":true");
}
static void install() {
    if(!std::filesystem::exists(std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"hud-heat.request"))return;
    const unsigned address=0x43c532;auto *code=reinterpret_cast<unsigned char *>(address);
    unsigned previous{};std::memcpy(&previous,code+1,4);
    if(code[0]!=0xe8 || address+5+previous!=target)throw std::runtime_error("Heat CALL identity mismatch");
    DWORD old{};if(!VirtualProtect(code,5,PAGE_EXECUTE_READWRITE,&old))throw std::runtime_error("Heat CALL protection");
    const unsigned relative=reinterpret_cast<unsigned>(&bridge)-(address+5);std::memcpy(code+1,&relative,4);
    DWORD ignored{};
    if(!VirtualProtect(code,5,old,&ignored) || !FlushInstructionCache(GetCurrentProcess(),code,5))
        throw std::runtime_error("Heat CALL publication");
    enabled=true;line("\"event\":\"hud_heat_installed\",\"replacement_enabled\":false");
}
}
