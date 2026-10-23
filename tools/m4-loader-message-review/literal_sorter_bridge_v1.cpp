#include "literal_owner_v1.hpp"
#include <cstring>
#include <stdexcept>
using mw34_message_literal::Owner;
using mw34_message_literal::State;
namespace {
thread_local Owner* active=nullptr;
Owner& own(void*memory) {
 if(!active || memory!=active)throw std::logic_error("Exact exclusive live literal owner");return *active;
}
std::uint32_t sourcePC(Owner& owner) {
 std::uint32_t pc;std::memcpy(&pc,owner.state().bytes+2472,4);return pc;
}
}
extern "C" void* mw34_message_literal_f_10001000_body(State*,std::uint32_t,void*);
extern "C" void* mw34_message_literal_f_10001740_body(State*,std::uint32_t,void*);
extern "C" std::uint32_t __remill_read_memory_32(void*m,std::uint32_t a){return own(m).read(a,4);}
extern "C" std::uint8_t __remill_read_memory_8(void*m,std::uint32_t a){return static_cast<std::uint8_t>(own(m).read(a,1));}
extern "C" void* __remill_write_memory_32(void*m,std::uint32_t a,std::uint32_t v){own(m).write(a,v,4);return m;}
extern "C" void* __remill_function_return(State*s,std::uint32_t pc,void*m){auto&o=own(m);if(s!=&o.state())throw std::logic_error("Current complete State owner");o.literal_return(s,pc);return m;}
extern "C" std::uint8_t mw34_message_literal_f_10001000_undefined_8(){if(!active)throw std::logic_error("Undefined outside literal scope");active->undefined_flag("f_10001000",sourcePC(*active));return 0;}
extern "C" std::uint8_t mw34_message_literal_f_10001740_undefined_8(){if(!active)throw std::logic_error("Undefined outside literal scope");active->undefined_flag("f_10001740",sourcePC(*active));return 0;}
extern "C" void* sub_10001740(State*s,std::uint32_t pc,void*m) {
 auto&o=own(m);if(pc!=0x10001740||s!=&o.state())throw std::logic_error("Physical helper entry");
 o.enter_helper(pc);try { auto*r=mw34_message_literal_f_10001740_body(s,pc,m);o.leave_helper();return r; }catch(...){o.leave_helper();throw;}
}
bool mw34_message_literal::run_sort(TableView table) {
 if(active||!table.native||table.source!=0x10003010||table.bytes!=1577*8)throw std::logic_error("Whole exact source/native1577 table");
 auto*o=MW34MessageCurrentLiteralOwner();if(!o)return false;
 o->begin_literal_sort(table);active=o;
 try { auto*r=mw34_message_literal_f_10001000_body(&o->state(),0x10001000,o);if(r!=o)throw std::logic_error("Literal memory identity");o->finish_literal_sort(table);active=nullptr;return true; }
 catch(...){active=nullptr;throw;}
}
