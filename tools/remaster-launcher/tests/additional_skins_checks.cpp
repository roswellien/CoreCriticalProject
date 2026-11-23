#include "../../m4-crt-heap-carry/host/additional_skins.hpp"
#include <sstream>
#include <iostream>

int main(){
    unsigned checks=0;
    auto require=[&](bool value){if(!value)throw std::runtime_error("skin check failed");++checks;};
    auto number=[](unsigned n){std::string s;for(unsigned i=0;i<4;++i)s+=char(n>>(8*i));return s;};
    auto text=[&](std::string s){return number(unsigned(s.size()))+s;};
    const auto record=text("test.skin:sommerset")+text("Sommerset")+text("bushwacker")+text("close.bin")+text("far.bin");
    const auto blob=std::string("BWSKIN1\0",8)+number(1)+record;
    std::istringstream file(blob);const auto skins=mw34::skins::read_additions(file);
    require(skins.size()==1&&skins[0].name=="Sommerset");
    const std::string chassis="community.additional-mech-pack:additional-chassis";
    const auto added=std::string("BWSKIN1\0",8)+number(1)+text("community.paint:paint")+
        text("New Paint")+text(chassis)+text("close.bin")+text("far.bin");
    std::istringstream added_file(added);
    require(mw34::skins::read_additions(added_file).at(0).chassis==chassis);
    auto rejected=[&](std::string data){try{std::istringstream in(data);mw34::skins::read_additions(in);}catch(const std::runtime_error&){++checks;return;}throw std::runtime_error("bad skin accepted");};
    rejected(blob.substr(0,blob.size()-1));rejected(blob+"x");rejected(std::string("BWSKIN1\0",8)+number(129));
    rejected(std::string("BWSKIN1\0",8)+number(2)+record+record);
    const char* base="base.bin";const char* alternate="alternate.bin";
    require(mw34::skins::replacement_texture_path(nullptr,base,0,nullptr)==base);
    for(unsigned skin=1;skin<8;++skin){
        require(mw34::skins::replacement_texture_path(nullptr,base,skin,nullptr)==nullptr);
        require(mw34::skins::replacement_texture_path(nullptr,base,skin,alternate)==alternate);
        require(mw34::skins::replacement_texture_path(alternate,base,skin,nullptr)==alternate);
    }
    for(unsigned original=0;original<8;++original){
        require(mw34::skins::appearance(original,8,false,false)==original); // Enemy A–H retained.
        require(mw34::skins::appearance(original,0,true,false)==original); // Original option restores identity.
        require(mw34::skins::appearance(original,8,true,false)==8);
        require(mw34::skins::appearance(original,8,false,true)==8);
        require(mw34::skins::selection(original,std::nullopt,true,false)==original);
        require(mw34::skins::selection(original,0,false,false)==original);
        require(mw34::skins::selection(original,0,true,false)==0);
    }
    std::cout<<checks<<" additional skin checks passed\n";
}
