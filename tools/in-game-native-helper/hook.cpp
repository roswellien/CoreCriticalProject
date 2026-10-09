// Additive x86 bridge to the actual compiled x64 helper. No authored arithmetic
// result is used here. The admitted 22-byte source stays intact in the game.
#include "protocol.hpp"
#include "../in-game-hook/identity.hpp"
#include <algorithm>
#include <cstdio>

using namespace mw34::live_helper;
using mw34::hook::admitted_image;
using mw34::hook::environment;
using mw34::hook::sha256;
struct Frame { std::uint32_t edi,esi,ebp,saved_esp,ebx,edx,ecx,eax,flags,caller,n; };
static_assert(sizeof(void*) == 4 && offsetof(Frame, flags) == 32 && offsetof(Frame, caller) == 36 && offsetof(Frame, n) == 40);
extern "C" {
Cpu helper_input{}, helper_after{}, helper_test_input{}, helper_test_after{};
std::uint32_t helper_host_esp{}, helper_test_host_esp{}, helper_test_mxcsr{0x1f80}, helper_host_mxcsr{0x1f80};
std::uint16_t helper_test_cw{0x37f};
std::uint32_t helper_test_depth{};
alignas(16) std::uint8_t helper_test_xmm[128]{};
alignas(16) std::uint8_t helper_guest_fx[512]{}, helper_host_fx[512]{}, helper_fx_after[512]{};
alignas(16) std::uint8_t helper_test_host_fx[512]{}, helper_test_fx_after[512]{};
std::uint8_t helper_guest_env[28]{}, helper_host_env[28]{}, helper_env_after[28]{};
std::uint8_t helper_test_host_env[28]{}, helper_test_env_after[28]{};
void mw34_helper_entry(); void helper_enter(); void helper_capture(); void helper_restore();
void helper_test_enter(); void helper_test_capture();
}
namespace {
constexpr std::uint32_t callsite = 0x40516e, prefix_base = 0x405160;
constexpr char call_sha[] = "113fd2486dfadd238e546035e16e8857a923b98ffcaf340faacc7eb4d7f38aad";
constexpr char prefix_sha[] = "c1ac93565fd8ecd512260561f2cc54310e6e3a430394651e42913f4f043a6c43";
constexpr DWORD timeout_ms = 10000;
constexpr std::size_t test_stack_size = 16 * 4096;
struct Handle {
    HANDLE value{};
    explicit Handle(HANDLE h = nullptr) : value(h) {}
    ~Handle() { if (value && value != INVALID_HANDLE_VALUE) CloseHandle(value); }
    Handle(const Handle&) = delete; Handle& operator=(const Handle&) = delete;
};
struct Lock {
    CRITICAL_SECTION* value;
    explicit Lock(CRITICAL_SECTION& s) : value(&s) { EnterCriticalSection(value); }
    ~Lock() { LeaveCriticalSection(value); }
};
HANDLE log_file = INVALID_HANDLE_VALUE, pipe_file = INVALID_HANDLE_VALUE, worker_process{};
DWORD worker_pid{};
CRITICAL_SECTION serial{};
bool initialized{}, live{}, fixture{}, installed{};
std::uint32_t sequence{}, private_original{};
std::uint64_t calls{};
std::filesystem::path capture_directory;
std::uint8_t* shadow_memory{};
std::uint8_t* test_memory{};
std::array<std::uint8_t,4096> shadow_before{}, shadow_after{};
std::array<std::uint8_t,19> original_prefix{}, patched_prefix{};
Request test_request{}; Response test_response{};
std::uint32_t actual_ss_selector{}, actual_ss_base{};
bool actual_ss_valid{};

template<class T> T load(const void* p) { T v{}; std::memcpy(&v,p,sizeof(v)); return v; }
template<class T> std::uint32_t address(T* p) { return reinterpret_cast<std::uint32_t>(p); }
void require(bool value,const char* reason) { if (!value) throw std::runtime_error(reason); }
std::string escaped(const std::string& s) {
    std::string r; constexpr char hex[]="0123456789abcdef";
    for (const unsigned char c:s) {
        if(c=='"'||c=='\\'){r+='\\';r+=static_cast<char>(c);}
        else if(c<32){r+="\\u00";r+=hex[c>>4];r+=hex[c&15];}
        else r+=static_cast<char>(c);
    }
    return r;
}
std::string utf8(const std::wstring& s) {
    const auto n=WideCharToMultiByte(CP_UTF8,0,s.c_str(),static_cast<int>(s.size()),nullptr,0,nullptr,nullptr);
    require(n>0,"Path UTF-8 conversion failed"); std::string r(static_cast<std::size_t>(n),'\0');
    require(WideCharToMultiByte(CP_UTF8,0,s.c_str(),static_cast<int>(s.size()),r.data(),n,nullptr,nullptr)==n,"Path UTF-8 conversion failed");
    return r;
}
std::wstring module_path(HMODULE module) {
    std::array<wchar_t,32768> path{};
    const auto n=GetModuleFileNameW(module,path.data(),static_cast<DWORD>(path.size()));
    require(n>0&&n<path.size(),"Module path unavailable"); return std::wstring(path.data(),n);
}
std::vector<std::uint8_t> read_file(const std::wstring& path) {
    std::ifstream f(std::filesystem::path(path),std::ios::binary|std::ios::ate);
    require(static_cast<bool>(f),"Worker identity file unavailable"); const auto n=f.tellg();
    require(n>0&&n<64*1024*1024,"Worker identity file size rejected");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(n)); f.seekg(0);
    require(static_cast<bool>(f.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()))),"Worker identity file read failed");
    return bytes;
}
void log_line(const std::string& line) {
    DWORD wrote{};
    require(log_file!=INVALID_HANDLE_VALUE&&WriteFile(log_file,line.data(),static_cast<DWORD>(line.size()),&wrote,nullptr)&&
            wrote==line.size()&&FlushFileBuffers(log_file),"Helper evidence log write failed");
}
void fatal(const char* message) noexcept {
    try { log_line("{\"event\":\"fatal\",\"message\":\""+escaped(message)+"\",\"win32\":"+std::to_string(GetLastError())+"}\n"); } catch(...) {}
    OutputDebugStringA(message);
}
void binary(const std::filesystem::path& path,const void* data,std::size_t n) {
    Handle file(CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr)); DWORD wrote{};
    require(file.value!=INVALID_HANDLE_VALUE&&WriteFile(file.value,data,static_cast<DWORD>(n),&wrote,nullptr)&&wrote==n&&FlushFileBuffers(file.value),
            "Fresh helper capture publication failed");
}
void open_log() {
    const auto path=std::filesystem::path(environment(L"MW34_HELPER_LOG"));
    log_file=CreateFileW(path.c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    require(log_file!=INVALID_HANDLE_VALUE,"Fresh helper log path required");
    capture_directory=path.parent_path()/(path.stem().wstring()+L"-captures");
    require(std::filesystem::create_directory(capture_directory),"Fresh helper capture directory required");
}
void cancelled(OVERLAPPED& op) {
    CancelIoEx(pipe_file,&op);
    if(WaitForSingleObject(op.hEvent,1000)!=WAIT_OBJECT_0){fatal("Helper IPC cancellation did not complete");ExitProcess(91);}
}
DWORD finish(OVERLAPPED& op,ULONGLONG deadline) {
    const auto now=GetTickCount64();
    if(now>=deadline){cancelled(op);throw std::runtime_error("Helper IPC deadline exceeded");}
    HANDLE waits[]{op.hEvent,worker_process}; const auto count=worker_process?2U:1U;
    if(WaitForMultipleObjects(count,waits,FALSE,static_cast<DWORD>(deadline-now))!=WAIT_OBJECT_0){
        cancelled(op);throw std::runtime_error("Helper worker exited or IPC timed out");}
    DWORD n{};require(GetOverlappedResult(pipe_file,&op,&n,FALSE)!=FALSE,"Helper IPC completion failed");return n;
}
void transfer(void* data,DWORD n,bool writing,ULONGLONG deadline) {
    auto* cursor=static_cast<std::uint8_t*>(data);
    while(n){
        require(!worker_process||WaitForSingleObject(worker_process,0)==WAIT_TIMEOUT,"Helper worker no longer live");
        Handle event(CreateEventW(nullptr,TRUE,FALSE,nullptr)); require(event.value!=nullptr,"Helper IPC event allocation failed");
        OVERLAPPED op{};op.hEvent=event.value;DWORD done{};
        const auto ok=writing?WriteFile(pipe_file,cursor,n,&done,&op):ReadFile(pipe_file,cursor,n,&done,&op);
        if(!ok){require(GetLastError()==ERROR_IO_PENDING,"Helper IPC transport failed");done=finish(op,deadline);}
        require(done>0&&done<=n,"Helper IPC transfer extent failed");cursor+=done;n-=done;
    }
}
Response exchange(const Request& before) {
    Response result{};const auto deadline=GetTickCount64()+timeout_ms;
    transfer(const_cast<Request*>(&before),sizeof(before),true,deadline);transfer(&result,sizeof(result),false,deadline);
    require(std::memcmp(result.magic,response_magic,8)==0&&result.version==version&&result.bytes==sizeof(result)&&
            result.sequence==before.sequence&&result.worker_pid==worker_pid,"Helper response identity/sequence rejected");
    require(WaitForSingleObject(worker_process,0)==WAIT_TIMEOUT,"Helper worker died before publication");
    require(result.status==0||result.status==2||result.status==3,"Unknown helper worker response status");return result;
}
void connect_worker() {
    const auto name=environment(L"MW34_HELPER_PIPE");require(name.starts_with(L"\\\\.\\pipe\\mw34-helper-"),"Dedicated local helper pipe required");
    pipe_file=CreateNamedPipeW(name.c_str(),PIPE_ACCESS_DUPLEX|FILE_FLAG_OVERLAPPED|FILE_FLAG_FIRST_PIPE_INSTANCE,
        PIPE_TYPE_BYTE|PIPE_READMODE_BYTE|PIPE_WAIT|PIPE_REJECT_REMOTE_CLIENTS,1,sizeof(Response),sizeof(Request),timeout_ms,nullptr);
    require(pipe_file!=INVALID_HANDLE_VALUE,"Helper pipe server creation failed");
    Handle event(CreateEventW(nullptr,TRUE,FALSE,nullptr));require(event.value!=nullptr,"Helper pipe connect event failed");
    OVERLAPPED op{};op.hEvent=event.value;
    if(!ConnectNamedPipe(pipe_file,&op)){const auto error=GetLastError();
        if(error==ERROR_IO_PENDING)finish(op,GetTickCount64()+timeout_ms);else require(error==ERROR_PIPE_CONNECTED,"Helper worker connect failed");}
    ULONG pid{};require(GetNamedPipeClientProcessId(pipe_file,&pid)&&pid&&pid!=GetCurrentProcessId(),"Helper worker process owner unavailable");
    worker_pid=pid;worker_process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,worker_pid);
    require(worker_process!=nullptr,"Helper worker process handle unavailable");BOOL wow64{};
    require(IsWow64Process(worker_process,&wow64)&&!wow64,"Helper worker must be native x64");
    std::array<wchar_t,32768> path{};DWORD count=static_cast<DWORD>(path.size());
    require(QueryFullProcessImageNameW(worker_process,0,path.data(),&count)&&count,"Helper worker image unavailable");
    const auto worker_bytes=read_file(std::wstring(path.data(),count));
    auto hello=request(++sequence,0);hello.pid=GetCurrentProcessId();hello.tid=GetCurrentThreadId();
    const auto result=exchange(hello);require(result.status==0&&!result.complete&&!result.reads&&!result.returns,"Helper handshake rejected or granted false execution credit");
    log_line("{\"event\":\"worker_handshake\",\"worker_pid\":"+std::to_string(worker_pid)+",\"sequence\":"+std::to_string(sequence)+
        ",\"worker_path\":\""+escaped(utf8(std::wstring(path.data(),count)))+"\",\"worker_sha256\":\""+
        sha256(worker_bytes.data(),worker_bytes.size())+"\",\"protocol_version\":1}\n");
}
std::uint8_t* guarded(std::size_t n) {
    auto* p=static_cast<std::uint8_t*>(VirtualAlloc(nullptr,n+8192,MEM_RESERVE,PAGE_NOACCESS));require(p!=nullptr,"Guarded helper stack reservation failed");
    require(VirtualAlloc(p+4096,n,MEM_COMMIT,PAGE_READWRITE)==p+4096,"Guarded helper stack commit failed");return p+4096;
}
std::size_t file_offset(const std::vector<std::uint8_t>& image,std::uint32_t va,std::size_t n) {
    const auto* dos=reinterpret_cast<const IMAGE_DOS_HEADER*>(image.data());
    require(dos->e_magic==IMAGE_DOS_SIGNATURE&&dos->e_lfanew>0&&static_cast<std::size_t>(dos->e_lfanew)+sizeof(IMAGE_NT_HEADERS32)<=image.size(),"Game PE header rejected");
    const auto* nt=reinterpret_cast<const IMAGE_NT_HEADERS32*>(image.data()+dos->e_lfanew);
    require(nt->Signature==IMAGE_NT_SIGNATURE&&nt->OptionalHeader.ImageBase==0x400000&&va>=0x400000,"Game PE base rejected");
    const auto rva=va-0x400000;const auto* sections=IMAGE_FIRST_SECTION(nt);
    for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i){const auto& s=sections[i];
        if(rva>=s.VirtualAddress&&std::uint64_t{rva}+n<=std::uint64_t{s.VirtualAddress}+s.SizeOfRawData){
            const auto offset=static_cast<std::size_t>(s.PointerToRawData)+rva-s.VirtualAddress;
            require(offset+n<=image.size(),"Game source span exceeds file");return offset;}}
    throw std::runtime_error("Game source span not file backed");
}
void prepare_original(const std::vector<std::uint8_t>& image) {
    const auto offset=file_offset(image,prefix_base,original_prefix.size());
    std::memcpy(original_prefix.data(),image.data()+offset,original_prefix.size());
    require(sha256(original_prefix.data(),19)==prefix_sha&&sha256(original_prefix.data()+14,5)==call_sha&&
            original_prefix[14]==0xe8&&caller+load<std::uint32_t>(original_prefix.data()+15)==root,"Exact helper caller route disk identity rejected");
    binary(capture_directory/L"admitted-helper-source.bin",image.data()+mw34::hook::leaf_offset,mw34::hook::leaf_size);
    binary(capture_directory/L"admitted-caller-prefix.bin",original_prefix.data(),original_prefix.size());
    auto* page=static_cast<std::uint8_t*>(VirtualAlloc(nullptr,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
    require(page!=nullptr,"Private original helper code allocation failed");std::memcpy(page,image.data()+mw34::hook::leaf_offset,mw34::hook::leaf_size);
    require(sha256(page,mw34::hook::leaf_size)==mw34::hook::leaf_sha,"Private original helper source differs");
    DWORD old{};require(VirtualProtect(page,4096,PAGE_EXECUTE_READ,&old)&&FlushInstructionCache(GetCurrentProcess(),page,4096),"Private original helper RX transition failed");
    private_original=address(page);shadow_memory=guarded(4096);
}
void source_check() {
    require(sha256(reinterpret_cast<void*>(root),mw34::hook::leaf_size)==mw34::hook::leaf_sha,"Unmodified loaded helper source changed");
    require(!installed||std::memcmp(reinterpret_cast<void*>(prefix_base),patched_prefix.data(),patched_prefix.size())==0,"Patched reviewed helper caller prefix changed");
}
bool owned_caller(const Request& before) {
    HMODULE owner{};
    if(before.caller!=caller||!installed||address(GetModuleHandleW(nullptr))!=0x400000||
       !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
           reinterpret_cast<LPCWSTR>(before.caller),&owner)||owner!=GetModuleHandleW(nullptr))return false;
    return std::memcmp(reinterpret_cast<void*>(prefix_base),patched_prefix.data(),patched_prefix.size())==0&&
        *reinterpret_cast<std::uint8_t*>(callsite)==0xe8&&caller+load<std::uint32_t>(reinterpret_cast<void*>(callsite+1))==address(&mw34_helper_entry);
}
Cpu cpu(const Frame& f) { return {f.eax,f.ecx,f.edx,f.ebx,f.saved_esp+4U,f.ebp,f.esi,f.edi,f.flags,root}; }
Request prepare(const Frame& f,const std::uint8_t* fx,const std::uint8_t* env) {
    auto r=request(++sequence,fixture?1U:2U);r.pid=GetCurrentProcessId();r.tid=GetCurrentThreadId();r.cpu=cpu(f);r.n=f.n;r.caller=f.caller;
    r.memory_seed=r.sequence*71U;std::memcpy(r.fx.data(),fx,512);std::memcpy(r.env.data(),env,28);
    std::uint16_t selector{};
    __asm {
        mov ax, ss
        mov selector, ax
    }
    actual_ss_selector=selector;LDT_ENTRY entry{};
    actual_ss_valid=GetThreadSelectorEntry(GetCurrentThread(),selector,&entry)!=FALSE;
    actual_ss_base=entry.BaseLow|(static_cast<std::uint32_t>(entry.HighWord.Bytes.BaseMid)<<16)|
        (static_cast<std::uint32_t>(entry.HighWord.Bytes.BaseHi)<<24);
    return r;
}
bool same_cpu(const Cpu& a,const Cpu& b) { return std::memcmp(&a,&b,sizeof(a))==0; }
void response_contract(const Request& before,const Response& after) {
    require(after.reads==2&&after.returns==1&&after.complete==1,"Compiled helper route incomplete");
    require(after.events[0].address==virtual_frame+4&&after.events[0].value==before.n&&after.events[0].width==4&&!after.events[0].write&&
            after.events[1].address==virtual_frame&&after.events[1].value==broker&&after.events[1].width==4&&!after.events[1].write,
            "Compiled helper argument/RET event route differs");
    require(after.memory==initial_memory(before),"Compiled helper changed the observed virtual page");
    require(after.fx==before.fx&&after.env==before.env,"Compiled integer helper changed opaque FP/vector transport");
    require(after.cpu.ecx==before.cpu.ecx&&after.cpu.ebx==before.cpu.ebx&&after.cpu.esp==before.cpu.esp+8&&
            after.cpu.ebp==before.cpu.ebp&&after.cpu.esi==before.cpu.esi&&after.cpu.edi==before.cpu.edi&&after.cpu.eip==before.caller&&
            ((after.cpu.flags^before.cpu.flags)&~arithmetic_mask)==0,"Compiled helper preserved CPU/full non-arithmetic flags/RET4 projection differs");
}
void publish(Frame& f,const Cpu& c) { f.eax=c.eax;f.edx=c.edx;f.flags=c.flags; }
DWORD execute_original() {
    __try {helper_enter();return 0;}
    __except(EXCEPTION_EXECUTE_HANDLER){const auto code=GetExceptionCode();helper_restore();return code;}
}
#pragma pack(push,1)
struct Original {
    Cpu literal{},projected{};std::array<std::uint8_t,512>fx{};std::array<std::uint8_t,28>env{};
    std::uint32_t shadow_entry{},capture{},fault{};
};
#pragma pack(pop)
static_assert(sizeof(Original)==632);
Original original(const Request& before) {
    const auto page=initial_memory(before);std::memcpy(shadow_memory,page.data(),page.size());
    const auto stack=address(shadow_memory)+(virtual_frame-memory_base),sentinel=address(&helper_capture);
    std::memcpy(reinterpret_cast<void*>(stack),&sentinel,4);std::memcpy(shadow_before.data(),shadow_memory,4096);
    helper_input=before.cpu;helper_input.esp=stack;helper_input.eip=live?root:private_original;helper_after={};
    std::memcpy(helper_guest_fx,before.fx.data(),512);std::memcpy(helper_guest_env,before.env.data(),28);
    // FXSAVE does not write reserved storage: preserve literal opaque padding
    // in its capture destination before overwriting the hardware-defined fields.
    std::memcpy(helper_fx_after,before.fx.data(),512);std::memcpy(helper_env_after,before.env.data(),28);
    Original result{};result.shadow_entry=stack;result.capture=sentinel;result.fault=execute_original();
    result.literal=helper_after;result.projected=helper_after;std::memcpy(result.fx.data(),helper_fx_after,512);std::memcpy(result.env.data(),helper_env_after,28);
    std::memcpy(shadow_after.data(),shadow_memory,4096);
    require(!result.fault,"Actual original helper faulted on guarded shadow stack");
    require(result.literal.esp==stack+8&&result.literal.eip==sentinel,"Original helper isolated RET4 broker differs");
    require(shadow_before==shadow_after,"Original helper changed the guarded observed page");
    result.projected.esp=before.cpu.esp+8;result.projected.eip=before.caller;
    if(live)source_check();else require(sha256(reinterpret_cast<void*>(private_original),22)==mw34::hook::leaf_sha,"Private original helper code changed");
    return result;
}
void captures(const Request& before,const Response& native,const Original& actual) {
    const auto prefix=capture_directory/(L"call-"+std::to_wstring(before.sequence));
    binary(prefix.wstring()+L".before.bin",&before,sizeof(before));binary(prefix.wstring()+L".native.bin",&native,sizeof(native));
    binary(prefix.wstring()+L".original.bin",&actual,sizeof(actual));
    binary(prefix.wstring()+L".original-memory-before.bin",shadow_before.data(),4096);
    binary(prefix.wstring()+L".original-memory-after.bin",shadow_after.data(),4096);
}
void record(const Request& before,const Response& native,const Original& actual,bool applied,const std::string& reason,
            bool verified=false,const std::string& worker_reason={},const std::string& caller_reason={},const std::string& input_reason={}) {
    const auto prefix=capture_directory/(L"call-"+std::to_wstring(before.sequence));
    log_line("{\"event\":\""+std::string(fixture?"hook_selftest_call":"game_call")+"\",\"call\":"+std::to_string(++calls)+
        ",\"pid\":"+std::to_string(before.pid)+",\"tid\":"+std::to_string(before.tid)+",\"in_game\":"+(live?"true":"false")+
        ",\"native_applied\":"+(applied?"true":"false")+",\"worker_pid\":"+std::to_string(worker_pid)+",\"sequence\":"+std::to_string(before.sequence)+
        ",\"caller_va\":"+std::to_string(before.caller)+",\"n\":"+std::to_string(before.n)+",\"base\":"+std::to_string(before.cpu.ecx)+
        ",\"eax\":"+std::to_string(applied?native.cpu.eax:actual.projected.eax)+",\"edx\":"+std::to_string(applied?native.cpu.edx:actual.projected.edx)+
        ",\"flags\":"+std::to_string(applied?native.cpu.flags:actual.projected.flags)+",\"before_sha256\":\""+sha256(&before,sizeof(before))+
        "\",\"native_sha256\":\""+sha256(&native,sizeof(native))+"\",\"original_sha256\":\""+sha256(&actual,sizeof(actual))+
        "\",\"input_snapshot\":\""+escaped(utf8(prefix.wstring()+L".before.bin"))+"\",\"output_snapshot\":\""+escaped(utf8(prefix.wstring()+L".native.bin"))+
        "\",\"original_snapshot\":\""+escaped(utf8(prefix.wstring()+L".original.bin"))+"\",\"original_memory_before_sha256\":\""+sha256(shadow_before.data(),4096)+
        "\",\"original_memory_after_sha256\":\""+sha256(shadow_after.data(),4096)+"\",\"reason\":\""+escaped(reason)+
        "\",\"worker_rejection_reason\":\""+escaped(worker_reason)+"\",\"caller_rejection_reason\":\""+escaped(caller_reason)+
        "\",\"input_rejection_reason\":\""+escaped(input_reason)+"\",\"actual_ss_selector\":"+std::to_string(actual_ss_selector)+
        ",\"actual_ss_base\":"+std::to_string(actual_ss_base)+",\"actual_ss_queried\":"+(actual_ss_valid?"true":"false")+
        ",\"stack_delta\":8,\"arguments\":1,\"original_compare\":"+(verified?"true":"false")+
        ",\"cpu_full_flags_compared\":"+(verified?"true":"false")+",\"fp512_env28_compared\":"+(verified?"true":"false")+
        ",\"original_memory_bytes_compared\":4096,\"native_reads\":"+std::to_string(native.reads)+",\"native_returns\":"+std::to_string(native.returns)+
        ",\"memory_unchanged\":true,\"fp_compare_scope\":\"opaque512bytes+separateENV28\",\"caller_admission\":\"loaded-game405173;patched-directCALL40516e-resolves-authored-thunk\"}\n");
}
void initialize() {
    require(!initialized,"Helper bridge already initialized");open_log();
    const auto image=admitted_image(environment(L"MW34_GAME_FILE"));InitializeCriticalSection(&serial);prepare_original(image);connect_worker();
    log_line("{\"event\":\"identity\",\"image_sha256\":\""+std::string(mw34::hook::game_sha)+"\",\"source_sha256\":\""+mw34::hook::leaf_sha+
        "\",\"source_va\":"+std::to_string(root)+",\"source_bytes\":22,\"original_call_sha256\":\""+call_sha+
        "\",\"caller_prefix_sha256\":\""+prefix_sha+"\",\"caller_prefix_va\":"+std::to_string(prefix_base)+"}\n");initialized=true;
}
void self_tests() {
    fixture=true;test_memory=guarded(test_stack_size);
    const auto stack=address(test_memory+test_stack_size-4096),sentinel=address(&helper_test_capture);
    constexpr std::array<std::uint32_t,8> flags{0x202,0x202|0xcd5,0x202|0x400,0x202|0x800,0x202|0x801,0x202|0x4d5,0x202|0x8d5,0x202|0xcc0};
    constexpr std::array<std::uint32_t,8> arguments{0,1,15,255,0x05555555,0x7fffffff,0x80000000,0xffffffff};
    constexpr std::array<std::uint16_t,3> control_words{0x27f,0x37f,0xa7f};
    constexpr std::array<std::uint32_t,4> depths{0,1,3,7};
    for(unsigned i=0;i<64;++i){
        std::memset(reinterpret_cast<void*>(stack),0xa5,4096);const auto n=arguments[i%8];
        std::memcpy(reinterpret_cast<void*>(stack),&sentinel,4);std::memcpy(reinterpret_cast<void*>(stack+4),&n,4);
        std::array<std::uint8_t,4096> caller_bytes{};std::memcpy(caller_bytes.data(),reinterpret_cast<void*>(stack),4096);
        helper_test_mxcsr=i&1?0x1fa0:0x1f80;
        helper_test_cw=control_words[i%control_words.size()];helper_test_depth=depths[i%depths.size()];
        for(unsigned byte=0;byte<128;++byte)helper_test_xmm[byte]=static_cast<std::uint8_t>(i*71+byte*29+0x5a);
        helper_test_input={0x13579bdfU^i,0x2468ace0U+i*117871U,0x81726354U-i,0x10293847U^(i*17),stack,
            0x92837465U+i,0x56473829U-i,0xaabbccddU^i,flags[i/8],root};helper_test_after={};
        helper_test_enter();response_contract(test_request,test_response);
        require(same_cpu(helper_test_after,test_response.cpu)&&std::memcmp(helper_test_fx_after,test_response.fx.data(),512)==0&&
                std::memcmp(helper_test_env_after,test_response.env.data(),28)==0&&std::memcmp(caller_bytes.data(),reinterpret_cast<void*>(stack),4096)==0,
                "Helper thunk actual worker CPU/full flags/RET4/opaque FP/caller memory fixture differs");
    }
    log_line("{\"event\":\"hook_thunk_selftest\",\"cases\":64,\"mismatches\":0,\"arguments\":1,\"stack_delta\":8,\"full_flags_compared\":true,"
        "\"direction_and_overflow_flags_tested\":true,\"fp512_env28_preserved\":true,\"populated_x87_depths\":[0,1,3,7],"
        "\"control_words\":[639,895,2687],\"mxcsr_values\":[8064,8096],\"varied_xmm_banks\":8,\"caller_memory_bytes\":4096,"
        "\"in_game\":false,\"native_applied\":false}\n");fixture=false;
}
} // namespace

