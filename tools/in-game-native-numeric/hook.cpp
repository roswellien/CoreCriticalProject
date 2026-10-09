// Additive live numeric bridge. No admitted game/provider instructions are copied
// into public source or overwritten; only one CRT initializer table slot changes.
#include "protocol.hpp"
#include "../in-game-hook/identity.hpp"
#include <algorithm>
#include <cstdio>
#include <span>

using namespace mw34::live_numeric;
using mw34::hook::admitted_image;
using mw34::hook::environment;
using mw34::hook::sha256;

struct Frame {
    std::uint32_t edi, esi, ebp, saved_esp, ebx, edx, ecx, eax, flags, caller;
};
static_assert(sizeof(void*) == 4 && offsetof(Frame, flags) == 32 && offsetof(Frame, caller) == 36);
extern "C" {
Cpu numeric_input{}, numeric_after{}, numeric_test_input{}, numeric_test_after{};
std::uint32_t numeric_host_esp{}, numeric_test_host_esp{}, numeric_test_mxcsr{0x1f80};
alignas(16) std::uint8_t numeric_guest_fx[512]{}, numeric_host_fx[512]{}, numeric_fx_after[512]{};
alignas(16) std::uint8_t numeric_test_host_fx[512]{}, numeric_test_fx_after[512]{};
std::uint8_t numeric_guest_env[28]{}, numeric_host_env[28]{}, numeric_env_after[28]{};
std::uint8_t numeric_test_host_env[28]{}, numeric_test_env_after[28]{};
void mw34_numeric_entry();
void numeric_enter();
void numeric_capture();
void numeric_restore();
void numeric_test_enter();
void numeric_test_capture();
}
namespace {
constexpr char wrapper_sha[] = "1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc";
constexpr char body_sha[] = "642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5";
constexpr char provider_sha[] = "91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a";
constexpr char provider_leaf_sha[] = "31d3ed84e61450051bfba7bc7265523bc3e687f3c7e1a1cb237ec08494ec3d1d";
// This test's actual modern SysWOW64 CRT was independently recovered from its
// file and observed loaded callback. Its ASLR-selected base is never invented.
constexpr char observed_crt_sha[] = "23a918921c545140d189ce6dc68590bacdeb0ab2f3e3a9a2d722c5aff45ce64f";
constexpr std::uint32_t observed_initterm_rva = 0x683b0, observed_return_offset = 31;
constexpr DWORD timeout_ms = 10000;
constexpr std::size_t stack_size = 16 * 4096;
struct Handle {
    HANDLE value{};
    explicit Handle(HANDLE h = nullptr) : value(h) {}
    ~Handle() { if (value && value != INVALID_HANDLE_VALUE) CloseHandle(value); }
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
};
struct Lock {
    CRITICAL_SECTION* value;
    explicit Lock(CRITICAL_SECTION& l) : value(&l) { EnterCriticalSection(value); }
    ~Lock() { LeaveCriticalSection(value); }
};
HANDLE log_file = INVALID_HANDLE_VALUE;
HANDLE pipe_file = INVALID_HANDLE_VALUE;
HANDLE worker_process{};
DWORD worker_pid{};
CRITICAL_SECTION serial{};
bool initialized{}, live{}, fixture{};
std::uint32_t sequence{};
std::uint64_t calls{};
std::filesystem::path capture_directory;
std::uint8_t* shadow_memory{};
std::uint8_t* test_memory{};
std::array<std::uint8_t, stack_size> shadow_snapshot{};
std::array<std::uint8_t, 44> fixture_globals{};
Request test_request{};
Response test_response{};
HMODULE provider_module{}, crt_module{};
std::uint32_t crt_initterm{}, crt_base{}, crt_image_size{};
std::string crt_file_sha, crt_export_sha;
std::uint32_t caller_opcode{}, caller_target{};

template <class T> T load(const void* p) { T x{}; std::memcpy(&x, p, sizeof(x)); return x; }
template <class T> std::uint32_t address(T* p) { return reinterpret_cast<std::uint32_t>(p); }
void require(bool ok, const char* reason) { if (!ok) throw std::runtime_error(reason); }
std::string escaped(const std::string& s) {
    std::string r;
    constexpr char hex[] = "0123456789abcdef";
    for (const unsigned char c : s) {
        if (c == '"' || c == '\\') { r += '\\'; r += static_cast<char>(c); }
        else if (c < 32) { r += "\\u00"; r += hex[c >> 4]; r += hex[c & 15]; }
        else r += static_cast<char>(c);
    }
    return r;
}
std::string utf8(const std::wstring& s) {
    const auto size = WideCharToMultiByte(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), nullptr, 0, nullptr, nullptr);
    require(size > 0, "UTF-8 path conversion failed");
    std::string r(static_cast<std::size_t>(size), '\0');
    require(WideCharToMultiByte(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), r.data(), size, nullptr, nullptr) == size,
            "UTF-8 path conversion failed");
    return r;
}
std::wstring module_path(HMODULE module) {
    std::array<wchar_t, 32768> p{};
    const auto count = GetModuleFileNameW(module, p.data(), static_cast<DWORD>(p.size()));
    require(count > 0 && count < p.size(), "Loaded module path unavailable");
    return std::wstring(p.data(), count);
}
std::vector<std::uint8_t> read_file(const std::wstring& path) {
    std::ifstream f(std::filesystem::path(path), std::ios::binary | std::ios::ate);
    require(static_cast<bool>(f), "Identity file unavailable");
    const auto count = f.tellg();
    require(count > 0 && count < 64 * 1024 * 1024, "Identity file size rejected");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(count));
    f.seekg(0);
    require(static_cast<bool>(f.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()))),
            "Identity file read failed");
    return bytes;
}
void log_line(const std::string& line) {
    DWORD wrote{};
    require(log_file != INVALID_HANDLE_VALUE && WriteFile(log_file, line.data(), static_cast<DWORD>(line.size()), &wrote, nullptr) &&
            wrote == line.size() && FlushFileBuffers(log_file), "Numeric evidence log write failed");
}
void log_fatal(const char* reason) noexcept {
    try { log_line("{\"event\":\"fatal\",\"message\":\"" + escaped(reason) + "\",\"win32\":" +
                   std::to_string(GetLastError()) + "}\n"); } catch (...) {}
    OutputDebugStringA(reason);
}
void binary(const std::filesystem::path& p, const void* bytes, std::size_t size) {
    Handle file(CreateFileW(p.c_str(), GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr));
    DWORD wrote{};
    require(file.value != INVALID_HANDLE_VALUE && WriteFile(file.value, bytes, static_cast<DWORD>(size), &wrote, nullptr) &&
            wrote == size && FlushFileBuffers(file.value), "Fresh binary capture publication failed");
}
void open_log() {
    const auto p = std::filesystem::path(environment(L"MW34_NUMERIC_LOG"));
    log_file = CreateFileW(p.c_str(), GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    require(log_file != INVALID_HANDLE_VALUE, "A fresh numeric log path is required");
    capture_directory = p.parent_path() / (p.stem().wstring() + L"-captures");
    require(std::filesystem::create_directory(capture_directory), "A fresh numeric capture directory is required");
}
void cancelled(OVERLAPPED& op) {
    CancelIoEx(pipe_file, &op);
    // Cancellation must finish before a stack-owned OVERLAPPED can disappear.
    if (WaitForSingleObject(op.hEvent, 1000) != WAIT_OBJECT_0) {
        log_fatal("Pipe cancellation did not complete");
        ExitProcess(91);
    }
}
DWORD finish(OVERLAPPED& op, ULONGLONG deadline) {
    const auto now = GetTickCount64();
    if (now >= deadline) { cancelled(op); throw std::runtime_error("Numeric IPC deadline exceeded"); }
    HANDLE waits[]{op.hEvent, worker_process};
    const auto count = worker_process ? 2U : 1U;
    const auto result = WaitForMultipleObjects(count, waits, FALSE, static_cast<DWORD>(deadline - now));
    if (result != WAIT_OBJECT_0) { cancelled(op); throw std::runtime_error("Numeric worker exited or IPC timed out"); }
    DWORD bytes{};
    require(GetOverlappedResult(pipe_file, &op, &bytes, FALSE) != FALSE, "Numeric pipe completion failed");
    return bytes;
}
void transfer(void* data, DWORD size, bool writing, ULONGLONG deadline) {
    auto* cursor = static_cast<std::uint8_t*>(data);
    while (size) {
        require(!worker_process || WaitForSingleObject(worker_process, 0) == WAIT_TIMEOUT, "Numeric worker is no longer live");
        Handle event(CreateEventW(nullptr, TRUE, FALSE, nullptr));
        require(event.value != nullptr, "IPC event allocation failed");
        OVERLAPPED op{}; op.hEvent = event.value;
        DWORD count{};
        const auto ok = writing ? WriteFile(pipe_file, cursor, size, &count, &op) : ReadFile(pipe_file, cursor, size, &count, &op);
        if (!ok) { require(GetLastError() == ERROR_IO_PENDING, "Numeric pipe transport failed"); count = finish(op, deadline); }
        require(count > 0 && count <= size, "Numeric pipe transfer extent failed");
        cursor += count; size -= count;
    }
}
Response exchange(const Request& request_value) {
    Response r{};
    const auto deadline = GetTickCount64() + timeout_ms;
    transfer(const_cast<Request*>(&request_value), sizeof(Request), true, deadline);
    transfer(&r, sizeof(r), false, deadline);
    require(std::memcmp(r.magic, response_magic, 8) == 0 && r.version == version && r.bytes == sizeof(r) &&
            r.sequence == request_value.sequence && r.worker_pid == worker_pid, "Numeric response identity/sequence rejected");
    require(WaitForSingleObject(worker_process, 0) == WAIT_TIMEOUT, "Numeric worker died before publication");
    require(r.status == 0 || r.status == 2 || r.status == 3, "Unknown numeric response status");
    return r;
}
void connect_worker() {
    const auto name = environment(L"MW34_NUMERIC_PIPE");
    require(name.starts_with(L"\\\\.\\pipe\\mw34-numeric-"), "Numeric pipe name outside authored namespace");
    pipe_file = CreateNamedPipeW(name.c_str(), PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED | FILE_FLAG_FIRST_PIPE_INSTANCE,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS, 1,
        sizeof(Response), sizeof(Request), timeout_ms, nullptr);
    require(pipe_file != INVALID_HANDLE_VALUE, "Numeric pipe server creation failed");
    Handle event(CreateEventW(nullptr, TRUE, FALSE, nullptr));
    require(event.value != nullptr, "Connect event allocation failed");
    OVERLAPPED op{}; op.hEvent = event.value;
    if (!ConnectNamedPipe(pipe_file, &op)) {
        const auto error = GetLastError();
        if (error == ERROR_IO_PENDING) finish(op, GetTickCount64() + timeout_ms);
        else require(error == ERROR_PIPE_CONNECTED, "Numeric worker connection failed");
    }
    ULONG pid{};
    require(GetNamedPipeClientProcessId(pipe_file, &pid) && pid && pid != GetCurrentProcessId(), "Numeric worker owner unavailable");
    worker_pid = pid;
    worker_process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, FALSE, worker_pid);
    require(worker_process != nullptr, "Numeric worker process unavailable");
    BOOL wow64{};
    require(IsWow64Process(worker_process, &wow64) && !wow64, "Numeric worker must be a native x64 process");
    std::array<wchar_t, 32768> path{}; DWORD size = static_cast<DWORD>(path.size());
    require(QueryFullProcessImageNameW(worker_process, 0, path.data(), &size) && size, "Numeric worker image owner unavailable");
    const auto worker_bytes = read_file(std::wstring(path.data(), size));
    auto handshake_request = request(++sequence, 0);
    handshake_request.pid = GetCurrentProcessId(); handshake_request.tid = GetCurrentThreadId();
    const auto handshake = exchange(handshake_request);
    require(handshake.status == 0, "Numeric transport handshake rejected");
    log_line("{\"event\":\"worker_handshake\",\"worker_pid\":" + std::to_string(worker_pid) +
        ",\"sequence\":" + std::to_string(sequence) + ",\"worker_path\":\"" + escaped(utf8(std::wstring(path.data(), size))) +
        "\",\"worker_sha256\":\"" + sha256(worker_bytes.data(), worker_bytes.size()) + "\",\"protocol_version\":1}\n");
}
std::uint8_t* guarded_stack() {
    auto* r = static_cast<std::uint8_t*>(VirtualAlloc(nullptr, stack_size + 8192, MEM_RESERVE, PAGE_NOACCESS));
    require(r != nullptr, "Guarded stack reservation failed");
    require(VirtualAlloc(r + 4096, stack_size, MEM_COMMIT, PAGE_READWRITE) == r + 4096, "Guarded stack commit failed");
    return r + 4096;
}
void source_check() {
    require(sha256(reinterpret_cast<void*>(root), 10) == wrapper_sha && sha256(reinterpret_cast<void*>(body), 117) == body_sha,
            "Loaded numeric wrapper/body changed");
    require(address(provider_module) == provider_base && load<std::uint32_t>(reinterpret_cast<void*>(slot)) == leaf &&
            sha256(reinterpret_cast<void*>(leaf), 7) == provider_leaf_sha &&
            load<std::uint32_t>(reinterpret_cast<void*>(leaf + 2)) == 0x78115004 &&
            load<std::uint32_t>(reinterpret_cast<void*>(0x78115004)) == 0x7f7fffff,
            "Loaded exact provider/IAT/source operand changed");
}
void prepare_loaded_owners() {
    require(address(GetModuleHandleW(nullptr)) == 0x400000, "Unsupported loaded game base");
    admitted_image(module_path(nullptr));
    provider_module = GetModuleHandleW(L"MSVCP50.dll");
    require(provider_module != nullptr, "Loaded MSVCP50 owner missing");
    const auto provider_path = module_path(provider_module);
    const auto provider_bytes = read_file(provider_path);
    require(provider_bytes.size() == 565760 && sha256(provider_bytes.data(), provider_bytes.size()) == provider_sha,
            "Exact loaded provider disk identity rejected");
    const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(provider_bytes.data());
    require(dos->e_magic == IMAGE_DOS_SIGNATURE && dos->e_lfanew > 0 &&
            static_cast<std::size_t>(dos->e_lfanew) + sizeof(IMAGE_NT_HEADERS32) <= provider_bytes.size(), "Provider PE header rejected");
    const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS32*>(provider_bytes.data() + dos->e_lfanew);
    require(nt->Signature == IMAGE_NT_SIGNATURE && nt->OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR32_MAGIC &&
            nt->OptionalHeader.ImageBase == provider_base &&
            address(GetProcAddress(provider_module, "?max@?$numeric_limits@M@std@@SAMXZ")) == leaf,
            "Provider preferred base or export owner rejected");
    source_check();
    require(load<std::uint32_t>(reinterpret_cast<void*>(table_slot)) == root, "Loaded initializer slot differs from exact root");
    crt_module = GetModuleHandleW(L"MSVCRT.dll");
    require(crt_module != nullptr, "Actual loaded MSVCRT missing");
    const auto entry = GetProcAddress(crt_module, "_initterm");
    HMODULE owner{};
    require(entry && GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(entry), &owner) && owner == crt_module, "Actual _initterm export owner rejected");
    crt_base = address(crt_module); crt_initterm = address(entry);
    const auto* loaded_dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(crt_module);
    const auto* loaded_nt = reinterpret_cast<const IMAGE_NT_HEADERS32*>(reinterpret_cast<const std::uint8_t*>(crt_module) + loaded_dos->e_lfanew);
    crt_image_size = loaded_nt->OptionalHeader.SizeOfImage;
    require(crt_initterm >= crt_base && std::uint64_t{crt_initterm} + 512 <= std::uint64_t{crt_base} + crt_image_size,
            "Actual _initterm range exceeds owning image");
    const auto crt_path = module_path(crt_module);
    const auto crt_bytes = read_file(crt_path);
    crt_file_sha = sha256(crt_bytes.data(), crt_bytes.size());
    require(crt_file_sha == observed_crt_sha && crt_initterm - crt_base == observed_initterm_rva,
            "Actual observed MSVCRT disk/export profile differs");
    crt_export_sha = sha256(reinterpret_cast<void*>(crt_initterm), 512);
    require(load<std::uint16_t>(reinterpret_cast<void*>(crt_initterm + observed_return_offset - 2)) == 0xd7ff,
            "Actual observed _initterm CALL EDI source differs");
    log_line("{\"event\":\"loaded_owners\",\"provider_base\":" + std::to_string(address(provider_module)) +
        ",\"provider_path\":\"" + escaped(utf8(provider_path)) + "\",\"provider_sha256\":\"" + provider_sha +
        "\",\"iat_target\":" + std::to_string(leaf) + ",\"crt_base\":" + std::to_string(crt_base) +
        ",\"crt_path\":\"" + escaped(utf8(crt_path)) + "\",\"crt_sha256\":\"" + crt_file_sha +
        "\",\"initterm_export\":" + std::to_string(crt_initterm) + ",\"initterm_512_sha256\":\"" + crt_export_sha +
        "\",\"initterm_export_rva\":" + std::to_string(observed_initterm_rva) +
        ",\"admitted_call_register\":\"EDI\",\"admitted_return_offset\":31}\n");
}
bool owned_caller(const Request& r) {
    caller_opcode = 0; caller_target = r.cpu.edi;
    const auto caller = r.caller;
    HMODULE owner{};
    if (!(crt_file_sha == observed_crt_sha && crt_initterm - crt_base == observed_initterm_rva &&
        caller == crt_initterm + observed_return_offset && caller >= crt_base &&
        std::uint64_t{caller} < std::uint64_t{crt_base} + crt_image_size &&
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(caller), &owner) && owner == crt_module &&
        GetModuleHandleW(L"MSVCRT.dll") == crt_module &&
        sha256(reinterpret_cast<void*>(crt_initterm), 512) == crt_export_sha)) return false;
    caller_opcode = load<std::uint16_t>(reinterpret_cast<void*>(caller - 2));
    return caller_opcode == 0xd7ff && r.cpu.edi == address(&mw34_numeric_entry) && r.cpu.esi == table_slot &&
        load<std::uint32_t>(reinterpret_cast<void*>(table_slot)) == r.cpu.edi;
}
Cpu cpu(const Frame& f) {
    return {f.eax, f.ecx, f.edx, f.ebx, f.saved_esp + 4U, f.ebp, f.esi, f.edi, f.flags, root};
}
void publish(Frame& f, const Cpu& c) {
    f.eax = c.eax; f.ecx = c.ecx; f.edx = c.edx; f.ebx = c.ebx;
    f.ebp = c.ebp; f.esi = c.esi; f.edi = c.edi; f.flags = c.flags;
}
Request prepare(const Frame& f, const std::uint8_t* fx, const std::uint8_t* env) {
    auto r = request(++sequence, fixture ? 1U : 2U);
    r.pid = GetCurrentProcessId(); r.tid = GetCurrentThreadId(); r.cpu = cpu(f); r.caller = f.caller;
    std::memcpy(r.fx.data(), fx, 512); std::memcpy(r.env.data(), env, 28);
    std::memcpy(r.globals.data(), fixture ? fixture_globals.data() : reinterpret_cast<void*>(output), 44);
    std::uint16_t cs_value{}, ds_value{}, ss_value{}, fs_value{};
    __asm {
        mov ax, cs
        mov cs_value, ax
        mov ax, ds
        mov ds_value, ax
        mov ax, ss
        mov ss_value, ax
        mov ax, fs
        mov fs_value, ax
    }
    r.cs = cs_value; r.ds = ds_value; r.ss = ss_value;
    LDT_ENTRY entry{};
    require(GetThreadSelectorEntry(GetCurrentThread(), fs_value, &entry) != FALSE, "Actual FS selector ownership unavailable");
    r.fs_base = entry.BaseLow | (static_cast<std::uint32_t>(entry.HighWord.Bytes.BaseMid) << 16) |
                (static_cast<std::uint32_t>(entry.HighWord.Bytes.BaseHi) << 24);
    r.provider_base = fixture ? provider_base : address(provider_module);
    r.provider_bits = fixture ? 0x7f7fffffU : load<std::uint32_t>(reinterpret_cast<void*>(0x78115004));
    r.iat_target = fixture ? leaf : load<std::uint32_t>(reinterpret_cast<void*>(slot));
    return r;
}
bool same_cpu(const Cpu& a, const Cpu& b) { return std::memcmp(&a, &b, sizeof(a)) == 0; }
bool same_numeric_fx(const std::uint8_t* a, const std::uint8_t* b) {
    if (std::memcmp(a, b, 5) || std::memcmp(a + 24, b + 24, 8)) return false;
    for (unsigned i = 0; i < 8; ++i) {
        if (std::memcmp(a + 32 + i * 16, b + 32 + i * 16, 10) ||
            std::memcmp(a + 160 + i * 16, b + 160 + i * 16, 16)) return false;
    }
    return true;
}
void response_contract(const Request& before, const Response& after) {
    auto expected = before.cpu; expected.esp += 4; expected.eip = before.caller;
    require(same_cpu(expected, after.cpu), "Native full CPU/flags/RET0 projection differs");
    require(after.steps == 22 && after.complete == 1, "Native compiled numeric closure incomplete");
    constexpr std::array<std::uint32_t, 15> routes{
        broker, root, broker, 0, 1, 0x4c19f3, body, 0x4c19f8, 0, 1, 0x4c1a03, slot, 0x4c1a09, 1, 1};
    require(after.routes == routes, "Native three completed compiled call routes differ");
    constexpr std::array<std::uint32_t, 22> event_addresses{
        virtual_frame-4, virtual_frame-8, virtual_frame-12, slot, virtual_frame-16, 0x78115004, virtual_frame-16,
        output, output+4, output+8, output+12, output+16, output+20, output+24, output+28, output+32, output+36, output+40,
        virtual_frame-12, virtual_frame-8, virtual_frame-4, virtual_frame};
    for (unsigned i = 0; i < after.events.size(); ++i) {
        const bool writing = i < 3 || i == 4 || (i >= 7 && i <= 17);
        require(after.events[i].address == event_addresses[i] && after.events[i].width == 4 &&
                after.events[i].write == static_cast<unsigned>(writing), "Native 22 ordered numeric memory events differ");
    }
    require(load<std::uint32_t>(after.globals.data()) == before.provider_bits &&
            std::all_of(after.globals.begin() + 4, after.globals.end(), [](auto b) { return b == 0; }), "Native numeric globals differ");
    require(load<std::uint32_t>(after.env.data() + 12) == 0x4c1a09 &&
            (load<std::uint32_t>(after.env.data() + 16) >> 16) == 0x11d &&
            load<std::uint32_t>(after.env.data() + 20) == output, "Native legacy FP instruction/data provenance differs");
}
DWORD execute_original() {
    __try { numeric_enter(); return 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { const auto code = GetExceptionCode(); numeric_restore(); return code; }
}
#pragma pack(push, 1)
struct Original { Cpu literal{}, projected{}; std::array<std::uint8_t, 512> fx{}; std::array<std::uint8_t, 28> env{};
    std::array<std::uint8_t, 44> globals{}; std::uint32_t shadow_entry{}, capture{}, fault{}; };
#pragma pack(pop)
Original original(const Request& r) {
    for (std::size_t i = 0; i < stack_size; ++i) shadow_memory[i] = static_cast<std::uint8_t>((i * 37 + sequence * 71) & 255);
    const auto shadow_esp = address(shadow_memory + stack_size - 1024);
    const auto sentinel = address(&numeric_capture);
    std::memcpy(reinterpret_cast<void*>(shadow_esp), &sentinel, 4);
    std::memcpy(shadow_snapshot.data(), shadow_memory, stack_size);
    numeric_input = r.cpu; numeric_input.esp = shadow_esp; numeric_input.eip = root; numeric_after = {};
    std::memcpy(numeric_guest_fx, r.fx.data(), 512); std::memcpy(numeric_guest_env, r.env.data(), 28);
    // Restore literal before globals; original body temporarily writes the live
    // 44-byte output while this initializer thread cannot continue its caller.
    std::memcpy(reinterpret_cast<void*>(output), r.globals.data(), 44);
    Original result{}; result.shadow_entry = shadow_esp; result.capture = sentinel; result.fault = execute_original();
    result.literal = numeric_after; result.projected = numeric_after;
    std::memcpy(result.fx.data(), numeric_fx_after, 512); std::memcpy(result.env.data(), numeric_env_after, 28);
    std::memcpy(result.globals.data(), reinterpret_cast<void*>(output), 44);
    require(!result.fault, "Unmodified original initializer faulted on guarded stack");
    require(result.literal.esp == shadow_esp + 4 && result.literal.eip == sentinel, "Original isolated RET0 capture differs");
    const auto written_begin = stack_size - 1024 - 16;
    require(std::memcmp(shadow_snapshot.data(), shadow_memory, written_begin) == 0 &&
            std::memcmp(shadow_snapshot.data() + written_begin + 16, shadow_memory + written_begin + 16,
                        stack_size - written_begin - 16) == 0, "Original wrote outside declared private stack slots");
    result.projected.esp = r.cpu.esp + 4; result.projected.eip = r.caller;
    source_check();
    return result;
}
void captures(const Request& r, const Response* native, const Original* actual) {
    const auto prefix = capture_directory / (L"call-" + std::to_wstring(r.sequence));
    binary(prefix.wstring() + L".before.bin", &r, sizeof(r));
    if (native) binary(prefix.wstring() + L".native.bin", native, sizeof(*native));
    if (actual) binary(prefix.wstring() + L".original.bin", actual, sizeof(*actual));
}
void record(const Request& r, const Response* n, const Original* o, bool applied, const std::string& reason,
            const std::string& worker_reason = {}, const std::string& caller_reason = {}) {
    const auto original_hash = o ? sha256(o, sizeof(*o)) : std::string{};
    const auto native_hash = n ? sha256(n, sizeof(*n)) : std::string{};
    const auto prefix = capture_directory / (L"call-" + std::to_wstring(r.sequence));
    const auto input_path = escaped(utf8(prefix.wstring() + L".before.bin"));
    const auto output_path = n ? escaped(utf8(prefix.wstring() + L".native.bin")) : std::string{};
    const auto original_path = o ? escaped(utf8(prefix.wstring() + L".original.bin")) : std::string{};
    log_line("{\"event\":\"" + std::string(fixture ? "hook_selftest_call" : "game_call") + "\",\"call\":" +
        std::to_string(++calls) + ",\"pid\":" + std::to_string(r.pid) + ",\"tid\":" + std::to_string(r.tid) +
        ",\"in_game\":" + (live ? "true" : "false") + ",\"native_applied\":" + (applied ? "true" : "false") +
        ",\"worker_pid\":" + std::to_string(worker_pid) + ",\"sequence\":" + std::to_string(r.sequence) +
        ",\"caller_va\":" + std::to_string(r.caller) + ",\"crt_base\":" + std::to_string(crt_base) +
        ",\"caller_rva\":" + std::to_string(live && r.caller >= crt_base ? r.caller - crt_base : 0) +
        ",\"before_sha256\":\"" + sha256(&r, sizeof(r)) + "\",\"native_sha256\":\"" + native_hash +
        "\",\"original_sha256\":\"" + original_hash + "\",\"input_snapshot\":\"" + input_path +
        "\",\"output_snapshot\":\"" + output_path + "\",\"original_snapshot\":\"" + original_path +
        "\",\"reason\":\"" + escaped(reason) + "\",\"worker_rejection_reason\":\"" + escaped(worker_reason) +
        "\",\"caller_rejection_reason\":\"" + escaped(caller_reason) +
        "\",\"caller_register\":\"" + (live ? "EDI" : "synthetic") +
        "\",\"caller_opcode\":" + std::to_string(caller_opcode) + ",\"caller_target\":" + std::to_string(caller_target) +
        ",\"caller_table_slot\":" + std::to_string(live ? r.cpu.esi : 0) +
        ",\"crt_sha256\":\"" + crt_file_sha +
        "\",\"stack_delta\":4,\"arguments\":0,\"cpu_full_flags_compared\":" + (o && n && applied ? "true" : "false") +
        ",\"fp_numeric_compared\":" + (o && n && applied ? "true" : "false") +
        ",\"env28_compared\":" + (o && n && applied ? "true" : "false") +
        ",\"original_compare\":" + (o && n && applied ? "true" : "false") +
        ",\"native_events\":" + std::to_string(n ? n->steps : 0) +
        ",\"native_completed_routes\":" + std::to_string(n && n->complete ? 3 : 0) +
        ",\"output_bytes_compared\":" + std::to_string(o && n && applied ? 44 : 0) +
        ",\"fx_compare_scope\":\"CW,SW,physical-FTW,raw80x8,XMMx8,MXCSR,MXCSRmask;legacy/reserved-metadata-separate\","
        "\"env_compare_scope\":\"all28bytes;FIP=4c1a09;FOP=11d;FDP=60b368;CS/DS=actual-segments\"}\n");
}
void initialize() {
    require(!initialized, "Numeric bridge already initialized");
    open_log();
    const auto image = admitted_image(environment(L"MW34_GAME_FILE"));
    (void)image;
    InitializeCriticalSection(&serial);
    shadow_memory = guarded_stack();
    connect_worker();
    log_line("{\"event\":\"identity\",\"image_sha256\":\"" + std::string(mw34::hook::game_sha) +
        "\",\"wrapper_sha256\":\"" + wrapper_sha + "\",\"body_sha256\":\"" + body_sha +
        "\",\"provider_sha256\":\"" + provider_sha + "\",\"provider_leaf_sha256\":\"" + provider_leaf_sha + "\"}\n");
    initialized = true;
}
void self_tests() {
    fixture = true;
    test_memory = guarded_stack();
    const auto test_esp = address(test_memory + stack_size - 4096);
    const auto test_return = address(&numeric_test_capture);
    constexpr std::array<std::uint32_t, 8> flag_cases{
        0x202, 0x202 | 0xcd5, 0x202 | 0x400, 0x202 | 0x800,
        0x202 | 0x801, 0x202 | 0x4d5, 0x202 | 0x8d5, 0x202 | 0xcc0};
    for (unsigned i = 0; i < 8; ++i) {
        std::memset(test_memory + stack_size - 4096, 0xa5, 4096);
        std::memcpy(reinterpret_cast<void*>(test_esp), &test_return, 4);
        std::array<std::uint8_t, 4096> caller_bytes{};
        std::memcpy(caller_bytes.data(), reinterpret_cast<void*>(test_esp), caller_bytes.size());
        fixture_globals.fill(0xa5);
        numeric_test_input = {0x13579bdfU ^ i, 0x2468ace0U + i, 0x81726354U - i, 0x10293847U ^ (i * 17),
            test_esp, 0x92837465U + i, 0x56473829U - i, 0xaabbccddU ^ i, flag_cases[i], root};
        numeric_test_after = {};
        numeric_test_enter();
        response_contract(test_request, test_response);
        require(same_cpu(numeric_test_after, test_response.cpu) &&
                same_numeric_fx(numeric_test_fx_after, test_response.fx.data()) &&
                std::memcmp(numeric_test_env_after, test_response.env.data(), 28) == 0 &&
                std::memcmp(caller_bytes.data(), reinterpret_cast<void*>(test_esp), caller_bytes.size()) == 0,
                "Authored thunk full CPU/flags/RET0/native FP restoration fixture differs");
    }
    log_line("{\"event\":\"hook_thunk_selftest\",\"cases\":8,\"mismatches\":0,\"arguments\":0,\"stack_delta\":4,"
             "\"full_flags_preserved\":true,\"direction_and_overflow_flags_tested\":true,\"native_after_fp_restored\":true,"
             "\"caller_memory_bytes\":4096,\"in_game\":false,\"native_applied\":false}\n");
    fixture = false;
}
} // namespace

