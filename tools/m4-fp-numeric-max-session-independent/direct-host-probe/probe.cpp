// Direct host observations. The frozen earlier cleanup test is not a boundary test.
#define main historical_independent_fixture_main
#include "../controls.cpp"
#undef main
struct alignas(16) Snapshot {
 std::array<std::byte,512>fx{};
 std::array<std::byte,28>env{};
};
void snap(Snapshot&s){__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(s.fx),"=m"(s.env)::"memory");}
void restore(const Snapshot&s){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(s.fx),"m"(s.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
struct Record {unsigned cw,mode,denied,reserved;Snapshot before,after,cleanup;};
int main(int argc,char**argv){try{
 check(argc==5,"Independent direct host probe arguments");
 auto g=file(argv[1]),d=file(argv[2]),o=file(argv[3]);
 const ni::Proof p{m4::sha256(o),"73a4fa0b37415a7510775d4a1939872a598168b92cc4f9b5bcf581f97e5f312e"};
 std::array<Record,6>records{};unsigned count=0;
 for(unsigned cw:{0x7fU,0x37fU,0xb7fU})for(unsigned mode:{0U,1U}){
  Fixture f(g,d,p,1,0,0,cw);if(mode)f.permission(ni::output,Permissions::read);
  Snapshot initial{};snap(initial);
  const double live_a=1.25,live_b=42.5;const float one=1,three=3;double scratch{};const auto word=static_cast<std::uint16_t>(cw);
  __asm__ volatile("fninit\n\tfldcw %0\n\tfldl %1\n\tfldl %2\n\tflds %3\n\tfdivs %4\n\tfstpl %5"::"m"(word),"m"(live_a),"m"(live_b),"m"(one),"m"(three),"m"(scratch):"memory","st","st(1)","st(2)");
  auto&r=records[count++];r.cw=cw;r.mode=mode;
  {ni::Session::Borrow b(*f.session);snap(r.before);
   try{f.r.call_direct({ni::root},{ret});}catch(const std::exception&){r.denied=1;}
   snap(r.after);
  }
  restore(initial);snap(r.cleanup);
  check(bool(r.denied)==bool(mode),"Actual positive/fault probe route");
 }
 std::ofstream output(argv[4],std::ios::binary|std::ios::trunc);output.write(reinterpret_cast<const char*>(records.data()),sizeof(records));if(!output)throw std::runtime_error("Independent raw probe write");
 std::cout<<"{\"passed\":true,\"records\":6,\"record_bytes\":"<<sizeof(Record)<<",\"snapshot_bytes\":"<<sizeof(Snapshot)<<",\"after_capture_before_restore\":true,\"original_executed\":false}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
