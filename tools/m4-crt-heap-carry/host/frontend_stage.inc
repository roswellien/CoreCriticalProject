// The original modal Lab owns one canvas across initialization, its loop and
// teardown. This is presentation state, not a replacement for its game state.
bool frontend_lab{};
bool frontend_on() const { return frontend_lab&&mw34::vkscene::Renderer::remaster_width()!=0; }
void frontend_switch(bool active){
 if(frontend_lab==active)return;
 if(hud_gpu_active){hud_flush();hud_gpu_active=false;}
 gpu_sync(0);gpu_protect(false);
 // Finish the previous composition domain before invalidating residency.
 // The next scene uploads the authoritative original logical buffer once.
 host.res_rt=host.res_zb=0;host.res_ver_rt=host.res_ver_zb=0;
 frontend_lab=active;wide_world_frame=~0U;
 if(const char*p=std::getenv("MW34_FRONTEND_LOG");p&&*p){if(FILE*f=std::fopen(p,"a")){std::fprintf(f,"canvas frame %u lab %u logical %ux%u\n",host.frames,unsigned(active),host.display.width,host.display.height);std::fclose(f);}}
}
void*frontend_body(State*s,unsigned target,void*p,Body body){
 const bool previous=frontend_lab;
 if(target==0x448960){frontend_switch(true);try{return body(s,target,p);}catch(...){frontend_switch(previous);throw;}}
 void*result{};try{result=body(s,target,p);}catch(...){frontend_switch(false);throw;}
 frontend_switch(false);return result;
}
void frontend_input_point(POINT&point,bool physical,HWND window){
 if(!frontend_on()||window!=host.display.window)return;
 RECT client{};if(!::GetClientRect(window,&client)||client.right<=0||client.bottom<=0)deny("Frontend client canvas unavailable",0);
 mw34::vkscene::HostFpEnvironment fp;
 const auto fit=mw34::frontend::CanvasFit::fit(host.display.width,host.display.height,unsigned(client.right),unsigned(client.bottom));
 point=physical?POINT{fit.physical_x(point.x),fit.physical_y(point.y)}:POINT{fit.logical_x(point.x),fit.logical_y(point.y)};
}
