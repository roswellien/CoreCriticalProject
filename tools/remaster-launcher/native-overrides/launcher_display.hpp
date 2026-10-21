#pragma once
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <windows.h>

namespace mw34::display {
struct Samples { unsigned x{1}, y{1}; };
inline Samples samples(const char* value) {
    if (!value || !std::strcmp(value,"off") || !std::strcmp(value,"1") || !std::strcmp(value,"fxaa")) return {};
    if (!std::strcmp(value,"2")) return {2,1};
    if (!std::strcmp(value,"4")) return {2,2};
    throw std::runtime_error("Unknown Remaster AA setting");
}
// Own the fullscreen Windows mode without persisting a desktop configuration change.
class ExclusiveMode {
    std::wstring device;
    DEVMODEW original{}, requested{};
    bool owned{}, changing{};
    HWND window{};
public:
    ~ExclusiveMode() { release(); }
    void release() noexcept {
        if (!owned || changing) return;
        changing=true;
        const LONG result=::ChangeDisplaySettingsExW(device.c_str(),&original,nullptr,0,nullptr);
        if(result==DISP_CHANGE_SUCCESSFUL)owned=false;
        changing=false;
    }
    void acquire(HWND hwnd, unsigned width, unsigned height) {
        if(changing)return;
        if(owned&&window==hwnd&&requested.dmPelsWidth==width&&requested.dmPelsHeight==height)return;
        release();
        MONITORINFOEXW monitor{};monitor.cbSize=sizeof(monitor);
        if(!::GetMonitorInfoW(::MonitorFromWindow(hwnd,MONITOR_DEFAULTTONEAREST),&monitor))throw std::runtime_error("Cannot locate fullscreen monitor");
        device=monitor.szDevice;original={};original.dmSize=sizeof(original);
        if(!::EnumDisplaySettingsExW(device.c_str(),ENUM_CURRENT_SETTINGS,&original,0))throw std::runtime_error("Cannot read desktop display mode");
        requested=original;requested.dmPelsWidth=width;requested.dmPelsHeight=height;
        requested.dmFields=DM_PELSWIDTH|DM_PELSHEIGHT|DM_BITSPERPEL;
        changing=true;
        LONG result=::ChangeDisplaySettingsExW(device.c_str(),&requested,nullptr,CDS_TEST,nullptr);
        if(result==DISP_CHANGE_SUCCESSFUL)result=::ChangeDisplaySettingsExW(device.c_str(),&requested,nullptr,CDS_FULLSCREEN,nullptr);
        changing=false;
        if(result!=DISP_CHANGE_SUCCESSFUL)throw std::runtime_error("Exclusive fullscreen mode is not supported by this monitor (Windows result "+std::to_string(result)+")");
        window=hwnd;owned=true;
    }
};
inline ExclusiveMode& exclusive() { static ExclusiveMode mode;return mode; }
}
