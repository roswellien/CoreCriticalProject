 if((mode>=81&&mode<=104)||(mode>=157&&mode<=168)){
  review_need(h.query_called&&h.query_preflight&&h.query_output_complete&&h.query_returned&&h.selector_returned&&h.output_count==37&&h.api_access_count==2&&h.undefined_count==5,"Every new return control starts from actual complete native query and genuine selector result");
  const auto progress=h.progress();const bool before_store=mode==81||(mode>=85&&mode<=92)||mode==157||mode==158;
  const bool pushed=mode==98||mode==162||mode==163;const bool popped=mode==83||mode==99||mode==100||mode==103||mode==104||mode==164||mode==165;
  const bool read_ret=mode==101||mode==166;const bool returned=mode==84||mode==102||mode==167||mode==168;
  const unsigned count=before_store?31:pushed?33:popped?34:read_ret||returned?35:32;
  review_need(h.access_count==count&&progress[0]==1&&progress[1]==1&&progress[2]==1&&progress[3]==!before_store&&progress[4]==unsigned(!before_store)&&progress[5]==unsigned(mode==83||mode==100||mode==101||mode==103||mode==104||mode>=165||mode==84||mode==102)&&progress[6]==unsigned(returned)&&!progress[7],"Exact private store/return chronology and committed source access count after cleanup");
  if(mode==98||mode==162)review_need(c.state.gpr.rip.dword==0x78003a08&&c.state.gpr.rsp.dword==0x20001858&&f.r.memory().load<unsigned>({0x20001854})==1,"PUSH memory commits before generated ESP publication");
  if(mode==99||mode==164)review_need(c.state.gpr.rip.dword==0x78003a0a&&c.state.gpr.rsp.dword==0x20001858&&c.state.gpr.rax.dword==1,"POP advances ESP before checked read and retains prior EAX on observer exception");
  if(mode==101||mode==166)review_need(c.state.gpr.rip.dword==0x78003a0b&&c.state.gpr.rsp.dword==0x20001858&&!h.initializer_returned,"Genuine RET read commits before generated EIP/ESP and return publication");
  if(returned)review_need(c.state.gpr.rip.dword==hr::ret&&c.state.gpr.rsp.dword==0x2000185c&&h.initializer_returned,"Source initializer RET published before later observer/terminal fault");
 }
