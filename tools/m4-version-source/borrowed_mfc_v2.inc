 // Exact external version-source CALL frame, with the already accepted literal
 // MFC823/825 allocator, including its genuine initial free(NULL) route.
 void borrow_version_mfc(State&source,unsigned site,unsigned frame,unsigned ret){
  check();require(bootstrapped&&&source==&s&&r.cpu().eip==0x4af240&&!version_buffer_live_,"Same current version Runtime/State and no outstanding native-buffer lease");
  const bool allocate=site==0x4af11a;require(allocate||site==0x4af1a8,"Only two physical version MFC CALL sites");
  const unsigned thunk=allocate?0x5abd26:0x5abd1a,expected_ret=allocate?0x4af11f:0x4af1ad,slot=allocate?0x5bb4bc:0x5bb4c8,raw=allocate?0x80000337:0x80000339;
  require(ret==expected_ret&&s.gpr.rsp.dword==frame&&s.gpr.rip.dword==thunk&&r.memory().load<unsigned>({frame})==ret&&r.memory().load<unsigned>({slot})==raw,"Whole current version CALL return and physical MFC owning import preimage");
  std::array<std::byte,5>call{};r.memory().read({site},call);require(call[0]==std::byte{0xe8},"Actual whole direct MFC CALL opcode");int displacement{};std::memcpy(&displacement,call.data()+1,4);require(unsigned(site+5+displacement)==thunk,"Complete physical version MFC CALL displacement");
  const auto argument=r.memory().load<unsigned>({frame+4});
  if(allocate)require(argument&&argument<=1024*1024&&argument==r.memory().load<unsigned>({0x60b198}),"Actual version size return is the same genuine allocator request");
  else require(argument==r.memory().load<unsigned>({0x60b19c}),"Actual current source version-buffer pointer, including NULL");
  require(binding->calls_.empty()&&binding->fs_active_.empty()&&!binding->registry_root_,"Serial accepted research provider context with no fabricated initializer-domain claim");
  InvocationHostBoundary host;fn::LastErrorBoundary errors;fresh_external_pages();activate();
  try{
   capture("version-mfc-before");binding->guard();binding->source_identity();
   binding->research_projections_.push_back({10,0x4af240,site,thunk,slot,raw,frame,ret});
   binding->source_accesses_.push_back({site,frame,ret,4,1});
   binding->calls_.push_back({thunk,frame,ret,site,s.gpr.rbp.dword,s.gpr.rbx.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,0});
   const auto result=lb::dispatch_body(thunk,&s,binding.get());binding->guard();binding->source_identity();
   require(result==binding.get()&&binding->calls_.empty()&&s.gpr.rsp.dword==frame+4&&s.gpr.rip.dword==ret,"Genuine MFC literal return consumes only current committed version CALL");
   if(allocate){auto*a=binding->allocation_for(s.gpr.rax.dword);require(a&&a->guest==s.gpr.rax.dword&&a->kind==4&&a->requested==argument&&a->native&&!a->pending,"Actual completed whole MFC-owned version buffer");}
   capture("version-mfc-after");pause();
  }catch(...){poison();throw;}
 }
 VersionBuffer borrow_version_buffer(unsigned site,unsigned guest,unsigned bytes){
  check();require(bootstrapped&&!version_buffer_live_&&r.cpu().eip==0x4af240&&(site==0x4af12c||site==0x4af167),"Only real version fill/query native-buffer boundaries");
  auto*a=binding->allocation_for(guest,bytes);auto*w=a?binding->mfc_for_generation(a->generation):nullptr;
  require(a&&w&&a->kind==4&&a->guest==guest&&!a->pending&&a->native&&a->requested==bytes&&bytes==r.memory().load<unsigned>({0x60b198})&&guest==r.memory().load<unsigned>({0x60b19c})&&w->words[4]==0x4af11a&&w->words[21]&&!w->words[25]&&a->extent>=bytes&&a->extent<=1024*1024,"Same actual version MFC generation, requested size, complete extent and current publication");
  fresh_external_pages();activate();
  try{binding->guard();binding->source_identity();capture("version-buffer-before");version_buffer_={guest,a->generation,site,bytes,a->extent,reinterpret_cast<std::uintptr_t>(a->native)};version_buffer_before_.assign(static_cast<const std::byte*>(a->native),static_cast<const std::byte*>(a->native)+a->extent);version_buffer_live_=true;pause();return {a->native,guest,a->generation,bytes,a->extent};}
  catch(...){poison();throw;}
 }
 void commit_version_buffer(unsigned site,const VersionBuffer&lease){
  check();try{require(bootstrapped&&version_buffer_live_&&site==version_buffer_[2]&&lease.guest==version_buffer_[0]&&lease.generation==version_buffer_[1]&&lease.requested==version_buffer_[3]&&lease.extent==version_buffer_[4]&&reinterpret_cast<std::uintptr_t>(lease.native)==version_buffer_[5],"Exact private version native-buffer lease and same generation");
  auto*a=binding->allocation_for(lease.guest,lease.extent);require(a&&a->native==lease.native&&a->generation==lease.generation&&a->kind==4&&a->extent==lease.extent&&a->requested==lease.requested&&version_buffer_before_.size()==a->extent&&std::equal(version_buffer_before_.begin(),version_buffer_before_.end(),a->expected.begin()),"Private owner and checked BEFORE bytes survive actual version API");
  std::vector<std::byte>guest(a->mapped_bytes);r.memory().read({a->guest},guest);require(guest==a->expected,"Entire guest extent/tail has no uncommitted caller writes");
  // Commit every actual native extent byte; neither an API success constant
  // nor the original observer's resource bytes are accepted by this function.
  std::vector<std::byte>after(static_cast<const std::byte*>(a->native),static_cast<const std::byte*>(a->native)+a->extent);
  for(unsigned off=0;off<a->extent;){const auto n=std::min<unsigned>(4096-((a->guest+off)&4095),a->extent-off);r.memory().write({a->guest+off},std::span(after).subspan(off,n));binding->expected_store(a->guest+off,after.data()+off,n);off+=n;}
  version_buffer_history_.push_back({version_buffer_,version_buffer_before_,after});version_buffer_live_=false;version_buffer_before_.clear();fresh_external_pages();activate();
  binding->guard();binding->source_identity();capture("version-buffer-after");pause();
  }catch(...){poison();throw;}
 }
