// Private diagnostic sampler; reused from the whole-frame profiler.
struct HostProfiler {
 unsigned from{};std::thread t;std::atomic<bool> stop{};std::string path;HANDLE main{};
 struct Sample {unsigned frame{}, guest_pc{};std::array<std::uint64_t,16> stack{};};
 std::vector<Sample> samples;
 void start(const char* p){path=p;mw34_profile_main_thread=::GetCurrentThreadId();::DuplicateHandle(::GetCurrentProcess(),::GetCurrentThread(),::GetCurrentProcess(),&main,0,FALSE,DUPLICATE_SAME_ACCESS);
 t=std::thread([this]{HANDLE timer=::CreateWaitableTimerExW(nullptr,nullptr,CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,TIMER_ALL_ACCESS);
  while(!stop){if(timer){LARGE_INTEGER due{};due.QuadPart=-10000;::SetWaitableTimer(timer,&due,0,nullptr,nullptr,FALSE);::WaitForSingleObject(timer,INFINITE);}else ::Sleep(1);
   const unsigned frame=mw34_frames_presented.load(std::memory_order_relaxed);
   if(frame<std::max(from,1200U)||frame>=2700||samples.size()>=100000)continue;
   if(::SuspendThread(main)==DWORD(-1))break;
   CONTEXT context{};context.ContextFlags=CONTEXT_FULL;Sample sample{};sample.frame=frame;
   if(::GetThreadContext(main,&context)){if(auto*s=mw34_profile_state.load())sample.guest_pc=s->gpr.rip.dword;
    const auto start=context.Rsp;
    for(unsigned i=0;i<sample.stack.size()&&context.Rip;++i){sample.stack[i]=context.Rip;DWORD64 base=0;auto* entry=::RtlLookupFunctionEntry(context.Rip,&base,nullptr);
     const auto previous=context.Rsp;
     if(entry){void* handler{};DWORD64 establisher{};::RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,context.Rip,entry,&context,&handler,&establisher,nullptr);}
     else {DWORD64 address{};SIZE_T bytes{};if(!::ReadProcessMemory(::GetCurrentProcess(),reinterpret_cast<void*>(context.Rsp),&address,8,&bytes)||bytes!=8)break;context.Rip=address;context.Rsp+=8;}
     if(context.Rsp<=previous||context.Rsp>start+1024*1024)break;
    }
   }
   ::ResumeThread(main);if(sample.stack[0])samples.push_back(sample);
  }if(timer)::CloseHandle(timer);
 });}
 ~HostProfiler(){if(!t.joinable())return;stop=true;t.join();::CloseHandle(main);
  std::map<std::uint64_t,std::string> modules;
  for(const auto& sample:samples)for(auto address:sample.stack)if(address){MEMORY_BASIC_INFORMATION mbi{};if(::VirtualQuery(reinterpret_cast<void*>(address),&mbi,sizeof(mbi))&&mbi.Type==MEM_IMAGE){const auto base=reinterpret_cast<std::uint64_t>(mbi.AllocationBase);if(!modules.contains(base)){wchar_t w[1024]{};char name[4096]{};::GetModuleFileNameW(static_cast<HMODULE>(mbi.AllocationBase),w,1024);::WideCharToMultiByte(CP_UTF8,0,w,-1,name,4096,nullptr,nullptr);modules[base]=name;}}}
  std::ofstream out(path);for(const auto& [base,name]:modules)out<<"MODULE "<<std::hex<<base<<std::dec<<" "<<name<<"\n";
  for(const auto& sample:samples){out<<"S "<<sample.frame<<" "<<std::hex<<sample.guest_pc<<std::dec;for(auto address:sample.stack)out<<" "<<std::hex<<address<<std::dec;out<<"\n";}
 }
};
