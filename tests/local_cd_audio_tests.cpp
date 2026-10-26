// Failure-path tests for runtime/audio/local_cd_audio.hpp. WinMM wave calls, the
// worker's event signaling/wait, IsWindow and PostMessageA are redirected to a
// scripted fake driver, so no audio device is opened and no mixer level changes.
// These tests establish provider logic only, not real-driver behavior.
#define NOMINMAX
#include <windows.h>

#include <mmsystem.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <mutex>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace {
const auto real_SetEvent = &::SetEvent;
const auto real_WaitForMultipleObjectsEx = &::WaitForMultipleObjectsEx;
const auto fake_wave = reinterpret_cast<HWAVEOUT>(std::uintptr_t{0x1234});
const auto fake_window = reinterpret_cast<HWND>(std::uintptr_t{0x5678});

struct FakeDriver {
    std::mutex m;
    HANDLE event{};
    std::deque<WAVEHDR *> queue;
    unsigned long long position{};
    int fail_unprepare_at = -1, unprepare_calls = 0, writes = 0, closes = 0;
    bool fail_write{}, fail_position{};
    std::vector<int> first_samples;
    std::vector<WPARAM> notes;
    std::atomic<int> fail_wait{0}; // >0: fail that many waits, -1: fail every wait
    std::atomic<long> waits{0};
    std::atomic<bool> fail_set_event{false};

    void clear() {
        std::lock_guard lock(m);
        fail_unprepare_at = -1;
        unprepare_calls = writes = closes = 0;
        fail_write = fail_position = false;
        first_samples.clear();
        notes.clear();
        fail_wait = 0;
        fail_set_event = false;
    }
} driver;

void complete_locked(unsigned n) {
    while (n-- && !driver.queue.empty()) {
        auto *h = driver.queue.front();
        driver.queue.pop_front();
        driver.position += h->dwBufferLength / 4;
        h->dwFlags = (h->dwFlags & ~DWORD(WHDR_INQUEUE)) | WHDR_DONE;
    }
    real_SetEvent(driver.event);
}
} // namespace

