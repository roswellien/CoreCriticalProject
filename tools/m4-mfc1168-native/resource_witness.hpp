// Actual AMD64 Windows providers and owned TLS/CS lifetime observations.
#include <type_traits>
static unsigned resource_serial{};
static CRITICAL_SECTION*resource_CS{};
static const std::array<const char*,9>resource_names{"TlsAlloc","TlsSetValue","TlsGetValue","TlsFree","InitializeCriticalSection","EnterCriticalSection","LeaveCriticalSection","DeleteCriticalSection","GetACP"};
static void resource_identity(unsigned serial,unsigned kind,void*target,const char*side){
 HMODULE owner{};require(GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<const char*>(target),&owner),"Actual native provider owning image");MEMORY_BASIC_INFORMATION mbi{};require(VirtualQuery(target,&mbi,sizeof(mbi))==sizeof(mbi)&&mbi.AllocationBase==owner&&mbi.Type==MEM_IMAGE&&mbi.State==MEM_COMMIT,"Actual native executable image identity");char path[32768]{};auto length=GetModuleFileNameA(owner,path,sizeof(path));require(length&&length<sizeof(path),"Whole actual native owner path");auto bytes=read_file(path);const auto digest=m4::sha256(bytes);auto stem="resources/"+std::to_string(serial)+"/"+side;const std::array<std::uint64_t,9>words{1,kind,reinterpret_cast<std::uintptr_t>(target),reinterpret_cast<std::uintptr_t>(owner),reinterpret_cast<std::uintptr_t>(mbi.BaseAddress),mbi.RegionSize,mbi.State,mbi.Protect,mbi.Type};dump(stem+"-identity.bin",words.data(),sizeof(words));dump(stem+"-path.txt",path,length);dump(stem+"-sha256.txt",digest.data(),digest.size());dump(stem+"-entry64.bin",target,64);
}
template<class F>static auto resource_call(unsigned kind,void*target,std::uint64_t arg0,std::uint64_t arg1,F fn){
 const auto serial=resource_serial++;const auto error=GetLastError();std::array<std::byte,40>before{},after{};if(resource_CS)std::memcpy(before.data(),resource_CS,40);resource_identity(serial,kind,target,"before");SetLastError(error);std::uint64_t result{};using T=std::invoke_result_t<F>;
 if constexpr(std::is_void_v<T>){fn();}else{auto value=fn();if constexpr(std::is_pointer_v<T>)result=reinterpret_cast<std::uintptr_t>(value);else result=std::uint64_t(value);}
 const auto actual_error=GetLastError();if(resource_CS)std::memcpy(after.data(),resource_CS,40);resource_identity(serial,kind,target,"after");const std::array<std::uint64_t,8>w{1,serial,kind,arg0,arg1,result,GetCurrentThreadId(),actual_error};const auto stem="resources/"+std::to_string(serial)+"/";dump(stem+"call.bin",w.data(),sizeof(w));dump(stem+"CS-before40.bin",before.data(),40);dump(stem+"CS-after40.bin",after.data(),40);SetLastError(actual_error);
 if constexpr(!std::is_void_v<T>){if constexpr(std::is_pointer_v<T>)return reinterpret_cast<T>(result);else return static_cast<T>(result);}
}
static DWORD mf_TlsAlloc(){return resource_call(0,reinterpret_cast<void*>(&TlsAlloc),0,0,[]{return TlsAlloc();});}
static BOOL mf_TlsSetValue(DWORD index,void*value){return resource_call(1,reinterpret_cast<void*>(&TlsSetValue),index,reinterpret_cast<std::uintptr_t>(value),[&]{return TlsSetValue(index,value);});}
static void*mf_TlsGetValue(DWORD index){return resource_call(2,reinterpret_cast<void*>(&TlsGetValue),index,0,[&]{return TlsGetValue(index);});}
static BOOL mf_TlsFree(DWORD index){return resource_call(3,reinterpret_cast<void*>(&TlsFree),index,0,[&]{return TlsFree(index);});}
static void mf_InitializeCriticalSection(CRITICAL_SECTION*p){resource_call(4,reinterpret_cast<void*>(&InitializeCriticalSection),reinterpret_cast<std::uintptr_t>(p),0,[&]{InitializeCriticalSection(p);});}
static void mf_EnterCriticalSection(CRITICAL_SECTION*p){resource_call(5,reinterpret_cast<void*>(&EnterCriticalSection),reinterpret_cast<std::uintptr_t>(p),0,[&]{EnterCriticalSection(p);});}
static void mf_LeaveCriticalSection(CRITICAL_SECTION*p){resource_call(6,reinterpret_cast<void*>(&LeaveCriticalSection),reinterpret_cast<std::uintptr_t>(p),0,[&]{LeaveCriticalSection(p);});}
static void mf_DeleteCriticalSection(CRITICAL_SECTION*p){resource_call(7,reinterpret_cast<void*>(&DeleteCriticalSection),reinterpret_cast<std::uintptr_t>(p),0,[&]{DeleteCriticalSection(p);});}
static unsigned mf_GetACP(){return resource_call(8,reinterpret_cast<void*>(&GetACP),0,0,[]{return GetACP();});}
