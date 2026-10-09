#include "context.hpp"
using namespace mw34::m4_integer_startup;
extern "C" std::uint32_t mw34_integer_read32(void *m,std::uint32_t a){return static_cast<Context *>(m)->read32(a);}
extern "C" void *mw34_integer_write32(void *m,std::uint32_t a,std::uint32_t v){static_cast<Context *>(m)->write32(a,v);return m;}
extern "C" void *mw34_integer_write8(void *m,std::uint32_t a,std::uint8_t v){static_cast<Context *>(m)->write8(a,v);return m;}
extern "C" void *mw34_integer_return(State *s,std::uint32_t pc,void *m){return static_cast<Context *>(m)->returned(*s,pc);}
extern "C" void *mw34_integer_tail_enter(State *s,std::uint32_t pc,void *m){return static_cast<Context *>(m)->tail(*s,pc);}
