// Display metadata for the original translucent HUD queue. The original
// descriptors, TL vertices, sorting, draw order and return values are untouched.
// 57BF80 enqueues; 57E110 sorts descriptor indices and later issues D3D draws.
struct HudDeferredPanel { unsigned role, type, count, vertices, frame; };
std::map<unsigned,HudDeferredPanel> hud_deferred_panels;
unsigned hud_deferred_restored{};
unsigned hud_panel_producer_role() const {
 for(unsigned i=depth;i>0;--i)switch(returns[i-1]){
  case 0x43c767:return WideLeft;
  case 0x43c77d:case 0x43c797:case 0x43c7c2:return WideRight;
 }
 return WideWorld;
}
void* hud_panel_body(State*s,unsigned target,void*p,Body body) {
 const unsigned before=load(0x803550),role=hud_panel_producer_role();
 if(!before)hud_deferred_panels.clear();
 void*result=body(s,target,p);
 const unsigned after=load(0x803550);
 // Failed/full, immediate and separately flagged paths enqueue nothing.
 if(role&&before<6000&&after==before+1){
  const unsigned descriptor=0x80cd9c+16*before;
  if(!readable(descriptor,16))deny("HUD deferred descriptor unavailable",descriptor);
  const unsigned type=load(descriptor),count=load(descriptor+4),texture=load(descriptor+8),vertices=load(descriptor+12);
  if(texture||!count||count>24000||vertices<0x82449c||
     std::uint64_t(vertices)+32ULL*count>0x82449c+32ULL*24000||!readable(vertices,32*count))
   deny("HUD deferred panel outside original queue contract",descriptor);
  hud_deferred_panels[descriptor]={role,type,count,vertices,host.frames};
 }
 return result;
}
unsigned hud_deferred_role(unsigned type,unsigned vertices,unsigned count,unsigned fallback) {
 // Provider calls bypass enter(); their CALL return is on the guest stack,
 // while returns[] still describes the surrounding translated flush.
 if(!wide_on()||!readable(state.gpr.rsp.dword,4)||load(state.gpr.rsp.dword)!=0x57e2ed)return fallback;
 const unsigned descriptor=state.gpr.rsi.dword;
 auto it=hud_deferred_panels.find(descriptor);
 if(it==hud_deferred_panels.end())return fallback;
 const auto&panel=it->second;
 if(panel.frame!=host.frames||panel.type!=type||panel.count!=count||panel.vertices!=vertices||
    !readable(descriptor,16)||load(descriptor)!=type||load(descriptor+4)!=count||
    load(descriptor+8)||load(descriptor+12)!=vertices)
  deny("HUD deferred panel identity changed before flush",descriptor);
 if(FILE*log=wide_log_file();log&&(hud_deferred_restored<8||host.frames==hud_detail_frame)){
  std::fprintf(log,"deferred-panel frame %u descriptor %08x vertices %08x count %u role %u (late %u)\n",host.frames,descriptor,vertices,count,panel.role,fallback);std::fflush(log);
 }
 ++hud_deferred_restored;
 return panel.role;
}
