#pragma once
#include "runtime.hpp"
#include "session.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <cstddef>
#include <memory>
#include <span>
#include <string_view>
namespace mw34::m4_constructor_native {
using Sink=void(*)(std::string_view,std::span<const std::byte>,void*);
struct alignas(16) HostBoundary {std::array<std::byte,1632>bytes{};};
class Component final {
 public:struct Impl;
 private:std::unique_ptr<Impl>impl_;
 public:
 Component(m4_runtime::Runtime&,m4_onexit::Session&,std::string_view current_before_gate,Sink,void*);
 ~Component();Component(const Component&)=delete;Component&operator=(const Component&)=delete;
 void execute(unsigned,HostBoundary&);void borrow_entry(unsigned,HostBoundary&);void checkpoint(std::string_view);
 static void entry_4103f0(m4_runtime::Runtime&);
 static void entry_410440(m4_runtime::Runtime&);
 static void entry_459b40(m4_runtime::Runtime&);
};
}
