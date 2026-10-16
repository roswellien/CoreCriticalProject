// Optional display-only extension of the original main-world camera far plane.
// Original 4F3A70 owns near/far setters; 4F4170/4F41B0 rebuild the terrain footprint.
// Retain the original near clip, object LOD, fog mode/color and preview cameras.
struct DistanceCamera{unsigned original{},applied{};bool owns{};};
std::map<unsigned,DistanceCamera>distance_cameras;
unsigned distance_requested(){static const unsigned value=[this]{
 const char*p=std::getenv("MW34_REMASTER_DRAW_DISTANCE");
 if(!p||!*p||std::strcmp(p,"800")==0)return 800U;
 if(std::strcmp(p,"1600")==0)return 1600U;
 if(std::strcmp(p,"2400")==0)return 2400U;
 if(std::strcmp(p,"3200")==0)return 3200U;
 deny("Unsupported Remaster draw distance (expected 800,1600,2400,3200)",0);return 800U;}();return value;}
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
void distance_prepare(unsigned node){const unsigned requested=distance_requested();if(requested==800&&!distance_log())return;
 if(!node||!readable(node,0x3c)||load(node+0x34)!=1)return;const unsigned data=load(node+0x38);if(!data||!readable(data,0x1dc))return;
 const bool world=distance_world(node,data);if(!world){distance_restore(node);return;}
 if(requested>800){auto&c=distance_cameras[data];
  if(!c.owns||load(data+0xb4)!=c.applied){
   mw34::vkscene::HostFpEnvironment fp;const float original=wide_float(data+0xb4);
   if(original<=wide_float(data+0xb0))deny("Invalid original camera far plane",data);
   c.original=load(data+0xb4);wide_store_float(data+0xb4,std::max(original,float(requested)));
   c.applied=load(data+0xb4);c.owns=true;store(data+0xf8,1);
  }
 }
 if(distance_fog_active&&!distance_fog_scaled)distance_extend_fog(data);
 if(FILE*f=distance_log()){static unsigned last=~0U;if(last!=host.frames){last=host.frames;
  std::fprintf(f,"camera frame %u node %08x data %08x far %.9g near %.9g xyz %.9g %.9g %.9g fog-range %.9g %.9g\n",host.frames,node,data,double(wide_float(data+0xb4)),double(wide_float(data+0xb0)),double(wide_float(data+0x2c)),double(wide_float(data+0x30)),double(wide_float(data+0x34)),double(wide_float(0x74a240)),double(wide_float(0x74a248)));std::fflush(f);}}
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
void*distance_camera_body(State*s,unsigned target,void*p,Body body){
 if(distance_fog_active)return body(s,target,p);
 // Context4B52C0 tail-JMP fuses alternate4F7030. Frustum preparation runs
 // after the original camera/world setup, when full-viewport identity is valid.
 constexpr unsigned addresses[]={0x74a240,0x74a244,0x74a248,0x74a24c,0x74a250,0x74a260};
 unsigned saved[6];for(unsigned i=0;i<6;++i)saved[i]=load(addresses[i]);
 distance_fog_active=true;distance_fog_scaled=false;
 const auto restore=[&]{for(unsigned i=0;i<6;++i)store(addresses[i],saved[i]);distance_fog_active=false;distance_fog_scaled=false;};
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
