// Opt-in display-only Hor+ camera correction, before the original camera's
// dirty frustum rebuild. Original zoom/clamp setters and vertical FOV run first.
// Shipped functions:4F3B90/4F3D90 setters;4F41B0 frustum;526E10 projection.
struct WideCamera{unsigned raw_h{},raw_half{},raw_cot{},wide_h{},wide_half{},wide_cot{};bool applied{};};
std::map<unsigned,WideCamera>wide_cameras;
std::uint64_t wide_updates{};
unsigned wide_world_frame=~0U;
static bool wide_on(){static const bool on=mw34::vkscene::Renderer::widescreen();return on;}
FILE*wide_log_file(){static FILE*log=[]{const char*p=std::getenv("MW34_WIDE_LOG");return p&&*p?std::fopen(p,"w"):nullptr;}();return log;}
float wide_float(unsigned address){const unsigned bits=load(address);float result;std::memcpy(&result,&bits,4);if(!std::isfinite(result))deny("Widescreen camera has non-finite input",address);return result;}
void wide_store_float(unsigned address,float value){if(!std::isfinite(value))deny("Widescreen camera has non-finite output",address);unsigned bits;std::memcpy(&bits,&value,4);store(address,bits);}
bool wide_owns(unsigned data,const WideCamera&c){return c.applied&&load(data+0xe8)==c.wide_h&&load(data+0xf0)==c.wide_half&&load(data+0x1d4)==c.wide_cot;}
void wide_restore(unsigned node){if(!wide_on()||!node||!readable(node,0x3c)||load(node+0x34)!=1)return;const unsigned data=load(node+0x38);auto it=wide_cameras.find(data);if(it==wide_cameras.end())return;
 auto&c=it->second;if(readable(data,0x1dc)&&wide_owns(data,c)){store(data+0xe8,c.raw_h);store(data+0xf0,c.raw_half);store(data+0x1d4,c.raw_cot);store(data+0xf8,1);store(data+0x138,1);}c.applied=false;}
