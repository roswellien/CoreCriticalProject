#pragma once
#include "controller_math.hpp"
#include "controller_virtual_test.hpp"
#include <bcrypt.h>
#include <filesystem>
#include <fstream>
#include <vector>
#include <memory>

namespace mw34::controller {
inline std::wstring utf16(const std::string& value) {
    int size=::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),int(value.size()),nullptr,0);
    if(!size) throw std::runtime_error("Invalid controller path encoding");
    std::wstring result(size,0); ::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),int(value.size()),result.data(),size); return result;
}
inline std::string hex(const unsigned char* data,size_t size) {
    static constexpr char digits[]="0123456789ABCDEF"; std::string out; out.reserve(size*2);
    for(size_t i=0;i<size;++i){out+=digits[data[i]>>4];out+=digits[data[i]&15];} return out;
}
inline std::string identity_hash(const std::string& value) {
    std::array<unsigned char,32> result{};
    if(::BCryptHash(BCRYPT_SHA256_ALG_HANDLE,nullptr,0,reinterpret_cast<PUCHAR>(const_cast<char*>(value.data())),ULONG(value.size()),result.data(),ULONG(result.size()))<0)
        throw std::runtime_error("Controller identity hash failed");
    return hex(result.data(),result.size());
}
class Input {
    HMODULE library{};
    bool initialized{};
    void* pad{};
    unsigned instance{};
    ULONGLONG scan_after{};
    template<class T>T function(const char* name) {
        auto result=reinterpret_cast<T>(::GetProcAddress(library,name));
        if(!result) throw std::runtime_error(std::string("Controller backend lacks ")+name); return result;
    }
    struct Guid { unsigned char data[16]; };
    bool (*init)(unsigned){}; void (*quit)(unsigned){}; const char* (*error)(){};
    void (*update)(){}; unsigned* (*enumerate)(int*){}; void (*free_memory)(void*){};
    void* (*open)(unsigned){}; void (*close)(void*){}; bool (*attached)(void*){};
    short (*axis)(void*,int){}; bool (*button)(void*,int){};
    const char* (*serial)(void*){}; const char* (*path)(void*){}; Guid (*guid)(unsigned){};
    static std::string string(const char* p){return p?p:"";}
public:
    Config config; State state;
    std::unique_ptr<VirtualTest> diagnostic;
    Input(const std::wstring& config_path,const std::wstring& library_path) {
        const auto cp=std::filesystem::path(config_path),lp=std::filesystem::path(library_path);
        if(!cp.is_absolute()||!lp.is_absolute()) throw std::runtime_error("Controller paths must be absolute");
        if(std::filesystem::file_size(cp)>8192) throw std::runtime_error("Controller config exceeds size limit");
        std::ifstream file(cp); config=Config::read(file);
        library=::LoadLibraryExW(lp.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
        if(!library) throw std::runtime_error("SDL3 controller runtime could not load");
        try {
            if(function<int(*)()>("SDL_GetVersion")()!=3004018) throw std::runtime_error("Wrong SDL3 controller version");
            init=function<decltype(init)>("SDL_InitSubSystem"); quit=function<decltype(quit)>("SDL_QuitSubSystem"); error=function<decltype(error)>("SDL_GetError");
            update=function<decltype(update)>("SDL_UpdateGamepads"); enumerate=function<decltype(enumerate)>("SDL_GetGamepads"); free_memory=function<decltype(free_memory)>("SDL_free");
            open=function<decltype(open)>("SDL_OpenGamepad"); close=function<decltype(close)>("SDL_CloseGamepad"); attached=function<decltype(attached)>("SDL_GamepadConnected");
            axis=function<decltype(axis)>("SDL_GetGamepadAxis"); button=function<decltype(button)>("SDL_GetGamepadButton");
            serial=function<decltype(serial)>("SDL_GetGamepadSerial"); path=function<decltype(path)>("SDL_GetGamepadPath"); guid=function<decltype(guid)>("SDL_GetGamepadGUIDForID");
            if(!init(0x2000)) throw std::runtime_error("SDL3 initialization failed: "+string(error())); initialized=true;
            function<void(*)(bool)>("SDL_SetGamepadEventsEnabled")(false); function<void(*)(bool)>("SDL_SetJoystickEventsEnabled")(false);
            if(const wchar_t* script=::_wgetenv(L"MW34_CONTROLLER_TEST_SCRIPT");script&&*script)diagnostic=std::make_unique<VirtualTest>(library,script);
        } catch(...) { if(initialized)quit(0x2000); ::FreeLibrary(library);library=nullptr;throw; }
    }
    Input(const Input&)=delete; Input& operator=(const Input&)=delete;
    ~Input(){if(pad)close(pad);diagnostic.reset();if(initialized)quit(0x2000);if(library)::FreeLibrary(library);}
    void poll(bool focused,unsigned frame=0) {
        if(diagnostic){diagnostic->tick(frame);focused=diagnostic->focused;}
        update();
        if(pad&&!attached(pad)){close(pad);pad=nullptr;instance=0;scan_after=0;}
        if(!pad&&::GetTickCount64()>=scan_after) {
            scan_after=::GetTickCount64()+1000;
            int count{}; unsigned* ids=enumerate(&count);
            if(!ids) throw std::runtime_error("SDL3 controller enumeration failed: "+string(error()));
            try {
                if(count<0||count>128)throw std::runtime_error("Invalid controller count");
                for(int i=0;i<count;++i) {
                    void* candidate=open(ids[i]);
                    if(!candidate)throw std::runtime_error("Cannot open controller: "+string(error()));
                    try {
                        auto g=guid(ids[i]); const auto s=string(serial(candidate)),p=string(path(candidate));
                        const auto key=identity_hash(hex(g.data,16)+":"+(s.empty()?p:s));
                        if(diagnostic?ids[i]==diagnostic->instance:((!s.empty()||!p.empty())&&key==config.device)) {
                            if(pad)throw std::runtime_error("Controller identity is ambiguous; disconnect the duplicate device");
                            pad=candidate;instance=ids[i];candidate=nullptr;
                        }
                    } catch(...) {if(candidate)close(candidate);throw;}
                    if(candidate)close(candidate);
                }
            } catch(...) {free_memory(ids);throw;}
            free_memory(ids);
        }
        Sample sample;sample.connected=pad&&attached(pad);sample.focused=focused;
        if(sample.connected){for(int i=0;i<6;++i)sample.axes[i]=axis(pad,i);for(int i=0;i<26;++i)sample.buttons[i]=button(pad,i);}
        state.update(config,sample);
    }
};
} // namespace mw34::controller
