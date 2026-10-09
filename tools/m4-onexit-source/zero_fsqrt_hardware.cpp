// Finite direct x87 hardware witness; no game execution and no numerical AFTER seed.
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <array>
struct alignas(16) Fx { unsigned char bytes[512]; };
struct alignas(4) Env { unsigned char bytes[28]; };
struct Case { unsigned words[8]; Fx before,after; };
static unsigned short word(const void*p){unsigned short v;std::memcpy(&v,p,2);return v;}
int main(int argc,char**argv){if(argc!=2)return 2;FILE*out{};if(fopen_s(&out,argv[1],"wb"))return 3;
 const unsigned header[4]{0x5a535148,1,192,sizeof(Case)};fwrite(header,sizeof(header),1,out);
 for(unsigned control:{0x7fu,0x37fu,0xf7fu,0x47fu,0xa7fu,0xe7fu})for(unsigned top:{0u,7u})for(unsigned negative:{0u,1u})for(unsigned seed=0;seed<8;++seed){
  const unsigned flags=(seed&1)|((seed&2))|((seed&4)<<3);unsigned short cw=static_cast<unsigned short>(control);alignas(16) unsigned char raw[16]{};raw[9]=negative?0x80:0;Fx saved{},restored{};Env env{};Case r{};
  __asm__ volatile("fxsave64 %0\n\tfninit\n\tfldcw %1":"=m"(saved):"m"(cw):"memory");
  for(unsigned i=0;i<((top+1)&7);++i)__asm__ volatile("fincstp":::"memory");
  __asm__ volatile("fldt %1\n\tfnstenv %0\n\tfldenv %0":"=m"(env):"m"(raw):"memory","st");
  unsigned short sw=word(env.bytes+4);sw=static_cast<unsigned short>((sw&~0x23u)|flags);std::memcpy(env.bytes+4,&sw,2);
  __asm__ volatile("fldenv %2\n\tfxsave64 %0\n\tfsqrt\n\tfxsave64 %1":"=m"(r.before),"=m"(r.after):"m"(env):"memory","st");
  __asm__ volatile("fxrstor64 %1\n\tfxsave64 %0":"=m"(restored):"m"(saved):"memory");
  const auto before=word(r.before.bytes+2),after=word(r.after.bytes+2);const bool host=std::memcmp(saved.bytes,restored.bytes,512)==0;
  r.words[0]=control;r.words[1]=top;r.words[2]=negative;r.words[3]=flags;r.words[4]=before;r.words[5]=after;r.words[6]=host;r.words[7]=0;
  const bool ok=word(r.before.bytes)==control&&word(r.after.bytes)==control&&(before>>11&7)==top&&(after>>11&7)==top&&(before&0x23)==flags&&(after&0x23)==flags&&std::memcmp(r.before.bytes+32,raw,10)==0&&std::memcmp(r.after.bytes+32,raw,10)==0&&host;
  if(!ok){fclose(out);return 4;}fwrite(&r,sizeof(r),1,out);
 }
 fclose(out);return 0;
}
