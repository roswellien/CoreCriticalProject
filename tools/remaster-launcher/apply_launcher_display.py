"""Connect launcher resolution, SSAA and window modes in a private host snapshot."""
from pathlib import Path
import argparse
import shutil


def replace(path, old, new):
    text=path.read_text(encoding='utf-8')
    if text.count(old)!=1:raise RuntimeError(f'{path.name}: expected one source contract: {old[:90]}')
    path.write_text(text.replace(old,new),encoding='utf-8')


def apply(host):
    shutil.copyfile(Path(__file__).parent/'native-overrides/launcher_display.hpp',host/'launcher_display.hpp')
    shutil.copyfile(Path(__file__).resolve().parents[2]/'runtime/graphics/material_normals.hpp',host/'material_normals.hpp')
    shutil.copyfile(Path(__file__).resolve().parents[2]/'runtime/graphics/normal_codec.hpp',host/'normal_codec.hpp')
    replace(host/'surface_normals_stage.inc','if(authored_bytes>256ULL*1024*1024)','if(authored_bytes>mw34::materials::authored_normal_budget)')
    vk=host/'vk_scene.hpp'
    replace(vk,'#include "frontend_canvas.hpp"','#include "frontend_canvas.hpp"\n#include "launcher_display.hpp"')
    replace(vk,'if((w||h)&&((w!=1920&&w!=3440)||h!=1440))throw std::runtime_error("This GPU Remaster candidate supports 1920x1440 or 3440x1440");',
        'if((w||h)&&(w<640||h<480||w>7680||h>4320))throw std::runtime_error("Remaster output resolution outside 640x480..7680x4320");')
    replace(vk,'static unsigned remaster_height(){return remaster_width()?1440:0;}','static unsigned remaster_height(){return remaster_width()?remaster_setting("MW34_REMASTER_HEIGHT",0):0;}')
    replace(vk,'static bool widescreen(){return remaster_width()==3440;}','static bool widescreen(){return remaster_width()&&std::uint64_t(remaster_width())*3>std::uint64_t(remaster_height())*4;}')
    replace(vk,'if(std::strcmp(p,"fxaa"))throw std::runtime_error("MW34_REMASTER_AA supports 1/off or fxaa; SSAA sample counts are not supported");',
        'if(std::strcmp(p,"fxaa")){(void)mw34::display::samples(p);return false;}')
    replace(vk,'if(widescreen()){if(target_frontend){const auto fit=mw34::frontend::CanvasFit::fit(w,h,remaster_width(),remaster_height());rw=unsigned(fit.width);rh=unsigned(fit.height);}else{rw=3440;rh=1440;}}',
        '''if(remaster_width()){if(target_frontend){const auto fit=mw34::frontend::CanvasFit::fit(w,h,remaster_width(),remaster_height());rw=unsigned(fit.width);rh=unsigned(fit.height);}else{rw=remaster_width();rh=remaster_height();}}
        const auto samples=mw34::display::samples(std::getenv("MW34_REMASTER_AA"));
        rw*=samples.x;rh*=samples.y;
        VkPhysicalDeviceProperties limits{};f.vkGetPhysicalDeviceProperties(gpu,&limits);
        if(rw>limits.limits.maxImageDimension2D||rh>limits.limits.maxImageDimension2D||rw>limits.limits.maxFramebufferWidth||rh>limits.limits.maxFramebufferHeight)throw std::runtime_error("Requested resolution and SSAA exceed GPU target limits");
        std::fprintf(stderr,"Display target: output %ux%u, raster %ux%u, SSAA %ux%u, frontend %u\\n",remaster_width(),remaster_height(),rw,rh,samples.x,samples.y,unsigned(target_frontend));''')
    replace(vk,'if (scale == 1.f&&scale_x==1.f) return r;','if (rw==width&&rh==height) return r;')
    text=vk.read_text(encoding='utf-8').replace('r.offset.y * double(scale)','r.offset.y * (double(rh)/height)').replace('(r.offset.y + int(r.extent.height)) * double(scale)','(r.offset.y + int(r.extent.height)) * (double(rh)/height)')
    vk.write_text(text,encoding='utf-8')
    replace(vk,'const double sx = double(swapExtent.width) / rw, sy = double(swapExtent.height) / rh, fit = std::min(sx, sy);\n        const int dw = int(std::lround(rw * fit)), dh = int(std::lround(rh * fit)), dx = (int(swapExtent.width) - dw) / 2, dy = (int(swapExtent.height) - dh) / 2;',
        '''const auto ss=mw34::display::samples(std::getenv("MW34_REMASTER_AA"));
        const double ow=double(rw)/ss.x,oh=double(rh)/ss.y;
        const double fit=std::min(double(swapExtent.width)/ow,double(swapExtent.height)/oh);
        const int dw=int(std::lround(ow*fit)),dh=int(std::lround(oh*fit)),dx=(int(swapExtent.width)-dw)/2,dy=(int(swapExtent.height)-dh)/2;''')
    wide=host/'widescreen_stage.inc'
    text=wide.read_text(encoding='utf-8').replace('(3440.0/1440.0)','(double(mw34::vkscene::Renderer::remaster_width())/mw34::vkscene::Renderer::remaster_height())').replace('(3440.f/1440.f)','(float(mw34::vkscene::Renderer::remaster_width())/mw34::vkscene::Renderer::remaster_height())')
    wide.write_text(text,encoding='utf-8')
    stage=host/'mfc_stage.hpp'
    replace(stage,'~Host(){local_cd.reset();','~Host(){mw34::display::exclusive().release();local_cd.reset();')
    replace(stage,'if(is_dd&&n=="RestoreDisplayMode")return done(unsigned(reinterpret_cast<IDirectDraw*>(o->native)->RestoreDisplayMode()),1);','if(is_dd&&n=="RestoreDisplayMode"){mw34::display::exclusive().release();return done(unsigned(reinterpret_cast<IDirectDraw*>(o->native)->RestoreDisplayMode()),1);}')
    text=stage.read_text(encoding='utf-8')
    start=text.index('     if(wm&&std::string(wm)=="windowed"){')
    end=text.index('     }else{',start)
    replace(stage,text[start:end],'''     if(wm&&(std::string(wm)=="windowed"||std::string(wm)=="fullscreen"||std::string(wm)=="fullscreen_windowed")){
      const bool windowed=std::string(wm)=="windowed",exclusive=std::string(wm)=="fullscreen";
      if(exclusive)mw34::display::exclusive().acquire(wnd,rw?rw:w,rh?rh:h);else mw34::display::exclusive().release();
      MONITORINFO monitor{sizeof(monitor)};if(!::GetMonitorInfoW(::MonitorFromWindow(wnd,MONITOR_DEFAULTTONEAREST),&monitor))throw std::runtime_error("Cannot locate display monitor");
      RECT r=monitor.rcMonitor;
      if(windowed){r={0,0,int(rw?rw:w),int(rh?rh:h)};::AdjustWindowRectEx(&r,WS_OVERLAPPEDWINDOW,FALSE,WS_EX_APPWINDOW|WS_EX_WINDOWEDGE);}
      const DWORD style=windowed?WS_OVERLAPPEDWINDOW|WS_VISIBLE:WS_POPUP|WS_VISIBLE;
      ::SetWindowLongPtrW(wnd,GWL_STYLE,style);
      ::SetWindowLongPtrW(wnd,GWL_EXSTYLE,(::GetWindowLongPtrW(wnd,GWL_EXSTYLE)&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE))|WS_EX_APPWINDOW|(windowed?WS_EX_WINDOWEDGE:0));
      const int x=windowed?monitor.rcWork.left+std::max<LONG>(0,((monitor.rcWork.right-monitor.rcWork.left)-(r.right-r.left))/2):r.left;
      const int y=windowed?monitor.rcWork.top+std::max<LONG>(0,((monitor.rcWork.bottom-monitor.rcWork.top)-(r.bottom-r.top))/2):r.top;
      {LastError l(host);if(!::SetWindowPos(wnd,exclusive?HWND_TOP:HWND_NOTOPMOST,x,y,r.right-r.left,r.bottom-r.top,SWP_FRAMECHANGED|SWP_SHOWWINDOW|(host.scripted?SWP_NOACTIVATE:0U)))throw std::runtime_error("Cannot apply requested game window mode");}
''')
    replace(stage,'if(n=="DestroyWindow"&&r)host.windows.erase(W(0));','if(n=="DestroyWindow"&&r){if(W(0)==host.display.window)mw34::display::exclusive().release();host.windows.erase(W(0));}')
    replace(vk,'if(widescreen()&&!wide_world){','if(!wide_world){')
    replace(stage,'if(n=="SetWindowPos"){BOOL r{};', 'if(n=="SetWindowPos"){const char*wm=std::getenv("MW34_WINDOW_MODE");if(W(0)==host.display.window&&wm&&mw34::vkscene::Renderer::remaster_width()&&int(arg(4))>0&&int(arg(4))<=800)return done(::SetWindowPos(W(0),nullptr,0,0,0,0,arg(6)|SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER)?1U:0U,7);BOOL r{};')
    replace(stage,'   LONG r{};{LastError l(host);r=set?::SetWindowLongA(h,idx,LONG(arg(2))): ::GetWindowLongA(h,idx);}',
        '''   LONG value=LONG(arg(2));
   if(set&&h==host.display.window){const char*wm=std::getenv("MW34_WINDOW_MODE");if(wm){
    const bool windowed=std::string(wm)=="windowed";
    if(idx==GWL_STYLE)value=windowed?((value&~WS_POPUP)|WS_OVERLAPPEDWINDOW):((value&~WS_OVERLAPPEDWINDOW)|WS_POPUP);
    if(idx==GWL_EXSTYLE)value=(value&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE))|WS_EX_APPWINDOW|(windowed?WS_EX_WINDOWEDGE:0);
   }}
   LONG r{};{LastError l(host);r=set?::SetWindowLongA(h,idx,value): ::GetWindowLongA(h,idx);}''')
    apply_exclusive(host)


