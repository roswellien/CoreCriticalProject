// Asset-free execution of a source-bound extracted original perspective loop.
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

using U = std::uint32_t;
extern "C" void* mw34_projection_fixture(void*, U, void*, U);
template<class T> T get(const void* p,unsigned a){T v;std::memcpy(&v,static_cast<const unsigned char*>(p)+a,sizeof(v));return v;}
template<class T> void put(void* p,unsigned a,T v){std::memcpy(static_cast<unsigned char*>(p)+a,&v,sizeof(v));}
extern "C" U __remill_read_memory_32(void* p,U a){return get<U>(p,a);}
extern "C" float __remill_read_memory_f32(void* p,U a){return get<float>(p,a);}
extern "C" void* __remill_write_memory_f32(void* p,U a,float v){put(p,a,v);return p;}
extern "C" unsigned char mw34_attach_m_53f2e0_undefined_8(){return 0;}
extern "C" void __remill_fpu_exception_clear(int){__asm__("fnclex");}
extern "C" int __remill_fpu_exception_test(int mask){unsigned short s;__asm__("fnstsw %0":"=m"(s));return s&mask;}
static void cw(unsigned short v){__asm__("fldcw %0"::"m"(v));}
static unsigned short status(){unsigned short s;__asm__("fnstsw %0":"=m"(s));return s;}
static void dump(const char* name,const void* p,std::size_t n){std::ofstream f(name,std::ios::binary);f.write(static_cast<const char*>(p),n);}
static bool bounded(U b){b&=0x7fffffff;return b==0||(b>=0x3b800000&&b<=0x47800000);}
static bool admitted(const unsigned char* s,const unsigned char* m,unsigned n){
 if(s[2745]!=1||!n||n>64)return false;
 for(U a:{0x73fb80U,0x73fc30U,0x73fb88U,0x73fb98U,0x73fb8cU})if(!bounded(get<U>(m,a)))return false;
 if(!(get<U>(m,0x73fb80)&0x7fffffff))return false;
 for(unsigned i=0;i<n;++i){U a=0x7476a4+12*i;
  if(!bounded(get<U>(m,a))||!bounded(get<U>(m,a+4)))return false;
  U z=get<U>(m,a+8);if(z<0x3b800000||z>0x47800000)return false;
 }return true;
}
int main(){
 constexpr unsigned size=0x750000;
 std::vector<unsigned char> initial(size),full(size),last(size);
 alignas(64) std::array<unsigned char,4096> seed{},a{},b{};
 unsigned cases=0;
 try{
  // Valid distinct 80-bit register payloads, selectors, TOP, flags and padding.
  for(unsigned j=0;j<8;++j){put<std::uint64_t>(seed.data(),2486+16*j,0x8000000000000000ULL+(std::uint64_t(j)<<56));put<unsigned short>(seed.data(),2494+16*j,0x3fff);}
  seed[2737]=1;seed[2739]=1;seed[2741]=1;seed[2743]=1;seed[2745]=1;
  for(unsigned off:{2747,2749,2751,2753,2755,2757})seed[off]=unsigned((off/2)&1);
  put<unsigned short>(seed.data(),2770,0x1800);
  put<unsigned short>(seed.data(),2106,0x1234);put<unsigned short>(seed.data(),2110,0x5678);
  const std::array<float,11> values={0.f,-0.f,0.00390625f,-0.00390625f,1.f,-1.f,65536.f,-65536.f,0.5f,-16.f,123.456f};
  for(unsigned n:{1U,2U,3U,4U,64U})for(unsigned mode=0;mode<12;++mode)for(unsigned pattern=0;pattern<values.size()+3;++pattern){
   std::fill(initial.begin(),initial.end(),0x5a);
   const unsigned short control=static_cast<unsigned short>(0x7f|((mode%3==0?0:mode%3==1?2:3)<<8)|((mode/3)<<10));
   put<unsigned short>(seed.data(),2768,control);
   put<unsigned short>(seed.data(),2770,static_cast<unsigned short>((pattern%8)<<11));
   unsigned exception_index=0;for(unsigned off:{2747,2749,2751,2753,2755,2757})seed[off]=static_cast<unsigned char>((pattern>>exception_index++)&1);
   for(unsigned j=0;j<n;++j){U p=0x7476a4+12*j;put(initial.data(),p,values[(pattern+j)%values.size()]);put(initial.data(),p+4,values[(pattern+2*j+3)%values.size()]);put(initial.data(),p+8,values[(pattern+j)%3==0?2:(pattern+j)%3==1?4:6]);}
   put(initial.data(),0x73fb80,values[(pattern%3==0)?2:(pattern%3==1)?4:6]);
   put(initial.data(),0x73fc30,values[(pattern+2)%values.size()]);put(initial.data(),0x73fb98,values[(pattern+4)%values.size()]);
   put(initial.data(),0x73fb88,values[(pattern+1)%values.size()]);put(initial.data(),0x73fb8c,values[(pattern+3)%values.size()]);
   if(pattern>=values.size()){
    unsigned special=pattern-static_cast<unsigned>(values.size());
    float xy=special==0?65536.f:special==1?0.00390625f:1.f;
    float z=special==0?0.00390625f:special==1?65536.f:1.f;
    float factor=special==0?65536.f:special==1?0.00390625f:1.f;
    for(unsigned j=0;j<n;++j){U p=0x7476a4+12*j;put(initial.data(),p,xy);put(initial.data(),p+4,-xy);put(initial.data(),p+8,z);}
    put(initial.data(),0x73fb80,factor);put(initial.data(),0x73fc30,factor);put(initial.data(),0x73fb98,factor);
    put(initial.data(),0x73fb88,special==2?-1.f:0.f);put(initial.data(),0x73fb8c,special==2?1.f:0.f);
   }
   if(!admitted(seed.data(),initial.data(),n))throw std::runtime_error("Positive case rejected");
   a=seed;b=seed;full=initial;last=initial;
   cw(control);__remill_fpu_exception_clear(127);mw34_projection_fixture(a.data(),n,full.data(),0);auto sa=status();
   cw(control);__remill_fpu_exception_clear(127);mw34_projection_fixture(b.data(),n,last.data(),1);auto sb=status();
   unsigned difference=4096;for(unsigned j=0;j<a.size();++j)if(a[j]!=b[j]){difference=j;break;}
   // Exactly the prefix x/y/z scratch writes are intentionally omitted.
   for(unsigned j=0;j+1<n;++j)for(unsigned k=0;k<12;++k)full[0x72f41c+32*j+k]=last[0x72f41c+32*j+k];
   if(difference!=4096||sa!=sb||full!=last){
    dump("failure-state-full.bin",a.data(),a.size());dump("failure-state-last.bin",b.data(),b.size());
    dump("failure-memory-full.bin",full.data(),full.size());dump("failure-memory-last.bin",last.data(),last.size());
    std::cerr<<"Mismatch count="<<n<<" mode="<<mode<<" pattern="<<pattern<<" state_offset="<<difference<<" status="<<sa<<","<<sb<<"\n";return 1;
   }++cases;
  }
  // Rejection boundaries are tested without executing rejected FP operands.
  for(U bad:{0x7f800000U,0xff800000U,0x7fc00001U,1U,0x3b7fffffU,0x47800001U}){
   put(initial.data(),0x7476a4,bad);if(admitted(seed.data(),initial.data(),1))throw std::runtime_error("Bad X admitted");
  }
  put(initial.data(),0x7476a4,1.f);
  for(U bad:{0U,0x80000000U,0xbf800000U,0x7fc00000U}){put(initial.data(),0x7476ac,bad);if(admitted(seed.data(),initial.data(),1))throw std::runtime_error("Bad Z admitted");}
  put(initial.data(),0x7476ac,1.f);seed[2745]=0;if(admitted(seed.data(),initial.data(),1))throw std::runtime_error("PE0 admitted");
  seed[2745]=1;
  if(admitted(seed.data(),initial.data(),0)||admitted(seed.data(),initial.data(),65))throw std::runtime_error("Bad count admitted");
  for(U address:{0x73fb80U,0x73fc30U,0x73fb88U,0x73fb98U,0x73fb8cU}){
   U saved=get<U>(initial.data(),address);
   for(U bad:{0x7fc00001U,1U,0x3b7fffffU,0x47800001U}){put(initial.data(),address,bad);if(admitted(seed.data(),initial.data(),1))throw std::runtime_error("Bad projection scalar admitted");}
   put(initial.data(),address,saved);
  }
  put(initial.data(),0x73fb80,0.f);if(admitted(seed.data(),initial.data(),1))throw std::runtime_error("Zero numerator admitted");
  cw(0x37f);__remill_fpu_exception_clear(127);
  std::cout<<"Original projection full/last fixture: "<<cases<<" complete-State, last-corner, memory footprint and hardware-status cases pass; negative gates pass\n";
 }catch(const std::exception& e){cw(0x37f);std::cerr<<e.what()<<"\n";return 1;}
}
