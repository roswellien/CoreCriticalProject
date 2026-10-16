// Original zoom camera geometry is CPU-projected into an engine viewport.
// The D3D viewport remains full-target and is not that camera's screen anchor.
// Snapshot display metadata while 442F50's exact zoom owner is still active.
unsigned zoom_display_owner{};
float zoom_display_anchor() {
 const unsigned owner=zoom_display_owner;
 if(!owner||!readable(owner,0x3c)||load(owner)!=0x5c0608)
  deny("Widescreen zoom scene owner unavailable",owner);
 const unsigned node=load(owner+0x38);
 if(!node||!readable(node,0x3c)||load(node+0x34)!=1||pose_name(node,36)!="zoomcam")
  deny("Widescreen zoom scene camera unavailable",node);
 const unsigned data=load(node+0x38),view=data&&readable(data,8)?load(data+4):0;
 const unsigned vd=view&&readable(view,0x3c)&&load(view+0x34)==3?load(view+0x38):0;
 if(!vd||!readable(vd,16))deny("Widescreen zoom scene viewport unavailable",view);
 const int x=int(load(vd)),y=int(load(vd+4)),w=int(load(vd+8)),h=int(load(vd+12));
 if(x<0||y<0||w<=0||h<=0||std::int64_t(x)+w>host.display.width||std::int64_t(y)+h>host.display.height)
  deny("Widescreen zoom scene viewport outside target",vd);
 return float(x)+float(w)*.5f;
}
void zoom_capture_command(D3DCmd&command) {
 if(!wide_on()||command.hud_role!=WideZoom)return;
 command.zoom_anchor=zoom_display_anchor();command.zoom_anchor_known=true;
 if(FILE*log=wide_log_file();log&&host.frames%100==0){
  static unsigned last=~0U;
  if(last!=host.frames){last=host.frames;std::fprintf(log,"zoom-capture frame %u owner %08x lock %u anchor %.9g\n",host.frames,zoom_display_owner,load(zoom_display_owner+0x174)&255,double(command.zoom_anchor));std::fflush(log);}
 }
}
void*zoom_scene_body(State*s,unsigned target,void*p,Body body) {
 const unsigned previous=zoom_display_owner;zoom_display_owner=state.gpr.rcx.dword;
 void*result{};
 try{result=body(s,target,p);}catch(...){zoom_display_owner=previous;throw;}
 zoom_display_owner=previous;return result;
}
