#pragma once
#include <filesystem>
#include <fstream>
#include <vector>
#include <stdexcept>
#include <iostream>
namespace mw34::m4_fp_sincos_publication {
inline std::vector<unsigned char> read(const std::filesystem::path &p){
    std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>{f},std::istreambuf_iterator<char>{}};
}
template<class Publisher> void controls(const char *directory){
    const std::filesystem::path root(directory);
    if(std::filesystem::exists(root)||!std::filesystem::create_directory(root))throw std::runtime_error("Fresh publication control directory required");
    const std::vector<unsigned char> sentinel{0x4d,0x57,0x33,0x34,0,0xff,0x80,0x42};
    auto write=[&](const auto &path){std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char *>(sentinel.data()),sentinel.size());if(!f)throw std::runtime_error("Fixture write failed");};
    for(unsigned stage=0;stage<2;++stage){
        auto destination=root/(stage?"pre-existing-stage.bin":"pre-existing-output.bin");
        auto staging=std::filesystem::path(destination.string()+".fp-stage-"+std::to_string(GetCurrentProcessId()));
        write(stage?staging:destination);bool rejected{};
        try{Publisher output(destination.string().c_str());}catch(const std::exception &){rejected=true;}
        if(!rejected||read(stage?staging:destination)!=sentinel||std::filesystem::exists(stage?destination:staging))throw std::runtime_error("Pre-existing publication evidence lost");
    }
    std::cout<<"2 actual publisher admission controls passed\n";
}
}