def apply_exclusive(host):
    vk=host/'vk_scene.hpp'
    replace(vk,'    bool srcRgba{};', '''    PFN_vkGetPhysicalDeviceSurfaceCapabilities2KHR surfaceCaps2{};
    PFN_vkAcquireFullScreenExclusiveModeEXT acquireExclusive{};
    PFN_vkReleaseFullScreenExclusiveModeEXT releaseExclusive{};
    bool exclusiveDevice{},exclusiveHeld{};
    static bool exclusiveRequested(){const char*p=std::getenv("MW34_WINDOW_MODE");return p&&!std::strcmp(p,"fullscreen");}
    bool syncExclusive(){
        if(!exclusiveDevice)return true;
        const bool foreground=::GetAncestor(::GetForegroundWindow(),GA_ROOT)==::GetAncestor(presentParent,GA_ROOT);
        if(!foreground){if(exclusiveHeld){check(releaseExclusive(device,swapchain),"release fullscreen on focus loss");exclusiveHeld=false;}return false;}
        if(!exclusiveHeld){check(acquireExclusive(device,swapchain),"acquire Vulkan exclusive fullscreen");exclusiveHeld=true;std::fprintf(stderr,"Vulkan exclusive fullscreen acquired\\n");}
        return true;
    }
    bool srcRgba{};''')
    replace(vk,'if (has(VK_KHR_SURFACE_EXTENSION_NAME) && has(VK_KHR_WIN32_SURFACE_EXTENSION_NAME)) instanceExtensions = {VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_WIN32_SURFACE_EXTENSION_NAME};', '''if (has(VK_KHR_SURFACE_EXTENSION_NAME) && has(VK_KHR_WIN32_SURFACE_EXTENSION_NAME)) instanceExtensions = {VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_WIN32_SURFACE_EXTENSION_NAME};
            if(exclusiveRequested()){
                if(!has(VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME)||!has(VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME))throw std::runtime_error("Vulkan exclusive fullscreen instance extensions are unavailable");
                instanceExtensions.push_back(VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME);
                instanceExtensions.push_back(VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME);
            }''')
    replace(vk,'        const char *swapExt = VK_KHR_SWAPCHAIN_EXTENSION_NAME;', '        const char *swapExt = VK_KHR_SWAPCHAIN_EXTENSION_NAME;\n        std::vector<const char*> deviceExtensions;')
    replace(vk,'for (const auto &p : props) if (!std::strcmp(p.extensionName, swapExt)) presentable = !instanceExtensions.empty() && f.vkCreateWin32SurfaceKHR;', '''for (const auto &p : props){if (!std::strcmp(p.extensionName, swapExt)) presentable = !instanceExtensions.empty() && f.vkCreateWin32SurfaceKHR;
                if(exclusiveRequested()&&!std::strcmp(p.extensionName,VK_EXT_FULL_SCREEN_EXCLUSIVE_EXTENSION_NAME))exclusiveDevice=true;}
            if(exclusiveRequested()&&!exclusiveDevice)throw std::runtime_error("GPU does not support Vulkan exclusive fullscreen");''')
    replace(vk,'if (presentable) { dci.enabledExtensionCount = 1; dci.ppEnabledExtensionNames = &swapExt; }', '''if(presentable){deviceExtensions.push_back(swapExt);if(exclusiveDevice)deviceExtensions.push_back(VK_EXT_FULL_SCREEN_EXCLUSIVE_EXTENSION_NAME);dci.enabledExtensionCount=unsigned(deviceExtensions.size());dci.ppEnabledExtensionNames=deviceExtensions.data();}''')
    replace(vk,'        MW34_VK_DEV_FNS(MW34_VK_DLOAD)', '''        MW34_VK_DEV_FNS(MW34_VK_DLOAD)
        if(exclusiveDevice){
            surfaceCaps2=reinterpret_cast<PFN_vkGetPhysicalDeviceSurfaceCapabilities2KHR>(get(instance,"vkGetPhysicalDeviceSurfaceCapabilities2KHR"));
            acquireExclusive=reinterpret_cast<PFN_vkAcquireFullScreenExclusiveModeEXT>(f.vkGetDeviceProcAddr(device,"vkAcquireFullScreenExclusiveModeEXT"));
            releaseExclusive=reinterpret_cast<PFN_vkReleaseFullScreenExclusiveModeEXT>(f.vkGetDeviceProcAddr(device,"vkReleaseFullScreenExclusiveModeEXT"));
            if(!surfaceCaps2||!acquireExclusive||!releaseExclusive)throw std::runtime_error("Vulkan exclusive fullscreen entry points are missing");
        }''')
    replace(vk,'        f.vkDestroySwapchainKHR(device, swapchain, nullptr);','        if(exclusiveHeld){releaseExclusive(device,swapchain);exclusiveHeld=false;}\n        f.vkDestroySwapchainKHR(device, swapchain, nullptr);')
    replace(vk,'if (swapchain && e.width == swapExtent.width && e.height == swapExtent.height) return true;', 'if (swapchain && e.width == swapExtent.width && e.height == swapExtent.height) return syncExclusive();')
    replace(vk,'        sc.surface = windowSurface;', '''        sc.surface = windowSurface;
        VkSurfaceFullScreenExclusiveWin32InfoEXT monitor{VK_STRUCTURE_TYPE_SURFACE_FULL_SCREEN_EXCLUSIVE_WIN32_INFO_EXT};monitor.hmonitor=::MonitorFromWindow(presentParent,MONITOR_DEFAULTTONEAREST);
        VkSurfaceFullScreenExclusiveInfoEXT full{VK_STRUCTURE_TYPE_SURFACE_FULL_SCREEN_EXCLUSIVE_INFO_EXT};full.fullScreenExclusive=VK_FULL_SCREEN_EXCLUSIVE_APPLICATION_CONTROLLED_EXT;full.pNext=&monitor;
        if(exclusiveDevice){
            VkPhysicalDeviceSurfaceInfo2KHR info{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SURFACE_INFO_2_KHR};info.surface=windowSurface;info.pNext=&full;
            VkSurfaceCapabilitiesFullScreenExclusiveEXT supported{VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_FULL_SCREEN_EXCLUSIVE_EXT};
            VkSurfaceCapabilities2KHR capabilities{VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_2_KHR};capabilities.pNext=&supported;
            check(surfaceCaps2(gpu,&info,&capabilities),"query exclusive fullscreen support");
            if(!supported.fullScreenExclusiveSupported)throw std::runtime_error("Exclusive fullscreen is not supported for this window and monitor");
            sc.pNext=&full;
        }''')
    replace(vk,'        swapExtent = e;\n        return true;', '        swapExtent = e;\n        return syncExclusive();')
    text=vk.read_text(encoding='utf-8').replace('r == VK_ERROR_OUT_OF_DATE_KHR', '(r == VK_ERROR_OUT_OF_DATE_KHR || r == VK_ERROR_FULL_SCREEN_EXCLUSIVE_MODE_LOST_EXT)')
    vk.write_text(text,encoding='utf-8')



if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
