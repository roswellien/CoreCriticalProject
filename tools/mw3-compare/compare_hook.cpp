// Original-side comparison hook (Win32, injected at the game entry into the 1998-runtime research copy made by
// prepare_runtime.py). It gives the original process the replay environment of the native host's scripted runs
// (tools/m4-crt-heap-carry, MW34_INPUT_SCRIPT + MW34_VIRTUAL_CLOCK) and writes the same per-frame scene fingerprint
// (MW34_DRAW_LOG), so the two logs can be compared line by line. Every rule below mirrors a native service:
// - virtual clock: starts at 1,000,000 us; each GetTickCount/timeGetTime/QueryPerformanceCounter/system-time query
//   adds 1 us; Sleep adds its duration without sleeping; each present adds the frame step;
//   QueryPerformanceFrequency is 1,000,000; rdtsc (three sites in Mech3.exe) is clock_us * 3000;
// - presents: Flip, and Blt/BltFast to a primary surface without an attached back buffer (frame counter, log line);
// - scripted DirectInput: GetDeviceState (keyboard 256 / mouse 16 bytes) and GetDeviceData (keyboard) from the
//   script with the native cursors; Poll returns DI_OK without the device;
// - DirectSound buffers: virtual play/write positions and playing status from the clock;
// - PeekMessageA/GetMessageA drop desktop messages (0x0060, mouse move/hover/leave, 0x031F); the cursor is virtual.
// Only imports of the guest modules (Mech3.exe, Mech3Msg.dll, MFC42, MSVCP50, MSVCRZ, IFORCE2) are redirected; system
// DLLs keep real services, as in the native host. Research tool; no gameplay change is intended.
#include <windows.h>
#include <mmsystem.h>
#include <ddraw.h>
#include <d3d.h>
#include <dinput.h>
#include <dsound.h>
#include <vfw.h>
#include <cctype>
#include <array>
#include <intrin.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace {
std::uint64_t clock_us = 1000000, step_us = 0;
unsigned frames = 0;
std::uint64_t scene_t0 = 0;
FILE *draw_log = nullptr, *diag = nullptr;
std::uint64_t draw_hash = 0xcbf29ce484222325ULL;
unsigned draw_calls = 0;
void fold(const void *p, std::size_t n) {
    const auto *b = static_cast<const unsigned char *>(p);
    for (std::size_t i = 0; i < n; ++i) { draw_hash ^= b[i]; draw_hash *= 0x100000001b3ULL; }
}
std::uint64_t query() { return ++clock_us; }

struct Event { bool timed, mouse, down; unsigned frame, scan; int dx, dy; unsigned buttons; };
std::vector<Event> script;
std::size_t mouse_at = 0, kstate_at = 0, key_at = 0;
unsigned buttons = 0, seq = 0;
std::array<unsigned char, 256> keys{};
POINT vcursor{320, 240};
bool due(const Event &e) {
    if (!e.timed) return e.frame <= frames;
    return scene_t0 && clock_us / 1000 - scene_t0 >= e.frame;
}

char shot_dir[1024]{};
unsigned shot_every = 25, shot_from = 0, shot_to = ~0u;
void screenshot() {  // MW34_COMPARE_SHOTS=<dir>: the game window every 25 presents (diagnostic only)
    HWND w = FindWindowA("Mech3Class", nullptr);
    if (!w || !shot_dir[0]) return;
    RECT r{}; GetClientRect(w, &r);
    const int cw = r.right, ch = r.bottom;
    if (cw <= 0 || ch <= 0) return;
    HDC wdc = GetDC(w), mdc = CreateCompatibleDC(wdc);
    BITMAPINFO bi{}; bi.bmiHeader = {sizeof(BITMAPINFOHEADER), cw, -ch, 1, 24, BI_RGB};
    void *bits{}; HBITMAP bmp = CreateDIBSection(wdc, &bi, DIB_RGB_COLORS, &bits, nullptr, 0);
    HGDIOBJ old = SelectObject(mdc, bmp);
    PrintWindow(w, mdc, PW_CLIENTONLY | 2 /* PW_RENDERFULLCONTENT */);
    char path[1200]; std::snprintf(path, sizeof path, "%s\\frame-%04u.bmp", shot_dir, frames);
    if (FILE *f = std::fopen(path, "wb")) {
        const DWORD stride = (DWORD(cw) * 3 + 3) & ~3u, size = stride * DWORD(ch);
        BITMAPFILEHEADER fh{0x4d42, DWORD(sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER) + size), 0, 0, DWORD(sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER))};
        std::fwrite(&fh, sizeof fh, 1, f); std::fwrite(&bi.bmiHeader, sizeof bi.bmiHeader, 1, f); std::fwrite(bits, size, 1, f); std::fclose(f);
    }
    SelectObject(mdc, old); DeleteObject(bmp); DeleteDC(mdc); ReleaseDC(w, wdc);
    if (diag) { std::fprintf(diag, "frame %u foreground %d active-window %p game %p\n", frames, GetForegroundWindow() == w, static_cast<void *>(GetForegroundWindow()), static_cast<void *>(w)); std::fflush(diag); }
}
unsigned frame_budget = 0, polls_mouse = 0, polls_keys = 0, dp_raw = 0, scenes = 0;
unsigned mem_dump_frame = 0;
char mem_dump_path[1024]{};
void present() {
    ++frames;
    if (mem_dump_frame && frames == mem_dump_frame && mem_dump_path[0])  // diagnostic: game .data/.bss image at that frame
        if (FILE *f = std::fopen(mem_dump_path, "wb")) { std::fwrite(reinterpret_cast<const void *>(0x5e0000), 1, 0x9a2000 - 0x5e0000, f); std::fclose(f); }
    if (frames == 1 || frames % 25 == 0) {  // the game pauses input while inactive; the native run window is active
        if (HWND w = FindWindowA("Mech3Class", nullptr); w && GetForegroundWindow() != w) {
            const BOOL ok = SetForegroundWindow(w);
            if (diag) { std::fprintf(diag, "frame %u SetForegroundWindow %d now-foreground %d\n", frames, ok, GetForegroundWindow() == w); std::fflush(diag); }
        }
    }
    if (diag && frames % 25 == 0) { std::fprintf(diag, "frame %u clock %llu scene_t0 %llu polls m%u k%u draws %u scenes %u\n", frames, static_cast<unsigned long long>(clock_us), static_cast<unsigned long long>(scene_t0), polls_mouse, polls_keys, dp_raw, scenes); std::fflush(diag); }
    if (draw_log) {
        std::fprintf(draw_log, "%u %u %016llx\n", frames, draw_calls, static_cast<unsigned long long>(draw_hash));
        draw_hash = 0xcbf29ce484222325ULL; draw_calls = 0;
    }
    clock_us += step_us;
    if (frame_budget && frames >= frame_budget) {  // the native host's presentation frame budget
        if (draw_log) std::fflush(draw_log);
        if (diag) { std::fprintf(diag, "frame budget %u reached\n", frame_budget); std::fflush(diag); }
        TerminateProcess(GetCurrentProcess(), 0);
    }
}

