// Window classes, window procedures and messages between real USER32 windows and lifted guest code
// (included inside mf::Stage). Real classes/windows are registered/created on the host; every guest
// window procedure is reached through the host trampoline wnd_tramp, which marshals pointer messages
// into guest scratch memory below the guest ESP and runs the guest procedure as a nested call. Host
// window procedures the guest sees (DefWindowProc, system classes, pre-subclass procedures) are host
// procedure tokens. Faults inside callbacks are recorded and re-thrown when the host API returns.

// ---- host procedure tokens ------------------------------------------------------------------------
unsigned host_proc_token(WNDPROC p){for(unsigned i=0;i<host.host_procs.size();++i)if(host.host_procs[i]==p)return host_proc_base+16*i;host.host_procs.push_back(p);return host_proc_base+16*unsigned(host.host_procs.size()-1);}
WNDPROC host_proc(unsigned t)const{if(t<host_proc_base||(t-host_proc_base)%16||(t-host_proc_base)/16>=host.host_procs.size())return nullptr;return host.host_procs[(t-host_proc_base)/16];}
// ---- per-window guest procedure -------------------------------------------------------------------
unsigned class_guest_proc(HWND h){char name[256]{};if(!::GetClassNameA(h,name,sizeof(name)))return 0;for(const auto&c:host.classes)if(_stricmp(c.name.c_str(),name)==0)return c.guest_proc;return 0;}
unsigned window_proc(HWND h){auto it=host.windows.find(h);if(it!=host.windows.end())return it->second;return class_guest_proc(h);}
// ---- message frames: guest copies of host message parameters ----------------------------------------
struct MsgFrame{HWND hwnd;UINT msg;WPARAM host_w;LPARAM host_l;unsigned guest_w,guest_l;unsigned copy;unsigned bytes;};
std::vector<MsgFrame>msg_frames;unsigned opaque_count{};static constexpr unsigned opaque_base=0x3b000000;
static bool pointer_message(UINT m){switch(m){case WM_CREATE:case WM_NCCREATE:case WM_GETMINMAXINFO:case WM_NCCALCSIZE:case WM_WINDOWPOSCHANGING:case WM_WINDOWPOSCHANGED:
 case WM_STYLECHANGING:case WM_STYLECHANGED:case WM_SETTEXT:case WM_GETTEXT:case WM_DRAWITEM:case WM_MEASUREITEM:case WM_NOTIFY:case WM_COPYDATA:case WM_HELP:case WM_DELETEITEM:case WM_COMPAREITEM:
 case WM_WININICHANGE:case WM_DEVMODECHANGE:case WM_MDICREATE:return true;default:return false;}}
// Writes the guest copy of a host structure (bytes, x86 layout == host layout for these POD records).
unsigned put_bytes(unsigned&at,const void*p,unsigned n){at-=(n+3)&~3U;const auto*b=static_cast<const unsigned char*>(p);for(unsigned i=0;i<n;++i)runtime.memory().store<unsigned char>({at+i},b[i]);return at;}
void get_bytes(unsigned a,void*p,unsigned n){auto*b=static_cast<std::byte*>(p);for(unsigned o=0;o<n;){const unsigned k=std::min(n-o,4096U-((a+o)&4095U));runtime.memory().read({a+o},std::span<std::byte>(b+o,k));o+=k;}}
// Bulk guest write in page-bounded chunks (the caller has checked the range against the memory contract).
void write_bytes(unsigned a,const void*p,unsigned n){auto*b=static_cast<const std::byte*>(p);for(unsigned o=0;o<n;){const unsigned k=std::min(n-o,4096U-((a+o)&4095U));runtime.memory().write({a+o},std::span<const std::byte>(b+o,k));o+=k;}}
unsigned gwnd(HWND h){const auto v=reinterpret_cast<std::intptr_t>(h);if(v!=std::intptr_t(std::int32_t(v)))deny("Window handle not representable as a guest word",0);return unsigned(v);}
static HWND hwnd_of(unsigned v){return reinterpret_cast<HWND>(std::intptr_t(std::int32_t(v)));}
// x86 CREATESTRUCTA (48 bytes) with strings copied below `at`.
unsigned put_createstruct(unsigned&at,const CREATESTRUCTA&cs){const unsigned name=scratch_string(at,cs.lpszName),cls=scratch_string(at,cs.lpszClass);at-=48;
 const std::array<unsigned,12>v{unsigned(reinterpret_cast<std::uintptr_t>(cs.lpCreateParams)),guest_instance(cs.hInstance),gwnd(reinterpret_cast<HWND>(cs.hMenu)),gwnd(cs.hwndParent),unsigned(cs.cy),unsigned(cs.cx),unsigned(cs.y),unsigned(cs.x),unsigned(cs.style),name,cls,cs.dwExStyle};
 for(unsigned i=0;i<12;++i)store(at+4*i,v[i]);return at;}
