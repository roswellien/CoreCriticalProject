// Optional display-only extension of authenticated world and zoom cameras.
// Original 4F3A70 owns near/far setters; 4F4170/4F41B0 rebuild the terrain footprint.
// Retain the original near clip, object LOD, fog mode/color and preview cameras.
struct DistanceCamera{unsigned original{},applied{};bool owns{};};
std::map<unsigned,DistanceCamera>distance_cameras;
unsigned distance_marker_owner{};
unsigned distance_requested(){static const unsigned value=[this]{
 const char*p=std::getenv("MW34_REMASTER_DRAW_DISTANCE");
 if(!p||!*p||std::strcmp(p,"800")==0)return 800U;
 if(std::strcmp(p,"1200")==0)return 1200U;
 if(std::strcmp(p,"1600")==0)return 1600U;
 if(std::strcmp(p,"2400")==0)return 2400U;
 if(std::strcmp(p,"3200")==0)return 3200U;
 deny("Unsupported Remaster draw distance (expected 800,1200,1600,2400,3200)",0);return 800U;}();return value;}
unsigned distance_fog_requested(){static const unsigned value=[this]{
 const char*p=std::getenv("MW34_REMASTER_FOG_DISTANCE");if(!p||!*p)return 0U;
 char*end{};const unsigned long n=std::strtoul(p,&end,10);
 if(*end||n>3200)deny("Unsupported Remaster fog distance (expected 0..3200)",0);
 return unsigned(n);}();return value;}
FILE*distance_log(){static FILE*f=[]{const char*p=std::getenv("MW34_VIEW_DISTANCE_LOG");return p&&*p?std::fopen(p,"w"):nullptr;}();return f;}
void distance_restore(unsigned node){if(distance_requested()==800||!node||!readable(node,0x3c)||load(node+0x34)!=1)return;
 const unsigned data=load(node+0x38);auto it=distance_cameras.find(data);if(it==distance_cameras.end())return;
 auto&c=it->second;if(c.owns&&readable(data,0xfc)&&load(data+0xb4)==c.applied){store(data+0xb4,c.original);store(data+0xf8,1);}c.owns=false;}
