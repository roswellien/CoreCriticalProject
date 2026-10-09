// Additive x64 transport for the frozen, bounded numeric initializer.
// Captured CPU/FP input is never reseeded to make an unsupported invocation pass.
#include "protocol.hpp"
#include "session.hpp"
#include <chrono>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>

namespace ln = mw34::live_numeric;
namespace ni = mw34::m4_nmx_integration;
namespace rt = mw34::m4_runtime;
using mw34::GuestAddress;
static_assert(sizeof(State) == 3504);
namespace {
constexpr char ancestor_sha[] = "22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1";
constexpr char session_sha[] = "c864029d2758aadef19e2604a775775372cd4c7077cc358cc914cdf529db45ea";
constexpr char gate_sha[] = "fe713df4600d61acb3ac1eb6ea80963c1dc225d5e73fa3032795dc1905ca7706";
constexpr DWORD transfer_timeout = 60000;
void require(bool condition, const char* reason) { if (!condition) throw std::invalid_argument(reason); }
template<class T, class A> T get(const A& bytes, unsigned offset) {
  T result{}; std::memcpy(&result, bytes.data() + offset, sizeof(result)); return result;
}
template<class T, class A> void put(A& bytes, unsigned offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}
void error(ln::Response& result, unsigned status, const char* message) {
  result.status = status; result.complete = 0;
  const auto length = std::min(std::strlen(message), sizeof(result.error) - 1);
  std::memcpy(result.error, message, length); result.error[length] = 0;
}
struct Handle {
  HANDLE value = INVALID_HANDLE_VALUE;
  explicit Handle(HANDLE handle = INVALID_HANDLE_VALUE):value(handle){}
  ~Handle(){ if (value != INVALID_HANDLE_VALUE && value) CloseHandle(value); }
  Handle(const Handle&) = delete; Handle& operator=(const Handle&) = delete;
};
bool transfer(HANDLE pipe, void* bytes, DWORD count, bool write) {
  auto* cursor = static_cast<unsigned char*>(bytes);
  const auto* first = cursor;
  while (count) {
    Handle event(CreateEventW(nullptr, TRUE, FALSE, nullptr));
    if (!event.value) throw std::runtime_error("Pipe transfer event failed");
    OVERLAPPED operation{}; operation.hEvent = event.value; DWORD done{};
    const BOOL immediate = write ? WriteFile(pipe, cursor, count, &done, &operation)
                                 : ReadFile(pipe, cursor, count, &done, &operation);
    if (!immediate) {
      const auto code = GetLastError();
      if (code == ERROR_BROKEN_PIPE || code == ERROR_PIPE_NOT_CONNECTED || code == ERROR_NO_DATA) return false;
      if (code != ERROR_IO_PENDING) throw std::runtime_error("Pipe transfer failed");
      // A game can remain running long after its one initializer callback.
      // Idle waiting for the first request byte lasts until server EOF; only
      // partially received requests and responses have a transfer deadline.
      const DWORD deadline = !write && cursor == first ? INFINITE : transfer_timeout;
      if (WaitForSingleObject(event.value, deadline) != WAIT_OBJECT_0) {
        CancelIoEx(pipe, &operation);
        // A still pending OVERLAPPED cannot outlive its stack storage. If a
        // defective peer/device prevents cancellation completion, end this
        // isolated worker rather than leaving an unbounded cleanup wait.
        if (WaitForSingleObject(event.value, 5000) != WAIT_OBJECT_0) ExitProcess(3);
        throw std::runtime_error("Pipe transfer timed out");
      }
      if (!GetOverlappedResult(pipe, &operation, &done, FALSE)) {
        const auto completion = GetLastError();
        if (completion == ERROR_BROKEN_PIPE || completion == ERROR_PIPE_NOT_CONNECTED || completion == ERROR_NO_DATA) return false;
        throw std::runtime_error("Pipe transfer completion failed");
      }
    }
    if (!done || done > count) return false;
    cursor += done; count -= done;
  }
  return true;
}
HANDLE connect(const std::filesystem::path& name) {
  const auto text = name.wstring();
  require(text.rfind(L"\\\\.\\pipe\\mw34-numeric-", 0) == 0, "Dedicated local numeric pipe path required");
  const auto deadline = GetTickCount64() + 30000;
  while (GetTickCount64() < deadline) {
    HANDLE pipe = CreateFileW(text.c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                              OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
    if (pipe != INVALID_HANDLE_VALUE) return pipe;
    const auto code = GetLastError();
    if (code != ERROR_FILE_NOT_FOUND && code != ERROR_PIPE_BUSY) throw std::runtime_error("Numeric pipe client connection failed");
    WaitNamedPipeW(text.c_str(), 250); Sleep(10);
  }
  throw std::runtime_error("Numeric pipe client connection timed out");
}

// Legacy ENV metadata is independent from FX metadata: measured FXSAVE elision
// on the original process can zero its pointer/selector bytes. Numerical fields
// must agree exactly; no such exception exists for CW, SW or the physical tags.
void input_consistency(const ln::Request& request) {
  const auto cw = get<std::uint16_t>(request.fx, 0);
  const auto sw = get<std::uint16_t>(request.fx, 2);
  require(cw == get<std::uint16_t>(request.env, 0), "ENV/FX control word mismatch");
  require(sw == get<std::uint16_t>(request.env, 4), "ENV/FX status word mismatch");
  unsigned tag = 0xffff;
  const unsigned top = (sw >> 11) & 7, ftw = request.fx[4];
  for (unsigned logical = 0; logical < 8; ++logical) {
    const auto physical = (top + logical) & 7;
    if (ftw & (1U << physical)) {
      const auto classified = ni::full_tag(request.fx.data() + 32 + logical * 16);
      tag = (tag & ~(3U << (physical * 2))) | (classified << (physical * 2));
    }
  }
  require(tag == get<std::uint16_t>(request.env, 8), "ENV/FX physical full-tag/raw80 mismatch");
  // The reviewed original capture reports elided FX metadata. Preserving that
  // zero transport image after a native x87 operation is sound only within
  // this measured bound; a nonelided incoming image needs a separate recipe.
  require(std::all_of(request.fx.begin() + 6, request.fx.begin() + 24,
                      [](auto byte){return byte == 0;}), "Nonelided FX metadata outside the measured live transport domain");
  require((get<unsigned>(request.env, 16) >> 16) <= 0x7ff, "Legacy ENV opcode metadata malformed");
  require(request.cpu.eip == ln::root && request.cpu.esp >= 16 && request.cpu.esp <= 0xfffffffbU && request.caller != 0,
          "Captured root/actual entry ESP/caller invalid");
  require(request.cs == 0x23 && request.ds == 0x2b && request.ss == 0x2b && request.fs_base,
          "Captured live segments/FS base outside the admitted domain");
  require(request.provider_base == ln::provider_base && request.provider_bits == 0x7f7fffff && request.iat_target == ln::leaf,
          "Actual preferred MSVCP50 base/operand/resolved IAT differs");
}
void import(State& state, const ln::Request& request, unsigned virtual_fs) {
  // All 3504 bytes start as an explicit authored hidden zero seed. The hook
  // cannot observe extended vector banks, segment caches or opaque State fields.
  // Observable 32-bit CPU, all eleven FP flags, raw80 and XMM input come solely
  // from BEFORE. ESP/EIP/caller and FS base are declared address projections.
  std::memset(&state, 0, sizeof(state));
  rt::Cpu32 cpu{}; std::memcpy(&cpu, &request.cpu, sizeof(cpu));
  cpu.esp = ln::virtual_frame; cpu.eip = ln::root; ni::project(state, cpu);
  state.seg.cs.flat = static_cast<std::uint16_t>(request.cs);
  state.seg.ds.flat = static_cast<std::uint16_t>(request.ds);
  state.seg.ss.flat = static_cast<std::uint16_t>(request.ss);
  state.addr.fs_base.dword = virtual_fs;
  state.x87.fxsave.cwd.flat = get<std::uint16_t>(request.fx, 0);
  const auto sw = get<std::uint16_t>(request.fx, 2);
  state.x87.fxsave.swd.flat = sw;
  state.x87.fxsave.ftw.flat = request.fx[4];
  state.x87.fxsave.mxcsr.flat = get<unsigned>(request.fx, 24);
  state.x87.fxsave.mxcsr_mask.flat = get<unsigned>(request.fx, 28);
  state.x87.fxsave.ip = get<unsigned>(request.env, 12);
  state.x87.fxsave.cs.flat = get<std::uint16_t>(request.env, 16);
  state.x87.fxsave.fop = get<std::uint16_t>(request.env, 18);
  state.x87.fxsave.dp = get<unsigned>(request.env, 20);
  state.x87.fxsave.ds.flat = get<std::uint16_t>(request.env, 24);
  state.sw.ie = (sw >> 0) & 1; state.sw.de = (sw >> 1) & 1;
  state.sw.ze = (sw >> 2) & 1; state.sw.oe = (sw >> 3) & 1;
  state.sw.ue = (sw >> 4) & 1; state.sw.pe = (sw >> 5) & 1;
  state.sw.sf = (sw >> 6) & 1; state.sw.c0 = (sw >> 8) & 1;
  state.sw.c1 = (sw >> 9) & 1; state.sw.c2 = (sw >> 10) & 1;
  state.sw.c3 = (sw >> 14) & 1;
  for (unsigned logical = 0; logical < 8; ++logical) {
    const auto* raw = request.fx.data() + 32 + logical * 16;
    std::memcpy(&state.st.elems[logical].val, raw, 10);
    std::memcpy(reinterpret_cast<std::byte*>(&state.x87) + 32 + logical * 16, raw, 10);
    std::memcpy(&state.vec[logical], request.fx.data() + 160 + logical * 16, 16);
    // Remill stores MMX separately. MMX aliases physical x87 storage; FXSAVE's
    // eight raw80 slots are logical ST order, so rotate by captured TOP.
    const auto physical = (((sw >> 11) & 7) + logical) & 7;
    std::memcpy(&state.mmx.elems[physical].val, raw, 8);
  }
}
rt::Policy policy() {
  rt::Policy result; result.stack_low = {0x20001000}; result.stack_bytes = 4096; result.heap_bytes = 8192; return result;
}
class Worker {
  std::vector<std::byte> game_, provider_;
  ni::Proof proof_;
  unsigned server_pid_{}, next_sequence_ = 1;
  bool handshake_{};
public:
  Worker(const char* game, const char* provider, const char* object):
    game_(mw34::m4::read_image(game)), provider_(mw34::m4::read_image(provider)),
    proof_{mw34::m4::sha256(mw34::m4::read_image(object)), gate_sha} {
    mw34::m4::admit_image(game_);
    require(provider_.size() == 565760 && mw34::m4::sha256(provider_) == ni::provider_sha, "Exact frozen MSVCP50 input required");
    require(proof_.native_sha == MW34_NMX_OBJECT_SHA, "Supplied object differs from the frozen object linked into this worker");
    require(std::filesystem::equivalent(object, MW34_NMX_OBJECT_PATH), "Supplied native object must name the exact linked frozen path");
    require(mw34::m4::sha256(mw34::m4::read_image(MW34_NMX_SESSION_PATH)) == session_sha, "Frozen Session source changed after worker build");
    require(mw34::m4::sha256(mw34::m4::read_image(MW34_NMX_ANCESTOR_PATH)) == ancestor_sha, "Canonical Session ancestor changed after worker build");
    require(mw34::m4::sha256(mw34::m4::read_image(MW34_NMX_GATE_PATH)) == gate_sha, "Accepted numeric component gate changed after worker build");
  }
  void server(unsigned pid){server_pid_ = pid;}
  ln::Response dispatch(const ln::Request& request) {
    auto result = ln::response(request.sequence); result.worker_pid = GetCurrentProcessId();
    // Rejected responses echo observable input and grant no completion/event credit.
    result.cpu = request.cpu; result.fx = request.fx; result.env = request.env; result.globals = request.globals;
    try {
      require(std::memcmp(request.magic, ln::request_magic, 8) == 0 && request.version == ln::version && request.bytes == sizeof(request),
              "Request framing/version/size mismatch");
      require(request.sequence == next_sequence_, "Nonsequential or replayed request rejected");
      require(next_sequence_ != 0xffffffffU, "Numeric sequence exhausted");
      require(request.pid == server_pid_ && request.tid, "Request process/thread does not identify the pipe server");
      require(request.kind <= 2, "Unknown numeric request kind");
      require(handshake_ ? request.kind != 0 : request.kind == 0, "Exactly one initial kind-0 handshake required");
      ++next_sequence_;
      if (!request.kind) { handshake_ = true; return result; }
      input_consistency(request);
      auto runtime = rt::Runtime::from_admitted_image(game_, policy());
      auto& state = *std::construct_at(reinterpret_cast<State*>(runtime.remill_state().data()));
      import(state, request, runtime.fs_base().value);
      const auto initial = ni::view(state);
      std::memcpy(runtime.fx().data(), initial.fx.data(), 512);
      runtime.mark_remill_seeded();
      runtime.cpu() = initial.cpu; runtime.cpu().esp = ln::virtual_frame + 4; runtime.cpu().eip = ln::broker;
      runtime.memory().store<unsigned>({ln::virtual_frame}, ln::broker);
      runtime.memory().write({ln::output}, std::as_bytes(std::span{request.globals}));
      // The live IAT is admitted above, while the virtual source image's IAT
      // remains its exact raw-file owner. Session's typed route resolves slot.
      ni::Session session(runtime, provider_, proof_); runtime.freeze_registry();
      const bool invoked = session.invoke({ln::root}, {ln::broker});
      result.steps = session.step(); result.complete = session.complete();
      for (unsigned i = 0; i < session.step() && i < result.events.size(); ++i) {
        const auto& event = session.events()[i]; result.events[i] = {event.pc,event.address,event.value,event.width,event.write};
      }
      const auto& calls = runtime.calls();
      for (unsigned i = 0; i < calls.size() && i < 3; ++i) {
        const auto& call = calls[i]; const auto offset = 5 * i;
        result.routes[offset] = call.site.value; result.routes[offset + 1] = call.target.value;
        result.routes[offset + 2] = call.return_pc.value; result.routes[offset + 3] = call.import;
        result.routes[offset + 4] = call.completed;
      }
      if (!invoked) {
        const auto fault = session.fault();
        error(result, result.steps == 0 ? 2U : 3U, fault.reason ? fault.reason : "Frozen Session invocation failed");
        return result;
      }
      require(session.complete() && session.step() == 22 && calls.size() == 3 &&
              std::all_of(calls.begin(), calls.end(), [](const auto& call){return call.completed;}), "Compiled closure incomplete");
      const auto output = ni::view(state);
      require(output.cpu.esp == ln::virtual_frame + 4 && output.cpu.eip == ln::broker, "Virtual root RET projection invalid");
      rt::Cpu32 expected{}; std::memcpy(&expected, &request.cpu, sizeof(expected));
      expected.esp = ln::virtual_frame + 4; expected.eip = ln::broker;
      require(output.cpu == expected, "Compiled CPU/nonvolatile/full flags preservation differs from captured BEFORE");
      std::memcpy(&result.cpu, &output.cpu, sizeof(result.cpu));
      result.cpu.esp = request.cpu.esp + 4; result.cpu.eip = request.caller;
      // Preserve every original FX reserved/padding byte and measured metadata
      // elision. Overlay only defined numerical fields, never the entire512.
      std::memcpy(result.fx.data(), output.fx.data(), 4); result.fx[4] = static_cast<std::uint8_t>(output.fx[4]);
      std::memcpy(result.fx.data() + 24, output.fx.data() + 24, 4);
      for (unsigned i = 0; i < 8; ++i) {
        std::memcpy(result.fx.data() + 32 + i * 16, output.fx.data() + 32 + i * 16, 10);
        std::memcpy(result.fx.data() + 160 + i * 16, output.fx.data() + 160 + i * 16, 16);
      }
      // Carry legacy ENV reserved words. Its defined metadata is native output.
      for (const unsigned offset : {0U,4U,8U,24U}) std::memcpy(result.env.data() + offset, output.env.data() + offset, 2);
      std::memcpy(result.env.data() + 12, output.env.data() + 12, 12);
      runtime.memory().read({ln::output}, std::as_writable_bytes(std::span{result.globals}));
      return result;
    } catch (const std::invalid_argument& exception) { error(result, result.steps ? 3U : 2U, exception.what()); }
      catch (const std::exception& exception) { error(result, 3, exception.what()); }
    return result;
  }
};
}
int main(int argc, char** argv) {
  try {
    require(argc == 5, "Usage: worker <admitted game> <exact provider> <linked frozen native object> <local pipe>");
    Worker worker(argv[1], argv[2], argv[3]); Handle pipe(connect(argv[4]));
    ULONG server_pid{};
    require(GetNamedPipeServerProcessId(pipe.value, &server_pid) && server_pid, "Pipe server process identity unavailable");
    worker.server(server_pid);
    std::cout << "{\"connected\":true,\"worker_pid\":" << GetCurrentProcessId()
      << ",\"server_pid\":" << server_pid << ",\"object_sha256\":\"" << MW34_NMX_OBJECT_SHA
      << "\",\"session_sha256\":\"" << session_sha << "\",\"gate_sha256\":\"" << gate_sha
      << "\",\"session_ancestor_sha256\":\"" << ancestor_sha
      << "\",\"gate_scope\":\"accepted canonical ancestor only; MXCSR1fa0 private extension separately prepared"
      << "\",\"state_hidden_seed\":\"authored zero; observed CPU/FP imported; ESP/EIP/FS projected\"}\n" << std::flush;
    ln::Request request{};
    while (transfer(pipe.value, &request, sizeof(request), false)) {
      auto response = worker.dispatch(request);
      if (!transfer(pipe.value, &response, sizeof(response), true)) break;
    }
    return 0;
  } catch (const std::exception& exception) { std::cerr << exception.what() << '\n'; return 1; }
}