// ---- clock and system services
DWORD WINAPI h_GetTickCount() { return static_cast<DWORD>(query() / 1000); }
DWORD WINAPI h_timeGetTime() { return static_cast<DWORD>(query() / 1000); }
BOOL WINAPI h_QPC(LARGE_INTEGER *v) { v->QuadPart = static_cast<LONGLONG>(query()); return TRUE; }
BOOL WINAPI h_QPF(LARGE_INTEGER *v) { v->QuadPart = 1000000; return TRUE; }
VOID WINAPI h_Sleep(DWORD ms) { clock_us += std::uint64_t(ms) * 1000; }
FILETIME vfile() { const std::uint64_t ft = 125911584000000000ULL + query() * 10; return FILETIME{DWORD(ft), DWORD(ft >> 32)}; }
VOID WINAPI h_GetSystemTime(SYSTEMTIME *t) { const FILETIME f = vfile(); FileTimeToSystemTime(&f, t); }
VOID WINAPI h_GetLocalTime(SYSTEMTIME *t) { const FILETIME f = vfile(); FileTimeToSystemTime(&f, t); }
VOID WINAPI h_GetSystemTimeAsFileTime(FILETIME *t) { *t = vfile(); }
bool drop(UINT m) {
    return m == 0x0060 || m == WM_MOUSEMOVE || m == WM_NCMOUSEMOVE || m == WM_MOUSEHOVER || m == WM_MOUSELEAVE ||
           m == WM_NCMOUSELEAVE || m == 0x031F;
}
BOOL WINAPI h_PeekMessageA(MSG *m, HWND w, UINT lo, UINT hi, UINT flags) {
    for (;;) {
        const BOOL r = PeekMessageA(m, w, lo, hi, flags);
        if (!(r && drop(m->message))) return r;
        if (!(flags & PM_REMOVE)) { MSG x{}; PeekMessageA(&x, m->hwnd, m->message, m->message, PM_REMOVE); }
    }
}
BOOL WINAPI h_GetMessageA(MSG *m, HWND w, UINT lo, UINT hi) {
    for (;;) {
        const BOOL r = GetMessageA(m, w, lo, hi);
        if (!(r && r != -1 && drop(m->message))) return r;
    }
}
BOOL WINAPI h_SetCursorPos(int x, int y) { vcursor = {x, y}; return TRUE; }
BOOL WINAPI h_GetCursorPos(POINT *p) { *p = vcursor; return TRUE; }

// ---- registry: the native host's overlay (MW34_REG_OVERLAY, a copy of MW3/mw34-registry.txt) is read first; values not
// in it come from the real registry. Writes by the game go to the in-memory overlay only; the real registry is never written.
std::map<std::string, std::map<std::string, std::pair<DWORD, std::vector<unsigned char>>>> overlay;
std::map<HKEY, std::string> key_path;
unsigned fake_serial = 0;
std::string lower(std::string s) { for (auto &c : s) c = char(std::tolower(static_cast<unsigned char>(c))); return s; }
std::string path_of(HKEY parent, const char *sub) {
    std::string base;
    if (parent == HKEY_CURRENT_USER) base = "hkcu";
    else if (parent == HKEY_LOCAL_MACHINE) base = "hklm";
    else if (auto it = key_path.find(parent); it != key_path.end()) base = it->second;
    else return {};
    return sub && *sub ? base + "\\" + lower(sub) : base;
}
bool overlay_owned(const std::string &p) { return p.rfind("hkcu\\software\\microprose", 0) == 0 || overlay.count(p); }
void load_overlay(const char *file) {
    std::ifstream f(file);
    for (std::string line; std::getline(f, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.size() < 3 || line[0] != 'V') continue;
        std::istringstream l(line.substr(2));
        std::string path, name, type, hex;
        if (!std::getline(l, path, '\t') || !std::getline(l, name, '\t') || !std::getline(l, type, '\t')) continue;
        std::getline(l, hex, '\t');
        std::vector<unsigned char> bytes;
        for (std::size_t i = 0; i + 1 < hex.size(); i += 2) bytes.push_back(static_cast<unsigned char>(std::stoul(hex.substr(i, 2), nullptr, 16)));
        overlay[path][name] = {DWORD(std::stoul(type)), bytes};
    }
}
LONG WINAPI h_RegOpenKeyExA(HKEY parent, LPCSTR sub, DWORD opt, REGSAM sam, PHKEY out) {
    const std::string p = path_of(parent, sub);
    LONG r = RegOpenKeyExA(parent, sub, opt, sam, out);
    if (r != ERROR_SUCCESS && !p.empty() && overlay.count(p)) { *out = reinterpret_cast<HKEY>(std::uintptr_t(0x7e000000 + 16 * ++fake_serial)); r = ERROR_SUCCESS; }
    if (r == ERROR_SUCCESS && !p.empty()) key_path[*out] = p;
    return r;
}
LONG WINAPI h_RegCreateKeyExA(HKEY parent, LPCSTR sub, DWORD, LPSTR, DWORD opt, REGSAM sam, LPSECURITY_ATTRIBUTES, PHKEY out, LPDWORD disp) {
    // Opened, never created: a missing key becomes an overlay-only key.
    const std::string p = path_of(parent, sub);
    LONG r = RegOpenKeyExA(parent, sub, opt, sam, out);
    if (disp) *disp = REG_OPENED_EXISTING_KEY;
    if (r != ERROR_SUCCESS && !p.empty()) { *out = reinterpret_cast<HKEY>(std::uintptr_t(0x7e000000 + 16 * ++fake_serial)); r = ERROR_SUCCESS; if (disp) *disp = REG_CREATED_NEW_KEY; }
    if (r == ERROR_SUCCESS && !p.empty()) key_path[*out] = p;
    if (diag) { std::fprintf(diag, "RegCreateKeyExA %s -> %ld\n", p.c_str(), r); std::fflush(diag); }
    return r;
}
bool fake_key(HKEY h) { const auto v = std::uintptr_t(h); return v >= 0x7e000000 && v < 0x7f000000; }
LONG WINAPI h_RegQueryValueExA(HKEY h, LPCSTR name, LPDWORD res, LPDWORD type, LPBYTE data, LPDWORD cb) {
    if (auto it = key_path.find(h); it != key_path.end()) {
        auto k = overlay.find(it->second);
        if (k != overlay.end()) {
            auto v = k->second.find(lower(name ? name : ""));
            if (v != k->second.end()) {
                const DWORD need = DWORD(v->second.second.size());
                if (type) *type = v->second.first;
                LONG r = ERROR_SUCCESS;
                if (data && cb && *cb < need) r = ERROR_MORE_DATA;
                else if (data && need) std::memcpy(data, v->second.second.data(), need);
                if (cb) *cb = need;
                return r;
            }
        }
    }
    if (fake_key(h)) return ERROR_FILE_NOT_FOUND;
    return RegQueryValueExA(h, name, res, type, data, cb);
}
LONG WINAPI h_RegSetValueExA(HKEY h, LPCSTR name, DWORD, DWORD type, const BYTE *data, DWORD cb) {
    if (auto it = key_path.find(h); it != key_path.end() && overlay_owned(it->second)) {
        overlay[it->second][lower(name ? name : "")] = {type, std::vector<unsigned char>(data, data + cb)};
        return ERROR_SUCCESS;
    }
    if (diag) { std::fprintf(diag, "RegSetValueExA outside the overlay refused\n"); std::fflush(diag); }
    return ERROR_ACCESS_DENIED;
}
LONG WINAPI h_RegCloseKey(HKEY h) {
    key_path.erase(h);
    if (fake_key(h)) return ERROR_SUCCESS;
    return RegCloseKey(h);
}
// MW34_STAGED_CODEC=0 (the native harness setting): the native host then has no IV50 decoder (its fallback is the x64
// system ICLocate, which finds none), so the intro decode fails; the original side mirrors that.
using ICLocate_t = HIC(WINAPI *)(DWORD, DWORD, LPBITMAPINFOHEADER, LPBITMAPINFOHEADER, WORD);
ICLocate_t o_ICLocate{};
bool no_codec = false;
HIC WINAPI h_ICLocate(DWORD type, DWORD handler, LPBITMAPINFOHEADER in, LPBITMAPINFOHEADER out, WORD flags) {
    if (no_codec) return nullptr;
    return o_ICLocate(type, handler, in, out, flags);
}

