#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <string>

std::string json_path(HMODULE module){
 wchar_t path[32768]{};const auto n=GetModuleFileNameW(module,path,32768);
 if(!n||n==32768)return "null";
 const auto bytes=WideCharToMultiByte(CP_UTF8,0,path,n,nullptr,0,nullptr,nullptr);
 std::string utf8(bytes,'\0');WideCharToMultiByte(CP_UTF8,0,path,n,utf8.data(),bytes,nullptr,nullptr);
 std::string result="\"";
 for(unsigned char c:utf8){if(c=='\\')result+='/';else if(c=='\"')result+="\\\"";else if(c<32){char encoded[8]{};std::snprintf(encoded,sizeof(encoded),"\\u%04x",c);result+=encoded;}else result+=char(c);}
 return result+'\"';
}
std::uintptr_t ptr(const void*value){return reinterpret_cast<std::uintptr_t>(value);}
void bytes(const unsigned char*value,unsigned size){std::printf("\"");for(unsigned i=0;i<size;++i)std::printf("%02x",value[i]);std::printf("\"");}
int main(){
 static_assert(sizeof(void*)==4,"Genuine original32 loader probe");
 const auto crt=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
 if(!crt){std::printf("{\"passed\":false,\"stage\":\"load_exact_CRT\",\"error\":%lu}\n",GetLastError());return 1;}
 const auto mfc=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MFC42.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
 if(!mfc){std::printf("{\"passed\":false,\"stage\":\"load_exact_MFC\",\"error\":%lu}\n",GetLastError());return 2;}
 const auto cb=ptr(crt),mb=ptr(mfc);
 const auto allocation=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(823)),release=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(825));
 std::printf("{\"passed\":true,\"process_bits\":32,\"CRT_base\":%lu,\"CRT_path\":%s,\"MFC_base\":%lu,\"MFC_path\":%s,\"MFC_allocator_export823\":%lu,\"MFC_free_export825\":%lu,\"MFC_initialized_handler\":%lu,\"bindings\":[",unsigned long(cb),json_path(crt).c_str(),unsigned long(mb),json_path(mfc).c_str(),unsigned long(ptr(allocation)),unsigned long(ptr(release)),*reinterpret_cast<const unsigned long*>(mb+0x98970));
 const char*names[]{"malloc","free"};const unsigned offsets[]{0x9814c,0x98148};
 for(unsigned i=0;i<2;++i){
  const auto target=*reinterpret_cast<const unsigned long*>(mb+offsets[i]);const auto named=GetProcAddress(crt,names[i]);HMODULE owner{};
  if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(target),&owner))return 3;
  const auto owner_named=GetProcAddress(owner,names[i]);MEMORY_BASIC_INFORMATION region{};
  if(VirtualQuery(reinterpret_cast<const void*>(target),&region,sizeof(region))!=sizeof(region))return 4;
  std::printf("%s{\"name\":\"%s\",\"MFC_IAT_slot\":%lu,\"actual_loader_target\":%lu,\"exact_staged_CRT_named_export\":%lu,\"actual_owner_base\":%lu,\"actual_owner_path\":%s,\"actual_owner_named_export\":%lu,\"region_base\":%lu,\"region_allocation_base\":%lu,\"region_size\":%lu,\"region_state\":%lu,\"region_type\":%lu,\"region_protect\":%lu,\"target_first32_hex\":",i?",":"",names[i],unsigned long(mb+offsets[i]),target,unsigned long(ptr(named)),unsigned long(ptr(owner)),json_path(owner).c_str(),unsigned long(ptr(owner_named)),unsigned long(ptr(region.BaseAddress)),unsigned long(ptr(region.AllocationBase)),unsigned long(region.RegionSize),region.State,region.Type,region.Protect);
  bytes(reinterpret_cast<const unsigned char*>(target),32);std::printf("}");
 }
 std::printf("],\"game_functions_called\":false,\"allocator_called\":false,\"raw_bound_targets_executed\":false}\n");
 FreeLibrary(mfc);FreeLibrary(crt);return 0;
}