MMRESULT fake_waveOutOpen(LPHWAVEOUT h, UINT, LPCWAVEFORMATEX, DWORD_PTR callback, DWORD_PTR,
                          DWORD) {
    std::lock_guard lock(driver.m);
    driver.event = reinterpret_cast<HANDLE>(callback);
    driver.queue.clear();
    driver.position = 0;
    *h = fake_wave;
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutPrepareHeader(HWAVEOUT, LPWAVEHDR h, UINT) {
    h->dwFlags |= WHDR_PREPARED;
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutUnprepareHeader(HWAVEOUT, LPWAVEHDR h, UINT) {
    std::lock_guard lock(driver.m);
    if (driver.unprepare_calls++ == driver.fail_unprepare_at)
        return MMSYSERR_ERROR;
    h->dwFlags &= ~DWORD(WHDR_PREPARED);
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutWrite(HWAVEOUT, LPWAVEHDR h, UINT) {
    std::lock_guard lock(driver.m);
    if (driver.fail_write)
        return MMSYSERR_NODRIVER;
    if (!(h->dwFlags & WHDR_PREPARED))
        return WAVERR_UNPREPARED;
    h->dwFlags = (h->dwFlags & ~DWORD(WHDR_DONE)) | WHDR_INQUEUE;
    driver.queue.push_back(h);
    ++driver.writes;
    driver.first_samples.push_back(reinterpret_cast<const short *>(h->lpData)[0]);
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutReset(HWAVEOUT) {
    std::lock_guard lock(driver.m);
    for (auto *h : driver.queue)
        h->dwFlags = (h->dwFlags & ~DWORD(WHDR_INQUEUE)) | WHDR_DONE;
    driver.queue.clear();
    driver.position = 0;
    real_SetEvent(driver.event);
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutClose(HWAVEOUT) {
    std::lock_guard lock(driver.m);
    ++driver.closes;
    return MMSYSERR_NOERROR;
}
MMRESULT fake_waveOutPause(HWAVEOUT) { return MMSYSERR_NOERROR; }
MMRESULT fake_waveOutRestart(HWAVEOUT) { return MMSYSERR_NOERROR; }
MMRESULT fake_waveOutGetPosition(HWAVEOUT, LPMMTIME t, UINT) {
    std::lock_guard lock(driver.m);
    if (driver.fail_position)
        return MMSYSERR_NODRIVER;
    t->wType = TIME_SAMPLES;
    t->u.sample = DWORD(driver.position);
    return MMSYSERR_NOERROR;
}
BOOL fake_SetEvent(HANDLE h) {
    if (driver.fail_set_event) {
        ::SetLastError(ERROR_INVALID_HANDLE);
        return FALSE;
    }
    return real_SetEvent(h);
}
DWORD fake_WaitForMultipleObjectsEx(DWORD n, const HANDLE *h, BOOL all, DWORD ms, BOOL alertable) {
    ++driver.waits;
    const int fail = driver.fail_wait.load();
    if (fail) {
        if (fail > 0)
            driver.fail_wait = fail - 1;
        ::SetLastError(ERROR_INVALID_HANDLE);
        return WAIT_FAILED;
    }
    return real_WaitForMultipleObjectsEx(n, h, all, ms, alertable);
}
DWORD fake_WaitForMultipleObjects(DWORD n, const HANDLE *h, BOOL all, DWORD ms) {
    return fake_WaitForMultipleObjectsEx(n, h, all, ms, FALSE);
}
BOOL fake_IsWindow(HWND w) { return w == fake_window; }
BOOL fake_PostMessageA(HWND, UINT, WPARAM reason, LPARAM) {
    std::lock_guard lock(driver.m);
    driver.notes.push_back(reason);
    return TRUE;
}

#define waveOutOpen fake_waveOutOpen
#define waveOutPrepareHeader fake_waveOutPrepareHeader
#define waveOutUnprepareHeader fake_waveOutUnprepareHeader
#define waveOutWrite fake_waveOutWrite
#define waveOutReset fake_waveOutReset
#define waveOutClose fake_waveOutClose
#define waveOutPause fake_waveOutPause
#define waveOutRestart fake_waveOutRestart
#define waveOutGetPosition fake_waveOutGetPosition
#define SetEvent fake_SetEvent
#define WaitForMultipleObjects fake_WaitForMultipleObjects
#define WaitForMultipleObjectsEx fake_WaitForMultipleObjectsEx
#define IsWindow fake_IsWindow
#define PostMessageA fake_PostMessageA
#include "audio/local_cd_audio.hpp"
#undef SetEvent

namespace {
using mw34::audio::LocalCdAudio;
namespace fs = std::filesystem;
constexpr UINT dev = LocalCdAudio::device_id;
int failures = 0;

void check(bool ok, const char *what) {
    std::printf("  [%s] %s\n", ok ? "ok" : "FAIL", what);
    if (!ok)
        ++failures;
}
void put32(std::string &s, std::uint32_t v) {
    for (int i = 0; i < 4; ++i)
        s.push_back(char((v >> (8 * i)) & 0xff));
}
// Track 2 lasts 2 s and track 3 lasts 1 s. Each left/right sample is
// (timeline frame % 30000) + 1, so a write's first sample names its position.
fs::path make_fixture(const fs::path &dir) {
    fs::create_directories(dir);
    const std::uint32_t frames[2] = {88200, 44100};
    std::string manifest("MW3CD1\0\0", 8);
    put32(manifest, 1);
    put32(manifest, 2);
    std::uint32_t base = 0;
    for (std::uint32_t t = 0; t < 2; ++t) {
        const auto wav = fs::absolute(dir / ("track" + std::to_string(t + 2) + ".wav")).string();
        std::string w = "RIFF";
        put32(w, 36 + frames[t] * 4);
        w += "WAVEfmt ";
        put32(w, 16);
        put32(w, 0x00020001);
        put32(w, 44100);
        put32(w, 44100 * 4);
        put32(w, 0x00100004);
        w += "data";
        put32(w, frames[t] * 4);
        for (std::uint32_t i = 0; i < frames[t]; ++i) {
            const auto v = std::uint16_t((base + i) % 30000 + 1);
            for (int c = 0; c < 2; ++c) {
                w.push_back(char(v & 0xff));
                w.push_back(char(v >> 8));
            }
        }
        std::ofstream(wav, std::ios::binary).write(w.data(), std::streamsize(w.size()));
        base += frames[t];
        put32(manifest, t + 2);
        put32(manifest, 44100);
        put32(manifest, 2);
        put32(manifest, 16);
        put32(manifest, frames[t]);
        put32(manifest, 0);
        put32(manifest, std::uint32_t(wav.size()));
        manifest += wav;
    }
    const auto path = dir / "music.mw3cd1";
    std::ofstream(path, std::ios::binary).write(manifest.data(), std::streamsize(manifest.size()));
    return path;
}

void pause_ms(int ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }
std::size_t queued() {
    std::lock_guard lock(driver.m);
    return driver.queue.size();
}
int writes() {
    std::lock_guard lock(driver.m);
    return driver.writes;
}
void complete(unsigned n) {
    std::lock_guard lock(driver.m);
    complete_locked(n);
}
bool noted(WPARAM reason) {
    std::lock_guard lock(driver.m);
    for (auto n : driver.notes)
        if (n == reason)
            return true;
    return false;
}
// Return buffers one at a time through the worker's reap and refill path.
void advance(unsigned buffers) {
    for (unsigned i = 0; i <= buffers; ++i) {
        for (int spin = 0; queued() < 4 && spin < 500; ++spin)
            pause_ms(1);
        if (i < buffers)
            complete(1);
    }
}
MCIERROR open(LocalCdAudio &cd) {
    MCI_OPEN_PARMSA o{};
    o.lpstrDeviceType = "cdaudio";
    return cd.send(0, MCI_OPEN, MCI_OPEN_TYPE, reinterpret_cast<DWORD_PTR>(&o));
}
MCIERROR status(LocalCdAudio &cd, DWORD item, DWORD_PTR &out) {
    MCI_STATUS_PARMS p{};
    p.dwItem = item;
    const auto e = cd.send(dev, MCI_STATUS, MCI_STATUS_ITEM, reinterpret_cast<DWORD_PTR>(&p));
    out = p.dwReturn;
    return e;
}
MCIERROR play(LocalCdAudio &cd, DWORD flags, DWORD from = 0, DWORD to = 0) {
    MCI_PLAY_PARMS p{};
    p.dwCallback = reinterpret_cast<DWORD_PTR>(fake_window);
    p.dwFrom = from;
    p.dwTo = to;
    return cd.send(dev, MCI_PLAY, flags, reinterpret_cast<DWORD_PTR>(&p));
}
MCIERROR command(LocalCdAudio &cd, UINT msg) { return cd.send(dev, msg, 0, 0); }
unsigned cd_frames(DWORD_PTR msf) {
    const auto v = DWORD(msf);
    return MCI_MSF_MINUTE(v) * 4500U + MCI_MSF_SECOND(v) * 75U + MCI_MSF_FRAME(v);
}
// A deadlock cannot be recovered in-process; report it and stop.
void within(int ms, const char *what, const std::function<void()> &body) {
    std::atomic<bool> done{false};
    std::thread t([&] {
        body();
        done = true;
    });
    for (int waited = 0; !done && waited < ms; waited += 10)
        pause_ms(10);
    if (!done) {
        std::printf("  [FAIL] %s did not finish within %d ms\n", what, ms);
        std::fflush(stdout);
        ::ExitProcess(1);
    }
    t.join();
}

void control(const fs::path &manifest) {
    std::puts("control: completion, abort and cursor");
    driver.clear();
    LocalCdAudio cd(manifest);
    check(open(cd) == 0, "MCI_OPEN succeeds");
    // 0:1:0 to 0:1:30 is 30 CD frames, 17640 PCM frames, 40 buffers.
    check(play(cd, MCI_NOTIFY | MCI_FROM | MCI_TO, MCI_MAKE_MSF(0, 1, 0), MCI_MAKE_MSF(0, 1, 30)) ==
              0,
          "PLAY range succeeds");
    advance(20);
    DWORD_PTR v{};
    check(status(cd, MCI_STATUS_POSITION, v) == 0 && cd_frames(v) == 90,
          "cursor is base plus 20 returned buffers");
    advance(16);
    complete(4);
    pause_ms(50);
    check(noted(MCI_NOTIFY_SUCCESSFUL), "SUCCESSFUL after the final buffer drains");
    check(status(cd, MCI_STATUS_MODE, v) == 0 && v == MCI_MODE_STOP, "mode STOP after completion");
    check(play(cd, MCI_NOTIFY | MCI_FROM, MCI_MAKE_MSF(0, 0, 0)) == 0, "second PLAY succeeds");
    check(command(cd, MCI_STOP) == 0 && noted(MCI_NOTIFY_ABORTED), "STOP aborts notification");
    check(command(cd, MCI_CLOSE) == 0, "CLOSE succeeds");
}

void aux_device_contract(const fs::path &manifest) {
    using mw34::audio::valid_host_aux_device;
    check(!valid_host_aux_device(UINT(-1), false, 0), "missing AUX sentinel is not a host mixer");
    check(!valid_host_aux_device(0, false, 0), "no physical AUX means device zero is absent");
    check(!valid_host_aux_device(UINT(-1), true, 2), "AUX mapper is not a volume-device ID");
    check(!valid_host_aux_device(0, true, 2), "private CD device is not a physical mixer");
    check(valid_host_aux_device(0, false, 2) && valid_host_aux_device(1, false, 2),
          "physical IDs retain normal bounds without private CD");
    check(!valid_host_aux_device(2, false, 2), "unshifted enumeration upper boundary is invalid");
    check(valid_host_aux_device(1, true, 2) && valid_host_aux_device(2, true, 2),
          "private CD shifts host IDs exactly once");
    check(!valid_host_aux_device(3, true, 2), "shifted enumeration upper boundary is invalid");
    driver.clear();
    LocalCdAudio cd(manifest);
    check(cd.enabled(), "authored PCM fixture enables private CD");
    AUXCAPSA caps{};
    check(cd.aux_caps(caps) == 0 && caps.wTechnology == AUXCAPS_CDAUDIO,
          "private device advertises CD audio");
    check(cd.aux_set_volume(0x12345678) == 0,
          "private volume request succeeds without a physical mixer");
    DWORD value{};
    check(cd.aux_get_volume(value) == 0 && value == 0x12345678,
          "private stereo volume is retained exactly");
}

void close_failure(const fs::path &manifest) {
    std::puts("F1: failed MCI_CLOSE after a successful reset");
    driver.clear();
    LocalCdAudio cd(manifest);
    open(cd);
    play(cd, MCI_NOTIFY | MCI_FROM, MCI_MAKE_MSF(0, 0, 0));
    advance(10);
    {
        std::lock_guard lock(driver.m);
        driver.fail_unprepare_at = 0;
    }
    const int before = writes();
    check(command(cd, MCI_CLOSE) == MCIERR_HARDWARE, "CLOSE reports MCIERR_HARDWARE");
    pause_ms(80);
    check(writes() == before && queued() == 0, "no refill after the failed CLOSE");
    check(noted(MCI_NOTIFY_FAILURE), "pending play notification resolved as FAILURE");
    DWORD_PTR v{};
    check(status(cd, MCI_STATUS_MODE, v) == MCIERR_HARDWARE, "later commands report the fault");
    {
        std::lock_guard lock(driver.m);
        driver.fail_unprepare_at = -1;
    }
    check(command(cd, MCI_CLOSE) == 0, "retried CLOSE succeeds");
    std::lock_guard lock(driver.m);
    check(driver.closes == 1, "device closed exactly once");
}

void device_failure_cursor(const fs::path &manifest, bool position_fails) {
    std::printf("F2%s: waveOutWrite failure during refill%s\n", position_fails ? "b" : "a",
                position_fails ? " with position query also failing" : "");
    driver.clear();
    LocalCdAudio cd(manifest);
    open(cd);
    play(cd, MCI_NOTIFY | MCI_FROM, MCI_MAKE_MSF(0, 0, 0));
    advance(100); // 44100 frames returned: 75 CD frames
    {
        std::lock_guard lock(driver.m);
        driver.fail_write = true;
        driver.fail_position = position_fails;
    }
    complete(1);
    pause_ms(80);
    check(noted(MCI_NOTIFY_FAILURE), "FAILURE notification posted");
    {
        std::lock_guard lock(driver.m);
        driver.fail_write = driver.fail_position = false;
        driver.first_samples.clear();
    }
    DWORD_PTR v{};
    check(status(cd, MCI_STATUS_POSITION, v) == MCIERR_HARDWARE, "STATUS reports the fault");
    check(command(cd, MCI_STOP) == 0, "STOP clears the play fault");
    check(status(cd, MCI_STATUS_POSITION, v) == 0 && cd_frames(v) >= 75,
          "cursor keeps the returned audio");
    check(play(cd, 0) == 0, "PLAY without FROM succeeds");
    int first = -1;
    {
        std::lock_guard lock(driver.m);
        if (!driver.first_samples.empty())
            first = driver.first_samples.front() - 1;
    }
    // Sample tags wrap at 30000; timeline frames 44100..59999 tag as 14100..29999.
    check(first >= 44100 % 30000, "continuation starts at or after the returned audio");
    command(cd, MCI_CLOSE);
}

void shutdown_signal_failure(const fs::path &manifest) {
    std::puts("F3: shutdown when signaling the worker fails");
    driver.clear();
    auto *cd = new LocalCdAudio(manifest);
    open(*cd);
    play(*cd, MCI_FROM, MCI_MAKE_MSF(0, 0, 0));
    advance(2);
    driver.fail_set_event = true;
    DWORD_PTR v{};
    within(2000, "ordinary request with failed signaling", [&] {
        check(status(*cd, MCI_STATUS_MODE, v) == MCIERR_HARDWARE,
              "ordinary request reports MCIERR_HARDWARE");
    });
    within(2000, "destructor with failed signaling", [&] { delete cd; });
    check(true, "destructor returned");
    std::lock_guard lock(driver.m);
    check(driver.closes == 1, "device closed during shutdown");
}

void wait_failure(const fs::path &manifest) {
    std::puts("F4a: one worker wait failure during playback");
    {
        driver.clear();
        LocalCdAudio cd(manifest);
        open(cd);
        play(cd, MCI_NOTIFY | MCI_FROM, MCI_MAKE_MSF(0, 0, 0));
        advance(4);
        driver.fail_wait = 1;
        complete(1);
        pause_ms(150);
        const int after_failure = writes();
        complete(4);
        pause_ms(80);
        check(writes() == after_failure, "playback stops after the failed wait");
        check(noted(MCI_NOTIFY_FAILURE), "FAILURE notification posted");
        DWORD_PTR v{};
        check(status(cd, MCI_STATUS_MODE, v) == MCIERR_HARDWARE, "STATUS reports the fault");
        check(command(cd, MCI_STOP) == MCIERR_HARDWARE, "STOP does not clear a worker fault");
        check(play(cd, MCI_FROM, MCI_MAKE_MSF(0, 0, 0)) == MCIERR_HARDWARE,
              "PLAY does not report false success");
        check(command(cd, MCI_CLOSE) == 0, "CLOSE still releases the device");
    }
    std::puts("F4b: MCI_WAIT play pending when the wait fails");
    {
        driver.clear();
        LocalCdAudio cd(manifest);
        open(cd);
        std::atomic<MCIERROR> waited{0xffffffff};
        std::thread player([&] { waited = play(cd, MCI_WAIT | MCI_FROM, MCI_MAKE_MSF(0, 0, 0)); });
        advance(2);
        driver.fail_wait = 1;
        complete(1);
        within(2000, "MCI_WAIT release", [&] { player.join(); });
        check(waited == MCIERR_HARDWARE, "waiting PLAY returns MCIERR_HARDWARE");
        command(cd, MCI_CLOSE);
    }
    std::puts("F4c: persistent worker wait failure");
    {
        driver.clear();
        auto *cd = new LocalCdAudio(manifest);
        open(*cd);
        const long before = driver.waits;
        driver.fail_wait = -1;
        DWORD_PTR v{};
        status(*cd, MCI_STATUS_MODE, v); // served by the wait already in progress
        pause_ms(100);
        within(2000, "request during persistent wait failure", [&] {
            check(status(*cd, MCI_STATUS_MODE, v) == MCIERR_HARDWARE,
                  "request completes with MCIERR_HARDWARE");
        });
        pause_ms(300);
        const long count = driver.waits - before;
        std::printf("    waits in about 300 ms: %ld\n", count);
        check(count < 40, "worker does not spin");
        within(2000, "CLOSE during persistent wait failure",
               [&] { check(command(*cd, MCI_CLOSE) == 0, "CLOSE completes"); });
        within(2000, "destructor during persistent wait failure", [&] { delete cd; });
        check(true, "destructor returned");
    }
}
} // namespace

// An optional scenario name runs one group, so a deadlocking group cannot hide others.
int main(int argc, char **argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    const auto manifest = make_fixture(fs::path(argv[0]).parent_path() / "local_cd_audio_fixture");
    const std::string only = argc > 1 ? argv[1] : "";
    const std::pair<const char *, std::function<void()>> groups[] = {
        {"control", [&] { control(manifest); }},
        {"aux", [&] { aux_device_contract(manifest); }},
        {"close", [&] { close_failure(manifest); }},
        {"cursor",
         [&] {
             device_failure_cursor(manifest, false);
             device_failure_cursor(manifest, true);
         }},
        {"wait", [&] { wait_failure(manifest); }},
        {"shutdown", [&] { shutdown_signal_failure(manifest); }},
    };
    for (const auto &[name, run] : groups)
        if (only.empty() || only == name)
            run();
    std::printf("%d failures\n", failures);
    return failures ? 1 : 0;
}
