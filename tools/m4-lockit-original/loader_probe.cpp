#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <string>
#include <fstream>
#include <filesystem>

static unsigned ptr(const void*p){return reinterpret_cast<unsigned>(p);}
static std::string path(HMODULE module){
 wchar_t p[32768]{};const auto n=GetModuleFileNameW(module,p,32768);if(!n||n==32768)return "null";
 const auto bytes=WideCharToMultiByte(CP_UTF8,0,p,n,nullptr,0,nullptr,nullptr);std::string s(bytes,'\0');WideCharToMultiByte(CP_UTF8,0,p,n,s.data(),bytes,nullptr,nullptr);
 std::string out="\"";for(unsigned char c:s){if(c=='\\')out+='/';else if(c=='\"')out+="\\\"";else if(c<32){char e[8]{};std::snprintf(e,sizeof(e),"\\u%04x",c);out+=e;}else out+=char(c);}return out+'\"';
}
static bool save(const std::filesystem::path&out,unsigned address,unsigned size){std::ofstream f(out,std::ios::binary);f.write(reinterpret_cast<const char*>(address),size);return bool(f);}
int main(int argc,char**argv){
 static_assert(sizeof(void*)==4,"Authentic original32 loader state");if(argc!=2)return 1;const std::filesystem::path out(argv[1]);std::filesystem::create_directory(out);
 const auto crt=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(ptr(crt)!=0x78000000)return 2;
 const auto msvcp=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCP50.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(ptr(msvcp)!=0x780c0000)return 3;
 const auto ctor=GetProcAddress(msvcp,"??0_Lockit@std@@QAE@XZ"),dtor=GetProcAddress(msvcp,"??1_Lockit@std@@QAE@XZ");if(ptr(ctor)!=0x7810a290||ptr(dtor)!=0x7810a350)return 4;
 const auto state=*reinterpret_cast<const unsigned*>(0x78145658);unsigned cs[6]{};std::memcpy(cs,reinterpret_cast<const void*>(0x78145640),24);
 for(const auto page:{0x7810a000u,0x78145000u,0x78146000u}){char name[64]{};std::snprintf(name,sizeof(name),"post-DllMain-%08x-page.bin",page);if(!save(out/name,page,4096))return 5;}
 if(!save(out/"state-and-CS.bin",0x78145640,28))return 6;
 std::ofstream f(out/"observations.json");f<<"{\"passed\":true,\"process_bits\":32,\"CRT_base\":"<<ptr(crt)<<",\"CRT_path\":"<<path(crt)<<",\"MSVCP_base\":"<<ptr(msvcp)<<",\"MSVCP_path\":"<<path(msvcp)<<",\"constructor\":"<<ptr(ctor)<<",\"destructor\":"<<ptr(dtor)<<",\"post_DllMain_state\":"<<state<<",\"thread_id\":"<<GetCurrentThreadId()<<",\"critical_section\":[";
 for(unsigned n=0;n<6;++n){if(n)f<<',';f<<cs[n];}f<<"],\"pages\":[";unsigned count{};
 for(const auto page:{0x7810a000u,0x78145000u,0x78146000u}){MEMORY_BASIC_INFORMATION m{};if(VirtualQuery(reinterpret_cast<const void*>(page),&m,sizeof(m))!=sizeof(m))return 7;if(count++)f<<',';f<<"{\"page\":"<<page<<",\"allocation_base\":"<<ptr(m.AllocationBase)<<",\"region_base\":"<<ptr(m.BaseAddress)<<",\"region_size\":"<<unsigned(m.RegionSize)<<",\"state\":"<<m.State<<",\"type\":"<<m.Type<<",\"protection\":"<<m.Protect<<'}';}
 struct Import{unsigned cell;const char*name;const char*lib;};const Import imports[]={{0x78146184,"LeaveCriticalSection","KERNEL32.dll"},{0x7814618c,"InterlockedExchange","KERNEL32.dll"},{0x78146190,"InitializeCriticalSection","KERNEL32.dll"},{0x78146194,"Sleep","KERNEL32.dll"},{0x78146198,"EnterCriticalSection","KERNEL32.dll"},{0x78146278,"__dllonexit","MSVCRT.dll"},{0x7814627c,"_onexit","MSVCRT.dll"}};
 f<<"],\"imports\":[";count=0;for(const auto&i:imports){auto actual=*reinterpret_cast<const unsigned*>(i.cell);HMODULE owner{};if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(actual),&owner))return 8;const auto declared=GetModuleHandleA(i.lib);const auto resolved=GetProcAddress(declared,i.name);if(actual!=ptr(resolved))return 9;if(count++)f<<',';f<<"{\"cell\":"<<i.cell<<",\"symbol\":\""<<i.name<<"\",\"library\":\""<<i.lib<<"\",\"target\":"<<actual<<",\"declared_base\":"<<ptr(declared)<<",\"declared_path\":"<<path(declared)<<",\"resolved_export\":"<<ptr(resolved)<<",\"actual_owner_base\":"<<ptr(owner)<<",\"actual_owner_path\":"<<path(owner)<<'}';}
 f<<"],\"state_seeded\":false,\"constructor_called\":false,\"game_called\":false}\n";if(!f)return 10;f.close();std::printf("{\"passed\":true,\"state\":%u,\"recursion\":%u,\"owner_thread\":%u}\n",state,cs[2],cs[3]);
 FreeLibrary(msvcp);FreeLibrary(crt);return 0;
}