extern "C" void mw34_helper_dispatch(Frame* frame,std::uint8_t* fx,std::uint8_t* env) {
    Lock hold(serial);
    try {
        require(initialized&&(live||fixture),"Helper thunk outside initialized mode");if(live)source_check();
        const auto before=prepare(*frame,fx,env);const auto native=exchange(before);
        std::string worker_rejection,caller_rejection,input_rejection;
        if(native.status==2){worker_rejection=std::string(native.error,strnlen_s(native.error,sizeof(native.error)));
            if(worker_rejection.empty())worker_rejection="Helper worker rejected actual input";}
        else require(native.status==0,"Helper worker execution failed");
        if(live&&!owned_caller(before))caller_rejection="Actual caller is outside reviewed loaded game direct-CALL40516e ownership";
        if(!actual_ss_valid||actual_ss_base!=0)input_rejection="Actual stack segment does not prove SSBASE zero";
        if((before.cpu.flags&~(0x202U|observed_mask))!=0||(before.cpu.flags&0x202U)!=0x202U)
            input_rejection+=(input_rejection.empty()?"":"; ")+std::string("Captured flags outside measured restorable 202+arithmetic+DF domain");
        const auto actual=original(before);captures(before,native,actual);
        auto rejection=worker_rejection+(worker_rejection.empty()||caller_rejection.empty()?"":"; ")+caller_rejection;
        rejection+=(rejection.empty()||input_rejection.empty()?"":"; ")+input_rejection;
        if(!rejection.empty()){
            require(!fixture,"Synthetic helper fixture rejected");record(before,native,actual,false,rejection,false,worker_rejection,caller_rejection,input_rejection);
            publish(*frame,actual.projected);std::memcpy(fx,actual.fx.data(),512);std::memcpy(env,actual.env.data(),28);return;}
        response_contract(before,native);
        const bool matched=same_cpu(native.cpu,actual.projected)&&native.fx==actual.fx&&native.env==actual.env;
        if(!matched){record(before,native,actual,false,"native-original-state-mismatch");throw std::runtime_error("Helper native/original full CPU/FP/ENV mismatch");}
        // Publish only the actual verified compiled x64 worker result.
        publish(*frame,native.cpu);std::memcpy(fx,native.fx.data(),512);std::memcpy(env,native.env.data(),28);
        if(fixture){test_request=before;test_response=native;std::memcpy(helper_test_fx_after,native.fx.data(),512);
            std::memcpy(helper_test_env_after,native.env.data(),28);}
        record(before,native,actual,live,fixture?"synthetic-worker-original-and-thunk-preflight":"verified-compiled-x64-result-published",true);
    } catch(const std::exception& error){fatal(error.what());ExitProcess(91);}
}
extern "C" DWORD WINAPI mw34_selftest(void*) {
    try{initialize();self_tests();return 0;}catch(const std::exception& error){fatal(error.what());return 90;}
}
extern "C" DWORD WINAPI mw34_install(void*) {
    try {
        initialize();require(address(GetModuleHandleW(nullptr))==0x400000,"Unsupported loaded game base");admitted_image(module_path(nullptr));
        source_check();require(std::memcmp(reinterpret_cast<void*>(prefix_base),original_prefix.data(),original_prefix.size())==0,
                               "Loaded reviewed helper caller differs from admitted file");
        patched_prefix=original_prefix;patched_prefix[14]=0xe8;const auto delta=address(&mw34_helper_entry)-caller;
        std::memcpy(patched_prefix.data()+15,&delta,4);DWORD old{},ignored{};
        require(VirtualProtect(reinterpret_cast<void*>(callsite),5,PAGE_EXECUTE_READWRITE,&old),"Helper call-site protection failed");
        std::memcpy(reinterpret_cast<void*>(callsite),patched_prefix.data()+14,5);
        require(VirtualProtect(reinterpret_cast<void*>(callsite),5,old,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(callsite),5),
                "Helper call-site protection/cache restore failed");installed=true;source_check();live=true;
        log_line("{\"event\":\"installed\",\"pid\":"+std::to_string(GetCurrentProcessId())+",\"entry_va\":"+std::to_string(root)+
            ",\"callsite_va\":"+std::to_string(callsite)+",\"caller_va\":"+std::to_string(caller)+",\"hook_pointer\":"+std::to_string(address(&mw34_helper_entry))+
            ",\"patched_call_bytes\":5,\"patched_source_bytes\":0,\"source_sha256\":\""+mw34::hook::leaf_sha+"\",\"original_call_sha256\":\""+call_sha+
            "\",\"caller_prefix_sha256\":\""+prefix_sha+"\",\"patched_caller_prefix_sha256\":\""+sha256(patched_prefix.data(),19)+
            "\",\"on_disk_game_unchanged\":true,\"synthetic_install_calls\":0,\"replacement\":\"actual-persistent-compiled-x64-worker\"}\n");return 0;
    }catch(const std::exception& error){fatal(error.what());return 90;}
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID) { return TRUE; }