// Guest threads run to completion inside CreateThread, as in the native host (its guest threads run to completion at
// creation, on their own stacks). The creator waits for the real thread, dispatching only cross-thread sent messages so a
// worker's SendMessage to the main window cannot deadlock. Suspended creation is not modelled natively either.
HANDLE WINAPI h_CreateThread(LPSECURITY_ATTRIBUTES sa, SIZE_T ss, LPTHREAD_START_ROUTINE start, LPVOID p, DWORD fl, LPDWORD id) {
    HANDLE h = CreateThread(sa, ss, start, p, fl, id);
    if (diag) { std::fprintf(diag, "CreateThread start %p flags %lx at frame %u\n", reinterpret_cast<void *>(start), fl, frames); std::fflush(diag); }
    if (!h || (fl & CREATE_SUSPENDED)) return h;
    for (;;) {
        const DWORD r = MsgWaitForMultipleObjects(1, &h, FALSE, INFINITE, QS_SENDMESSAGE);
        if (r == WAIT_OBJECT_0) break;
        MSG m;
        PeekMessageA(&m, nullptr, 0, 0, PM_NOREMOVE | PM_QS_SENDMESSAGE);
    }
    return h;
}

// MW34_HEAP_FILL=<byte> (diagnostic): new non-zeroed heap blocks of the guest modules are filled with that byte, to
// expose reads of uninitialized heap memory (behaviour that would depend on the heap's prior contents).
int heap_fill = -1;
LPVOID WINAPI h_HeapAlloc(HANDLE h, DWORD flags, SIZE_T n) {
    LPVOID p = HeapAlloc(h, flags, n);
    if (p && heap_fill >= 0 && !(flags & HEAP_ZERO_MEMORY)) std::memset(p, heap_fill, n);
    return p;
}

// ---- vtable patching (slots from the SDK declaration order). Each patched table keeps its own originals, so several
// implementations of one interface (e.g. IDirectDraw and IDirectDraw4 objects) are all hooked.
std::map<std::pair<void **, unsigned>, void *> originals;
template <class F> F orig(void *object, unsigned slot) {
    return reinterpret_cast<F>(originals.at({*static_cast<void ***>(object), slot}));
}
void patch_slot(void *object, unsigned slot, void *hook, void **) {
    void **table = *static_cast<void ***>(object);
    if (table[slot] == hook) return;
    originals[{table, slot}] = table[slot];
    DWORD old{};
    VirtualProtect(&table[slot], sizeof(void *), PAGE_EXECUTE_READWRITE, &old);
    table[slot] = hook;
    VirtualProtect(&table[slot], sizeof(void *), old, &old);
    if (diag) { std::fprintf(diag, "hooked table %p slot %u\n", static_cast<void *>(table), slot); std::fflush(diag); }
}

// ---- DirectInput
using CreateDeviceA_t = HRESULT(WINAPI *)(IDirectInputA *, REFGUID, LPDIRECTINPUTDEVICEA *, LPUNKNOWN);
using SetDataFormat_t = HRESULT(WINAPI *)(IDirectInputDeviceA *, LPCDIDATAFORMAT);
using GetDeviceState_t = HRESULT(WINAPI *)(IDirectInputDeviceA *, DWORD, LPVOID);
using GetDeviceData_t = HRESULT(WINAPI *)(IDirectInputDeviceA *, DWORD, LPDIDEVICEOBJECTDATA, LPDWORD, DWORD);
using Poll_t = HRESULT(WINAPI *)(IDirectInputDevice2A *);
using DIQI_t = HRESULT(WINAPI *)(IDirectInputDeviceA *, REFIID, void **);
CreateDeviceA_t o_CreateDevice{}; SetDataFormat_t o_SetDataFormat{}; GetDeviceState_t o_GetDeviceState{};
GetDeviceData_t o_GetDeviceData{}; Poll_t o_Poll{}; DIQI_t o_DIQI{};
std::map<void *, DWORD> di_format;
HRESULT WINAPI h_SetDataFormat(IDirectInputDeviceA *d, LPCDIDATAFORMAT f) {
    const HRESULT hr = orig<SetDataFormat_t>(d, 11)(d, f);
    if (SUCCEEDED(hr)) di_format[d] = f->dwDataSize;
    if (diag) { std::fprintf(diag, "SetDataFormat %p size %lu hr %lx\n", static_cast<void *>(d), f->dwDataSize, hr); std::fflush(diag); }
    return hr;
}
HRESULT WINAPI h_GetDeviceState(IDirectInputDeviceA *, DWORD z, LPVOID a) {
    auto *out = static_cast<unsigned char *>(a);
    std::memset(out, 0, z);
    if (z == 16) ++polls_mouse; else if (z == 256) ++polls_keys;
    if (z == 16) {
        int dx = 0, dy = 0;
        while (mouse_at < script.size() && (!script[mouse_at].mouse || due(script[mouse_at]))) {
            const auto &e = script[mouse_at++];
            if (e.mouse) { dx += e.dx; dy += e.dy; buttons = e.buttons; }
        }
        std::memcpy(out, &dx, 4); std::memcpy(out + 4, &dy, 4);
        for (unsigned b = 0; b < 4; ++b) out[12 + b] = (buttons >> b) & 1 ? 0x80 : 0;
    } else if (z == 256) {
        while (kstate_at < script.size() && (script[kstate_at].mouse || due(script[kstate_at]))) {
            const auto &e = script[kstate_at++];
            if (!e.mouse) keys[e.scan & 255] = e.down ? 0x80 : 0;
        }
        std::memcpy(out, keys.data(), 256);
    } else if (diag) std::fprintf(diag, "GetDeviceState size %lu outside the scripted model\n", z);
    return DI_OK;
}
HRESULT WINAPI h_GetDeviceData(IDirectInputDeviceA *, DWORD z, LPDIDEVICEOBJECTDATA a, LPDWORD pn, DWORD fl) {
    if (z != 16 && diag) std::fprintf(diag, "GetDeviceData record size %lu\n", z);
    const DWORD cnt = *pn;
    DWORD k = 0;
    std::size_t at = key_at;
    while (at < script.size() && k < cnt) {
        const auto &e = script[at];
        if (e.mouse) { ++at; continue; }
        if (!due(e)) break;
        if (a) {
            a[k].dwOfs = e.scan; a[k].dwData = e.down ? 0x80U : 0U;
            a[k].dwTimeStamp = static_cast<DWORD>(query() / 1000); a[k].dwSequence = ++seq;
        }
        ++k; ++at;
    }
    if (!(fl & DIGDD_PEEK)) key_at = at;
    *pn = k;
    return DI_OK;
}
HRESULT WINAPI h_Poll(IDirectInputDevice2A *d) {
    if (di_format.count(d)) return DI_OK;
    return orig<Poll_t>(d, 25)(d);
}
void hook_device(void *d) {
    patch_slot(d, 11, reinterpret_cast<void *>(&h_SetDataFormat), reinterpret_cast<void **>(&o_SetDataFormat));
    patch_slot(d, 9, reinterpret_cast<void *>(&h_GetDeviceState), reinterpret_cast<void **>(&o_GetDeviceState));
    patch_slot(d, 10, reinterpret_cast<void *>(&h_GetDeviceData), reinterpret_cast<void **>(&o_GetDeviceData));
}
HRESULT WINAPI h_DIQI(IDirectInputDeviceA *d, REFIID riid, void **out) {
    const HRESULT hr = orig<DIQI_t>(d, 0)(d, riid, out);
    if (SUCCEEDED(hr) && *out && IsEqualGUID(riid, IID_IDirectInputDevice2A)) {
        hook_device(*out);
        patch_slot(*out, 25, reinterpret_cast<void *>(&h_Poll), reinterpret_cast<void **>(&o_Poll));
        if (*out != d && di_format.count(d)) di_format[*out] = di_format[d];
    }
    return hr;
}
HRESULT WINAPI h_CreateDevice(IDirectInputA *di, REFGUID g, LPDIRECTINPUTDEVICEA *out, LPUNKNOWN u) {
    const HRESULT hr = orig<CreateDeviceA_t>(di, 3)(di, g, out, u);
    if (SUCCEEDED(hr) && *out) {
        hook_device(*out);
        patch_slot(*out, 0, reinterpret_cast<void *>(&h_DIQI), reinterpret_cast<void **>(&o_DIQI));
    }
    return hr;
}
using DirectInputCreateA_t = HRESULT(WINAPI *)(HINSTANCE, DWORD, LPDIRECTINPUTA *, LPUNKNOWN);
DirectInputCreateA_t o_DirectInputCreateA{};
HRESULT WINAPI h_DirectInputCreateA(HINSTANCE h, DWORD v, LPDIRECTINPUTA *out, LPUNKNOWN u) {
    const HRESULT hr = o_DirectInputCreateA(h, v, out, u);
    if (SUCCEEDED(hr) && *out) patch_slot(*out, 3, reinterpret_cast<void *>(&h_CreateDevice), reinterpret_cast<void **>(&o_CreateDevice));
    return hr;
}

