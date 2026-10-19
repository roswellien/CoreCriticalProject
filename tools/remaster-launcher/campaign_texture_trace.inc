// Optional capture-build trace: first world draw submission for a full material
// identity. Submission is not proof of depth-visible pixels. No gameplay hooks.
void campaign_texture_trace(const D3DCmd& command,const mw34::vkscene::Draw& draw,unsigned texture){
 static const char* path=std::getenv("MW34_CAMPAIGN_TEXTURE_TRACE");
 if(!path||!*path||!texture||!draw.count||draw.sky||frontend_on()||
    (command.hud_role!=WideWorld&&command.hud_role!=WideZoom)||
    (command.model&&!command.model->world)||(!command.sun_tl&&!(command.model&&command.model->world)))return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 auto*surface=vsurface(texture);if(!surface||surface->bpp!=16||surface->pitch<surface->width*2||!surface->width||!surface->height)return;
 const unsigned format=surface->tex_masks[0]==0xf800?1:surface->tex_masks[0]==0x7c00?2:surface->tex_masks[0]==0x0f00?3:0;
 if(!format)return;
 static std::ofstream log(path,std::ios::out|std::ios::trunc);
 if(!log)throw std::runtime_error("Campaign texture encounter trace cannot be opened");
 static std::set<std::tuple<unsigned,std::uint64_t,unsigned,unsigned,unsigned,unsigned>> surfaces;
 const auto stamp=std::make_tuple(surface->guest,surface->version,surface->width,surface->height,surface->mem,format);
 if(surfaces.count(stamp))return;
 gpu_sync(surface->guest);
 std::vector<unsigned char> bytes(size_t(surface->width)*surface->height*2);
 for(unsigned y=0;y<surface->height;++y)get_bytes(surface->mem+y*surface->pitch,bytes.data()+size_t(y)*surface->width*2,surface->width*2);
 const auto hash=mw34::materials::normal_hash(bytes.data(),bytes.size());
 surfaces.insert(stamp);
 static std::set<mw34::materials::SurfaceKey> identities;
 if(!identities.insert({surface->width,surface->height,format,hash}).second)return;
 log<<"{\"event\":\"first_world_texture_submission\",\"sequence\":"<<identities.size()
    <<",\"frame\":"<<host.frames+1<<",\"width\":"<<surface->width<<",\"height\":"<<surface->height
    <<",\"format\":"<<format<<",\"hash\":"<<hash<<",\"terrain_gpu\":"<<(command.model&&command.model->world?"true":"false")
    <<",\"alpha_blend\":"<<unsigned(draw.key.blend)<<",\"alpha_test\":"<<((draw.push.mode[0]&32)?"true":"false")<<"}\n";
 log.flush();if(!log)throw std::runtime_error("Campaign texture encounter trace write failed");
}
