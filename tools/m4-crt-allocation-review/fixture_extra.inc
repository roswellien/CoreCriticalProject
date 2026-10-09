// Fresh independent authored observer/control effects; never API response injection.
namespace {
unsigned review_case{},review_hook_hits{},review_checks{},review_token_units{},review_thread_units{};
void review_check(bool ok,const char*why){++review_checks;require(ok,why);}
void review_seed(std::array<std::byte,512>&fx,std::array<std::byte,28>&env){
 struct alignas(16) H{std::array<std::byte,512>fx;std::array<std::byte,28>env;};H old{},rich{};
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(old.fx),"=m"(old.env)::"memory");
 unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;
 __asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(rich.fx),"=m"(rich.env)::"memory");
 __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(old.fx),"m"(old.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 fx=rich.fx;env=rich.env;
}
void review_hook(al::Binding&b,unsigned point){
 if(!b.control&&point==31){
  review_check(b.known_allocation()!=0&&b.known_handle()!=0,"Actual full-width owned host resources reached genuine malloc return");
  review_check((b.known_allocation()&15)==0,"Measured native allocation alignment");
  review_check(b.allocation_token_valid(al::allocation_address)&&!b.allocation_token_valid(al::allocation_address+4),"Private guest allocation token denies interior alias");
  review_check(b.token_valid(al::token)&&!b.token_valid(al::token+1),"Private heap token denies forged alias");review_token_units+=2;
  if(review_case==0){bool denied=false;std::thread other([&](){try{(void)al::current(&b,al::allocation_address);}catch(const std::invalid_argument&){denied=true;}});other.join();review_check(denied,"Wrong-thread private authority denied before host API");++review_thread_units;}
 }
 auto modify=[&](unsigned address,unsigned value){auto base=address&~4095U;b.runtime.memory().protect({base},Permissions::read|Permissions::write);b.runtime.memory().store<unsigned>({address},value);};
 if(b.control==1001&&point==26){++review_hook_hits;b.runtime.memory().map({al::allocation_address},4096,Permissions::read|Permissions::write);}
 if(b.control==1002&&point==26){++review_hook_hits;modify(al::alloc_iat,al::alloc_raw^1);}
 if(b.control==1003&&point==34){++review_hook_hits;modify(al::free_iat,al::free_raw^1);}
 if(b.control==1004&&point==28){++review_hook_hits;b.runtime.memory().store<unsigned>({b.state.gpr.rsp.dword},al::alloc_return^1);}
 if(b.control==1005&&point==34){++review_hook_hits;b.runtime.memory().store<unsigned>({b.state.gpr.rsp.dword},al::free_return^1);}
 if(b.control==1006&&point==27){++review_hook_hits;b.allocation_registry[4]^=std::uint64_t(1)<<32;}
 if(b.control==1007&&point==26){++review_hook_hits;b.registry[4]^=std::uint64_t(1)<<32;}
 if(b.control==1008&&point==28){++review_hook_hits;auto v=b.runtime.memory().load<unsigned>({al::allocation_address});b.runtime.memory().store<unsigned>({al::allocation_address},v^1);}
 if(b.control==1009&&point==32){++review_hook_hits;b.runtime.memory().protect({al::allocation_address},Permissions::write);}
 if(b.control==1010&&point==25){++review_hook_hits;modify(al::malloc_entry,0);}
 if(b.control==1011&&point==34){++review_hook_hits;auto bad=reinterpret_cast<void*>(reinterpret_cast<std::uintptr_t>(&b)+8);(void)al::current(bad,al::free_iat);}
 if(b.control==1012&&point==31){++review_hook_hits;b.allocation_guest^=4;}
}
}
