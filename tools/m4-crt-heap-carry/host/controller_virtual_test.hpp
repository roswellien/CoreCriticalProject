#pragma once
#include <windows.h>
#include <array>
#include <filesystem>
#include <fstream>
#include <vector>
#include <stdexcept>
#include <cstdio>

namespace mw34::controller {
// Opt-in, process-local authored input for native integration checks. Not a player backend.
class VirtualTest {
    struct Description {
        unsigned version{136}; unsigned short type{1},padding{},vendor{},product{},axes{6},buttons{26},balls{},hats{},touchpads{},sensors{},padding2[2]{};
        unsigned button_mask{(1U<<26)-1},axis_mask{63}; const char* name{"Core Critical native diagnostic pad"};
        void* touchpad_desc{};void* sensor_desc{};void* userdata{};void* callbacks[8]{};
    };
    static_assert(sizeof(Description)==136);
    struct Event {unsigned frame{},mode{},buttons{};std::array<short,6> axes{};};
    std::vector<Event> events;size_t at{}; void* joystick{};
    unsigned (*attach)(const Description*){};bool(*detach)(unsigned){};void*(*open)(unsigned){};void(*close)(void*){};
    bool(*set_axis)(void*,int,short){};bool(*set_button)(void*,int,bool){};
    template<class T>T fn(HMODULE lib,const char* name){auto p=reinterpret_cast<T>(::GetProcAddress(lib,name));if(!p)throw std::runtime_error("SDL virtual test API missing");return p;}
    void connect(){Description d;instance=attach(&d);if(!instance)throw std::runtime_error("Diagnostic controller attach failed");joystick=open(instance);if(!joystick)throw std::runtime_error("Diagnostic controller open failed");for(int i=4;i<6;++i)if(!set_axis(joystick,i,-32768))throw std::runtime_error("Diagnostic trigger initialization failed");}
    void disconnect(){if(joystick){close(joystick);joystick=nullptr;}if(instance){detach(instance);instance=0;}}
public:
    unsigned instance{};bool focused{true};
    VirtualTest(HMODULE lib,const std::wstring& script){
        if(std::filesystem::file_size(script)>128*1024)throw std::runtime_error("Controller diagnostic script too large");
        std::ifstream input{std::filesystem::path(script)};std::string magic;input>>magic;
        if(magic!="CC_CONTROLLER_TEST_V1")throw std::runtime_error("Unknown controller diagnostic script");
        unsigned frame,mode,buttons;int value;unsigned previous{};
        while(input>>frame){
            if(!(input>>mode>>buttons)||mode>2||buttons>=(1U<<26)||(!events.empty()&&frame<previous)||events.size()>=1024)throw std::runtime_error("Invalid diagnostic event");
            Event e{frame,mode,buttons};for(auto& axis:e.axes){if(!(input>>value)||value < -32768||value>32767)throw std::runtime_error("Invalid diagnostic axis");axis=short(value);}
            events.push_back(e);previous=frame;
        }
        if(!input.eof())throw std::runtime_error("Invalid diagnostic script tail");
        attach=fn<decltype(attach)>(lib,"SDL_AttachVirtualJoystick");detach=fn<decltype(detach)>(lib,"SDL_DetachVirtualJoystick");open=fn<decltype(open)>(lib,"SDL_OpenJoystick");close=fn<decltype(close)>(lib,"SDL_CloseJoystick");
        set_axis=fn<decltype(set_axis)>(lib,"SDL_SetJoystickVirtualAxis");set_button=fn<decltype(set_button)>(lib,"SDL_SetJoystickVirtualButton");
        connect();std::fprintf(stderr,"CONTROLLER DIAGNOSTIC: authored virtual input enabled, not physical hardware\n");
    }
    ~VirtualTest(){disconnect();}
    void tick(unsigned frame){
        while(at<events.size()&&events[at].frame<=frame){const auto& e=events[at++];focused=e.mode==1;
            if(e.mode==0){disconnect();continue;}if(!joystick)connect();
            for(int i=0;i<6;++i)if(!set_axis(joystick,i,e.axes[i]))throw std::runtime_error("Diagnostic axis write failed");
            for(int i=0;i<26;++i)if(!set_button(joystick,i,(e.buttons>>i)&1))throw std::runtime_error("Diagnostic button write failed");
        }
    }
};
} // namespace mw34::controller
