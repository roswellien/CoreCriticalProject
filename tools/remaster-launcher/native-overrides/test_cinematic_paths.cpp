#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
struct Reader {
#include "cinematic_paths.inc"
};
int main(int argc,char**argv){try{
 if(argc!=3)return 3;
 auto result=Reader{}.cinematic_path(argv[1]);
 if(result!=argv[2]){std::fprintf(stderr,"Unexpected cinematic route: %s\n",result.c_str());return 2;}
 return 0;
}catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
