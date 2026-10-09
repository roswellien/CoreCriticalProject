// Additive persistent transport around the existing reviewed Remill State and
// checked-memory adaptor. Only the frozen mw34_lifted_entry executes the leaf.
#include "protocol.hpp"
#include "admission.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <algorithm>
#include <filesystem>
#include <iostream>
#include <string>

namespace lh = mw34::live_helper;
static_assert(sizeof(void*) == 8 && sizeof(State) == 3504);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Winvalid-offsetof"
static_assert(__builtin_offsetof(State, aflag) == 2064);
static_assert(__builtin_offsetof(State, gpr) == 2208);
#pragma clang diagnostic pop
static_assert(__builtin_offsetof(GPR, rax) == 8);
static_assert(__builtin_offsetof(GPR, rsp) == 104);
static_assert(__builtin_offsetof(GPR, rip) == 264);
extern "C" void* mw34_lifted_entry(State*, std::uint32_t, void*);
namespace {
constexpr char leaf_sha[] = "560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65";
constexpr char build_sha[] = "3a51677200b38b30ec3500323ba4f937fdcfdcfc33f6c07ca7101add7359098e";
constexpr char adaptor_sha[] = "6293c46c155103fb8ef6a288be39960dffe6defc2220a0ece22b5e5049e4c178";
constexpr DWORD transfer_timeout = 60000;
void require(bool condition, const char* why) {if (!condition) throw std::invalid_argument(why);}
struct Handle {
  HANDLE value;
  explicit Handle(HANDLE handle):value(handle){}
  ~Handle(){if (value && value != INVALID_HANDLE_VALUE) CloseHandle(value);}
  Handle(const Handle&) = delete; Handle& operator=(const Handle&) = delete;
};
bool transfer(HANDLE pipe, void* bytes, DWORD count, bool writing) {
  auto* cursor = static_cast<unsigned char*>(bytes); const auto* first = cursor;
  while (count) {
    Handle event(CreateEventW(nullptr, TRUE, FALSE, nullptr));
    if (!event.value) throw std::runtime_error("Helper pipe event creation failed");
    OVERLAPPED operation{}; operation.hEvent = event.value; DWORD done{};
    const BOOL immediate = writing ? WriteFile(pipe, cursor, count, &done, &operation)
                                   : ReadFile(pipe, cursor, count, &done, &operation);
    if (!immediate) {
      const auto code = GetLastError();
      if (code == ERROR_BROKEN_PIPE || code == ERROR_PIPE_NOT_CONNECTED || code == ERROR_NO_DATA) return false;
      if (code != ERROR_IO_PENDING) throw std::runtime_error("Helper pipe transfer start failed");
      const DWORD timeout = !writing && cursor == first ? INFINITE : transfer_timeout;
      if (WaitForSingleObject(event.value, timeout) != WAIT_OBJECT_0) {
        CancelIoEx(pipe, &operation);
        if (WaitForSingleObject(event.value, 5000) != WAIT_OBJECT_0) ExitProcess(3);
        throw std::runtime_error("Helper partial request/response timed out");
      }
      if (!GetOverlappedResult(pipe, &operation, &done, FALSE)) {
        const auto code_done = GetLastError();
        if (code_done == ERROR_BROKEN_PIPE || code_done == ERROR_PIPE_NOT_CONNECTED || code_done == ERROR_NO_DATA) return false;
        throw std::runtime_error("Helper pipe transfer completion failed");
      }
    }
    if (!done || done > count) return false;
    cursor += done; count -= done;
  }
  return true;
}
HANDLE connect(const std::filesystem::path& path) {
  const auto name = path.wstring();
  require(name.rfind(L"\\\\.\\pipe\\mw34-helper-", 0) == 0, "Dedicated local helper pipe path required");
  const auto until = GetTickCount64() + 30000;
  while (GetTickCount64() < until) {
    auto pipe = CreateFileW(name.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr, OPEN_EXISTING,
                            FILE_FLAG_OVERLAPPED, nullptr);
    if (pipe != INVALID_HANDLE_VALUE) return pipe;
    const auto code = GetLastError();
    if (code != ERROR_FILE_NOT_FOUND && code != ERROR_PIPE_BUSY) throw std::runtime_error("Helper pipe client connection failed");
    WaitNamedPipeW(name.c_str(), 250); Sleep(10);
  }
  throw std::runtime_error("Helper pipe client connection timed out");
}
void error(lh::Response& response, unsigned status, const char* why) {
  response.status = status; response.complete = 0;
  const auto length = std::min(std::strlen(why), sizeof(response.error) - 1);
  std::memcpy(response.error, why, length); response.error[length] = 0;
}
struct Bridge {
  mw34::GuestMemory memory;
  State* state{};
  std::array<lh::Event,2> events{};
  unsigned reads{}, returns{};
  const char* fault{};
  void fail(const char* why){if (!fault) fault = why;}
};
thread_local Bridge* active{};
struct Borrow {
  explicit Borrow(Bridge& bridge){require(!active, "Helper bridge already borrowed"); active = &bridge;}
  ~Borrow(){active = nullptr;}
};
void import_cpu(State& state, const lh::Cpu& cpu) {
  // This reproduces tools/lifting/lifted_worker.cpp's observed32-bit adaptor.
  // Whole3504 hidden State starts as an explicit authored zero seed. FP/ENV
  // remain separate opaque bytes, because the admitted source is integer-only.
  std::memset(&state, 0, sizeof(state));
  state.gpr.rax.dword = cpu.eax; state.gpr.rcx.dword = cpu.ecx;
  state.gpr.rdx.dword = cpu.edx; state.gpr.rbx.dword = cpu.ebx;
  state.gpr.rsp.dword = lh::virtual_frame; state.gpr.rbp.dword = cpu.ebp;
  state.gpr.rsi.dword = cpu.esi; state.gpr.rdi.dword = cpu.edi; state.gpr.rip.dword = lh::root;
  state.rflag.flat = cpu.flags;
  state.aflag.cf = (cpu.flags >> 0) & 1; state.aflag.pf = (cpu.flags >> 2) & 1;
  state.aflag.af = (cpu.flags >> 4) & 1; state.aflag.zf = (cpu.flags >> 6) & 1;
  state.aflag.sf = (cpu.flags >> 7) & 1; state.aflag.df = (cpu.flags >> 10) & 1;
  state.aflag.of = (cpu.flags >> 11) & 1;
}
lh::Cpu export_cpu(const State& state, const lh::Request& request) {
  const unsigned arithmetic = (state.aflag.cf << 0) | (state.aflag.pf << 2) | (state.aflag.af << 4) |
                              (state.aflag.zf << 6) | (state.aflag.sf << 7) | (state.aflag.of << 11);
  // The generated six SUB arithmetic flags replace only0x8d5. Every other
  // literal incoming flag, including DF, survives this integer-only source.
  return {state.gpr.rax.dword, state.gpr.rcx.dword, state.gpr.rdx.dword, state.gpr.rbx.dword,
          request.cpu.esp + 8, state.gpr.rbp.dword, state.gpr.rsi.dword, state.gpr.rdi.dword,
          (request.cpu.flags & ~lh::arithmetic_mask) | arithmetic, request.caller};
}
class Worker {
  unsigned server_pid_{}, sequence_ = 1;
  bool handshake_{};
public:
  Worker(const char* game, const char* object) {
    const auto image = mw34::m4::read_image(game); mw34::m4::admit_image(image);
    require(image.size() >= 37584 + 22 && mw34::m4::sha256(std::span{image}.subspan(37584,22)) == leaf_sha,
            "Exact admitted integer helper source differs");
    const auto native = mw34::m4::read_image(object);
    require(native.size() >= 2 && native[0] == std::byte{0x64} && native[1] == std::byte{0x86}, "Linked helper object must be AMD64 COFF");
    require(mw34::m4::sha256(native) == MW34_HELPER_OBJECT_SHA && std::filesystem::equivalent(object,MW34_HELPER_OBJECT_PATH),
            "Supplied helper object differs from the exact frozen object linked into this worker");
    require(mw34::m4::sha256(mw34::m4::read_image(MW34_HELPER_BUILD_PATH)) == build_sha, "Frozen helper build association changed");
    require(mw34::m4::sha256(mw34::m4::read_image(MW34_HELPER_ADAPTOR_PATH)) == adaptor_sha, "Reviewed lifting adaptor source changed");
  }
  void server(unsigned pid){server_pid_ = pid;}
  lh::Response dispatch(const lh::Request& request) {
    auto result = lh::response(request.sequence); result.worker_pid = GetCurrentProcessId();
    result.cpu = request.cpu; result.fx = request.fx; result.env = request.env;
    try {
      require(std::memcmp(request.magic,lh::request_magic,8) == 0 && request.version == lh::version && request.bytes == sizeof(request), "Helper request framing/version/size mismatch");
      require(request.sequence == sequence_ && sequence_ != 0xffffffffU, "Nonsequential or replayed helper request rejected");
      require(request.pid == server_pid_ && request.tid, "Helper request process/thread does not identify the pipe server");
      require(request.kind <= 2 && (handshake_ ? request.kind != 0 : request.kind == 0), "One initial kind0 handshake required; unsupported request kind");
      ++sequence_;
      if (!request.kind){handshake_ = true; return result;}
      require(request.cpu.eip == lh::root && request.cpu.esp >= 4 && request.cpu.esp <= 0xfffffff7U && request.caller,
              "Captured helper entry ESP/EIP/caller invalid");
      require(request.kind != 2 || request.caller == lh::caller, "Live helper caller must be the pinned405173 direct CALL");
      result.memory = lh::initial_memory(request);
      Bridge bridge; State state; import_cpu(state,request.cpu); bridge.state = &state;
      bridge.memory.map({lh::memory_base},lh::memory_size,mw34::Permissions::read | mw34::Permissions::write);
      bridge.memory.write({lh::memory_base},std::as_bytes(std::span{result.memory}));
      bridge.memory.protect({lh::memory_base},mw34::Permissions::read);
      void* token{};
      {Borrow borrow(bridge); token = mw34_lifted_entry(&state,lh::root,&bridge.memory);}
      result.events = bridge.events; result.reads = bridge.reads; result.returns = bridge.returns;
      if (bridge.fault || token != &bridge.memory || bridge.reads != 2 || bridge.returns != 1 ||
          state.gpr.rsp.dword != lh::virtual_frame + 8 || state.gpr.rip.dword != lh::broker) {
        error(result,3,bridge.fault ? bridge.fault : "Generated helper token/read/RET4 closure rejected"); return result;
      }
      std::array<std::uint8_t,lh::memory_size> after{};
      bridge.memory.read({lh::memory_base},std::as_writable_bytes(std::span{after}));
      require(after == result.memory, "Generated integer helper changed its whole readonly4096 owned page");
      require(state.gpr.rcx.dword == request.cpu.ecx && state.gpr.rbx.dword == request.cpu.ebx &&
              state.gpr.rbp.dword == request.cpu.ebp && state.gpr.rsi.dword == request.cpu.esi && state.gpr.rdi.dword == request.cpu.edi,
              "Generated helper preserved-register closure differs");
      require(state.aflag.df == ((request.cpu.flags >> 10) & 1), "Generated helper changed literal DF");
      result.cpu = export_cpu(state,request); result.complete = 1;
      return result;
    } catch (const std::invalid_argument& exception){error(result,result.reads ? 3U : 2U,exception.what());}
      catch (const std::exception& exception){error(result,3,exception.what());}
    return result;
  }
};
}
extern "C" std::uint32_t __remill_read_memory_32(void* memory, std::uint32_t address) {
  auto* bridge = active;
  if (!bridge) return 0;
  const auto index = bridge->reads++;
  if (memory != &bridge->memory || index >= 2 || address != (index ? lh::virtual_frame : lh::virtual_frame + 4)) {
    bridge->fail("Unexpected exact helper checked read/token/count"); return 0;
  }
  try {
    const auto value = bridge->memory.load<std::uint32_t>({address});
    bridge->events[index] = {address,value,4,0}; return value;
  } catch (const std::exception&){bridge->fail("Generated helper checked read fault"); return 0;}
}
extern "C" void* __remill_write_memory_32(void* memory, std::uint32_t, std::uint32_t) {
  if (active) active->fail("Integer helper attempted an unadmitted guest write"); return memory;
}
extern "C" void* __remill_function_return(State* state, std::uint32_t address, void* memory) {
  if (auto* bridge = active) {
    ++bridge->returns;
    if (state != bridge->state || memory != &bridge->memory || address != lh::broker ||
        state->gpr.rip.dword != lh::broker || state->gpr.rsp.dword != lh::virtual_frame + 8 || bridge->returns != 1)
      bridge->fail("Generated helper actual RET4 state/token/count rejected");
  }
  return memory;
}
int main(int argc, char** argv) {
  try {
    require(argc == 4, "Usage: worker <admitted game> <linked frozen helper object> <local pipe>");
    Worker worker(argv[1],argv[2]); Handle pipe(connect(argv[3])); ULONG server_pid{};
    require(GetNamedPipeServerProcessId(pipe.value,&server_pid) && server_pid, "Helper pipe server identity unavailable"); worker.server(server_pid);
    std::cout << "{\"connected\":true,\"worker_pid\":" << GetCurrentProcessId() << ",\"server_pid\":" << server_pid
      << ",\"object_sha256\":\"" << MW34_HELPER_OBJECT_SHA << "\",\"leaf_sha256\":\"" << leaf_sha
      << "\",\"adaptor_ancestor_sha256\":\"" << adaptor_sha << "\",\"build_sha256\":\"" << build_sha
      << "\",\"state_hidden_seed\":\"authored zero; captured32-bit CPU and full flags imported; ESP/EIP projected\",\"fp_env\":\"opaque unchanged transport, source integer-only\"}\n" << std::flush;
    lh::Request request{};
    while (transfer(pipe.value,&request,sizeof(request),false)) {
      auto result = worker.dispatch(request); if (!transfer(pipe.value,&result,sizeof(result),true)) break;
    }
    return 0;
  } catch (const std::exception& exception){std::cerr << exception.what() << '\n'; return 1;}
}
