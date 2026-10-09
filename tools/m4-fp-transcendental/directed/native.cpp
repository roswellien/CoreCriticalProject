// Earlier fixed-input main remains linked but is never invoked by this worker.
#define main mw34_prior_fixed_cosine_main
#include "../native_cosine.cpp"
#undef main
#include "corpus.hpp"
int main(int argc,char **argv){using namespace mw34::m4_fp_cosine_native;try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    require(argc==4,"Cosine directed native: exact-pack exact-image fresh-output");
    const auto pack=admit(argv[1],argv[2]);Output out(argv[3]);
    const std::uint32_t header[]{1,mw34::m4_fp_cosine_directed::records,sizeof(Result),3504,9,4096};
    out.write("MW4COS01",8);out.write(header,sizeof(header));
    for(unsigned repeat=0;repeat<2;++repeat)for(auto root:mw34::m4_fp_cosine::roots)
      for(unsigned input=0;input<mw34::m4_fp_cosine_directed::inputs.size();++input)
      for(auto cw:mw34::m4_fp_cosine::controls)for(unsigned top:{0U,7U}){
        Harness h(pack);
        h.memory.protect({0x5cc000},mw34::Permissions::read|mw34::Permissions::write);
        h.memory.store<std::uint64_t>({root.input},mw34::m4_fp_cosine_directed::inputs[input]);
        h.memory.protect({0x5cc000},mw34::Permissions::read);
        Context c(h.memory,root);State s;initialize(s,cw,top,repeat*3571+cw+input*1709,root.entry);Result r{};
        r.repeat=(repeat<<16)|input;r.pc=root.entry;r.cw=cw;r.top=top;
        execute(h,s,c,r);require(!r.status&&r.host_restored,"Directed cosine route/host isolation failed");out.write(&r,sizeof(r));
    }
    out.commit();std::cout<<mw34::m4_fp_cosine_directed::records<<" actual compiled directed cosine records\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
