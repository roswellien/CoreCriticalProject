// Compile-only native message-provider candidate. Runtime admission is separate.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include "source_table.hpp"
namespace {
struct Pair { std::uint32_t name; std::uint32_t id; };
static_assert(sizeof(Pair)==8);
Pair table[1577];
void* host_exit_table=nullptr; // Wide owning native CRT pointer; never truncated.
std::uint64_t dll_notifications=0;
const unsigned char* name_bytes(std::uint32_t pointer) {
  // Entire fixed current source data image is generated/pinned; all1577
  // authenticated pointers are in this source extent. This is guest metadata,
  // not reinterpret_cast of a guest integer as a native host pointer.
  return source_data+(pointer-0x10003000u);
}
int compare(const unsigned char* a,const unsigned char* b) {
  // Literal unsigned byte compare and NUL termination at1000102D..10001056.
  for(;;++a,++b) { if(*a<*b)return -1;if(*a>*b)return 1;if(*a==0)return 0; }
}
void sort_pairs() {
  // Independent no-allocation endpoint implementation, not an assertion of
  // instruction/stack/flags equivalence to original quicksort/insertion CFG.
  for(std::size_t i=1;i<1577;++i) {
    Pair value=table[i];std::size_t j=i;
    while(j!=0 && compare(name_bytes(value.name),name_bytes(table[j-1].name))<0) {
      table[j]=table[j-1];--j;
    }
    table[j]=value;
  }
}
}
extern "C" __declspec(dllexport) std::uint32_t __cdecl ZLocGetID(const char* name) {
  // Source export is not called by normal47F760. Future invocation admission
  // requires its own complete caller/input/ABI and owned string proof.
  std::size_t first=0,last=1577;
  while(first<last) {
    auto mid=first+(last-first)/2;
    int order=compare(reinterpret_cast<const unsigned char*>(name),name_bytes(table[mid].name));
    if(order==0)return table[mid].id;
    if(order<0)last=mid;else first=mid+1;
  }
  return 0;
}
extern "C" __declspec(dllexport) const void* __cdecl MW34MessageTable(std::size_t* count) {
  *count=1577;return table;
}
extern "C" __declspec(dllexport) std::uintptr_t __cdecl MW34HostExitTable() {
  return reinterpret_cast<std::uintptr_t>(host_exit_table);
}
BOOL WINAPI DllMain(HINSTANCE,DWORD reason,LPVOID) {
  if(reason==DLL_PROCESS_ATTACH) {
    host_exit_table=std::malloc(128);if(!host_exit_table)return FALSE;
    *static_cast<std::uint32_t*>(host_exit_table)=0;
    for(std::size_t i=0;i<1577;++i)table[i]={source_pairs[i][0],source_pairs[i][1]};
  }
  // The source userDllMain sorts on every notification, not attach alone.
  sort_pairs();++dll_notifications;
  if(reason==DLL_PROCESS_DETACH) { std::free(host_exit_table);host_exit_table=nullptr; }
  return TRUE;
}
