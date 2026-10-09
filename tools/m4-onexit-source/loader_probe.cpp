#include <windows.h>
#include <cstdio>
#include <cstdint>
int main(){
 auto h=LoadLibraryExW(L"D:/Projects/MW34Recomp/local/mw3-staged/Shared_DLLs/MSVCRT.DLL",nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
 if(!h){std::printf("load failed %lu\n",GetLastError());return 1;}
 wchar_t path[2048]{};GetModuleFileNameW(h,path,2048);
 const auto b=reinterpret_cast<std::uintptr_t>(h);auto onexit=GetProcAddress(h,"_onexit");auto size=GetProcAddress(h,"_msize");
 std::printf("base=%08lx onexit=%08lx msize=%08lx\n",static_cast<unsigned long>(b),static_cast<unsigned long>(reinterpret_cast<std::uintptr_t>(onexit)),static_cast<unsigned long>(reinterpret_cast<std::uintptr_t>(size)));
 if(b==0x78000000){std::printf("begin=%08lx next=%08lx heapmode=%08lx\n",*reinterpret_cast<unsigned long*>(b+0x3788c),*reinterpret_cast<unsigned long*>(b+0x37888),*reinterpret_cast<unsigned long*>(b+0x377d0));}
 // The probe does not register callbacks or call source producer/game bodies.
 return 0;
}