// Marshal host (w,l) to guest values; returns the frame (copy = guest structure address, 0 if none).
MsgFrame marshal(HWND h,UINT m,WPARAM w,LPARAM l,unsigned&at){MsgFrame f{h,m,w,l,unsigned(w),unsigned(l),0,0};
 if(mw34::temporal::enabled()&&h==host.display.window&&(m==WM_SETFOCUS||m==WM_KILLFOCUS||m==WM_ACTIVATEAPP||m==WM_SIZE))camera_reset();
 // A host lParam that does not fit a guest word (undocumented system messages such as the UAH menu
 // messages carry host pointers the application never interprets) becomes an opaque guest token; the
 // frame maps it back to the host pointer when the guest forwards the message to a host procedure.
 auto plain=[&](){const auto lw=static_cast<std::int64_t>(l);if(lw!=std::int64_t(std::int32_t(lw)))f.guest_l=opaque_base+16*unsigned(++opaque_count%0x10000);};
 switch(m){
 case WM_CREATE:case WM_NCCREATE:{f.copy=put_createstruct(at,*reinterpret_cast<const CREATESTRUCTA*>(l));f.guest_l=f.copy;break;}
 case WM_GETMINMAXINFO:f.bytes=sizeof(MINMAXINFO);f.copy=put_bytes(at,reinterpret_cast<const void*>(l),f.bytes);f.guest_l=f.copy;break;
 case WM_WINDOWPOSCHANGING:case WM_WINDOWPOSCHANGED:{const auto&p=*reinterpret_cast<const WINDOWPOS*>(l);at-=28;const std::array<unsigned,7>v{gwnd(p.hwnd),gwnd(p.hwndInsertAfter),unsigned(p.x),unsigned(p.y),unsigned(p.cx),unsigned(p.cy),p.flags};
  for(unsigned i=0;i<7;++i)store(at+4*i,v[i]);f.copy=at;f.bytes=28;f.guest_l=at;break;}
 case WM_NCCALCSIZE:if(!w){f.bytes=16;f.copy=put_bytes(at,reinterpret_cast<const void*>(l),16);f.guest_l=f.copy;}
  else{const auto&p=*reinterpret_cast<const NCCALCSIZE_PARAMS*>(l);const auto&wp=*p.lppos;at-=28;const std::array<unsigned,7>v{gwnd(wp.hwnd),gwnd(wp.hwndInsertAfter),unsigned(wp.x),unsigned(wp.y),unsigned(wp.cx),unsigned(wp.cy),wp.flags};
   for(unsigned i=0;i<7;++i)store(at+4*i,v[i]);const unsigned gpos=at;at-=52;for(unsigned r=0;r<3;++r){const RECT&rc=p.rgrc[r];store(at+16*r,unsigned(rc.left));store(at+16*r+4,unsigned(rc.top));store(at+16*r+8,unsigned(rc.right));store(at+16*r+12,unsigned(rc.bottom));}
   store(at+48,gpos);f.copy=at;f.bytes=48;f.guest_l=at;}break;
 case WM_STYLECHANGING:case WM_STYLECHANGED:f.bytes=8;f.copy=put_bytes(at,reinterpret_cast<const void*>(l),8);f.guest_l=f.copy;break;
 case WM_SETTEXT:case WM_WININICHANGE:case WM_DEVMODECHANGE:f.guest_l=scratch_string(at,reinterpret_cast<const char*>(l));break;
 case WM_GETTEXT:{const unsigned n=unsigned(w);if(n>0x10000)deny("WM_GETTEXT buffer too large",n);at-=(n+3)&~3U;f.copy=at;f.bytes=n;f.guest_l=at;break;}
 // F1 (WM_KEYF1) makes DefWindowProc send WM_HELP: x86 HELPINFO (28 bytes; read-only for the receiver).
 case WM_HELP:{const auto&hi=*reinterpret_cast<const HELPINFO*>(l);if(hi.dwContextId>0xffffffffull)deny("WM_HELP context id not representable as a guest word",0);at-=28;
  const std::array<unsigned,7>v{28u,unsigned(hi.iContextType),unsigned(hi.iCtrlId),gwnd(reinterpret_cast<HWND>(hi.hItemHandle)),unsigned(hi.dwContextId),unsigned(hi.MousePos.x),unsigned(hi.MousePos.y)};
  for(unsigned i=0;i<7;++i)store(at+4*i,v[i]);f.copy=at;f.guest_l=at;break;}
 default:if(pointer_message(m))deny("Pointer message without marshalling: "+std::to_string(m),m);plain();
  if(m==WM_ACTIVATE||m==WM_MDIACTIVATE||m==WM_SETFOCUS||m==WM_KILLFOCUS||m==WM_PARENTNOTIFY)f.guest_l=gwnd(reinterpret_cast<HWND>(l));
 }
 if(m==WM_SETFOCUS||m==WM_KILLFOCUS||m==WM_SETCURSOR||m==WM_ERASEBKGND||m==WM_CTLCOLORMSGBOX||m==WM_CTLCOLOREDIT||m==WM_CTLCOLORLISTBOX||m==WM_CTLCOLORBTN||m==WM_CTLCOLORDLG||m==WM_CTLCOLORSCROLLBAR||m==WM_CTLCOLORSTATIC)
  f.guest_w=gwnd(reinterpret_cast<HWND>(w));
 return f;}
