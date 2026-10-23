// Compile-only actual native API design. Runtime/state/hardware admission pending.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstring>
struct SourceFrame {
  std::uint32_t pc,return_pc,source_name,source_module;
  std::uint64_t occurrence,thread_token,source_context_token;
};
struct ModuleOwner {
  HMODULE module;FARPROC export_address;std::uint64_t generation;
  DWORD load_incoming_error,load_outgoing_error,export_incoming_error,export_outgoing_error;
  wchar_t actual_module_path[32768];DWORD actual_path_length;
};
static_assert(sizeof(HMODULE)==8 && sizeof(FARPROC)==8);
// The caller must authenticate exact prepared source frame bytes, literal
// argument bytes, active source Context and true owner thread before this API.
// This layer does not substitute a hardware CALL/RET/CPU/FX witness.
extern "C" bool MW34LoadMessageNative(ModuleOwner* owner,const SourceFrame* frame,const char* bare_name) {
  if(owner->module || !frame->source_context_token || !frame->thread_token || !frame->occurrence ||
     frame->pc!=0x575f3a || frame->return_pc!=0x575f40 || frame->source_name!=0x5e5db0 ||
     std::strcmp(bare_name,"mech3Msg.dll")!=0)return false;
  owner->load_incoming_error=GetLastError();SetLastError(owner->load_incoming_error);
  owner->module=LoadLibraryA(bare_name);owner->load_outgoing_error=GetLastError();
  if(owner->module) {
    ++owner->generation;
    owner->actual_path_length=GetModuleFileNameW(owner->module,owner->actual_module_path,32768);
    // Actual module/path/file digest/PE32+ provider identity must be checked
    // against independent approved provenance before source success credit.
  }
  SetLastError(owner->load_outgoing_error);return owner->module!=nullptr;
}
extern "C" bool MW34ResolveMessageNative(ModuleOwner* owner,const SourceFrame* frame,const char* name) {
  if(!owner->module || !frame->source_context_token || !frame->thread_token || !frame->occurrence ||
     frame->pc!=0x575f54 || frame->return_pc!=0x575f5a || frame->source_name!=0x5f09d4 ||
     std::strcmp(name,"ZLocGetID")!=0)return false;
  owner->export_incoming_error=GetLastError();SetLastError(owner->export_incoming_error);
  owner->export_address=GetProcAddress(owner->module,name);owner->export_outgoing_error=GetLastError();
  SetLastError(owner->export_outgoing_error);
  // Physical source succeeds on module!=0 even when GetProcAddress returns0.
  return true;
}
// Source and harness lifetimes are deliberately distinct. No automatic
// destructor calls FreeLibrary or substitutes DLL_PROCESS_DETACH here.
