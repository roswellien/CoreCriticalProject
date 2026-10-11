 // Borrow only the exact source import reached by the six normal widget roots.
 // The caller owns the already committed guest CALL. No extra frame is pushed,
 // no original response is supplied, and the accepted provider bodies execute.
 void borrow_widget_onexit(State&source,unsigned root,unsigned frame,unsigned ret){
  check();require(bootstrapped&&&source==&s&&r.cpu().eip==root,"Exact initialized same Runtime/source State widget service owner");
  unsigned callback{};switch(root){case 0x40e250:callback=0x40e420;break;case 0x40ef50:callback=0x40ff90;break;case 0x5a3c30:callback=0x5a3d70;break;case 0x5a3ff0:callback=0x5a4330;break;case 0x5a66f0:callback=0x5a6740;break;case 0x479590:callback=0x4795d0;break;default:throw std::runtime_error("Unreviewed widget callback root");}
  require(s.gpr.rip.dword==0x78004a36&&s.gpr.rsp.dword==frame&&ret==0x5ac124&&frame+24==r.cpu().esp,"Actual inner source onexit CALL frame/current root frame");
  require(r.memory().load<unsigned>({frame})==ret&&r.memory().load<unsigned>({frame+4})==callback&&r.memory().load<unsigned>({0x5bb52c})==0x1decb0,"Exact committed onexit return/callback/raw IAT");
  const std::array<std::byte,6>call{std::byte{0xff},std::byte{0x15},std::byte{0x2c},std::byte{0xb5},std::byte{0x5b},std::byte{0}};std::array<std::byte,6>actual{};r.memory().read({0x5ac11e},actual);require(actual==call,"Complete owning literal onexit CALL bytes");
  require(binding->calls_.empty()&&binding->fs_active_.empty()&&r.memory().load<unsigned>(r.fs_base())==binding->fs_expected_,"Widget constructor restores complete FS before registration service");
  const auto begin=r.memory().load<unsigned>({0x7803788c}),next=r.memory().load<unsigned>({0x78037888});auto*allocation=binding->allocation_for(begin);require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity,"Current owned source producer callback capacity");
  InvocationHostBoundary host;fn::LastErrorBoundary errors;fresh_external_pages();activate();
  try{
   capture("widget-onexit-before");binding->guard();binding->source_identity();
   // Independently verified current source operand/CALL word is imported as a
   // typed borrowed-source witness, distinguished from provider read callbacks.
   binding->research_projections_.push_back({9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,frame,ret});
   binding->source_accesses_.push_back({0x5ac11e,0x5bb52c,0x1decb0,4,0});binding->source_accesses_.push_back({0x5ac11e,frame,ret,4,1});
   binding->calls_.push_back({0x78004a36,frame,ret,0x5ac11e,s.gpr.rbp.dword,s.gpr.rbx.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,0});
   const auto result=lb::dispatch_body(0x78004a36,&s,binding.get());binding->guard();binding->source_identity();
   require(result==binding.get()&&binding->calls_.empty()&&s.gpr.rsp.dword==frame+4&&s.gpr.rip.dword==ret&&s.gpr.rax.dword==callback,"Actual accepted literal onexit returns to committed widget CALL");
   require(r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual source-owned registry publication and complete capacity carry");
   capture("widget-onexit-after");r.cpu()=::cpu(s);pause();
  }catch(...){r.cpu()=::cpu(s);poison();throw;}
 }
