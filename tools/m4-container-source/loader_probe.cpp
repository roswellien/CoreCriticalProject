#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <string>
#include <fstream>
std::string path(HMODULE module){wchar_t p[32768]{};const auto n=GetModuleFileNameW(module,p,32768);if(!n||n==32768)return "null";const auto bytes=WideCharToMultiByte(CP_UTF8,0,p,n,nullptr,0,nullptr,nullptr);std::string s(bytes,'\0');WideCharToMultiByte(CP_UTF8,0,p,n,s.data(),bytes,nullptr,nullptr);std::string out="\"";for(unsigned char c:s){if(c=='\\')out+='/';else if(c=='\"')out+="\\\"";else if(c<32){char e[8]{};std::snprintf(e,sizeof(e),"\\u%04x",c);out+=e;}else out+=char(c);}return out+'\"';}
unsigned ptr(const void*p){return reinterpret_cast<unsigned>(p);}
int main(int argc,char**argv){
 static_assert(sizeof(void*)==4,"Genuine original32 loader observation");if(argc!=2)return 1;
 const auto crt=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(ptr(crt)!=0x78000000)return 2;
 const auto mfc=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MFC42.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(ptr(mfc)!=0x5f400000)return 3;
 const auto nil=*reinterpret_cast<const unsigned*>(0x5f4ccb54);MEMORY_BASIC_INFORMATION r{},p{};
 if(VirtualQuery(reinterpret_cast<const void*>(0x5f4ccb54),&r,sizeof(r))!=sizeof(r)||VirtualQuery(reinterpret_cast<const void*>(nil),&p,sizeof(p))!=sizeof(p))return 4;
 HMODULE owner{};if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(nil),&owner))return 5;
 std::ofstream file(argv[1],std::ios::binary);file.write(reinterpret_cast<const char*>(0x5f4cc000),4096);if(!file)return 6;
 std::printf("{\"passed\":true,\"process_bits\":32,\"CRT_base\":%u,\"CRT_path\":%s,\"MFC_base\":%u,\"MFC_path\":%s,\"loaded_ordinal540\":%u,\"loaded_ordinal825\":%u,\"loaded_ordinal823\":%u,\"nil_address\":%u,\"nil_value\":%u,\"page\":%u,\"page_bytes\":4096,\"source_region_base\":%u,\"source_allocation_base\":%u,\"source_region_size\":%u,\"source_state\":%lu,\"source_type\":%lu,\"source_protect\":%lu,\"pointee_owner_base\":%u,\"pointee_owner_path\":%s,\"pointee_region_base\":%u,\"pointee_allocation_base\":%u,\"pointee_state\":%lu,\"pointee_type\":%lu,\"pointee_protect\":%lu,\"pointee_bytes_read\":0,\"game_called\":false,\"constructor_called\":false,\"allocator_called\":false}\n",ptr(crt),path(crt).c_str(),ptr(mfc),path(mfc).c_str(),ptr(GetProcAddress(mfc,reinterpret_cast<LPCSTR>(540))),ptr(GetProcAddress(mfc,reinterpret_cast<LPCSTR>(825))),ptr(GetProcAddress(mfc,reinterpret_cast<LPCSTR>(823))),0x5f4ccb54,nil,0x5f4cc000,ptr(r.BaseAddress),ptr(r.AllocationBase),unsigned(r.RegionSize),r.State,r.Type,r.Protect,ptr(owner),path(owner).c_str(),ptr(p.BaseAddress),ptr(p.AllocationBase),p.State,p.Type,p.Protect);
 FreeLibrary(mfc);FreeLibrary(crt);return 0;
}
