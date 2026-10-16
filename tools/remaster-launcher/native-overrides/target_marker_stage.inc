// Display-only target-marker adaptation. Original 440B00 chooses the camera;
// 440510 receives that choice at [ESP+C]. Only the three triangle line draws
// under 441490 consume this provenance. Lead cues and offscreen arrows do not.
struct TargetMarkerProjection{unsigned frame{};bool zoom{};float anchor{};};
std::map<unsigned,TargetMarkerProjection>target_marker_projections;
unsigned target_marker_update_owner{},target_marker_draw_owner{};
unsigned target_marker_clip{},target_marker_clip_output{};
void target_marker_owner(unsigned owner){
 if(!owner||!readable(owner,0x2408)||load(owner)!=0x5c03e8)
  deny("Widescreen target marker owner unavailable",owner);
}
float target_marker_camera_anchor(unsigned owner){
 target_marker_owner(owner);
 const unsigned previous=zoom_display_owner;
 zoom_display_owner=load(owner+0x34)+0x1508;
 try{const float anchor=zoom_display_anchor();zoom_display_owner=previous;return anchor;}
 catch(...){zoom_display_owner=previous;throw;}
}
const TargetMarkerProjection&target_marker_projection(){
 target_marker_owner(target_marker_draw_owner);
 const auto it=target_marker_projections.find(target_marker_draw_owner);
 if(it==target_marker_projections.end()||it->second.frame!=host.frames)
  deny("Widescreen target triangle has no current camera provenance",target_marker_draw_owner);
 return it->second;
}
bool target_marker_zoom(){return target_marker_projection().zoom;}
float target_marker_anchor(){
 const auto&projection=target_marker_projection();
 if(!projection.zoom)deny("Widescreen target triangle is not zoom-projected",target_marker_draw_owner);
 return projection.anchor;
}
void*target_marker_body(State*s,unsigned target,void*p,Body body){
 if(target==0x440b00){
  const unsigned owner=state.gpr.rcx.dword;target_marker_owner(owner);
  const unsigned previous=target_marker_update_owner,previous_clip=target_marker_clip,previous_output=target_marker_clip_output;
  target_marker_update_owner=owner;target_marker_clip=target_marker_clip_output=0;
  target_marker_projections.erase(owner);
  try{void*result=body(s,target,p);target_marker_update_owner=previous;target_marker_clip=previous_clip;target_marker_clip_output=previous_output;return result;}
  catch(...){target_marker_update_owner=previous;target_marker_clip=previous_clip;target_marker_clip_output=previous_output;throw;}
 }
 if(target==0x441490){
  const unsigned previous=target_marker_draw_owner;target_marker_draw_owner=state.gpr.rcx.dword;
  target_marker_owner(target_marker_draw_owner);
  try{void*result=body(s,target,p);target_marker_draw_owner=previous;return result;}
  catch(...){target_marker_draw_owner=previous;throw;}
 }
 if(target==0x440510){
  const unsigned owner=state.gpr.rcx.dword,sp=state.gpr.rsp.dword;target_marker_owner(owner);
  if(owner!=target_marker_update_owner||!readable(sp,16))deny("Widescreen target builder outside update scope",owner);
  const unsigned zoom=load(sp+12)&255;if(zoom>1)deny("Unknown original target projection choice",zoom);
  const float anchor=zoom?target_marker_camera_anchor(owner):0.f;
  void*result=body(s,target,p);
  target_marker_projections[owner]={host.frames,zoom!=0,anchor};
  if(FILE*log=wide_log_file();log&&host.frames%10==0)
   std::fprintf(log,"target-marker-built frame %u owner %08x zoom %u anchor %.9g\n",host.frames,owner,zoom,double(anchor));
  return result;
 }
 if(target==0x53cf10){
  const unsigned ret=load(state.gpr.rsp.dword),output=state.gpr.rdx.dword;
  void*result=body(s,target,p);
  if(ret==0x440cc6){target_marker_clip=state.gpr.rax.dword;target_marker_clip_output=output;}
  return result;
 }
 // Let 40DA30 finish the original coordinate conversion first. On the
 // nonzero zoom-clip branch this temporary X is used only by 440D21..D6C
 // to decide whether the normal marker lies underneath the zoom window.
 // Transform that comparison edge to the actual displayed footprint. Never
 // modify clip flags, the zoom-inside result, main projection or target choice.
 const unsigned ret=load(state.gpr.rsp.dword),output=state.gpr.rcx.dword;
 void*result=body(s,target,p);
 if(ret==0x440cd1&&target_marker_clip<=15&&(target_marker_clip&3)){
  if(output!=target_marker_clip_output||!readable(output,12)||load(0x5f4d4c)!=0)
   deny("Widescreen target occlusion coordinate profile unavailable",output);
  mw34::vkscene::HostFpEnvironment fp;
  const float center=target_marker_camera_anchor(target_marker_update_owner);
  const float before=wide_float(output),k=wide_hud_factor(host.display.width,host.display.height);
  const float after=center+(before+.5f-center)/k-.5f;
  wide_store_float(output,after);
  if(FILE*log=wide_log_file();log&&host.frames%10==0)
   std::fprintf(log,"target-marker-occlusion frame %u owner %08x code %u center %.9g edge %.9g -> %.9g\n",host.frames,target_marker_update_owner,target_marker_clip,double(center),double(before),double(after));
 }
 return result;
}