// ---- DirectSound
struct VSound { unsigned size = 0, rate = 0, pos0 = 0; std::uint64_t t0 = 0; bool playing = false, looping = false; };
std::map<void *, VSound> vsound;
using DSB = IDirectSoundBuffer;
using Play_t = HRESULT(WINAPI *)(DSB *, DWORD, DWORD, DWORD);
using Stop_t = HRESULT(WINAPI *)(DSB *);
using SetPos_t = HRESULT(WINAPI *)(DSB *, DWORD);
using SetFreq_t = HRESULT(WINAPI *)(DSB *, DWORD);
using GetPos_t = HRESULT(WINAPI *)(DSB *, LPDWORD, LPDWORD);
using GetStatus_t = HRESULT(WINAPI *)(DSB *, LPDWORD);
Play_t o_Play{}; Stop_t o_Stop{}; SetPos_t o_SetPos{}; SetFreq_t o_SetFreq{}; GetPos_t o_GetPos{}; GetStatus_t o_GetStatus{};
VSound &vs(DSB *b) {
    auto &v = vsound[b];
    if (!v.size) {
        DSBCAPS c{sizeof c}; WAVEFORMATEX f{};
        if (SUCCEEDED(b->GetCaps(&c))) v.size = c.dwBufferBytes;
        if (SUCCEEDED(b->GetFormat(&f, sizeof f, nullptr))) v.rate = f.nAvgBytesPerSec;
        if (!v.size) v.size = 1;
    }
    return v;
}
unsigned vpos(VSound &v) {
    if (!v.playing) return v.pos0;
    const std::uint64_t moved = (clock_us - v.t0) * v.rate / 1000000ULL, p = v.pos0 + moved;
    if (v.looping) return unsigned(p % v.size);
    if (p >= v.size) { v.playing = false; v.pos0 = 0; return 0; }
    return unsigned(p);
}
HRESULT WINAPI h_Play(DSB *b, DWORD r, DWORD p, DWORD f) {
    auto &v = vs(b); v.pos0 = vpos(v); v.t0 = clock_us; v.playing = true; v.looping = (f & DSBPLAY_LOOPING) != 0;
    return orig<Play_t>(b, 12)(b, r, p, f);
}
HRESULT WINAPI h_Stop(DSB *b) { auto &v = vs(b); v.pos0 = vpos(v); v.playing = false; return orig<Stop_t>(b, 18)(b); }
HRESULT WINAPI h_SetPos(DSB *b, DWORD p) { auto &v = vs(b); v.pos0 = p % v.size; v.t0 = clock_us; return orig<SetPos_t>(b, 13)(b, p); }
HRESULT WINAPI h_SetFreq(DSB *b, DWORD hz) {
    auto &v = vs(b); v.pos0 = vpos(v); v.t0 = clock_us;
    WAVEFORMATEX f{};
    if (SUCCEEDED(b->GetFormat(&f, sizeof f, nullptr))) v.rate = (hz ? hz : f.nSamplesPerSec) * f.nBlockAlign;
    return orig<SetFreq_t>(b, 17)(b, hz);
}
HRESULT WINAPI h_GetPos(DSB *b, LPDWORD play, LPDWORD write) {
    auto &v = vs(b); const unsigned pl = vpos(v), wp = (pl + v.rate / 100) % v.size;
    if (play) *play = pl;
    if (write) *write = wp;
    return DS_OK;
}
HRESULT WINAPI h_GetStatus(DSB *b, LPDWORD st) {
    DWORD s{}; const HRESULT hr = orig<GetStatus_t>(b, 9)(b, &s);
    auto &v = vs(b); (void)vpos(v);
    s &= ~DWORD(DSBSTATUS_PLAYING | DSBSTATUS_LOOPING);
    if (v.playing) s |= DSBSTATUS_PLAYING | (v.looping ? DSBSTATUS_LOOPING : 0);
    *st = s;
    return hr;
}
void hook_buffer(void *b) {
    patch_slot(b, 12, reinterpret_cast<void *>(&h_Play), reinterpret_cast<void **>(&o_Play));
    patch_slot(b, 18, reinterpret_cast<void *>(&h_Stop), reinterpret_cast<void **>(&o_Stop));
    patch_slot(b, 13, reinterpret_cast<void *>(&h_SetPos), reinterpret_cast<void **>(&o_SetPos));
    patch_slot(b, 17, reinterpret_cast<void *>(&h_SetFreq), reinterpret_cast<void **>(&o_SetFreq));
    patch_slot(b, 4, reinterpret_cast<void *>(&h_GetPos), reinterpret_cast<void **>(&o_GetPos));
    patch_slot(b, 9, reinterpret_cast<void *>(&h_GetStatus), reinterpret_cast<void **>(&o_GetStatus));
}
using CreateSB_t = HRESULT(WINAPI *)(IDirectSound *, LPCDSBUFFERDESC, LPDIRECTSOUNDBUFFER *, LPUNKNOWN);
using DupSB_t = HRESULT(WINAPI *)(IDirectSound *, LPDIRECTSOUNDBUFFER, LPDIRECTSOUNDBUFFER *);
CreateSB_t o_CreateSB{}; DupSB_t o_DupSB{};
HRESULT WINAPI h_CreateSB(IDirectSound *ds, LPCDSBUFFERDESC d, LPDIRECTSOUNDBUFFER *out, LPUNKNOWN u) {
    const HRESULT hr = orig<CreateSB_t>(ds, 3)(ds, d, out, u);
    if (SUCCEEDED(hr) && *out) hook_buffer(*out);
    return hr;
}
HRESULT WINAPI h_DupSB(IDirectSound *ds, LPDIRECTSOUNDBUFFER s, LPDIRECTSOUNDBUFFER *out) {
    const HRESULT hr = orig<DupSB_t>(ds, 5)(ds, s, out);
    if (SUCCEEDED(hr) && *out) hook_buffer(*out);
    return hr;
}
using DirectSoundCreate_t = HRESULT(WINAPI *)(LPGUID, LPDIRECTSOUND *, LPUNKNOWN);
DirectSoundCreate_t o_DirectSoundCreate{};
HRESULT WINAPI h_DirectSoundCreate(LPGUID g, LPDIRECTSOUND *out, LPUNKNOWN u) {
    const HRESULT hr = o_DirectSoundCreate(g, out, u);
    if (SUCCEEDED(hr) && *out) {
        patch_slot(*out, 3, reinterpret_cast<void *>(&h_CreateSB), reinterpret_cast<void **>(&o_CreateSB));
        patch_slot(*out, 5, reinterpret_cast<void *>(&h_DupSB), reinterpret_cast<void **>(&o_DupSB));
    }
    return hr;
}

