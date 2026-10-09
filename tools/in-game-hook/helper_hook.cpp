#include "identity.hpp"
#include <algorithm>
#include <bit>
#include <cstdio>
#include <cstring>

using namespace mw34::hook;
struct Cpu { std::uint32_t r[8]; std::uint32_t flags, eip; };
// PUSHAD at the hook entry follows PUSHFD; saved ESP is entry ESP minus four.
struct Frame { std::uint32_t edi, esi, ebp, saved_esp, ebx, edx, ecx, eax, flags, caller, n; };
static_assert(sizeof(Cpu) == 40 && offsetof(Frame, flags) == 32 && offsetof(Frame, n) == 40);
extern "C" {
Cpu mw34_shadow_input{}, mw34_shadow_output{};
Cpu mw34_hook_input{}, mw34_hook_output{};
alignas(16) std::array<std::uint8_t, 512> mw34_hook_fp_input{}, mw34_hook_fp_output{};
std::uint32_t mw34_shadow_host_esp{}, mw34_shadow_entry{}, mw34_shadow_sentinel{};
std::uint32_t mw34_hook_host_esp{}, mw34_hook_sentinel{};
void mw34_hook_entry();
void mw34_enter_shadow();
void mw34_capture_shadow();
void mw34_enter_hook_test();
void mw34_capture_hook_test();
}
static HANDLE log_file = INVALID_HANDLE_VALUE;
static CRITICAL_SECTION lock;
static std::uint8_t *shadow_memory{};
static std::array<std::uint8_t, 4096> snapshot{};
static std::uint64_t calls{};
static bool initialized{};
static bool in_game{};

static bool cpu_matches(const Cpu &a, const Cpu &b) {
    return std::equal(std::begin(a.r), std::end(a.r), std::begin(b.r)) &&
        !((a.flags ^ b.flags) & observed_mask) && a.eip == b.eip;
}

