#pragma once
#include <windows.h>
#include <algorithm>
#include <cstdlib>
#include <string>
#include <string_view>
#include <cstdint>
#include <vector>

namespace mw34::menu_version {
inline const std::string &launcher_version() {
    static const std::string version = [] {
        const char *value = std::getenv("MW34_CORE_CRITICAL_VERSION");
        if (!value || !*value) return std::string{};
        const std::string text(value);
        if (text.size() > 32 || !std::all_of(text.begin(), text.end(),
            [](unsigned char c) { return (c >= '0' && c <= '9') || c == '.'; })) return std::string{};
        return text;
    }();
    return version;
}
inline std::string caption(std::string_view original) {
    const auto &version = launcher_version();
    if (version.empty() || (!original.starts_with("MechWarrior 3") && !original.starts_with("MechWarrior3")))
        return std::string(original);
    return "Core Critical " + version + " - " + std::string(original);
}
inline std::wstring caption(std::wstring_view original) {
    const auto &version = launcher_version();
    if (version.empty() || (!original.starts_with(L"MechWarrior 3") && !original.starts_with(L"MechWarrior3")))
        return std::wstring(original);
    return L"Core Critical " + std::wstring(version.begin(), version.end()) + L" - " + std::wstring(original);
}

// Match only the solid white strokes of the original main-menu version row.
// Its background scrolls, so background colours are deliberately excluded.
// This is a digest, not a stored copy of original artwork or glyph pixels.
inline bool footer_present(const std::uint8_t *pixels,unsigned w,unsigned h,unsigned pitch) {
    if(w!=640||h!=480||pitch<w*2)return false;
    std::uint64_t hash=0xcbf29ce484222325ULL;unsigned strokes=0;
    for(unsigned y=464;y<474;++y)for(unsigned x=520;x<640;++x){
        const auto*p=pixels+size_t(y)*pitch+x*2;const unsigned bit=p[0]==255&&p[1]==255;
        strokes+=bit;hash=(hash^bit)*0x100000001b3ULL;
    }
    return strokes==43&&hash==0x3584650397303d5eULL;
}
struct FooterLabel {
    unsigned width{},height{};std::vector<std::uint8_t>coverage;
    FooterLabel(){
        const auto text="Core Critical "+launcher_version();
        HDC dc=::CreateCompatibleDC(nullptr);HFONT font=::CreateFontA(-10,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,
            ANSI_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,"Tahoma");
        if(!dc||!font){if(font)::DeleteObject(font);if(dc)::DeleteDC(dc);return;}
        const auto old_font=::SelectObject(dc,font);SIZE size{};
        if(::GetTextExtentPoint32A(dc,text.data(),int(text.size()),&size)&&size.cx>0&&size.cx<480&&size.cy>0&&size.cy<20){
            width=unsigned(size.cx);height=unsigned(size.cy);BITMAPINFO info{};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
            info.bmiHeader.biWidth=LONG(width);info.bmiHeader.biHeight=-LONG(height);info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;
            void*bits{};HBITMAP bitmap=::CreateDIBSection(dc,&info,DIB_RGB_COLORS,&bits,nullptr,0);
            if(bitmap&&bits){const auto old_bitmap=::SelectObject(dc,bitmap);
                std::fill_n(static_cast<std::uint32_t*>(bits),size_t(width)*height,0U);::SetBkMode(dc,TRANSPARENT);::SetTextColor(dc,RGB(255,255,255));
                ::TextOutA(dc,0,0,text.data(),int(text.size()));::GdiFlush();coverage.resize(size_t(width)*height);
                const auto*p=static_cast<const std::uint8_t*>(bits);for(size_t i=0;i<coverage.size();++i)coverage[i]=std::max({p[4*i],p[4*i+1],p[4*i+2]});
                ::SelectObject(dc,old_bitmap);::DeleteObject(bitmap);
            }
        }
        ::SelectObject(dc,old_font);::DeleteObject(font);::DeleteDC(dc);
    }
};
// Host presentation copy only: never write the badge into a guest surface.
inline void paint_footer(std::uint8_t*pixels,unsigned w,unsigned h,unsigned pitch){
    if(launcher_version().empty()||!footer_present(pixels,w,h,pitch))return;
    const DWORD last_error=::GetLastError();static const FooterLabel label;::SetLastError(last_error);if(label.coverage.empty())return;
    const unsigned left=517-label.width,top=464;
    auto blend=[&](unsigned x,unsigned y,unsigned a,unsigned r,unsigned g,unsigned b){
        if(!a||x>=w||y>=h)return;auto*p=pixels+size_t(y)*pitch+x*2;const unsigned old=unsigned(p[0])|unsigned(p[1])<<8;
        auto mix=[&](unsigned c,unsigned v){return(c*a+v*(255-a)+127)/255;};
        const unsigned result=(mix(r,(old>>11)*255/31)>>3)<<11|(mix(g,((old>>5)&63)*255/63)>>2)<<5|(mix(b,(old&31)*255/31)>>3);
        p[0]=std::uint8_t(result);p[1]=std::uint8_t(result>>8);
    };
    for(unsigned y=0;y<label.height;++y)for(unsigned x=0;x<label.width;++x)blend(left+x+1,top+y+1,unsigned(label.coverage[size_t(y)*label.width+x])*160/255,0,0,0);
    for(unsigned y=0;y<label.height;++y)for(unsigned x=0;x<label.width;++x)blend(left+x,top+y,label.coverage[size_t(y)*label.width+x],239,163,72);
}
} // namespace mw34::menu_version
