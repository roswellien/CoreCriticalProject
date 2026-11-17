#include "frontend/sdl/crash_report.h"

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
  return length > 0 ? static_cast<size_t>(length) : 0;
}

namespace {

char g_program[64] = "mw3";
char g_tail[1024] = "";  // the box's text after the reason
#if defined(_WIN32)
char g_crash_line[2048];
char g_dump_path[MAX_PATH + 16];
char g_crash_text[1200];
char g_crash_reason[32];
char g_rva_text[64];
volatile LONG g_exception_in_progress = 0;
HANDLE g_stderr_handle = INVALID_HANDLE_VALUE;
using MiniDumpWriteDumpFunction = BOOL(WINAPI*)(HANDLE, DWORD, HANDLE, MINIDUMP_TYPE,
                                                PMINIDUMP_EXCEPTION_INFORMATION,
                                                PMINIDUMP_USER_STREAM_INFORMATION,
                                                PMINIDUMP_CALLBACK_INFORMATION);
MiniDumpWriteDumpFunction g_write_dump = nullptr;
uintptr_t g_module_base = 0;
size_t g_module_image_size = 0;

void crash_log(const char* format, ...) {
  va_list arguments;
  va_start(arguments, format);
  const int length = std::vsnprintf(g_crash_line, sizeof g_crash_line, format, arguments);
  va_end(arguments);
  if (length <= 0) return;
  if (g_stderr_handle == nullptr || g_stderr_handle == INVALID_HANDLE_VALUE) return;
  DWORD written = 0;
  if (!WriteFile(g_stderr_handle, g_crash_line,
                 static_cast<DWORD>(length < static_cast<int>(sizeof g_crash_line)
                                        ? length
                                        : sizeof g_crash_line - 1),
                 &written, nullptr))
    return;
}

char g_log[1024] = "";
#endif
bool g_box = false;
bool g_test = false;

void set_text(const std::string& program, const std::string& log) {
  std::snprintf(g_program, sizeof g_program, "%s", program.c_str());
  std::snprintf(g_tail, sizeof g_tail, ".\n\nThe log is %s\nPlease include it if you report this.", log.c_str());
#if defined(_WIN32)
  std::snprintf(g_log, sizeof g_log, "%s", log.c_str());
#endif
}

[[noreturn]] void on_terminate() {
  const char* what = "";
  try {
    if (auto e = std::current_exception()) std::rethrow_exception(e);
  } catch (const std::exception& e) {
    what = e.what();
  } catch (...) {
  }
  std::fprintf(stderr, "%s: uncaught exception: %s\n", g_program, what);
  std::abort();  // the crash's report from here
}

#if defined(_WIN32)

void say_crash(const char* reason) {
  Sleep(100);  // the log's thread passes this on (run_log.cpp)
  if (g_test) _exit(70);
  std::snprintf(g_crash_text, sizeof g_crash_text, "MechWarrior 3 crashed (%s)%s", reason,
                g_tail);
  // Topmost: with no owner it could open behind a fullscreen game.
  if (g_box)
    MessageBoxA(nullptr, g_crash_text, "MechWarrior 3",
                MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND);
}

LONG WINAPI on_exception(EXCEPTION_POINTERS* e) {
  if (InterlockedCompareExchange(&g_exception_in_progress, 1, 0) != 0)
    return EXCEPTION_EXECUTE_HANDLER;
  if (e && e->ExceptionRecord) {
    const auto exception_address = reinterpret_cast<uintptr_t>(e->ExceptionRecord->ExceptionAddress);
    uintptr_t rva = 0;
    const bool inside_image = crash_report_address_rva(g_module_base, g_module_image_size,
                                                        exception_address, &rva);
    crash_report_format_rva(g_rva_text, sizeof g_rva_text, inside_image, rva);
    crash_log("%s: crashed: exception 0x%08lx at %p module base %p %s\n", g_program,
              e->ExceptionRecord->ExceptionCode, e->ExceptionRecord->ExceptionAddress,
              reinterpret_cast<void*>(g_module_base), g_rva_text);
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

    g_dump_path[0] = '\0';
    if (g_log[0]) {
      std::snprintf(g_dump_path, sizeof g_dump_path, "%s", g_log);
      char* separator = std::strrchr(g_dump_path, '\\');
      char* slash = std::strrchr(g_dump_path, '/');
      if (slash && (!separator || slash > separator)) separator = slash;
      if (separator) separator[1] = '\0';
      else g_dump_path[0] = '\0';
    }
    const size_t directory_length = std::strlen(g_dump_path);
    if (directory_length + sizeof("crash.dmp") <= sizeof g_dump_path) {
      std::memcpy(g_dump_path + directory_length, "crash.dmp", sizeof("crash.dmp"));
      crash_log("%s: minidump path: %s\n", g_program, g_dump_path);
      if (g_write_dump) {
        HANDLE file = CreateFileA(g_dump_path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                                  FILE_ATTRIBUTE_NORMAL, nullptr);
        if (file != INVALID_HANDLE_VALUE) {
          MINIDUMP_EXCEPTION_INFORMATION exception_info{};
          exception_info.ThreadId = GetCurrentThreadId();
          exception_info.ExceptionPointers = e;
          exception_info.ClientPointers = FALSE;
          if (g_write_dump(GetCurrentProcess(), GetCurrentProcessId(), file, MiniDumpNormal,
                           &exception_info, nullptr, nullptr))
            crash_log("%s: minidump: %s\n", g_program, g_dump_path);
          else
            crash_log("%s: minidump failed: %s\n", g_program, g_dump_path);
          CloseHandle(file);
        } else {
          crash_log("%s: could not create minidump: %s\n", g_program, g_dump_path);
        }
      } else {
        crash_log("%s: dbghelp unavailable for minidump\n", g_program);
      }
    }
  } else {
    crash_log("%s: crashed: exception details unavailable\n", g_program);
  }
  std::snprintf(g_crash_reason, sizeof g_crash_reason, "exception 0x%08lx",
                e && e->ExceptionRecord ? e->ExceptionRecord->ExceptionCode : 0ul);
  say_crash(g_crash_reason);
  return EXCEPTION_EXECUTE_HANDLER;
}

// abort() (an uncaught exception's end too) never reaches the filter above: the
// CRT raises this and exits with 3.
void on_abort(int) {
  crash_log("%s: crashed: aborted\n", g_program);
  say_crash("aborted");
  _exit(3);
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

void crash_report_install(const std::string& program, const std::string& log, bool box) {
  set_text(program, log);
  g_box = box && !std::getenv("MW3_LAUNCHER_WATCHES");
  g_test = std::getenv("MW3_CRASH_TEST") != nullptr;
  std::set_terminate(on_terminate);
#if defined(_WIN32)
  g_stderr_handle = GetStdHandle(STD_ERROR_HANDLE);
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
  if (HMODULE dbghelp = LoadLibraryA("dbghelp.dll")) {
    g_write_dump = reinterpret_cast<MiniDumpWriteDumpFunction>(
        GetProcAddress(dbghelp, "MiniDumpWriteDump"));
  }
  SetUnhandledExceptionFilter(on_exception);
  std::signal(SIGABRT, on_abort);
#else
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
  std::fprintf(stderr, "mw3: %s\n", message.c_str());
  if (!hidden && !SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "MechWarrior 3", message.c_str(), nullptr))
    std::fprintf(stderr, "mw3: no message box either: %s\n", SDL_GetError());
}

}  // namespace sdlfe