extern "C" void mw34_numeric_dispatch(Frame* f, std::uint8_t* fx, std::uint8_t* env) {
    Lock hold(serial);
    try {
        require(initialized && (live || fixture), "Numeric thunk entered outside initialized mode");
        if (live) source_check();
        const auto before = prepare(*f, fx, env);
        if (fixture) {
            const auto native = exchange(before);
            require(native.status == 0, "Synthetic numeric fixture rejected");
            response_contract(before, native);
            test_request = before; test_response = native;
            captures(before, &native, nullptr); record(before, &native, nullptr, false, "synthetic-preflight-only");
            fixture_globals = native.globals; publish(*f, native.cpu);
            std::memcpy(fx, native.fx.data(), 512); std::memcpy(env, native.env.data(), 28);
            return;
        }
        const auto native = exchange(before);
        const bool caller_admitted = owned_caller(before);
        std::string worker_rejection, caller_rejection;
        if (native.status == 2) {
            worker_rejection = std::string(native.error, strnlen_s(native.error, sizeof(native.error)));
            if (worker_rejection.empty()) worker_rejection = "Numeric worker rejected actual input";
        } else require(native.status == 0, "Numeric worker execution failed");
        if (!caller_admitted) caller_rejection = "Actual caller does not match pinned loaded MSVCRT _initterm CALL EDI/table-slot/target ownership";
        const auto rejection = worker_rejection + (worker_rejection.empty() || caller_rejection.empty() ? "" : "; ") + caller_rejection;
        const auto actual = original(before);
        if (!rejection.empty()) {
            captures(before, &native, &actual);
            record(before, &native, &actual, false, rejection, worker_rejection, caller_rejection);
            publish(*f, actual.projected); std::memcpy(fx, actual.fx.data(), 512); std::memcpy(env, actual.env.data(), 28);
            return;
        }
        captures(before, &native, &actual);
        response_contract(before, native);
        const auto expected_env_cs = load<std::uint32_t>(actual.env.data() + 16) & 0xffff;
        const auto expected_env_ds = load<std::uint32_t>(actual.env.data() + 24) & 0xffff;
        const bool matched = same_cpu(native.cpu, actual.projected) && same_numeric_fx(native.fx.data(), actual.fx.data()) &&
            native.globals == actual.globals && native.env == actual.env &&
            expected_env_cs == before.cs && expected_env_ds == before.ds;
        if (!matched) { record(before, &native, &actual, false, "native-original-state-mismatch"); throw std::runtime_error("Native/original numeric CPU/FP/ENV/globals mismatch"); }
        // Live credit starts only here: native bytes replace temporary original
        // globals and native numerical FX+legacy ENV return through the thunk.
        std::memcpy(reinterpret_cast<void*>(output), native.globals.data(), 44);
        publish(*f, native.cpu); std::memcpy(fx, native.fx.data(), 512); std::memcpy(env, native.env.data(), 28);
        record(before, &native, &actual, true, "verified-compiled-x64-result-published");
    } catch (const std::exception& e) {
        log_fatal(e.what());
        // This process is the launcher's owned child. Never continue past a
        // mismatch with silently substituted original output.
        ExitProcess(91);
    }
}
extern "C" DWORD WINAPI mw34_selftest(void*) {
    try { initialize(); self_tests(); return 0; }
    catch (const std::exception& e) { log_fatal(e.what()); return 90; }
}
extern "C" DWORD WINAPI mw34_install(void*) {
    try {
        initialize(); prepare_loaded_owners();
        auto* slot_pointer = reinterpret_cast<volatile LONG*>(table_slot);
        DWORD old{};
        require(VirtualProtect(reinterpret_cast<void*>(table_slot), 4, PAGE_READWRITE, &old) != FALSE,
                "Initializer slot protection failed");
        const auto original_slot = InterlockedCompareExchange(slot_pointer, static_cast<LONG>(address(&mw34_numeric_entry)), static_cast<LONG>(root));
        DWORD ignored{};
        const auto protected_again = VirtualProtect(reinterpret_cast<void*>(table_slot), 4, old, &ignored);
        require(original_slot == static_cast<LONG>(root) && protected_again, "Initializer slot publication/protection failed");
        source_check(); live = true;
        log_line("{\"event\":\"installed\",\"pid\":" + std::to_string(GetCurrentProcessId()) +
            ",\"table_slot\":" + std::to_string(table_slot) + ",\"original_pointer\":" + std::to_string(root) +
            ",\"hook_pointer\":" + std::to_string(address(&mw34_numeric_entry)) +
            ",\"patched_code_bytes\":0,\"changed_table_bytes\":4,\"on_disk_game_unchanged\":true,"
            "\"original_comparison_scope\":\"initializer-thread-held;other-game-threads-not-suspended\"}\n");
        return 0;
    } catch (const std::exception& e) { log_fatal(e.what()); return 90; }
}
BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) { return TRUE; }
