#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstddef>
#include <cstdint>
struct SourceLoadLibrary32Frame { std::uint32_t return_pc,name; };
struct SourceGetProcAddress32Frame { std::uint32_t return_pc,module,name; };
struct NativeOwner { HMODULE module;FARPROC export_address;std::uint64_t generation; };
static_assert(sizeof(HMODULE)==8 && sizeof(FARPROC)==8 && sizeof(std::uintptr_t)==8);
static_assert(sizeof(SourceLoadLibrary32Frame)==8 && offsetof(SourceLoadLibrary32Frame,name)==4);
static_assert(sizeof(SourceGetProcAddress32Frame)==12 && offsetof(SourceGetProcAddress32Frame,module)==4 && offsetof(SourceGetProcAddress32Frame,name)==8);
static_assert(sizeof(NativeOwner)==24 && offsetof(NativeOwner,export_address)==8 && offsetof(NativeOwner,generation)==16);
extern "C" const unsigned mw34_message_abi_witness[]={
  8,8,8,8,4,12,4,8,24,8,16,
  0x575f3a,0x575f40,0x575f54,0x575f5a,
  0x5e5db0,0x5f09d4,0x72e67c,0x72c670,0x72e680,0x1720
};
