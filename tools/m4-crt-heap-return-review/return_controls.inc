 if(point>=21&&point<=24){review_need(h.live_handle()&&h.token_valid(hr::token)&&h.known_handle()==f.private_handle,"Exact original private HANDLE remains live through every genuine store/RET checkpoint");review_need(review_heap_member(f.private_handle),"Actual private heap remains in process inventory until source exit");}
 if(mode>=81&&mode<=84&&point==21+mode-81)throw std::runtime_error("Independent initializer store/return checkpoint exception");
 if(point==21){
  if(mode==85)f.r.memory().protect({hr::global},Permissions::read);
  if(mode==86){f.r.memory().protect({hr::global},Permissions::none);bool denied{};try{h.source_identity();}catch(const mg::BridgeAbort&){denied=true;}f.r.memory().protect({hr::global},Permissions::read|Permissions::write);review_need(denied&&h.access_count==31,"NOACCESS mode-global page fails checked identity read before store; read permission restored only for diagnostic capture");throw mg::BridgeAbort{};}
  if(mode==87)f.r.memory().store<unsigned>({hr::global+4},1);
  if(mode==88){f.r.memory().protect({0x78003000},Permissions::read|Permissions::write);f.r.memory().store<unsigned char>({0x78003a08},0);f.r.memory().protect({0x78003000},Permissions::read|Permissions::execute);}
  if(mode==89)c.state.gpr.rax.dword=2;
  if(mode==90)++c.state.gpr.rsp.dword;
  if(mode==91)++f.r.cpu().eip;
  if(mode==92)f.r.fx()[24]^=std::byte{0x20};
 }
 if(point==22){
  if(mode==93)h.mode_value^=1;
  if(mode==94)h.mode_published=false;
  if(mode==95)h.query_witness[3]^=1;
  if(mode==96)h.query_output[4]^=std::byte{1};
  if(mode==97)f.r.memory().protect({0x20001000},Permissions::read);
 }
 if(mode==98&&point==2&&h.access_count==33)throw std::runtime_error("Independent initializer PUSH commit before ESP publication");
 if(mode==99&&point==2&&h.access_count==34)throw std::runtime_error("Independent initializer POP read with ESP already advanced");
 if(mode==100&&point==2&&h.access_count==34)f.r.memory().store<unsigned>({0x20001858},hr::ret^1);
 if(mode==101&&point==2&&h.access_count==35)throw std::runtime_error("Independent genuine initializer RET read before State publication");
 if(mode==102&&point==24)c.state.rflag.flat^=0x100;
 if(mode==103&&point==23){bool denied{};try{(void)h.owns_token(hr::token^1);}catch(const mg::BridgeAbort&){denied=true;}review_need(denied&&h.live_handle()&&!h.token_valid(hr::token^1)&&h.access_count==34&&!h.initializer_returned,"Unknown opaque token refuses before genuine initializer return while original full HANDLE stays private/live");++review_malformed;throw mg::BridgeAbort{};}
 if(mode==104&&point==23){bool denied{};try{(void)h.returned(reinterpret_cast<State*>(std::uintptr_t{1}),hr::ret,&h);}catch(const mg::BridgeAbort&){denied=true;}review_need(denied&&h.access_count==34&&!h.initializer_returned,"Malformed initializer RET State refuses before dereference or invented source-return publication");++review_malformed;throw mg::BridgeAbort{};}
