#include "execution.hpp"
using namespace mw34::m4_initializer_chain;
extern "C" std::uint32_t __remill_read_memory_32(void *token,std::uint32_t address){return static_cast<Context *>(token)->read32(address);}
extern "C" void *__remill_write_memory_32(void *token,std::uint32_t address,std::uint32_t value){static_cast<Context *>(token)->write32(address,value);return token;}
extern "C" void *mw34_chain_enter_callee(State *s,std::uint32_t pc,void *token){return static_cast<Context *>(token)->callee(*s,pc);}
extern "C" void *__remill_write_memory_8(void *token,std::uint32_t address,std::uint8_t value){static_cast<Context *>(token)->write8(address,value);return token;}
extern "C" void *__remill_function_return(State *s,std::uint32_t pc,void *token){return static_cast<Context *>(token)->returned(*s,pc);}