void wide_prepare(unsigned node){if(!wide_on()||!node||!readable(node,0x3c)||load(node+0x34)!=1)return;const unsigned data=load(node+0x38);if(!data||!readable(data,0x1dc))return;
 const unsigned context=load(0x5f4c8c),view=load(data+4);const unsigned vd=view&&readable(view,0x3c)&&load(view+0x34)==3?load(view+0x38):0;
 const auto name=pose_name(node,36);
 const bool world=context&&readable(context,8)&&load(context+4)==node&&vd&&readable(vd,16)&&load(vd)==0&&load(vd+4)==0&&load(vd+8)==host.display.width&&load(vd+12)==host.display.height&&name!="labcam"&&name!="zoomcam"&&name!="camx";
 static std::set<unsigned>seen;if(FILE*log=wide_log_file();log&&seen.insert(node).second){std::fprintf(log,"seen frame %u node %08x %s context %08x active %08x view %08x rect %u,%u %ux%u display %ux%u world %u\n",host.frames,node,name.c_str(),context,context&&readable(context,8)?load(context+4):0,vd,vd&&readable(vd,16)?load(vd):0,vd&&readable(vd,16)?load(vd+4):0,vd&&readable(vd,16)?load(vd+8):0,vd&&readable(vd,16)?load(vd+12):0,host.display.width,host.display.height,unsigned(world));std::fflush(log);}
 if(!world){wide_restore(node);return;}
 wide_world_frame=host.frames;
 auto&c=wide_cameras[data];if(wide_owns(data,c))return;
 mw34::vkscene::HostFpEnvironment fp;
 const double old_h=wide_float(data+0xe8),old_half=wide_float(data+0xf0),old_cot=wide_float(data+0x1d4);
 if(old_h<=0.0||old_h>=3.141592653589793||old_half<=0.0||old_cot<=0.0||!host.display.height||!host.display.width)deny("Widescreen camera contract unavailable",node);
 const double ratio=(double(mw34::vkscene::Renderer::remaster_width())/mw34::vkscene::Renderer::remaster_height())/(double(host.display.width)/double(host.display.height));
 const double new_h=2.0*std::atan(std::tan(old_h*0.5)*ratio);
 c.raw_h=load(data+0xe8);c.raw_half=load(data+0xf0);c.raw_cot=load(data+0x1d4);
 wide_store_float(data+0xe8,float(new_h));wide_store_float(data+0xf0,float(new_h*0.5));wide_store_float(data+0x1d4,float(1.0/std::tan(new_h*0.5)));
 c.wide_h=load(data+0xe8);c.wide_half=load(data+0xf0);c.wide_cot=load(data+0x1d4);c.applied=true;store(data+0xf8,1);store(data+0x138,1);++wide_updates;
 FILE*log=wide_log_file();
 if(log){std::fprintf(log,"frame %u camera %08x %s viewport %ux%u h %.9g -> %.9g v %.9g cot %.9g -> %.9g zoom %.9g\n",host.frames,node,name.c_str(),host.display.width,host.display.height,old_h,new_h,double(wide_float(data+0xec)),old_cot,double(wide_float(data+0x1d4)),double(wide_float(data+0xd8)));std::fflush(log);}
}
// Explicit original widget draw scopes, including split lifted tail bodies.
// Return addresses are recorded by Stage before each original nested CALL.
enum WideHudRole:unsigned{WideWorld=0,WideLeft=1,WideRight=2,WideCenter=3,WideGauges=4,WideReticle=5,WideZoom=6,WideZoomBorder=7};
unsigned wide_radar_mode{};
unsigned wide_hud_role(){if(frontend_on()||!wide_on())return WideWorld;
 for(unsigned i=depth;i>0;--i){const unsigned pc=returns[i-1];
  switch(pc){
   // 444230's child virtual +28 returns here. Unlike the reticle's +24
   // image/sprite update (4441B8), this draws the zoom camera and its mask.
   case 0x444244:return WideZoom;
   // Original 43C6B0 clears depth before either status preview draws.
   case 0x43c72a:return WideLeft;
   case 0x43c748:return WideRight;
   // 442E30's rectangle child +24, distinct from circle child 442F33 and
   // the root reticle sprite 4441FC. Its four lines share one zoom viewport.
   case 0x442f49:return WideZoomBorder;
   case 0x4414b8:case 0x4414c8:case 0x4414d8:return target_marker_zoom()?WideZoom:WideWorld;
   case 0x44154b:case 0x44155b:return WideWorld;
   case 0x4452e8:case 0x445312:case 0x445322:case 0x445332:case 0x445342:case 0x43ca7e:case 0x43cf76:case 0x43cfac:case 0x43cff2:return WideRight;
   case 0x4452f2:case 0x445302:case 0x445352:case 0x445362:case 0x445372:case 0x445382:case 0x445392:case 0x43cf3b:return WideLeft;}
  if(pc>=0x43dd00&&pc<0x43f0bf)return wide_radar_mode?WideCenter:WideLeft;
  if(pc>=0x441410&&pc<0x441560)return WideLeft;
  if((pc>=0x442500&&pc<0x4425ca)||(pc>=0x446680&&pc<0x4466f2)||(pc>=0x448450&&pc<0x4484ab))return WideRight;
  if((pc>=0x447410&&pc<0x447451)||(pc>=0x40f680&&pc<0x40f6a5))return WideCenter;
  if(pc>=0x43f620&&pc<0x43f654)return WideCenter;
  if(pc>=0x4452c0&&pc<0x445398)return WideGauges;
  if(pc>=0x4441a0&&pc<0x444248)return WideReticle;
  if(pc==0x43c767)return WideLeft;if(pc==0x43c77d||pc==0x43c797||pc==0x43c7c2)return WideRight;if(pc==0x43c7e1||pc==0x43c7c7)return WideCenter;
 }return wide_world_frame==host.frames?WideWorld:WideCenter;
}
float wide_hud_factor(unsigned w,unsigned h){return (float(mw34::vkscene::Renderer::remaster_width())/mw34::vkscene::Renderer::remaster_height())/(float(w)/float(h));}
float wide_zoom_border_anchor(){
 // Original 5A38F0 keeps its line-array this in EDI; 562940 and the line
 // provider dispatch preserve it. The zoom owns that widget at +754.
 // Read the live owner/camera rather than a previous-frame cached rectangle:
 // the +24 border can run before the first +28 camera preview.
 const unsigned poly=state.gpr.rdi.dword;
 if(poly<0x754||!readable(poly,0xe0)||load(poly)!=0x5c0580||load(poly+0xdc)!=5)deny("Widescreen zoom border widget unavailable",poly);
 const unsigned zoom=poly-0x754;
 if(!readable(zoom,0x3c)||load(zoom)!=0x5c0608)deny("Widescreen zoom border owner unavailable",zoom);
 const unsigned node=load(zoom+0x38),context=load(0x5f4c8c);
 if(!context||!readable(context,8)||!load(context+4)||!node||!readable(node,0x3c)||load(node+0x34)!=1||pose_name(node,36)!="zoomcam")deny("Widescreen zoom border camera unavailable",node);
 const unsigned data=load(node+0x38),view=data&&readable(data,8)?load(data+4):0;
 const unsigned vd=view&&readable(view,0x3c)&&load(view+0x34)==3?load(view+0x38):0;
 if(!vd||!readable(vd,16))deny("Widescreen zoom border viewport unavailable",view);
 const int x=int(load(vd)),y=int(load(vd+4)),w=int(load(vd+8)),h=int(load(vd+12));
 if(x<0||y<0||w<=0||h<=0||std::int64_t(x)+w>host.display.width||std::int64_t(y)+h>host.display.height)deny("Widescreen zoom border viewport outside target",vd);
 return float(x)+float(w)*.5f;
}
float wide_anchor(unsigned role,float middle,unsigned w){
 if(role==WideLeft)return 0.f;if(role==WideRight)return float(w);if(role==WideCenter)return float(w)*.5f;
 if(role==WideZoomBorder)return wide_zoom_border_anchor();
 // The recovered gauge group contains separate left heat/coolant and right
 // speed/fuel anchors. No projected world markers pass through this scope.
 if(role==WideGauges)deny("Unresolved original gauge draw scope",unsigned(middle));
 return middle; // Reticle/sprite center follows the original world projection.
}
RECT wide_rect(RECT r,unsigned role,unsigned w,unsigned h){
 if(!wide_on()||role==WideWorld||role==WideReticle||role==WideZoomBorder)return r;
 // Full-target clears initialize the physical margins as well as menu content.
 if(r.left==0&&r.top==0&&r.right==LONG(w)&&r.bottom==LONG(h))return r;
 const float a=wide_anchor(role,role==WideZoom?(float(r.left)+float(r.right))*.5f:0.f,w),k=wide_hud_factor(w,h);
 r.left=LONG(std::floor(a+(float(r.left)-a)/k));r.right=LONG(std::ceil(a+(float(r.right)-a)/k));return r;
}
void wide_adapt_tl(mw34::vkscene::Scene&sc,mw34::vkscene::Draw&d,unsigned role,const float*center_hint=nullptr){if(frontend_on()||!wide_on()||!role)return;
 const float k=wide_hud_factor(sc.width,sc.height);float lo=1e30f,hi=-1e30f;
 // All zoom-camera batches share their original viewport/scissor midpoint.
 // A separate mesh-batch bbox would leave each part at a stretched position.
 // This is an edge coordinate; D3D TL/model positions acquire +0.5 in the
 // vertex shader, so transform that position and then remove the half pixel.
 // The original D3D scissor is full-target even for zoom. Its midpoint
 // is a clipping bound, not the engine zoom camera's projection center.
 if(role==WideZoom&&!center_hint)deny("Widescreen zoom draw has no captured camera anchor",role);
 const float zoom_a=role==WideZoom?*center_hint:0.f;
 if(FILE*log=wide_log_file();log&&role==WideZoom&&host.frames%100==0){static unsigned last=~0U;if(last!=host.frames){last=host.frames;
  std::fprintf(log,"zoom-adapt frame %u target %ux%u scissor %d,%d %ux%u old-anchor %.9g camera-anchor %.9g\n",host.frames,sc.width,sc.height,d.scissor.offset.x,d.scissor.offset.y,d.scissor.extent.width,d.scissor.extent.height,double(float(d.scissor.offset.x)+float(d.scissor.extent.width)*.5f),double(zoom_a));std::fflush(log);}}

 if(d.model){auto m=std::make_shared<mw34::vkscene::ModelInstance>(*d.model);const float a=wide_anchor(role,role==WideZoom?zoom_a:m->projection[3],sc.width);m->projection[1]/=k;m->projection[3]=role==WideReticle?a+(m->projection[3]-a)/k:a+(m->projection[3]+.5f-a)/k-.5f;d.model=std::move(m);}
 else{for(unsigned i=d.first;i<d.first+d.count;++i){float x;std::memcpy(&x,sc.vertices.data()+size_t(i)*32,4);lo=std::min(lo,x);hi=std::max(hi,x);}const float a=wide_anchor(role,role==WideZoom?zoom_a:(center_hint?*center_hint:(lo+hi)*.5f),sc.width);
  if(d.sun_tl){auto light=std::make_shared<mw34::sun::Tl>(*d.sun_tl);light->projection[1]/=k;light->projection[3]=a+(light->projection[3]+.5f-a)/k-.5f;d.sun_tl=std::move(light);}
  if(d.sky_view){auto view=std::make_shared<mw34::sun::Tl>(*d.sky_view);view->projection[1]/=k;view->projection[3]=a+(view->projection[3]+.5f-a)/k-.5f;d.sky_view=std::move(view);}
  for(unsigned i=d.first;i<d.first+d.count;++i){float x;auto*p=sc.vertices.data()+size_t(i)*32;std::memcpy(&x,p,4);x=role==WideReticle?a+(x-a)/k:a+(x+.5f-a)/k-.5f;std::memcpy(p,&x,4);}}
 if(d.camera_view){auto view=std::make_shared<mw34::temporal::Snapshot>(*d.camera_view);
  if(d.model)view->projection=d.model->projection;
  else if(d.sun_tl)view->projection=d.sun_tl->projection;
  else if(d.sky_view)view->projection=d.sky_view->projection;
  else{d.camera_view.reset();view.reset();} // Unproven adapted TL projection is not temporal input.
  if(view)d.camera_view=std::move(view);}
 if(role==WideLeft||role==WideRight||role==WideCenter||role==WideZoom){const float a=wide_anchor(role,role==WideZoom?zoom_a:0.f,sc.width);const int x0=int(std::floor(a+(float(d.scissor.offset.x)-a)/k)),x1=int(std::ceil(a+(float(d.scissor.offset.x+int(d.scissor.extent.width))-a)/k));d.scissor.offset.x=x0;d.scissor.extent.width=unsigned(std::max(0,x1-x0));}
}
