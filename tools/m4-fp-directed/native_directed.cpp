// The reviewed first observer remains unchanged; this separate harness adds
// only explicitly authored constant inputs. Its old main is never invoked.
#define main mw34_prior_native_observation_main
#include "../m4-fp-native/native_first.cpp"
#undef main
#include "corpus.hpp"
int main(int argc,char **argv){using namespace mw34::m4_fp_native;try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    require(argc==4,"Directed native: exact-pack exact-image fresh-output");
    const auto pack=admit(argv[1],argv[2]);Output out(argv[3]);const std::uint32_t header[]{1,mw34::m4_fp_directed::records,sizeof(Result),3504,9,4096};
    out.write("MW4FPN01",8);out.write(header,sizeof(header));
    for(unsigned repeat=0;repeat<2;++repeat)for(unsigned input=0;input<mw34::m4_fp_directed::inputs.size();++input)
      for(auto cw:mw34::m4_fp_directed::controls)for(unsigned top:{0U,7U}){
        Harness h(pack);h.memory.protect({0x5e1000},mw34::Permissions::read|mw34::Permissions::write);
        h.memory.store<std::uint32_t>({0x5e1f58},mw34::m4_fp_directed::inputs[input]);h.memory.protect({0x5e1000},mw34::Permissions::read);
        Context c(h.memory);State s;initialize(s,cw,top,input*7919+repeat*3571+cw);Result r{};
        r.repeat=(repeat<<16)|input;r.pc=entry;r.cw=cw;r.top=top;execute(h,s,c,r);
        require(!r.status&&r.host_restored,"Directed native route/host isolation failed");out.write(&r,sizeof(r));
    }
    out.commit();std::cout<<mw34::m4_fp_directed::records<<" actual compiled directed first FP records; no equivalence shortcut\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
