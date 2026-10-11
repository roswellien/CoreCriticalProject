#pragma once
#include "runtime.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <span>
#include <string_view>

namespace mw34::m4_widget_native {
using m4_runtime::Runtime;
using Sink = void (*)(std::string_view, std::span<const std::byte>, void *);
struct Import { unsigned pc{}, slot{}, raw{}, projected{}; };
struct SourceCall { unsigned root{}, site{}, target{}, frame{}, return_pc{}; bool tail{}; };

// The persistent registry/CRT implementation supplies these actual services.
// No original return values, allocation bytes, GDI handles, or AFTER State are
// accepted by this interface. The implementation is independently admitted.
class Services {
 public:
  virtual ~Services() = default;
  virtual Runtime &runtime() noexcept = 0;
  virtual void authority() = 0;
  virtual unsigned resolve_import(const Import &) = 0;
  virtual void invoke(State &, const SourceCall &) = 0;
};

struct Inputs {
  // Current own-branch raw IAT cells, not an original observer address.
  std::array<Import, 7> imports{};
  // A caller must authenticate its complete BEFORE mappings and permissions.
  // This library verifies source bytes, but cannot query GuestMemory rights.
  std::string_view before_domain_gate_sha256;
};

struct alignas(16) HostBoundary { std::array<std::byte, 1632> bytes{}; };
struct alignas(16) ApiSide {
  std::uint64_t rax{}, rcx{}, rdx{}, rflags{};
  std::array<std::byte, 512> fx{};
  std::array<std::byte, 28> env{};
  std::array<std::byte, 4> padding{};
};
struct alignas(16) ApiHardware { ApiSide before, after; };
static_assert(sizeof(ApiSide)==576 && sizeof(ApiHardware)==1152);

class Component final {
 public:
  struct Impl;
 private:
  std::unique_ptr<Impl> impl_;
 public:
  Component(Runtime &, Services &, const Inputs &, Sink, void *);
  ~Component();
  Component(const Component &) = delete;
  Component &operator=(const Component &) = delete;
  Runtime &runtime() noexcept;
  void authority();
  // Called from the current registered Runtime route with its committed frame.
  // Source and host hardware records are emitted separately.
  void execute(unsigned root, HostBoundary &);
  void cleanup_fonts(HostBoundary &);
  void checkpoint(std::string_view);
  // Seven explicit callbacks; caller binds physical evidence before registering.
  static void entry_40e250(Runtime &);
  static void entry_40ef50(Runtime &);
  static void entry_5a3c30(Runtime &);
  static void entry_5a3ff0(Runtime &);
  static void entry_5a66f0(Runtime &);
  static void entry_479590(Runtime &);
  static void entry_40f000(Runtime &);
};
} // namespace mw34::m4_widget_native
