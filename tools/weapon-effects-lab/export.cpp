#include "effects.hpp"
#include "flow.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>

using namespace mw34::effects_lab;
static void vec(std::ostream& o,Vec3 v){o<<v.x<<','<<v.y<<','<<v.z;}
int main(int argc,char** argv) try {
    if(argc!=2) throw std::runtime_error("Usage: effects_preview_export output.json");
    std::ofstream o(argv[1]);
    if(!o) throw std::runtime_error("Cannot open preview output");
    o<<std::setprecision(5)<<"{\"fps\":30,\"duration\":4,\"scenes\":[";
    const char* names[]={"PPC","Gauss","Fire","Explosion"};
    const auto folder=std::filesystem::path(argv[1]).parent_path();
    for(unsigned scene=0;scene<4;++scene){
        if(scene)o<<',';
        System system(1);
        Event e{1,{1,1},static_cast<Kind>(scene),.25,scene==0?1.15:(scene==1?.61:(scene==2?2.8:.25)),
                scene<2?Vec3{-5,1.5,0}:Vec3{0,.15,0},scene==0?Vec3{10,0,0}:(scene==1?Vec3{25,0,0}:Vec3{})};
        if(system.submit(e)!=Submit::accepted) throw std::runtime_error("Fixture event rejected");
        // Separate authored impact, NOT inferred collision or recovered PPC behavior.
        if(scene==0 && system.submit({1,{2,1},Kind::ppc_impact,1.15,1.15,{4,1.5,0},{}})!=Submit::accepted)
            throw std::runtime_error("Fixture impact rejected");
        if(scene==1 && system.submit({1,{2,1},Kind::gauss_impact,.61,.61,{4,1.5,0},{}})!=Submit::accepted)
            throw std::runtime_error("Fixture Gauss impact rejected");
        if(scene<2 && system.submit({1,{3,1},scene==0?Kind::ppc_muzzle:Kind::gauss_muzzle,.25,.25,{-5,1.5,0},{}})!=Submit::accepted)
            throw std::runtime_error("Fixture muzzle rejected");
        Flow flow;
        o<<"{\"name\":\""<<names[scene]<<"\",\"frames\":[";
        for(unsigned frame=0;frame<=120;++frame){
            if(frame)o<<',';
            if(scene>=2 && frame)for(unsigned step=0;step<2;++step)
                flow.step((static_cast<double>(frame)*2-1+step)/60.,scene==3);
            auto s=system.sample(static_cast<double>(frame)/30.);
            o<<"{\"p\":[";
            bool comma=false;
            for(const auto& p:s.particles){
                if(comma)o<<',';
                comma=true;
                o<<'[';vec(o,p.position);o<<',';vec(o,p.color);
                o<<','<<p.size<<','<<p.alpha<<','<<static_cast<unsigned>(p.layer)<<','<<p.rotation
                 <<','<<(scene<2&&p.key.source==2?1:0)<<','<<p.ordinal<<']';
            }
            o<<"],\"r\":[";comma=false;
            for(const auto& r:s.ribbons){
                if(comma)o<<',';
                comma=true;
                o<<"{\"c\":[";vec(o,r.color);o<<"],\"w\":"<<r.width<<",\"a\":"<<r.alpha
                 <<",\"impact\":"<<(scene<2&&r.key.source==2?1:0)<<",\"v\":[";
                bool separator=false;
                for(const auto& p:r.points){if(separator)o<<',';separator=true;o<<'[';vec(o,p);o<<']';}
                o<<"]}";
            }
            o<<"],\"l\":[";comma=false;
            for(const auto& l:s.lights){
                if(comma)o<<',';
                comma=true;
                o<<'[';vec(o,l.position);o<<',';vec(o,l.color);o<<','<<l.radius<<','<<l.intensity
                 <<','<<(scene<2&&l.key.source==2?1:0)<<']';
            }
            o<<']';
            if(scene>=2){
                o<<",\"field\":{\"width\":"<<Flow::width<<",\"height\":"<<Flow::height
                 <<",\"worldWidth\":"<<(scene==3?8:4.8)<<",\"worldHeight\":"<<(scene==3?8:7.2);
                for(unsigned layer=0;layer<2;++layer){
                    const auto filename="flow-"+std::to_string(scene)+"-"+std::to_string(frame)+"-"+std::to_string(layer)+".rgba";
                    const auto pixels=flow.pixels(layer==0);
                    std::ofstream image(folder/filename,std::ios::binary);
                    image.write(reinterpret_cast<const char*>(pixels.data()),static_cast<std::streamsize>(pixels.size()));
                    image.close();if(!image)throw std::runtime_error("Flow image write failed");
                    o<<(layer==0?",\"fire\":\"":",\"smoke\":\"")<<filename<<'"';
                }
                o<<'}';
            }
            o<<'}';
        }
        o<<"]}";
    }
    o<<"]}";
    o.close();
    if(!o) throw std::runtime_error("Preview output write failed");
    std::cout<<"Exported four authored scenarios at 30 samples/second. Not native-game evidence.\n";
    return 0;
} catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
