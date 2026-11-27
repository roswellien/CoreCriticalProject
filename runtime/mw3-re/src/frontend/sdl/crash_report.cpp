#include "frontend/sdl/crash_report.h"
#include "frontend/sdl/log.h"
#include "frontend/sdl/run_log.h"

#include <SDL3/SDL.h>

#include <csignal>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <exception>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <dbghelp.h>
#include <process.h>
#else
#include <limits.h>
#include <unistd.h>
#if defined(__APPLE__)
#include <mach-o/dyld.h>
#endif
#if defined(__GLIBC__) || defined(__APPLE__)
#include <execinfo.h>
#define MW3_HAVE_BACKTRACE 1
#endif
#endif

namespace sdlfe {

// The minidump goes next to the log: keep the log path's directory (with its separator) and add
// crash.dmp. A bare log file name (no separator) means the current directory, so the result is
// plain "crash.dmp". Returns false, with an empty result, when the path would not fit.
bool crash_report_dump_path(const char* log, char* output, size_t capacity) {
  return crash_report_sibling_path(log, "crash.dmp", output, capacity);
}

bool crash_report_sibling_path(const char* log, const char* name, char* output, size_t capacity) {
  if (!output || capacity == 0 || !name) return false;
  output[0] = '\0';
  const size_t name_length = std::strlen(name);
  size_t directory_length = 0;
  if (log) {
    for (size_t index = 0; log[index]; ++index)
      if (log[index] == '\\' || log[index] == '/') directory_length = index + 1;
  }
  if (directory_length + name_length + 1 > capacity) return false;
  if (directory_length) std::memcpy(output, log, directory_length);
  std::memcpy(output + directory_length, name, name_length + 1);
  return true;
}

bool crash_report_address_rva(uintptr_t module_base, size_t image_size, uintptr_t address,
                              uintptr_t* rva) {
  if (!rva || module_base == 0 || address < module_base || address - module_base >= image_size)
    return false;
  const uintptr_t offset = address - module_base;
  *rva = offset;
  return true;
}

size_t crash_report_format_rva(char* output, size_t capacity, bool inside_image, uintptr_t rva) {
  if (!output || capacity == 0) return 0;
  const int length = inside_image
                         ? std::snprintf(output, capacity, "RVA 0x%llx",
                                         static_cast<unsigned long long>(rva))
                         : std::snprintf(output, capacity, "outside mw3.exe image");
  // snprintf always terminates for capacity >= 1; a negative length or a truncated result is a
  // failure with an empty result, like the other helpers.
  if (length < 0 || static_cast<size_t>(length) >= capacity) {
    output[0] = '\0';
    return 0;
  }
  return static_cast<size_t>(length);
}

CrashReportWaitOutcome crash_report_classify_wait_result(uint32_t wait_result) {
  if (wait_result == 0) return CrashReportWaitOutcome::completed;
  if (wait_result == 1) return CrashReportWaitOutcome::worker_exited;
  if (wait_result == 258) return CrashReportWaitOutcome::timed_out;
  return CrashReportWaitOutcome::failed;
}

bool crash_report_report_was_written(CrashReportWaitOutcome outcome, bool worker_failed) {
  return outcome == CrashReportWaitOutcome::completed && !worker_failed;
}

CrashReportEntry crash_report_try_enter(std::atomic<bool>& in_progress, bool on_worker) {
  // The worker must never wait on itself, even if it fails before any request is captured.
  if (on_worker) return CrashReportEntry::skip_worker;
  bool expected = false;
  if (in_progress.compare_exchange_strong(expected, true)) return CrashReportEntry::capture;
  return CrashReportEntry::wait;
}

namespace {

char g_program[64] = "mw3";
char g_tail[1024] = "";  // the box's text after the reason
bool g_box = false;
bool g_test = false;
#if defined(_WIN32)
char g_dump_path[MAX_PATH + 16];
// Handler admission must not acquire a library lock on an exhausted or faulting thread.
static_assert(std::atomic<bool>::is_always_lock_free);
std::atomic<bool> g_exception_in_progress{false};
std::atomic<bool> g_dump_worker_stopping{false};
// Set when the worker could not serve a request. It also signals completion so waiters are
// released, so the waiters must look at this flag before treating completion as success.
std::atomic<bool> g_dump_worker_failed{false};
bool g_fail_worker_start_for_test = false;
HANDLE g_stderr_handle = INVALID_HANDLE_VALUE;
HANDLE g_dump_request_event = nullptr;
HANDLE g_dump_complete_event = nullptr;
// Set after the box has been closed (or at once when no box is shown), so the faulting thread
// can keep the process alive while the user reads the message.
HANDLE g_dump_box_done_event = nullptr;
HANDLE g_dump_worker_thread = nullptr;
bool g_dump_worker_available = false;
DWORD g_dump_worker_thread_id = 0;
DWORD g_installing_thread_id = 0;
bool g_installed = false;
LPTOP_LEVEL_EXCEPTION_FILTER g_previous_exception_filter = nullptr;
using AbortHandler = void (*)(int);
AbortHandler g_previous_abort_handler = SIG_DFL;
std::terminate_handler g_previous_terminate_handler = nullptr;
enum class CrashReportCause { exception, aborted, terminated };
CrashReportCause g_report_cause = CrashReportCause::exception;
EXCEPTION_RECORD g_dump_exception_record{};
CONTEXT g_dump_context{};
EXCEPTION_POINTERS g_dump_exception_pointers{};
DWORD g_dump_faulting_thread_id = 0;
// Keep dbghelp loaded for the process lifetime so the exception handler never
// calls LoadLibrary or FreeLibrary while the loader lock may be held.
HMODULE g_dbghelp = nullptr;
using MiniDumpWriteDumpFunction = BOOL(WINAPI*)(HANDLE, DWORD, HANDLE, MINIDUMP_TYPE,
                                                PMINIDUMP_EXCEPTION_INFORMATION,
                                                PMINIDUMP_USER_STREAM_INFORMATION,
                                                PMINIDUMP_CALLBACK_INFORMATION);
MiniDumpWriteDumpFunction g_write_dump = nullptr;
uintptr_t g_module_base = 0;
size_t g_module_image_size = 0;

void crash_log(const char* format, ...);
void report_exception();
void say_crash();
void request_crash_report(EXCEPTION_POINTERS* exception, CrashReportCause cause);

void write_minidump() {
  if (!g_write_dump) {
    crash_log("%s: dbghelp unavailable for minidump\n", g_program);
  } else if (!g_dump_path[0]) {
    crash_log("%s: minidump path does not fit\n", g_program);
  } else {
    HANDLE file = CreateFileA(g_dump_path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) {
      crash_log("%s: could not create minidump: %s\n", g_program, g_dump_path);
      return;
    }
    MINIDUMP_EXCEPTION_INFORMATION exception_info{};
    exception_info.ThreadId = g_dump_faulting_thread_id;
    exception_info.ExceptionPointers = &g_dump_exception_pointers;
    exception_info.ClientPointers = FALSE;
    // Abort and a filter invocation without a context still get a dump of the live threads.
    const bool have_context = g_dump_exception_pointers.ExceptionRecord &&
                              g_dump_exception_pointers.ContextRecord;
    if (g_write_dump(GetCurrentProcess(), GetCurrentProcessId(), file, MiniDumpNormal,
                     have_context ? &exception_info : nullptr, nullptr, nullptr)) {
      CloseHandle(file);
      crash_log("%s: minidump: %s\n", g_program, g_dump_path);
    } else {
      CloseHandle(file);
      crash_log("%s: minidump failed: %s\n", g_program, g_dump_path);
    }
  }
}

DWORD WINAPI dump_worker(void*) {
  for (;;) {
    if (WaitForSingleObject(g_dump_request_event, INFINITE) != WAIT_OBJECT_0) {
      g_dump_worker_failed.store(true);
      SetEvent(g_dump_complete_event);
      SetEvent(g_dump_box_done_event);
      return 1;
    }
    if (g_dump_worker_stopping.load()) {
      SetEvent(g_dump_complete_event);
      SetEvent(g_dump_box_done_event);
      return 0;
    }
    // The crash reason goes to crash.txt first: it is one small write to our own file handle, and a
    // slow or blocked minidump must not be able to cost it. All formatting, I/O and UI stay on this
    // independent stack, including for stack overflow.
    report_exception();
    write_minidump();
    // The last lines printed before the crash into mw3.log (run_log.h), before anything can end the process.
    sdlfe::run_log_drain(500);
    // Completion means "dump and log are written". It is published BEFORE the message box, so
    // the faulting thread's bounded wait never expires while the box is open.
    SetEvent(g_dump_complete_event);
    // A test exits on the faulting thread, right after completion.
    if (!g_test) say_crash();
    SetEvent(g_dump_box_done_event);
  }
}

void start_dump_worker() {
  // The error is read right after the call that failed (0 when no call failed, as with the test
  // switch): a later call or the CloseHandle cleanup below would overwrite or stale it.
  DWORD creation_error = 0;
  g_dump_request_event = CreateEventA(nullptr, FALSE, FALSE, nullptr);
  if (!g_dump_request_event) creation_error = GetLastError();
  g_dump_complete_event = CreateEventA(nullptr, TRUE, FALSE, nullptr);
  if (!g_dump_complete_event && !creation_error) creation_error = GetLastError();
  g_dump_box_done_event = CreateEventA(nullptr, TRUE, FALSE, nullptr);
  if (!g_dump_box_done_event && !creation_error) creation_error = GetLastError();
  if (g_dump_request_event && g_dump_complete_event && g_dump_box_done_event &&
      !g_fail_worker_start_for_test) {
    g_dump_worker_thread = CreateThread(nullptr, 1024 * 1024, dump_worker, nullptr,
                                        STACK_SIZE_PARAM_IS_A_RESERVATION,
                                        &g_dump_worker_thread_id);
    if (!g_dump_worker_thread) creation_error = GetLastError();
  }
  if (g_dump_worker_thread) {
    g_dump_worker_available = true;
    return;
  }
  if (g_dump_request_event) {
    CloseHandle(g_dump_request_event);
    g_dump_request_event = nullptr;
  }
  if (g_dump_complete_event) {
    CloseHandle(g_dump_complete_event);
    g_dump_complete_event = nullptr;
  }
  if (g_dump_box_done_event) {
    CloseHandle(g_dump_box_done_event);
    g_dump_box_done_event = nullptr;
  }
  g_write_dump = nullptr;
  g_dump_worker_thread_id = 0;
  // Logged once: this runs only at install.
  crash_log("%s: minidump worker unavailable (error %lu); dump disabled\n", g_program,
            creation_error);
}

void crash_log(const char* format, ...) {
  char line[2048];
  va_list arguments;
  va_start(arguments, format);
  const int length = std::vsnprintf(line, sizeof line, format, arguments);
  va_end(arguments);
  if (length <= 0) return;
  if (g_stderr_handle == nullptr || g_stderr_handle == INVALID_HANDLE_VALUE) return;
  DWORD written = 0;
  if (!WriteFile(g_stderr_handle, line,
                 static_cast<DWORD>(length < static_cast<int>(sizeof line) ? length : sizeof line - 1),
                 &written, nullptr))
    return;
}

#endif
void set_text(const std::string& program, const std::string& log) {
  std::snprintf(g_program, sizeof g_program, "%s", program.c_str());
#if defined(_WIN32)
  // The exception address, RVA and registers are in crash.txt next to the log, not in the log.
  char crash_text_path[MAX_PATH + 16] = "";
  if (crash_report_sibling_path(log.c_str(), "crash.txt", crash_text_path,
                                sizeof crash_text_path)) {
    std::snprintf(g_tail, sizeof g_tail,
                  ".\n\nThe log is %s\nThe crash details are in %s\nPlease include both (and crash.dmp "
                  "next to them) if you report this.",
                  log.c_str(), crash_text_path);
  } else {
    // No path for crash.txt fits: name only the log rather than an empty file name.
    std::snprintf(g_tail, sizeof g_tail, ".\n\nThe log is %s\nPlease include it if you report this.",
                  log.c_str());
  }
#else
  std::snprintf(g_tail, sizeof g_tail, ".\n\nThe log is %s\nPlease include it if you report this.", log.c_str());
#endif
}

[[noreturn]] void on_terminate() {
#if defined(_WIN32)
  // abort() itself can print to stderr before raising SIGABRT. Bypass it here so termination
  // cannot block before reaching the shared guard and bounded worker wait.
  request_crash_report(nullptr, CrashReportCause::terminated);
  // _exit would take the CRT exit lock, which can hang while the process is going down.
  TerminateProcess(GetCurrentProcess(), 3);
  for (;;) Sleep(1000);
#else
  const char* what = "";
  try {
    if (auto e = std::current_exception()) std::rethrow_exception(e);
  } catch (const std::exception& e) {
    what = e.what();
  } catch (...) {
  }
  sdlfe::log::line(sdlfe::log::Level::error, "%s: uncaught exception: %s\n", g_program, what);
  std::abort();  // the crash's report from here
#endif
}

#if defined(_WIN32)

void say_crash() {
  char text[1200];
  char exception_reason[32];
  const char* reason = "exception";
  if (g_report_cause == CrashReportCause::aborted) reason = "aborted";
  else if (g_report_cause == CrashReportCause::terminated) reason = "uncaught exception";
  else if (g_dump_exception_pointers.ExceptionRecord) {
    std::snprintf(exception_reason, sizeof exception_reason, "exception 0x%08lx",
                  g_dump_exception_record.ExceptionCode);
    reason = exception_reason;
  }
  std::snprintf(text, sizeof text, "MechWarrior 3 crashed (%s)%s", reason, g_tail);
  // Topmost: with no owner it could open behind a fullscreen game.
  if (g_box)
    MessageBoxA(nullptr, text, "MechWarrior 3",
                MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND);
}

void report_exception() {
  if (g_report_cause != CrashReportCause::exception) {
    const char* reason = g_report_cause == CrashReportCause::terminated ? "uncaught exception"
                                                                     : "aborted";
    crash_log("%s: crashed: %s\n", g_program, reason);
    return;
  }
  const EXCEPTION_POINTERS* e = &g_dump_exception_pointers;
  if (e->ExceptionRecord) {
    const auto exception_address = reinterpret_cast<uintptr_t>(e->ExceptionRecord->ExceptionAddress);
    uintptr_t rva = 0;
    char rva_text[64];
    const bool inside_image = crash_report_address_rva(g_module_base, g_module_image_size,
                                                        exception_address, &rva);
    crash_report_format_rva(rva_text, sizeof rva_text, inside_image, rva);
    crash_log("%s: crashed: exception 0x%08lx at %p module base %p %s\n", g_program,
              e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress,
              reinterpret_cast<void*>(g_module_base), rva_text);
    if (e->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION &&
        e->ExceptionRecord->NumberParameters >= 2) {
      const ULONG_PTR access = e->ExceptionRecord->ExceptionInformation[0];
      const char* access_name = "unknown";
      if (access == 0) access_name = "read";
      else if (access == 1) access_name = "write";
      else if (access == 8) access_name = "execute";
      crash_log("%s: access violation: %s (%llu) target %p\n", g_program, access_name,
                static_cast<unsigned long long>(access),
                reinterpret_cast<void*>(e->ExceptionRecord->ExceptionInformation[1]));
    }
    if (e->ContextRecord) {
#if defined(_M_X64) || defined(__x86_64__)
      crash_log("%s: registers: RIP=%p RAX=%p RBX=%p RCX=%p RDX=%p\n", g_program,
                reinterpret_cast<void*>(e->ContextRecord->Rip),
                reinterpret_cast<void*>(e->ContextRecord->Rax),
                reinterpret_cast<void*>(e->ContextRecord->Rbx),
                reinterpret_cast<void*>(e->ContextRecord->Rcx),
                reinterpret_cast<void*>(e->ContextRecord->Rdx));
#else
      crash_log("%s: registers: context is not x64\n", g_program);
#endif
    }
  } else {
    crash_log("%s: crashed: exception details unavailable\n", g_program);
  }
}

// Fills the preallocated capture. Both pointers are cleared first: an abort or terminate request
// carries no exception, and must not report an earlier capture's record or context.
void store_capture(const EXCEPTION_POINTERS* exception, CrashReportCause cause) {
  g_report_cause = cause;
  g_dump_exception_pointers = {};
  if (exception && exception->ExceptionRecord) {
    g_dump_exception_record = *exception->ExceptionRecord;
    g_dump_exception_record.ExceptionRecord = nullptr;
    g_dump_exception_pointers.ExceptionRecord = &g_dump_exception_record;
  }
  if (exception && exception->ContextRecord) {
    g_dump_context = *exception->ContextRecord;
    g_dump_exception_pointers.ContextRecord = &g_dump_context;
  }
}

void request_crash_report(EXCEPTION_POINTERS* exception, CrashReportCause cause) {
  const DWORD thread_id = GetCurrentThreadId();
  const CrashReportEntry entry = crash_report_try_enter(
      g_exception_in_progress, thread_id == g_dump_worker_thread_id);
  if (entry == CrashReportEntry::skip_worker || !g_dump_worker_available) return;
  if (entry == CrashReportEntry::capture) {
    // Only the winning thread writes this preallocated capture. The request event publishes it
    // to the worker. Completion starts unsignalled at install and is never reset by a crash:
    // another failing thread can safely start waiting even before the capture is published.
    store_capture(exception, cause);
    g_dump_faulting_thread_id = thread_id;
    if (!SetEvent(g_dump_request_event)) {
      g_dump_worker_failed.store(true);
      SetEvent(g_dump_complete_event);
      return;
    }
  }
  // All SEH, abort and terminate entries share this bounded wait. In particular, abort cannot
  // exit the process immediately while another thread is still writing the dump. A dead worker
  // is observable without burning the full timeout, and never waits on itself.
  const HANDLE handles[] = {g_dump_complete_event, g_dump_worker_thread};
  const DWORD result = WaitForMultipleObjects(2, handles, FALSE, 5000);
  const CrashReportWaitOutcome outcome = crash_report_classify_wait_result(result);
  // There is deliberately no logging here: even an error/timeout must not touch the stderr pipe.
  const bool report_written =
      crash_report_report_was_written(outcome, g_dump_worker_failed.load());
  if (g_test && report_written) TerminateProcess(GetCurrentProcess(), 70);
  // The dump and log are written: keep the process alive until the user closes the box. A worker
  // that died ends this wait at once.
  // The wait is bounded: a stuck worker, or a box hidden behind a frozen fullscreen game, must not
  // keep a crashed process alive forever.
  if (report_written && g_box) {
    const HANDLE box_handles[] = {g_dump_box_done_event, g_dump_worker_thread};
    WaitForMultipleObjects(2, box_handles, FALSE, 120000);
  } else if (report_written) {
    // No box: a short grace so the log's tee thread can drain before the process ends.
    Sleep(200);
  }
}

LONG WINAPI on_exception(EXCEPTION_POINTERS* e) {
  request_crash_report(e, CrashReportCause::exception);
  return EXCEPTION_EXECUTE_HANDLER;
}

// abort() never reaches the SEH filter: the CRT raises SIGABRT and exits with 3.
void on_abort(int) {
  // The UCRT resets SIGABRT to the default action before calling this, so a second abort() would
  // bypass the guard: install the handler again first.
  std::signal(SIGABRT, on_abort);
  request_crash_report(nullptr, CrashReportCause::aborted);
  TerminateProcess(GetCurrentProcess(), 3);  // not _exit: see on_terminate
  for (;;) Sleep(1000);
}

#else

char g_exe[PATH_MAX] = "";
char g_stack[64 * 1024];  // a stack overflow's handler needs its own

void put(const char* s) {
  ssize_t ignored = write(2, s, std::strlen(s));
  (void)ignored;
}

void append(char* to, size_t size, const char* s) {
  size_t n = std::strlen(to);
  while (*s && n + 1 < size) to[n++] = *s++;
  to[n] = 0;
}

const char* signal_name(int sig) {
  switch (sig) {
    case SIGSEGV: return "segmentation fault";
    case SIGBUS: return "bus error, its files gone or unreadable";
    case SIGFPE: return "arithmetic error";
    case SIGILL: return "illegal instruction";
    case SIGABRT: return "aborted";
  }
  return "signal";
}

// Only what is safe in a signal handler: write, fork, exec, raise. SA_RESETHAND:
// the raise ends the program by the signal, as without this.
void on_signal(int sig) {
  static char text[1200];
  put(g_program), put(": crashed: "), put(signal_name(sig)), put("\n");
#ifdef MW3_HAVE_BACKTRACE
  void* frames[48];
  backtrace_symbols_fd(frames, backtrace(frames, 48), 2);
#endif
  usleep(100000);  // the log's thread passes this on (run_log.cpp)
  if (g_test) _exit(70);
  if (g_box && g_exe[0] && fork() == 0) {
    setsid();  // on its own: the box stays after the game's window has gone
    text[0] = 0;
    append(text, sizeof text, "MechWarrior 3 crashed (");
    append(text, sizeof text, signal_name(sig));
    append(text, sizeof text, ")");
    append(text, sizeof text, g_tail);
    char flag[] = "--crash-box";
    char* argv[] = {g_exe, flag, text, nullptr};
    execv(g_exe, argv);
    _exit(127);
  }
  raise(sig);
}

void own_path() {
#if defined(__APPLE__)
  uint32_t size = sizeof g_exe;
  if (_NSGetExecutablePath(g_exe, &size) != 0) g_exe[0] = 0;
#else
  const ssize_t n = readlink("/proc/self/exe", g_exe, sizeof g_exe - 1);
  g_exe[n > 0 ? n : 0] = 0;
#endif
}

#endif

}  // namespace

bool crash_report_dump_prerequisites_present() {
#if defined(_WIN32)
  HMODULE dbghelp = LoadLibraryA("dbghelp.dll");
  if (!dbghelp) return false;
  const bool present = GetProcAddress(dbghelp, "MiniDumpWriteDump") != nullptr;
  FreeLibrary(dbghelp);
  return present;
#else
  return false;
#endif
}

void crash_report_fail_worker_start_for_test(bool fail) {
#if defined(_WIN32)
  g_fail_worker_start_for_test = fail;
#else
  (void)fail;
#endif
}

bool crash_report_dump_worker_ready() {
#if defined(_WIN32)
  return g_dump_worker_available;
#else
  return false;
#endif
}

#if defined(_WIN32)
bool crash_report_store_capture_for_test(const EXCEPTION_POINTERS* exception, bool* has_record,
                                         bool* has_context) {
  if (!g_installed || !has_record || !has_context) return false;
  store_capture(exception, exception ? CrashReportCause::exception : CrashReportCause::aborted);
  *has_record = g_dump_exception_pointers.ExceptionRecord != nullptr;
  *has_context = g_dump_exception_pointers.ContextRecord != nullptr;
  return true;
}

bool crash_report_uninstall_for_test() {
  if (!g_installed) return true;
  if (GetCurrentThreadId() != g_installing_thread_id || g_exception_in_progress.load())
    return false;
  // Restore the process handlers first so nothing can enter the worker while it is closed.
  SetUnhandledExceptionFilter(g_previous_exception_filter);
  std::signal(SIGABRT, g_previous_abort_handler);
  std::set_terminate(g_previous_terminate_handler);
  if (g_dump_worker_thread) {
    g_dump_worker_stopping.store(true);
    if (!SetEvent(g_dump_request_event) ||
        WaitForSingleObject(g_dump_worker_thread, 5000) != WAIT_OBJECT_0)
      return false;
    CloseHandle(g_dump_worker_thread);
    CloseHandle(g_dump_request_event);
    CloseHandle(g_dump_complete_event);
    if (g_dump_box_done_event) CloseHandle(g_dump_box_done_event);
  }
  if (g_stderr_handle != nullptr && g_stderr_handle != INVALID_HANDLE_VALUE)
    CloseHandle(g_stderr_handle);
  g_stderr_handle = INVALID_HANDLE_VALUE;
  g_dump_box_done_event = nullptr;
  // Production keeps dbghelp loaded. Tests release it only after the worker is joined.
  if (g_dbghelp) FreeLibrary(g_dbghelp);
  g_dbghelp = nullptr;
  g_write_dump = nullptr;
  g_dump_worker_thread = nullptr;
  g_dump_request_event = nullptr;
  g_dump_complete_event = nullptr;
  g_dump_worker_thread_id = 0;
  g_dump_worker_available = false;
  g_dump_worker_stopping.store(false);
  g_dump_worker_failed.store(false);
  g_dump_exception_pointers = {};
  g_dump_exception_record = {};
  g_dump_context = {};
  // Per-crash state: a later install starts from a clean guard.
  g_exception_in_progress.store(false);
  g_installed = false;
  return true;
}
#endif

void crash_report_install(const std::string& program, const std::string& log, bool box) {
#if defined(_WIN32)
  if (g_installed) return;
#endif
  set_text(program, log);
  g_box = box && !std::getenv("MW3_LAUNCHER_WATCHES");
  g_test = std::getenv("MW3_CRASH_TEST") != nullptr;
#if defined(_WIN32)
  g_installing_thread_id = GetCurrentThreadId();
  g_exception_in_progress.store(false);
  // The crash lines go to their own file next to crash.dmp, opened now for append. The run log
  // reopens mw3.log without append and a late crash could write into a recycled stderr handle, so
  // neither can be trusted to keep these lines. The normal log gets one pointer line here.
  char crash_text_path[MAX_PATH + 16];
  if (crash_report_sibling_path(log.c_str(), "crash.txt", crash_text_path,
                                sizeof crash_text_path)) {
    g_stderr_handle = CreateFileA(crash_text_path, FILE_APPEND_DATA,
                                  FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
                                  OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    const DWORD open_error = GetLastError();
    if (g_stderr_handle == INVALID_HANDLE_VALUE)
      std::fprintf(stderr, "%s: crash report file could not be opened (error %lu): %s\n",
                   g_program, open_error, crash_text_path);
    else
      std::fprintf(stderr, "%s: crash details, if any, are written to %s\n", g_program,
                   crash_text_path);
  } else {
    std::fprintf(stderr, "%s: crash report file path does not fit; no crash text file\n",
                 g_program);
  }
  // SetThreadStackGuarantee applies to this thread only: production installs on the main/game
  // thread. Other threads still use the same minimal handoff, but need their own guarantee.
  ULONG stack_guarantee = 64 * 1024;
  if (!SetThreadStackGuarantee(&stack_guarantee))
    crash_log("%s: could not reserve exception handler stack\n", g_program);
  crash_report_dump_path(log.c_str(), g_dump_path, sizeof g_dump_path);
  HMODULE executable = GetModuleHandle(nullptr);
  if (executable) {
    const auto* dos_header = reinterpret_cast<const IMAGE_DOS_HEADER*>(executable);
    if (dos_header->e_magic == IMAGE_DOS_SIGNATURE && dos_header->e_lfanew > 0) {
      const auto* nt_headers = reinterpret_cast<const IMAGE_NT_HEADERS*>(
          reinterpret_cast<const unsigned char*>(executable) + dos_header->e_lfanew);
      if (nt_headers->Signature == IMAGE_NT_SIGNATURE &&
          nt_headers->OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR_MAGIC) {
        g_module_base = reinterpret_cast<uintptr_t>(executable);
        g_module_image_size = nt_headers->OptionalHeader.SizeOfImage;
      }
    }
  }
  g_dbghelp = LoadLibraryA("dbghelp.dll");
  if (g_dbghelp) {
    g_write_dump = reinterpret_cast<MiniDumpWriteDumpFunction>(
        GetProcAddress(g_dbghelp, "MiniDumpWriteDump"));
  }
  // Even without dbghelp, use the independent stack for diagnostics and the message box.
  start_dump_worker();
  if (!g_dump_worker_available) {
    // Without the worker every crash request would return at once and the process would crash
    // silently under our handlers. Keep whatever handlers were there instead; the failure was
    // logged once above.
    std::fprintf(stderr, "%s: crash reporting not installed (no dump worker); previous handlers kept\n",
                 g_program);
    if (g_stderr_handle != nullptr && g_stderr_handle != INVALID_HANDLE_VALUE)
      CloseHandle(g_stderr_handle);
    g_stderr_handle = INVALID_HANDLE_VALUE;
    // Nothing will use dbghelp: free it so a later install does not leak a second reference.
    if (g_dbghelp) FreeLibrary(g_dbghelp);
    g_dbghelp = nullptr;
    g_write_dump = nullptr;
    return;
  }
  g_previous_exception_filter = SetUnhandledExceptionFilter(on_exception);
  g_previous_abort_handler = std::signal(SIGABRT, on_abort);
  g_previous_terminate_handler = std::set_terminate(on_terminate);
  g_installed = true;
#else
  std::set_terminate(on_terminate);
  own_path();
#ifdef MW3_HAVE_BACKTRACE
  void* first[1];
  backtrace(first, 1);  // loads what it needs now, not in the handler
#endif
  stack_t alt{};
  alt.ss_sp = g_stack, alt.ss_size = sizeof g_stack;
  sigaltstack(&alt, nullptr);
  struct sigaction sa {};
  sa.sa_handler = on_signal;
  sa.sa_flags = SA_ONSTACK | SA_RESETHAND;
  sigemptyset(&sa.sa_mask);
  for (int sig : {SIGSEGV, SIGBUS, SIGFPE, SIGILL, SIGABRT}) sigaction(sig, &sa, nullptr);
#endif
  if (g_test) {
    if (std::strcmp(std::getenv("MW3_CRASH_TEST"), "abort") == 0) std::abort();
#if defined(_WIN32)
    volatile int* nothing = nullptr;  // the CRT's raise(SIGSEGV) never reaches the filter
    *nothing = 0;
#else
    std::raise(SIGSEGV);
#endif
  }
}

bool crash_box_main(int argc, char** argv) {
  if (argc != 3 || std::strcmp(argv[1], "--crash-box") != 0) return false;
  SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "MechWarrior 3", argv[2], nullptr);
  return true;
}

void fatal_box(const std::string& message, bool hidden) {
  log::line(log::Level::error, "mw3: %s\n", message.c_str());
  if (!hidden && !SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "MechWarrior 3", message.c_str(), nullptr))
    std::fprintf(stderr, "mw3: no message box either: %s\n", SDL_GetError());
}

}  // namespace sdlfe
