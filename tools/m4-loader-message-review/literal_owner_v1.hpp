#pragma once
#include <cstddef>
#include <cstdint>
namespace mw34_message_literal {
// Exact compiled Remill layout, independently pinned by helper-lifts-r2.
struct alignas(8) State { unsigned char bytes[3504]; };
static_assert(sizeof(State)==3504 && alignof(State)==8);
struct TableView { void* native;std::uint32_t source;std::size_t bytes; };
// Implementation belongs to a reviewed owning host backplane. No default
// bootstrap, call frame, imported CRT value or API result is supplied here.
class Owner {
public:
 virtual State& state()=0;
 virtual void begin_literal_sort(TableView)=0;
 virtual std::uint32_t read(std::uint32_t address,unsigned width)=0;
 virtual void write(std::uint32_t address,std::uint32_t value,unsigned width)=0;
 virtual void enter_helper(std::uint32_t pc)=0;
 virtual void leave_helper()=0;
 virtual void literal_return(State*,std::uint32_t pc)=0;
 virtual void undefined_flag(const char* body,std::uint32_t sourcePC)=0;
 virtual void finish_literal_sort(TableView)=0;
 virtual ~Owner()=default;
};
// Must bind same live Context/thread/module generation, current State/FX,
// exact source10001710 CALL/return10001715 and whole source/native table alias.
// Host must arrange this bridge before actual LoadLibrary/DllMain. DLL cannot
// bootstrap itself from a synthetic State or install it after process_attach.
extern "C" Owner* MW34MessageCurrentLiteralOwner();
bool run_sort(TableView);
}