static void log_line(const char *line) {
    const auto size = static_cast<DWORD>(std::strlen(line));
    DWORD written{};
    if (log_file == INVALID_HANDLE_VALUE || !WriteFile(log_file, line, size, &written, nullptr) || written != size)
        throw std::runtime_error("Research log write failed");
    if (!FlushFileBuffers(log_file)) throw std::runtime_error("Research log flush failed");
}
static Cpu replacement(const Cpu &input, std::uint32_t n) {
    auto result = input;
    const auto t = n * 48U;
    const auto r = t - n;
    std::uint32_t flags = 0;
    if (t < n) flags |= 1;
    if ((std::popcount(r & 255U) & 1) == 0) flags |= 4;
    if ((t ^ n ^ r) & 16U) flags |= 16;
    if (r == 0) flags |= 64;
    if (r & 0x80000000U) flags |= 128;
    if ((t ^ n) & (t ^ r) & 0x80000000U) flags |= 0x800;
    result.r[0] = input.r[1] + n * 188U + 312U;
    result.r[2] = r;
    result.r[4] += 8U;
    result.flags = (input.flags & ~arithmetic_mask) | flags;
    result.eip = mw34_shadow_sentinel;
    return result;
}
static std::uint32_t execute_shadow() {
    __try { mw34_enter_shadow(); return 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return GetExceptionCode(); }
}
static void prepare_original(const std::uint8_t *code) {
    auto *page = static_cast<std::uint8_t *>(VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (!page) throw std::runtime_error("Shadow code allocation failed");
    std::memcpy(page, code, leaf_size);
    mw34_shadow_entry = reinterpret_cast<std::uint32_t>(page);
    mw34_shadow_sentinel = reinterpret_cast<std::uint32_t>(page + 0x100);
    page[0x100] = 0xe9;
    const auto displacement = reinterpret_cast<std::uint32_t>(&mw34_capture_shadow) - (mw34_shadow_sentinel + 5U);
    std::memcpy(page + 0x101, &displacement, 4);
    DWORD old{};
    if (!VirtualProtect(page, 4096, PAGE_EXECUTE_READ, &old) || !FlushInstructionCache(GetCurrentProcess(), page, 4096))
        throw std::runtime_error("Shadow code protection failed");
    auto *reservation = static_cast<std::uint8_t *>(VirtualAlloc(nullptr, 3 * 4096, MEM_RESERVE, PAGE_NOACCESS));
    if (!reservation) throw std::runtime_error("Shadow stack reservation failed");
    shadow_memory = reservation + 4096;
    if (VirtualAlloc(shadow_memory, 4096, MEM_COMMIT, PAGE_READWRITE) != shadow_memory)
        throw std::runtime_error("Shadow stack commit failed");
}
static Cpu check_case(Cpu input, std::uint32_t n, std::uint32_t seed, std::uint32_t stack_offset = 2048) {
    if (stack_offset < 16 || stack_offset > 4080) throw std::runtime_error("Unsafe shadow stack");
    for (std::size_t i = 0; i < 4096; ++i) shadow_memory[i] = static_cast<std::uint8_t>((i * 37 + seed) & 255);
    input.r[4] = reinterpret_cast<std::uint32_t>(shadow_memory + stack_offset);
    input.flags = 0x202U | (input.flags & observed_mask);
    input.eip = mw34_shadow_entry;
    std::memcpy(shadow_memory + stack_offset, &mw34_shadow_sentinel, 4);
    std::memcpy(shadow_memory + stack_offset + 4, &n, 4);
    std::memcpy(snapshot.data(), shadow_memory, 4096);
    mw34_shadow_input = input;
    mw34_shadow_output = {};
    if (execute_shadow()) throw std::runtime_error("Original shadow hardware fault");
    auto expected = replacement(input, n);
    const auto &actual = mw34_shadow_output;
    if (!cpu_matches(actual, expected) || std::memcmp(snapshot.data(), shadow_memory, 4096))
        throw std::runtime_error("Original/replacement state or memory mismatch");
    return actual;
}
static void self_tests() {
    std::uint32_t random = 0x3434;
    auto next = [&]() { random ^= random << 13; random ^= random >> 17; random ^= random << 5; return random; };
    constexpr std::array<std::uint32_t, 20> edges{0, 1, 2, 7, 8, 15, 16, 255, 256,
        0x05555554, 0x05555555, 0x05555556, 0x10000000, 0x20000000, 0x7fffffff,
        0x80000000, 0xaaaaaaaau, 0xfffffff7u, 0xfffffff8u, 0xffffffffu};
    unsigned cases = 0;
    for (const auto n : edges) for (const auto base : edges) {
        Cpu input{};
        for (auto &r : input.r) r = next();
        input.r[1] = base; input.flags = next();
        check_case(input, n, next(), 16 + cases % 32); ++cases;
    }
    for (unsigned i = 0; i < 10000; ++i) {
        Cpu input{};
        for (auto &r : input.r) r = next();
        input.flags = next(); const auto n = next();
        check_case(input, n, next(), 16 + i % 4065); ++cases;
    }
    char line[256];
    std::snprintf(line, sizeof(line), "{\"event\":\"selftest\",\"cases\":%u,\"mismatches\":0,\"memory_bytes_per_case\":4096,\"seed\":13364}\n", cases);
    log_line(line);
    Cpu input{}; input.flags = 0x202;
    const auto valid = check_case(input, 0xffffffffU, 123);
    for (unsigned field : {0U, 2U, 3U, 4U}) {
        auto corrupt = valid; corrupt.r[field] ^= 1U;
        if (cpu_matches(corrupt, valid)) throw std::runtime_error("Register corruption control did not fail");
    }
    auto corrupt = valid; corrupt.flags ^= 1U;
    if (cpu_matches(corrupt, valid)) throw std::runtime_error("Flag corruption control did not fail");
    corrupt = valid; corrupt.eip ^= 1U;
    if (cpu_matches(corrupt, valid)) throw std::runtime_error("Return corruption control did not fail");
    shadow_memory[0] ^= 1U;
    if (!std::memcmp(snapshot.data(), shadow_memory, 4096)) throw std::runtime_error("Memory corruption control did not fail");
    shadow_memory[0] ^= 1U;
    log_line("{\"event\":\"comparison_controls\",\"cases\":7,\"rejected\":7}\n");
}
static void initialize(const std::vector<std::uint8_t> &image) {
    if (initialized) throw std::runtime_error("Hook already initialized");
    const auto path = environment(L"MW34_HOOK_LOG");
    log_file = CreateFileW(path.c_str(), GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (log_file == INVALID_HANDLE_VALUE) throw std::runtime_error("New log path required");
    InitializeCriticalSection(&lock);
    prepare_original(image.data() + leaf_offset);
    log_line("{\"event\":\"identity\",\"profile\":\"mw3-us-1-2-retail\",\"image_sha256\":\"95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf\",\"entry_va\":4234960,\"replacement\":\"authored-x86-integer-helper-v1\"}\n");
    self_tests();
    initialized = true;
}
extern "C" void mw34_dispatch(Frame *frame) {
    EnterCriticalSection(&lock);
    try {
        Cpu input{{frame->eax, frame->ecx, frame->edx, frame->ebx,
                   frame->saved_esp + 4U, frame->ebp, frame->esi, frame->edi}, frame->flags, static_cast<std::uint32_t>(guest_entry)};
        const auto actual = check_case(input, frame->n, static_cast<std::uint32_t>(calls));
        const auto result = replacement(input, frame->n);
        // Only the reviewed outputs change in the saved live game context.
        frame->eax = result.r[0]; frame->edx = result.r[2]; frame->flags = result.flags;
        char line[640];
        std::snprintf(line, sizeof(line), "{\"event\":\"%s\",\"call\":%llu,\"pid\":%lu,\"tid\":%lu,\"caller_va\":%u,\"n\":%u,\"base\":%u,\"eax\":%u,\"edx\":%u,\"flags\":%u,\"original_eax\":%u,\"original_edx\":%u,\"original_flags\":%u,\"registers_match\":true,\"stack_delta\":8,\"memory_unchanged\":true}\n",
            in_game ? "game_call" : "hook_selftest_call", ++calls, GetCurrentProcessId(), GetCurrentThreadId(), frame->caller, frame->n,
            input.r[1], result.r[0], result.r[2], result.flags & observed_mask,
            actual.r[0], actual.r[2], actual.flags & observed_mask);
        log_line(line);
        LeaveCriticalSection(&lock);
    } catch (const std::exception &e) {
        char line[256]; std::snprintf(line, sizeof(line), "{\"event\":\"fatal\",\"message\":\"%s\"}\n", e.what());
        try { log_line(line); } catch (...) {}
        // Never hide a mismatch by reverting to the original function.
        ExitProcess(91);
    }
}
static void hook_tests() {
    // Larger guarded stack accommodates the authored logger/C++ scratch frame.
    constexpr auto size = 16 * 4096;
    auto *reservation = static_cast<std::uint8_t *>(VirtualAlloc(nullptr, size + 2 * 4096, MEM_RESERVE, PAGE_NOACCESS));
    if (!reservation) throw std::runtime_error("Hook-test stack reservation failed");
    auto *memory = reservation + 4096;
    if (VirtualAlloc(memory, size, MEM_COMMIT, PAGE_READWRITE) != memory)
        throw std::runtime_error("Hook-test stack commit failed");
    mw34_hook_sentinel = reinterpret_cast<std::uint32_t>(&mw34_capture_hook_test);
    for (unsigned i = 0; i < 64; ++i) {
        Cpu input{};
        for (unsigned r = 0; r < 8; ++r) input.r[r] = 0xdeadbeefU ^ (i * 73471U + r * 117871U);
        input.r[4] = reinterpret_cast<std::uint32_t>(memory + size - 1024);
        input.flags = 0x202U | ((i * 113U) & observed_mask);
        const auto n = i < 32 ? i : (0xffffffffU - i * 0x05555555U);
        std::array<std::uint8_t, 1024> caller_bytes{};
        std::memcpy(caller_bytes.data(), &mw34_hook_sentinel, 4);
        std::memcpy(caller_bytes.data() + 4, &n, 4);
        std::memcpy(memory + size - 1024, caller_bytes.data(), caller_bytes.size());
        mw34_hook_input = input; mw34_hook_output = {};
        mw34_enter_hook_test();
        auto expected = replacement(input, n); expected.eip = mw34_hook_sentinel;
        if (!cpu_matches(expected, mw34_hook_output) ||
            std::memcmp(memory + size - 1024, caller_bytes.data(), caller_bytes.size()) ||
            mw34_hook_fp_input != mw34_hook_fp_output)
            throw std::runtime_error("Hook thunk state, FP/vector or caller-memory mismatch");
    }
    log_line("{\"event\":\"hook_thunk_selftest\",\"cases\":64,\"mismatches\":0,\"caller_memory_bytes_per_case\":1024,\"fp_vector_preserved\":true}\n");
    VirtualFree(reservation, 0, MEM_RELEASE);
    calls = 0;
}
extern "C" DWORD WINAPI mw34_selftest(void *) {
    try { initialize(admitted_image(environment(L"MW34_GAME_FILE"))); hook_tests(); return 0; }
    catch (const std::exception &e) { OutputDebugStringA(e.what()); return 90; }
}
extern "C" DWORD WINAPI mw34_install(void *) {
    try {
        std::array<wchar_t, 32768> path{};
        const auto count = GetModuleFileNameW(nullptr, path.data(), static_cast<DWORD>(path.size()));
        if (!count || count >= path.size() || reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)) != 0x400000)
            throw std::runtime_error("Unsupported loaded game image");
        auto image = admitted_image(std::wstring(path.data(), count));
        auto *target = reinterpret_cast<std::uint8_t *>(guest_entry);
        if (sha256(target, leaf_size) != leaf_sha) throw std::runtime_error("Loaded leaf differs from disk profile");
        initialize(image);
        hook_tests();
        // Seven bytes cover the first two complete instructions. Every old byte
        // remains available in the private original-copy reference reservation.
        std::array<std::uint8_t, 7> patch{0xe9, 0, 0, 0, 0, 0x90, 0x90};
        const auto delta = reinterpret_cast<std::uint32_t>(&mw34_hook_entry) - static_cast<std::uint32_t>(guest_entry + 5);
        std::memcpy(patch.data() + 1, &delta, 4);
        DWORD old{};
        if (!VirtualProtect(target, patch.size(), PAGE_EXECUTE_READWRITE, &old)) throw std::runtime_error("Patch protection failed");
        std::memcpy(target, patch.data(), patch.size());
        DWORD ignored{};
        if (!VirtualProtect(target, patch.size(), old, &ignored) || !FlushInstructionCache(GetCurrentProcess(), target, patch.size()))
            throw std::runtime_error("Patch protection restore failed");
        char line[256];
        std::snprintf(line, sizeof(line), "{\"event\":\"installed\",\"pid\":%lu,\"entry_va\":4234960,\"hook_va\":%u,\"patched_bytes\":7,\"on_disk_game_unchanged\":true}\n",
            GetCurrentProcessId(), reinterpret_cast<std::uint32_t>(&mw34_hook_entry));
        log_line(line);
        in_game = true;
        return 0;
    } catch (const std::exception &e) { OutputDebugStringA(e.what()); return 90; }
}
BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) { return TRUE; }
