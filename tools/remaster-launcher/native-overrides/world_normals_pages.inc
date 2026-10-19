// Optional automatic world normals reuse validated BWSNR2 pages. Header keys
// register geometry without allocating pixels; each page is read on first use.
void surface_normals_load_world(){
 const char*configured=std::getenv("MW34_WORLD_NORMALS");if(!configured||!*configured)return;
 auto&state=surface_normals;const std::filesystem::path manifest(configured);
 std::ifstream list(manifest);if(!list)throw std::runtime_error("Configured world-normal manifest is missing");
 std::string line;if(!std::getline(list,line))throw std::runtime_error("Empty world-normal manifest");
 if(!line.empty()&&line.back()=='\r')line.pop_back();if(line!="MW34SNP1")throw std::runtime_error("Invalid world-normal manifest version");
 std::set<std::string>files;std::set<mw34::materials::SurfaceKey>unique;std::uint64_t total{};
 while(std::getline(list,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  if(line.empty()||line.size()>80||line=="."||line==".."||line.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")!=std::string::npos||!files.insert(line).second||files.size()>256)throw std::runtime_error("Invalid world-normal page name/count");
  SurfaceNormalState::Page page;page.path=manifest.parent_path()/line;
  const auto size=std::filesystem::file_size(page.path);total+=size;
  if(size>16*1024*1024||total>512*1024*1024)throw std::runtime_error("World-normal package exceeds byte budget");
  std::ifstream input(page.path,std::ios::binary);if(!input)throw std::runtime_error("World-normal page is missing");
  auto header=mw34::materials::read_surface_normal_header(input);
  for(const auto&entry:header){
   if(!unique.insert(entry.first).second||unique.size()>16384)throw std::runtime_error("Duplicate/excess world-normal texture keys");
   page.keys.insert(entry.first);state.world_bindings.emplace(entry.first,state.pages.size());
   state.bindings.emplace(entry.first,-1); // Authored catalog indices take precedence.
  }
  state.pages.push_back(std::move(page));
 }
 if(!list.eof()||state.pages.empty())throw std::runtime_error("Incomplete world-normal manifest");
 auto&log=override_state().log;if(log.is_open())log<<"{\"event\":\"world_normal_catalog_loaded\",\"pages\":"<<state.pages.size()<<",\"bindings\":"<<unique.size()<<",\"images\":0,\"method\":\"automatic color-derived preview; lazy pages\"}\n";
}
void surface_normals_load_page(size_t index){
 auto&state=surface_normals;auto&page=state.pages.at(index);if(page.loaded)return;
 std::ifstream input(page.path,std::ios::binary);if(!input)throw std::runtime_error("World-normal page disappeared");
 auto parsed=mw34::materials::read_surface_normals(input);
 if(parsed.bindings.size()!=page.keys.size())throw std::runtime_error("World-normal page keys changed");
 for(const auto&entry:parsed.bindings)if(!page.keys.count(entry.first))throw std::runtime_error("World-normal page identity changed");
 std::uint64_t bytes{};for(const auto&image:parsed.pack.images)bytes+=image.pixels.size()*4;
 if(state.world_bytes+bytes>512*1024*1024)throw std::runtime_error("Resident automatic normals exceed budget");
 auto&o=override_state();const auto offset=o.normal_textures.size();
 if(offset+parsed.pack.images.size()>size_t(std::numeric_limits<int>::max()))throw std::runtime_error("World-normal index overflow");
 for(auto&image:parsed.pack.images){OverrideTexture t{};t.name=std::move(image.name);t.width=image.width;t.height=image.height;t.hash=image.hash;t.pixels32=std::move(image.pixels);o.normal_textures.push_back(std::move(t));}
 for(const auto&[key,normal]:parsed.bindings){
  // A stock authored binding remains authoritative even if this page contains
  // an automatic estimate of the same texture. Explicit authored exclusions win.
  if(!state.authored.count(key))state.bindings.at(key)=normal==mw34::materials::no_normal?-1:int(offset+normal);
 }
 state.world_bytes+=bytes;page.loaded=true;
 if(o.log.is_open())o.log<<"{\"event\":\"world_normal_page_loaded\",\"page\":"<<index<<",\"images\":"<<parsed.pack.images.size()<<",\"resident_bytes\":"<<state.world_bytes<<"}\n";
}
