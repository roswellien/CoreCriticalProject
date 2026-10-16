// Experimental PM entry driver in the existing native host composition.
// Uses literal input images and native dependency attach, with no BEFORE/AFTER pack.
int main(int argc,char**argv){
 ::SetUnhandledExceptionFilter(host_crash);
 try{
  require(argc==3,"Usage: pirates_moon_native exact-installation fresh-output-directory");
  const auto installation=std::filesystem::absolute(argv[1]);
  const std::filesystem::path output=std::filesystem::absolute(argv[2]);
  std::array<std::vector<std::byte>,5>images;
  for(unsigned i=0;i<images.size();++i){images[i]=read_file((installation/mf::pm_module_names[i]).string().c_str());require(m4::sha256(images[i])==mf::pm_module_hashes[i],"Exact PM executable/dependency identity required");}
  require(!std::filesystem::exists(output)&&std::filesystem::create_directories(output),"Fresh PM execution directory required");
  // Environment drives the same loader path as the MW3 play host. No accepted bounded-entry route is used.
  ::SetEnvironmentVariableA("MW34_STARTUP","loader");
  for(const char*flag:{"MW34_GPU_HUD","MW34_SEH_TEST"}){const char*v=std::getenv(flag);require(!v||!*v||*v=='0',"MW3 address-specific HUD/SEH test hooks are not recovered for PM");}
  Policy policy;policy.stack_low={0x20001000};policy.stack_bytes=4096;policy.heap_bytes=4096;
  auto r=Runtime::from_research_image(images[0],mf::pm_module_hashes[0],policy);
  seed(r,host_seed_input());
  mf::Host host;hs::HostHeap heap;
  hs::heap=&heap;attach_host=&heap;mfc_host=&host;loader_runtime=&r;
  struct Clear{~Clear(){hs::heap=nullptr;attach_host=nullptr;mfc_host=nullptr;loader_runtime=nullptr;hs::fdiv_inplace_hook=nullptr;}}clear;
  host.msvcrt=&images[1];
  (void)mf::map_provider_code(r,images[1],true);
  mf::map_image(r,images[2],images[1],host);
  mf::map_module(r,images[3],mf::pm_module_hashes[3],"MSVCP60.DLL",images[1],host);
  mf::bind_game(r,images[0],images[2],images[1],host);
  for(unsigned i=0;i<4;++i)host.paths[mf::pm_module_bases[i]]= (installation/mf::pm_module_names[i]).string();
  host.frame_dir=(output/"frames").string();std::filesystem::create_directory(host.frame_dir);
  if(const char*q=std::getenv("MW34_INPUT_SCRIPT")){
   std::ifstream input(q);require(bool(input),"PM input script readable");std::string line;
   while(std::getline(input,line)){if(line.empty()||line[0]=='#')continue;
    mf::Host::ScriptEvent event{};event.timed=line[0]=='+';std::istringstream fields(event.timed?line.substr(1):line);std::string kind;
    require(bool(fields>>event.frame>>kind),"PM input script event header");
    if(kind=="mouse"){event.mouse=true;require(bool(fields>>event.dx>>event.dy>>event.buttons),"PM mouse input event");}
    else if(kind=="key"){std::string state;require(bool(fields>>std::hex>>event.scan>>state)&&(state=="down"||state=="up"),"PM key input event");event.down=state=="down";}
    else require(false,"PM input event kind");
    require(host.script.empty()||(host.script.back().timed?event.timed&&host.script.back().frame<=event.frame:(event.timed||host.script.back().frame<=event.frame)),"PM input events ascending: frames then relative mission milliseconds");
    host.script.push_back(event);
   }
   host.scripted=true;
  }
  if(const char*v=std::getenv("MW34_VIRTUAL_CLOCK");v&&*v){const double ms=std::stod(v);require(host.scripted&&ms>=1&&ms<=1000,"PM virtual clock requires a script and 1..1000 ms per frame");host.vclock_step_us=std::uint64_t(ms*1000);host.vclock_us=1000000;host.tick_uptime=true;}
  host.tick_init();
  host.loadable.push_back({"Mech3Msg.dll",(installation/"Mech3Msg.dll").string(),images[4],mf::pm_module_hashes[4]});
  if(const char*b=std::getenv("MW34_FRAME_BUDGET"))host.frame_budget=unsigned(std::stoul(b));
  if(const char*b=std::getenv("MW34_FRAME_DUMP"))host.frame_dump=unsigned(std::stoul(b));
  hs::fdiv_inplace_hook=&fdiv_in_place;
  run_attach(r);require(attach_saved&&attach_result.complete,"PM shared CRT attach to command-line writer");
  {auto text=std::string("\"")+(installation/"Mech3.exe").string()+"\"";
   if(const char*v=std::getenv("MW34_PM_NOFMV");v&&*v=='1')text+=" -nofmv";
   std::vector<std::byte>line(text.size()+1);std::memcpy(line.data(),text.c_str(),line.size());
   r.memory().map({cm::buffer},unsigned(line.size()),Permissions::read|Permissions::write);
   r.memory().write({cm::buffer},line);r.memory().protect({cm::buffer},Permissions::read);r.memory().store<unsigned>({cm::global},cm::buffer);}
  run_resume(r);require(host.all_attached(),"PM required dependency attaches complete");
  r.memory().map({mf::stack_extension},mf::game_stack_low-mf::stack_extension,Permissions::read|Permissions::write);
  std::cout<<"PM data imports bound: "<<mf::bind_game_data(r,host)<<"\n";
  auto&s=*reinterpret_cast<State*>(r.remill_state().data());s.gpr.rsp.dword=frame;s.gpr.rip.dword=mf::crt_entry;
  r.memory().store<unsigned>({frame},Runtime::external_return);
  static int token;mf::Stage stage(r,heap,host,mf::stage_token(r,&token),mf::Stage::Kind::initterm);
  try{stage.run();}catch(const std::exception&e){std::cerr<<"PM native boundary: "<<e.what()<<" bodies="<<stage.bodies<<" services="<<(stage.apis_dropped+stage.apis.size())<<" frames="<<host.frames<<"\n";
   if(const char*v=std::getenv("MW34_PM_FAULT_FRAME");v&&*v=='1'){
    std::cerr<<"PM fault frame: esp=0x"<<std::hex<<s.gpr.rsp.dword<<" ecx=0x"<<s.gpr.rcx.dword<<" words=";
    try{for(unsigned i=0;i<9;++i)std::cerr<<" 0x"<<r.memory().load<unsigned>({s.gpr.rsp.dword+4*i});}catch(...){std::cerr<<" [unreadable]";}
    std::cerr<<std::dec<<"\n";
   }
   throw;}
  throw std::runtime_error("PM CRT entry returned without normal process shutdown");
 }catch(const std::exception&e){std::cerr<<"PM experimental host stopped: "<<e.what()<<"\n";return 1;}
}
