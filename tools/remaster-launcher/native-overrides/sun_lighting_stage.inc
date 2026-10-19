struct SunCaptureFp {
 alignas(16) unsigned char fx[512];DWORD error{};
 SunCaptureFp(){__asm__ volatile("fxsave64 %0":"=m"(fx)::"memory");error=::GetLastError();}
 ~SunCaptureFp(){::SetLastError(error);__asm__ volatile("fxrstor64 %0"::"m"(fx):"memory",
  "xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7",
  "xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
};
// The active renderer binding identifies the actual world/zoom camera. Its
// camera-to-world matrix starts at +44: original 4F444A copies 12 matrix
// words there before 520B00 prepares the inverse view. This is distinct from the
// optional mesh world cache. Combine it with the captured local-to-camera
// matrix; this retains all original parent, animation and instance transforms.
bool sun_camera_world(OverrideMatrix& matrix) {
 const unsigned data=load(0x7402f4),context=load(0x5f4c8c);
 unsigned node=context&&readable(context,8)?load(context+4):0;
 if(!data||!readable(data,0x100))throw std::runtime_error("Sun active camera unavailable");
 bool admitted=node&&readable(node,0x3c)&&load(node+0x34)==1&&load(node+0x38)==data&&distance_world(node,data);
 const unsigned owner=distance_zoom_owner();
 if(!admitted&&owner&&readable(owner,0x3c)){
  node=load(owner+0x38);admitted=node&&readable(node,0x3c)&&load(node+0x38)==data&&distance_zoom(node,data);
 }
 if(!admitted)return false; // Original preview/Lab/target-schematic cameras.
 // Original 520B00 negates camera columns Y/Z before forming the renderer
 // view inverse. The unchanged camera-to-world copy is at 73FC00; 73FBC0
 // receives its inverse. Using the node matrix without this conversion would
 // invert terrain up and misorient every world light.
 auto expected=override_matrix(data+0x44);
 for(unsigned row=0;row<3;++row){expected[row*4+1]=-expected[row*4+1];expected[row*4+2]=-expected[row*4+2];}
 matrix=override_matrix(0x73fc00);
 for(unsigned i=0;i<12;++i)if(matrix[i]!=expected[i])throw std::runtime_error("Sun camera binding and renderer basis disagree");
 return true;
}
void sun_capture_world(mw34::vkscene::ModelInstance& instance,unsigned) {
 if(!mw34::sun::settings().enabled)return;
 SunCaptureFp preserve;
 mw34::vkscene::HostFpEnvironment fp;
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 auto local_camera=override_identity();for(unsigned i=0;i<12;++i)local_camera[i]=instance.camera[i];
 instance.sun_normal=mw34::sun::normal_matrix(override_product(camera_world,local_camera));instance.sun_eligible=true;
}
void sun_capture_model(mw34::vkscene::ModelInstance& instance,unsigned,
                       const OverrideMatrix&,const OverrideMatrix& batch_camera) {
 if(!mw34::sun::settings().enabled||frontend_on()||override_status_preview())return;
 SunCaptureFp preserve;
 mw34::vkscene::HostFpEnvironment fp;
 OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;
 instance.sun_normal=mw34::sun::normal_matrix(override_product(camera_world,batch_camera));instance.sun_eligible=true;
}
