// Connected source-role/public-memory controls. No source AFTER input.
#include "carry.hpp"
#include "locale_batch.hpp"
static unsigned mfc_control_mode{};
static void mfc_mutate(mw34::m4_mixed::Context&c,unsigned phase){
 if(phase!=13)return;using namespace mw34;auto&r=c.runtime();
 auto scalar=[&](unsigned address,unsigned value){r.memory().store<unsigned>({address},value);};
 switch(mfc_control_mode){
 case 1:{unsigned v=4;std::memcpy(reinterpret_cast<std::byte*>(&c.state())+2184,&v,4);break;}
 case 2:r.memory().protect({0x5f401000},mw34::Permissions::read|mw34::Permissions::write);r.memory().store<std::uint8_t>({0x5f401083},0xcc);r.memory().protect({0x5f401000},mw34::Permissions::read|mw34::Permissions::execute);break;
 case 3:scalar(0x5f498330,0);break;
 case 4:scalar(0x7ffdee1c,0x33005000);break;
 case 5:r.memory().store<std::uint8_t>({0x33005014},2);break;
 case 6:scalar(0x3300200c,0x33005000);break;
 case 7:r.memory().protect({0x33005000},mw34::Permissions::read);break;
 case 8:r.memory().protect({0x33007000},mw34::Permissions::read);break;
 case 9:scalar(0x7802e0c8,0);break;
 case 10:scalar(0x780379c0,1251);break;
 case 11:scalar(0x5f4cb008,0);break;
 case 12:{unsigned v=4;std::memcpy(reinterpret_cast<std::byte*>(&c.state())+2120,&v,4);break;}
 default:throw std::runtime_error("Unknown authored connected control");
 }
}
static void mfc_retry_snapshot(mw34::m4_mixed::Context&c,mw34::capture_direct::Writer&w,const std::string&p){
 using namespace mw34;using namespace m4_mixed;
 w.append(p+"State.bin",&c.state(),3504);w.append(p+"CPU.bin",&c.runtime().cpu(),40);w.append(p+"FX.bin",c.runtime().fx().data(),512);
 const auto summary=c.registry().summary();w.append(p+"registry-summary.bin",summary.data(),sizeof(summary));
 const auto fault=c.fault();const unsigned status[]{c.completed,unsigned(c.failed()),unsigned(c.runtime().poisoned()),fault.phase,fault.pc,fault.address,fault.step,fault.kind};w.append(p+"Context-status.bin",status,sizeof(status));
 const std::string why=c.failure_reason();w.append(p+"Context-reason.txt",why.data(),why.size());
 std::vector<std::byte>calls;auto put=[&](const void*b,std::size_t n){auto v=static_cast<const std::byte*>(b);calls.insert(calls.end(),v,v+n);};
 for(const auto&a:c.runtime().calls()){const unsigned row[]{a.site.value,a.target.value,a.return_pc.value,unsigned(a.import),unsigned(a.completed),unsigned(a.name.size())};put(row,sizeof(row));put(a.name.data(),a.name.size());}w.append(p+"Runtime-calls.bin",calls.data(),calls.size());
 std::vector<std::array<unsigned,2>>regions;auto add=[&](unsigned a,unsigned n){if(std::none_of(regions.begin(),regions.end(),[&](const auto&x){return x[0]==a&&x[1]==n;}))regions.push_back({a,n});};
 for(unsigned a:pages)add(a,4096);for(unsigned a:registration_pages)add(a,4096);for(auto row:m4_crt_locale_batch::source_pages())add(row.address,4096);
 for(auto row:mc::literal::source_spans)add(row.pc&~4095U,4096);
 const auto input=mc::make_fixture_inputs();for(const auto&row:input.new_mappings)add(row.address,unsigned(row.before.size()));add(0x78037000,4096);add(c.runtime().fs_base().value,4);add(c.runtime().fs_base().value+4,8);add(c.runtime().fs_base().value+0x18,4);
 std::sort(regions.begin(),regions.end());w.append(p+"memory-index.bin",regions.data(),regions.size()*sizeof(regions[0]));
 for(auto row:regions){std::vector<std::byte>b(row[1]);c.runtime().memory().read({row[0]},b);w.append(p+"memory-"+std::to_string(row[0])+"-"+std::to_string(row[1])+".bin",b.data(),b.size());}
 c.control_checkpoint(p.ends_with("retry-before/")?"retry-before":"retry-after");
}
int main(int argc,char**argv){try{
 using namespace mw34;using namespace m4_mixed;need(argc==6,"Connected causal control exact inputs/fresh output");
 auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760),crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);m4::admit_image(std::as_bytes(std::span{game}));
 need(old::sha256(provider)==ni::provider_sha&&old::sha256(crt)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7"&&old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact three physical providers");
 capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer writer(argv[5],options);const unsigned header[]{1,12,14,17,sizeof(Native)};writer.append("control-header.bin",header,sizeof(header));
 for(unsigned mode=1;mode<=12;++mode){mfc_control_mode=mode;mfc_output.clear();Context context(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),0,0x7f,0);const std::string prefix="control-"+std::to_string(mode)+"/";context.before_phase=&mfc_mutate;std::vector<Native>records;records.reserve(14);
  alignas(16)std::array<std::byte,1632>hardware{};MFCConnectedGuarded guarded{&context,0,0,0,&records,false,false};mfc_connected_hardware_call(&guarded,hardware.data());writer.append(prefix+"caller-hardware.bin",hardware.data(),hardware.size());
  const std::string refusal=context.failure_reason();writer.append(prefix+"refusal.txt",refusal.data(),refusal.size());for(unsigned i=0;i<records.size();++i)writer.append(prefix+"phase-"+std::to_string(i)+".bin",&records[i],sizeof(Native));
  need(!guarded.completed&&context.failed()&&context.runtime().poisoned()&&context.completed==13&&records.size()==13&&!refusal.empty(),"Actual precise connected phase13 refusal after13complete roots");context.control_checkpoint("refused");
  mfc_retry_snapshot(context,writer,prefix+"retry-before/");alignas(16)std::array<std::byte,1632>retry_hardware{};MFCConnectedGuarded retry{&context,0,0,0,&records,false,true};mfc_connected_hardware_call(&retry,retry_hardware.data());writer.append(prefix+"retry-hardware.bin",retry_hardware.data(),retry_hardware.size());need(retry.completed,"Actual poisoned Runtime retry refused");mfc_retry_snapshot(context,writer,prefix+"retry-after/");
  context.control_cleanup();context.control_checkpoint("cleaned");for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());context.registry().finish();need(!context.registry().live_handle(),"Actual old registry owner cleanup after external poison");
  const unsigned facts[]{1,mode,13,1,1,1,1,unsigned(context.has_component())};writer.append(prefix+"facts.bin",facts,sizeof(facts));
 }
 const char done[]="12 actual connected MFC denials, unchanged poisoned retries and owned cleanup; no initializer credit\n";writer.append("COMPLETE.txt",done,sizeof(done)-1);writer.finish();std::cout<<done;return 0;
}catch(const std::exception&e){mw34::m4_mixed::observation=nullptr;ni::owner=nullptr;mw34::m4_spi_connected::owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
