// Optional exact-pixel registrations. Upgrade-derived data stays outside game
// banks; no original pixels, UVs, alpha planes or animation frames are changed.
void surface_detail_load(){
 auto&state=surface_normals;
 for(unsigned role=1;role<=3;++role){
  if(!mw34::detail::enabled(role))continue;
  const char*name=role==1?"MW34_WATER_NORMALS":role==2?"MW34_SURF_NORMALS":"MW34_CLOUD_NORMALS";
  const char*path=std::getenv(name);
  if(!path||!*path)throw std::runtime_error(std::string("Enabled surface detail requires ")+name);
  if(std::filesystem::file_size(path)>16ULL*1024*1024)throw std::runtime_error("Surface detail pack exceeds 16 MiB budget");
  std::ifstream file(path,std::ios::binary);if(!file)throw std::runtime_error("Configured surface detail pack is missing");
  if(!mw34::materials::normal_maps_enabled()){
   for(const auto&[key,index]:mw34::materials::read_surface_normal_header(file)){
    if(state.authored.count(key)||!state.detail_roles.emplace(key,role).second)throw std::runtime_error("Conflicting surface detail registration");
    state.bindings[key]=-1;state.authored.insert(key);
   }
  }else{
   auto parsed=mw34::materials::read_surface_normals(file);auto&o=override_state();
   const size_t offset=o.normal_textures.size();
   if(offset+parsed.pack.images.size()>size_t(std::numeric_limits<int>::max()))throw std::runtime_error("Surface detail index overflow");
   for(const auto&[key,index]:parsed.bindings){
    if(index==mw34::materials::no_normal||state.authored.count(key)||!state.detail_roles.emplace(key,role).second)throw std::runtime_error("Conflicting or empty surface detail registration");
    state.bindings[key]=int(offset+index);state.authored.insert(key);
   }
   for(auto&image:parsed.pack.images){OverrideTexture t{};t.name=std::move(image.name);t.width=image.width;t.height=image.height;t.hash=image.hash;t.pixels32=std::move(image.pixels);o.normal_textures.push_back(std::move(t));}
   if(o.log.is_open())o.log<<"{\"event\":\"surface_detail_loaded\",\"role\":"<<role<<",\"bindings\":"<<parsed.bindings.size()<<",\"images\":"<<parsed.pack.images.size()<<"}\n";
  }
 }
}
unsigned surface_detail_role(VSurfaceRec&surface){
 surface_normal_binding(surface);
 const auto found=surface_normals.cache.find(surface.guest);
 return found==surface_normals.cache.end()?0:found->second.detail;
}
