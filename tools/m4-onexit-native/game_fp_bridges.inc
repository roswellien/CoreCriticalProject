
extern "C" float mw34_onexit_game_readf32(void*p,unsigned a){const auto value=unsigned(mw34::m4_onexit::read(p,a,4));float result;std::memcpy(&result,&value,4);return result;}
extern "C" double mw34_onexit_game_readf64(void*p,unsigned a){const auto value=mw34::m4_onexit::read(p,a,8);double result;std::memcpy(&result,&value,8);return result;}
extern "C" void*mw34_onexit_game_writef32(void*p,unsigned a,float v){unsigned bits;std::memcpy(&bits,&v,4);return mw34::m4_onexit::write(p,a,bits,4);}
extern "C" void*mw34_onexit_game_writef64(void*p,unsigned a,double v){std::uint64_t bits;std::memcpy(&bits,&v,8);return mw34::m4_onexit::write(p,a,bits,8);}
extern "C" void mw34_onexit_game_fpu_clear(unsigned mask){if(!mw34::m4_onexit::active()||mask!=127)throw std::runtime_error("Exact active literal x87 primitive exception clear");__asm__ volatile("fnclex":::"memory");}
extern "C" unsigned mw34_onexit_game_fpu_test(unsigned mask){if(!mw34::m4_onexit::active()||mask!=127)throw std::runtime_error("Exact active literal x87 primitive exception test");unsigned short status;__asm__ volatile("fnstsw %0":"=m"(status)::"memory");return status&mask;}
extern "C" void mw34_onexit_game_fsqrt_raw80(const void*input,void*result){if(!mw34::m4_onexit::active()||!result||!input)throw std::runtime_error("Active raw80 literal FSQRT scratch");__asm__ volatile("fldt (%1)\n\tfsqrt\n\tfstpt (%0)"::"r"(result),"r"(input):"memory","st");}