// ---- DirectDraw / Direct3D: presents and the scene fingerprint
std::map<void *, bool> primary_has_back;  // primary surfaces: whether a back buffer is attached
using Flip_t = HRESULT(WINAPI *)(void *, void *, DWORD);
using Blt_t = HRESULT(WINAPI *)(void *, LPRECT, void *, LPRECT, DWORD, LPDDBLTFX);
using BltFast_t = HRESULT(WINAPI *)(void *, DWORD, DWORD, void *, LPRECT, DWORD);
Flip_t o_Flip[2]{}; Blt_t o_Blt[2]{}; BltFast_t o_BltFast[2]{};
// MW34_COMPARE_SHOTS=<dir>: the back buffer about to be flipped, every 25 presents, as PPM (RGB565 or 32-bit sources).
template <int V> void dump_back(void *primary) {
    if (!shot_dir[0] || (frames + 1) % shot_every || frames + 1 < shot_from || frames + 1 > shot_to) return;
    using GetAttached_t = HRESULT(WINAPI *)(void *, void *, void **);
    using Lock_t = HRESULT(WINAPI *)(void *, LPRECT, void *, DWORD, HANDLE);
    using Unlock_t = HRESULT(WINAPI *)(void *, void *);
    void **table = *static_cast<void ***>(primary);
    void *back{};
    DDSCAPS2 caps{}; caps.dwCaps = DDSCAPS_BACKBUFFER;
    if (FAILED(reinterpret_cast<GetAttached_t>(table[12])(primary, &caps, &back)) || !back) return;
    void **bt = *static_cast<void ***>(back);
    DDSURFACEDESC2 d2{}; DDSURFACEDESC d1{};
    void *desc = V ? static_cast<void *>(&d2) : static_cast<void *>(&d1);
    d2.dwSize = sizeof d2; d1.dwSize = sizeof d1;
    if (SUCCEEDED(reinterpret_cast<Lock_t>(bt[25])(back, nullptr, desc, DDLOCK_WAIT | DDLOCK_READONLY, nullptr))) {
        const unsigned w = V ? d2.dwWidth : d1.dwWidth, h = V ? d2.dwHeight : d1.dwHeight;
        const LONG pitch = V ? d2.lPitch : d1.lPitch;
        const DWORD bpp = V ? d2.ddpfPixelFormat.dwRGBBitCount : d1.ddpfPixelFormat.dwRGBBitCount;
        const auto *src = static_cast<const unsigned char *>(V ? d2.lpSurface : d1.lpSurface);
        char path[1200]; std::snprintf(path, sizeof path, "%s\\frame-%04u.ppm", shot_dir, frames + 1);
        if (FILE *f = std::fopen(path, "wb")) {
            std::fprintf(f, "P6\n%u %u\n255\n", w, h);
            std::vector<unsigned char> row(3 * std::size_t(w));
            for (unsigned y = 0; y < h; ++y) {
                const unsigned char *r = src + std::ptrdiff_t(y) * pitch;
                for (unsigned x = 0; x < w; ++x) {
                    unsigned char *o = &row[3 * std::size_t(x)];
                    if (bpp == 16) { const unsigned p = r[2 * x] | r[2 * x + 1] << 8; o[0] = ((p >> 11) & 31) * 255 / 31; o[1] = ((p >> 5) & 63) * 255 / 63; o[2] = (p & 31) * 255 / 31; }
                    else { o[0] = r[4 * x + 2]; o[1] = r[4 * x + 1]; o[2] = r[4 * x]; }
                }
                std::fwrite(row.data(), row.size(), 1, f);
            }
            std::fclose(f);
        }
        reinterpret_cast<Unlock_t>(bt[32])(back, nullptr);
    }
    reinterpret_cast<HRESULT(WINAPI *)(void *)>(bt[2])(back);
}
template <int V> HRESULT WINAPI h_Flip(void *s, void *t, DWORD f) { dump_back<V>(s); const HRESULT hr = orig<Flip_t>(s, 11)(s, t, f); present(); return hr; }
bool lone_primary(void *s) { auto it = primary_has_back.find(s); return it != primary_has_back.end() && !it->second; }
template <int V> HRESULT WINAPI h_Blt(void *s, LPRECT d, void *src, LPRECT sr, DWORD f, LPDDBLTFX fx) {
    const HRESULT hr = orig<Blt_t>(s, 5)(s, d, src, sr, f, fx);
    if (lone_primary(s)) present();
    return hr;
}
template <int V> HRESULT WINAPI h_BltFast(void *s, DWORD x, DWORD y, void *src, LPRECT sr, DWORD f) {
    const HRESULT hr = orig<BltFast_t>(s, 7)(s, x, y, src, sr, f);
    if (lone_primary(s)) present();
    return hr;
}
template <int V> void hook_surface(void *s) {
    patch_slot(s, 11, reinterpret_cast<void *>(&h_Flip<V>), reinterpret_cast<void **>(&o_Flip[V]));
    patch_slot(s, 5, reinterpret_cast<void *>(&h_Blt<V>), reinterpret_cast<void **>(&o_Blt[V]));
    patch_slot(s, 7, reinterpret_cast<void *>(&h_BltFast<V>), reinterpret_cast<void **>(&o_BltFast[V]));
}
unsigned detail_frame = 0;
void callers(char *out, std::size_t size, void *ret, void *frame) {  // the caller and an EBP chain (diagnostic)
    int k = std::snprintf(out, size, " ret %p", ret);
    auto **f = static_cast<void **>(frame);
    for (int i = 0; i < 6 && f && k > 0 && std::size_t(k) < size; ++i) {
        MEMORY_BASIC_INFORMATION m{};
        if (!VirtualQuery(f, &m, sizeof m) || m.State != MEM_COMMIT || !(m.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE))) break;
        k += std::snprintf(out + k, size - k, " %p", f[1]);
        auto **next = static_cast<void **>(f[0]);
        if (next <= f) break;
        f = next;
    }
}
char caller_text[256]{};
void detail(unsigned type, unsigned n, unsigned ni, const void *v) {  // MW34_DRAW_DETAIL=<frame>, as the native host
    std::uint64_t h = 0xcbf29ce484222325ULL;
    const auto *b = static_cast<const unsigned char *>(v);
    for (std::size_t i = 0; i < 32 * std::size_t(n); ++i) { h ^= b[i]; h *= 0x100000001b3ULL; }
    float v0[8]{};
    if (n) std::memcpy(v0, v, 32);
    std::fprintf(draw_log, "  draw %u type %u n %u idx %u v0 %.2f %.2f %.4f tex %08x %016llx%s\n", draw_calls, type, n, ni, v0[0], v0[1], v0[2], 0u, static_cast<unsigned long long>(h), caller_text);
}
using DP_t = HRESULT(WINAPI *)(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, LPVOID, DWORD, DWORD);
using DIP_t = HRESULT(WINAPI *)(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, LPVOID, DWORD, LPWORD, DWORD, DWORD);
using EndScene_t = HRESULT(WINAPI *)(IDirect3DDevice3 *);
DP_t o_DP{}; DIP_t o_DIP{}; EndScene_t o_EndScene{};
HRESULT WINAPI h_DP(IDirect3DDevice3 *d, D3DPRIMITIVETYPE t, DWORD fvf, LPVOID v, DWORD n, DWORD f) {
    ++dp_raw;
    if (draw_log) {
        if (fvf != D3DFVF_TLVERTEX && diag) std::fprintf(diag, "DrawPrimitive fvf %lx\n", fvf);
        if (detail_frame == frames + 1) {
            // Stack words above the return address that point into Mech3.exe code just after a CALL (diagnostic).
            auto *sp = static_cast<unsigned *>(_AddressOfReturnAddress());
            int k = 0;
            for (int i = 0, found = 0; i < 400 && found < 10 && k < int(sizeof caller_text) - 12; ++i) {
                const unsigned w = sp[i];
                if (w < 0x401005 || w >= 0x5bb000) continue;
                const auto *c = reinterpret_cast<const unsigned char *>(w);
                if (c[-5] == 0xe8 || (c[-2] == 0xff && (c[-1] & 0x38) == 0x10) || (c[-3] == 0xff && (c[-2] & 0x38) == 0x10) || (c[-6] == 0xff && (c[-5] & 0x38) == 0x10)) {
                    k += std::snprintf(caller_text + k, sizeof caller_text - k, " %x", w); ++found;
                }
            }
            detail(unsigned(t), n, 0, v);
        }
        ++draw_calls; const unsigned type = unsigned(t), count = n; fold(&type, 4); fold(&count, 4); fold(v, 32 * std::size_t(n));
    }
    return orig<DP_t>(d, 28)(d, t, fvf, v, n, f);
}
HRESULT WINAPI h_DIP(IDirect3DDevice3 *d, D3DPRIMITIVETYPE t, DWORD fvf, LPVOID v, DWORD n, LPWORD idx, DWORD ni, DWORD f) {
    if (draw_log) {
        if (detail_frame == frames + 1) detail(unsigned(t), n, ni, v);
        ++draw_calls; const unsigned type = unsigned(t), count = n; fold(&type, 4); fold(&count, 4); fold(v, 32 * std::size_t(n));
        if (ni) fold(idx, 2 * std::size_t(ni));
    }
    return orig<DIP_t>(d, 29)(d, t, fvf, v, n, idx, ni, f);
}
HRESULT WINAPI h_EndScene(IDirect3DDevice3 *d) {
    ++scenes;
    if (!scene_t0) scene_t0 = (std::max)(clock_us / 1000, std::uint64_t(1));
    return orig<EndScene_t>(d, 10)(d);
}
// MW34_NATIVE_CAPS=1: report the native provider's capabilities, so provider differences do not enter the comparison.
// Texture formats: the native list (RGB565, ARGB1555, ARGB4444) in its order. Video memory: MW34_VIDMEM, the native
// answers in call order ("total/free,total/free,...", from the native service log); the last pair repeats.
bool native_caps = false;
std::vector<std::pair<DWORD, DWORD>> vidmem;
std::size_t vidmem_at = 0;
using EnumTexFmt_t = HRESULT(WINAPI *)(IDirect3DDevice3 *, LPD3DENUMPIXELFORMATSCALLBACK, LPVOID);
HRESULT WINAPI h_EnumTexFmt(IDirect3DDevice3 *d, LPD3DENUMPIXELFORMATSCALLBACK cb, LPVOID ctx) {
    if (!native_caps) return orig<EnumTexFmt_t>(d, 8)(d, cb, ctx);
    const DDPIXELFORMAT formats[3] = {
        {sizeof(DDPIXELFORMAT), DDPF_RGB, 0, {16}, {0xf800}, {0x07e0}, {0x001f}, {0}},
        {sizeof(DDPIXELFORMAT), DDPF_RGB | DDPF_ALPHAPIXELS, 0, {16}, {0x7c00}, {0x03e0}, {0x001f}, {0x8000}},
        {sizeof(DDPIXELFORMAT), DDPF_RGB | DDPF_ALPHAPIXELS, 0, {16}, {0x0f00}, {0x00f0}, {0x000f}, {0xf000}}};
    for (const auto &f : formats) {
        DDPIXELFORMAT copy = f;
        if (cb(&copy, ctx) == D3DENUMRET_CANCEL) break;
    }
    return D3D_OK;
}
using VidMem_t = HRESULT(WINAPI *)(void *, void *, LPDWORD, LPDWORD);
HRESULT WINAPI h_VidMem(void *dd, void *caps, LPDWORD total, LPDWORD free) {
    if (!native_caps || vidmem.empty()) return orig<VidMem_t>(dd, 23)(dd, caps, total, free);
    const auto v = vidmem[(std::min)(vidmem_at++, vidmem.size() - 1)];
    if (total) *total = v.first;
    if (free) *free = v.second;
    return DD_OK;
}
using CreateD3DDevice_t = HRESULT(WINAPI *)(IDirect3D3 *, REFCLSID, LPDIRECTDRAWSURFACE4, LPDIRECT3DDEVICE3 *, LPUNKNOWN);
CreateD3DDevice_t o_CreateD3DDevice{};
HRESULT WINAPI h_CreateD3DDevice(IDirect3D3 *d3, REFCLSID c, LPDIRECTDRAWSURFACE4 s, LPDIRECT3DDEVICE3 *out, LPUNKNOWN u) {
    const HRESULT hr = orig<CreateD3DDevice_t>(d3, 8)(d3, c, s, out, u);
    if (SUCCEEDED(hr) && *out) {
        patch_slot(*out, 28, reinterpret_cast<void *>(&h_DP), reinterpret_cast<void **>(&o_DP));
        patch_slot(*out, 29, reinterpret_cast<void *>(&h_DIP), reinterpret_cast<void **>(&o_DIP));
        patch_slot(*out, 10, reinterpret_cast<void *>(&h_EndScene), reinterpret_cast<void **>(&o_EndScene));
        patch_slot(*out, 8, reinterpret_cast<void *>(&h_EnumTexFmt), nullptr);
    }
    return hr;
}
using CreateSurface_t = HRESULT(WINAPI *)(void *, void *, void **, IUnknown *);
using DDQI_t = HRESULT(WINAPI *)(void *, REFIID, void **);
CreateSurface_t o_CreateSurface[2]{}; DDQI_t o_DDQI{};
template <int V> HRESULT WINAPI h_CreateSurface(void *dd, void *desc, void **out, IUnknown *u) {
    const HRESULT hr = orig<CreateSurface_t>(dd, 6)(dd, desc, out, u);
    if (SUCCEEDED(hr) && *out) {
        hook_surface<V>(*out);
        const DWORD caps = V ? static_cast<DDSURFACEDESC2 *>(desc)->ddsCaps.dwCaps : static_cast<DDSURFACEDESC *>(desc)->ddsCaps.dwCaps;
        const DWORD flags = V ? static_cast<DDSURFACEDESC2 *>(desc)->dwFlags : static_cast<DDSURFACEDESC *>(desc)->dwFlags;
        const DWORD back = V ? static_cast<DDSURFACEDESC2 *>(desc)->dwBackBufferCount : static_cast<DDSURFACEDESC *>(desc)->dwBackBufferCount;
        if (caps & DDSCAPS_PRIMARYSURFACE) primary_has_back[*out] = (flags & DDSD_BACKBUFFERCOUNT) && back;
    }
    return hr;
}
HRESULT WINAPI h_DDQI(void *dd, REFIID riid, void **out) {
    const HRESULT hr = orig<DDQI_t>(dd, 0)(dd, riid, out);
    if (SUCCEEDED(hr) && *out) {
        if (IsEqualGUID(riid, IID_IDirectDraw4)) {
            patch_slot(*out, 23, reinterpret_cast<void *>(&h_VidMem), nullptr);
            patch_slot(*out, 0, reinterpret_cast<void *>(&h_DDQI), reinterpret_cast<void **>(&o_DDQI));
            patch_slot(*out, 6, reinterpret_cast<void *>(&h_CreateSurface<1>), reinterpret_cast<void **>(&o_CreateSurface[1]));
        }
        if (IsEqualGUID(riid, IID_IDirectDraw2)) {
            patch_slot(*out, 0, reinterpret_cast<void *>(&h_DDQI), reinterpret_cast<void **>(&o_DDQI));
            patch_slot(*out, 6, reinterpret_cast<void *>(&h_CreateSurface<0>), reinterpret_cast<void **>(&o_CreateSurface[0]));
        }
        if (IsEqualGUID(riid, IID_IDirect3D3))
            patch_slot(*out, 8, reinterpret_cast<void *>(&h_CreateD3DDevice), reinterpret_cast<void **>(&o_CreateD3DDevice));
    }
    return hr;
}
using DirectDrawCreate_t = HRESULT(WINAPI *)(GUID *, LPDIRECTDRAW *, IUnknown *);
DirectDrawCreate_t o_DirectDrawCreate{};
HRESULT WINAPI h_DirectDrawCreate(GUID *g, LPDIRECTDRAW *out, IUnknown *u) {
    const HRESULT hr = o_DirectDrawCreate(g, out, u);
    if (SUCCEEDED(hr) && *out) {
        patch_slot(*out, 0, reinterpret_cast<void *>(&h_DDQI), reinterpret_cast<void **>(&o_DDQI));
        patch_slot(*out, 6, reinterpret_cast<void *>(&h_CreateSurface<0>), reinterpret_cast<void **>(&o_CreateSurface[0]));
    }
    return hr;
}