// Copy the guest structure back into the host structure (after the guest procedure ran).
void unmarshal(const MsgFrame&f){if(!f.copy)return;
 switch(f.msg){
 case WM_GETMINMAXINFO:case WM_STYLECHANGING:get_bytes(f.copy,reinterpret_cast<void*>(f.host_l),f.bytes);break;
 case WM_NCCALCSIZE:if(!f.host_w)get_bytes(f.copy,reinterpret_cast<void*>(f.host_l),16);else{auto&p=*reinterpret_cast<NCCALCSIZE_PARAMS*>(f.host_l);for(unsigned r=0;r<3;++r){RECT&rc=p.rgrc[r];rc.left=LONG(load(f.copy+16*r));rc.top=LONG(load(f.copy+16*r+4));rc.right=LONG(load(f.copy+16*r+8));rc.bottom=LONG(load(f.copy+16*r+12));}}break;
 case WM_WINDOWPOSCHANGING:{auto&p=*reinterpret_cast<WINDOWPOS*>(f.host_l);p.hwndInsertAfter=hwnd_of(load(f.copy+4));p.x=int(load(f.copy+8));p.y=int(load(f.copy+12));p.cx=int(load(f.copy+16));p.cy=int(load(f.copy+20));p.flags=load(f.copy+24);break;}
 case WM_GETTEXT:get_bytes(f.copy,reinterpret_cast<void*>(f.host_l),f.bytes);break;
 default:break;}}
// Host message -> guest procedure (nested call), with copy-back.
LRESULT deliver(unsigned proc,HWND h,UINT m,WPARAM w,LPARAM l){auto&g=state.gpr;unsigned at=(g.rsp.dword-0x200)&~15U;MsgFrame f=marshal(h,m,w,l,at);
 msg_frames.push_back(f);struct Pop{std::vector<MsgFrame>&v;~Pop(){v.pop_back();}}pop{msg_frames};
 ++in_wndproc;struct WndprocDepth{unsigned&n;~WndprocDepth(){--n;}}wndproc_depth{in_wndproc};
 const unsigned r=call_guest(proc,{gwnd(h),unsigned(m),f.guest_w,f.guest_l},true,"window procedure message "+std::to_string(m),at&~15U);unmarshal(msg_frames.back());return LRESULT(std::int32_t(r));}
static LRESULT CALLBACK wnd_tramp(HWND h,UINT m,WPARAM w,LPARAM l){Stage*st=owner;
 if(!st||!st->callback_fault.empty())return ::DefWindowProcA(h,m,w,l);
 if(st->host.thread_tid){st->callback_fault="Window procedure invoked while a secondary guest thread runs (cross-thread message delivery is not modelled) (message "+std::to_string(m)+")";return ::DefWindowProcA(h,m,w,l);}
 try{const unsigned proc=st->window_proc(h);if(!proc)throw std::runtime_error("Window without a guest procedure");if(auto hp=st->host_proc(proc))return ::CallWindowProcA(hp,h,m,w,l);return st->deliver(proc,h,m,w,l);}
 catch(const std::exception&e){st->callback_fault=std::string(e.what())+" (message "+std::to_string(m)+")";return ::DefWindowProcA(h,m,w,l);}}
// Guest (hwnd,msg,w,l) back to a host procedure: inside an active frame for the same message the guest copy
// is synced into the host structure and the original host parameters are passed; otherwise plain values.
LRESULT to_host(WNDPROC p,unsigned hw,unsigned m,unsigned w,unsigned l){const HWND h=hwnd_of(hw);
 for(auto it=msg_frames.rbegin();it!=msg_frames.rend();++it)if(it->hwnd==h&&it->msg==m&&it->guest_l==l&&it->guest_w==w){unmarshal(*it);LRESULT r=p?::CallWindowProcA(p,h,m,it->host_w,it->host_l): ::DefWindowProcA(h,m,it->host_w,it->host_l);
  // refresh the guest copy with what the host procedure wrote
  if(it->copy&&it->bytes&&(m==WM_GETMINMAXINFO||m==WM_STYLECHANGING||m==WM_GETTEXT||(m==WM_NCCALCSIZE&&!it->host_w)))put_back(*it);return r;}
 if(pointer_message(m))deny("Host procedure call with a pointer message outside its active frame: "+std::to_string(m),m);
 const WPARAM hwp=(m==WM_SETFOCUS||m==WM_KILLFOCUS||m==WM_SETCURSOR||m==WM_ERASEBKGND)?WPARAM(hwnd_of(w)):WPARAM(w);const LPARAM hl=LPARAM(std::int64_t(std::int32_t(l)));
 return p?::CallWindowProcA(p,h,m,hwp,hl): ::DefWindowProcA(h,m,hwp,hl);}
void put_back(const MsgFrame&f){const auto*b=reinterpret_cast<const unsigned char*>(f.host_l);for(unsigned i=0;i<f.bytes;++i)runtime.memory().store<unsigned char>({f.copy+i},b[i]);}
