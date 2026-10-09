#pragma once
#include "runtime.hpp"
#include <cstdint>
#include <span>
#include <memory>
#include <array>
#include <string_view>
#include <remill/Arch/X86/Runtime/State.h>
namespace mw34::m4_onexit {
using Sink=void(*)(std::string_view,std::span<const std::byte>,void*);
struct SessionImpl;
class Session {
 std::unique_ptr<SessionImpl> impl_;
 public:
 Session(m4_runtime::Runtime&,std::span<const std::byte>);
 ~Session() noexcept;
 Session(const Session&)=delete;Session&operator=(const Session&)=delete;
 void bootstrap();void enter(unsigned root);void replay(unsigned root,unsigned marker=0xffffffa0);
 void finish();void dump(Sink,void*)const;
 // Summary word 15 is the currently live native heap handle; cleanup makes it
 // zero. Historical acquisition remains in the inherited owner/API witnesses.
 std::array<std::uint64_t,32>summary()const noexcept;
 std::span<const std::array<std::uint64_t,32>>growth_witnesses()const noexcept;
 void(*test_hook)(Session&,unsigned){};
 void*token()const noexcept;
 m4_runtime::Runtime& runtime()const noexcept;bool live_handle()const noexcept;
};
bool active()noexcept;
std::uint64_t read(void*,unsigned,unsigned);void*write(void*,unsigned,std::uint64_t,unsigned);
void*called(void*,State*,unsigned);void*returned(void*,State*,unsigned);void*missing(void*,State*,unsigned);
unsigned char undefined();
}
