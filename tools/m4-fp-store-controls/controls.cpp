// Compile the unchanged harness against the actual repaired object so its
// denied memory/return cases exercise the new store status bridge as well.
#define main mw34_prior_first_positive_main
#include "../m4-fp-native/native_first.cpp"
#undef main
int main(int argc,char **argv){using namespace mw34::m4_fp_native;try{
    require(argc==3,"Repaired context controls: exact-pack exact-image");
    const auto pack=admit(argv[1],argv[2]);controls(pack);return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