// ---- rdtsc emulation (int3 + nop at the three Mech3.exe sites)
constexpr std::array<DWORD, 3> rdtsc_sites{0x598964, 0x598991, 0x598b0e};
LONG CALLBACK rdtsc_handler(EXCEPTION_POINTERS *e) {
    if (e->ExceptionRecord->ExceptionCode != EXCEPTION_BREAKPOINT) return EXCEPTION_CONTINUE_SEARCH;
    const DWORD at = e->ContextRecord->Eip;
    for (DWORD s : rdtsc_sites)
        if (at == s) {
            const std::uint64_t t = clock_us * 3000ULL;
            e->ContextRecord->Eax = DWORD(t); e->ContextRecord->Edx = DWORD(t >> 32); e->ContextRecord->Eip = s + 2;
            return EXCEPTION_CONTINUE_EXECUTION;
        }
    return EXCEPTION_CONTINUE_SEARCH;
}

// ---- import redirection for the guest modules
struct Redirect { const char *dll, *name; void *hook; void **original; };
int redirect_module(HMODULE m, const std::vector<Redirect> &table) {
    auto *base = reinterpret_cast<unsigned char *>(m);
    auto *nt = reinterpret_cast<IMAGE_NT_HEADERS *>(base + reinterpret_cast<IMAGE_DOS_HEADER *>(base)->e_lfanew);
    const auto &dir = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    int count = 0;
    for (auto *d = reinterpret_cast<IMAGE_IMPORT_DESCRIPTOR *>(base + dir.VirtualAddress); d->Name; ++d) {
        const char *dll = reinterpret_cast<const char *>(base + d->Name);
        auto *names = reinterpret_cast<IMAGE_THUNK_DATA *>(base + (d->OriginalFirstThunk ? d->OriginalFirstThunk : d->FirstThunk));
        auto *iat = reinterpret_cast<IMAGE_THUNK_DATA *>(base + d->FirstThunk);
        for (; names->u1.AddressOfData; ++names, ++iat) {
            char ordinal[16]{};
            const char *fn = ordinal;
            if (IMAGE_SNAP_BY_ORDINAL(names->u1.Ordinal)) std::snprintf(ordinal, sizeof ordinal, "#%u", unsigned(IMAGE_ORDINAL(names->u1.Ordinal)));
            else fn = reinterpret_cast<const char *>(reinterpret_cast<IMAGE_IMPORT_BY_NAME *>(base + names->u1.AddressOfData)->Name);
            for (const auto &r : table)
                if (_stricmp(dll, r.dll) == 0 && std::strcmp(fn, r.name) == 0) {
                    if (!*r.original) *r.original = reinterpret_cast<void *>(iat->u1.Function);
                    DWORD old{};
                    VirtualProtect(&iat->u1.Function, sizeof(void *), PAGE_READWRITE, &old);
                    iat->u1.Function = reinterpret_cast<ULONG_PTR>(r.hook);
                    VirtualProtect(&iat->u1.Function, sizeof(void *), old, &old);
                    ++count;
                }
        }
    }
    return count;
}
void *unused{};
}  // namespace