bool distance_world(unsigned node,unsigned data){
 const unsigned context=load(0x5f4c8c),view=load(data+4);
 const unsigned vd=view&&readable(view,0x3c)&&load(view+0x34)==3?load(view+0x38):0;
 const auto name=pose_name(node,36);
 return context&&readable(context,8)&&load(context+4)==node&&vd&&readable(vd,16)&&
  load(vd)==0&&load(vd+4)==0&&load(vd+8)==host.display.width&&load(vd+12)==host.display.height&&
  name!="labcam"&&name!="zoomcam"&&name!="camx";
}
unsigned distance_zoom_owner(){
 unsigned owner=zoom_display_owner;
 // Target markers prepare the zoom camera before its render scope starts.
 if(!owner&&distance_marker_owner&&readable(distance_marker_owner,0x2408)&&load(distance_marker_owner)==0x5c03e8)
  owner=load(distance_marker_owner+0x34)+0x1508;
 return owner;
}
bool distance_zoom(unsigned node,unsigned data){
 const unsigned owner=distance_zoom_owner();
 if(!owner||!readable(owner,0x3c)||load(owner)!=0x5c0608||load(owner+0x38)!=node||
    pose_name(node,36)!="zoomcam")return false;
 const unsigned view=load(data+4),vd=view&&readable(view,0x3c)&&load(view+0x34)==3?load(view+0x38):0;
 if(!vd||!readable(vd,16))return false;
 const unsigned x=load(vd),y=load(vd+4),w=load(vd+8),h=load(vd+12);
 return w&&h&&std::uint64_t(x)+w<=host.display.width&&std::uint64_t(y)+h<=host.display.height;
}
void distance_prepare(unsigned node){const unsigned requested=distance_requested();if(requested==800&&!distance_fog_requested()&&!distance_log())return;
 if(!node||!readable(node,0x3c)||load(node+0x34)!=1)return;const unsigned data=load(node+0x38);if(!data||!readable(data,0x1dc))return;
 const bool world=distance_world(node,data),zoom=distance_zoom(node,data);if(!world&&!zoom){distance_restore(node);return;}
 if(requested>800){auto&c=distance_cameras[data];
  if(!c.owns||load(data+0xb4)!=c.applied){
   mw34::vkscene::HostFpEnvironment fp;const float original=wide_float(data+0xb4);
   if(original<=wide_float(data+0xb0))deny("Invalid original camera far plane",data);
   c.original=load(data+0xb4);wide_store_float(data+0xb4,std::max(original,float(requested)));
   c.applied=load(data+0xb4);c.owns=true;store(data+0xf8,1);
  }
 }
 if(distance_fog_active&&!distance_fog_scaled)distance_extend_fog(data);
 if(FILE*f=distance_log()){static std::map<unsigned,unsigned>last;auto it=last.find(node);if(it==last.end()||it->second!=host.frames){last[node]=host.frames;
  std::fprintf(f,"camera frame %u node %08x data %08x kind %s far %.9g near %.9g xyz %.9g %.9g %.9g fog-range %.9g %.9g\n",host.frames,node,data,zoom?"zoom":"world",double(wide_float(data+0xb4)),double(wide_float(data+0xb0)),double(wide_float(data+0x2c)),double(wide_float(data+0x30)),double(wide_float(data+0x34)),double(wide_float(0x74a240)),double(wide_float(0x74a248)));std::fflush(f);}}
}
void*distance_marker_body(State*s,unsigned target,void*p,Body body){
 const unsigned previous=distance_marker_owner;distance_marker_owner=state.gpr.rcx.dword;
 const auto run=[&]{return wide_on()?target_marker_body(s,target,p,body):body(s,target,p);};
 try{void*result=run();distance_marker_owner=previous;return result;}catch(...){distance_marker_owner=previous;throw;}
}
void distance_tiles(unsigned camera){FILE*f=distance_log();if(!f||!camera||!readable(camera,0x1dc))return;
 unsigned total=0,max_count=0,max_ring=0;
 for(unsigned ring=0;ring<50;++ring){const unsigned count=load(0x736910+ring*0x2d4);
  if(count>30)deny("Original terrain tiler row capacity exceeded",count);
  total+=count;max_count=std::max(max_count,count);if(count)max_ring=ring;
 }
 std::fprintf(f,"tiles frame %u camera %08x far %.9g total %u max-ring %u max-count %u\n",host.frames,camera,double(wide_float(camera+0xb4)),total,max_ring,max_count);std::fflush(f);
}
bool distance_fog_active{},distance_fog_scaled{};
void distance_extend_fog(unsigned cd){
 const unsigned explicit_far=distance_fog_requested();
 if(explicit_far){
  // Override only the linear distance ramp. Weather enable/mode/color,
  // altitude taper and density remain authored by the current mission.
  if(!load(0x74a22c)||!load(0x74a230))return;
  mw34::vkscene::HostFpEnvironment fp;
  const float fog_near=wide_float(0x74a240),fog_far=wide_float(0x74a248);
  if(!std::isfinite(fog_near)||!std::isfinite(fog_far)||fog_near<0||fog_far<=fog_near)deny("Invalid original linear fog interval",cd);
  const float new_far=float(explicit_far),new_near=fog_near*(new_far/fog_far);
  wide_store_float(0x74a240,new_near);wide_store_float(0x74a244,new_near*new_near);
  wide_store_float(0x74a248,new_far);wide_store_float(0x74a24c,new_far*new_far);
  wide_store_float(0x74a250,1.f/(new_far-new_near));distance_fog_scaled=true;return;
 }
 float original_far=wide_float(cd+0xb4);const auto it=distance_cameras.find(cd);
 if(it!=distance_cameras.end()&&it->second.owns&&load(cd+0xb4)==it->second.applied)std::memcpy(&original_far,&it->second.original,4);
 if(!std::isfinite(original_far)||original_far<=0)deny("Extended-distance original far plane unavailable",cd);
 float scale;{mw34::vkscene::HostFpEnvironment fp;scale=std::max(1.f,float(distance_requested())/original_far);}
 if(FILE*f=distance_log();f&&host.frames%100==0){std::fprintf(f,"fog frame %u camera-data %08x enabled %u linear %u near %.9g far %.9g density %.9g scale %.9g\n",host.frames,cd,load(0x74a22c),load(0x74a230),double(wide_float(0x74a240)),double(wide_float(0x74a248)),double(wide_float(0x74a260)),double(scale));std::fflush(f);}
 if(scale==1)return;
 // Exact renderer fields maintained by 526BA0/526C00/526CD0. Camera draws
 // consume these pre-applied globals; world fog updates can precede cameras.
 // Extend haze with the view while retaining mode/color/altitude. Restore
 // every byte before preview/zoom rendering and on guest non-local returns.
 constexpr unsigned addresses[]={0x74a240,0x74a244,0x74a248,0x74a24c,0x74a250,0x74a260};
 {mw34::vkscene::HostFpEnvironment fp;
  wide_store_float(addresses[0],wide_float(addresses[0])*scale);
  wide_store_float(addresses[1],wide_float(addresses[1])*scale*scale);
  wide_store_float(addresses[2],wide_float(addresses[2])*scale);
  wide_store_float(addresses[3],wide_float(addresses[3])*scale*scale);
  wide_store_float(addresses[4],wide_float(addresses[4])/scale);
  wide_store_float(addresses[5],wide_float(addresses[5])/scale);}
 distance_fog_scaled=true;
}
void distance_fog_bound(unsigned data){
 const unsigned context=load(0x5f4c8c),owner=distance_zoom_owner();
 unsigned node=context&&readable(context,8)?load(context+4):0;
 // Zoom rendering leaves the gameplay context pointing at the main camera.
 // Authenticate its separate node from the scoped original zoom owner.
 if(owner&&readable(owner,0x3c)&&load(owner)==0x5c0608){const unsigned z=load(owner+0x38);if(z&&readable(z,0x3c)&&load(z+0x38)==data&&distance_zoom(z,data))node=z;}
 const bool valid=node&&readable(node,0x3c)&&load(node+0x34)==1&&load(node+0x38)==data&&
  (distance_world(node,data)||distance_zoom(node,data));
 if(valid&&distance_fog_active&&(!distance_fog_scaled||distance_fog_requested()))distance_extend_fog(data);
 if(FILE*f=distance_log();f&&valid&&host.frames%100==0){
  mw34::vkscene::HostFpEnvironment fp;
  std::fprintf(f,"fog-bind frame %u node %08x camera %08x active %u scaled %u near %.9g far %.9g density %.9g\n",host.frames,node,data,unsigned(distance_fog_active),unsigned(distance_fog_scaled),double(wide_float(0x74a240)),double(wide_float(0x74a248)),double(wide_float(0x74a260)));std::fflush(f);
 }
}
void distance_fog_consumed(){
 FILE*f=distance_log();if(!f||host.frames%100)return;
 const unsigned data=load(0x7402f4);static std::map<unsigned,unsigned>last;auto it=last.find(data);if(it!=last.end()&&it->second==host.frames)return;last[data]=host.frames;
 mw34::vkscene::HostFpEnvironment fp;
 std::fprintf(f,"fog-consume frame %u camera %08x active %u near %.9g far %.9g density %.9g\n",host.frames,data,unsigned(distance_fog_active),double(wide_float(0x74a240)),double(wide_float(0x74a248)),double(wide_float(0x74a260)));std::fflush(f);
}
void*distance_camera_body(State*s,unsigned target,void*p,Body body){
 // Preserve the legacy one-scale-per-world-draw contract for implicit fog.
 if(distance_fog_active&&!distance_fog_requested())return body(s,target,p);
 // Context4B52C0 tail-JMP fuses alternate4F7030. Frustum preparation runs
 // after the original camera/world setup, when full-viewport identity is valid.
 constexpr unsigned addresses[]={0x74a240,0x74a244,0x74a248,0x74a24c,0x74a250,0x74a260};
 unsigned saved[6];for(unsigned i=0;i<6;++i)saved[i]=load(addresses[i]);
 const bool previous_active=distance_fog_active,previous_scaled=distance_fog_scaled;
 distance_fog_active=true;distance_fog_scaled=false;
 const auto restore=[&]{for(unsigned i=0;i<6;++i)store(addresses[i],saved[i]);distance_fog_active=previous_active;distance_fog_scaled=previous_scaled;};
 void*result{};try{result=body(s,target,p);}catch(...){restore();throw;}restore();return result;
}
void distance_scene_log(const mw34::vkscene::Scene&sc){FILE*f=distance_log();if(!f||host.frames%100)return;
 unsigned enabled=0,disabled=0,alpha_min=255,alpha_max=0,vertices=0;
 for(const auto&d:sc.draws){if(!(d.push.mode[0]&16)){++disabled;continue;}++enabled;
  if(d.model)continue;
  for(unsigned i=d.first;i<d.first+d.count;++i){unsigned spec;std::memcpy(&spec,sc.vertices.data()+size_t(i)*32+20,4);
   alpha_min=std::min(alpha_min,spec>>24);alpha_max=std::max(alpha_max,spec>>24);++vertices;}}
 std::fprintf(f,"render-fog frame %u enabled %u disabled %u tl-vertices %u alpha-min %u alpha-max %u\n",host.frames,enabled,disabled,vertices,alpha_min,alpha_max);std::fflush(f);
}
