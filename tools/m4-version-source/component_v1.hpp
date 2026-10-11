#pragma once
#include "runtime.hpp"
#include "session.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <memory>
#include <span>
#include <string_view>
namespace mw34::m4_version_native {
using Sink=void(*)(std::string_view,std::span<const std::byte>,void*);
struct alignas(16) HostBoundary {std::array<std::byte,1632>bytes{};};
class Component {
 public:struct Impl;
 private:std::unique_ptr<Impl>impl_;
 public:Component(m4_runtime::Runtime&,m4_onexit::Session&,std::string_view independent_before_domain_sha,Sink,void*);~Component();Component(const Component&)=delete;Component&operator=(const Component&)=delete;
 void execute(HostBoundary&);void checkpoint(std::string_view);static void entry(m4_runtime::Runtime&);
};
}