extern "C" DWORD WINAPI mw34_install(void *) {
    char buffer[4096]{};
    if (GetEnvironmentVariableA("MW34_COMPARE_DIAG", buffer, sizeof buffer)) diag = std::fopen(buffer, "w");
    if (GetEnvironmentVariableA("MW34_DRAW_LOG", buffer, sizeof buffer)) {
        draw_log = std::fopen(buffer, "w");
        if (draw_log) std::setvbuf(draw_log, nullptr, _IOFBF, 1 << 20);
    }
    GetEnvironmentVariableA("MW34_COMPARE_SHOTS", shot_dir, sizeof shot_dir);
    if (GetEnvironmentVariableA("MW34_COMPARE_SHOT_EVERY", buffer, sizeof buffer)) shot_every = unsigned(std::stoul(buffer));
    if (GetEnvironmentVariableA("MW34_COMPARE_SHOT_FROM", buffer, sizeof buffer)) shot_from = unsigned(std::stoul(buffer));
    if (GetEnvironmentVariableA("MW34_COMPARE_SHOT_TO", buffer, sizeof buffer)) shot_to = unsigned(std::stoul(buffer));
    if (GetEnvironmentVariableA("MW34_REG_OVERLAY", buffer, sizeof buffer)) load_overlay(buffer);
    if (GetEnvironmentVariableA("MW34_STAGED_CODEC", buffer, sizeof buffer)) no_codec = buffer[0] == '0';
    if (GetEnvironmentVariableA("MW34_MEM_DUMP_FRAME", buffer, sizeof buffer)) mem_dump_frame = unsigned(std::stoul(buffer));
    GetEnvironmentVariableA("MW34_MEM_DUMP", mem_dump_path, sizeof mem_dump_path);
    if (GetEnvironmentVariableA("MW34_NATIVE_CAPS", buffer, sizeof buffer)) native_caps = buffer[0] == '1';
    if (GetEnvironmentVariableA("MW34_VIDMEM", buffer, sizeof buffer)) {
        std::istringstream l(buffer);
        for (std::string pair; std::getline(l, pair, ',');) {
            const auto slash = pair.find('/');
            if (slash != std::string::npos) vidmem.push_back({DWORD(std::stoul(pair.substr(0, slash))), DWORD(std::stoul(pair.substr(slash + 1)))});
        }
    }
    if (GetEnvironmentVariableA("MW34_HEAP_FILL", buffer, sizeof buffer)) heap_fill = int(std::stoul(buffer, nullptr, 0));
    if (GetEnvironmentVariableA("MW34_DRAW_DETAIL", buffer, sizeof buffer)) detail_frame = unsigned(std::stoul(buffer));
    if (GetEnvironmentVariableA("MW34_FRAME_BUDGET", buffer, sizeof buffer)) frame_budget = unsigned(std::stoul(buffer));
    if (!GetEnvironmentVariableA("MW34_VIRTUAL_CLOCK", buffer, sizeof buffer)) return 2;
    step_us = std::uint64_t(std::stod(buffer) * 1000);
    if (!GetEnvironmentVariableA("MW34_INPUT_SCRIPT", buffer, sizeof buffer)) return 3;
    std::ifstream f(buffer);
    if (!f) return 4;
    for (std::string line; std::getline(f, line);) {
        if (line.empty() || line[0] == '#') continue;
        Event e{}; e.timed = line[0] == '+';
        std::istringstream l(e.timed ? line.substr(1) : line);
        std::string kind;
        if (!(l >> e.frame >> kind)) continue;
        if (kind == "mouse") { e.mouse = true; if (!(l >> e.dx >> e.dy >> e.buttons)) return 5; }
        else if (kind == "key") { std::string st; if (!(l >> std::hex >> e.scan >> st) || (st != "down" && st != "up")) return 6; e.down = st == "down"; }
        else return 7;
        script.push_back(e);
    }
    const std::vector<Redirect> table{
        {"KERNEL32.dll", "GetTickCount", reinterpret_cast<void *>(&h_GetTickCount), &unused},
        {"KERNEL32.dll", "QueryPerformanceCounter", reinterpret_cast<void *>(&h_QPC), &unused},
        {"KERNEL32.dll", "QueryPerformanceFrequency", reinterpret_cast<void *>(&h_QPF), &unused},
        {"KERNEL32.dll", "Sleep", reinterpret_cast<void *>(&h_Sleep), &unused},
        {"KERNEL32.dll", "GetSystemTime", reinterpret_cast<void *>(&h_GetSystemTime), &unused},
        {"KERNEL32.dll", "GetLocalTime", reinterpret_cast<void *>(&h_GetLocalTime), &unused},
        {"KERNEL32.dll", "GetSystemTimeAsFileTime", reinterpret_cast<void *>(&h_GetSystemTimeAsFileTime), &unused},
        {"ADVAPI32.dll", "RegOpenKeyExA", reinterpret_cast<void *>(&h_RegOpenKeyExA), &unused},
        {"ADVAPI32.dll", "RegCreateKeyExA", reinterpret_cast<void *>(&h_RegCreateKeyExA), &unused},
        {"ADVAPI32.dll", "RegQueryValueExA", reinterpret_cast<void *>(&h_RegQueryValueExA), &unused},
        {"ADVAPI32.dll", "RegSetValueExA", reinterpret_cast<void *>(&h_RegSetValueExA), &unused},
        {"ADVAPI32.dll", "RegCloseKey", reinterpret_cast<void *>(&h_RegCloseKey), &unused},
        {"MSVFW32.dll", "ICLocate", reinterpret_cast<void *>(&h_ICLocate), reinterpret_cast<void **>(&o_ICLocate)},
        {"KERNEL32.dll", "HeapAlloc", reinterpret_cast<void *>(&h_HeapAlloc), &unused},
        {"KERNEL32.dll", "CreateThread", reinterpret_cast<void *>(&h_CreateThread), &unused},
        {"WINMM.dll", "timeGetTime", reinterpret_cast<void *>(&h_timeGetTime), &unused},
        {"USER32.dll", "PeekMessageA", reinterpret_cast<void *>(&h_PeekMessageA), &unused},
        {"USER32.dll", "GetMessageA", reinterpret_cast<void *>(&h_GetMessageA), &unused},
        {"USER32.dll", "SetCursorPos", reinterpret_cast<void *>(&h_SetCursorPos), &unused},
        {"USER32.dll", "GetCursorPos", reinterpret_cast<void *>(&h_GetCursorPos), &unused},
        {"DINPUT.dll", "DirectInputCreateA", reinterpret_cast<void *>(&h_DirectInputCreateA), reinterpret_cast<void **>(&o_DirectInputCreateA)},
        {"DSOUND.dll", "#1", reinterpret_cast<void *>(&h_DirectSoundCreate), reinterpret_cast<void **>(&o_DirectSoundCreate)},
        {"DSOUND.dll", "DirectSoundCreate", reinterpret_cast<void *>(&h_DirectSoundCreate), reinterpret_cast<void **>(&o_DirectSoundCreate)},
        {"DDRAW.dll", "DirectDrawCreate", reinterpret_cast<void *>(&h_DirectDrawCreate), reinterpret_cast<void **>(&o_DirectDrawCreate)},
    };
    int total = 0;
    for (const char *name : {"Mech3.exe", "Mech3Msg.dll", "MFC42.DLL", "MSVCP50.dll", "MSVCRZ.dll", "IFORCE2.dll"})
        if (HMODULE m = GetModuleHandleA(name)) {
            const int n = redirect_module(m, table);
            if (diag) std::fprintf(diag, "%s: %d imports redirected\n", name, n);
            total += n;
        }
    // DirectSound is also imported by ordinal 1 (DirectSoundCreate) in some builds; record if it was not found by name.
    if (!o_DirectSoundCreate && diag) std::fprintf(diag, "DirectSoundCreate not imported by name\n");
    AddVectoredExceptionHandler(1, &rdtsc_handler);
    for (DWORD s : rdtsc_sites) {
        auto *p = reinterpret_cast<unsigned char *>(s);
        if (p[0] != 0x0f || p[1] != 0x31) return 8;
        DWORD old{};
        VirtualProtect(p, 2, PAGE_EXECUTE_READWRITE, &old);
        p[0] = 0xcc; p[1] = 0x90;
        VirtualProtect(p, 2, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, 2);
    }
    if (diag) { std::fprintf(diag, "installed: %d redirects, %zu script events, step %llu us\n", total, script.size(), static_cast<unsigned long long>(step_us)); std::fflush(diag); }
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_DETACH) {
        if (draw_log) std::fflush(draw_log);
        if (diag) std::fflush(diag);
    }
    return TRUE;
}
