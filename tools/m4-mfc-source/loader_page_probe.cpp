#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <string>
#include <fstream>
int main(int argc,char**argv){
 static_assert(sizeof(void*)==4);
 if(argc!=2)return 1;
 auto crt=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(reinterpret_cast<std::uintptr_t>(crt)!=0x78000000)return 2;
 auto mfc=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MFC42.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);if(reinterpret_cast<std::uintptr_t>(mfc)!=0x5f400000)return 3;
 std::ofstream out(argv[1],std::ios::binary);out.write(reinterpret_cast<const char*>(0x5f498000),4096);if(!out)return 4;
 auto dos=reinterpret_cast<const IMAGE_DOS_HEADER*>(mfc);auto nt=reinterpret_cast<const IMAGE_NT_HEADERS32*>(reinterpret_cast<std::uintptr_t>(mfc)+dos->e_lfanew);const auto&dd=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];auto desc=reinterpret_cast<const IMAGE_IMPORT_DESCRIPTOR*>(reinterpret_cast<std::uintptr_t>(mfc)+dd.VirtualAddress);
 std::printf("{\"process_bits\":32,\"base\":%lu,\"imports\":[",unsigned long(reinterpret_cast<std::uintptr_t>(mfc)));bool first=true;
 for(;desc->Name;++desc){const auto lib=reinterpret_cast<const char*>(reinterpret_cast<std::uintptr_t>(mfc)+desc->Name);auto owner=GetModuleHandleA(lib);if(!owner)return 5;auto original=reinterpret_cast<const IMAGE_THUNK_DATA32*>(reinterpret_cast<std::uintptr_t>(mfc)+desc->OriginalFirstThunk);auto thunk=reinterpret_cast<const IMAGE_THUNK_DATA32*>(reinterpret_cast<std::uintptr_t>(mfc)+desc->FirstThunk);
  for(unsigned i=0;original[i].u1.AddressOfData;++i){const auto slot=reinterpret_cast<std::uintptr_t>(&thunk[i]);if(slot<0x5f498000||slot>=0x5f499000)continue;const auto ordinal=IMAGE_SNAP_BY_ORDINAL32(original[i].u1.Ordinal)?IMAGE_ORDINAL32(original[i].u1.Ordinal):0;const char*name=ordinal?nullptr:reinterpret_cast<const IMAGE_IMPORT_BY_NAME*>(reinterpret_cast<std::uintptr_t>(mfc)+original[i].u1.AddressOfData)->Name;const auto target=GetProcAddress(owner,ordinal?reinterpret_cast<LPCSTR>(ordinal):name);if(reinterpret_cast<std::uintptr_t>(target)!=thunk[i].u1.Function)return 6;
   std::printf("%s{\"slot\":%lu,\"library\":\"%s\",\"name\":%s%s%s,\"ordinal\":%u,\"target\":%lu,\"declared_module\":%lu}",first?"":",",unsigned long(slot),lib,name?"\"":"",name?name:"null",name?"\"":"",ordinal,unsigned long(thunk[i].u1.Function),unsigned long(reinterpret_cast<std::uintptr_t>(owner)));first=false;
  }
 }
 std::printf("]}\n");return 0;
}
