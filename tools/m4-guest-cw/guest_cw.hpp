#pragma once
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
namespace mw34::m4_guest_cw {
enum class Fault {none,wrong_state,unsupported_state,operand_bounds,memory_access};
// Restricted transfer domain measured on the hardware corpus: SW0/TOP0,
// empty physical tags, guest MXCSR1F80, normalized existing CW. Does not admit
// numerical operations, occupied stacks or pending exception dispatch.
class Context {
 public:
  Context(GuestMemory &memory,State &state,std::span<std::byte,512> fx,GuestAddress begin,std::uint32_t bytes);
  bool store(State *state,GuestAddress address) noexcept;
  bool load(State *state,GuestAddress address) noexcept;
  [[nodiscard]] Fault fault()const noexcept{return fault_;}
  [[nodiscard]] GuestAddress fault_address()const noexcept{return fault_address_;}
  static constexpr std::uint16_t normalized(std::uint16_t word){return (word&0x1f3fU)|0x40U;}
 private:
  GuestMemory &memory_;State &state_;std::span<std::byte,512> fx_;GuestAddress begin_;std::uint32_t bytes_;Fault fault_{};GuestAddress fault_address_{};
  bool admit(State *state,GuestAddress address) noexcept;
  bool deny(Fault fault,GuestAddress address)noexcept;
};
}
extern "C" void *mw34_m4_guest_fnstcw(State *,std::uint32_t,void *) noexcept;
extern "C" void *mw34_m4_guest_fldcw(State *,std::uint32_t,void *) noexcept;
