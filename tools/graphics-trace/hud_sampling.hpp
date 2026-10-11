#pragma once
#include <map>
// Retain transitions per source; this is sampled evidence, not frame coverage.
class HudTransitions {
    struct Entry {std::string signature;unsigned retained=0;};
    std::map<std::string,Entry> previous;
    unsigned limit;
public:
    explicit HudTransitions(unsigned perSource=16):limit(perSource) {}
    static std::string pattern(const std::string &text) {
        std::string result;bool digits=false;
        for(unsigned char character:text) {
            if(character>='0' && character<='9') {
                if(!digits)result+='#';digits=true;
            } else {result+=static_cast<char>(character);digits=false;}
        }
        return result;
    }
    bool changed(const std::string &key,const std::string &signature) {
        const auto found=previous.find(key);
        if(found!=previous.end()) {
            if(found->second.signature==signature || found->second.retained>=limit)return false;
            found->second.signature=signature;++found->second.retained;
        } else {
            if(previous.size()>=128 || !limit)return false;
            previous.emplace(key,Entry{signature,1});
        }
        return true;
    }
};
