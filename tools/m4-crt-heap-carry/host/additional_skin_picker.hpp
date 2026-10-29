#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::skins {
// Generic native UI: labels and selection are supplied by the content registry.
// It owns no chassis IDs, skin names, texture paths or preference files.
class Picker {
    HWND window_{}, list_{};
    std::optional<std::size_t> chosen_;
    static LRESULT CALLBACK proc(HWND window,UINT message,WPARAM wp,LPARAM lp) noexcept {
        auto* self=reinterpret_cast<Picker*>(GetWindowLongPtrW(window,GWLP_USERDATA));
        if(message==WM_NCCREATE){self=static_cast<Picker*>(reinterpret_cast<CREATESTRUCTW*>(lp)->lpCreateParams);
            SetWindowLongPtrW(window,GWLP_USERDATA,reinterpret_cast<LONG_PTR>(self));}
        if(!self)return DefWindowProcW(window,message,wp,lp);
        if(message==DM_GETDEFID)return MAKELONG(103,DC_HASDEFID);
        if(message==WM_COMMAND){
            if(LOWORD(wp)==104){DestroyWindow(window);return 0;}
            if((LOWORD(wp)==103&&HIWORD(wp)==BN_CLICKED)||(LOWORD(wp)==102&&HIWORD(wp)==LBN_DBLCLK)){
                const auto index=SendMessageW(self->list_,LB_GETCURSEL,0,0);
                if(index>=0)self->chosen_=std::size_t(index);
                DestroyWindow(window);return 0;
            }
        }
        if(message==WM_CLOSE){DestroyWindow(window);return 0;}
        if(message==WM_DESTROY){self->window_=nullptr;self->list_=nullptr;return 0;}
        return DefWindowProcW(window,message,wp,lp);
    }
public:
    std::optional<std::size_t> show(HWND owner,const std::vector<std::wstring>& labels,std::size_t initial) {
        if(labels.empty()||initial>=labels.size()||!owner||!IsWindow(owner))
            throw std::runtime_error("Invalid Mech Skins choices or owner");
        const HINSTANCE instance=GetModuleHandleW(nullptr);
        WNDCLASSW cls{};cls.lpfnWndProc=&proc;cls.hInstance=instance;
        cls.hCursor=LoadCursorW(nullptr,MAKEINTRESOURCEW(32512));cls.hbrBackground=reinterpret_cast<HBRUSH>(COLOR_BTNFACE+1);
        cls.lpszClassName=L"CoreCritical.MechSkins.v1";
        if(!RegisterClassW(&cls)&&GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)throw std::runtime_error("Cannot register Mech Skins window");
        RECT area{};GetWindowRect(owner,&area);MONITORINFO monitor{sizeof(MONITORINFO)};
        if(GetMonitorInfoW(MonitorFromWindow(owner,MONITOR_DEFAULTTONEAREST),&monitor))area=monitor.rcWork;
        window_=CreateWindowExW(WS_EX_DLGMODALFRAME|WS_EX_CONTROLPARENT,cls.lpszClassName,L"Mech Skins — Core Critical",
            WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU,area.left+(area.right-area.left-540)/2,area.top+(area.bottom-area.top-450)/2,
            540,450,owner,nullptr,instance,this);
        if(!window_)throw std::runtime_error("Cannot open Mech Skins window");
        const bool enabled=IsWindowEnabled(owner)!=FALSE;
        auto cleanup=[&]{if(window_)DestroyWindow(window_);if(enabled)EnableWindow(owner,TRUE);SetForegroundWindow(owner);};
        try {
            auto control=[&](const wchar_t* type,const wchar_t* title,DWORD style,int x,int y,int w,int h,unsigned id){
                HWND child=CreateWindowExW(0,type,title,WS_CHILD|WS_VISIBLE|style,x,y,w,h,window_,
                    reinterpret_cast<HMENU>(UINT_PTR(id)),instance,nullptr);
                if(!child)throw std::runtime_error("Cannot create Mech Skins control");
                SendMessageW(child,WM_SETFONT,reinterpret_cast<WPARAM>(GetStockObject(DEFAULT_GUI_FONT)),TRUE);return child;
            };
            control(L"STATIC",L"Choose a skin for your mech. Existing skins remain available.",0,16,12,500,24,100);
            list_=control(L"LISTBOX",L"Available mech skins",WS_BORDER|WS_TABSTOP|WS_VSCROLL|LBS_NOTIFY|LBS_NOINTEGRALHEIGHT,16,42,500,300,102);
            control(L"BUTTON",L"Apply",WS_TABSTOP|BS_DEFPUSHBUTTON,306,365,100,30,103);
            control(L"BUTTON",L"Cancel",WS_TABSTOP|BS_PUSHBUTTON,416,365,100,30,104);
            for(const auto& label:labels)if(SendMessageW(list_,LB_ADDSTRING,0,reinterpret_cast<LPARAM>(label.c_str()))<0)
                throw std::runtime_error("Cannot populate Mech Skins");
            SendMessageW(list_,LB_SETCURSEL,initial,0);
            EnableWindow(owner,FALSE);ShowWindow(window_,SW_SHOW);SetForegroundWindow(window_);SetFocus(list_);
#ifdef MW34_SKIN_PICKER_CREATED
            MW34_SKIN_PICKER_CREATED(window_);
#endif
            MSG message{};
            while(window_){const BOOL status=GetMessageW(&message,nullptr,0,0);
                if(status<=0){if(status==0)PostQuitMessage(int(message.wParam));break;}
                if(!IsDialogMessageW(window_,&message)){TranslateMessage(&message);DispatchMessageW(&message);}}
        }catch(...){cleanup();throw;}
        cleanup();
        if(chosen_&&*chosen_>=labels.size())throw std::runtime_error("Invalid Mech Skins selection");
        return chosen_;
    }
};
} // namespace mw34::skins
