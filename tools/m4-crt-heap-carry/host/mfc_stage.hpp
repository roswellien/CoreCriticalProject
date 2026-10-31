#pragma once
// MFC42 DLL attach: _DllMainCRTStartup(hinst=5F400000, DLL_PROCESS_ATTACH, reserved!=0) from its
// real entry 0x5F4052A2 over the static closure lifted by lift_closure.py (296 entries, dispatched
// through the generated mfc_entries.inc table) plus the already lifted MSVCRT bodies MFC42 reaches
// through its bound imports.
//
// map_image() is the loader model: MFC42 at its preferred base (no relocation) with literal
// headers and sections, then import binding. MSVCRT imports are bound to the export addresses of
// the staged MSVCRT image, whose attach has completed natively in this guest; every other import
// is bound to a per-import token that only this stage dispatches, by name, to a real host service.
//
// Every CALL pushes its return word and every RET must return to it. Indirect calls, JMPs and
// continuations resolve only to lifted entries, bound MSVCRT bodies or service tokens; anything
// else (an unlifted target, an unimplemented service, an access outside the memory contract, a
// divide error) stops with a typed unresolved_translation Fault. SEH dispatch is not modelled.
#include "vk_scene.hpp"
#include "missile_exhaust.hpp"
#include "early_triangle_commands.hpp"
#include "controller_input.hpp"
#include "mech_headlights.hpp"
#include "surface_page_pool.hpp"
#include "texture_backing.hpp"
#include "menu_wave.hpp"
#include "sun_camera_binding.hpp"
#include "heap_partitions.hpp"
#include "service_history.hpp"
#include "body_dispatch.hpp"
#include "exact_shared_value.hpp"
#include "large_texture_seek.hpp"
#include "texture_read_diagnostics.hpp"
#include "turret_aim_math.hpp"
#include "photo_replay_math.hpp"
#include <atomic>
#include <deque>
#include <string_view>
#include <unordered_map>
#include <set>
#include <map>
#include <mmsystem.h>
#include "audio/local_cd_audio.hpp"
#include "graphics/menu_version.hpp"
#include "graphics/retained_texture_cache.hpp"
#include <vfw.h>
#include <fstream>
#include <iterator>
#include <functional>
#include "com_ddraw.hpp"
#include "input/directinput_caps.hpp"
#include <string>
inline std::atomic<unsigned>mw34_frames_presented{0};  /* presented frames, for the host profiler window */
extern "C" unsigned long long mw34_x87_counts[2];  /* composition.cpp: flog2/fexp2 bridge calls (diagnostic) */
#include "guest_memory_fast.hpp"  /* the region cache of guest_memory_cached.cpp */
#include "fast_gate.hpp"  /* gate for the inlined bridge fast paths (fast_bridges.cpp) */
extern "C" { inline Mw34FastGate mw34_fast_gate{}; }
static_assert(sizeof(Mw34FastHit)==sizeof(mw34::fastmem::Hit)&&offsetof(Mw34FastHit,owner)==offsetof(mw34::fastmem::Hit,owner)&&offsetof(Mw34FastHit,generation)==offsetof(mw34::fastmem::Hit,generation)
 &&offsetof(Mw34FastHit,start)==offsetof(mw34::fastmem::Hit,start)&&offsetof(Mw34FastHit,size)==offsetof(mw34::fastmem::Hit,size)&&offsetof(Mw34FastHit,bytes)==offsetof(mw34::fastmem::Hit,bytes)
 &&offsetof(Mw34FastHit,permissions)==offsetof(mw34::fastmem::Hit,permissions),"Fast-path cache mirror matches mw34::fastmem::Hit");
static_assert(sizeof(unsigned long long)==sizeof(std::uint64_t)&&static_cast<unsigned>(mw34::Permissions::read)==1&&static_cast<unsigned>(mw34::Permissions::write)==2,"Fast-path cache permission bits");
namespace mw34::m4_crt_mfc_attach {
namespace hs=m4_crt_heap_carry;
using Body=hs::Body;
struct Entry{unsigned addr;Body body;};
#include "mfc_entries.inc"
inline constexpr unsigned base=0x5f400000,image_end=0x5f4ed000,data=0x5f4cb000,data_end=0x5f4d3000,entry=0x5f4052a2,token_base=0x38000000,token_end=0x38010000,host_proc_base=0x39000000,vsurface_arena=0x40000000,vsurface_arena_end=0x50000000;
inline constexpr unsigned msvcrt_base=0x78000000,msvcrt_text_end=0x7802e000,msvcrt_data=0x78035000,msvcrt_data_end=0x7803c000;
inline constexpr unsigned crt_entry=0x5ac3a0,initterm_thunk=0x5ac598,game_end=0x9f5000,game_data=0x5e0000,game_data_end=0x9a2000,game_stack_low=0x20001000,game_stack_top=0x20002000,stack_extension=0x1ff01000,entry_continuation=0x5ac480,msvcrt_entry=0x780017fd;
inline constexpr char image_sha[]="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8";
// Lifted MSVCRT bodies reachable through MFC42's bound imports (functions and their continuations).
inline constexpr std::array<Entry,22>msvcrt_entries{{{0x78001000,hs::mw34_attach_memset_body},{0x78001055,hs::mw34_attach_lock_body},{0x78001080,hs::mw34_attach_lock_tail_body},
 {0x7800129e,hs::mw34_attach_unlock_body},{0x780012b3,hs::mw34_allocation_malloc_body},{0x780012c5,hs::mw34_allocation_size_body},{0x780012e3,hs::mw34_allocation_worker_body},
 {0x78001367,hs::mw34_allocation_worker_epilogue_body},{0x78001377,hs::mw34_allocation_alloc_tail_body},{0x78001390,hs::mw34_allocation_free_body},{0x78001416,hs::mw34_allocation_free_epilogue_body},
 {0x78001428,hs::mw34_allocation_free_tail_body},{0x780014f8,hs::mw34_attach_initterm_body},{0x78001514,hs::mw34_attach_lockexit_body},{0x7800151d,hs::mw34_attach_msize_body},
 {0x780018f9,hs::mw34_attach_calloc_body},{0x78002f32,hs::mw34_attach_strlen_body},{0x78003041,hs::mw34_attach_unlockexit_body},{0x780044dd,hs::mw34_attach_allmul_body},
 {0x78004a36,hs::mw34_attach_onexit_body},{0x7800cc39,hs::mw34_allocation_freecold_body},{0x7800cc97,hs::mw34_allocation_round_body}}};
// MSVCRT _ftol (0x78002551): FNSTCW, RC := truncate, FLDCW, FISTP qword, FLDCW, then EAX:EDX, the compiler's
// float-to-integer conversion, called constantly by the game. The lifted body runs it through two rounding-mode
// bridges (serializing FLDCW/LDMXCSR), two FWAIT exception clears, an FRNDINT bridge and an FNCLEX; for a finite
// normal or zero ST0 with |ST0| < 2^63 its whole effect is fixed, and this host body produces exactly that effect:
// - guest stack: [ESP-4] = EBP, [ESP-6] = CW, [ESP-8] = CW|0C00h, [ESP-10h] = the 64-bit result;
// - registers: EAX:EDX = trunc(ST0), EBP restored, ESP += 4, EIP = the return word; EFLAGS of `or ah,0Ch`
//   (CF, ZF, OF, AF clear; PF of that byte; SF = CW bit 15);
// - x87: ST0 popped (the lifted stack rotation: slots shift down, slot 7 = old ST0), TOP + 1, CW unchanged, last
//   instruction FISTP (opcode 37Dh at 7800256Ah, data pointer [EBP-0Ch]); DE status cleared; and, when neither IE nor
//   PE is already sticky, PE = inexact;
// - host: the guest rounding mode mirrored into the x87 CW and MXCSR as the closing FLDCW leaves it, and the host
//   exception flags clear (the lifted body's FNCLEX; no later operation of this case raises one).
// Every other operand (NaN, infinity, denormal, unnormal, out of range) takes the lifted body. MW34_FTOL_FAST=0
// disables this; MW34_FTOL_CHECK=1 runs both on every call and stops on any State, stack or host-FPU difference.
extern "C" void*__remill_function_return(State*,unsigned,void*)noexcept(false);
inline bool ftol_fast_on(){static const bool on=[]{const char*e=std::getenv("MW34_FTOL_FAST");return !(e&&*e=='0');}();return on;}
inline bool ftol_check_on(){static const bool on=[]{const char*e=std::getenv("MW34_FTOL_CHECK");return e&&*e=='1';}();return on;}
// False when the operand needs the lifted body (nothing has been changed then); otherwise sets the return word.
inline bool ftol_core(State*st,unsigned pc,void*p,unsigned&ret_out){
 auto*S=reinterpret_cast<unsigned char*>(st);auto*M=static_cast<unsigned char*>(p);
 auto rd32=[&](unsigned o){unsigned v;std::memcpy(&v,S+o,4);return v;};auto wr32=[&](unsigned o,unsigned v){std::memcpy(S+o,&v,4);};
 auto rd16=[&](unsigned o){unsigned short v;std::memcpy(&v,S+o,2);return v;};auto wr16=[&](unsigned o,unsigned short v){std::memcpy(S+o,&v,2);};
 std::uint64_t m;unsigned short se;std::memcpy(&m,S+0x9b6,8);std::memcpy(&se,S+0x9be,2);const unsigned e=se&0x7fffU;const bool neg=(se>>15)!=0;
 std::uint64_t ip;bool inexact;
 if(e==0&&m==0){ip=0;inexact=false;}
 else{if(e==0||e==0x7fff||!(m>>63)||e>16383U+62U)return false;  // denormal/unnormal/NaN/infinity or |x| >= 2^63
  if(e<16383U){ip=0;inexact=true;}else{const unsigned sh=63U-(e-16383U);ip=m>>sh;inexact=(m&((std::uint64_t(1)<<sh)-1))!=0;}}
 const std::uint64_t rc=neg?std::uint64_t(0)-ip:ip;
 const unsigned ss=rd32(0x848),esp0=rd32(0x908),ebp0=rd32(0x918),frame=esp0-4;const unsigned short cw=rd16(0xad0);
 auto mem=[&](unsigned a){return M+a;};
 std::memcpy(mem(frame+ss),&ebp0,4);                                   // push ebp
 std::memcpy(mem(ss+esp0-6),&cw,2);                                    // fnstcw [ebp-2]
 const unsigned short tcw=static_cast<unsigned short>(cw|0x0c00);std::memcpy(mem(ss+esp0-8),&tcw,2);  // [ebp-4]
 const unsigned char ah=static_cast<unsigned char>((cw>>8)|0x0c);
 S[0x811]=0;S[0x813]=static_cast<unsigned char>((__builtin_popcount(ah)&1)==0);S[0x817]=0;S[0x819]=static_cast<unsigned char>((cw>>15)&1);S[0x81d]=0;S[0x815]=0;
 const unsigned fd=frame+ss-0xc;
 wr16(0xad6,0x37d);wr32(0xad8,pc+0x19);wr16(0xadc,rd16(0x83e));wr32(0xae0,fd);wr16(0xae4,rd16(0x83a));
 S[0xac1]=0;                                                            // DE := host DE (clear)
 if((S[0xac3]|S[0xab9])==0){S[0xab9]=static_cast<unsigned char>(inexact);S[0xac3]=0;}
 std::memcpy(mem(fd),&rc,8);                                            // fistp qword [ebp-0Ch]
 {unsigned char old[10];std::memcpy(old,S+0x9b6,10);for(unsigned i=0;i<7;++i)std::memmove(S+0x9b6+16*i,S+0x9c6+16*i,10);std::memcpy(S+0xa26,old,10);}
 {const unsigned short sw=rd16(0xad2);wr16(0xad2,static_cast<unsigned short>((sw&~0x3800U)|((sw+0x800U)&0x3800U)));}
 unsigned short cw2;std::memcpy(&cw2,mem(frame+ss-2),2);wr16(0xad0,cw2);
 unsigned lo,hi,ebp1,ret;std::memcpy(&lo,mem(frame+ss-0xc),4);std::memcpy(&hi,mem(frame+ss-8),4);std::memcpy(&ebp1,mem(frame+ss),4);std::memcpy(&ret,mem(frame+ss+4),4);
 wr32(0x8a8,lo);wr32(0x8d8,hi);wr32(0x918,ebp1);wr32(0x908,frame+8);wr32(0x9a8,ret);
 {const unsigned mode=(cw2>>10)&3U;unsigned short hc;__asm__ volatile("fnstcw %0":"=m"(hc));const unsigned short nc=static_cast<unsigned short>((hc&~0xc00)|(mode<<10));if(nc!=hc)__asm__ volatile("fldcw %0"::"m"(nc));
  unsigned mx;__asm__ volatile("stmxcsr %0":"=m"(mx));const unsigned nmx=(mx&~0x6000U)|(mode<<13);if(nmx!=mx)__asm__ volatile("ldmxcsr %0"::"m"(nmx));
  unsigned short hs;__asm__ volatile("fnstsw %0":"=m"(hs));if(hs&0x80ffU)__asm__ volatile("fnclex":::"memory");}
 ret_out=ret;return true;}
inline void*ftol_body(State*s,unsigned a,void*p){
 if(!ftol_check_on()){unsigned ret;if(ftol_core(s,a,p,ret))return __remill_function_return(s,ret,p);return mw34_attach_m_78002551_body(s,a,p);}
 // Differential check: the host body on a snapshot, then the lifted body on the original; both results compared.
 static std::uint64_t checked{},fallbacks{};
 std::array<unsigned char,3504>s0,s1;std::memcpy(s0.data(),s,3504);
 const unsigned ss=reinterpret_cast<const unsigned*>(reinterpret_cast<unsigned char*>(s)+0x848)[0],esp0=reinterpret_cast<const unsigned*>(reinterpret_cast<unsigned char*>(s)+0x908)[0];
 unsigned char*mb=static_cast<unsigned char*>(p)+(ss+esp0-0x10);std::array<unsigned char,20>m0,m1;std::memcpy(m0.data(),mb,20);
 struct alignas(4) Env{std::uint32_t w[7];}e0;unsigned mx0;__asm__ volatile("fnstenv %0\n\tfldenv %0":"+m"(e0)::"memory");__asm__ volatile("stmxcsr %0":"=m"(mx0));
 unsigned ret;if(!ftol_core(s,a,p,ret)){++fallbacks;return mw34_attach_m_78002551_body(s,a,p);}
 std::memcpy(s1.data(),s,3504);std::memcpy(m1.data(),mb,20);unsigned short c1,w1;unsigned x1;__asm__ volatile("fnstcw %0\n\tfnstsw %1":"=m"(c1),"=m"(w1));__asm__ volatile("stmxcsr %0":"=m"(x1));
 std::memcpy(s,s0.data(),3504);std::memcpy(mb,m0.data(),20);__asm__ volatile("fldenv %0"::"m"(e0):"memory");__asm__ volatile("ldmxcsr %0"::"m"(mx0));
 void*r=mw34_attach_m_78002551_body(s,a,p);
 unsigned short c2,w2;unsigned x2;__asm__ volatile("fnstcw %0\n\tfnstsw %1":"=m"(c2),"=m"(w2));__asm__ volatile("stmxcsr %0":"=m"(x2));
 const auto*sn=reinterpret_cast<const unsigned char*>(s);std::string diff;
 for(unsigned i=0;i<3504;++i)if(sn[i]!=s1[i]){char b[48];std::snprintf(b,sizeof b," state+%x lifted %02x host %02x",i,sn[i],s1[i]);diff+=b;if(diff.size()>400)break;}
 for(unsigned i=0;i<20;++i)if(mb[i]!=m1[i]){char b[48];std::snprintf(b,sizeof b," stack[esp-%x] lifted %02x host %02x",0x10-i,mb[i],m1[i]);diff+=b;}
 if(c1!=c2||(w1&0x80ff)!=(w2&0x80ff)||x1!=x2){char b[96];std::snprintf(b,sizeof b," host cw %04x/%04x sw %04x/%04x mxcsr %08x/%08x",c2,c1,w2,w1,x2,x1);diff+=b;}
 if(!diff.empty()){std::fprintf(stderr,"_ftol check mismatch after %llu checks (lifted/host):%s\n",(unsigned long long)checked,diff.c_str());throw std::runtime_error("_ftol host body differs from the lifted body");}
 if((++checked&((1ULL<<20)-1))==0)std::fprintf(stderr,"_ftol check: %llu identical, %llu lifted fallbacks\n",(unsigned long long)checked,(unsigned long long)fallbacks);
 return r;}
inline Body find_uncached(unsigned a){
 if(a==0x78002551&&ftol_fast_on())return &ftol_body;
 auto it=std::lower_bound(mfc_entries.begin(),mfc_entries.end(),a,[](const Entry&e,unsigned v){return e.addr<v;});if(it!=mfc_entries.end()&&it->addr==a)return it->body;
 for(const auto&e:msvcrt_entries)if(e.addr==a)return e.body;return nullptr;}
// The entry tables are fixed at build time, so a direct-mapped cache of recent lookups (hits and misses) returns
// exactly what the search returns.
inline Body find(unsigned a){struct Slot{unsigned addr;bool valid;Body body;};thread_local std::array<Slot,4096>cache{};
 auto&s=cache[(a>>2)&4095];if(s.valid&&s.addr==a)return s.body;const Body b=find_uncached(a);s={a,true,b};return b;}

struct Import{unsigned cell,bound;std::string dll,name;mutable const void*iface_cache{};mutable bool iface_resolved{};mutable const std::string*label[3]{};/* service-log text by prefix (none, MSVCRT>, GAME>), built once */mutable signed char op=-1;/* IDirect3DDevice3 hot-method selector, resolved once from the name */};
struct VSurfaceRec{unsigned guest,width,height,pitch,bpp,caps,mem,bytes,attached,clipper,palette;DDCOLORKEY src_key{},dst_key{};bool has_src_key{},has_dst_key{};unsigned locks{};bool primary{};std::array<unsigned,4>tex_masks{0xf800,0x07e0,0x001f,0};unsigned zbuffer{};
 /* content version, unique across surfaces: advanced by every API path that writes the surface (Unlock,
    Blt/BltFast/colour fills as destination, Texture2::Load, Flip, scene write-back) */
 mutable std::uint64_t version{};mutable mw34::textures::Backing pixels;};
struct VPaletteRec{unsigned guest;PALETTEENTRY entries[256];unsigned flags;};
// DIB sections: the real bitmap's bits are mirrored in guest pages (the game reads bmBits directly);
// GDI drawing calls sync guest->host before and host->guest after.
struct DibRec{HBITMAP bitmap;void*bits;unsigned guest,bytes;};
// Guest heap manager for allocations made while native stages run: a packed first-fit allocator
// (16-byte granularity, coalescing free list) over [50000000, 70000000), mapped in 1 MB chunks.
// HeapAlloc/HeapFree/HeapSize/HeapReAlloc have Win32 semantics (requested size reported, zero-fill
// flag honoured); the allocation lives in guest memory, where the game reads and writes it.
using GuestHeap=mw34::heap_partitions::GuestHeap;
struct SoundLock{unsigned buffer;void*p1;DWORD b1;void*p2;DWORD b2;unsigned g1,g2;};
// Direct3D provider records: per-device state and the commands of the current scene.
unsigned fixture_mesh_node{},fixture_mesh_frame{};
struct D3DCmd{enum Kind{Clear,Draw}kind;unsigned flags,a;float z;std::vector<RECT>rects;std::vector<unsigned char>vertices;unsigned prim{};std::vector<unsigned short>indices;std::shared_ptr<const std::vector<unsigned>>state_snapshot;unsigned texture{};unsigned fixture_node{},fixture_polygon{};int override_texture{-1};int override_normal_texture{-1};std::shared_ptr<const mw34::vkscene::ModelInstance>model{};std::shared_ptr<const mw34::sun::Tl>sun_tl{};std::shared_ptr<const mw34::sun::Tl>sky_view{};bool missile_exhaust{};bool condition_schematic{};unsigned hud_role{};float zoom_anchor{};bool zoom_anchor_known{};};
struct D3DDev{unsigned guest,target,zbuffer,d3d;std::array<unsigned,256>rs{};std::array<std::array<unsigned,32>,8>tss{};std::array<unsigned,8>textures{};std::vector<unsigned>viewports;unsigned current{};bool in_scene{};std::vector<D3DCmd>commands;
 /* draws share one state snapshot until a state setter advances the epoch (the stage-0 texture is per draw) */
 std::uint64_t epoch{1},snap_epoch{};std::shared_ptr<const std::vector<unsigned>>snap;};
struct D3DViewport{unsigned guest;std::array<unsigned char,44>vp{};bool set{};unsigned background{};};
// Loader state that outlives the attach Stage: the import binding, module references, the TLS
// indexes and LocalAlloc blocks MFC42 owns, and the guest-visible last error.
struct Host{
 struct Local{unsigned guest,bytes;HLOCAL native;bool freed;};
 // Global memory: the real HGLOBAL carries allocation, lock and failure semantics; the guest sees a
 // handle token (moveable) or the block address (fixed), and the contents live in guest pages.
 struct Global{unsigned handle,guest,bytes,flags;HGLOBAL native;unsigned locks;bool freed;};
 // A provider DLL mapped by the loader model: image range, entry, writable sections, attach state.
 std::uint64_t raises{},unwinds{},nonlocal_returns{};  // guest SEH dispatch counters
 struct Module{std::string name;unsigned base,end,entry;const std::vector<std::byte>*bytes;std::vector<std::pair<unsigned,unsigned>>writable;bool attached{},thread_calls_disabled{};};
 std::vector<Module>modules;
 // Staged modules a guest LoadLibraryA may map at run time (name, host path, exact bytes and SHA-256).
 struct Loadable{std::string name,path;std::vector<std::byte>bytes;std::string sha;};std::vector<Loadable>loadable;unsigned nested_calls{};
 const Module*module_named(const std::string&n)const{for(const auto&m:modules)if(same_name(m.name,n))return &m;return nullptr;}
 static bool same_name(std::string_view a,std::string_view b){if(a.size()!=b.size())return false;for(std::size_t i=0;i<a.size();++i)if(char(std::toupper(static_cast<unsigned char>(a[i])))!=char(std::toupper(static_cast<unsigned char>(b[i]))))return false;return true;}
 bool all_attached()const{for(const auto&m:modules)if(!m.attached)return false;return !modules.empty();}
 std::map<unsigned,std::string>paths;const std::vector<std::byte>*msvcrt{};unsigned provider_pages{};  // host paths of the guest images actually loaded, by base
 std::vector<com::Object>com_objects;std::map<std::string,unsigned>com_vtables;unsigned com_next=com::arena;com::Provider ddraw;com::SoundProvider dsound;com::InputProvider dinput;
 bool in_com(unsigned a,unsigned n)const{return com_next>com::arena&&a>=com::arena&&std::uint64_t(a)+n<=com_next;}
 // Lookups by guest token use first-match indexes over these append-only vectors (identical to the linear
 // searches they replace): com_objects, imports and vsurfaces only grow.
 std::unordered_map<unsigned,std::size_t>com_index;std::size_t com_indexed{};
 com::Object*com_object(unsigned g){for(;com_indexed<com_objects.size();++com_indexed)com_index.emplace(com_objects[com_indexed].guest,com_indexed);
  const auto it=com_index.find(g);if(it==com_index.end())return nullptr;if(com_objects[it->second].alive)return &com_objects[it->second];
  for(auto&o:com_objects)if(o.alive&&o.guest==g)return &o;return nullptr;}
 // Window hooks the guest installed: the real thread hook (host trampoline) and the guest procedure.
 struct Hook{unsigned guest;int id;unsigned proc;HHOOK native;bool live;};std::vector<Hook>hooks;
 // Guest window classes (real class on the host with the trampoline), per-window guest procedures,
 // and host window procedures the guest holds as tokens.
 struct WndClass{std::string name;ATOM atom;unsigned guest_proc,guest_instance,style,cls_extra,wnd_extra,icon,cursor,brush,menu;};std::vector<WndClass>classes;
 std::map<HWND,unsigned>windows;std::vector<WNDPROC>host_procs;
 // Guest current directory (starts at the game folder, as an install shortcut launches it) and the
 // kernel handles the guest owns (files, find handles).
 std::string cwd;std::vector<unsigned>files;std::set<unsigned>replacement_bank_files;unsigned large_texture_seeks{};mw34::texture_diagnostics::RecentSeeks texture_seeks;unsigned failed_heap_bytes{},failed_heap_owner{},heap_failures{};std::vector<std::pair<unsigned,HANDLE>>finds;/* find handles are host heap pointers: guest tokens */std::vector<unsigned>closed_std;
 std::vector<HINSTANCE>foreign_instances;std::map<unsigned,PAINTSTRUCT>paints;
 // Virtual display state (exclusive level and display mode emulated in the game window).
 struct Display{HWND window{};bool exclusive{};unsigned flags{},width{},height{},bpp{};}display;
 std::vector<VSurfaceRec>vsurfaces;std::vector<VPaletteRec>vpalettes;unsigned vsurface_next{};mw34::surface_pages::FreeList surface_free_pages;unsigned frames{},frame_budget{120},frame_dump{30};
 /* MW34_DRAW_LOG=<file>: per presented frame, the number of DrawPrimitive/DrawIndexedPrimitive calls and an FNV-1a 64
    hash over each call's primitive type, vertex count, the game-computed TL vertex bytes and indices, in call order (an
    address-free fingerprint of the frame's scene for original/native comparisons; host-only, no guest effect). */
 unsigned draw_detail_frame=[]{const char*q=std::getenv("MW34_DRAW_DETAIL");return q&&*q?unsigned(std::stoul(q)):0U;}();  /* MW34_DRAW_DETAIL=<frame>: one line per draw of that frame in the draw log */
 FILE*draw_log=[]{const char*q=std::getenv("MW34_DRAW_LOG");FILE*f=q&&*q?std::fopen(q,"w"):nullptr;if(f)std::setvbuf(f,nullptr,_IOFBF,1<<20);return f;}();std::uint64_t draw_hash=0xcbf29ce484222325ULL;unsigned draw_calls{};
 void draw_fold(const void*p,std::size_t n){const auto*b=static_cast<const unsigned char*>(p);for(std::size_t i=0;i<n;++i){draw_hash^=b[i];draw_hash*=0x100000001b3ULL;}}
/* Block-publication ranges in the guest block arena: blocks published by pages() and their released
   (unmapped) ranges, reused first-fit with coalescing. Ranges published before the hand-off are not
   tracked and are never reused. */
std::map<unsigned,unsigned>pages_live,pages_free;
/* The staged Indeo IV50 codec (the install's Ir50_32.dll, rebased to 0x11000000 as the loader would after
   Mech3Msg takes its preferred base), driven natively through its DriverProc with msvfw32's ICM protocol.
   Guest codec handles are tokens naming the codec's driver id. */
struct CodecState{bool loaded{},enabled{};unsigned base{},driverproc{},serial{};std::map<unsigned,unsigned>open;}codec;
/* Guest heaps created by modules with their own CRT (HeapCreate): blocks come from the guest heap manager. */
std::map<unsigned,std::set<unsigned>>guest_heaps;unsigned guest_heap_serial{};
/* Guest virtual memory (VirtualAlloc/VirtualFree) in [2A000000, 2E000000): reservations at 64 KB granularity,
   committed pages mapped zero-filled read/write; only committed pages are inside the memory contract. */
std::set<unsigned>env_blocks;struct Moveable{unsigned ptr,size,locks;};std::map<unsigned,Moveable>moveable;unsigned moveable_serial{};
/* Page-file-backed (named) file mappings: one block of committed guest pages per section; every view maps that
   block (guest memory cannot alias, so concurrent views share one address). Handles are guest tokens. */
struct Section{std::string name;unsigned size,base,views,handles;};std::vector<Section>sections;std::map<unsigned,size_t>section_handles;unsigned section_serial{};
struct VmState{static constexpr unsigned lo=0x2a000000U,hi=0x2e000000U;std::map<unsigned,unsigned>reserved;std::set<unsigned>committed;}vm;std::uint64_t surface_versions{};
/* Guest threads (CreateThread). Each runs to completion when created, on a full context switch: its own
   State and x87 state, host control word/MXCSR, a fresh 1 MB stack in [2E000000, 30000000), its own TEB
   exception list, fresh TLS values and last error, and DLL_THREAD_ATTACH/DETACH for the attached modules.
   This is a legal schedule for a correctly synchronized program (strict-priority uniprocessor). Anything
   the schedule cannot honour stops typed: a secondary thread that would block, a wait on a mutex another
   guest thread owns, message retrieval or window procedures inside a secondary thread. The thread object
   is a real manual-reset event, signalled at exit. Mutex ownership is tracked per guest thread because all
   guest threads share one host thread (real mutexes would grant recursive ownership silently). */
struct GuestThread{unsigned handle,tid,start,param,exit_code,stack_lo,stack_hi;int priority;bool exited;};std::deque<GuestThread>threads;unsigned thread_tid{};
std::map<unsigned,std::pair<unsigned,unsigned>>mutexes;std::unique_ptr<mw34::vkscene::Renderer>renderer,presenter;  /* scene rendering; window presentation (may be another adapter) */
/* Scripted player input (MW34_INPUT_SCRIPT): stands in for the human at the DirectInput data boundary.
   Device objects, data formats and cooperative levels stay real; only the input data comes from the
   script. Lines: "FRAME mouse DX DY BUTTONS" (relative motion delivered once, at the first read at or after
   that presented frame; buttons persist) and "FRAME key SCANCODE down|up" (one buffered keyboard record). */
struct ScriptEvent{unsigned frame;bool mouse;int dx,dy;unsigned buttons,scan;bool down,timed;};std::vector<ScriptEvent>script;size_t script_mouse_at{},script_key_at{},script_kstate_at{};std::array<unsigned char,256>script_keys{};
/* Opt-in deterministic clock for scripted test runs (MW34_VIRTUAL_CLOCK=<ms per presented frame>, only with
   MW34_INPUT_SCRIPT): every guest time source reads one virtual clock that advances by that step at each presented
   frame, by 1 us per query (so polling loops progress) and by the requested time on Sleep. A script then replays
   identically. Interactive play never uses it. */
std::uint64_t vclock_step_us{},vclock_us{};bool vclock()const{return vclock_step_us!=0;}
std::uint64_t vclock_query(){return ++vclock_us;}  /* monotonic, deterministic */
/* Under the virtual clock, DirectSound play positions are virtual too: real playback runs in real time, and the game's
   audio streaming polls GetCurrentPosition/GetStatus, which made scripted replays branch between runs. Per buffer:
   playing/looping, position at the last Play/SetCurrentPosition/SetFrequency, its virtual time, byte rate, size. */
struct VSound{bool playing{},looping{};std::uint64_t t0{};unsigned pos0{},rate{},size{};};std::map<void*,VSound>vsound;
/* Live guest tick clock (interactive and unclocked runs): GetTickCount, timeGetTime and the message/input timestamps
   read milliseconds since host start plus a one-minute boot offset, from the performance counter (1 ms steps). The
   engine clock (0x575a00) keeps `now` as float32 seconds, so raw Windows uptime of days leaves it tens of ms of
   resolution and jitters every frame step (62.5 ms at 7 days); the original ran on PCs booted hours before.
   MW34_GUEST_CLOCK=uptime restores raw host uptime. */
bool tick_uptime{};std::int64_t tick_qpc0{},tick_qpf{1};DWORD tick_raw0{};static constexpr unsigned tick_base=60000;
void tick_init(){LARGE_INTEGER q{},f{};::QueryPerformanceFrequency(&f);::QueryPerformanceCounter(&q);tick_qpf=f.QuadPart?f.QuadPart:1;tick_qpc0=q.QuadPart;tick_raw0=::GetTickCount();}
unsigned guest_tick()const{if(tick_uptime)return ::GetTickCount();LARGE_INTEGER q{};::QueryPerformanceCounter(&q);return tick_base+unsigned((q.QuadPart-tick_qpc0)*1000/tick_qpf);}
unsigned guest_tick_of(DWORD host_tick)const{return tick_uptime?host_tick:tick_base+(host_tick-tick_raw0);}  /* host GetTickCount-domain stamps */
DWORD host_tick_of(unsigned guest)const{return tick_uptime?guest:tick_raw0+(guest-tick_base);}
unsigned script_buttons{},script_seq{};bool scripted{};
std::map<unsigned,unsigned>di_format;std::uint64_t scene_t0{};unsigned res_rt{},res_zb{};bool res_dirty{},res_protected{};mw34::vkscene::Renderer*sren{};  /* the scene renderer: the presenter's device in lazy mode (direct presentation), else host.renderer */std::uint64_t res_ver_rt{},res_ver_zb{};  /* lazy 3D-target residency (vdd.inc gpu_sync) */  /* host ms of the first rendered 3D scene ("+MS" script events) */POINT vcursor{320,240};std::string frame_dir;std::map<unsigned,unsigned>clippers,d3d_owner;GuestHeap gheap;std::vector<void*>handle_tokens;/* pointer-valued host handles: token 0x3d000000+16k */std::vector<DibRec>dibs;std::vector<SoundLock>sound_locks;std::vector<D3DDev>devices;std::vector<D3DViewport>viewports;std::map<unsigned,std::array<unsigned char,80>>materials;std::map<unsigned,unsigned>ver_blocks;std::map<std::string,unsigned>shared_images;/* LoadIcon/LoadCursor shared handles */std::vector<unsigned>keys;std::map<unsigned,unsigned>tls_shadow;  /* guest-freed TLS indexes: reads 0 after TlsFree, as Windows; host slots untouched */
/* registry: guest key handles and the per-install overlay of the game's writes */
struct VKey{unsigned guest;std::string path;HKEY real;};std::vector<VKey>vkeys;unsigned vkey_serial{};
struct RegOverlay{static constexpr DWORD deleted=0xffffffffU;std::map<std::string,std::map<std::string,std::pair<DWORD,std::vector<BYTE>>>>keys;bool loaded{};std::string file;}reg;std::vector<Import>imports,crt_imports,game_imports;std::deque<std::string>service_labels;std::vector<DWORD>tls;bool attached{};std::vector<Local>locals;std::vector<Global>globals;std::map<std::string,unsigned>loads;unsigned last_error{};
 // One native CD player survives the attach/game Stage hand-offs. It owns only its PCM stream.
 std::unique_ptr<audio::LocalCdAudio>local_cd;
 audio::LocalCdAudio&music(){if(!local_cd)local_cd=std::make_unique<audio::LocalCdAudio>();return *local_cd;}
 Host()=default;Host(const Host&)=delete;Host&operator=(const Host&)=delete;
 // Children before parents: releasing a real IDirectSound frees its buffers, so creation order would leave them dangling.
 ~Host(){mw34::display::exclusive().release();local_cd.reset();static const bool trace=std::getenv("MW34_TRACE_TEARDOWN")!=nullptr;
  for(auto it=com_objects.rbegin();it!=com_objects.rend();++it)if(it->alive&&it->native){if(trace)std::fprintf(stderr,"teardown release %s guest %x owner %x refs %u\n",it->iface->name,it->guest,it->owner,it->refs);for(unsigned r=0;r<it->refs;++r)it->native->Release();}if(ddraw.module)::FreeLibrary(ddraw.module);for(auto k:keys)::RegCloseKey(reinterpret_cast<HKEY>(std::intptr_t(std::int32_t(k))));for(auto&k:vkeys)if(k.real)::RegCloseKey(k.real);for(auto t:tls)::TlsFree(t);for(auto&l:locals)if(!l.freed)::LocalFree(l.native);for(auto&g:globals)if(!g.freed){while(g.locks--)::GlobalUnlock(g.native);::GlobalFree(g.native);}}
 Global*global(unsigned handle){for(auto&g:globals)if(!g.freed&&g.handle==handle)return &g;return nullptr;}
 bool in_global(unsigned a,unsigned n)const{for(const auto&g:globals)if(!g.freed&&a>=g.guest&&std::uint64_t(a)+n<=std::uint64_t(g.guest)+g.bytes)return true;return false;}
 const Import*by_cell(unsigned c)const{for(const auto&i:imports)if(i.cell==c)return &i;return nullptr;}
 mutable std::unordered_map<unsigned,std::size_t>bound_index;mutable std::size_t bound_indexed{};
 const Import*by_bound(unsigned b)const{for(;bound_indexed<imports.size();++bound_indexed)bound_index.emplace(imports[bound_indexed].bound,bound_indexed);
  const auto it=bound_index.find(b);return it==bound_index.end()?nullptr:&imports[it->second];}
 std::unordered_map<unsigned,std::size_t>vsurf_index;std::size_t vsurf_indexed{};
 const Import*by_raw(unsigned r)const{for(const auto&i:crt_imports)if(i.bound==r)return &i;return nullptr;}
 // Game IAT words stay raw (the runtime's import model); each raw word is unique across the game's
 // imports and resolves to its import: cell = the IAT cell, bound = the MFC42/MSVCRT export or 0.
 const Import*by_game_raw(unsigned r)const{for(const auto&i:game_imports)if(i.cell==r)return &i;return nullptr;}
 bool local(unsigned a,unsigned n)const{for(const auto&l:locals)if(!l.freed&&a>=l.guest&&std::uint64_t(a)+n<=std::uint64_t(l.guest)+l.bytes)return true;return false;}
};
inline thread_local Host*host_state{};

namespace pe {
inline unsigned u16(const std::vector<std::byte>&b,std::size_t o){if(o+2>b.size())throw std::runtime_error("PE read outside image");return unsigned(b[o])|unsigned(b[o+1])<<8;}
inline unsigned u32(const std::vector<std::byte>&b,std::size_t o){if(o+4>b.size())throw std::runtime_error("PE read outside image");return u16(b,o)|u16(b,o+2)<<16;}
struct Section{unsigned va,vsize,raw,rawsize,flags;};
inline std::vector<Section>sections(const std::vector<std::byte>&b){const unsigned p=u32(b,0x3c),n=u16(b,p+6),opt=p+24,so=u16(b,p+20);std::vector<Section>s;
 for(unsigned i=0;i<n;++i){const unsigned o=opt+so+40*i;s.push_back({u32(b,o+12),u32(b,o+8),u32(b,o+20),u32(b,o+16),u32(b,o+36)});}return s;}
inline std::size_t offset(const std::vector<std::byte>&b,unsigned rva){for(const auto&s:sections(b))if(rva>=s.va&&rva<s.va+std::max(s.vsize,s.rawsize)&&rva-s.va<s.rawsize)return s.raw+(rva-s.va);throw std::runtime_error("PE RVA outside raw data");}
inline std::string cstr(const std::vector<std::byte>&b,unsigned rva){std::string s;for(auto o=offset(b,rva);o<b.size()&&b[o]!=std::byte{0};++o)s.push_back(char(b[o]));return s;}
inline unsigned dir(const std::vector<std::byte>&b,unsigned i,unsigned*size=nullptr){const unsigned opt=u32(b,0x3c)+24;if(size)*size=u32(b,opt+96+8*i+4);return u32(b,opt+96+8*i);}
// Export RVA by name, or by ordinal when name is "#n"; forwarded exports are refused.
inline unsigned export_rva(const std::vector<std::byte>&b,const std::string&name){unsigned size{};const unsigned d=dir(b,0,&size),o=unsigned(offset(b,d));const unsigned ordbase=u32(b,o+16),nfun=u32(b,o+20),nnames=u32(b,o+24),funs=u32(b,o+28),names=u32(b,o+32),ords=u32(b,o+36);
 unsigned index=~0U;if(name.size()>1&&name[0]=='#'){index=unsigned(std::stoul(name.substr(1)))-ordbase;}else for(unsigned i=0;i<nnames;++i)if(cstr(b,u32(b,offset(b,names)+4*i))==name){index=u16(b,offset(b,ords)+2*i);break;}
 if(index>=nfun)throw std::runtime_error("MSVCRT export absent: "+name);const unsigned rva=u32(b,offset(b,funs)+4*index);if(!rva||(rva>=d&&rva<d+size))throw std::runtime_error("MSVCRT export forwarded or empty: "+name);return rva;}
}
inline bool same(std::string_view a,std::string_view b){return Host::same_name(a,b);}
// Maps a provider DLL at its preferred base with literal headers and sections and binds its imports:
// MSVCRT imports to the staged MSVCRT export addresses, every other import to a service token.
inline void map_module(m4_runtime::Runtime&r,const std::vector<std::byte>&mfc,const char*sha,const char*name,const std::vector<std::byte>&msvcrt,Host&host){
 if(m4::sha256(mfc)!=sha)throw std::runtime_error(std::string("Exact staged provider image ")+name);
 const unsigned opt=pe::u32(mfc,0x3c)+24,base=pe::u32(mfc,opt+28),image_end=base+pe::u32(mfc,opt+56);
 for(const auto&m:host.modules)if(base<m.end&&m.base<image_end)throw std::runtime_error("Provider images overlap");
 if(base<0x10000000||(image_end>msvcrt_base&&base<0x78040000))throw std::runtime_error("Provider preferred base outside the modelled address space");
 const unsigned headers=pe::u32(mfc,opt+60);r.memory().map({base},4096,Permissions::read|Permissions::write);r.memory().write({base},std::span<const std::byte>(mfc).first(headers));r.memory().protect({base},Permissions::read);
 for(const auto&s:pe::sections(mfc)){const unsigned bytes=(std::max(s.vsize,s.rawsize)+4095U)&~4095U;r.memory().map({base+s.va},bytes,Permissions::read|Permissions::write);
  if(s.rawsize)r.memory().write({base+s.va},std::span<const std::byte>(mfc).subspan(s.raw,std::min(s.rawsize,bytes)));}
 // Import binding (the loader writes every IAT cell before any MFC42 code runs).
 unsigned tokens=0;for(const auto&i:host.imports)if(i.bound>=token_base&&i.bound<token_end)++tokens;
 for(unsigned d=unsigned(pe::offset(mfc,pe::dir(mfc,1)));pe::u32(mfc,d+12);d+=20){const std::string dll=pe::cstr(mfc,pe::u32(mfc,d+12));const unsigned lookup=pe::u32(mfc,d),iat=pe::u32(mfc,d+16);
  for(unsigned i=0;;++i){const unsigned v=pe::u32(mfc,pe::offset(mfc,lookup)+4*i);if(!v)break;
   const std::string name=(v&0x80000000U)?"#"+std::to_string(v&0xffff):pe::cstr(mfc,(v&0x7fffffffU)+2);
   const unsigned bound=same(dll,"MSVCRT.dll")?msvcrt_base+pe::export_rva(msvcrt,name):token_base+16*tokens++;if(bound>=token_end&&bound<msvcrt_base)throw std::runtime_error("Import token space");
   host.imports.push_back({base+iat+4*i,bound,dll,name});r.memory().store<unsigned>({base+iat+4*i},bound);}}
 Host::Module mod{name,base,image_end,base+pe::u32(mfc,opt+16),&mfc,{}};
 for(const auto&s:pe::sections(mfc)){r.memory().protect({base+s.va},(s.flags&0x80000000U)?Permissions::read|Permissions::write:(s.flags&0x20000000U)?Permissions::read|Permissions::execute:Permissions::read);
  if(s.flags&0x80000000U)mod.writable.push_back({base+s.va,base+s.va+((std::max(s.vsize,s.rawsize)+4095U)&~4095U)});}
 host.modules.push_back(mod);host.loads[name]=1;}
inline void map_image(m4_runtime::Runtime&r,const std::vector<std::byte>&mfc,const std::vector<std::byte>&msvcrt,Host&host){
 map_module(r,mfc,image_sha,"MFC42.DLL",msvcrt,host);if(host.modules.back().base!=base||host.modules.back().end!=image_end)throw std::runtime_error("MFC42 preferred base and image size");
 // MSVCRT's own IAT is mapped literally (unbound hint/name RVAs); its lifted bodies call through
 // those raw words, which this stage resolves by name.
 host.crt_imports.clear();
 for(unsigned d=unsigned(pe::offset(msvcrt,pe::dir(msvcrt,1)));pe::u32(msvcrt,d+12);d+=20){const std::string dll=pe::cstr(msvcrt,pe::u32(msvcrt,d+12));const unsigned iat=pe::u32(msvcrt,d+16);
  for(unsigned i=0;;++i){const unsigned v=pe::u32(msvcrt,pe::offset(msvcrt,iat)+4*i);if(!v)break;if(v&0x80000000U)throw std::runtime_error("MSVCRT ordinal import not modelled");
   host.crt_imports.push_back({msvcrt_base+iat+4*i,v,dll,pe::cstr(msvcrt,v+2)});}}
 host.loads["MFC42.DLL"]=1;}

// Game import table (the runtime keeps game IAT words raw): each cell with its import and, for MFC42
// (by ordinal) and MSVCRT imports, the export address the loader would bind; other imports are
// services resolved by name. The guest cells must hold their raw words.
inline void bind_game(m4_runtime::Runtime&r,const std::vector<std::byte>&game,const std::vector<std::byte>&mfc,const std::vector<std::byte>&msvcrt,Host&host){
 host.game_imports.clear();
 for(unsigned d=unsigned(pe::offset(game,pe::dir(game,1)));pe::u32(game,d+12);d+=20){const std::string dll=pe::cstr(game,pe::u32(game,d+12));const unsigned lookup=pe::u32(game,d),iat=pe::u32(game,d+16);
  for(unsigned i=0;;++i){const unsigned v=pe::u32(game,pe::offset(game,lookup)+4*i);if(!v)break;const unsigned cell=0x400000+iat+4*i;
   const std::string name=(v&0x80000000U)?"#"+std::to_string(v&0xffff):pe::cstr(game,(v&0x7fffffffU)+2);
   const auto*m=host.module_named(dll);(void)mfc;
   const unsigned bound=m?m->base+pe::export_rva(*m->bytes,name):same(dll,"MSVCRT.dll")?msvcrt_base+pe::export_rva(msvcrt,name):0;
   if(r.memory().load<unsigned>({cell})!=v)throw std::runtime_error("Game IAT cell does not hold its raw import word");host.game_imports.push_back({cell,bound,dll,name});}}}
// Late loader binding for data imports: the loader binds every IAT cell before entry; the runtime keeps
// function words raw (the stage resolves them by name) but code dereferences data-import cells directly,
// so each game import of an MSVCRT/MFC42/MSVCP50 export located outside its module's code sections gets
// its export address written into the cell when the native stage takes over.
inline bool code_rva(const std::vector<std::byte>&b,unsigned rva){for(const auto&s:pe::sections(b))if(rva>=s.va&&rva<s.va+std::max(s.vsize,s.rawsize))return (s.flags&0x20000000U)!=0;return false;}
inline unsigned bind_game_data(m4_runtime::Runtime&r,Host&host){unsigned bound=0;
 for(const auto&i:host.game_imports){if(!i.bound)continue;const std::vector<std::byte>*b=nullptr;unsigned base_=0;
  if(i.bound>=msvcrt_base&&i.bound<0x78040000){b=host.msvcrt;base_=msvcrt_base;}else for(const auto&m:host.modules)if(i.bound>=m.base&&i.bound<m.end){b=m.bytes;base_=m.base;}
  if(!b||code_rva(*b,i.bound-base_))continue;const unsigned page=i.cell&~4095U;r.memory().protect({page},Permissions::read|Permissions::write);r.memory().store<unsigned>({i.cell},i.bound);r.memory().protect({page},Permissions::read);++bound;}
 return bound;}
// The bounded FDIV pack owns selected source ranges, not complete provider
// sections: unused bytes in some read-only pages are deliberately 0xCC. On
// the loader-order play path complete those pages from the admitted PE before
// ordinary CRT/MFC execution can read its strings/tables. Preserve initialized
// writable data and the already-bound import page. The accepted bounded path
// retains its original pack bytes and integrity contract.
inline unsigned map_provider_code(m4_runtime::Runtime&r,const std::vector<std::byte>&msvcrt,bool complete_literals=false){unsigned added=0;
 for(const auto&sec:pe::sections(msvcrt)){const unsigned lo=msvcrt_base+sec.va,hi=msvcrt_base+sec.va+((std::max(sec.vsize,sec.rawsize)+4095U)&~4095U);
  // .text/.rdata always; .data/.rsrc pages the runtime never mapped (never written: literal initial bytes); .reloc is not needed
  if(lo>=0x7803d000)continue;
  for(unsigned page=lo;page<hi;page+=4096){bool mapped=true;try{(void)r.memory().load<unsigned char>({page});}catch(...){mapped=false;}
   if(mapped&&(!complete_literals||(sec.flags&0x80000000U)||page==0x7802e000U))continue;
   std::vector<std::byte>v(4096);const unsigned off=page-msvcrt_base-sec.va;if(off<sec.rawsize)std::memcpy(v.data(),msvcrt.data()+sec.raw+off,std::min(4096U,sec.rawsize-off));
   if(mapped)r.memory().protect({page},Permissions::read|Permissions::write);else r.memory().map({page},4096,Permissions::read|Permissions::write);
   r.memory().write({page},v);if(!(sec.flags&0x80000000U))r.memory().protect({page},(sec.flags&0x20000000U)?Permissions::read|Permissions::execute:Permissions::read);++added;}}
 return added;}
constexpr unsigned external_return(){return m4_runtime::Runtime::external_return;}
struct Stage;
// Nonlocal guest return (an SEH __except block or a C++ catch continuation): the guest returned to the bound return
// word of an outer frame, abandoning the frames above it. Thrown by Stage::returned(); the enter()/call_guest() that
// bound that frame catches it, so the host frames of the abandoned guest calls are released by C++ unwinding.
struct GuestReturn:std::runtime_error{unsigned frame;explicit GuestReturn(unsigned f):std::runtime_error("Nonlocal guest return crossed a host callback boundary"),frame(f){}};
inline thread_local Stage*owner{};
// Memory token for a Stage: the flat guest base (recompiled code adds guest addresses to it), else a dummy.
inline void*stage_token(m4_runtime::Runtime&r,int*dummy){void*b=r.memory().flat_base();return b?b:dummy;}
struct Stage {
 m4_runtime::Runtime&runtime;State&state;hs::HostHeap&heap;Host&host;void*token_ptr;
 unsigned entry_esp{},low{},depth{},reads{},writes{},api_calls{},undefined_count{},max_depth{},bodies{};
 std::array<unsigned,4>saved{};std::array<unsigned,128>returns{};std::array<unsigned,128>returns_sp{};  /* the stack slot holding each bound return word */mw34::ServiceHistory apis;std::uint64_t apis_dropped{};  /* the log keeps the most recent services; the count stays total */
 bool active{},complete{};std::thread::id thread=std::this_thread::get_id();const unsigned long thread_dw=::GetCurrentThreadId();  // the same identity, read inline from the TEB in guard()
 enum class Kind{attach,initterm,call};Kind kind;Host::Module*mod{};
  bool from_entry{};unsigned call_return{};
 Stage(m4_runtime::Runtime&r,hs::HostHeap&h,Host&m,void*t,Kind k=Kind::attach,Host::Module*md=nullptr):runtime(r),state(*reinterpret_cast<State*>(r.remill_state().data())),heap(h),host(m),token_ptr(t),kind(k),mod(md){
  const auto&g=state.gpr;saved={g.rbx.dword,g.rsi.dword,g.rdi.dword,g.rbp.dword};entry_esp=g.rsp.dword;
  if(kind==Kind::initterm&&g.rip.dword==crt_entry){
   // Loader order (MW34_STARTUP=loader, play path): the game's CRT entry itself, called by the process start with
   // the return word on the stack, after native MSVCRT and MFC42 attach; the whole entry then runs in this stage.
   if(load(entry_esp)!=external_return()||!heap.handle||!host.all_attached()||host.game_imports.empty())
    deny("Exact game CRT entry call after native MSVCRT and MFC42 attach required",entry_esp);
   from_entry=true;low=stack_extension;return;}
  if(kind==Kind::initterm){
   // The game's main _initterm CALL through its import thunk, after native MSVCRT and MFC42 attach.
   if(g.rip.dword!=initterm_thunk||load(entry_esp)!=0x5ac480||load(entry_esp+4)!=0x5e0000||load(entry_esp+8)!=0x5e0244||!heap.handle||!host.all_attached()||host.game_imports.empty())
    deny("Exact game main _initterm CALL after native MSVCRT and MFC42 attach required",entry_esp);
   low=stack_extension;return;}
  if(kind==Kind::call){
   // One provider function called in place from a suspended heap Stage (loader order: the MSVCRT FDIV initializer
   // 0x78004254 from _cinit, return word 0x78004232). It completes at its own RET to that word, ESP above it and the
   // callee-saved registers unchanged.
   call_return=load(entry_esp);if(g.rip.dword!=hs::fdiv_writer||call_return!=0x78004232||!heap.handle||!host.msvcrt||host.attached)
    deny("Exact in-place MSVCRT FDIV initializer call from _cinit before MFC42 attach required",entry_esp);
   low=hs::lower_page;return;}
  if(!host.msvcrt)deny("Staged MSVCRT image required for the loader model",0);if(!host.provider_pages){const char*startup=std::getenv("MW34_STARTUP");host.provider_pages=map_provider_code(runtime,*host.msvcrt,startup&&std::string(startup)=="loader");}
  if(!mod||mod->attached)deny("Attach of a mapped, not yet attached provider module required",0);
  if(entry_esp!=hs::attach_esp||g.rip.dword!=mod->entry||load(entry_esp)!=external_return()||load(entry_esp+4)!=mod->base||load(entry_esp+8)!=DLL_PROCESS_ATTACH||!load(entry_esp+12)||!heap.handle||host.imports.empty())
   deny("Exact declared _DllMainCRTStartup(DLL_PROCESS_ATTACH) projection frame on a mapped, bound MFC42 image after native MSVCRT attach required",entry_esp);
  low=hs::lower_page;}
 // A fatal stop ends the process even if teardown of host resources (COM objects, the Vulkan presenter on a window
 // whose messages are no longer pumped) then blocks: the report is written by then, so the process exits with code 3
 // after 15 seconds instead of lingering.
 static void arm_exit_watchdog(){static std::once_flag once;std::call_once(once,[]{std::thread([]{::Sleep(15000);std::fflush(nullptr);::TerminateProcess(::GetCurrentProcess(),3);}).detach();});}
 [[noreturn]]void stop(m4_runtime::FaultReason r,const std::string&w,unsigned a){arm_exit_watchdog();throw m4_runtime::Fault(r,{state.gpr.rip.dword},{a},w);}
 [[noreturn]]void deny(const std::string&w,unsigned a=0){stop(m4_runtime::FaultReason::unresolved_translation,w,a);}
 unsigned load(unsigned a){unsigned v{};if(const auto*fp=guest_fast_pointer(&runtime.memory(),a,4,Permissions::read)){std::memcpy(&v,fp,4);return v;}bool bad{};try{v=runtime.memory().load<unsigned>({a});}catch(...){bad=true;}if(bad)deny("Checked MFC42-stage load fault",a);return v;}
 void store(unsigned a,unsigned v){bool bad{};try{runtime.memory().store<unsigned>({a},v);}catch(...){bad=true;}if(bad)deny("Checked MFC42-stage store fault",a);}
 void guard(void*p)const{if(owner!=this||!active||complete||p!=token_ptr||thread_dw!=__readgsdword(0x48)/*TEB ClientId.UniqueThread*/)const_cast<Stage*>(this)->deny("Exact current active MFC42 Stage token required",state.gpr.rip.dword);}
 // Memory contract: own stack frame, the mapped MFC42 image (writes only to .data), MSVCRT .data
 // (reads only), real heap/local blocks, and the TEB exception-list word for SEH frame links.
 // Pages the native MSVCRT attach/command-line carry published for the process: provider strings,
 // environment copy, wide command line (0x32000000..0x32200FFF) and the GetCommandLineA page 0x33000000.
 static bool provider_published(unsigned a,unsigned n){const auto e=std::uint64_t(a)+n;return (a>=0x32000000&&e<=0x32201000)||(a>=0x33000000&&e<=0x33001000);}
 // Virtual surface pixel memory (the game writes it through Lock pointers and its own renderer).
 bool in_surfaces(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;for(const auto&v:host.vsurfaces)if(v.mem&&a>=v.mem&&e<=std::uint64_t(v.mem)+v.bytes)return true;return false;}
 bool frame(unsigned a,unsigned n,bool write)const{if(kind==Kind::initterm)return a>=low&&std::uint64_t(a)+n<=game_stack_top;return a>=low&&std::uint64_t(a)+n<=(write?entry_esp:entry_esp+16);}
 bool in_module(unsigned a,unsigned n,bool write)const{const auto e=std::uint64_t(a)+n;for(const auto&m:host.modules){if(!write){if(a>=m.base&&e<=m.end)return true;}else for(const auto&[lo,hi]:m.writable)if(a>=lo&&e<=hi)return true;}return false;}
 bool in_thread_stack(unsigned a,unsigned n)const{for(const auto&t:host.threads)if(!t.exited&&a>=t.stack_lo&&std::uint64_t(a)+n<=t.stack_hi)return true;return false;}
 // Exact fast paths: each is a subset of the full predicate below, gated by the arena the predicate's
 // ranges live in (pages() blocks, virtual surfaces, guest thread stacks); a miss falls back to the full check.
 bool vm_committed(unsigned a,unsigned n)const{if(a<Host::VmState::lo||std::uint64_t(a)+n>Host::VmState::hi||!n)return false;for(unsigned p=a&~4095U;p<a+n;p+=4096U)if(!host.vm.committed.count(p))return false;return true;}
 bool fast_access(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;if(host.gheap.contains(a,n)||frame(a,n,false))return true;if(a>=Host::VmState::lo&&e<=Host::VmState::hi)return vm_committed(a,n);
  if(a>=hs::arena&&e<=hs::arena_end)return heap.block(a,n)||host.local(a,n)||host.in_global(a,n)||in_dib(a,n)||in_sound(a,n);
  if(a>=vsurface_arena&&e<=vsurface_arena_end)return in_surfaces(a,n);if(a>=0x2e000000U&&e<=0x30000000U)return in_thread_stack(a,n);return false;}
 bool readable(unsigned a,unsigned n)const{if(fast_access(a,n)||(kind==Kind::initterm&&a>=0x400000&&std::uint64_t(a)+n<=game_end))return true;const auto e=std::uint64_t(a)+n;return frame(a,n,false)||in_thread_stack(a,n)||in_module(a,n,false)||(a>=msvcrt_base+0x1000&&e<=msvcrt_data_end)||(kind==Kind::initterm&&a>=0x400000&&e<=game_end)||heap.block(a,n)||host.local(a,n)||host.in_global(a,n)||host.in_com(a,n)||host.gheap.contains(a,n)||provider_published(a,n)||in_surfaces(a,n)||in_dib(a,n)||in_sound(a,n)||(a==runtime.fs_base().value&&n==4)||(a==runtime.fs_base().value+0x18&&n==4);}
 bool writable(unsigned a,unsigned n)const{if((host.gheap.contains(a,n)||(fast_access(a,n)&&!frame(a,n,false)))||frame(a,n,true))return true;
  {const auto e=std::uint64_t(a)+n;if((kind==Kind::initterm&&a>=game_data&&e<=game_data_end)||(a>=msvcrt_data&&e<=msvcrt_data_end))return true;}const auto e=std::uint64_t(a)+n;return frame(a,n,true)||in_thread_stack(a,n)||host.gheap.contains(a,n)||in_module(a,n,true)||in_surfaces(a,n)||in_dib(a,n)||in_sound(a,n)||(a>=msvcrt_data&&e<=msvcrt_data_end)||(kind==Kind::initterm&&a>=game_data&&e<=game_data_end)||heap.block(a,n)||host.local(a,n)||host.in_global(a,n)||(a==runtime.fs_base().value&&n==4);}
 // Inline subsets of readable()/writable() (each disjunct appears in the full predicate) for the classes that carry
 // nearly all mission accesses: the stage's own stack frame, the game image (.data for writes) and the guest heap.
 bool read_fast(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;return frame(a,n,false)||(kind==Kind::initterm&&a>=0x400000&&e<=game_end)||host.gheap.contains(a,n);}
 bool write_fast(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;return frame(a,n,true)||(kind==Kind::initterm&&a>=game_data&&e<=game_data_end)||host.gheap.contains(a,n);}
 template<class T>T read(unsigned a,void*p){guard(p);if(!read_fast(a,sizeof(T))&&!readable(a,sizeof(T)))deny("MFC42-stage read outside its memory contract",a);if(const auto*fp=guest_fast_pointer(&runtime.memory(),a,sizeof(T),Permissions::read)){T v;std::memcpy(&v,fp,sizeof(T));++reads;return v;}
  T v{};bool bad{};try{if(((a&4095U)+sizeof(T))>4096U){unsigned char b[sizeof(T)];for(unsigned i=0;i<sizeof(T);++i)b[i]=runtime.memory().load<unsigned char>({a+i});std::memcpy(&v,b,sizeof(T));}else v=runtime.memory().load<T>({a});}catch(...){bad=true;}if(bad)deny("Checked MFC42-stage read",a);++reads;return v;}
 template<class T>void write(unsigned a,T v,void*p){guard(p);if(!write_fast(a,sizeof(T))&&!writable(a,sizeof(T)))deny("MFC42-stage write outside its memory contract",a);if(auto*fp=guest_fast_pointer(&runtime.memory(),a,sizeof(T),Permissions::write)){std::memcpy(fp,&v,sizeof(T));++writes;return;}
  std::string why;try{if(((a&4095U)+sizeof(T))>4096U){unsigned char b[sizeof(T)];std::memcpy(b,&v,sizeof(T));for(unsigned i=0;i<sizeof(T);++i)runtime.memory().store<unsigned char>({a+i},b[i]);}else runtime.memory().store<T>({a},v);}catch(const std::exception&x){why=x.what();if(why.empty())why="?";}catch(...){why="non-standard exception";}if(!why.empty())deny("Checked MFC42-stage write ("+why+", esp "+std::to_string(state.gpr.rsp.dword)+")",a);++writes;}
 unsigned root_index{},root_addr{};bool initterm_returned{};
 // HUD command capture (MW34_HUD_LOG=<file>): the game's software HUD primitives (docs/hud-vulkan-integration-handoff.md)
 // are recorded with their arguments at entry; the original bodies still run (dual mode, output unchanged).
 struct HudCmd{unsigned fn,ecx,edx,a0,a1,a2,a3;};std::vector<HudCmd>hud_frame;
 FILE*hud_log=[]{const char*q=std::getenv("MW34_HUD_LOG");FILE*f=q&&*q?std::fopen(q,"w"):nullptr;if(f)std::setvbuf(f,nullptr,_IOFBF,1<<20);return f;}();
 unsigned hud_detail_frame=[]{const char*q=std::getenv("MW34_HUD_DETAIL");return q&&*q?unsigned(std::stoul(q)):0U;}();
 void hud_capture(unsigned target){if(target!=0x55b3c0&&target!=0x563b80&&target!=0x5630c0&&target!=0x564080)return;const auto&g=state.gpr;const unsigned sp=g.rsp.dword;
  hud_frame.push_back({target,g.rcx.dword,g.rdx.dword,load(sp+4),load(sp+8),load(sp+12),load(sp+16)});}
 void hud_present(){if(!hud_log)return;unsigned n[4]{};for(const auto&c:hud_frame)++n[c.fn==0x55b3c0?0:c.fn==0x563b80?1:c.fn==0x5630c0?2:3];
  std::fprintf(hud_log,"%u blit %u line %u circle %u span %u\n",host.frames,n[0],n[1],n[2],n[3]);
  if(hud_detail_frame==host.frames)for(const auto&c:hud_frame){std::fprintf(hud_log,"  %06x ecx %08x edx %08x a %08x %08x %08x %08x",c.fn,c.ecx,c.edx,c.a0,c.a1,c.a2,c.a3);
   if(c.fn==0x55b3c0&&readable(c.ecx,0x34)){const unsigned w=load(c.ecx+4)&0xffff,h=load(c.ecx+6)&0xffff;std::fprintf(hud_log," image %ux%u flags %02x pixels %08x surf %08x",w,h,load(c.ecx+8)>>8&0xff,load(c.ecx+0x10),load(c.ecx+0x30));
    if(c.a2&&readable(c.a2,16))std::fprintf(hud_log," src %d,%d-%d,%d",int(load(c.a2)),int(load(c.a2+4)),int(load(c.a2+8)),int(load(c.a2+12)));}
   std::fprintf(hud_log,"\n");}
  hud_frame.clear();}
std::string pose_name(unsigned address,unsigned limit){std::string result;
 if(!address)return result;
 for(unsigned i=0;i<limit;++i){if(!readable(address+i,1))return std::string();unsigned char c{};try{c=runtime.memory().load<unsigned char>({address+i});}catch(...){return std::string();}
  if(!c)return result;if(c<32||c>126||c=='"'||c=='\\')return std::string();result.push_back(char(c));}return std::string();
}

 #include "widescreen_stage.inc"
 #include "frontend_stage.inc"
 #include "draw_distance_stage.inc"
 #include "turret_aim_stage.inc"
 #include "photo_replay_stage.inc"
 #include "platform_trace_stage.inc"
 #include "hud_deferred_stage.inc"
 #include "zoom_alignment_stage.inc"
 #include "target_marker_stage.inc"
 mw34::GeometryProfile geometry_profile;
 bool body_dispatch_warmed{};
 #include "mesh_override_stage.inc"
 #include "additional_skins_stage.inc"
 #include "mechlab_skins_stage.inc"
 #include "additional_chassis_stage.inc"
 #include "chassis_sockets_stage.inc"
 #include "mech_headlights_stage.inc"
 #include "chassis_selection_stage.inc"
 #include "remaster_banks.inc"
 #include "cinematic_paths.inc"
 // Preserve current enter()/SEH dispatch and restore the optional model scope
 // on every host exception, including a guest non-local return.
 #include "world_direct_stage.inc"
 #include "sun_lighting_stage.inc"
 #include "surface_normals_stage.inc"
bool render_reuse_enabled(){
 static const bool enabled=[] {
  const char* value=std::getenv("MW34_RENDER_STATE_REUSE");
  if(!value||!*value||!std::strcmp(value,"0"))return false;
  if(!std::strcmp(value,"1"))return true;
  throw std::runtime_error("MW34_RENDER_STATE_REUSE must be 0 or 1");
 }();return enabled;
}
mw34::submission::ExactSharedValue<mw34::sun::Tl> sun_tl_values,sky_view_values;
#include "sun_tl_capture_stage.inc"
#include "effect_lighting_stage.inc"
#include "missile_exhaust_stage.inc"
 #include "divergence_trace_stage.inc"
 void*lighting_body(State*s,unsigned target,void*p,Body body){
  if(target==0x520b00&&sun_view_capture_enabled()){
   const unsigned source=state.gpr.rcx.dword;
   mw34::sun::CameraBinding::Words words{};
   {SunCaptureFp preserve;words=sun_view_words(source);sun_view_binding.valid=false;}
   void*r=remaster_body_inner(s,target,p,body);
   {SunCaptureFp preserve;sun_view_binding.capture(source,words,sun_view_words(0x73fc00),sun_view_words(0x73fbc0));}
   return r;
  }
  if(target==0x40a210){static const double hz=[]{const char*p=std::getenv("MW34_MENU_SCROLL_HZ");const double v=p?std::atof(p):0.0;return v>0&&v<=1000?v:0.0;}();
   const unsigned w=state.gpr.rcx.dword;
   if(hz>0&&w&&readable(w,0x140)&&(load(w+0x138)&0xff)){
    struct Clock{LARGE_INTEGER last{};double carry{};};static std::map<unsigned,Clock> clocks;static LARGE_INTEGER freq{};
    if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
    LARGE_INTEGER now{};::QueryPerformanceCounter(&now);auto& c=clocks[w];mw34::vkscene::HostFpEnvironment fp;
    const double elapsed=c.last.QuadPart?std::min(0.25,double(now.QuadPart-c.last.QuadPart)/double(freq.QuadPart)):1.0/hz;
    c.last=now;const double steps=c.carry+elapsed*hz;unsigned n=unsigned(steps);c.carry=steps-n;
    const int dx=int(load(w+0xbc)),dy=int(load(w+0xc0));
    const unsigned image=load(w+0x3c);const int iw=image&&readable(image,8)?int(short(load(image+4)&0xffff)):0,ih=image&&readable(image,8)?int(short(load(image+4)>>16)):0;
    while(n>1&&((iw>0&&std::abs(dx)*int(n)>=iw)||(ih>0&&std::abs(dy)*int(n)>=ih)))--n;
    store(w+0xbc,unsigned(dx*int(n)));store(w+0xc0,unsigned(dy*int(n)));
    try{void*r=remaster_body_inner(s,target,p,body);store(w+0xbc,unsigned(dx));store(w+0xc0,unsigned(dy));return r;}
    catch(...){store(w+0xbc,unsigned(dx));store(w+0xc0,unsigned(dy));throw;}
   }}
  if(target==0x42fb30){static const double hz=[]{const char*p=std::getenv("MW34_MENU_SCROLL_HZ");const double v=p?std::atof(p):0.0;return v>0&&v<=1000?v:0.0;}();
   const unsigned w=state.gpr.rcx.dword;
   if(hz>0&&w&&readable(w,0xc0)){
    struct Clock{LARGE_INTEGER last{};double carry{};};static std::map<unsigned,Clock> clocks;static LARGE_INTEGER freq{};
    const unsigned bits=load(w+0xbc);float speed;std::memcpy(&speed,&bits,4);float due=0;
    {mw34::vkscene::HostFpEnvironment fp;
     if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
     LARGE_INTEGER now{};::QueryPerformanceCounter(&now);auto& c=clocks[w];
     const double elapsed=c.last.QuadPart?std::min(0.25,double(now.QuadPart-c.last.QuadPart)/double(freq.QuadPart)):1.0/hz;
     c.last=now;
     if(std::isfinite(speed)&&std::abs(speed)<1000){const double px=c.carry+double(speed)*elapsed*hz;const double whole=std::trunc(px);c.carry=px-whole;due=float(whole);}else due=speed;}
    unsigned due_bits;std::memcpy(&due_bits,&due,4);store(w+0xbc,due_bits);
    try{void*r=remaster_body_inner(s,target,p,body);store(w+0xbc,bits);return r;}catch(...){store(w+0xbc,bits);throw;}
   }}

  if(target==0x558dd0&&menu_hd_image().ok&&wide_world_frame!=host.frames){const size_t index=menu_dl.size();menu_dl_wave_record();try{void*r=remaster_body_inner(s,target,p,body);menu_dl_wave_finish(index);return r;}catch(...){menu_dl_bad=true;throw;}}
  if(target==0x55b3c0&&menu_hd_image().ok&&wide_world_frame!=host.frames)menu_dl_record();
  if(target==0x40a210){menu_bg_widget=state.gpr.rcx.dword;menu_bg_frame=host.frames;}
  if(world_enabled()&&target==0x4f6720){++world_cell_depth;try{void*r=remaster_body_inner(s,target,p,body);--world_cell_depth;return r;}catch(...){--world_cell_depth;throw;}}
  if(world_enabled()&&target==0x53f2e0){auto previous=world_scope;
   const auto previous_fixture_node=fixture_mesh_node,previous_fixture_frame=fixture_mesh_frame;
   fixture_mesh_node=state.gpr.rcx.dword;fixture_mesh_frame=state.gpr.rsp.dword-4;
   world_scope=world_begin(fixture_mesh_node,fixture_mesh_frame);
   try{void*r=remaster_body_inner(s,target,p,body);world_scope=std::move(previous);fixture_mesh_node=previous_fixture_node;fixture_mesh_frame=previous_fixture_frame;return r;}
   catch(...){world_scope=std::move(previous);fixture_mesh_node=previous_fixture_node;fixture_mesh_frame=previous_fixture_frame;throw;}}
  return remaster_body_inner(s,target,p,body);
 }
 void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};
  if(target==0x4eaea0)chassis_retire_root(state.gpr.rcx.dword);
  if(target==0x408b40||target==0x48aac0||target==0x48a930||target==0x44ffc0||target==0x449220)return chassis_selection_body(s,target,p,body);
  if(chassis_target(target))return chassis_body(s,target,p,body);
  if(target==0x4b36e0)return chassis_socket_body(s,target,p,body);
  if(target==0x44cf70||target==0x44b1c0||target==0x44e6a0)return mechlab_skin_body(s,target,p,body);
  if(target==0x448a20)mechlab_skin_closed();
  if(missile_enabled()){
   if(target==0x585010)return missile_create_body(s,target,p,body);
   if(target==0x584f40||target==0x586600)missile_retire(state.gpr.rdx.dword);
   if(target==0x4eaea0)missile_retire_root(state.gpr.rcx.dword);
  }
  if(platform_trace_enabled()&&(target==0x4a76b0||target==0x4a5c60||target==0x4f8b80||target==0x4f9d60||target==0x4d7330||target==0x4d6d00||target==0x4a7ab0||target==0x4b4a40||target==0x4a71c0||target==0x4a7620||target==0x4f5910||target==0x4f4ab0||target==0x541760||target==0x53d750||target==0x4eb170||target==0x4fc300))return platform_body(s,target,p,body);
  if(target==0x448960||target==0x448a20)return frontend_body(s,target,p,body);
  if(target==0x4f73f0&&override_enabled()&&override_status_preview()&&!override_state().preview_active){override_state().preview_active=true;override_preview_start();try{result=remaster_body_inner(s,target,p,body);override_preview_finish();override_state().preview_active=false;return result;}catch(...){override_state().preview_active=false;throw;}}
  if(target==0x4f3a70)distance_restore(state.gpr.rcx.dword);
  if(target==0x4f4170||target==0x4f41b0)distance_prepare(state.gpr.rcx.dword);
  if((target==0x4b52c0||target==0x4f6dc0||target==0x4f7030||target==0x4f73f0)&&(distance_requested()>800||distance_fog_requested()||distance_log())){if(target==0x4b52c0||target==0x4f6dc0||target==0x4f7030)return photo_replay_body(s,target,p,[&]{return distance_camera_body(s,target,p,body);});return distance_camera_body(s,target,p,body);}
  if(target==0x49bfd0&&distance_requested()>800){const unsigned sp=state.gpr.rsp.dword;
   if(readable(sp,20)&&load(sp+4)==0x200&&(load(sp+16)==0x5ea600||load(sp+16)==0x5ea628))deny("Extended draw distance exceeds original terrain tiler capacity",target);}
  if((target==0x4f5c80||target==0x4f61b0)&&distance_log()){
   const unsigned camera=load(state.gpr.rsp.dword+4);result=body(s,target,p);distance_tiles(camera);return result;}
  if(target==0x440b00&&(distance_requested()>800||distance_fog_requested()))return distance_marker_body(s,target,p,body);
  if(target==0x526e10&&(distance_requested()>800||distance_fog_requested()||distance_log()))distance_fog_bound(state.gpr.rcx.dword);
  if(target==0x555a70&&distance_log())distance_fog_consumed();

  if(wide_on()&&(target==0x440b00||target==0x441490||target==0x440510||
     (target_marker_update_owner&&(target==0x53cf10||target==0x40da30))))return target_marker_body(s,target,p,body);
  if(target==0x442f50&&(wide_on()||distance_requested()>800||distance_fog_requested()))return zoom_scene_body(s,target,p,body);
  if(wide_on()&&target==0x57bf80)return hud_panel_body(s,target,p,body);
  if(wide_on()&&target==0x57e110){
   try{result=body(s,target,p);}catch(...){hud_deferred_panels.clear();throw;}
   hud_deferred_panels.clear();return result;
  }
  if(target==0x558c10&&hud_gpu_active)return hud_noise_body(s,target,p,body);
  if(target==0x563440&&hud_gpu_active)return hud_jitter_body(s,target,p,body);
  if(target==0x562970&&hud_gpu_active)return hud_jitter_body(s,target,p,body,true);
  if(target==0x43dd00&&wide_on()){const unsigned radar=state.gpr.rcx.dword;if(!readable(radar+0x5a,2))deny("Widescreen radar mode outside memory contract",radar);wide_radar_mode=load(radar+0x5a)&0xffff;if(wide_radar_mode>1)deny("Unknown original radar mode",wide_radar_mode);}
  // 4F4170's original tail JMP fuses the 4F41B0 rebuild into that lifted body.
  if((target==0x4f3b90||target==0x4f3d90||target==0x4f4170||target==0x4f41b0)&&wide_on()){if(target==0x4f4170||target==0x4f41b0)wide_prepare(state.gpr.rcx.dword);else wide_restore(state.gpr.rcx.dword);}
  if(target==0x53f2e0&&platform_trace_enabled())platform_visibility("mesh-producer",target,state.gpr.rcx.dword,0);
  if(target==0x53f2e0&&(override_enabled()||photo_replay_detached_cam()||missile_enabled())){const auto previous=override_begin(state.gpr.rcx.dword);missile_begin(state.gpr.rcx.dword);
   try{result=body(s,target,p);}catch(...){missile_end();override_restore(previous);throw;}missile_end();override_restore(previous);
  }else result=body(s,target,p);if(target==0x51fb30){override_emit();missile_emit();}return result;}
 void*controller_next_body(State*s,unsigned target,void*p,Body body){
  return photo_replay_body(s,target,p,[&]{return turret_aim_body(s,target,p,[&]{return lighting_body(s,target,p,body);});});
 }
 #include "controller_stage.inc"
 void*remaster_body(State*s,unsigned target,void*p,Body body){
  static const bool fast=[]{const char*p=std::getenv("MW34_BODY_DISPATCH");
   if(!p||!*p||!std::strcmp(p,"0"))return false;
   if(!std::strcmp(p,"1"))return true;
   throw std::runtime_error("MW34_BODY_DISPATCH must be 0 or 1");}();
  // The first ordinary call still traverses every adapter, retaining lazy
  // launch-setting initialization and its original validation failures.
  if(fast&&!mw34::body_dispatch::handled(target)){
   if(body_dispatch_warmed)return body(s,target,p);
   body_dispatch_warmed=true;
  }

  return headlight_body(s,target,p,[&]{return controller_body(s,target,p,[&]{return controller_next_body(s,target,p,body);});});
 }
 void*enter(State*s,unsigned target,void*p,Body body){if(depth>=returns.size())deny("MFC42-stage call depth bound",target);if(hud_log)hud_capture(target);{void*r{};if(hud_intercept(target,p,r))return r;}
  if(kind==Kind::initterm&&depth==0)for(unsigned i=0;i<145;++i)if(load(0x5e0000+4*i)==target&&load(state.gpr.rsp.dword)>=msvcrt_base){root_index=i;root_addr=target;break;}{const unsigned sp=state.gpr.rsp.dword,w=load(sp);
   /* A direct tail JMP to a function entry is lifted as a tail call through the CALL router: it enters with
      ESP at the slot of the active return word (a real CALL always enters strictly deeper) and binds nothing new. */
   if(!(depth&&sp==returns_sp[depth-1]&&w==returns[depth-1])){returns_sp[depth]=sp;returns[depth++]=w;}else{max_depth=std::max(max_depth,depth);++bodies;return remaster_body(s,target,p,body);}}
   max_depth=std::max(max_depth,depth);++bodies;const unsigned mine=depth-1;
   if(seh_test&&(in_wndproc||seh_test_any)&&target>=0x401000&&target<0x5bb000&&!--seh_test)try{seh_test_throw(target);}catch(const GuestReturn&r){if(r.frame!=mine)throw;depth=mine;return p;}
   try{return remaster_body(s,target,p,body);}catch(const GuestReturn&r){if(r.frame!=mine)throw;depth=mine;return p;}}
 void*called(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact MFC42-stage CALL State",target);const Body b=find(target);if(!b)deny("Direct CALL target outside the lifted MFC42 closure",target);return enter(s,target,p,b);}
 void*function_call(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact MFC42-stage indirect CALL State",target);
  if(const Body b=find(target))return enter(s,target,p,b);
  if(const auto*i=game_import(target)){if(!i->bound)return api(s,target,p);const Body b=find(i->bound);if(!b)deny("Game import has no lifted provider body: "+i->dll+"!"+i->name,i->bound);state.gpr.rip.dword=i->bound;return enter(s,i->bound,p,b);}
  if((target>=token_base&&target<token_end)||host.by_raw(target))return api(s,target,p);
  if(const auto*i=host.by_bound(target))deny("Bound import has no lifted provider body yet: "+i->dll+"!"+i->name,target);
  deny("Indirect CALL target outside the lifted closure, bound imports and service tokens",target);}
 void*returned(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact MFC42-stage RET State",target);
  if(depth){if(target!=returns[depth-1]){
     for(unsigned j=depth-1;j-->0;)if(returns[j]==target){const unsigned sp=state.gpr.rsp.dword,at=returns_sp[j]+4;if(sp>=at&&sp<=at+256&&!((sp-at)&3)){++host.nonlocal_returns;if(const char*q=std::getenv("MW34_SEH_LOG");q&&*q)std::fprintf(stderr,"nonlocal return to 0x%08x: frame %u of %u (raises %llu unwinds %llu)\n",target,j,depth,(unsigned long long)host.raises,(unsigned long long)host.unwinds);throw GuestReturn(j);}break;}
     std::string w;for(unsigned i=depth>6?depth-6:0;i<depth;++i){char h[12];std::snprintf(h,sizeof h," %x",returns[i]);w+=h;}deny("MFC42-stage RET to a non-source return address (bound return words:"+w+"; thread "+std::to_string(host.thread_tid)+")",target);}--depth;return p;}
  const auto&g=state.gpr;
  if(kind==Kind::initterm&&target==entry_continuation&&g.rsp.dword==entry_esp+4&&g.rbx.dword==saved[0]&&g.rsi.dword==saved[1]&&g.rdi.dword==saved[2]&&g.rbp.dword==saved[3]&&!initterm_returned){initterm_returned=true;return p;}
  if(kind==Kind::initterm&&initterm_returned&&target==external_return()){complete=true;return p;}  // the entry itself returned to its caller
  if(kind==Kind::call&&target==call_return&&g.rsp.dword==entry_esp+4&&g.rbx.dword==saved[0]&&g.rsi.dword==saved[1]&&g.rdi.dword==saved[2]&&g.rbp.dword==saved[3]){complete=true;return p;}
  if(kind==Kind::attach&&target==external_return()&&g.rsp.dword==entry_esp+16&&g.rax.dword==1&&g.rbx.dword==saved[0]&&g.rsi.dword==saved[1]&&g.rdi.dword==saved[2]&&g.rbp.dword==saved[3]){complete=true;return p;}
  deny("MFC42-stage outermost RET outside the DllMain contract (TRUE, RET 0Ch, callee-saved registers)",target);}
 void*missing(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact MFC42-stage continuation State",target);const Body b=find(target);if(!b)deny("Continuation outside the lifted MFC42 closure",target);++bodies;return b(s,target,p);}
 void*jumped(State*s,unsigned target,void*p){guard(p);
  if(const Body b=find(target)){state.gpr.rip.dword=target;++bodies;if(chassis_target(target))return remaster_body(s,target,p,b);return b(s,target,p);}
  if(const auto*i=game_import(target);i&&i->bound){const Body b=find(i->bound);if(!b)deny("Game import thunk has no lifted provider body: "+i->dll+"!"+i->name,i->bound);state.gpr.rip.dword=i->bound;++bodies;return b(s,i->bound,p);}
  if((target>=token_base&&target<token_end)||host.by_raw(target)||game_import(target)){const unsigned ret=load(state.gpr.rsp.dword);void*r=api(s,target,p);if(depth&&returns[depth-1]==ret)--depth;else deny("Import tail JMP must return to the active caller",target);return r;}
  if(const auto*i=host.by_bound(target))deny("Bound import tail JMP has no lifted provider body yet: "+i->dll+"!"+i->name,target);
  deny("Indirect JMP target outside the lifted closure, bound imports and service tokens",target);}
 // INT3/INT n/INTO/BOUND traps: reached only on a path the original would take into exception dispatch
// (compilers also emit INT3 as padding between functions, which lifted spans may contain but never run).
void*trap(State*s,unsigned pc,void*p){guard(p);char h[64];std::snprintf(h,sizeof h,"Trap instruction reached (hyper call %u)",unsigned(s?reinterpret_cast<const std::uint32_t*>(s)[2]:0));
 stop(m4_runtime::FaultReason::unimplemented_seh_dispatch,std::string(h)+"; exception dispatch is not modelled",pc);}
void*error(State*,unsigned pc,void*p){guard(p);stop(m4_runtime::FaultReason::unimplemented_seh_dispatch,"Divide error (#DE) in lifted x86 source; hardware SEH dispatch is not modelled",pc);}
 bool in_atomic{};unsigned atomics{};
 void*atomic(void*p,bool begin){guard(p);if(in_atomic==begin)deny("Unbalanced LOCK atomic markers");in_atomic=begin;if(begin)++atomics;return p;}
 unsigned char undefined(){if(owner!=this||!active)deny("MFC42-stage undefined flag outside Stage");++undefined_count;return 0;}
 // RDTSC for guest code. Under the virtual clock it is a virtual 3 GHz counter (virtual microseconds x 3000), so the
 // game's start-up CPU-speed measurement (0x5988c0: RDTSC timed against QueryPerformanceCounter) always yields the
 // same value; with the real counter it varied between runs and changed later frames. Interactive play: real RDTSC.
 unsigned long long guest_tsc()const{return host.vclock()?host.vclock_us*3000ULL:__rdtsc();}
 // Real host services for MFC42's non-MSVCRT imports, implemented as reached.
 struct LastError{Host&h;DWORD saved=GetLastError();explicit LastError(Host&x):h(x){SetLastError(0);}~LastError(){h.last_error=GetLastError();SetLastError(saved);}};
 // Loader model for module names: the guest modules by base; system DLLs by a per-module guest token
 // (their code is never mapped; GetProcAddress on them yields service tokens resolved by name).
 // DDRAW/DSOUND/DINPUT and the other platform DLLs are services of this project (DirectDraw -> Vulkan);
 // the dgVoodoo DDraw.dll in the game folder is not part of the original game and is bypassed.
 static const std::vector<std::pair<std::string,unsigned>>&system_modules(){static const std::vector<std::pair<std::string,unsigned>>m{{"KERNEL32.DLL",0x35010000},{"USER32.DLL",0x35020000},{"GDI32.DLL",0x35030000},{"ADVAPI32.DLL",0x35040000},{"COMDLG32.DLL",0x35050000},{"WINSPOOL.DRV",0x35060000},{"SHELL32.DLL",0x35070000},{"COMCTL32.DLL",0x35080000},{"OLE32.DLL",0x35090000},{"OLEAUT32.DLL",0x350a0000},{"DDRAW.DLL",0x350b0000},{"DSOUND.DLL",0x350c0000},{"DINPUT.DLL",0x350d0000},{"WINMM.DLL",0x350e0000},{"DPLAYX.DLL",0x350f0000},{"VERSION.DLL",0x35100000},{"AVIFIL32.DLL",0x35110000},{"MSVFW32.DLL",0x35120000},{"D3DIM.DLL",0x35130000}};return m;}
 unsigned module(std::string m){std::transform(m.begin(),m.end(),m.begin(),[](unsigned char c){return char(std::toupper(c));});if(m.find('.')==std::string::npos)m+=".DLL";
  if(m=="MSVCRT.DLL")return msvcrt_base;if(const auto*x=host.module_named(m))return x->base;for(const auto&[k,v]:system_modules())if(k==m)return v;return 0;}
 // Whether the real loader would find a file for this name: an explicit path as given, a bare name in
 // the game directory or the system directories.
 bool present(const std::string&m){namespace fs=std::filesystem;std::error_code ec;if(m.find_first_of("\\/:")!=std::string::npos){std::string q=m;char sys[MAX_PATH]{},wow[MAX_PATH]{};const UINT k=::GetSystemDirectoryA(sys,MAX_PATH);
   // A 32-bit guest sees the system directory through WOW64 file-system redirection.
   if(k&&::GetSystemWow64DirectoryA(wow,MAX_PATH)&&q.size()>k&&same(q.substr(0,k),sys)&&(q[k]=='\\'||q[k]=='/'))q=std::string(wow)+q.substr(k);return fs::exists(fs::path(q),ec);}
  std::vector<fs::path>dirs;if(host.paths.count(0x400000))dirs.push_back(fs::path(host.paths.at(0x400000)).parent_path());char sys[MAX_PATH]{};if(::GetSystemDirectoryA(sys,MAX_PATH))dirs.push_back(sys);if(::GetSystemWow64DirectoryA(sys,MAX_PATH))dirs.push_back(sys);
  for(const auto&d:dirs)if(fs::exists(d/m,ec))return true;return false;}
 unsigned rsrc_rva(unsigned h){const unsigned opt=h+load(h+0x3c)+24;return load(opt+96+8*2);}
 // Directory entry lookup by ID or upper-case name (IMAGE_RESOURCE_DIR_STRING_U, compared upper-case).
 unsigned entry_of(unsigned root,unsigned dir,const std::pair<unsigned,std::string>&k){const unsigned named=load(dir+12)&0xffff,ids=load(dir+12)>>16;
  for(unsigned i=0;i<named+ids;++i){const unsigned e=dir+16+8*i,name=load(e),off=load(e+4);
   if(name&0x80000000U){if(k.first!=0xffffffffU)continue;const unsigned str=root+(name&0x7fffffffU),len=load(str)&0xffff;std::string t;for(unsigned c=0;c<len;++c){const unsigned w=load(str+2+2*c)&0xffff;t.push_back(char(w<0x80?std::toupper(int(w)):0xff));}if(t!=k.second)continue;}
   else if(name!=k.first)continue;return off;}return 0xffffffffU;}
 unsigned resource(unsigned h,const std::pair<unsigned,std::string>&type,const std::pair<unsigned,std::string>&name){const unsigned rva=rsrc_rva(h);if(!rva)return 0;const unsigned root=h+rva;
  unsigned o=entry_of(root,root,type);if(o==0xffffffffU||!(o&0x80000000U))return 0;o=entry_of(root,root+(o&0x7fffffffU),name);if(o==0xffffffffU||!(o&0x80000000U))return 0;
  const unsigned langs=root+(o&0x7fffffffU),count=(load(langs+12)&0xffff)+(load(langs+12)>>16);if(!count)return 0;
  // Language fallback: neutral, the user's UI language, US English, then the first entry.
  for(const unsigned want:{0U,unsigned(::GetUserDefaultUILanguage()),0x409U}){const unsigned d=entry_of(root,langs,{want,{}});if(d!=0xffffffffU&&!(d&0x80000000U))return root+d;}
  const unsigned d=load(langs+16+4);return (d&0x80000000U)?0:root+d;}
 // Dynamic load: the loader maps and binds the staged module, then calls its DllMain(hinst,
 // DLL_PROCESS_ATTACH, NULL) synchronously as a nested guest call before LoadLibrary returns. The
 // nested return word is a sentinel bound on the returns stack; the call must RET 0Ch to it with TRUE
 // and the callee-saved registers restored.
 // Nested guest call (loader DllMain, window hooks/procedures): the arguments and a sentinel return
 // word are pushed below `below` (default: the current guest ESP), the sentinel is bound on the returns
 // stack, and the callee must return to it with the callee-saved registers restored and the stack
 // popped by its convention (stdcall: all arguments; cdecl: none). ESP/EIP are restored afterwards.
 unsigned call_guest(unsigned target,std::initializer_list<unsigned>args,bool stdcall,const std::string&what,unsigned below=0,bool adapted=false){
  const Body b=find(target);if(!b)deny("Nested guest call target has no lifted body: "+what,target);auto&g=state.gpr;const unsigned esp0=g.rsp.dword,eip0=g.rip.dword;
  const std::array<unsigned,4>keep{g.rbx.dword,g.rsi.dword,g.rdi.dword,g.rbp.dword};const unsigned sentinel=0x36000000U+16U*(++host.nested_calls),n=unsigned(args.size()),esp=(below?below:esp0)-4*(n+1);
  if(!writable(esp,4*(n+1)))deny("Nested call frame outside the stack contract: "+what,esp);store(esp,sentinel);unsigned k=0;for(unsigned v:args)store(esp+4+4*k++,v);
  g.rsp.dword=esp;g.rip.dword=target;const unsigned d0=depth;if(depth>=returns.size())deny("Nested call depth bound",target);returns_sp[depth]=esp;returns[depth++]=sentinel;++bodies;try{if(adapted)(void)remaster_body(&state,target,token_ptr,b);else (void)b(&state,target,token_ptr);}catch(const GuestReturn&r){if(r.frame!=d0)throw;depth=d0;}
  if(depth!=d0||g.rsp.dword!=esp+4+(stdcall?4*n:0)||g.rip.dword!=sentinel||g.rbx.dword!=keep[0]||g.rsi.dword!=keep[1]||g.rdi.dword!=keep[2]||g.rbp.dword!=keep[3])deny("Nested call did not return through its contract: "+what,g.rip.dword);
  const unsigned r=g.rax.dword;g.rsp.dword=esp0;g.rip.dword=eip0;return r;}
  std::string callback_fault;bool host_internal{};unsigned in_wndproc{};
  // MW34_SEH_TEST=<n> (diagnostic; changes game behaviour for one message): the n-th call into game code made inside a
  // window procedure instead does what MFC42 AfxThrowUserException (0x5F463574) does: _CxxThrowException(&p,
  // ThrowInfo 0x5F4B3310) with p = MFC's static CUserException (0x5F4CE380). AfxCallWndProc's CATCH_ALL takes it
  // (CWinApp::ProcessWndProcException reports nothing for CUserException), exercising guest SEH dispatch, RtlUnwind,
  // the catch funclet and the nonlocal continuation.
  const bool seh_test_any=[]{const char*e=std::getenv("MW34_SEH_TEST_ANY");return e&&*e=='1';}();  // MW34_SEH_TEST_ANY=1: count every game call (unhandled path)
  unsigned seh_test=[]{const char*e=std::getenv("MW34_SEH_TEST");return e&&*e?unsigned(std::stoul(e)):0U;}();
  void seh_test_throw(unsigned target){const unsigned at=(state.gpr.rsp.dword-16)&~3U;store(at,0x5f4ce380U);seh_test=0;
   std::fprintf(stderr,"SEH test: game call 0x%08x inside window procedure throws CUserException (raises %llu unwinds %llu nonlocal %llu)\n",target,(unsigned long long)host.raises,(unsigned long long)host.unwinds,(unsigned long long)host.nonlocal_returns);
   (void)call_guest(0x7800ac1aU,{at,0x5f4b3310U},false,"SEH test _CxxThrowException",at);deny("SEH test: _CxxThrowException returned",target);}
 struct HostInternal{Stage&s;bool was;explicit HostInternal(Stage&x):s(x),was(x.host_internal){s.host_internal=true;}~HostInternal(){s.host_internal=was;}};
 static HRESULT enum_mode(Stage*st,unsigned cb,unsigned ctx,unsigned size,unsigned&calls,const DDSURFACEDESC2&d){if(!st->callback_fault.empty())return DDENUMRET_CANCEL;
  try{unsigned at=((st->state.gpr.rsp.dword-0x200)&~15U)-size;st->put_desc(at,d,size);++calls;return HRESULT(st->call_guest(cb,{at,ctx},true,"EnumDisplayModes callback",at&~15U));}catch(const std::exception&e){st->callback_fault=e.what();return DDENUMRET_CANCEL;}}
 struct HookFrame{WPARAM host_w;LPARAM host_l;unsigned guest_l;};std::vector<HookFrame>hook_frames;
 // Host trampolines: marshal the host arguments into guest scratch memory below the guest ESP and run
 // the guest hook procedure as a nested call. Faults never cross the Windows callback boundary: they
 // are recorded and re-thrown when the host API returns into the stage.
 static LRESULT run_hook(int id,int code,WPARAM w,LPARAM l){Stage*st=owner;HHOOK native{};unsigned proc{};
  if(st)for(const auto&k:st->host.hooks)if(k.live&&k.id==id){native=k.native;proc=k.proc;}
  // Windows created by host infrastructure (the Vulkan driver's helper windows while the renderer/presenter
  // runs) are not the game's: the guest hooks (MFC's CBT subclassing) do not see them.
  if(!st||!proc||!st->callback_fault.empty()||st->host_internal)return ::CallNextHookEx(native,code,w,l);
  try{return LRESULT(std::int32_t(st->hook_call(id,proc,code,w,l)));}catch(const std::exception&e){st->callback_fault=e.what();return ::CallNextHookEx(native,code,w,l);}}
 static LRESULT CALLBACK hook_msgfilter(int code,WPARAM w,LPARAM l){return run_hook(WH_MSGFILTER,code,w,l);}
 static LRESULT CALLBACK hook_cbt(int code,WPARAM w,LPARAM l){return run_hook(WH_CBT,code,w,l);}
 unsigned scratch_string(unsigned&at,const char*t){if(!t)return 0;if(reinterpret_cast<std::uintptr_t>(t)<0x10000)return unsigned(reinterpret_cast<std::uintptr_t>(t));const unsigned k=unsigned(std::strlen(t))+1;at-=(k+3)&~3U;
  for(unsigned i=0;i<k;++i)runtime.memory().store<unsigned char>({at+i},static_cast<unsigned char>(t[i]));return at;}
 unsigned hook_call(int id,unsigned proc,int code,WPARAM w,LPARAM l){auto&g=state.gpr;unsigned at=(g.rsp.dword-0x100)&~15U;unsigned gw=unsigned(w),gl=0;
  auto gh=[&](const void*h){const auto v=reinterpret_cast<std::intptr_t>(h);if(v!=std::intptr_t(std::int32_t(v)))deny("Hook handle not representable as a guest word",0);return unsigned(v);};
  if(id==WH_MSGFILTER){const MSG&m=*reinterpret_cast<const MSG*>(l);at-=28;const std::array<unsigned,7>v{gh(m.hwnd),m.message,unsigned(m.wParam),unsigned(m.lParam),host.guest_tick_of(m.time),unsigned(m.pt.x),unsigned(m.pt.y)};for(unsigned i=0;i<7;++i)store(at+4*i,v[i]);gl=at;}
  else if(id==WH_CBT){
   if(code==HCBT_CREATEWND){const auto&c=*reinterpret_cast<const CBT_CREATEWNDA*>(l);const auto&cs=*c.lpcs;const unsigned name=scratch_string(at,cs.lpszName),cls=scratch_string(at,cs.lpszClass);
    at-=48;const std::array<unsigned,12>v{unsigned(reinterpret_cast<std::uintptr_t>(cs.lpCreateParams)),guest_instance(cs.hInstance),gh(cs.hMenu),gh(cs.hwndParent),unsigned(cs.cy),unsigned(cs.cx),unsigned(cs.y),unsigned(cs.x),unsigned(cs.style),name,cls,cs.dwExStyle};
    for(unsigned i=0;i<12;++i)store(at+4*i,v[i]);const unsigned gcs=at;at-=8;store(at,gcs);store(at+4,gh(c.hwndInsertAfter));gl=at;gw=gh(reinterpret_cast<HWND>(w));}
   else if(code==HCBT_DESTROYWND||code==HCBT_MINMAX||code==HCBT_QS||code==HCBT_SYSCOMMAND||code==HCBT_KEYSKIPPED){gw=code==HCBT_DESTROYWND||code==HCBT_MINMAX?gh(reinterpret_cast<HWND>(w)):unsigned(w);gl=unsigned(l);}
   else if(code==HCBT_SETFOCUS){gw=gh(reinterpret_cast<HWND>(w));gl=gh(reinterpret_cast<HWND>(l));}
   else if(code==HCBT_CLICKSKIPPED){const auto&mh=*reinterpret_cast<const MOUSEHOOKSTRUCT*>(l);const auto ex=static_cast<std::uint64_t>(mh.dwExtraInfo);if(ex>0xffffffffULL)deny("HCBT_CLICKSKIPPED extra info not representable as a guest word",0);  // x86 MOUSEHOOKSTRUCT, 20 bytes
    at-=20;const std::array<unsigned,5>v{unsigned(mh.pt.x),unsigned(mh.pt.y),gh(mh.hwnd),unsigned(mh.wHitTestCode),unsigned(ex)};for(unsigned i=0;i<5;++i)store(at+4*i,v[i]);gl=at;gw=unsigned(w);}
   else if(code==HCBT_MOVESIZE){const auto&r=*reinterpret_cast<const RECT*>(l);at-=16;store(at,unsigned(r.left));store(at+4,unsigned(r.top));store(at+8,unsigned(r.right));store(at+12,unsigned(r.bottom));gl=at;gw=gh(reinterpret_cast<HWND>(w));}
   else if(code==HCBT_ACTIVATE){const auto&a=*reinterpret_cast<const CBTACTIVATESTRUCT*>(l);at-=8;store(at,unsigned(a.fMouse));store(at+4,gh(a.hWndActive));gl=at;gw=gh(reinterpret_cast<HWND>(w));}
   else deny("WH_CBT code not modelled: "+std::to_string(code),unsigned(code));}
  hook_frames.push_back({w,l,gl});struct Pop{std::vector<HookFrame>&f;~Pop(){f.pop_back();}}pop{hook_frames};
  return call_guest(proc,{unsigned(code),gw,gl},true,"hook "+std::to_string(id),at&~15U);}
#include "win_bridge.inc"
#include "vdd.inc"
#include "device_fog_stage.inc"
#include "d3d_provider.inc"
#include "gpu_hud.inc"
 // Guest view of a host HINSTANCE: the worker module stands for the game image (classes it registers).
 // System windows created on the guest thread (IME etc.) carry host module instances the guest never
 // loaded: those become opaque instance tokens that map back to the real HINSTANCE.
 unsigned guest_instance(HINSTANCE h){if(!h||h==::GetModuleHandleW(nullptr))return h?0x400000:0;for(unsigned i=0;i<host.foreign_instances.size();++i)if(host.foreign_instances[i]==h)return 0x3c000000U+16U*i;
  host.foreign_instances.push_back(h);return 0x3c000000U+16U*unsigned(host.foreign_instances.size()-1);}  // a fault inside a host->guest callback, re-thrown when the host API returns
 unsigned load_module(Host::Loadable&l){if(!host.msvcrt)deny("Staged MSVCRT image required for the loader model",0);
  map_module(runtime,l.bytes,l.sha.c_str(),l.name.c_str(),*host.msvcrt,host);auto&md=host.modules.back();host.paths[md.base]=l.path;
  const unsigned entry_body=md.entry;if(md.entry==md.base){md.attached=true;return md.base;}const Body b=find(entry_body);if(!b)deny("Dynamically loaded module entry has no lifted body: "+l.name,entry_body);
  (void)b;const unsigned ok=call_guest(entry_body,{md.base,DLL_PROCESS_ATTACH,0},true,"DllMain "+l.name);
  if(!ok)deny("Dynamically loaded module DllMain(DLL_PROCESS_ATTACH) returned FALSE (unload path not modelled): "+l.name,md.base);
  md.attached=true;return md.base;}
 // COM arena: guest objects (vtable word) and one token vtable per interface; host interface behind.
 unsigned com_alloc(unsigned bytes){if(host.com_next==com::arena){bool bad{};try{runtime.memory().map({com::arena},com::arena_end-com::arena,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked COM arena mapping",com::arena);}
  const unsigned g=host.com_next;if(std::uint64_t(g)+bytes>com::arena_end)deny("COM arena exhausted",g);host.com_next+=(bytes+15U)&~15U;return g;}
 unsigned com_vtable(const com::Iface&i){auto it=host.com_vtables.find(i.name);if(it!=host.com_vtables.end())return it->second;const unsigned vt=com_alloc(4*unsigned(i.slots.size()));
  unsigned tokens=0;for(const auto&x:host.imports)if(x.bound>=token_base&&x.bound<token_end)++tokens;
  for(unsigned k=0;k<i.slots.size();++k){const unsigned t=token_base+16*(tokens+k);if(t>=token_end)deny("Import token space",t);host.imports.push_back({0,t,i.name,i.slots[k]});store(vt+4*k,t);}
  host.com_vtables[i.name]=vt;return vt;}
 unsigned com_wrap(IUnknown*native,const com::Iface&i,unsigned owner=0){const unsigned g=com_alloc(16);store(g,com_vtable(i));host.com_objects.push_back({g,&i,native,true,owner});if(native)host.com_objects.back().refs=1;return g;}
 static unsigned root_of(const com::Object&o){return o.owner?o.owner:o.guest;}
 GUID guest_guid(unsigned a){if(!readable(a,16))deny("GUID outside the memory contract",a);GUID g;std::array<unsigned,4>w{load(a),load(a+4),load(a+8),load(a+12)};std::memcpy(&g,w.data(),16);return g;}
 // The provider: the real x64 system ddraw.dll, by explicit system-directory path, identified.
 com::Provider&ddraw(){auto&d=host.ddraw;if(d.module)return d;wchar_t sys[MAX_PATH]{};const UINT k=::GetSystemDirectoryW(sys,MAX_PATH);if(!k||k>=MAX_PATH)deny("System directory for the DirectDraw provider",0);
  d.path=std::wstring(sys)+L"\\ddraw.dll";d.module=::LoadLibraryW(d.path.c_str());if(!d.module)deny("Real system DirectDraw provider unavailable",0);
  d.create=reinterpret_cast<decltype(d.create)>(::GetProcAddress(d.module,"DirectDrawCreate"));if(!d.create)deny("Provider DirectDrawCreate export",0);
  std::ifstream f(d.path,std::ios::binary);const std::string raw((std::istreambuf_iterator<char>(f)),{});std::vector<std::byte>b(raw.size());std::memcpy(b.data(),raw.data(),raw.size());d.sha=m4::sha256(b);return d;}
 // The sound provider: the real x64 system dsound.dll, by explicit system-directory path, identified.
 com::SoundProvider&dsound(){auto&d=host.dsound;if(d.module)return d;wchar_t sys[MAX_PATH]{};const UINT k=::GetSystemDirectoryW(sys,MAX_PATH);if(!k||k>=MAX_PATH)deny("System directory for the DirectSound provider",0);
  d.path=std::wstring(sys)+L"\\dsound.dll";d.module=::LoadLibraryW(d.path.c_str());if(!d.module)deny("Real system DirectSound provider unavailable",0);
  d.create=reinterpret_cast<decltype(d.create)>(::GetProcAddress(d.module,"DirectSoundCreate"));if(!d.create)deny("Provider DirectSoundCreate export",0);
  std::ifstream f(d.path,std::ios::binary);const std::string raw((std::istreambuf_iterator<char>(f)),{});std::vector<std::byte>b(raw.size());std::memcpy(b.data(),raw.data(),raw.size());d.sha=m4::sha256(b);return d;}
 // x86 WAVEFORMATEX (18 bytes + cbSize extra) from guest memory.
 std::vector<unsigned char>guest_waveformat(unsigned a){if(!readable(a,18))deny("WAVEFORMATEX outside the memory contract",a);const unsigned extra=load(a+16)&0xffff;if(!readable(a,18+extra))deny("WAVEFORMATEX extra bytes outside the memory contract",a);
  std::vector<unsigned char>v(18+extra);for(unsigned i=0;i<v.size();++i)v[i]=runtime.memory().load<unsigned char>({a+i});return v;}
 // x86 DDSURFACEDESC (108) / DDSURFACEDESC2 (124): same field order as x64 except lpSurface (a guest word
 // at offset 36, never carried); colour keys, pixel format and caps are all DWORDs.
 void put_desc(unsigned a,const DDSURFACEDESC2&d,unsigned size){if(!writable(a,size))deny("Surface descriptor outside the memory contract",a);
  const std::array<unsigned,9>head{size,d.dwFlags,d.dwHeight,d.dwWidth,unsigned(d.lPitch),d.dwBackBufferCount,d.dwMipMapCount,d.dwAlphaBitDepth,d.dwReserved};for(unsigned i=0;i<9;++i)store(a+4*i,head[i]);store(a+36,0);
  std::array<unsigned,8>ck{};std::memcpy(ck.data(),&d.ddckCKDestOverlay,32);for(unsigned i=0;i<8;++i)store(a+40+4*i,ck[i]);std::array<unsigned,8>pf{};std::memcpy(pf.data(),&d.ddpfPixelFormat,32);for(unsigned i=0;i<8;++i)store(a+72+4*i,pf[i]);
  store(a+104,d.ddsCaps.dwCaps);if(size==124){store(a+108,d.ddsCaps.dwCaps2);store(a+112,d.ddsCaps.dwCaps3);store(a+116,d.ddsCaps.dwCaps4);store(a+120,d.dwTextureStage);}}
 DDSURFACEDESC2 get_desc(unsigned a,unsigned size){if(!readable(a,size)||load(a)!=size)deny("Surface descriptor outside the contract or with a wrong dwSize",a);DDSURFACEDESC2 d{};d.dwSize=sizeof(d);d.dwFlags=load(a+4);
  if(d.dwFlags&DDSD_LPSURFACE)deny("Surface descriptor with client memory is not modelled",a);d.dwHeight=load(a+8);d.dwWidth=load(a+12);d.lPitch=LONG(load(a+16));d.dwBackBufferCount=load(a+20);d.dwMipMapCount=load(a+24);d.dwAlphaBitDepth=load(a+28);d.dwReserved=load(a+32);
  std::array<unsigned,8>ck{};for(unsigned i=0;i<8;++i)ck[i]=load(a+40+4*i);std::memcpy(&d.ddckCKDestOverlay,ck.data(),32);std::array<unsigned,8>pf{};for(unsigned i=0;i<8;++i)pf[i]=load(a+72+4*i);std::memcpy(&d.ddpfPixelFormat,pf.data(),32);
  d.ddsCaps.dwCaps=load(a+104);if(size==124){d.ddsCaps.dwCaps2=load(a+108);d.ddsCaps.dwCaps3=load(a+112);d.ddsCaps.dwCaps4=load(a+116);d.dwTextureStage=load(a+120);}return d;}
 // Pixel formats of the virtual display: 16-bit RGB565 (the game's green mask 0x7E0 branch) and 8-bit palettized.
 static DDPIXELFORMAT virtual_format(unsigned bpp){DDPIXELFORMAT f{};f.dwSize=sizeof(f);if(bpp==8){f.dwFlags=DDPF_RGB|DDPF_PALETTEINDEXED8;f.dwRGBBitCount=8;return f;}
  if(bpp!=16)throw std::runtime_error("Virtual display depth not modelled");f.dwFlags=DDPF_RGB;f.dwRGBBitCount=16;f.dwRBitMask=0xf800;f.dwGBitMask=0x07e0;f.dwBBitMask=0x001f;return f;}
 std::vector<DDSURFACEDESC2>virtual_modes(IUnknown*dd){std::vector<std::pair<unsigned,unsigned>>sizes;IDirectDraw4*dd4{};
  if(FAILED(dd->QueryInterface(IID_IDirectDraw4,reinterpret_cast<void**>(&dd4)))||!dd4)deny("Virtual modes need the provider's DirectDraw4",0);
  dd4->EnumDisplayModes(0,nullptr,&sizes,[](LPDDSURFACEDESC2 d,LPVOID p)->HRESULT{auto&v=*static_cast<std::vector<std::pair<unsigned,unsigned>>*>(p);const std::pair<unsigned,unsigned>k{d->dwWidth,d->dwHeight};
   if(std::find(v.begin(),v.end(),k)==v.end())v.push_back(k);return DDENUMRET_OK;});dd4->Release();
  std::vector<DDSURFACEDESC2>out;for(const auto&[w,h]:sizes)for(unsigned b:{8U,16U,32U}){DDSURFACEDESC2 d{};d.dwSize=sizeof(d);d.dwFlags=DDSD_WIDTH|DDSD_HEIGHT|DDSD_PITCH|DDSD_PIXELFORMAT;d.dwWidth=w;d.dwHeight=h;d.lPitch=LONG(w*b/8);
   if(b==32){d.ddpfPixelFormat.dwSize=sizeof(DDPIXELFORMAT);d.ddpfPixelFormat.dwFlags=DDPF_RGB;d.ddpfPixelFormat.dwRGBBitCount=32;d.ddpfPixelFormat.dwRBitMask=0xff0000;d.ddpfPixelFormat.dwGBitMask=0xff00;d.ddpfPixelFormat.dwBBitMask=0xff;}else d.ddpfPixelFormat=virtual_format(b);
   out.push_back(d);}return out;}
 void dibs_to_host(){for(const auto&d:host.dibs)get_bytes(d.guest,d.bits,d.bytes);}
 void dibs_to_guest(){for(const auto&d:host.dibs)write_bytes(d.guest,d.bits,d.bytes);}
 bool in_sound(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;for(const auto&l:host.sound_locks)if((l.g1&&a>=l.g1&&e<=std::uint64_t(l.g1)+l.b1)||(l.g2&&a>=l.g2&&e<=std::uint64_t(l.g2)+l.b2))return true;return false;}
 bool in_dib(unsigned a,unsigned n)const{const auto e=std::uint64_t(a)+n;for(const auto&d:host.dibs)if(a>=d.guest&&e<=std::uint64_t(d.guest)+d.bytes)return true;return false;}
 unsigned gheap_alloc(unsigned bytes,bool zero,unsigned owner=0){
  const unsigned allocated=host.gheap.allocate(bytes,zero,owner,[&](unsigned at,unsigned size){bool bad{};try{runtime.memory().map({at},size,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked guest heap region mapping",at);},
   [&](unsigned at,unsigned size){std::vector<std::byte>z(size);runtime.memory().write({at},z);},
   [&](unsigned at,unsigned size,unsigned limit){return runtime.memory().find_unmapped_range(at,size,limit);});
  if(!allocated){host.failed_heap_bytes=bytes;host.failed_heap_owner=owner;++host.heap_failures;}
  return allocated;}
 void gheap_free(unsigned at){if(!host.gheap.live.count(at))deny("HeapFree of a pointer that is not a live guest heap block",at);host.gheap.release(at);}
 unsigned handle_token(void*h){if(!h)return 0;for(unsigned i=0;i<host.handle_tokens.size();++i)if(host.handle_tokens[i]==h)return 0x3d000000U+16U*i;host.handle_tokens.push_back(h);return 0x3d000000U+16U*unsigned(host.handle_tokens.size()-1);}
 void*token_handle(unsigned g){if(g<0x3d000000||(g-0x3d000000)%16||(g-0x3d000000)/16>=host.handle_tokens.size())return nullptr;return host.handle_tokens[(g-0x3d000000)/16];}
 // A mixer-object argument is a handle token or a small device id (MIXER_OBJECTF_* selects which).
 HMIXEROBJ mixer_obj(unsigned v){if(void*h=token_handle(v))return reinterpret_cast<HMIXEROBJ>(h);if(v>=0x10000)deny("Mixer object is neither a handle token nor a device id",v);return reinterpret_cast<HMIXEROBJ>(std::uintptr_t(v));}
 // The input provider: the real x64 system dinput.dll, by explicit system-directory path, identified.
 com::InputProvider&dinput(){auto&d=host.dinput;if(d.module)return d;wchar_t sys[MAX_PATH]{};const UINT k=::GetSystemDirectoryW(sys,MAX_PATH);if(!k||k>=MAX_PATH)deny("System directory for the DirectInput provider",0);
  d.path=std::wstring(sys)+L"\\dinput.dll";d.module=::LoadLibraryW(d.path.c_str());if(!d.module)deny("Real system DirectInput provider unavailable",0);
  d.create=reinterpret_cast<decltype(d.create)>(::GetProcAddress(d.module,"DirectInputCreateA"));if(!d.create)deny("Provider DirectInputCreateA export",0);
  std::ifstream f(d.path,std::ios::binary);const std::string raw((std::istreambuf_iterator<char>(f)),{});std::vector<std::byte>b(raw.size());std::memcpy(b.data(),raw.data(),raw.size());d.sha=m4::sha256(b);return d;}
 unsigned cur_tid()const{return host.thread_tid?host.thread_tid: ::GetCurrentThreadId();}
 Host::GuestThread*guest_thread(unsigned h){for(auto&t:host.threads)if(t.handle==h)return &t;return nullptr;}
 unsigned run_thread(size_t idx){auto&T=host.threads[idx];static_assert(std::is_trivially_copyable_v<State>);State saved;std::memcpy(&saved,&state,sizeof(State));
  const unsigned teb=runtime.fs_base().value,seh=load(teb),tid0=host.thread_tid,d0=depth,err0=host.last_error;std::vector<DWORD>ids(host.tls.begin(),host.tls.end());if(std::find(ids.begin(),ids.end(),DWORD(heap.tls))==ids.end())ids.push_back(heap.tls);
  std::vector<std::pair<DWORD,LPVOID>>tlsv;for(const DWORD k:ids){tlsv.push_back({k,::TlsGetValue(k)});::TlsSetValue(k,nullptr);}
  unsigned short cw0;unsigned mx0;__asm__ volatile("fnstcw %0\n\tstmxcsr %1":"=m"(cw0),"=m"(mx0));{const unsigned short cw=0x27f;const unsigned mx=0x1f80;__asm__ volatile("fldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mx));}
  auto&g=state.gpr;for(auto*r:{&g.rax,&g.rbx,&g.rcx,&g.rdx,&g.rsi,&g.rdi,&g.rbp})r->dword=0;state.aflag.df=0;std::memset(&state.st,0,sizeof(state.st));std::memset(&state.mmx,0,sizeof(state.mmx));std::memset(&state.sw,0,sizeof(state.sw));
  std::memset(&state.x87,0,sizeof(state.x87));state.x87.fxsave32.cwd.flat=0x27f;state.x87.fxsave32.mxcsr.flat=0x1f80;
  store(teb,0xffffffffU);host.thread_tid=T.tid;host.last_error=0;const unsigned top=T.stack_hi-16;g.rsp.dword=top;
  std::vector<std::remove_reference_t<decltype(host.modules.front())>*>mods;for(auto&m:host.modules)if(m.attached&&!m.thread_calls_disabled&&m.entry)mods.push_back(&m);
  call_guest(msvcrt_entry,{msvcrt_base,DLL_THREAD_ATTACH,0},true,"MSVCRT DLL_THREAD_ATTACH",top);for(const auto*m:mods)call_guest(m->entry,{m->base,DLL_THREAD_ATTACH,0},true,m->name+" DLL_THREAD_ATTACH",top);
  const unsigned code=call_guest(T.start,{T.param},true,"guest thread start routine",top);
  for(auto it=mods.rbegin();it!=mods.rend();++it)call_guest((*it)->entry,{(*it)->base,DLL_THREAD_DETACH,0},true,(*it)->name+" DLL_THREAD_DETACH",top);call_guest(msvcrt_entry,{msvcrt_base,DLL_THREAD_DETACH,0},true,"MSVCRT DLL_THREAD_DETACH",top);
  if(depth!=d0||load(teb)!=0xffffffffU)deny("Guest thread did not unwind its frames and exception list",load(teb));
  for(const auto&[k,v]:host.mutexes)if(v.first==T.tid)deny("Guest thread exited owning a mutex (abandoned mutexes are not modelled)",k);
  T.exit_code=code;T.exited=true;{bool bad{};try{runtime.memory().unmap({T.stack_lo});}catch(...){bad=true;}if(bad)deny("Checked guest thread stack release",T.stack_lo);}if(!::SetEvent(reinterpret_cast<HANDLE>(std::intptr_t(std::int32_t(T.handle)))))deny("Thread object signal",T.handle);
  std::memcpy(&state,&saved,sizeof(State));store(teb,seh);host.thread_tid=tid0;host.last_error=err0;for(const auto&[k,v]:tlsv)::TlsSetValue(k,v);__asm__ volatile("fldcw %0\n\tldmxcsr %1"::"m"(cw0),"m"(mx0));return code;}
 // Registry overlay persistence: "K path" and "V path<TAB>name<TAB>type<TAB>hex" lines in the game folder.
 Host::RegOverlay&reg_overlay(){auto&o=host.reg;if(o.loaded)return o;o.loaded=true;o.file=(std::filesystem::path(host.paths.at(0x400000)).parent_path()/"mw34-registry.txt").string();if(const char*e=std::getenv("MW34_REG_OVERLAY");e&&*e)o.file=e;  /* MW34_REG_OVERLAY=<file>: a test overlay instead of the game folder's (scripted replays use a frozen copy) */
 std::ifstream f(o.file);std::string line;
  while(std::getline(f,line)){if(line.size()>2&&line[0]=='K'&&line[1]==' ')o.keys[line.substr(2)];else if(line.size()>2&&line[0]=='V'&&line[1]==' '){std::istringstream l(line.substr(2));std::string p,nm,ty,hx;
   if(!std::getline(l,p,'\t')||!std::getline(l,nm,'\t')||!std::getline(l,ty,'\t'))deny("Registry overlay line malformed",0);std::getline(l,hx);std::vector<BYTE>b;for(size_t i=0;i+1<hx.size();i+=2)b.push_back(BYTE(std::stoul(hx.substr(i,2),nullptr,16)));
   o.keys[p][nm]={DWORD(std::stoul(ty)),std::move(b)};}}return o;}
 void save_reg_overlay(){auto&o=host.reg;const std::string tmp=o.file+".new";{std::ofstream f(tmp,std::ios::trunc);if(!f)deny("Registry overlay not writable in the game folder",0);
   for(const auto&[p,vals]:o.keys){f<<"K "<<p<<"\n";for(const auto&[nm,v]:vals){f<<"V "<<p<<'\t'<<nm<<'\t'<<v.first<<'\t';char h[3];for(BYTE c:v.second){std::snprintf(h,sizeof h,"%02x",c);f<<h;}f<<"\n";}}
   if(!f)deny("Registry overlay write failed",0);}
   // A scanner or indexer can hold the freshly written file briefly: retry transient sharing/lock/access errors
   // for up to about two seconds before failing visibly with the Windows error code.
   DWORD err=0;for(int attempt=0;attempt<40;++attempt){if(::MoveFileExA(tmp.c_str(),o.file.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))return;
    err=::GetLastError();if(err!=ERROR_SHARING_VIOLATION&&err!=ERROR_LOCK_VIOLATION&&err!=ERROR_ACCESS_DENIED)break;::Sleep(50);}
   deny("Registry overlay replace failed (Windows error "+std::to_string(err)+")",err);}
 // Script events are due by presented frame, or ("+MS" lines) by host milliseconds since the first rendered
 // 3D scene, the mission's wall-clock timeline independent of the host frame rate.
 bool script_due(const Host::ScriptEvent&e)const{if(!e.timed)return e.frame<=host.frames;return host.scene_t0&&host_ms()-host.scene_t0>=e.frame;}
 std::uint64_t host_ms()const{return host.vclock()?host.vclock_us/1000: ::GetTickCount64();}
 std::string guest_string(unsigned a,unsigned limit=4096){std::string s;for(unsigned i=0;i<limit;++i){if(!readable(a+i,1))deny("Service string outside the memory contract",a);const auto c=runtime.memory().load<unsigned char>({a+i});if(!c)return s;s.push_back(char(c));}deny("Service string unterminated",a);}
 unsigned pages(const void*contents,unsigned bytes){const unsigned n=(std::max(bytes,1U)+4095U)&~4095U;unsigned guest=0;
  for(auto it=host.pages_free.begin();it!=host.pages_free.end();++it)if(it->second>=n){guest=it->first;const unsigned rest=it->second-n;host.pages_free.erase(it);if(rest)host.pages_free[guest+n]=rest;break;}
  if(!guest){guest=heap.next;if(std::uint64_t(guest)+n>hs::arena_end)deny("Guest arena exhausted",guest);heap.next+=n;}host.pages_live[guest]=n;
  std::vector<std::byte>v(n);if(contents)std::memcpy(v.data(),contents,bytes);bool bad{};try{runtime.memory().map({guest},n,Permissions::read|Permissions::write);runtime.memory().write({guest},v);}catch(...){bad=true;}if(bad)deny("Checked guest block publication",guest);return guest;}
 unsigned publish_local(HLOCAL native,unsigned bytes){const unsigned guest=pages(native,bytes);host.locals.push_back({guest,bytes,native,false});return guest;}
 std::vector<std::byte>guest_bytes(unsigned a,unsigned n){std::vector<std::byte>v(n);bool bad{};try{for(unsigned o=0;o<n;){const unsigned k=std::min(n-o,4096U-((a+o)&4095U));runtime.memory().read({a+o},std::span<std::byte>(v.data()+o,k));o+=k;}}catch(...){bad=true;}if(bad)deny("Checked guest block read",a);return v;}
 void release(unsigned guest){bool bad{};try{runtime.memory().unmap({guest});}catch(...){bad=true;}if(bad)deny("Checked guest block release",guest);
  auto lv=host.pages_live.find(guest);if(lv==host.pages_live.end())return;unsigned at=guest,size=lv->second;host.pages_live.erase(lv);auto&fr=host.pages_free;
  auto nx=fr.lower_bound(at);if(nx!=fr.end()&&at+size==nx->first){size+=nx->second;nx=fr.erase(nx);}if(nx!=fr.begin()){auto pv=std::prev(nx);if(pv->first+pv->second==at){pv->second+=size;return;}}fr[at]=size;}
 void*api(State*s,unsigned token,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=token)deny("Exact MFC42-stage import State",token);
  const Import*imp=host.by_bound(token);const Import*gi=imp?nullptr:game_import(token);bool crt=false;if(gi)imp=gi;if(!imp){crt=true;imp=host.by_raw(token);}if(!imp)deny("Unbound service token",token);
  auto&g=state.gpr;const unsigned e=g.rsp.dword,ret=load(e);const std::string&n=imp->name;if(apis.size()>=400000)++apis_dropped;{auto&lb=imp->label[crt?1:gi?2:0];if(!lb){host.service_labels.push_back((crt?"MSVCRT>":gi?"GAME>":"")+imp->dll+"!"+n);lb=&host.service_labels.back();}apis.push_back(lb);}
  if(gi?!(ret>=0x401000&&ret<0x5bb000):crt?!(ret>=msvcrt_base+0x1000&&ret<msvcrt_text_end):(!find(ret)&&!in_module(ret,1,false)&&!(kind==Kind::initterm&&ret>=0x401000&&ret<0x5bb000)&&!(ret>=msvcrt_base+0x1000&&ret<msvcrt_text_end)))deny("Service return word outside the importing module's code",ret);  // MSVCRT code also calls GetProcAddress tokens (FDIV initializer)
  auto arg=[&](unsigned i){return load(e+4+4*i);};
  const bool gdi_sync=!host.dibs.empty()&&(same(imp->dll,"GDI32.dll")||n=="FillRect"||n=="DrawTextA"||n=="ReleaseDC"||n=="GetDC");if(gdi_sync)dibs_to_host();
  auto done=[&](unsigned eax,unsigned args){if(!callback_fault.empty())deny("Guest callback fault: "+callback_fault,0);{static FILE*const tr=[]{const char*q=std::getenv("MW34_TRACE_SERVICES");FILE*f=q&&*q?std::fopen(q,"w"):nullptr;if(f)std::setvbuf(f,nullptr,_IOFBF,1<<26);return f;}();static const std::string only=[]{const char*q=std::getenv("MW34_TRACE_ONLY");return q?std::string(",")+q+",":std::string();}();if(tr&&host.frames<=12&&(only.empty()||only.find(","+n+",")!=std::string::npos)){std::fprintf(tr,"%llu %s eax=%08x ret=%08x a0=%08x a1=%08x a2=%08x esp=%08x msg=%04x\n",(unsigned long long)host.frames,n.c_str(),eax,ret,args?load(e+4):0U,args>1?load(e+8):0U,args>2?load(e+12):0U,e,((n=="PeekMessageA"||n=="GetMessageA")&&eax&&eax!=0xffffffffU)?load(load(e+4)+4):0U);}else if(tr&&host.frames==13){std::fflush(tr);}}/* MW34_TRACE_SERVICES=<file> [MW34_TRACE_ONLY=name,...]: services of frames 0-12 with results, for finding replay divergence */if(gdi_sync)dibs_to_guest();g.rax.dword=eax;g.rsp.dword=e+4+4*args;g.rip.dword=ret;++api_calls;return p;};
  // COM method imports (the module is a modelled interface) go straight to the COM dispatch: every service test
  // between here and there is keyed on a Win32/CRT name or prefix that no modelled interface method has (the
  // only shared names, GetDC/ReleaseDC, are used above in gdi_sync only), so the result is the same.
  if(!imp->iface_resolved){imp->iface_cache=com::by_name(imp->dll);imp->iface_resolved=true;}
  if(imp->iface_cache)goto com_dispatch;
  if(n=="LoadLibraryA"){const std::string m=guest_string(arg(0));unsigned h=module(m.substr(m.find_last_of("\\/")==std::string::npos?0:m.find_last_of("\\/")+1));if(m.find_first_of("\\/:")!=std::string::npos&&h){bool path_ok=false;for(const auto&[b,path]:host.paths)if(b==h&&same(m,path))path_ok=true;if(!path_ok)h=0;}
   for(const auto&[b,path]:host.paths)if(same(m,path))h=b;
   if(!h){const std::string leaf=m.substr(m.find_last_of("\\/")==std::string::npos?0:m.find_last_of("\\/")+1);
    for(auto&l:host.loadable)if(same(leaf,l.name)&&(leaf==m||same(m,l.path))){const unsigned e0=e,ret0=ret;const unsigned hb=load_module(l);g.rsp.dword=e0;g.rip.dword=ret0;
     std::string k=l.name;std::transform(k.begin(),k.end(),k.begin(),[](unsigned char c){return char(std::toupper(c));});++host.loads[k];host.last_error=0;return done(hb,1);}}
   if(!h&&!present(m)){host.last_error=ERROR_MOD_NOT_FOUND;return done(0,1);}  // the real loader fails: no such file on its search path
   if(!h)deny("LoadLibraryA of an existing module outside the guest loader model: "+m,arg(0));std::string k=m;std::transform(k.begin(),k.end(),k.begin(),[](unsigned char c){return char(std::toupper(c));});++host.loads[k];host.last_error=0;return done(h,1);}
  if(n=="SetErrorMode"){UINT prev{};{LastError l(host);prev=::SetErrorMode(arg(0));}return done(prev,1);}
  // Moveable local memory: the handle is a guest token; the block (guest heap memory) never moves, as the API
  // permits. LocalLock returns it and counts locks.
  if(n=="LocalAlloc"&&(arg(0)&LMEM_MOVEABLE)){const unsigned flags=arg(0);if(flags&~(LMEM_MOVEABLE|LMEM_ZEROINIT))deny("LocalAlloc flags outside the model",flags);const unsigned p=gheap_alloc(arg(1),flags&LMEM_ZEROINIT);
   if(!p){host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(0,2);}const unsigned tok=0x3f700000U+16U*(++host.moveable_serial);host.moveable[tok]={p,arg(1),0};return done(tok,2);}
  if(host.moveable.count(arg(0))&&(n=="LocalLock"||n=="LocalUnlock"||n=="LocalFree"||n=="LocalSize"||n=="LocalReAlloc"||n=="LocalFlags")){auto&mv=host.moveable[arg(0)];
   if(n=="LocalLock"){++mv.locks;return done(mv.ptr,1);}
   if(n=="LocalUnlock"){if(!mv.locks){host.last_error=ERROR_NOT_LOCKED;return done(0,1);}--mv.locks;host.last_error=mv.locks?0:NO_ERROR;return done(mv.locks?1U:0U,1);}
   if(n=="LocalSize")return done(mv.size,1);
   if(n=="LocalFlags")return done(mv.locks&0xff,1);
   if(n=="LocalFree"){gheap_free(mv.ptr);host.moveable.erase(arg(0));return done(0,1);}
   const unsigned bytes=arg(1),flags=arg(2);if(flags&~(LMEM_MOVEABLE|LMEM_ZEROINIT))deny("LocalReAlloc flags outside the model",flags);const unsigned p=gheap_alloc(bytes,flags&LMEM_ZEROINIT);if(!p)return done(0,3);
   std::vector<std::byte>vb(std::min(mv.size,bytes));if(!vb.empty()){runtime.memory().read({mv.ptr},vb);runtime.memory().write({p},vb);}gheap_free(mv.ptr);mv.ptr=p;mv.size=bytes;return done(arg(0),3);}
  if(n=="LocalHandle")for(const auto&[tok,mv]:host.moveable)if(mv.ptr==arg(0))return done(tok,1);
  if(n=="LocalAlloc"){const unsigned flags=arg(0),bytes=arg(1);if(flags&LMEM_MOVEABLE)deny("LocalAlloc(LMEM_MOVEABLE) handles are not modelled",flags);HLOCAL h{};{LastError l(host);h=::LocalAlloc(flags,bytes);}return done(h?publish_local(h,bytes):0,2);}
  if(n=="LocalFree"){const unsigned a=arg(0);for(auto&l:host.locals)if(!l.freed&&l.guest==a){HLOCAL r{};{LastError x(host);r=::LocalFree(l.native);}if(r)deny("Real LocalFree failed",a);l.freed=true;bool bad{};try{runtime.memory().unmap({a});}catch(...){bad=true;}if(bad)deny("Checked LocalFree release",a);return done(0,1);}
   deny("LocalFree of a pointer that is not a live LocalAlloc block",a);}
  // LocalReAlloc of a fixed block (LMEM_MOVEABLE lets it move); the guest copy moves with it.
  if(n=="LocalReAlloc"){const unsigned a=arg(0),bytes=arg(1),flags=arg(2);if(flags&~(LMEM_MOVEABLE|LMEM_ZEROINIT))deny("LocalReAlloc flags outside the modelled set",flags);
   for(auto&l:host.locals)if(!l.freed&&l.guest==a){HLOCAL h{};{LastError x(host);h=::LocalReAlloc(l.native,bytes,flags);}if(!h)return done(0,3);
    std::vector<std::byte>v=guest_bytes(a,std::min(l.bytes,bytes));v.resize(bytes);if(!(flags&LMEM_ZEROINIT)&&bytes>l.bytes)std::memcpy(v.data()+l.bytes,static_cast<const std::byte*>(h)+l.bytes,bytes-l.bytes);
    release(a);l.native=h;l.guest=pages(v.data(),bytes);l.bytes=bytes;return done(l.guest,3);}
   deny("LocalReAlloc of a pointer that is not a live LocalAlloc block",a);}
  if(n=="GetModuleFileNameA"){const unsigned h=arg(0)?arg(0):0x400000,a=arg(1),size=arg(2);const auto it=host.paths.find(h);if(it==host.paths.end())deny("GetModuleFileNameA of a module without a loaded image path",h);
   if(!size)deny("GetModuleFileNameA with an empty buffer",a);if(!writable(a,size))deny("GetModuleFileNameA output outside the memory contract",a);const std::string&path=it->second;
   const unsigned k=unsigned(std::min<std::size_t>(path.size(),size-1));for(unsigned i=0;i<k;++i)runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(path[i]));runtime.memory().store<unsigned char>({a+k},0);
   if(path.size()>=size){host.last_error=ERROR_INSUFFICIENT_BUFFER;return done(size,3);}host.last_error=0;return done(k,3);}
  if(n=="GetVersion"){DWORD v{};{LastError l(host);v=::GetVersion();}return done(v,0);}
  if(n=="GetCurrentThreadId"){return done(cur_tid(),0);}
  // Normal process termination: DLL_PROCESS_DETACH (lpReserved non-zero) runs natively for every loaded module
  // in reverse initialization order, MSVCRT last; then the host process exits with the game's exit code.
  if(n=="ExitProcess"){const unsigned code=arg(0);if(host.thread_tid)deny("ExitProcess from a secondary guest thread is not modelled",code);std::string detached;
   for(auto it=host.modules.rbegin();it!=host.modules.rend();++it)if(it->attached&&it->entry!=it->base){if(!find(it->entry))deny("Module entry has no lifted body: "+it->name,it->entry);
    (void)call_guest(it->entry,{it->base,DLL_PROCESS_DETACH,1},true,it->name+" DLL_PROCESS_DETACH");detached+=" "+it->name;}
   if(!find(msvcrt_entry))deny("MSVCRT entry has no lifted body",msvcrt_entry);(void)call_guest(msvcrt_entry,{msvcrt_base,DLL_PROCESS_DETACH,1},true,"MSVCRT DLL_PROCESS_DETACH");detached+=" MSVCRT.DLL";
   std::cerr<<"process exit: ExitProcess("<<code<<") after native shutdown; DLL_PROCESS_DETACH:"<<detached<<"; bodies="<<bodies<<" services="<<(apis_dropped+apis.size())<<" frames="<<host.frames<<"\n";
   std::cout<<"process exit: ExitProcess("<<code<<")\n";std::cout.flush();std::cerr.flush();host.presenter.reset();host.renderer.reset();std::exit(int(code));}
  // The guest's unhandled-exception filter lives in the guest runtime model registered by MSVCRT attach (the
  // host process filter is untouched); the API returns the previous guest filter.
  if(n=="SetUnhandledExceptionFilter"){const unsigned prev=heap.unhandled_filter,f=arg(0);if(f&&!find(f))deny("Unhandled-exception filter without a lifted body",f);heap.unhandled_filter=f;
   char hx[24];std::snprintf(hx,sizeof hx,"(%x -> %x)",prev,f);apis.back()+=hx;return done(prev,1);}
  if(host.thread_tid&&(n=="PeekMessageA"||n=="GetMessageA"||n=="DispatchMessageA"||n=="SendMessageA"||n=="MsgWaitForMultipleObjects"))deny(n+" inside a secondary guest thread: per-thread message queues are not modelled",host.thread_tid);
  if(n=="TlsAlloc"){DWORD t{};{LastError l(host);t=::TlsAlloc();}if(t!=TLS_OUT_OF_INDEXES){if(t>=0x80000000U)deny("Host TLS index not representable",t);host.tls.push_back(t);}return done(t,0);}
  if(n=="TlsFree"){const unsigned t=arg(0);auto it=std::find(host.tls.begin(),host.tls.end(),t);const bool crt_slot=crt&&t==heap.tls&&!heap.tls_freed;if(it==host.tls.end()&&!crt_slot)deny("TlsFree of an index not allocated by the guest",t);
   BOOL ok{};{LastError l(host);ok=::TlsFree(t);}if(ok){if(it!=host.tls.end())host.tls.erase(it);else heap.tls_freed=true;host.tls_shadow[t]=0;}return done(ok?1U:0U,1);}
  if((n=="TlsSetValue"||n=="TlsGetValue")&&host.tls_shadow.count(arg(0))){auto&v=host.tls_shadow[arg(0)];host.last_error=0;if(n=="TlsGetValue")return done(v,1);v=arg(1);return done(1,2);}
  if(n=="TlsSetValue"||n=="TlsGetValue"){const unsigned t=arg(0);if(std::find(host.tls.begin(),host.tls.end(),t)==host.tls.end()&&!(crt&&t==heap.tls&&!heap.tls_freed))deny("TLS index not allocated by its importing module",t);
   if(n=="TlsSetValue"){BOOL ok{};{LastError l(host);ok=::TlsSetValue(t,reinterpret_cast<void*>(std::uintptr_t(arg(1))));}return done(ok?1U:0U,2);}
   void*v{};{LastError l(host);v=::TlsGetValue(t);}const auto x=reinterpret_cast<std::uintptr_t>(v);if(x>0xffffffffU)deny("TLS value not a guest word",t);return done(unsigned(x),1);}
  if(n=="InitializeCriticalSection"){const unsigned cs=arg(0);if(!writable(cs,24)||heap.lock(cs))deny("InitializeCriticalSection on a fresh guest object inside the contract required",cs);
   auto native=std::make_unique<CRITICAL_SECTION>();::InitializeCriticalSection(native.get());const auto debug=reinterpret_cast<std::uintptr_t>(native->DebugInfo);
   if((debug&&debug!=~std::uintptr_t{})||native->RecursionCount||native->OwningThread||native->LockSemaphore)deny("Host critical-section initial fields not representable in the guest object",cs);
   const std::array<unsigned,6>fields{debug?0xffffffffU:0U,static_cast<unsigned>(native->LockCount),0,0,0,static_cast<unsigned>(native->SpinCount)};for(unsigned i=0;i<6;++i)store(cs+4*i,fields[i]);heap.locks.emplace_back(cs,std::move(native));return done(0,1);}
  if(n=="DeleteCriticalSection"){const unsigned cs=arg(0);for(auto it=heap.locks.begin();it!=heap.locks.end();++it)if(it->first==cs){::DeleteCriticalSection(it->second.get());heap.locks.erase(it);return done(0,1);}deny("DeleteCriticalSection on a guest object without a real host section",cs);}
  if(n=="EnterCriticalSection"||n=="LeaveCriticalSection"){const unsigned cs=arg(0);auto*native=heap.lock(cs);if(!native)deny("Enter/LeaveCriticalSection on a guest object without a real host section",cs);
   if(n=="EnterCriticalSection")::EnterCriticalSection(native);else ::LeaveCriticalSection(native);
   store(cs+4,static_cast<unsigned>(native->LockCount));store(cs+8,static_cast<unsigned>(native->RecursionCount));store(cs+12,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(native->OwningThread)));return done(0,1);}
  if(n=="GlobalAlloc"){const unsigned flags=arg(0),bytes=arg(1);if(flags&~(GMEM_MOVEABLE|GMEM_ZEROINIT|GMEM_SHARE))deny("GlobalAlloc flags outside the modelled set",flags);
   HGLOBAL h{};{LastError l(host);h=::GlobalAlloc(flags,bytes);}if(!h)return done(0,2);
   void*q{};{LastError l(host);q=::GlobalLock(h);}if(!q)deny("Real GlobalLock of a fresh block failed",bytes);const unsigned guest=pages(q,bytes);{LastError l(host);::GlobalUnlock(h);}
   const unsigned handle=(flags&GMEM_MOVEABLE)?0x34000000U+8U*unsigned(host.globals.size()+1):guest;host.globals.push_back({handle,guest,bytes,flags,h,0,false});return done(handle,2);}
  if(n=="GlobalLock"||n=="GlobalUnlock"||n=="GlobalSize"||n=="GlobalFree"){auto*b=host.global(arg(0));if(!b)deny(n+" of a handle that is not a live GlobalAlloc block",arg(0));
   if(n=="GlobalLock"){void*q{};{LastError l(host);q=::GlobalLock(b->native);}if(!q)return done(0,1);++b->locks;return done(b->guest,1);}
   if(n=="GlobalUnlock"){if(!b->locks)deny("GlobalUnlock of an unlocked block",arg(0));BOOL r{};{LastError l(host);r=::GlobalUnlock(b->native);}--b->locks;return done(r?1U:0U,1);}
   if(n=="GlobalSize"){SIZE_T z{};{LastError l(host);z=::GlobalSize(b->native);}if(z!=b->bytes)deny("Real GlobalSize differs from the guest block",arg(0));return done(unsigned(z),1);}
   while(b->locks){::GlobalUnlock(b->native);--b->locks;}HGLOBAL r{};{LastError l(host);r=::GlobalFree(b->native);}if(r)deny("Real GlobalFree failed",arg(0));b->freed=true;release(b->guest);return done(0,1);}
  if(n=="GlobalHandle"){for(auto&b:host.globals)if(!b.freed&&b.guest==arg(0))return done(b.handle,1);deny("GlobalHandle of a pointer that is not a live GlobalAlloc block",arg(0));}
  if(n=="GlobalReAlloc"){auto*b=host.global(arg(0));const unsigned bytes=arg(1),flags=arg(2);if(!b)deny("GlobalReAlloc of a handle that is not a live GlobalAlloc block",arg(0));
   if(flags&~(GMEM_MOVEABLE|GMEM_ZEROINIT|GMEM_SHARE)||!(b->flags&GMEM_MOVEABLE)||b->locks)deny("GlobalReAlloc outside the modelled unlocked moveable resize",flags);
   HGLOBAL h{};{LastError l(host);h=::GlobalReAlloc(b->native,bytes,flags);}if(!h)return done(0,3);
   auto old=guest_bytes(b->guest,std::min(b->bytes,bytes));old.resize(bytes);release(b->guest);b->native=h;b->guest=pages(old.data(),bytes);b->bytes=bytes;return done(b->handle,3);}
  // MSVCRT's _heap_term: the CRT heap ends with its real host heap, the guest pages of its blocks and the guest
  // heap manager's blocks (allocated on the CRT heap's behalf after the hand-off).
  if(crt&&n=="HeapDestroy"){if(arg(0)!=hs::token||!heap.handle)deny("HeapDestroy of a heap other than the real CRT heap",arg(0));BOOL ok{};{LastError l(host);ok=::HeapDestroy(heap.handle);}
   if(ok){for(auto&b:heap.blocks)if(!b.freed){b.freed=true;release(b.guest);}heap.handle=nullptr;const auto live=host.gheap.destroy(hs::token);
    apis.back()+="(CRT heap destroyed; guest heap blocks ended: "+std::to_string(live)+")";}return done(ok?1U:0U,1);}
  if(crt&&(n=="HeapAlloc"||n=="HeapFree"||n=="HeapSize"||n=="HeapReAlloc")){if(arg(0)!=hs::token||!heap.handle)deny(n+" on a heap other than the real CRT heap",arg(0));
   auto block=[&](unsigned ptr)->hs::HostHeap::Block*{for(auto&b:heap.blocks)if(!b.freed&&b.guest==ptr)return &b;deny(n+" of a pointer that is not a live real CRT heap block",ptr);};
   if(n=="HeapAlloc"){const unsigned flags=arg(1),bytes=arg(2);if(flags&~HEAP_ZERO_MEMORY)deny("HeapAlloc flags outside the modelled set",flags);const unsigned g2=gheap_alloc(bytes,flags&HEAP_ZERO_MEMORY,hs::token);if(!g2)host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(g2,3);}
   if(host.gheap.live.count(arg(2))){const unsigned ptr=arg(2);if(host.gheap.owner_of(ptr)!=hs::token)deny(n+" of a block owned by another guest heap",ptr);
    if(n=="HeapSize"){if(arg(1))deny("HeapSize flags",arg(1));return done(host.gheap.live[ptr],3);}
    if(n=="HeapFree"){if(arg(1))deny("HeapFree flags",arg(1));gheap_free(ptr);return done(1,3);}
    const unsigned flags=arg(1),bytes=arg(3);if(flags&~HEAP_ZERO_MEMORY)deny("HeapReAlloc flags outside the modelled set",flags);const unsigned old=host.gheap.live[ptr];const unsigned g2=gheap_alloc(bytes,flags&HEAP_ZERO_MEMORY,hs::token);if(!g2)return done(0,4);
    std::vector<std::byte>v(std::min(old,bytes));if(!v.empty()){runtime.memory().read({ptr},v);runtime.memory().write({g2},v);}gheap_free(ptr);return done(g2,4);}
   auto*b=block(arg(2));
   if(n=="HeapSize"){if(arg(1))deny("HeapSize flags",arg(1));SIZE_T z{};{LastError l(host);z=::HeapSize(heap.handle,0,b->native);}return done(unsigned(z),3);}
   if(n=="HeapFree"){if(arg(1))deny("HeapFree flags",arg(1));BOOL ok{};{LastError l(host);ok=::HeapFree(heap.handle,0,b->native);}b->freed=true;release(b->guest);return done(ok?1U:0U,3);}
   const unsigned flags=arg(1),bytes=arg(3);if(flags&~HEAP_ZERO_MEMORY)deny("HeapReAlloc flags outside the modelled set",flags);void*q{};{LastError l(host);q=::HeapReAlloc(heap.handle,flags,b->native,bytes);}if(!q)return done(0,4);
   auto old=guest_bytes(b->guest,std::min(b->bytes,bytes));old.resize(bytes);release(b->guest);b->native=q;b->guest=pages(old.data(),bytes);b->bytes=bytes;return done(b->guest,4);}
  if(n=="GetLastError")return done(host.last_error,0);
  if(n=="SetLastError"){host.last_error=arg(0);return done(0,1);}
  // Handles of the real window station/GDI are 32-bit significant; anything else stops, never truncates.
  auto ghandle=[&](const void*h){const auto v=reinterpret_cast<std::intptr_t>(h);if(v!=std::intptr_t(std::int32_t(v)))deny(n+" returned a handle not representable as a guest word",0);return unsigned(v);};
  auto hhandle=[&](unsigned v){return reinterpret_cast<HANDLE>(std::intptr_t(std::int32_t(v)));};
  // Interlocked operations on guest words: the guest runs on one host thread inside one Stage, so a
  // contract-checked read-modify-write is the exact atomic result.
  if(n.rfind("Interlocked",0)==0){const unsigned a=arg(0);if(a%4||!writable(a,4))deny(n+" target outside the memory contract",a);const unsigned old=load(a);
   if(n=="InterlockedExchange"){store(a,arg(1));return done(old,2);}
   if(n=="InterlockedIncrement"){store(a,old+1);return done(old+1,1);}
   if(n=="InterlockedDecrement"){store(a,old-1);return done(old-1,1);}
   if(n=="InterlockedExchangeAdd"){store(a,old+arg(1));return done(old,2);}
   if(n=="InterlockedCompareExchange"){if(old==arg(2))store(a,arg(1));return done(old,3);}}
  // Loader state: the module asks for no DLL_THREAD_ATTACH/DETACH notifications.
  if(n=="DisableThreadLibraryCalls"){for(auto&m:host.modules)if(m.base==arg(0)){m.thread_calls_disabled=true;host.last_error=0;return done(1,1);}deny("DisableThreadLibraryCalls on a module outside the loader model",arg(0));}
  // Registry: the real host registry (32-bit view) is read only; the game's own writes go to a per-install
  // overlay persisted in the game folder (mw34-registry.txt), consulted before the real registry. The host
  // registry is never modified. Key handles are guest tokens naming a path and, when the real key exists, a
  // read-only real handle. Statuses follow Win32 (ERROR_FILE_NOT_FOUND, ERROR_MORE_DATA, dispositions).
  auto& ov=reg_overlay();
  auto keyof=[&](unsigned v)->Host::VKey*{for(auto&k:host.vkeys)if(k.guest==v)return &k;return nullptr;};
  auto rootname=[&](unsigned v)->std::string{switch(v){case 0x80000000U:return "hkcr";case 0x80000001U:return "hkcu";case 0x80000002U:return "hklm";case 0x80000003U:return "hku";case 0x80000005U:return "hkcc";default:return {};}};
  auto parent_path=[&](unsigned v)->std::string{const std::string r=rootname(v);if(!r.empty())return r;if(auto*k=keyof(v))return k->path;deny(n+" on a key handle the guest does not own",v);};
  auto parent_real=[&](unsigned v)->HKEY{if(!rootname(v).empty())return reinterpret_cast<HKEY>(std::intptr_t(std::int32_t(v)));auto*k=keyof(v);return k?k->real:nullptr;};
  auto join=[&](std::string p,const std::string&sub){std::string q=sub;std::replace(q.begin(),q.end(),'/','\\');while(!q.empty()&&q.back()=='\\')q.pop_back();while(!q.empty()&&q.front()=='\\')q.erase(q.begin());
   for(auto&c:q)c=char(std::tolower(static_cast<unsigned char>(c)));return q.empty()?p:p+"\\"+q;};
  auto ov_has_key=[&](const std::string&p){if(ov.keys.count(p))return true;auto it=ov.keys.lower_bound(p+"\\");return it!=ov.keys.end()&&it->first.compare(0,p.size()+1,p+"\\")==0;};
  auto open_key=[&](unsigned parent,const std::string&sub,bool create,unsigned out,unsigned disp)->LONG{const std::string p=join(parent_path(parent),sub);HKEY real{};LONG rc=ERROR_FILE_NOT_FOUND;
   if(HKEY pr=parent_real(parent))rc=::RegOpenKeyExA(pr,sub.c_str(),0,KEY_READ|KEY_WOW64_32KEY,&real);if(rc!=ERROR_SUCCESS)real=nullptr;
   const bool existed=real||ov_has_key(p);if(!existed&&!create)return rc==ERROR_SUCCESS?LONG(ERROR_FILE_NOT_FOUND):rc;
   if(!existed){ov.keys[p];save_reg_overlay();}const unsigned g=0x3e000000U+16U*(++host.vkey_serial);host.vkeys.push_back({g,p,real});store(out,g);
   if(disp){if(!writable(disp,4))deny(n+" disposition outside the memory contract",disp);store(disp,existed?REG_OPENED_EXISTING_KEY:REG_CREATED_NEW_KEY);}
   apis.back()+="("+p+(existed?"":", created in overlay")+(real?", host":"")+")";return ERROR_SUCCESS;};
  if(n=="RegOpenKeyExA"||n=="RegOpenKeyA"){const bool ex=n=="RegOpenKeyExA";const std::string sub=arg(1)?guest_string(arg(1)):std::string();const unsigned out=ex?arg(4):arg(2);if(!writable(out,4))deny(n+" output outside the memory contract",out);
   return done(unsigned(open_key(arg(0),sub,false,out,0)),ex?5:3);}
  if(n=="RegCreateKeyExA"||n=="RegCreateKeyA"){const bool ex=n=="RegCreateKeyExA";const std::string sub=arg(1)?guest_string(arg(1)):std::string();const unsigned out=ex?arg(7):arg(2);if(!writable(out,4))deny(n+" output outside the memory contract",out);
   if(ex&&(arg(4)&REG_OPTION_VOLATILE))deny("Volatile registry keys are not modelled",arg(4));return done(unsigned(open_key(arg(0),sub,true,out,ex?arg(8):0)),ex?9:3);}
  if(n=="RegSetValueExA"){auto*k=keyof(arg(0));if(!k)deny("RegSetValueExA on a key handle the guest does not own (root keys are not written)",arg(0));std::string v=arg(1)?guest_string(arg(1)):std::string();for(auto&c:v)c=char(std::tolower(static_cast<unsigned char>(c)));
   const unsigned type=arg(3),data=arg(4),cb=arg(5);if(cb>1048576||(cb&&!readable(data,cb)))deny("RegSetValueExA data outside the memory contract",data);std::vector<BYTE>b(cb);if(cb)get_bytes(data,b.data(),cb);
   ov.keys[k->path][v]={type,std::move(b)};save_reg_overlay();apis.back()+="("+k->path+"\\"+v+", overlay)";return done(ERROR_SUCCESS,6);}
  if(n=="RegQueryValueExA"){auto*k=keyof(arg(0));const std::string path=k?k->path:parent_path(arg(0));std::string v=arg(1)?guest_string(arg(1)):std::string();std::string lv=v;for(auto&c:lv)c=char(std::tolower(static_cast<unsigned char>(c)));
   const unsigned type=arg(3),data=arg(4),size=arg(5);LONG rc{};DWORD t{},cb=size?load(size):0;std::vector<BYTE>buf;const std::vector<BYTE>*src=nullptr;
   if(auto ki=ov.keys.find(path);ki!=ov.keys.end())if(auto vi=ki->second.find(lv);vi!=ki->second.end()){if(vi->second.first==Host::RegOverlay::deleted)rc=ERROR_FILE_NOT_FOUND;else{t=vi->second.first;src=&vi->second.second;}}
   if(src){const DWORD need=DWORD(src->size());if(data&&cb<need)rc=ERROR_MORE_DATA;else{rc=ERROR_SUCCESS;if(data)buf=*src;}cb=need;apis.back()+="("+v+", overlay)="+std::to_string(rc);}
   else if(rc!=ERROR_FILE_NOT_FOUND){HKEY real=k?k->real:parent_real(arg(0));if(!real)rc=ERROR_FILE_NOT_FOUND;else{buf.resize(cb);rc=::RegQueryValueExA(real,v.c_str(),nullptr,&t,data?buf.data():nullptr,size?&cb:nullptr);}apis.back()+="("+v+")="+std::to_string(rc);}
   if(type&&rc==ERROR_SUCCESS){if(!writable(type,4))deny("RegQueryValueExA type outside the memory contract",type);store(type,t);}
   if(rc==ERROR_SUCCESS&&data){if(!writable(data,cb))deny("RegQueryValueExA data outside the memory contract",data);for(DWORD i=0;i<cb;++i)runtime.memory().store<unsigned char>({data+i},buf[i]);}
   if(size&&(rc==ERROR_SUCCESS||rc==ERROR_MORE_DATA))store(size,cb);return done(unsigned(rc),6);}
  if(n=="RegDeleteValueA"){auto*k=keyof(arg(0));if(!k)deny("RegDeleteValueA on a key handle the guest does not own",arg(0));std::string v=arg(1)?guest_string(arg(1)):std::string();for(auto&c:v)c=char(std::tolower(static_cast<unsigned char>(c)));
   bool present=false;if(auto ki=ov.keys.find(k->path);ki!=ov.keys.end())if(auto vi=ki->second.find(v);vi!=ki->second.end())present=vi->second.first!=Host::RegOverlay::deleted;
   if(!present&&k->real)present=::RegQueryValueExA(k->real,v.c_str(),nullptr,nullptr,nullptr,nullptr)==ERROR_SUCCESS;if(!present)return done(ERROR_FILE_NOT_FOUND,2);
   ov.keys[k->path][v]={Host::RegOverlay::deleted,{}};save_reg_overlay();return done(ERROR_SUCCESS,2);}
  if(n=="RegCloseKey"){const unsigned g=arg(0);if(!rootname(g).empty())return done(ERROR_SUCCESS,1);auto it=std::find_if(host.vkeys.begin(),host.vkeys.end(),[&](const auto&k){return k.guest==g;});if(it==host.vkeys.end())deny("RegCloseKey of a key the guest does not own",g);
   if(it->real)::RegCloseKey(it->real);host.vkeys.erase(it);return done(ERROR_SUCCESS,1);}
  if(n.rfind("RegCreateKey",0)==0||n.rfind("RegSetValue",0)==0||n.rfind("RegDelete",0)==0)deny(n+" would modify the host registry; not authorized",0);
  if(n=="GetVersionExA"){const unsigned a=arg(0);if(!writable(a,4))deny("GetVersionExA buffer outside the memory contract",a);const unsigned size=load(a);
   if(size!=sizeof(OSVERSIONINFOA)&&size!=sizeof(OSVERSIONINFOEXA)){host.last_error=ERROR_INSUFFICIENT_BUFFER;return done(0,1);}if(!writable(a,size))deny("GetVersionExA buffer outside the memory contract",a);
   OSVERSIONINFOEXA v{};v.dwOSVersionInfoSize=size;BOOL ok{};{LastError l(host);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    ok=::GetVersionExA(reinterpret_cast<OSVERSIONINFOA*>(&v));
#pragma clang diagnostic pop
   }if(ok)for(unsigned i=0;i<size;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&v)[i]);return done(ok?1U:0U,1);}
  if(imp->dll=="DSOUND.dll"&&n=="#1"){const unsigned guid=arg(0),out=arg(1),outer=arg(2);if(guid||outer)deny("DirectSoundCreate with a device GUID or aggregation is not modelled",guid|outer);
   if(!writable(out,4))deny("DirectSoundCreate output outside the memory contract",out);auto&d=dsound();LPDIRECTSOUND ds{};const HRESULT hr=d.create(nullptr,&ds,nullptr);apis.back()+="="+std::to_string(unsigned(hr));
   store(out,SUCCEEDED(hr)&&ds?com_wrap(ds,*com::by_name("IDirectSound")):0);return done(unsigned(hr),3);}
  // DirectDrawEnumerateA on the real provider; each driver is passed to the guest callback (GUID copy
  // or NULL, description and name strings in guest scratch memory) as a nested stdcall.
  if(same(imp->dll,"DDRAW.DLL")&&n=="DirectDrawEnumerateA"){const unsigned cb=arg(0),ctx=arg(1);if(!find(cb))deny("DirectDrawEnumerateA callback has no lifted body",cb);auto&d=ddraw();
   auto en=reinterpret_cast<HRESULT(WINAPI*)(LPDDENUMCALLBACKA,LPVOID)>(::GetProcAddress(d.module,"DirectDrawEnumerateA"));if(!en)deny("Provider DirectDrawEnumerateA export",0);
   struct Ctx{Stage*st;unsigned cb,ctx,calls;};Ctx c{this,cb,ctx,0};
   auto tramp=+[](GUID*g,LPSTR desc,LPSTR name,LPVOID p)->BOOL{auto&c=*static_cast<Ctx*>(p);auto&st=*c.st;if(!st.callback_fault.empty())return FALSE;
    try{unsigned at=(st.state.gpr.rsp.dword-0x200)&~15U;unsigned gg=0;if(g){at-=16;std::array<unsigned,4>w{};std::memcpy(w.data(),g,16);for(unsigned i=0;i<4;++i)st.store(at+4*i,w[i]);gg=at;}
     const unsigned gd=st.scratch_string(at,desc),gn=st.scratch_string(at,name);++c.calls;return BOOL(st.call_guest(c.cb,{gg,gd,gn,c.ctx},true,"DirectDrawEnumerateA callback",at&~15U));}
    catch(const std::exception&e){st.callback_fault=e.what();return FALSE;}};
   const HRESULT hr=en(tramp,&c);apis.back()+="("+std::to_string(c.calls)+" drivers)="+std::to_string(unsigned(hr));return done(unsigned(hr),2);}
  if(same(imp->dll,"DINPUT.dll")&&n=="DirectInputCreateA"){const unsigned ver=arg(1),out=arg(2);if(arg(3))deny("DirectInputCreateA aggregation is not modelled",arg(3));if(!writable(out,4))deny("DirectInputCreateA output outside the memory contract",out);
   auto&d=dinput();LPDIRECTINPUTA di{};const HRESULT hr=d.create(::GetModuleHandleW(nullptr),ver,&di,nullptr);apis.back()+="(version "+std::to_string(ver)+")="+std::to_string(unsigned(hr));store(out,SUCCEEDED(hr)&&di?com_wrap(di,*com::by_name("IDirectInputA")):0);return done(unsigned(hr),4);}
  if(same(imp->dll,"DDRAW.DLL")&&n=="DirectDrawCreate"){const unsigned guid=arg(0),out=arg(1),outer=arg(2);if(guid||outer)deny("DirectDrawCreate with a device GUID or aggregation is not modelled",guid|outer);
   if(!writable(out,4))deny("DirectDrawCreate output outside the memory contract",out);auto&d=ddraw();LPDIRECTDRAW dd{};const HRESULT hr=d.create(nullptr,&dd,nullptr);apis.back()+="="+std::to_string(unsigned(hr));
   store(out,SUCCEEDED(hr)&&dd?com_wrap(dd,*com::by_name("IDirectDraw")):0);return done(unsigned(hr),3);}
  // DirectPlayLobbyCreateA (DPLAYX ordinal 4): project-implemented lobby object. This process was not
  // launched by a DirectPlay lobby, so GetConnectionSettings reports DPERR_NOTLOBBIED, as DirectPlay does.
  if(imp->dll=="DPLAYX.dll"&&n=="#4"){const unsigned guid=arg(0),out=arg(1),outer=arg(2);if(guid||outer||arg(3)||arg(4))deny("DirectPlayLobbyCreateA with a GUID, aggregation or data is not modelled",guid|outer);
   if(!writable(out,4))deny("DirectPlayLobbyCreateA output outside the memory contract",out);const unsigned g2=com_wrap(nullptr,*com::by_name("IDirectPlayLobbyA"));host.com_object(g2)->refs=1;store(out,g2);return done(0,5);}
  com_dispatch:
  if(const auto*ci=static_cast<const com::Iface*>(imp->iface_cache);ci&&com::is_lobby(ci)){auto*o=host.com_object(arg(0));if(!o||o->iface!=ci)deny("COM call on a guest object that is not a live "+imp->dll,arg(0));const unsigned root=root_of(*o);
   auto refs=[&]()->unsigned&{return host.com_object(root)?host.com_object(root)->refs:o->refs;};
   if(n=="AddRef")return done(++refs(),1);
   if(n=="Release"){const unsigned c=--refs();if(!c)for(auto&x:host.com_objects)if(x.alive&&root_of(x)==root)x.alive=false;return done(c,1);}
   if(n=="QueryInterface"){const GUID g=guest_guid(arg(1));const unsigned out=arg(2);if(!writable(out,4))deny("QueryInterface output outside the memory contract",out);const auto*wi=com::by_iid(g);
    if(!wi||!com::is_lobby(wi))deny("DirectPlay lobby QueryInterface for an interface outside the model",arg(1));++refs();store(out,com_wrap(nullptr,*wi,root));return done(0,3);}
   if(n=="GetConnectionSettings"){apis.back()+="=DPERR_NOTLOBBIED";return done(com::dperr_notlobbied,4);}
   stop(m4_runtime::FaultReason::unresolved_import,"DirectPlay lobby method not implemented: "+imp->dll+"::"+n,token);}
  if(const auto*ci=static_cast<const com::Iface*>(imp->iface_cache)){auto*o=host.com_object(arg(0));if(!o||o->iface!=ci)deny("COM call on a guest object that is not a live "+imp->dll,arg(0));
   const std::function<unsigned(unsigned)>argf=arg;const std::function<void*(unsigned,unsigned)>donef=done;
   if(!o->native&&imp->dll.find("Surface")!=std::string::npos)return vdd_surface(*imp,token,argf,donef);
   if(!o->native&&(imp->dll=="IDirectDrawClipper"||imp->dll=="IDirectDrawPalette"))return vdd_aux(*imp,token,argf,donef);
   if(!o->native&&com::is_d3d(ci))return d3d_call(*imp,token,argf,donef);
   // The Direct3D3 provider answers QueryInterface(IID_IDirect3D3) on every DirectDraw object.
   if(o->native&&n=="QueryInterface"&&com::is_dd(ci)&&IsEqualGUID(guest_guid(arg(1)),IID_IDirect3D3))return d3d_query(*o,arg(2),donef);
   if(n=="AddRef"){++o->refs;return done(o->native->AddRef(),1);}
   if(n=="Release"){if(!o->refs)deny("Release of a proxy whose references are already released",arg(0));const ULONG c=o->native->Release();apis.back()+="="+std::to_string(c);if(!--o->refs&&c){o->alive=false;o->native=nullptr;}if(!c){o->alive=false;o->native=nullptr;
     auto parent=[](const com::Iface*i){return com::is_dd(i)||std::string(i->name)=="IDirectSound";};
     if(parent(o->iface)){const unsigned root=root_of(*o);bool any=false;for(const auto&x:host.com_objects)if(x.alive&&parent(x.iface)&&root_of(x)==root)any=true;
      if(!any)for(auto&x:host.com_objects)if(x.alive&&root_of(x)==root){x.alive=false;x.native=nullptr;}}}  // last DirectDraw interface: its surfaces go with it
     return done(c,1);}
   if(n=="QueryInterface"){const GUID g=guest_guid(arg(1));const unsigned out=arg(2);if(!writable(out,4))deny("QueryInterface output outside the memory contract",out);
    void*q{};const HRESULT hr=o->native->QueryInterface(g,&q);apis.back()+="="+std::to_string(unsigned(hr));
    if(SUCCEEDED(hr)&&q){const auto*wi=com::by_iid(g);if(!wi){static_cast<IUnknown*>(q)->Release();deny("QueryInterface succeeded for an interface without a guest proxy model",arg(1));}store(out,com_wrap(static_cast<IUnknown*>(q),*wi,root_of(*o)));}
    else store(out,0);return done(unsigned(hr),3);}
   const bool is_dd=imp->dll.rfind("IDirectDraw",0)==0&&imp->dll.find("Surface")==std::string::npos;
   if(is_dd&&host.display.exclusive&&n=="CreateSurface"){if(arg(3))deny("CreateSurface aggregation is not modelled",arg(3));return vdd_create_surface(arg(2),arg(1),imp->dll=="IDirectDraw4"?124U:108U,donef);}
   if(is_dd&&host.display.exclusive&&n=="CreateClipper"){if(arg(1)||arg(3))deny("CreateClipper flags/aggregation are not modelled",arg(1));if(!writable(arg(2),4))deny("CreateClipper output outside the memory contract",arg(2));
    const unsigned g=com_wrap(nullptr,*com::by_name("IDirectDrawClipper"));host.com_object(g)->refs=1;host.clippers[g]=0;store(arg(2),g);return done(DD_OK,4);}
   if(is_dd&&host.display.exclusive&&n=="CreatePalette"){const unsigned fl=arg(1),ent=arg(2),out=arg(3);if(arg(4))deny("CreatePalette aggregation is not modelled",arg(4));if(!(fl&DDPCAPS_8BIT))deny("Only 8-bit palettes are modelled",fl);
    if(!readable(ent,1024)||!writable(out,4))deny("CreatePalette arguments outside the memory contract",ent);const unsigned g=com_wrap(nullptr,*com::by_name("IDirectDrawPalette"));host.com_object(g)->refs=1;VPaletteRec pr{g,{},fl};get_bytes(ent,pr.entries,1024);host.vpalettes.push_back(pr);store(out,g);return done(DD_OK,5);}
   if(imp->dll=="IDirectInputA"){auto*di=reinterpret_cast<IDirectInputA*>(o->native);
    if(n=="CreateDevice"){const GUID g=guest_guid(arg(1));const unsigned out=arg(2);if(controller_requested()&&!IsEqualGUID(g,GUID_SysKeyboard)&&!IsEqualGUID(g,GUID_SysMouse)){if(!writable(out,4))deny("Controller CreateDevice output outside memory contract",out);store(out,0);return done(unsigned(DIERR_DEVICENOTREG),4);}if(arg(3))deny("CreateDevice aggregation is not modelled",arg(3));if(!writable(out,4))deny("CreateDevice output outside the memory contract",out);
     LPDIRECTINPUTDEVICEA dev{};const HRESULT hr=di->CreateDevice(g,&dev,nullptr);apis.back()+="="+std::to_string(unsigned(hr));store(out,SUCCEEDED(hr)&&dev?com_wrap(dev,*com::by_name("IDirectInputDeviceA"),root_of(*o)):0);return done(unsigned(hr),4);}
    if(n=="EnumDevices"){const unsigned type=arg(1),cb=arg(2),ctx=arg(3),fl=arg(4);if(!find(cb))deny("EnumDevices callback has no lifted body",cb);static_assert(sizeof(DIDEVICEINSTANCEA)==580);
     struct C{Stage*st;unsigned cb,ctx,calls;};C c{this,cb,ctx,0};
     const HRESULT hr=di->EnumDevices(type,[](LPCDIDEVICEINSTANCEA d,LPVOID p)->BOOL{auto&c=*static_cast<C*>(p);auto&st=*c.st;if(!st.callback_fault.empty())return DIENUM_STOP;
       if(st.controller_requested()&&(d->dwDevType&0xff)==DIDEVTYPE_JOYSTICK)return DIENUM_CONTINUE;
       try{const unsigned at=((st.state.gpr.rsp.dword-0x200)&~15U)-580;const auto*b=reinterpret_cast<const unsigned char*>(d);for(unsigned i=0;i<580;++i)st.runtime.memory().store<unsigned char>({at+i},b[i]);st.store(at,580);++c.calls;
        return BOOL(st.call_guest(c.cb,{at,c.ctx},true,"DirectInput EnumDevices callback",at&~15U));}catch(const std::exception&e){st.callback_fault=e.what();return DIENUM_STOP;}},&c,fl);
     apis.back()+="("+std::to_string(c.calls)+" devices)="+std::to_string(unsigned(hr));return done(unsigned(hr),5);}}
   if(imp->dll=="IDirectInputDeviceA"||imp->dll=="IDirectInputDevice2A"){auto*dv=reinterpret_cast<IDirectInputDeviceA*>(o->native);
    if(n=="SetCooperativeLevel"){const HRESULT hr=dv->SetCooperativeLevel(hwnd_of(arg(1)),arg(2));apis.back()+="("+std::to_string(arg(2))+")="+std::to_string(unsigned(hr));return done(unsigned(hr),3);}
    if(n=="SetDataFormat"){const unsigned a=arg(1);if(!readable(a,24)||load(a)!=24||load(a+4)!=16)deny("DIDATAFORMAT outside the contract or with a wrong size",a);const unsigned cnt=load(a+16),objs=load(a+20);if(cnt>512||!readable(objs,16*cnt))deny("DIDATAFORMAT objects outside the memory contract",objs);
     std::vector<GUID>guids(cnt);std::vector<DIOBJECTDATAFORMAT>od(cnt);for(unsigned i=0;i<cnt;++i){const unsigned pg=load(objs+16*i);if(pg)guids[i]=guest_guid(pg);od[i].pguid=pg?&guids[i]:nullptr;od[i].dwOfs=load(objs+16*i+4);od[i].dwType=load(objs+16*i+8);od[i].dwFlags=load(objs+16*i+12);}
     DIDATAFORMAT f{sizeof(DIDATAFORMAT),sizeof(DIOBJECTDATAFORMAT),load(a+8),load(a+12),cnt,od.data()};const HRESULT hr=dv->SetDataFormat(&f);if(SUCCEEDED(hr))host.di_format[arg(0)]=load(a+12);apis.back()+="("+std::to_string(cnt)+" objects,"+std::to_string(load(a+12))+" bytes)="+std::to_string(unsigned(hr));return done(unsigned(hr),2);}
    if(host.scripted&&(n=="Poll"||n=="Acquire")&&host.di_format.count(arg(0))){apis.back()+="(scripted)";return done(0,1);}
    if(n=="Acquire")return done(unsigned(dv->Acquire()),1);
    if(n=="Unacquire")return done(unsigned(dv->Unacquire()),1);
    if(n=="Poll"){IDirectInputDevice2A*d2{};if(FAILED(dv->QueryInterface(IID_IDirectInputDevice2A,reinterpret_cast<void**>(&d2)))||!d2)deny("Poll on a device without IDirectInputDevice2A",arg(0));const HRESULT hr=d2->Poll();d2->Release();return done(unsigned(hr),1);}
    if(n=="GetDeviceState"&&host.scripted){const unsigned z=arg(1),a=arg(2);if(!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);
     if(z!=16&&z!=256)deny("Scripted GetDeviceState for a data format outside the model",z);for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},0);
     if(z==16){int dx=0,dy=0;auto&sc=host.script;while(host.script_mouse_at<sc.size()&&(!sc[host.script_mouse_at].mouse||script_due(sc[host.script_mouse_at]))){const auto&e=sc[host.script_mouse_at++];if(e.mouse){dx+=e.dx;dy+=e.dy;host.script_buttons=e.buttons;}}
      store(a,unsigned(dx));store(a+4,unsigned(dy));for(unsigned b=0;b<4;++b)runtime.memory().store<unsigned char>({a+12+b},(host.script_buttons>>b)&1?0x80:0);if(dx||dy)apis.back()+="(scripted "+std::to_string(dx)+","+std::to_string(dy)+" b"+std::to_string(host.script_buttons)+")";}
     if(z==256){auto&sc=host.script;auto&ks=host.script_keys;while(host.script_kstate_at<sc.size()&&(sc[host.script_kstate_at].mouse||script_due(sc[host.script_kstate_at]))){const auto&e=sc[host.script_kstate_at++];if(!e.mouse)ks[e.scan&255]=e.down?0x80:0;}
      headlight_keyboard(256,ks.data());std::string held;for(unsigned i=0;i<256;++i)if(ks[i]){runtime.memory().store<unsigned char>({a+i},ks[i]);char h[8];std::snprintf(h,sizeof h," %02x",i);held+=h;}if(!held.empty())apis.back()+="(scripted keys"+held+")";}
     return done(0,3);}
    if(n=="GetDeviceState"){const unsigned z=arg(1),a=arg(2);if(z>4096||!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);std::vector<unsigned char>b(z);const HRESULT hr=dv->GetDeviceState(z,b.data());headlight_keyboard(z,b.data(),SUCCEEDED(hr));if(SUCCEEDED(hr)){photo_replay_filter_device_state(z,b.data());for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);}return done(unsigned(hr),3);}
    if(n=="GetDeviceData"&&host.scripted){const unsigned z=arg(1),a=arg(2),pn=arg(3),fl=arg(4);if(z!=16||!writable(pn,4))deny("GetDeviceData record size or count outside the model",z);const DWORD cnt=load(pn);if(cnt>4096||(a&&!writable(a,16*cnt)))deny("GetDeviceData buffer outside the memory contract",a);
     if(host.di_format[arg(0)]!=256)deny("Scripted GetDeviceData for a device other than the keyboard",arg(0));auto&sc=host.script;DWORD k=0;size_t at=host.script_key_at;
     while(at<sc.size()&&k<cnt){const auto&e=sc[at];if(e.mouse){++at;continue;}if(!script_due(e))break;if(a){if(headlight_enabled()&&!(fl&DIGDD_PEEK)){headlight_keyboard_valid=true;headlight_keys[e.scan&255]=e.down?0x80:0;}store(a+16*k,e.scan);store(a+16*k+4,e.down?0x80U:0U);store(a+16*k+8,host.vclock()?unsigned(host.vclock_query()/1000):host.guest_tick());store(a+16*k+12,++host.script_seq);}apis.back()+="(scripted key "+std::to_string(e.scan)+(e.down?" down)":" up)");++k;++at;}
     if(!(fl&DIGDD_PEEK))host.script_key_at=at;store(pn,k);return done(0,5);}
    if(n=="GetDeviceData"){const unsigned z=arg(1),a=arg(2),pn=arg(3),fl=arg(4);if(z!=16||!writable(pn,4))deny("GetDeviceData record size or count outside the model",z);DWORD cnt=load(pn);if(cnt>4096||(a&&!writable(a,16*cnt)))deny("GetDeviceData buffer outside the memory contract",a);
     std::vector<DIDEVICEOBJECTDATA_DX3>b(std::max<DWORD>(cnt,1));static_assert(sizeof(DIDEVICEOBJECTDATA_DX3)==16);const HRESULT hr=dv->GetDeviceData(16,a?reinterpret_cast<LPDIDEVICEOBJECTDATA>(b.data()):nullptr,&cnt,fl);
     if(headlight_enabled()&&host.di_format[arg(0)]==256&&a&&!(fl&DIGDD_PEEK)){
      if(SUCCEEDED(hr)){headlight_keyboard_valid=true;for(DWORD k=0;k<cnt;++k)if(b[k].dwOfs<256)headlight_keys[b[k].dwOfs]=static_cast<unsigned char>(b[k].dwData);}
      else{headlight_keyboard_valid=false;headlight_edge={};}}
     if(SUCCEEDED(hr)){photo_replay_filter_device_data(b.data(),cnt);if(a)for(DWORD k=0;k<cnt;++k){b[k].dwTimeStamp=host.guest_tick_of(b[k].dwTimeStamp);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+16*k+i},reinterpret_cast<const unsigned char*>(&b[k])[i]);}store(pn,cnt);}return done(unsigned(hr),5);}
    if(n=="SetProperty"||n=="GetProperty"){const unsigned pg=arg(1),ph=arg(2);GUID gp{};const GUID*rp;if(pg<0x10000)rp=reinterpret_cast<const GUID*>(std::uintptr_t(pg));else{gp=guest_guid(pg);rp=&gp;}
     if(!readable(ph,16)||load(ph+4)!=16)deny(n+" DIPROPHEADER outside the contract",ph);const unsigned z=load(ph);if(z<16||z>256||!(n=="SetProperty"?readable(ph,z):writable(ph,z)))deny(n+" property outside the memory contract",ph);
     std::vector<unsigned char>b(z);get_bytes(ph,b.data(),z);const HRESULT hr=n=="SetProperty"?dv->SetProperty(*rp,reinterpret_cast<LPCDIPROPHEADER>(b.data())):dv->GetProperty(*rp,reinterpret_cast<LPDIPROPHEADER>(b.data()));
     if(n=="GetProperty"&&SUCCEEDED(hr))for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({ph+i},b[i]);apis.back()+="("+std::to_string(pg<0x10000?pg:0)+")="+std::to_string(unsigned(hr));return done(unsigned(hr),3);}
    if(n=="GetCapabilities"){const unsigned a=arg(1);if(!readable(a,4))deny("DIDEVCAPS outside the memory contract",a);const unsigned z=load(a);if(z<24||z>sizeof(DIDEVCAPS)||!writable(a,z))deny("DIDEVCAPS size outside the model",z);DIDEVCAPS c{};c.dwSize=z;
     const HRESULT hr=dv->GetCapabilities(&c);
     if(SUCCEEDED(hr)){
      // No IFORCE2 or effect service exists, so the game must take its plain-joystick path (see directinput_caps.hpp).
      if(mw34::directinput::hide_force_feedback(c))apis.back()+="(force feedback hidden)";
      for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&c)[i]);}
     return done(unsigned(hr),2);}
    if(n=="GetObjectInfo") {
     const unsigned out=arg(1);
     if(!readable(out,4))deny("GetObjectInfo size outside the memory contract",out);
     const unsigned size=load(out);
     static_assert(sizeof(DIDEVICEOBJECTINSTANCEA)==316 && sizeof(DIDEVICEOBJECTINSTANCE_DX3A)==292);
     static_assert(offsetof(DIDEVICEOBJECTINSTANCEA,tszName)==32 && offsetof(DIDEVICEOBJECTINSTANCEA,dwFFMaxForce)==292);
     if(size!=sizeof(DIDEVICEOBJECTINSTANCEA) && size!=sizeof(DIDEVICEOBJECTINSTANCE_DX3A))
      deny("DIDEVICEOBJECTINSTANCEA size outside the model",size);
     if(!writable(out,size))deny("GetObjectInfo output outside the memory contract",out);
     // Both ANSI layouts contain only DWORDs, WORDs, GUIDs and inline characters;
     // they have identical x86/x64 offsets. Never expose a guest pointer to COM.
     DIDEVICEOBJECTINSTANCEA info{};info.dwSize=size;
     const HRESULT hr=dv->GetObjectInfo(&info,arg(2),arg(3));
     if(SUCCEEDED(hr))for(unsigned i=0;i<size;++i)
      runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&info)[i]);
     apis.back()+="(size="+std::to_string(size)+",object="+std::to_string(arg(2))+",how="+std::to_string(arg(3))+")="+std::to_string(unsigned(hr));
     return done(unsigned(hr),4);
    }
    if(n=="GetDeviceInfo"){const unsigned a=arg(1);if(!readable(a,4))deny("DIDEVICEINSTANCEA outside the memory contract",a);const unsigned z=load(a);if(z!=580&&z!=572)deny("DIDEVICEINSTANCEA size outside the model",z);if(!writable(a,z))deny("GetDeviceInfo output outside the memory contract",a);
     DIDEVICEINSTANCEA d{};d.dwSize=z;const HRESULT hr=dv->GetDeviceInfo(&d);if(SUCCEEDED(hr))for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&d)[i]);return done(unsigned(hr),2);}
    if(n=="EnumObjects"){const unsigned cb=arg(1),ctx=arg(2),fl=arg(3);if(!find(cb))deny("EnumObjects callback has no lifted body",cb);struct C{Stage*st;unsigned cb,ctx,calls;};C c{this,cb,ctx,0};
     const HRESULT hr=dv->EnumObjects([](LPCDIDEVICEOBJECTINSTANCEA d,LPVOID p)->BOOL{auto&c=*static_cast<C*>(p);auto&st=*c.st;if(!st.callback_fault.empty())return DIENUM_STOP;
       try{const unsigned z=d->dwSize;const unsigned at=((st.state.gpr.rsp.dword-0x200)&~15U)-((z+15)&~15U);const auto*b=reinterpret_cast<const unsigned char*>(d);for(unsigned i=0;i<z;++i)st.runtime.memory().store<unsigned char>({at+i},b[i]);++c.calls;
        return BOOL(st.call_guest(c.cb,{at,c.ctx},true,"EnumObjects callback",at&~15U));}catch(const std::exception&e){st.callback_fault=e.what();return DIENUM_STOP;}},&c,fl);return done(unsigned(hr),4);}}
   if(imp->dll=="IDirectSound"){auto*ds=reinterpret_cast<IDirectSound*>(o->native);
    if(n=="SetCooperativeLevel"){const HRESULT hr=ds->SetCooperativeLevel(hwnd_of(arg(1)),arg(2));apis.back()+="("+std::to_string(arg(2))+")="+std::to_string(unsigned(hr));return done(unsigned(hr),3);}
    if(n=="GetCaps"){const unsigned a=arg(1);if(!writable(a,96)||load(a)!=96)deny("DSCAPS outside the contract or with a wrong dwSize",a);DSCAPS c{};c.dwSize=sizeof(c);static_assert(sizeof(DSCAPS)==96);const HRESULT hr=ds->GetCaps(&c);
     if(SUCCEEDED(hr))for(unsigned i=0;i<96;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&c)[i]);return done(unsigned(hr),2);}
    // A duplicate shares the original's audio memory and has its own play state (the real provider's object).
    if(n=="DuplicateSoundBuffer"){const unsigned src=arg(1),out=arg(2);auto*so=host.com_object(src);if(!so||!so->alive||!so->native||std::string(so->iface->name)!="IDirectSoundBuffer")deny("DuplicateSoundBuffer of an object that is not a live sound buffer",src);
     if(!writable(out,4))deny("DuplicateSoundBuffer output outside the memory contract",out);LPDIRECTSOUNDBUFFER b{};const HRESULT hr=ds->DuplicateSoundBuffer(reinterpret_cast<LPDIRECTSOUNDBUFFER>(so->native),&b);apis.back()+="="+std::to_string(unsigned(hr));
     store(out,SUCCEEDED(hr)&&b?com_wrap(b,*com::by_name("IDirectSoundBuffer"),root_of(*o)):0);return done(unsigned(hr),3);}
    if(n=="CreateSoundBuffer"){const unsigned a=arg(1),out=arg(2);if(arg(3))deny("CreateSoundBuffer aggregation is not modelled",arg(3));const unsigned size=readable(a,4)?load(a):0;
     if((size!=20&&size!=36)||!readable(a,size)||!writable(out,4))deny("DSBUFFERDESC outside the contract or with a wrong dwSize",a);DSBUFFERDESC d{};d.dwSize=sizeof(d);d.dwFlags=load(a+4);d.dwBufferBytes=load(a+8);
     std::vector<unsigned char>wf;if(load(a+16)){wf=guest_waveformat(load(a+16));d.lpwfxFormat=reinterpret_cast<LPWAVEFORMATEX>(wf.data());}if(size==36)deny("DSBUFFERDESC with 3D algorithm GUID is not modelled",a);
     LPDIRECTSOUNDBUFFER b{};const HRESULT hr=ds->CreateSoundBuffer(&d,&b,nullptr);apis.back()+="(flags="+std::to_string(d.dwFlags)+",bytes="+std::to_string(d.dwBufferBytes)+")="+std::to_string(unsigned(hr));
     store(out,SUCCEEDED(hr)&&b?com_wrap(b,*com::by_name("IDirectSoundBuffer"),root_of(*o)):0);return done(unsigned(hr),4);}}
   if(imp->dll=="IDirectSoundBuffer"){auto*b=reinterpret_cast<IDirectSoundBuffer*>(o->native);
    if(n=="SetFormat"){auto wf=guest_waveformat(arg(1));const HRESULT hr=b->SetFormat(reinterpret_cast<LPCWAVEFORMATEX>(wf.data()));return done(unsigned(hr),2);}
    if(n=="GetCaps"){const unsigned a=arg(1);if(!writable(a,20)||load(a)!=20)deny("DSBCAPS outside the contract or with a wrong dwSize",a);DSBCAPS c{};c.dwSize=sizeof(c);const HRESULT hr=b->GetCaps(&c);
     if(SUCCEEDED(hr))for(unsigned i=0;i<20;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&c)[i]);return done(unsigned(hr),2);}
    auto vs=[&]()->Host::VSound&{auto&v=host.vsound[b];if(!v.size){DSBCAPS c{sizeof c};WAVEFORMATEX f{};if(SUCCEEDED(b->GetCaps(&c)))v.size=c.dwBufferBytes;if(SUCCEEDED(b->GetFormat(&f,sizeof f,nullptr)))v.rate=f.nAvgBytesPerSec;if(!v.size)v.size=1;}return v;};
    auto vpos=[&](Host::VSound&v)->unsigned{if(!v.playing)return v.pos0;const std::uint64_t moved=(host.vclock_us-v.t0)*v.rate/1000000ULL,p=v.pos0+moved;
      if(v.looping)return unsigned(p%v.size);if(p>=v.size){v.playing=false;v.pos0=0;return 0;}return unsigned(p);};
    if(n=="Play"&&host.vclock()){auto&v=vs();v.pos0=vpos(v);v.t0=host.vclock_us;v.playing=true;v.looping=(arg(3)&DSBPLAY_LOOPING)!=0;}
    if(n=="Stop"&&host.vclock()){auto&v=vs();v.pos0=vpos(v);v.playing=false;}
    if(n=="SetCurrentPosition"&&host.vclock()){auto&v=vs();v.pos0=arg(1)%v.size;v.t0=host.vclock_us;}
    if(n=="SetFrequency"&&host.vclock()){auto&v=vs();v.pos0=vpos(v);v.t0=host.vclock_us;WAVEFORMATEX f{};if(SUCCEEDED(b->GetFormat(&f,sizeof f,nullptr)))v.rate=(arg(1)?arg(1):f.nSamplesPerSec)*f.nBlockAlign;}
    if(n=="GetCurrentPosition"&&host.vclock()){auto&v=vs();const unsigned pl=vpos(v),wp=(pl+v.rate/100)%v.size;  // write cursor 10 ms ahead
     for(auto[a,x]:{std::pair<unsigned,unsigned>{arg(1),pl},{arg(2),wp}})if(a){if(!writable(a,4))deny("GetCurrentPosition output outside the memory contract",a);store(a,x);}return done(DS_OK,3);}
    if(n=="GetStatus"&&host.vclock()){if(!writable(arg(1),4))deny("GetStatus output outside the memory contract",arg(1));DWORD st{};const HRESULT hr=b->GetStatus(&st);auto&v=vs();(void)vpos(v);
     st&=~DWORD(DSBSTATUS_PLAYING|DSBSTATUS_LOOPING);if(v.playing)st|=DSBSTATUS_PLAYING|(v.looping?DSBSTATUS_LOOPING:0);store(arg(1),st);return done(unsigned(hr),2);}
    if(n=="Play")return done(unsigned(b->Play(arg(1),arg(2),arg(3))),4);
    if(n=="Stop")return done(unsigned(b->Stop()),1);
    if(n=="SetVolume")return done(unsigned(b->SetVolume(LONG(arg(1)))),2);
    if(n=="SetPan")return done(unsigned(b->SetPan(LONG(arg(1)))),2);
    if(n=="SetFrequency")return done(unsigned(b->SetFrequency(arg(1))),2);
    if(n=="GetStatus"){if(!writable(arg(1),4))deny("GetStatus output outside the memory contract",arg(1));DWORD st{};const HRESULT hr=b->GetStatus(&st);store(arg(1),st);return done(unsigned(hr),2);}
    if(n=="GetFormat"){const unsigned a=arg(1),z=arg(2),wr=arg(3);std::vector<unsigned char>buf(std::max(z,64U));DWORD k{};const HRESULT hr=b->GetFormat(reinterpret_cast<LPWAVEFORMATEX>(a?buf.data():nullptr),a?z:0,&k);
     if(SUCCEEDED(hr)&&a){if(!writable(a,std::min<unsigned>(k,z)))deny("GetFormat output outside the memory contract",a);for(unsigned i=0;i<std::min<unsigned>(k,z);++i)runtime.memory().store<unsigned char>({a+i},buf[i]);}
     if(wr){if(!writable(wr,4))deny("GetFormat size outside the memory contract",wr);store(wr,k);}return done(unsigned(hr),4);}
    if(n=="GetCurrentPosition"){DWORD pl{},wp{};const HRESULT hr=b->GetCurrentPosition(arg(1)?&pl:nullptr,arg(2)?&wp:nullptr);for(auto[a,v]:{std::pair<unsigned,DWORD>{arg(1),pl},{arg(2),wp}})if(a){if(!writable(a,4))deny("GetCurrentPosition output outside the memory contract",a);store(a,v);}return done(unsigned(hr),3);}
    if(n=="SetCurrentPosition")return done(unsigned(b->SetCurrentPosition(arg(1))),2);
    if(n=="Restore")return done(unsigned(b->Restore()),1);
    if(n=="GetVolume"||n=="GetPan"){LONG v{};const HRESULT hr=n=="GetVolume"?b->GetVolume(&v):b->GetPan(&v);if(!writable(arg(1),4))deny(n+" output outside the memory contract",arg(1));store(arg(1),unsigned(v));return done(unsigned(hr),2);}
    if(n=="GetFrequency"){DWORD v{};const HRESULT hr=b->GetFrequency(&v);if(!writable(arg(1),4))deny("GetFrequency output outside the memory contract",arg(1));store(arg(1),v);return done(unsigned(hr),2);}
    // Lock: the locked regions are mirrored into guest pages; Unlock copies the written bytes back.
    if(n=="Lock"){const unsigned off=arg(1),bytes=arg(2),pp1=arg(3),pb1=arg(4),pp2=arg(5),pb2=arg(6),fl=arg(7);void*p1{};void*p2{};DWORD b1{},b2{};const HRESULT hr=b->Lock(off,bytes,&p1,&b1,pp2?&p2:nullptr,pp2?&b2:nullptr,fl);
     if(FAILED(hr))return done(unsigned(hr),8);if(!writable(pp1,4)||!writable(pb1,4)||(pp2&&(!writable(pp2,4)||!writable(pb2,4))))deny("Sound buffer Lock outputs outside the memory contract",pp1);
     SoundLock l{arg(0),p1,b1,p2,b2,b1?pages(p1,b1):0,b2?pages(p2,b2):0};store(pp1,l.g1);store(pb1,b1);if(pp2){store(pp2,l.g2);store(pb2,b2);}host.sound_locks.push_back(l);return done(unsigned(hr),8);}
    if(n=="Unlock"){const unsigned g1=arg(1),w1=arg(2),g2=arg(3),w2=arg(4);for(auto it=host.sound_locks.begin();it!=host.sound_locks.end();++it)if(it->g1==g1&&vsurf_root(it->buffer)==vsurf_root(arg(0))){
      if(w1>it->b1||w2>it->b2||(g2&&g2!=it->g2))deny("Sound buffer Unlock outside its locked regions",g1);if(w1)get_bytes(g1,it->p1,w1);if(w2)get_bytes(g2,it->p2,w2);const HRESULT hr=b->Unlock(it->p1,w1,it->p2,w2);
      if(it->g1)release(it->g1);if(it->g2)release(it->g2);host.sound_locks.erase(it);return done(unsigned(hr),5);}
     deny("Sound buffer Unlock without its Lock",g1);}}
   // DDCAPS (any version, sized by the guest dwSize) and DDDEVICEIDENTIFIER share the x86/x64 layout.
   if(is_dd&&n=="GetCaps"){auto caps=[&](unsigned a,std::vector<unsigned char>&v)->void*{if(!a)return nullptr;if(!readable(a,4))deny("DDCAPS outside the memory contract",a);const unsigned z=load(a);if(z<4||z>sizeof(DDCAPS)||!writable(a,z))deny("DDCAPS size outside the modelled versions",z);
     v.assign(sizeof(DDCAPS),0);std::memcpy(v.data(),&z,4);return v.data();};std::vector<unsigned char>dv,hv;void*pd=caps(arg(1),dv);void*ph=caps(arg(2),hv);
    const HRESULT hr=reinterpret_cast<IDirectDraw*>(o->native)->GetCaps(static_cast<LPDDCAPS>(pd),static_cast<LPDDCAPS>(ph));apis.back()+="="+std::to_string(unsigned(hr));
    if(SUCCEEDED(hr))for(auto[a,v]:{std::pair<unsigned,std::vector<unsigned char>*>{arg(1),&dv},{arg(2),&hv}})if(a){const unsigned z=load(a);for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},(*v)[i]);}
    return done(unsigned(hr),3);}
   if(is_dd&&n=="GetDeviceIdentifier"&&imp->dll=="IDirectDraw4"){const unsigned a=arg(1);static_assert(sizeof(DDDEVICEIDENTIFIER)==1064);if(!writable(a,1064))deny("DDDEVICEIDENTIFIER outside the memory contract",a);DDDEVICEIDENTIFIER id{};
    const HRESULT hr=reinterpret_cast<IDirectDraw4*>(o->native)->GetDeviceIdentifier(&id,arg(2));if(SUCCEEDED(hr))for(unsigned i=0;i<1064;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&id)[i]);
    apis.back()+="("+std::string(id.szDescription)+")";return done(unsigned(hr),3);}
   const unsigned dsize=imp->dll=="IDirectDraw4"?124U:108U;
   if(is_dd&&n=="GetAvailableVidMem"&&imp->dll!="IDirectDraw"){const unsigned c=arg(1),tot=arg(2),fr=arg(3);DDSCAPS2 caps{};if(c){if(!readable(c,imp->dll=="IDirectDraw4"?16:4))deny("GetAvailableVidMem caps outside the memory contract",c);caps.dwCaps=load(c);if(imp->dll=="IDirectDraw4"){caps.dwCaps2=load(c+4);caps.dwCaps3=load(c+8);caps.dwCaps4=load(c+12);}}
    DWORD t{},f{};HRESULT hr=imp->dll=="IDirectDraw4"?reinterpret_cast<IDirectDraw4*>(o->native)->GetAvailableVidMem(&caps,tot?&t:nullptr,fr?&f:nullptr):reinterpret_cast<IDirectDraw2*>(o->native)->GetAvailableVidMem(reinterpret_cast<LPDDSCAPS>(&caps),tot?&t:nullptr,fr?&f:nullptr);
    if(SUCCEEDED(hr)){if(tot){if(!writable(tot,4))deny("GetAvailableVidMem total outside the memory contract",tot);store(tot,t);}if(fr){if(!writable(fr,4))deny("GetAvailableVidMem free outside the memory contract",fr);store(fr,f);}}
    apis.back()+="("+std::to_string(t)+"/"+std::to_string(f)+")="+std::to_string(unsigned(hr));return done(unsigned(hr),4);}
   if(is_dd&&n=="GetDisplayMode"){const unsigned a=arg(1);if(!readable(a,4)||load(a)!=dsize)deny("GetDisplayMode descriptor with a wrong dwSize",a);DDSURFACEDESC2 d{};HRESULT hr;
    if(host.display.width){d.dwSize=sizeof(d);d.dwFlags=DDSD_WIDTH|DDSD_HEIGHT|DDSD_PITCH|DDSD_PIXELFORMAT;d.dwWidth=host.display.width;d.dwHeight=host.display.height;d.lPitch=LONG(host.display.width*host.display.bpp/8);
     d.ddpfPixelFormat=virtual_format(host.display.bpp);put_desc(a,d,dsize);return done(0,2);}
    if(dsize==124){d.dwSize=sizeof(d);hr=reinterpret_cast<IDirectDraw4*>(o->native)->GetDisplayMode(&d);}else{DDSURFACEDESC d1{};d1.dwSize=sizeof(d1);hr=reinterpret_cast<IDirectDraw*>(o->native)->GetDisplayMode(&d1);std::memcpy(&d,&d1,offsetof(DDSURFACEDESC,ddsCaps));d.ddsCaps.dwCaps=d1.ddsCaps.dwCaps;}
    if(SUCCEEDED(hr))put_desc(a,d,dsize);return done(unsigned(hr),2);}
   // Virtual display modes: every real host resolution in 8-, 16- (RGB565) and 32-bit depth, as modern
   // Windows offers legacy 32-bit DirectDraw applications; the guest filter (size/depth) is applied.
   if(is_dd&&n=="EnumDisplayModes"){const unsigned flags=arg(1),filter=arg(2),ctx=arg(3),cb=arg(4);if(!find(cb))deny("EnumDisplayModes callback has no lifted body",cb);
    if(flags&~(DDEDM_REFRESHRATES|DDEDM_STANDARDVGAMODES))deny("EnumDisplayModes flags not modelled",flags);DDSURFACEDESC2 f{};if(filter)f=get_desc(filter,dsize);
    unsigned calls=0;HRESULT r=DD_OK;for(const auto&m:virtual_modes(o->native)){
     if(filter&&(((f.dwFlags&DDSD_WIDTH)&&f.dwWidth!=m.dwWidth)||((f.dwFlags&DDSD_HEIGHT)&&f.dwHeight!=m.dwHeight)||((f.dwFlags&DDSD_PIXELFORMAT)&&f.ddpfPixelFormat.dwRGBBitCount!=m.ddpfPixelFormat.dwRGBBitCount)))continue;
     r=enum_mode(this,cb,ctx,dsize,calls,m);if(!callback_fault.empty()||r==DDENUMRET_CANCEL)break;}
    apis.back()+="("+std::to_string(calls)+" virtual modes)";return done(DD_OK,5);}
   if(is_dd&&n=="RestoreDisplayMode"){mw34::display::exclusive().release();return done(unsigned(reinterpret_cast<IDirectDraw*>(o->native)->RestoreDisplayMode()),1);}
   // Virtual display (project presentation provider): exclusive full-screen and display modes are
   // emulated in the game window; the host desktop is never taken over or re-moded. The real object is
   // put in DDSCL_NORMAL on the same window so its queries stay valid; its status is returned.
   if(is_dd&&n=="SetCooperativeLevel"&&(arg(2)&(DDSCL_EXCLUSIVE|DDSCL_FULLSCREEN))){const HRESULT hr=reinterpret_cast<IDirectDraw*>(o->native)->SetCooperativeLevel(hwnd_of(arg(1)),DDSCL_NORMAL);
    if(SUCCEEDED(hr)){host.display.window=hwnd_of(arg(1));host.display.exclusive=true;host.display.flags=arg(2);}apis.back()+="(virtual exclusive "+std::to_string(arg(2))+")="+std::to_string(unsigned(hr));return done(unsigned(hr),3);}
   if(is_dd&&n=="SetDisplayMode"){const unsigned w=arg(1),h=arg(2),bpp=arg(3);const unsigned extra=imp->dll=="IDirectDraw"?0:2;if(extra&&(arg(4)||arg(5)))deny("SetDisplayMode refresh/flags are not modelled",arg(4)|arg(5));
    if(!host.display.exclusive)deny("SetDisplayMode without the exclusive cooperative level",w);bool listed=false;
    for(const auto&m:virtual_modes(o->native))if(m.dwWidth==w&&m.dwHeight==h&&m.ddpfPixelFormat.dwRGBBitCount==bpp)listed=true;
    if(!listed){apis.back()+="("+std::to_string(w)+"x"+std::to_string(h)+"x"+std::to_string(bpp)+" not offered)";return done(unsigned(DDERR_INVALIDMODE),4+extra);}
    host.display.width=w;host.display.height=h;host.display.bpp=bpp;apis.back()+="(virtual "+std::to_string(w)+"x"+std::to_string(h)+"x"+std::to_string(bpp)+")";
    // As exclusive DirectDraw does with the cooperative window, the virtual mode shows it with a client area of
    // the mode size (integer-scaled to fit the host screen; presentation scales). Scripted runs leave the
    // player's focus alone (no activation); MW34_HIDE_WINDOW=1 keeps the window hidden.
    if(const char*hw=std::getenv("MW34_HIDE_WINDOW");host.display.window&&!(hw&&*hw=='1')){HWND wnd=host.display.window;const int sw=::GetSystemMetrics(SM_CXSCREEN),sh=::GetSystemMetrics(SM_CYSCREEN);
     /* MW34_WINDOW=fit: the largest window of the mode's aspect that fits the screen (non-integer scale; the play default);
        otherwise (integer) the mode size scaled by 1 or 2. Rendering follows the window size (vdd.inc render_scale). */
     static const bool fit=[]{const char*e=std::getenv("MW34_WINDOW");return e&&std::string(e)=="fit";}();
     const int sc=std::clamp(std::min((sw-80)/int(w),(sh-120)/int(h)),1,2);const double fs=std::max(1.0,std::min(double(sw-80)/double(w),double(sh-120)/double(h)));
     const unsigned rw=mw34::vkscene::Renderer::remaster_width(),rh=mw34::vkscene::Renderer::remaster_height();
     const char*wm=std::getenv("MW34_WINDOW_MODE");
     if(wm&&(std::string(wm)=="windowed"||std::string(wm)=="fullscreen"||std::string(wm)=="fullscreen_windowed")){
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
     }else{
      RECT r{0,0,rw?int(rw):(fit?int(std::lround(double(w)*fs)):int(w)*sc),rh?int(rh):(fit?int(std::lround(double(h)*fs)):int(h)*sc)};::AdjustWindowRectEx(&r,DWORD(::GetWindowLongW(wnd,GWL_STYLE)),FALSE,DWORD(::GetWindowLongW(wnd,GWL_EXSTYLE)));
      {LastError l(host);::SetWindowPos(wnd,nullptr,(sw-(r.right-r.left))/2,(sh-(r.bottom-r.top))/2,r.right-r.left,r.bottom-r.top,SWP_NOZORDER|SWP_SHOWWINDOW|(host.scripted?SWP_NOACTIVATE:0U));}
     }
     apis.back()+="(window client requested "+std::to_string(rw?int(rw):(fit?int(std::lround(double(w)*fs)):int(w)*sc))+"x"+std::to_string(rh?int(rh):(fit?int(std::lround(double(h)*fs)):int(h)*sc))+")";}
    return done(0,4+extra);}
   if(is_dd&&n=="SetCooperativeLevel"){const HRESULT hr=reinterpret_cast<IDirectDraw*>(o->native)->SetCooperativeLevel(static_cast<HWND>(hhandle(arg(1))),arg(2));apis.back()+="("+std::to_string(arg(2))+")="+std::to_string(unsigned(hr));return done(unsigned(hr),3);}
   if(is_dd&&n=="CreateSurface"&&(imp->dll=="IDirectDraw"||imp->dll=="IDirectDraw2")){const unsigned a=arg(1),out=arg(2);if(arg(3))deny("CreateSurface aggregation is not modelled",arg(3));
    if(!readable(a,com::desc1_size)||load(a)!=com::desc1_size)deny("CreateSurface descriptor outside the contract or with a wrong dwSize",a);if(!writable(out,4))deny("CreateSurface output outside the memory contract",out);
    DDSURFACEDESC d{};d.dwSize=sizeof(d);d.dwFlags=load(a+4);if(d.dwFlags&DDSD_LPSURFACE)deny("CreateSurface with client memory is not modelled",a);d.dwHeight=load(a+8);d.dwWidth=load(a+12);d.lPitch=LONG(load(a+16));d.dwBackBufferCount=load(a+20);d.dwMipMapCount=load(a+24);d.dwAlphaBitDepth=load(a+28);
    std::memcpy(&d.ddckCKDestOverlay,std::array<unsigned,8>{load(a+40),load(a+44),load(a+48),load(a+52),load(a+56),load(a+60),load(a+64),load(a+68)}.data(),32);
    std::array<unsigned,8>pf{};for(unsigned i=0;i<8;++i)pf[i]=load(a+72+4*i);std::memcpy(&d.ddpfPixelFormat,pf.data(),32);d.ddsCaps.dwCaps=load(a+104);
    IDirectDrawSurface*sf{};const HRESULT hr=reinterpret_cast<IDirectDraw*>(o->native)->CreateSurface(&d,&sf,nullptr);apis.back()+="(caps="+std::to_string(d.ddsCaps.dwCaps)+")="+std::to_string(unsigned(hr));
    store(out,SUCCEEDED(hr)&&sf?com_wrap(sf,*com::by_name("IDirectDrawSurface"),root_of(*o)):0);return done(unsigned(hr),4);}
   stop(m4_runtime::FaultReason::unresolved_import,"COM method without marshalling: "+imp->dll+"::"+n,token);}
  // FreeLibrary: loader reference counts. Static imports and platform-service modules stay loaded; a
  // dynamically loaded module reaching zero would need DllMain(DLL_PROCESS_DETACH) and unmapping.
  if(n=="FreeLibrary"){const unsigned h=arg(0);std::string name;bool dynamic=false;
   for(const auto&m:host.modules)if(m.base==h){name=m.name;for(const auto&l:host.loadable)if(same(l.name,m.name))dynamic=true;}
   for(const auto&[k,v]:system_modules())if(v==h)name=k;if(h==msvcrt_base)name="MSVCRT.DLL";if(name.empty())deny("FreeLibrary of a module outside the loader model",h);
   std::transform(name.begin(),name.end(),name.begin(),[](unsigned char c){return char(std::toupper(c));});if(!name.empty()&&name.find('.')==std::string::npos)name+=".DLL";
   auto&c=host.loads[name];if(!c)deny("FreeLibrary without a matching load: "+name,h);--c;
   // Last reference to a dynamically loaded module: DllMain(DLL_PROCESS_DETACH) runs natively (its result is
   // ignored, as by the loader), then its header and sections are unmapped and it leaves the loader model.
   if(dynamic&&!c){auto mi=std::find_if(host.modules.begin(),host.modules.end(),[&](const auto&m2){return m2.base==h;});if(mi==host.modules.end()||!mi->bytes)deny("Unload of a module outside the loader model: "+name,h);
    if(mi->entry!=mi->base){if(!find(mi->entry))deny("Dynamically loaded module entry has no lifted body: "+name,mi->entry);(void)call_guest(mi->entry,{mi->base,DLL_PROCESS_DETACH,0},true,"DllMain detach "+name);}
    mi=std::find_if(host.modules.begin(),host.modules.end(),[&](const auto&m2){return m2.base==h;});const auto&img=*mi->bytes;
    {bool bad{};try{runtime.memory().unmap({h});for(const auto&sec:pe::sections(img))runtime.memory().unmap({h+sec.va});}catch(...){bad=true;}if(bad)deny("Checked module image release: "+name,h);}
    host.paths.erase(h);host.modules.erase(mi);host.loads.erase(name);apis.back()+="("+name+" detached and unmapped)";}
   host.last_error=0;return done(1,1);}
  // SystemParametersInfoA: queries with pointer-free outputs are real calls (input words such as cbSize
  // are carried in); SET actions would change the host user's system settings and stop typed.
  if(n=="SystemParametersInfoA"){const unsigned act=arg(0),ui=arg(1),pv=arg(2),ini=arg(3);apis.back()+="("+std::to_string(act)+")";
   static const std::map<unsigned,unsigned>gets{{SPI_GETMOUSE,12},{SPI_GETKEYBOARDSPEED,4},{SPI_GETSCREENSAVETIMEOUT,4},{SPI_GETSCREENSAVEACTIVE,4},{SPI_GETKEYBOARDDELAY,4},{SPI_GETWORKAREA,16},
    {SPI_GETFILTERKEYS,24},{SPI_GETTOGGLEKEYS,8},{SPI_GETSTICKYKEYS,8},{SPI_GETMOUSESPEED,4},{SPI_GETLOWPOWERACTIVE,4},{SPI_GETPOWEROFFACTIVE,4},{SPI_GETSCREENREADER,4},{SPI_GETMENUDROPALIGNMENT,4},{SPI_GETDRAGFULLWINDOWS,4}};
   const auto it=gets.find(act);if(it==gets.end())deny("SystemParametersInfoA action not modelled (SET actions would change host settings): "+std::to_string(act),act);
   const unsigned bytes=it->second;if(!writable(pv,bytes))deny("SystemParametersInfoA output outside the memory contract",pv);std::vector<unsigned char>buf(bytes);for(unsigned i=0;i<bytes;++i)buf[i]=runtime.memory().load<unsigned char>({pv+i});
   BOOL ok{};{LastError l(host);ok=::SystemParametersInfoA(act,ui,buf.data(),ini);}if(ok)for(unsigned i=0;i<bytes;++i)runtime.memory().store<unsigned char>({pv+i},buf[i]);return done(ok?1U:0U,4);}
  // VERSION.dll on the real file; VerQueryValueA works on a host copy of the guest block and returns a
  // guest pointer at the same offset inside that block.
  // A relative version-resource file name is found as the real call finds it (a data-file module load): the guest
  // application directory first, then the guest current directory; not the host process directories.
  auto version_file=[&](std::string f)->std::string{std::filesystem::path p(f);if(!p.is_relative()||f.empty())return f;
   const auto exe=host.paths.find(0x400000U);if(exe!=host.paths.end()){const auto c=std::filesystem::path(exe->second).parent_path()/p;if(std::filesystem::exists(c))return c.string();}
   const auto c=std::filesystem::path(host.cwd)/p;return std::filesystem::exists(c)?c.string():f;};
  if(n=="GetFileVersionInfoSizeA"){const std::string f=version_file(guest_string(arg(0)));DWORD hnd{};DWORD z{};{LastError l(host);z=::GetFileVersionInfoSizeA(f.c_str(),&hnd);}
   if(arg(1)){if(!writable(arg(1),4))deny("GetFileVersionInfoSizeA handle outside the memory contract",arg(1));store(arg(1),hnd);}apis.back()+="("+f+")="+std::to_string(z);return done(z,2);}
  if(n=="GetFileVersionInfoA"){const std::string f=version_file(guest_string(arg(0)));const unsigned len=arg(2),a=arg(3);if(!writable(a,len))deny("GetFileVersionInfoA buffer outside the memory contract",a);
   std::vector<unsigned char>buf(len);for(unsigned i=0;i<len;++i)buf[i]=runtime.memory().load<unsigned char>({a+i});BOOL ok{};{LastError l(host);ok=::GetFileVersionInfoA(f.c_str(),arg(1),len,buf.data());}
   if(ok){for(unsigned i=0;i<len;++i)runtime.memory().store<unsigned char>({a+i},buf[i]);host.ver_blocks[a]=len;}return done(ok?1U:0U,4);}
  if(n=="VerQueryValueA"){const unsigned blk=arg(0);const std::string sub=guest_string(arg(1));const unsigned pp=arg(2),pl=arg(3);if(!readable(blk,6))deny("VerQueryValueA block outside the memory contract",blk);
   const auto vb=host.ver_blocks.find(blk);if(vb==host.ver_blocks.end())deny("VerQueryValueA on a block GetFileVersionInfoA did not fill",blk);const unsigned total=vb->second;if(!writable(blk,total))deny("VerQueryValueA block outside the memory contract",blk);std::vector<unsigned char>buf(total);for(unsigned i=0;i<total;++i)buf[i]=runtime.memory().load<unsigned char>({blk+i});
   void*q{};UINT ql{};BOOL ok{};{LastError l(host);ok=::VerQueryValueA(buf.data(),sub.c_str(),&q,&ql);}apis.back()+="("+sub+")";
   for(unsigned i=0;i<total;++i)runtime.memory().store<unsigned char>({blk+i},buf[i]);  // ANSI conversions land in the block's spare area
   if(ok){const auto off=static_cast<unsigned char*>(q)-buf.data();if(off<0||std::size_t(off)>buf.size())deny("VerQueryValueA result outside the guest block",blk);if(!writable(pp,4)||!writable(pl,4))deny("VerQueryValueA outputs outside the memory contract",pp);store(pp,blk+unsigned(off));store(pl,ql);}
   return done(ok?1U:0U,4);}
  // GetStartupInfoA: the real record, x86 layout, strings copied into the provider string page (as the
  // MSVCRT attach stage does); an inherited CRT handle table is not admitted.
  if(n=="GetStartupInfoA"){const unsigned info=arg(0);if(!writable(info,68))deny("GetStartupInfoA record outside the memory contract",info);STARTUPINFOA si{};si.cb=sizeof(si);{LastError l(host);::GetStartupInfoA(&si);}
   if(si.cbReserved2||si.lpReserved2)deny("Inherited CRT handle table (STARTUPINFO lpReserved2) is not admitted",info);
   auto cstr=[&](const char*t)->unsigned{if(!t)return 0;const std::size_t k=std::strlen(t)+1;if(heap.strings_next==hs::strings){bool bad{};try{runtime.memory().map({hs::strings},4096,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked provider string page",hs::strings);}
    if(std::uint64_t(heap.strings_next)+k>hs::strings+4096)deny("Provider string page exhausted",heap.strings_next);const unsigned g=heap.strings_next;runtime.memory().write({g},std::span<const std::byte>(reinterpret_cast<const std::byte*>(t),k));heap.strings_next+=unsigned(k);return g;};
   const std::array<unsigned,17>w{68,cstr(si.lpReserved),cstr(si.lpDesktop),cstr(si.lpTitle),si.dwX,si.dwY,si.dwXSize,si.dwYSize,si.dwXCountChars,si.dwYCountChars,si.dwFillAttribute,si.dwFlags,
    unsigned(si.wShowWindow),0,ghandle(si.hStdInput),ghandle(si.hStdOutput),ghandle(si.hStdError)};for(unsigned i=0;i<w.size();++i)store(info+4*i,w[i]);return done(0,1);}
  if(n=="SetWindowsHookExA"){const int id=int(arg(0));const unsigned proc=arg(1),thread=arg(3);if(thread!=::GetCurrentThreadId())deny("Only thread hooks on the guest thread are modelled",thread);
   HOOKPROC tramp=id==WH_MSGFILTER?&hook_msgfilter:id==WH_CBT?&hook_cbt:nullptr;if(!tramp)deny("SetWindowsHookExA hook type not modelled: "+std::to_string(id),unsigned(id));if(!find(proc))deny("Hook procedure has no lifted body",proc);
   HHOOK h{};{LastError l(host);h=::SetWindowsHookExA(id,tramp,nullptr,::GetCurrentThreadId());}if(!h)return done(0,4);const unsigned g2=ghandle(h);host.hooks.push_back({g2,id,proc,h,true});apis.back()+="("+std::to_string(id)+")";return done(g2,4);}
  if(n=="UnhookWindowsHookEx"){for(auto&k:host.hooks)if(k.live&&k.guest==arg(0)){BOOL ok{};{LastError l(host);ok=::UnhookWindowsHookEx(k.native);}k.live=false;return done(ok?1U:0U,1);}deny("UnhookWindowsHookEx of a hook the guest does not own",arg(0));}
  if(n=="CallNextHookEx"){for(auto&k:host.hooks)if(k.live&&k.guest==arg(0)){if(hook_frames.empty()||hook_frames.back().guest_l!=arg(3))deny("CallNextHookEx outside the active hook callback",arg(3));
    const auto&f=hook_frames.back();LRESULT r{};{LastError l(host);r=::CallNextHookEx(k.native,int(arg(1)),f.host_w,f.host_l);}return done(unsigned(r),4);}
   deny("CallNextHookEx with a hook the guest does not own",arg(0));}
  if(n=="FindWindowA"){const unsigned c=arg(0),t=arg(1);const std::string cs=c>=0x10000?guest_string(c):std::string(),ts=t?guest_string(t):std::string();HWND w{};
   {LastError l(host);w=::FindWindowA(c?(c<0x10000?MAKEINTATOM(c):cs.c_str()):nullptr,t?ts.c_str():nullptr);}apis.back()+="("+cs+","+ts+")";return done(w?ghandle(w):0,2);}
  // ---- window classes and windows (win_bridge.inc) ----
  auto host_instance=[&](unsigned gi)->HINSTANCE{if(!gi||gi==0x400000||in_module(gi,1,false))return ::GetModuleHandleW(nullptr);deny("Window instance outside the loaded guest images",gi);};
  // A guest "procedure" value may be lifted code, a host procedure token, or the import of a USER32
  // window procedure (service token / raw game IAT word): the latter become host procedure tokens.
  auto as_proc=[&](unsigned v)->unsigned{if(find(v)||host_proc(v))return v;const Import*i=host.by_bound(v);if(!i)i=game_import(v);
   if(i&&(i->name=="DefWindowProcA"||i->name=="DefFrameProcA"||i->name=="DefMDIChildProcA"||i->name=="DefDlgProcA")){HMODULE u=::GetModuleHandleA("user32.dll");return host_proc_token(reinterpret_cast<WNDPROC>(::GetProcAddress(u,i->name.c_str())));}return v;};
  auto class_name=[&](unsigned v)->std::string{return v<0x10000?"#"+std::to_string(v):guest_string(v);};
  if(n=="GetClassInfoA"){const unsigned gi=arg(0),cn=arg(1),out=arg(2);if(!writable(out,40))deny("GetClassInfoA output outside the memory contract",out);const std::string name=class_name(cn);apis.back()+="("+name+")";
   for(const auto&c:host.classes)if(_stricmp(c.name.c_str(),name.c_str())==0){const std::array<unsigned,10>v{c.style,c.guest_proc,c.cls_extra,c.wnd_extra,c.guest_instance,c.icon,c.cursor,c.brush,c.menu,cn};for(unsigned i=0;i<10;++i)store(out+4*i,v[i]);return done(1,3);}
   WNDCLASSA wc{};BOOL ok{};{LastError l(host);ok=::GetClassInfoA(gi?host_instance(gi):nullptr,cn<0x10000?MAKEINTATOM(cn):name.c_str(),&wc);}if(!ok)return done(0,3);
   const std::array<unsigned,10>v{wc.style,host_proc_token(wc.lpfnWndProc),unsigned(wc.cbClsExtra),unsigned(wc.cbWndExtra),gi,wc.hIcon?ghandle(wc.hIcon):0,wc.hCursor?ghandle(wc.hCursor):0,unsigned(reinterpret_cast<std::uintptr_t>(wc.hbrBackground)),0,cn};
   for(unsigned i=0;i<10;++i)store(out+4*i,v[i]);return done(1,3);}
  if(n=="RegisterClassA"){const unsigned a=arg(0);if(!readable(a,40))deny("RegisterClassA record outside the memory contract",a);std::array<unsigned,10>v{};for(unsigned i=0;i<10;++i)v[i]=load(a+4*i);
   const std::string name=class_name(v[9]);const unsigned proc=as_proc(v[1]);if(!find(proc)&&!host_proc(proc))deny("RegisterClassA procedure is neither lifted guest code nor a host procedure",proc);
   WNDCLASSA wc{};wc.style=v[0];wc.lpfnWndProc=host_proc(proc)?host_proc(proc):&wnd_tramp;wc.cbClsExtra=int(v[2]);wc.cbWndExtra=int(v[3]);wc.hInstance=host_instance(v[4]);wc.hIcon=static_cast<HICON>(hhandle(v[5]));wc.hCursor=static_cast<HCURSOR>(hhandle(v[6]));
   wc.hbrBackground=reinterpret_cast<HBRUSH>(std::intptr_t(std::int32_t(v[7])));const std::string menu=v[8]>=0x10000?guest_string(v[8]):std::string();if(v[8])deny("RegisterClassA with a class menu is not modelled",v[8]);wc.lpszClassName=v[9]<0x10000?MAKEINTATOM(v[9]):name.c_str();
   ATOM at{};{LastError l(host);at=::RegisterClassA(&wc);}apis.back()+="("+name+")="+std::to_string(at)+"/err"+std::to_string(host.last_error);if(at&&!host_proc(proc))host.classes.push_back({name,at,proc,v[4],v[0],v[2],v[3],v[5],v[6],v[7],v[8]});return done(at,1);}
  if(n=="UnregisterClassA"){const unsigned cn=arg(0);const std::string cls=cn<0x10000?std::string():class_name(cn);BOOL ok{};{LastError l(host);ok=::UnregisterClassA(cn<0x10000?MAKEINTATOM(cn):cls.c_str(),host_instance(arg(1)));}
   if(ok)host.classes.erase(std::remove_if(host.classes.begin(),host.classes.end(),[&](const auto&c){return cn<0x10000?c.atom==ATOM(cn):_stricmp(c.name.c_str(),cls.c_str())==0;}),host.classes.end());
   apis.back()+="("+(cn<0x10000?std::to_string(cn):cls)+")="+std::to_string(ok);return done(ok?1U:0U,2);}
  if(n=="CreateWindowExA"){const unsigned cn=arg(1),tn=arg(2);const std::string cls=class_name(cn),title=tn?guest_string(tn):std::string();HWND w{};
   {LastError l(host);w=::CreateWindowExA(arg(0),cn<0x10000?MAKEINTATOM(cn):cls.c_str(),tn?title.c_str():nullptr,arg(3),int(arg(4)),int(arg(5)),int(arg(6)),int(arg(7)),hwnd_of(arg(8)),reinterpret_cast<HMENU>(std::intptr_t(std::int32_t(arg(9)))),host_instance(arg(10)),reinterpret_cast<void*>(std::uintptr_t(arg(11))));}
   apis.back()+="("+cls+","+title+")";return done(w?gwnd(w):0,12);}
  if(n=="DefWindowProcA")return done(unsigned(std::int32_t(to_host(nullptr,arg(0),arg(1),arg(2),arg(3)))),4);
  if(n=="CallWindowProcA"){const unsigned p=as_proc(arg(0));if(auto hp=host_proc(p))return done(unsigned(std::int32_t(to_host(hp,arg(1),arg(2),arg(3),arg(4)))),5);
   if(!find(p))deny("CallWindowProcA target is neither lifted guest code nor a host procedure",p);const unsigned r=call_guest(p,{arg(1),arg(2),arg(3),arg(4)},true,"CallWindowProcA");return done(r,5);}
  if(n=="GetWindowLongA"||n=="SetWindowLongA"){const HWND h=hwnd_of(arg(0));const int idx=int(arg(1));const bool set=n=="SetWindowLongA";
   if(idx==-4/*GWL_WNDPROC (x86)*/){unsigned prev=window_proc(h);if(!prev){WNDPROC hp=reinterpret_cast<WNDPROC>(::GetWindowLongPtrA(h,GWLP_WNDPROC));prev=host_proc_token(hp);}
    if(set){const unsigned np=as_proc(arg(2));if(!find(np)&&!host_proc(np))deny("SetWindowLongA(GWL_WNDPROC) procedure is neither lifted guest code nor a host procedure",np);
     if(reinterpret_cast<WNDPROC>(::GetWindowLongPtrA(h,GWLP_WNDPROC))!=&wnd_tramp){::SetWindowLongPtrA(h,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(&wnd_tramp));}host.windows[h]=np;}
    return done(prev,set?3:2);}
   if(idx==-6/*GWL_HINSTANCE (x86)*/){if(set)deny("SetWindowLongA(GWL_HINSTANCE) is not modelled",0);return done(guest_instance(reinterpret_cast<HINSTANCE>(::GetWindowLongPtrA(h,GWLP_HINSTANCE))),2);}
   LONG value=LONG(arg(2));
   if(set&&h==host.display.window){const char*wm=std::getenv("MW34_WINDOW_MODE");if(wm){
    const bool windowed=std::string(wm)=="windowed";
    if(idx==GWL_STYLE)value=windowed?((value&~WS_POPUP)|WS_OVERLAPPEDWINDOW):((value&~WS_OVERLAPPEDWINDOW)|WS_POPUP);
    if(idx==GWL_EXSTYLE)value=(value&~(WS_EX_TOPMOST|WS_EX_WINDOWEDGE))|WS_EX_APPWINDOW|(windowed?WS_EX_WINDOWEDGE:0);
   }}
   LONG r{};{LastError l(host);r=set?::SetWindowLongA(h,idx,value): ::GetWindowLongA(h,idx);}return done(unsigned(r),set?3:2);}
  // FormatMessageA from the system message table (optionally with LocalAlloc'd output, as Win32 does).
  if(n=="FormatMessageA"&&(arg(0)&FORMAT_MESSAGE_FROM_HMODULE)&&!(arg(0)&FORMAT_MESSAGE_FROM_SYSTEM)){const unsigned flags=arg(0),h=arg(1),id=arg(2),buf=arg(4),size=arg(5),va=arg(6);
   if(!host.paths.count(h))deny("FormatMessageA on a module without a mapped image",h);if(flags&~(FORMAT_MESSAGE_FROM_HMODULE|FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_IGNORE_INSERTS|FORMAT_MESSAGE_ARGUMENT_ARRAY|FORMAT_MESSAGE_MAX_WIDTH_MASK))deny("FormatMessageA flags outside the module-message model",flags);
   // RT_MESSAGETABLE (11) id 1 of the guest image: blocks {LowId, HighId, OffsetToEntries}; entries {Length, Flags, Text}.
   const unsigned d=resource(h,{11U,{}},{1U,{}});if(!d){host.last_error=ERROR_RESOURCE_TYPE_NOT_FOUND;return done(0,7);}const unsigned mt=h+load(d),blocks=load(mt);std::string text;bool found=false;
   for(unsigned b=0;b<blocks&&!found;++b){const unsigned lo=load(mt+4+12*b),hi=load(mt+8+12*b),off=load(mt+12+12*b);if(id<lo||id>hi)continue;unsigned e=mt+off;for(unsigned k=lo;k<id;++k)e+=load(e)&0xffff;
    const unsigned len=load(e)&0xffff,fl=load(e)>>16;if(fl)deny("Unicode message-table entry is not modelled",id);for(unsigned i=0;i+4<len;++i){const char c=char(runtime.memory().load<unsigned char>({e+4+i}));if(!c)break;text.push_back(c);}found=true;}
   if(!found){host.last_error=ERROR_MR_MID_NOT_FOUND;return done(0,7);}
   // Inserts: %n or %n!fmt!; a string insert takes a guest char*, numeric inserts take the 4-byte guest argument.
   std::vector<std::string>strs(100);std::vector<DWORD_PTR>argv(100);unsigned maxn=0;
   if(!(flags&FORMAT_MESSAGE_IGNORE_INSERTS)){const unsigned base_args=(flags&FORMAT_MESSAGE_ARGUMENT_ARRAY)?va:load(va);
    for(std::size_t i=0;i+1<text.size();++i){if(text[i]!='%'||!std::isdigit(static_cast<unsigned char>(text[i+1])))continue;std::size_t j=i+1;unsigned k=0;while(j<text.size()&&std::isdigit(static_cast<unsigned char>(text[j])))k=k*10+unsigned(text[j++]-'0');
     std::string fmt="s";if(j<text.size()&&text[j]=='!'){const auto e2=text.find('!',j+1);if(e2==std::string::npos)deny("Malformed message insert",id);fmt=text.substr(j+1,e2-j-1);}
     if(!k||k>99)continue;if(fmt.find("I64")!=std::string::npos||fmt.find('*')!=std::string::npos)deny("64-bit or width-argument message inserts are not modelled",id);maxn=std::max(maxn,k);const unsigned v=load(base_args+4*(k-1));
     if(fmt.back()=='s'){strs[k-1]=v?guest_string(v):std::string("(null)");argv[k-1]=reinterpret_cast<DWORD_PTR>(strs[k-1].c_str());}else argv[k-1]=(fmt.back()=='d'||fmt.back()=='i')?DWORD_PTR(std::int64_t(std::int32_t(v))):DWORD_PTR(v);}}
   char*out{};DWORD k{};{LastError l(host);k=::FormatMessageA(FORMAT_MESSAGE_FROM_STRING|FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_ARGUMENT_ARRAY|(flags&(FORMAT_MESSAGE_IGNORE_INSERTS|FORMAT_MESSAGE_MAX_WIDTH_MASK)),text.c_str(),0,0,reinterpret_cast<char*>(&out),0,reinterpret_cast<va_list*>(argv.data()));}
   apis.back()+="(module "+std::to_string(id)+")";if(!k)return done(0,7);const std::string t(out,k);::LocalFree(out);
   if(flags&FORMAT_MESSAGE_ALLOCATE_BUFFER){if(!writable(buf,4))deny("FormatMessageA buffer pointer outside the memory contract",buf);HLOCAL hl{};{LastError l(host);hl=::LocalAlloc(LMEM_FIXED,std::max<std::size_t>(t.size()+1,size));}if(!hl)return done(0,7);
    std::memcpy(hl,t.c_str(),t.size()+1);store(buf,publish_local(hl,unsigned(std::max<std::size_t>(t.size()+1,size))));return done(k,7);}
   if(t.size()+1>size){host.last_error=ERROR_INSUFFICIENT_BUFFER;return done(0,7);}if(!writable(buf,unsigned(t.size())+1))deny("FormatMessageA buffer outside the memory contract",buf);
   for(unsigned i=0;i<=t.size();++i)runtime.memory().store<unsigned char>({buf+i},static_cast<unsigned char>(t.c_str()[i]));return done(k,7);}
  if(n=="FormatMessageA"){const unsigned flags=arg(0),id=arg(2),lang=arg(3),buf=arg(4),size=arg(5);if(arg(6)&&!(flags&FORMAT_MESSAGE_IGNORE_INSERTS))deny("FormatMessageA insert arguments are not modelled (flags "+std::to_string(flags)+", source "+std::to_string(arg(1))+", id "+std::to_string(id)+")",arg(6));
   if((flags&~(FORMAT_MESSAGE_FROM_SYSTEM|FORMAT_MESSAGE_ALLOCATE_BUFFER|FORMAT_MESSAGE_IGNORE_INSERTS|FORMAT_MESSAGE_MAX_WIDTH_MASK))||!(flags&FORMAT_MESSAGE_FROM_SYSTEM))deny("FormatMessageA flags outside the system-message model",flags);
   char*text{};DWORD k{};{LastError l(host);k=::FormatMessageA((flags&~FORMAT_MESSAGE_ALLOCATE_BUFFER)|FORMAT_MESSAGE_ALLOCATE_BUFFER,nullptr,id,lang,reinterpret_cast<char*>(&text),0,nullptr);}
   apis.back()+="("+std::to_string(id)+")";if(!k){return done(0,7);}const std::string t(text,k);::LocalFree(text);
   if(flags&FORMAT_MESSAGE_ALLOCATE_BUFFER){if(!writable(buf,4))deny("FormatMessageA buffer pointer outside the memory contract",buf);HLOCAL h{};{LastError l(host);h=::LocalAlloc(LMEM_FIXED,std::max<std::size_t>(t.size()+1,size));}if(!h)return done(0,7);
    std::memcpy(h,t.c_str(),t.size()+1);store(buf,publish_local(h,unsigned(std::max<std::size_t>(t.size()+1,size))));return done(k,7);}
   if(t.size()+1>size){host.last_error=ERROR_INSUFFICIENT_BUFFER;return done(0,7);}if(!writable(buf,unsigned(t.size())+1))deny("FormatMessageA buffer outside the memory contract",buf);
   for(unsigned i=0;i<=t.size();++i)runtime.memory().store<unsigned char>({buf+i},static_cast<unsigned char>(t.c_str()[i]));return done(k,7);}
  // Timing: the real clocks (simulation timing comes from the platform as it did originally).
  if(n=="QueryPerformanceFrequency"||n=="QueryPerformanceCounter"){const unsigned a=arg(0);if(!writable(a,8))deny(n+" output outside the memory contract",a);LARGE_INTEGER v{};BOOL ok{};
   if(host.vclock()){v.QuadPart=n=="QueryPerformanceFrequency"?1000000LL:LONGLONG(host.vclock_query());ok=TRUE;}else{LastError l(host);ok=n=="QueryPerformanceFrequency"?::QueryPerformanceFrequency(&v): ::QueryPerformanceCounter(&v);}if(ok){store(a,unsigned(v.QuadPart));store(a+4,unsigned(std::uint64_t(v.QuadPart)>>32));}return done(ok?1U:0U,1);}
  if(n=="timeGetTime")return done(host.vclock()?unsigned(host.vclock_query()/1000):host.guest_tick(),0);
  if(n=="timeBeginPeriod"||n=="timeEndPeriod"){MMRESULT r{};{LastError l(host);r=n=="timeBeginPeriod"?::timeBeginPeriod(arg(0)): ::timeEndPeriod(arg(0));}return done(r,1);}
  if(n=="timeGetDevCaps"){const unsigned a=arg(0),z=arg(1);if(z!=8||!writable(a,8))deny("timeGetDevCaps record outside the memory contract",a);TIMECAPS tc{};MMRESULT r{};{LastError l(host);r=::timeGetDevCaps(&tc,sizeof(tc));}if(!r){store(a,tc.wPeriodMin);store(a+4,tc.wPeriodMax);}return done(r,2);}
  if(n=="CreateThread"){const unsigned sa=arg(0),ss=arg(1),start=arg(2),param=arg(3),fl=arg(4),pid=arg(5);if(sa)deny("CreateThread security attributes are not modelled",sa);
   if(fl&~unsigned(STACK_SIZE_PARAM_IS_A_RESERVATION))deny("CreateThread flags outside the model (suspended threads are not modelled)",fl);if(ss>0x100000)deny("CreateThread stack size outside the model",ss);
   if(!find(start))deny("Guest thread start routine has no lifted body",start);if(pid&&!writable(pid,4))deny("CreateThread thread-id output outside the memory contract",pid);
   unsigned slot=0;for(;slot<32;++slot){const unsigned lo=0x2e000000U+slot*0x100000U;if(std::none_of(host.threads.begin(),host.threads.end(),[&](const auto&t){return !t.exited&&t.stack_lo==lo;}))break;}if(slot==32)deny("Guest thread stack slots exhausted",0);
   const unsigned lo=0x2e000000U+slot*0x100000U;{bool bad{};try{runtime.memory().map({lo},0x100000,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked guest thread stack mapping",lo);}
   HANDLE ev{};{LastError l(host);ev=::CreateEventA(nullptr,TRUE,FALSE,nullptr);}if(!ev)deny("Thread object event",0);const unsigned gh=ghandle(ev);host.files.push_back(gh);
   const unsigned tid=0x10000U+4U*unsigned(host.threads.size()+1);host.threads.push_back({gh,tid,start,param,0,lo,lo+0x100000U,THREAD_PRIORITY_NORMAL,false});if(pid)store(pid,tid);
   char sb[16];std::snprintf(sb,sizeof sb,"%x",start);apis.back()+="(start "+std::string(sb)+", thread "+std::to_string(tid)+", run to completion)";const std::uint64_t at=apis_dropped+apis.size();
   const unsigned code=run_thread(host.threads.size()-1);apis.push_back("guest thread "+std::to_string(tid)+" exited "+std::to_string(code)+" after "+std::to_string(apis_dropped+apis.size()-at)+" services");host.last_error=0;return done(gh,6);}
  if(n=="Sleep"){if(host.vclock()){if(arg(0)==INFINITE)deny("Sleep(INFINITE) under the virtual clock",0);host.vclock_us+=std::uint64_t(arg(0))*1000;return done(0,1);}{LastError l(host);::Sleep(arg(0));}return done(0,1);}
  auto own_thread=[&](unsigned h)->HANDLE{const HANDLE x=hhandle(h);if(x!=::GetCurrentThread())deny(n+" on a thread other than the guest's own",h);return x;};
  if((n=="GetThreadPriority"||n=="SetThreadPriority")&&guest_thread(arg(0))){auto*t=guest_thread(arg(0));if(n=="GetThreadPriority")return done(unsigned(t->priority),1);t->priority=int(arg(1));apis.back()+="(guest thread "+std::to_string(t->tid)+": "+std::to_string(int(arg(1)))+")";return done(1,2);}
  if(n=="GetThreadPriority"){int p{};{LastError l(host);p=::GetThreadPriority(own_thread(arg(0)));}return done(unsigned(p),1);}
  if(n=="SetThreadPriority"){BOOL ok{};{LastError l(host);ok=::SetThreadPriority(own_thread(arg(0)),int(arg(1)));}apis.back()+="("+std::to_string(int(arg(1)))+")";return done(ok?1U:0U,2);}
  if(n=="GetPriorityClass"||n=="SetPriorityClass"){if(hhandle(arg(0))!=::GetCurrentProcess())deny(n+" on another process",arg(0));
   if(n=="GetPriorityClass"){DWORD c{};{LastError l(host);c=::GetPriorityClass(::GetCurrentProcess());}return done(c,1);}
   if(arg(1)==REALTIME_PRIORITY_CLASS)deny("SetPriorityClass(REALTIME) can starve the host system and is not authorized",arg(1));BOOL ok{};{LastError l(host);ok=::SetPriorityClass(::GetCurrentProcess(),arg(1));}return done(ok?1U:0U,2);}
  // GlobalMemoryStatus: real values in the x86 MEMORYSTATUS, clamped as WOW64 reports them to a 32-bit
  // image without IMAGE_FILE_LARGE_ADDRESS_AWARE (2 GB); the virtual fields use the 32-bit user space.
  if(n=="GlobalMemoryStatus"){const unsigned a=arg(0);if(!writable(a,32))deny("GlobalMemoryStatus record outside the memory contract",a);MEMORYSTATUSEX m{};m.dwLength=sizeof(m);{LastError l(host);::GlobalMemoryStatusEx(&m);}
   const bool laa=(load(0x400000+load(0x40003c)+22)&0xffff)&IMAGE_FILE_LARGE_ADDRESS_AWARE;const std::uint64_t cap=laa?0xffffffffull:0x7fffffffull;auto c=[&](DWORDLONG v){return unsigned(std::min<std::uint64_t>(v,cap));};
   const std::array<unsigned,8>v{32,m.dwMemoryLoad,c(m.ullTotalPhys),c(m.ullAvailPhys),c(m.ullTotalPageFile),c(m.ullAvailPageFile),laa?0xfffe0000U:0x7ffe0000U,laa?0xfffe0000U:0x7ffe0000U};for(unsigned i=0;i<8;++i)store(a+4*i,v[i]);return done(0,1);}
  // ---- files: real Win32 on paths resolved against the guest current directory; writes only inside the
  // game folder ----
  auto game_dir=[&]()->std::string{return std::filesystem::path(host.paths.at(0x400000)).parent_path().string();};
  if(host.cwd.empty())host.cwd=game_dir();
  auto resolve=[&](unsigned a)->std::string{std::string q=guest_string(a,MAX_PATH);if(q.empty())return q;
    if(q.size()>=2&&(std::tolower(static_cast<unsigned char>(q[0]))=='b'||std::tolower(static_cast<unsigned char>(q[0]))=='z')&&q[1]==':'){
     std::string sub=(q.size()>=3&&(q[2]=='\\'||q[2]=='/'))?q.substr(3):(q.size()>2?q.substr(2):std::string());
     std::filesystem::path pth=sub.empty()?std::filesystem::path(game_dir()):(std::filesystem::path(game_dir())/sub);
     if(!sub.empty()&&!std::filesystem::exists(pth)){
      std::filesystem::path alt=std::filesystem::path(game_dir())/"video"/sub;
      if(std::filesystem::exists(alt))pth=alt;
      else{alt=std::filesystem::path(game_dir())/"VIDEO"/sub;if(std::filesystem::exists(alt))pth=alt;}
     }
     return remaster_bank(pth.lexically_normal().make_preferred(),std::filesystem::path(game_dir()));
    }
    std::filesystem::path pth(q);if(pth.is_relative())pth=std::filesystem::path(host.cwd)/pth;return remaster_bank(pth.lexically_normal().make_preferred(),std::filesystem::path(game_dir()));};  auto in_game=[&](const std::string&q){const std::string root=game_dir();return q.size()>=root.size()&&_strnicmp(q.c_str(),root.c_str(),root.size())==0&&(q.size()==root.size()||q[root.size()]=='\\'||q[root.size()]=='/');};
  auto owned_file=[&](unsigned h){return std::find(host.files.begin(),host.files.end(),h)!=host.files.end();};
  if(n=="GetFileAttributesA"){const std::string q=resolve(arg(0));DWORD r{};{LastError l(host);r=::GetFileAttributesA(q.c_str());}apis.back()+="("+q+")";return done(r,1);}
  if(n=="GetCurrentDirectoryA"){const unsigned z=arg(0),a=arg(1);if(host.cwd.size()+1>z)return done(unsigned(host.cwd.size())+1,2);if(!writable(a,unsigned(host.cwd.size())+1))deny("GetCurrentDirectoryA buffer outside the memory contract",a);
   for(unsigned i=0;i<=host.cwd.size();++i)runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(host.cwd.c_str()[i]));return done(unsigned(host.cwd.size()),2);}
  if(n=="SetCurrentDirectoryA"){const std::string q=resolve(arg(0));const DWORD at=::GetFileAttributesA(q.c_str());if(at==INVALID_FILE_ATTRIBUTES||!(at&FILE_ATTRIBUTE_DIRECTORY)){host.last_error=at==INVALID_FILE_ATTRIBUTES?::GetLastError():ERROR_DIRECTORY;return done(0,1);}
   host.cwd=q;apis.back()+="("+q+")";host.last_error=0;return done(1,1);}
  if(n=="CreateDirectoryA"){const std::string q=resolve(arg(0));if(arg(1))deny("CreateDirectoryA security attributes are not modelled",arg(1));if(!in_game(q))deny("CreateDirectoryA outside the game folder is not authorized: "+q,arg(0));
   BOOL r{};{LastError l(host);r=::CreateDirectoryA(q.c_str(),nullptr);}apis.back()+="("+q+")="+std::to_string(r);return done(unsigned(r),2);}
  if(n=="CreateFileA"){const std::string q=resolve(arg(0));const unsigned acc=arg(1),share=arg(2),disp=arg(4),fl=arg(5);if(arg(6))deny("CreateFileA template file is not modelled",arg(6));SECURITY_ATTRIBUTES sa{};sa.nLength=sizeof(sa);
   if(arg(3)){const unsigned a=arg(3);if(!readable(a,12)||load(a)!=12||load(a+4))deny("CreateFileA security attributes with a descriptor are not modelled",a);sa.bInheritHandle=BOOL(load(a+8));}
   const bool writes=(acc&(GENERIC_WRITE|FILE_WRITE_DATA|FILE_APPEND_DATA))||disp==CREATE_ALWAYS||disp==CREATE_NEW||disp==TRUNCATE_EXISTING||disp==OPEN_ALWAYS;
   if(writes&&!in_game(q))deny("CreateFileA write access outside the game folder is not authorized: "+q,arg(0));if(fl&FILE_FLAG_OVERLAPPED)deny("Overlapped file I/O is not modelled",fl);
   HANDLE h{};{LastError l(host);h=::CreateFileA(q.c_str(),acc,share,arg(3)?&sa:nullptr,disp,fl,nullptr);}apis.back()+="("+q+")";if(h==INVALID_HANDLE_VALUE)return done(0xffffffffU,7);if(!writes&&(acc&GENERIC_READ)&&disp==OPEN_EXISTING)mw34::campaign::CampaignManager::instance().observe_file(q,true);const unsigned g2=ghandle(h);host.files.push_back(g2);if(!writes&&(acc&GENERIC_READ)&&disp==OPEN_EXISTING&&remaster_bank_target(q))host.replacement_bank_files.insert(g2);return done(g2,7);}
  if(n=="ReadFile"||n=="WriteFile"){const unsigned h=arg(0),a=arg(1),z=arg(2),outn=arg(3);if(!owned_file(h)&&h!=0xffffffffU&&h!=0)deny(n+" on a handle the guest does not own",h);if(arg(4))deny("Overlapped file I/O is not modelled",arg(4));
   if(n=="ReadFile"?!writable(a,z):!readable(a,z))deny(n+" buffer outside the memory contract",a);std::vector<unsigned char>buf(z);if(n=="WriteFile")for(unsigned i=0;i<z;++i)buf[i]=runtime.memory().load<unsigned char>({a+i});
   DWORD k{};BOOL ok{};{LastError l(host);ok=n=="ReadFile"?::ReadFile(hhandle(h),buf.data(),z,&k,nullptr): ::WriteFile(hhandle(h),buf.data(),z,&k,nullptr);}
   if(n=="ReadFile")for(DWORD i=0;i<k;++i)runtime.memory().store<unsigned char>({a+i},buf[i]);if(outn){if(!writable(outn,4))deny(n+" count outside the memory contract",outn);store(outn,k);}return done(ok?1U:0U,5);}
  if(n=="SetFilePointer"){const unsigned h=arg(0);if(!owned_file(h))deny("SetFilePointer on a handle the guest does not own",h);LONG hi=0;const unsigned ph=arg(2);if(ph){if(!writable(ph,4))deny("SetFilePointer high word outside the memory contract",ph);hi=LONG(load(ph));}
   const bool wide=mw34::texture_banks::unsigned_archive_seek(host.replacement_bank_files.count(h)!=0,arg(1),ph,arg(3),std::span<const unsigned>(returns.data(),depth));
   DWORD r{};{LastError l(host);r=::SetFilePointer(hhandle(h),LONG(arg(1)),(ph||wide)?&hi:nullptr,arg(3));}
   if(wide&&(++host.large_texture_seeks<=8||r==INVALID_SET_FILE_POINTER))std::fprintf(stderr,"Replacement texture seek: unsigned offset=%08x result=%08x error=%u\n",arg(1),unsigned(r),host.last_error);
   host.texture_seeks.push({h,arg(1),ph,arg(3),unsigned(r),host.last_error,host.replacement_bank_files.count(h)!=0,std::find(returns.begin(),returns.begin()+depth,0x00518e08U)!=returns.begin()+depth,wide});
   if(ph)store(ph,unsigned(hi));return done(r,4);}
  if(n=="GetFileSize"){const unsigned h=arg(0);if(!owned_file(h))deny("GetFileSize on a handle the guest does not own",h);DWORD hi{};DWORD r{};{LastError l(host);r=::GetFileSize(hhandle(h),&hi);}if(arg(1)){if(!writable(arg(1),4))deny("GetFileSize high word outside the memory contract",arg(1));store(arg(1),hi);}return done(r,2);}
  if(n=="GetFileType"&&owned_file(arg(0))){DWORD r{};{LastError l(host);r=::GetFileType(hhandle(arg(0)));}return done(r,1);}
  // The process standard handles were published to the guest by the native MSVCRT attach; closing one
  // retires it for the guest only (the host worker keeps its own console), and later guest use fails.
  auto std_handle=[&](unsigned h){for(DWORD k:{STD_INPUT_HANDLE,STD_OUTPUT_HANDLE,STD_ERROR_HANDLE}){const HANDLE x=::GetStdHandle(k);if(x&&x!=INVALID_HANDLE_VALUE&&ghandle(x)==h)return true;}return false;};
  // ---- services a statically linked CRT uses at startup (the staged codec's own CRT) ----
  auto guest_wide=[&](unsigned p,int cch){std::wstring w;if(cch<0){for(unsigned i=0;;++i){if(!readable(p+2*i,2))deny(n+" string outside the memory contract",p);const wchar_t c=wchar_t(runtime.memory().load<unsigned short>({p+2*i}));if(!c)break;w.push_back(c);}w.push_back(0);}
   else{if(!readable(p,unsigned(cch)*2))deny(n+" string outside the memory contract",p);for(int i=0;i<cch;++i)w.push_back(wchar_t(runtime.memory().load<unsigned short>({p+2*unsigned(i)})));}return w;};
  auto guest_narrow=[&](unsigned p,int cch){std::string t;if(cch<0){t=guest_string(p);t.push_back(0);}else{if(!readable(p,unsigned(cch)))deny(n+" string outside the memory contract",p);t.resize(size_t(cch));get_bytes(p,t.data(),unsigned(cch));}return t;};
  if(n=="GetFileType"){const unsigned h=arg(0);if((!std_handle(h)&&!owned_file(h))||std::find(host.closed_std.begin(),host.closed_std.end(),h)!=host.closed_std.end()){host.last_error=ERROR_INVALID_HANDLE;return done(FILE_TYPE_UNKNOWN,1);}DWORD r{};{LastError l(host);r=::GetFileType(hhandle(h));}return done(r,1);}
  if(n=="FlushFileBuffers"){const unsigned h=arg(0);if(!std_handle(h)&&!owned_file(h)){host.last_error=ERROR_INVALID_HANDLE;return done(0,1);}BOOL ok{};{LastError l(host);ok=::FlushFileBuffers(hhandle(h));}return done(ok?1U:0U,1);}
  if(n=="SetHandleCount")return done(arg(0),1);  // NT: no effect, returns its argument
  if(n=="OutputDebugStringA"){const std::string t=guest_string(arg(0));::OutputDebugStringA(t.c_str());return done(0,1);}
  if(n=="FreeResource")return done(0,1);  // Win32: resources need no freeing; returns FALSE
  if(n=="IsBadReadPtr"||n=="IsBadWritePtr"){const unsigned p=arg(0),z=arg(1);if(!z)return done(0,2);const bool ok=n=="IsBadReadPtr"?readable(p,z):writable(p,z);return done(ok?0U:1U,2);}
  if(n=="IsBadCodePtr"){const unsigned p=arg(0);return done(find(p)||(p>=0x400000&&p<game_end)||in_module(p,1,false)?0U:1U,1);}
  if(n=="GetSystemInfo"){const unsigned a=arg(0);if(!writable(a,36))deny("GetSystemInfo output outside the memory contract",a);SYSTEM_INFO si{};::GetNativeSystemInfo(&si);
   // 32-bit view (as a WOW64 process sees it): x86 processor, 4 KB pages, 64 KB granularity, user range 0x10000..0x7ffeffff.
   const std::array<unsigned,9>v{0/*PROCESSOR_ARCHITECTURE_INTEL*/,4096,0x10000,0x7ffeffff,unsigned(si.dwActiveProcessorMask),si.dwNumberOfProcessors,586,0x10000,0};
   for(unsigned i=0;i<9;++i)store(a+4*i,v[i]);store(a+32,6U|(unsigned(si.wProcessorRevision)<<16));return done(0,1);}
  if(n=="LocalLock"||n=="LocalHandle"){const unsigned h=arg(0);if(!host.local(h,1)){host.last_error=ERROR_INVALID_HANDLE;return done(0,1);}return done(h,1);}  // fixed blocks: handle == pointer
  if(n=="LocalUnlock"){if(!host.local(arg(0),1)){host.last_error=ERROR_INVALID_HANDLE;return done(0,1);}host.last_error=ERROR_NOT_LOCKED;return done(0,1);}
  if(n=="GetStringTypeW"){const unsigned type=arg(0),src=arg(1),out=arg(3);const int cch=int(arg(2));const auto w=guest_wide(src,cch);const int len=cch<0?int(w.size()):cch;if(!writable(out,unsigned(len)*2))deny("GetStringTypeW output outside the memory contract",out);
   std::vector<WORD>t(static_cast<size_t>(len));BOOL ok{};{LastError l(host);ok=::GetStringTypeW(type,w.data(),len,t.data());}if(ok)for(int i=0;i<len;++i)runtime.memory().store<unsigned short>({out+2*unsigned(i)},t[size_t(i)]);return done(ok?1U:0U,4);}
  if(n=="GetStringTypeA"){const unsigned lcid=arg(0),type=arg(1),src=arg(2),out=arg(4);const int cch=int(arg(3));const auto t0=guest_narrow(src,cch);const int len=cch<0?int(t0.size()):cch;if(!writable(out,unsigned(len)*2))deny("GetStringTypeA output outside the memory contract",out);
   std::vector<WORD>t(static_cast<size_t>(len));BOOL ok{};{LastError l(host);ok=::GetStringTypeA(lcid,type,t0.data(),len,t.data());}if(ok)for(int i=0;i<len;++i)runtime.memory().store<unsigned short>({out+2*unsigned(i)},t[size_t(i)]);return done(ok?1U:0U,5);}
  if(n=="CompareStringW"){const unsigned lcid=arg(0),fl=arg(1),a=arg(2),b=arg(4);const int na=int(arg(3)),nb=int(arg(5));
   const auto x=a?guest_wide(a,na):std::wstring(),y=b?guest_wide(b,nb):std::wstring();int result{};
   {LastError l(host);result=::CompareStringW(lcid,fl,a?x.data():nullptr,na,b?y.data():nullptr,nb);}return done(unsigned(result),6);}
  if(n=="LCMapStringW"){const unsigned lcid=arg(0),fl=arg(1),src=arg(2),dst=arg(4);const int cch=int(arg(3)),cd=int(arg(5));if(fl&LCMAP_SORTKEY)deny("LCMapStringW sort keys are not modelled",fl);const auto w=guest_wide(src,cch);
   std::wstring o(size_t(std::max(cd,0)),0);int r{};{LastError l(host);r=::LCMapStringW(lcid,fl,w.data(),cch<0?-1:cch,cd?o.data():nullptr,cd);}
   if(r&&cd){if(!writable(dst,unsigned(r)*2))deny("LCMapStringW output outside the memory contract",dst);for(int i=0;i<r;++i)runtime.memory().store<unsigned short>({dst+2*unsigned(i)},static_cast<unsigned short>(o[size_t(i)]));}return done(unsigned(r),6);}
  if(n=="LCMapStringA"){const unsigned lcid=arg(0),fl=arg(1),src=arg(2),dst=arg(4);const int cch=int(arg(3)),cd=int(arg(5));if(fl&LCMAP_SORTKEY)deny("LCMapStringA sort keys are not modelled",fl);const auto t0=guest_narrow(src,cch);
   std::string o(size_t(std::max(cd,0)),0);int r{};{LastError l(host);r=::LCMapStringA(lcid,fl,t0.data(),cch<0?-1:cch,cd?o.data():nullptr,cd);}
   if(r&&cd){if(!writable(dst,unsigned(r)))deny("LCMapStringA output outside the memory contract",dst);write_bytes(dst,o.data(),unsigned(r));}return done(unsigned(r),6);}
  if(n=="GetLocaleInfoA"||n=="GetLocaleInfoW"){const bool wide=n=="GetLocaleInfoW";const unsigned lcid=arg(0),type=arg(1),out=arg(2);const int cch=int(arg(3));int r{};
   if(wide){std::wstring o(size_t(std::max(cch,0)),0);{LastError l(host);r=::GetLocaleInfoW(lcid,type,cch?o.data():nullptr,cch);}if(r&&cch){if(!writable(out,unsigned(r)*2))deny(n+" output outside the memory contract",out);for(int i=0;i<r;++i)runtime.memory().store<unsigned short>({out+2*unsigned(i)},static_cast<unsigned short>(o[size_t(i)]));}}
   else{std::string o(size_t(std::max(cch,0)),0);{LastError l(host);r=::GetLocaleInfoA(lcid,type,cch?o.data():nullptr,cch);}if(r&&cch){if(!writable(out,unsigned(r)))deny(n+" output outside the memory contract",out);write_bytes(out,o.data(),unsigned(r));}}
   return done(unsigned(r),4);}
  // Guest standard handles are the guest values of the real process handles (closing one is virtualized).
  if(n=="GetStdHandle"){const DWORD k=arg(0);if(k!=STD_INPUT_HANDLE&&k!=STD_OUTPUT_HANDLE&&k!=STD_ERROR_HANDLE){host.last_error=ERROR_INVALID_HANDLE;return done(0xffffffffU,1);}
   const HANDLE x=::GetStdHandle(k);if(x==INVALID_HANDLE_VALUE)return done(0xffffffffU,1);const unsigned g2=x?ghandle(x):0U;if(std::find(host.closed_std.begin(),host.closed_std.end(),g2)!=host.closed_std.end())return done(0,1);return done(g2,1);}
  // ---- named page-file sections ----
  auto section_named=[&](const std::string&nm)->long{for(size_t i=0;i<host.sections.size();++i)if(!nm.empty()&&host.sections[i].handles&&_stricmp(host.sections[i].name.c_str(),nm.c_str())==0)return long(i);return -1;};
  auto section_handle=[&](size_t i){const unsigned tok=0x3f600000U+16U*(++host.section_serial);host.section_handles[tok]=i;++host.sections[i].handles;return tok;};
  auto section_release=[&](size_t i){auto&sc=host.sections[i];if(sc.handles||sc.views||!sc.base)return;for(unsigned p=sc.base;p<sc.base+sc.size;p+=4096U)if(host.vm.committed.erase(p)){bool bad{};try{runtime.memory().unmap({p});}catch(...){bad=true;}if(bad)deny("Checked section page release",p);}
   host.vm.reserved.erase(sc.base);sc.base=0;};
  if(n=="OpenFileMappingA"){const std::string nm=arg(2)?guest_string(arg(2)):std::string();const long i=section_named(nm);apis.back()+="("+nm+")";if(i<0){host.last_error=ERROR_FILE_NOT_FOUND;return done(0,3);}host.last_error=0;return done(section_handle(size_t(i)),3);}
  if(n=="CreateFileMappingA"){const std::string nm=arg(5)?guest_string(arg(5)):std::string();apis.back()+="("+nm+")";
   if(arg(0)!=0xffffffffU)deny("CreateFileMappingA of a file is not modelled (page-file sections only)",arg(0));if(arg(1))deny("CreateFileMappingA security attributes are not modelled",arg(1));
   if((arg(2)&0xff)!=PAGE_READWRITE||arg(3)||!arg(4))deny("CreateFileMappingA protection or size outside the model",arg(2));
   if(const long i=section_named(nm);i>=0){host.last_error=ERROR_ALREADY_EXISTS;return done(section_handle(size_t(i)),6);}
   host.sections.push_back({nm,(arg(4)+4095U)&~4095U,0,0,0});host.last_error=0;return done(section_handle(host.sections.size()-1),6);}
  if(n=="MapViewOfFile"){auto it=host.section_handles.find(arg(0));if(it==host.section_handles.end()){host.last_error=ERROR_INVALID_HANDLE;return done(0,5);}auto&sc=host.sections[it->second];
   if(arg(2)||arg(3)||(arg(4)&&arg(4)>sc.size))deny("MapViewOfFile at an offset or beyond the section is not modelled",arg(3));
   if(!sc.base){unsigned at=Host::VmState::lo;auto free_at=[&](unsigned b0){if(std::uint64_t(b0)+sc.size>Host::VmState::hi)return false;for(const auto&[r0,rn]:host.vm.reserved)if(b0<r0+rn&&r0<b0+((sc.size+0xffffU)&~0xffffU))return false;return true;};
    while(at<Host::VmState::hi&&!free_at(at))at+=0x10000U;if(at>=Host::VmState::hi){host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(0,5);}host.vm.reserved[at]=(sc.size+0xffffU)&~0xffffU;
    for(unsigned p=at;p<at+sc.size;p+=4096U){bool bad{};try{runtime.memory().map({p},4096,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked section page commit",p);host.vm.committed.insert(p);}sc.base=at;}
   ++sc.views;host.last_error=0;return done(sc.base,5);}
  if(n=="UnmapViewOfFile"){for(size_t i=0;i<host.sections.size();++i)if(host.sections[i].base&&host.sections[i].base==arg(0)&&host.sections[i].views){--host.sections[i].views;section_release(i);return done(1,1);}host.last_error=ERROR_INVALID_ADDRESS;return done(0,1);}
  if(n=="CloseHandle"&&host.section_handles.count(arg(0))){const size_t i=host.section_handles[arg(0)];host.section_handles.erase(arg(0));--host.sections[i].handles;section_release(i);return done(1,1);}
  if(n=="CloseHandle"&&std_handle(arg(0))&&std::find(host.closed_std.begin(),host.closed_std.end(),arg(0))==host.closed_std.end()){host.closed_std.push_back(arg(0));host.last_error=0;apis.back()+="(guest standard handle)";return done(1,1);}
  if((n=="ReadFile"||n=="WriteFile"||n=="GetFileType"||n=="CloseHandle")&&std::find(host.closed_std.begin(),host.closed_std.end(),arg(0))!=host.closed_std.end()){host.last_error=ERROR_INVALID_HANDLE;return done(n=="GetFileType"?unsigned(FILE_TYPE_UNKNOWN):0U,n=="ReadFile"||n=="WriteFile"?5:1);}
  // A FindFirstFile search handle is not a kernel handle: CloseHandle on it fails with ERROR_INVALID_HANDLE
  // and the search stays open (the original game closes one of its searches this way).
  if(n=="CloseHandle"&&std::any_of(host.finds.begin(),host.finds.end(),[&](const auto&f){return f.first==arg(0);})){host.last_error=ERROR_INVALID_HANDLE;apis.back()+="(search handle: fails)";return done(0,1);}
  // GetCurrentProcess/GetCurrentThread pseudo-handles: closing them has no effect (the real call on the real
  // pseudo-handle reports the result).
  if(n=="CloseHandle"&&(arg(0)==0xffffffffU||arg(0)==0xfffffffeU)){BOOL ok{};{LastError l(host);ok=::CloseHandle(reinterpret_cast<HANDLE>(std::intptr_t(std::int32_t(arg(0)))));}apis.back()+="(pseudo-handle)";return done(ok?1U:0U,1);}
  if(n=="CloseHandle"){const unsigned h=arg(0);auto it=std::find(host.files.begin(),host.files.end(),h);if(it==host.files.end())deny("CloseHandle on a handle the guest does not own (standard handles: "+std::to_string(ghandle(::GetStdHandle(STD_INPUT_HANDLE)))+","+std::to_string(ghandle(::GetStdHandle(STD_OUTPUT_HANDLE)))+","+std::to_string(ghandle(::GetStdHandle(STD_ERROR_HANDLE)))+")",h);BOOL ok{};{LastError l(host);ok=::CloseHandle(hhandle(h));}host.files.erase(it);host.replacement_bank_files.erase(h);return done(ok?1U:0U,1);}
  if(n=="FindFirstFileA"||n=="FindNextFileA"){const unsigned out=n=="FindFirstFileA"?arg(1):arg(1);if(!writable(out,320))deny(n+" record outside the memory contract",out);WIN32_FIND_DATAA fd{};static_assert(sizeof(WIN32_FIND_DATAA)==320);
   if(n=="FindFirstFileA"){const std::string q=resolve(arg(0));HANDLE h{};{LastError l(host);h=::FindFirstFileA(q.c_str(),&fd);}apis.back()+="("+q+")";if(h==INVALID_HANDLE_VALUE)return done(0xffffffffU,2);
    const unsigned g2=0x3a000000U+16U*unsigned(host.finds.size()+1);host.finds.push_back({g2,h});for(unsigned i=0;i<320;++i)runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&fd)[i]);return done(g2,2);}
   HANDLE fh{};for(const auto&[g3,hh]:host.finds)if(g3==arg(0))fh=hh;if(!fh)deny("FindNextFileA on a handle the guest does not own",arg(0));BOOL ok{};{LastError l(host);ok=::FindNextFileA(fh,&fd);}
   if(ok)for(unsigned i=0;i<320;++i)runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&fd)[i]);return done(ok?1U:0U,2);}
  if(n=="FindClose"){auto it=std::find_if(host.finds.begin(),host.finds.end(),[&](const auto&f){return f.first==arg(0);});if(it==host.finds.end())deny("FindClose on a handle the guest does not own",arg(0));BOOL ok{};{LastError l(host);ok=::FindClose(it->second);}host.finds.erase(it);return done(ok?1U:0U,1);}
  if(n=="GetFullPathNameA"){const std::string q=resolve(arg(0));const unsigned z=arg(1),a=arg(2),fp=arg(3);if(q.size()+1>z)return done(unsigned(q.size())+1,4);if(!writable(a,unsigned(q.size())+1))deny("GetFullPathNameA buffer outside the memory contract",a);
   for(unsigned i=0;i<=q.size();++i)runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(q.c_str()[i]));if(fp){if(!writable(fp,4))deny("GetFullPathNameA file part outside the memory contract",fp);const auto sl=q.find_last_of("\\/");store(fp,sl==std::string::npos?a:a+unsigned(sl)+1);}
   return done(unsigned(q.size()),4);}
  // USER32 rectangle helpers: the real function on host copies of the guest RECT/POINT words.
  auto get_rect=[&](unsigned a){if(!readable(a,16))deny(n+" RECT outside the memory contract",a);return RECT{LONG(load(a)),LONG(load(a+4)),LONG(load(a+8)),LONG(load(a+12))};};
  auto put_rect=[&](unsigned a,const RECT&r){if(!writable(a,16))deny(n+" RECT outside the memory contract",a);store(a,unsigned(r.left));store(a+4,unsigned(r.top));store(a+8,unsigned(r.right));store(a+12,unsigned(r.bottom));};
  if(n=="SetRectEmpty"){RECT r{};BOOL ok=::SetRectEmpty(&r);put_rect(arg(0),r);return done(ok?1U:0U,1);}
  if(n=="SetRect"){RECT r{};BOOL ok=::SetRect(&r,int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)));put_rect(arg(0),r);return done(ok?1U:0U,5);}
  if(n=="CopyRect"){const RECT r=get_rect(arg(1));put_rect(arg(0),r);return done(1,2);}
  if(n=="IsRectEmpty"){const RECT r=get_rect(arg(0));return done(::IsRectEmpty(&r)?1U:0U,1);}
  if(n=="EqualRect"){const RECT a1=get_rect(arg(0)),a2=get_rect(arg(1));return done(::EqualRect(&a1,&a2)?1U:0U,2);}
  if(n=="OffsetRect"){RECT r=get_rect(arg(0));BOOL ok=::OffsetRect(&r,int(arg(1)),int(arg(2)));put_rect(arg(0),r);return done(ok?1U:0U,3);}
  if(n=="InflateRect"){RECT r=get_rect(arg(0));BOOL ok=::InflateRect(&r,int(arg(1)),int(arg(2)));put_rect(arg(0),r);return done(ok?1U:0U,3);}
  if(n=="IntersectRect"||n=="UnionRect"||n=="SubtractRect"){const RECT a1=get_rect(arg(1)),a2=get_rect(arg(2));RECT r{};BOOL ok=n=="IntersectRect"?::IntersectRect(&r,&a1,&a2):n=="UnionRect"?::UnionRect(&r,&a1,&a2): ::SubtractRect(&r,&a1,&a2);put_rect(arg(0),r);return done(ok?1U:0U,3);}
  if(n=="PtInRect"){const RECT r=get_rect(arg(0));const POINT pt{LONG(arg(1)),LONG(arg(2))};return done(::PtInRect(&r,pt)?1U:0U,3);}
  // GetCommandLineA: the process command line the command-line carry published at 0x33000000 (the same
  // string MSVCRT's _acmdln holds).
  if(n=="GetCommandLineA"){const unsigned a=0x33000000;if(load(hs::aenvptr-0x4)!=a&&load(0x78037174)!=a)deny("Published guest command line differs from MSVCRT _acmdln",load(0x78037174));(void)guest_string(a);return done(a,0);}
  // ---- window management and messages (real USER32; guest window procedures via wnd_tramp) ----
  auto W=[&](unsigned i){return hwnd_of(arg(i));};
  auto rect_out=[&](unsigned a,const RECT&r){if(!writable(a,16))deny(n+" RECT outside the memory contract",a);store(a,unsigned(r.left));store(a+4,unsigned(r.top));store(a+8,unsigned(r.right));store(a+12,unsigned(r.bottom));};
  auto rect_in=[&](unsigned a){if(!readable(a,16))deny(n+" RECT outside the memory contract",a);return RECT{LONG(load(a)),LONG(load(a+4)),LONG(load(a+8)),LONG(load(a+12))};};
  if(n=="AdjustWindowRectEx"||n=="AdjustWindowRect"){RECT r=rect_in(arg(0));BOOL ok{};{LastError l(host);ok=n=="AdjustWindowRectEx"?::AdjustWindowRectEx(&r,arg(1),BOOL(arg(2)),arg(3)): ::AdjustWindowRect(&r,arg(1),BOOL(arg(2)));}rect_out(arg(0),r);return done(ok?1U:0U,n=="AdjustWindowRectEx"?4:3);}
  if(n=="GetClientRect"||n=="GetWindowRect"){RECT r{};BOOL ok{};{LastError l(host);ok=n=="GetClientRect"?::GetClientRect(W(0),&r): ::GetWindowRect(W(0),&r);}if(ok)rect_out(arg(1),r);return done(ok?1U:0U,2);}
  if(n=="ShowWindow"){BOOL r{};{LastError l(host);r=::ShowWindow(W(0),int(arg(1)));}apis.back()+="("+std::to_string(arg(1))+")";return done(r?1U:0U,2);}
  // Original MFC WM_DESTROY releases its Windows Help client. Forward the
  // observed HELP_QUIT contract to Windows and preserve the real result/error.
  if(n=="WinHelpA"){
   const unsigned command=arg(2),data=arg(3);
   if(command!=HELP_QUIT||data)deny("Unsupported Windows Help command or data",command);
   const std::string help=arg(1)?guest_string(arg(1)):std::string{};
   BOOL result{};{LastError l(host);result=::WinHelpA(W(0),arg(1)?help.c_str():nullptr,command,0);}
   std::fprintf(stderr,"Windows Help release: command=%u result=%d error=%u\n",command,int(result),host.last_error);
   return done(result?1U:0U,4);
  }
  if(n=="ShowOwnedPopups"){BOOL r{};{LastError l(host);r=::ShowOwnedPopups(W(0),BOOL(arg(1)));}return done(r?1U:0U,2);}  // reached from the game's WM_CLOSE handler
  if(n=="UpdateWindow"||n=="DestroyWindow"||n=="SetForegroundWindow"||n=="IsWindow"||n=="IsWindowVisible"||n=="IsIconic"||n=="IsZoomed"||n=="IsWindowEnabled"||n=="BringWindowToTop"){BOOL r{};{LastError l(host);const HWND h=W(0);
    r=n=="UpdateWindow"?::UpdateWindow(h):n=="DestroyWindow"?::DestroyWindow(h):n=="SetForegroundWindow"?::SetForegroundWindow(h):n=="IsWindow"?::IsWindow(h):n=="IsWindowVisible"?::IsWindowVisible(h):n=="IsIconic"?::IsIconic(h):n=="IsZoomed"?::IsZoomed(h):n=="IsWindowEnabled"?::IsWindowEnabled(h): ::BringWindowToTop(h);}
   if(n=="DestroyWindow"&&r){if(W(0)==host.display.window)mw34::display::exclusive().release();host.windows.erase(W(0));}return done(r?1U:0U,1);}
  if(n=="SetFocus"||n=="SetActiveWindow"||n=="GetParent"||n=="SetCapture"){HWND r{};{LastError l(host);r=n=="SetFocus"?::SetFocus(W(0)):n=="SetActiveWindow"?::SetActiveWindow(W(0)):n=="GetParent"?::GetParent(W(0)): ::SetCapture(W(0));}return done(r?gwnd(r):0,1);}
  if(n=="GetFocus"||n=="GetActiveWindow"||n=="GetForegroundWindow"||n=="GetDesktopWindow"||n=="GetCapture"){HWND r=n=="GetFocus"?::GetFocus():n=="GetActiveWindow"?::GetActiveWindow():n=="GetForegroundWindow"?::GetForegroundWindow():n=="GetDesktopWindow"?::GetDesktopWindow(): ::GetCapture();return done(r?gwnd(r):0,0);}
  if(n=="ReleaseCapture"){BOOL r=::ReleaseCapture();return done(r?1U:0U,0);}
  if(n=="GetWindow"){HWND r=::GetWindow(W(0),arg(1));return done(r?gwnd(r):0,2);}
  if(n=="MoveWindow"){BOOL r{};{LastError l(host);r=::MoveWindow(W(0),int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),BOOL(arg(5)));}return done(r?1U:0U,6);}
  if(n=="SetWindowPos"){const char*wm=std::getenv("MW34_WINDOW_MODE");if(W(0)==host.display.window&&wm&&mw34::vkscene::Renderer::remaster_width()&&int(arg(4))>0&&int(arg(4))<=800)return done(::SetWindowPos(W(0),nullptr,0,0,0,0,arg(6)|SWP_NOMOVE|SWP_NOSIZE|SWP_NOZORDER)?1U:0U,7);BOOL r{};{LastError l(host);r=::SetWindowPos(W(0),hwnd_of(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),int(arg(5)),arg(6));}return done(r?1U:0U,7);}
  if(n=="InvalidateRect"||n=="ValidateRect"){RECT r{};const bool has=arg(1)!=0;if(has)r=rect_in(arg(1));BOOL ok{};{LastError l(host);ok=n=="InvalidateRect"?::InvalidateRect(W(0),has?&r:nullptr,BOOL(arg(2))): ::ValidateRect(W(0),has?&r:nullptr);}return done(ok?1U:0U,n=="InvalidateRect"?3:2);}
  if(n=="SetWindowTextA"){const std::string t=arg(1)?menu_version::caption(guest_string(arg(1))):std::string();BOOL r{};{LastError l(host);r=::SetWindowTextA(W(0),arg(1)?t.c_str():nullptr);}return done(r?1U:0U,2);}
  if(n=="GetWindowTextA"){const unsigned a=arg(1),z=arg(2);if(!z)return done(0,3);if(!writable(a,z))deny("GetWindowTextA buffer outside the memory contract",a);std::vector<char>b(z);int k{};{LastError l(host);k=::GetWindowTextA(W(0),b.data(),int(z));}
   for(int i=0;i<=k&&unsigned(i)<z;++i)runtime.memory().store<unsigned char>({a+unsigned(i)},static_cast<unsigned char>(b[size_t(i)]));return done(unsigned(k),3);}
  if(n=="GetDC"&&arg(0)){HDC d{};{LastError l(host);d=::GetDC(W(0));}return done(d?ghandle(d):0,1);}
  if(n=="ReleaseDC"&&arg(0)){int r{};{LastError l(host);r=::ReleaseDC(W(0),static_cast<HDC>(hhandle(arg(1))));}return done(unsigned(r),2);}
  if(n=="ShowCursor")return done(unsigned(::ShowCursor(BOOL(arg(0)))),1);
  if(n=="SetCursor"){HCURSOR r=::SetCursor(static_cast<HCURSOR>(hhandle(arg(0))));return done(r?ghandle(r):0,1);}
  if(n=="ClipCursor"){RECT r{};const bool has=arg(0)!=0;if(has)r=rect_in(arg(0));BOOL ok=::ClipCursor(has?&r:nullptr);return done(ok?1U:0U,1);}
  // Under scripted input the player has no physical mouse: the system cursor is the scripted player's
  // virtual pointer (the host's real cursor is not moved).
  if(n=="SetCursorPos"&&host.scripted){host.vcursor={LONG(arg(0)),LONG(arg(1))};apis.back()+="(virtual)";return done(1,2);}
  if(n=="SetCursorPos"){BOOL ok=::SetCursorPos(int(arg(0)),int(arg(1)));return done(ok?1U:0U,2);}
  // MSG (x86, 28 bytes): hwnd, message, wParam, lParam, time, pt.
  auto msg_out=[&](unsigned a,const MSG&m){if(!writable(a,28))deny(n+" MSG outside the memory contract",a);const std::array<unsigned,7>v{m.hwnd?gwnd(m.hwnd):0,m.message,unsigned(m.wParam),unsigned(m.lParam),host.guest_tick_of(m.time),unsigned(m.pt.x),unsigned(m.pt.y)};for(unsigned i=0;i<7;++i)store(a+4*i,v[i]);};
  auto msg_in=[&](unsigned a){if(!readable(a,28))deny(n+" MSG outside the memory contract",a);MSG m{};m.hwnd=hwnd_of(load(a));m.message=load(a+4);m.wParam=WPARAM(load(a+8));{const unsigned lv=load(a+12);if(void*hp=token_handle(lv))m.lParam=reinterpret_cast<LPARAM>(hp);else m.lParam=LPARAM(std::int64_t(std::int32_t(lv)));}m.time=host.host_tick_of(load(a+16));m.pt.x=LONG(load(a+20));m.pt.y=LONG(load(a+24));return m;};
  // Deterministic replays (virtual clock): queued messages produced by the real desktop rather than the game or the
  // script are removed before the game sees them - real-cursor mouse moves (the scripted cursor is virtual), the
  // undocumented system message 0x0060 and WM_DWMNCRENDERINGCHANGED - whose number varied between runs and shifted
  // later frames. Interactive play receives every message.
  auto replay_drop=[&](UINT msg){return host.vclock()&&(msg==0x0060||msg==WM_MOUSEMOVE||msg==WM_NCMOUSEMOVE||msg==WM_MOUSEHOVER||msg==WM_MOUSELEAVE||msg==WM_NCMOUSELEAVE||msg==0x031F);};
  if(n=="PeekMessageA"||n=="GetMessageA"){MSG m{};BOOL r{};for(;;){{LastError l(host);r=n=="PeekMessageA"?::PeekMessageA(&m,hwnd_of(arg(1)),arg(2),arg(3),arg(4)): ::GetMessageA(&m,hwnd_of(arg(1)),arg(2),arg(3));}
    if(!(r&&r!=-1&&replay_drop(m.message)))break;if(n=="PeekMessageA"&&!(arg(4)&PM_REMOVE)){MSG x{};LastError l(host);::PeekMessageA(&x,m.hwnd,m.message,m.message,PM_REMOVE);}}
   if(r&&r!=-1){const auto lw=static_cast<std::int64_t>(m.lParam);if(lw!=std::int64_t(std::int32_t(lw)))m.lParam=LPARAM(handle_token(reinterpret_cast<void*>(m.lParam)));msg_out(arg(0),m);}  /* host pointers (system timer callbacks) become tokens */return done(unsigned(r),n=="PeekMessageA"?5:4);}
  if(n=="TranslateMessage"){const MSG m=msg_in(arg(0));return done(::TranslateMessage(&m)?1U:0U,1);}
  if(n=="DispatchMessageA"){const MSG m=msg_in(arg(0));LRESULT r{};{LastError l(host);r=::DispatchMessageA(&m);}return done(unsigned(std::int32_t(r)),1);}
  if(n=="PostMessageA"||n=="SendMessageA"){const unsigned m=arg(1);if(pointer_message(m))deny(n+" of a pointer message is not modelled: "+std::to_string(m),m);LRESULT r{};
   {LastError l(host);r=n=="PostMessageA"?LRESULT(::PostMessageA(W(0),m,WPARAM(arg(2)),LPARAM(std::int64_t(std::int32_t(arg(3)))))): ::SendMessageA(W(0),m,WPARAM(arg(2)),LPARAM(std::int64_t(std::int32_t(arg(3)))));}return done(unsigned(std::int32_t(r)),4);}
  if(n=="PostQuitMessage"){::PostQuitMessage(int(arg(0)));return done(0,1);}
  if(n=="MessageBoxExA"){const std::string t=arg(1)?guest_string(arg(1)):std::string(),c=arg(2)?guest_string(arg(2)):std::string();deny("MessageBoxExA would block on a modal dialog: ["+c+"] "+t,arg(3));}
  if(n=="MessageBoxA"){const std::string t=arg(1)?guest_string(arg(1)):std::string(),c=arg(2)?guest_string(arg(2)):std::string();deny("MessageBoxA would block on a modal dialog: ["+c+"] "+t,arg(3));}
  // Class words: GCL_WNDPROC (-24, x86) is the guest class procedure (or a host procedure token),
  // GCL_HMODULE (-16) the guest instance; others are real.
  if(n=="GetClassLongA"||n=="SetClassLongA"){const HWND h=hwnd_of(arg(0));const int idx=int(arg(1));const bool set=n=="SetClassLongA";
   if(idx==-24){if(set)deny("SetClassLongA(GCL_WNDPROC) is not modelled",arg(2));const unsigned g2=class_guest_proc(h);return done(g2?g2:host_proc_token(reinterpret_cast<WNDPROC>(::GetClassLongPtrA(h,GCLP_WNDPROC))),2);}
   if(idx==-16){if(set)deny("SetClassLongA(GCL_HMODULE) is not modelled",arg(2));return done(guest_instance(reinterpret_cast<HINSTANCE>(::GetClassLongPtrA(h,GCLP_HMODULE))),2);}
   if(idx==-8)deny("GCL_MENUNAME is not modelled",0);
   DWORD r{};{LastError l(host);r=set?::SetClassLongA(h,idx,LONG(arg(2))): ::GetClassLongA(h,idx);}return done(r,set?3:2);}
  if(n=="GlobalGetAtomNameA"||n=="GetAtomNameA"){const unsigned a=arg(1),z=arg(2);if(!z)return done(0,3);if(!writable(a,z))deny(n+" buffer outside the memory contract",a);std::vector<char>b(z);UINT k{};
   {LastError l(host);k=n=="GlobalGetAtomNameA"?::GlobalGetAtomNameA(ATOM(arg(0)),b.data(),int(z)): ::GetAtomNameA(ATOM(arg(0)),b.data(),int(z));}for(UINT i=0;i<=k&&i<z;++i)runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(b[i]));return done(k,3);}
  if(n=="GlobalAddAtomA"||n=="GlobalFindAtomA"||n=="AddAtomA"||n=="FindAtomA"){const std::string t=arg(0)>=0x10000?guest_string(arg(0)):std::string();const char*q=arg(0)<0x10000?MAKEINTATOM(arg(0)):t.c_str();ATOM r{};
   {LastError l(host);r=n=="GlobalAddAtomA"?::GlobalAddAtomA(q):n=="GlobalFindAtomA"?::GlobalFindAtomA(q):n=="AddAtomA"?::AddAtomA(q): ::FindAtomA(q);}return done(r,1);}
  if(n=="GlobalDeleteAtom"||n=="DeleteAtom"){ATOM r{};{LastError l(host);r=n=="GlobalDeleteAtom"?::GlobalDeleteAtom(ATOM(arg(0))): ::DeleteAtom(ATOM(arg(0)));}return done(r,1);}
  // Window properties hold guest words (sign-extended into the host HANDLE slot and back).
  if(n=="SetPropA"||n=="GetPropA"||n=="RemovePropA"){const std::string t=arg(1)>=0x10000?guest_string(arg(1)):std::string();const char*q=arg(1)<0x10000?MAKEINTATOM(arg(1)):t.c_str();
   if(n=="SetPropA"){BOOL r{};{LastError l(host);r=::SetPropA(hwnd_of(arg(0)),q,reinterpret_cast<HANDLE>(std::intptr_t(std::int32_t(arg(2)))));}return done(r?1U:0U,3);}
   HANDLE r{};{LastError l(host);r=n=="GetPropA"?::GetPropA(hwnd_of(arg(0)),q): ::RemovePropA(hwnd_of(arg(0)),q);}return done(unsigned(reinterpret_cast<std::intptr_t>(r)),2);}
  if(n=="BeginDeferWindowPos"){HDWP r{};{LastError l(host);r=::BeginDeferWindowPos(int(arg(0)));}return done(r?ghandle(r):0,1);}
  if(n=="DeferWindowPos"){HDWP r{};{LastError l(host);r=::DeferWindowPos(static_cast<HDWP>(hhandle(arg(0))),hwnd_of(arg(1)),hwnd_of(arg(2)),int(arg(3)),int(arg(4)),int(arg(5)),int(arg(6)),arg(7));}return done(r?ghandle(r):0,8);}
  if(n=="EndDeferWindowPos"){BOOL r{};{LastError l(host);r=::EndDeferWindowPos(static_cast<HDWP>(hhandle(arg(0))));}return done(r?1U:0U,1);}
  // ---- plain-argument USER32/GDI batch (handles and integers only; real calls) ----
  {auto H=[&](unsigned i){return hhandle(arg(i));};auto W2=[&](unsigned i){return hwnd_of(arg(i));};auto wr=[&](HWND x){return x?gwnd(x):0U;};auto gr=[&](const void*x){return x?ghandle(x):0U;};
   if(n=="GetTopWindow")return done(wr(::GetTopWindow(W2(0))),1);
   if(n=="GetDlgItem")return done(wr(::GetDlgItem(W2(0),int(arg(1)))),2);
   if(n=="GetDlgCtrlID")return done(unsigned(::GetDlgCtrlID(W2(0))),1);
   if(n=="IsChild")return done(::IsChild(W2(0),W2(1))?1U:0U,2);
   if(n=="EnableWindow")return done(::EnableWindow(W2(0),BOOL(arg(1)))?1U:0U,2);
   if(n=="GetMenu")return done(gr(::GetMenu(W2(0))),1);
   if(n=="GetSystemMenu")return done(gr(::GetSystemMenu(W2(0),BOOL(arg(1)))),2);
   if(n=="DrawMenuBar")return done(::DrawMenuBar(W2(0))?1U:0U,1);
   if(n=="GetSubMenu")return done(gr(::GetSubMenu(static_cast<HMENU>(H(0)),int(arg(1)))),2);
   if(n=="GetMenuItemCount")return done(unsigned(::GetMenuItemCount(static_cast<HMENU>(H(0)))),1);
   if(n=="GetMenuState")return done(::GetMenuState(static_cast<HMENU>(H(0)),arg(1),arg(2)),3);
   if(n=="EnableMenuItem")return done(unsigned(::EnableMenuItem(static_cast<HMENU>(H(0)),arg(1),arg(2))),3);
   if(n=="CheckMenuItem")return done(::CheckMenuItem(static_cast<HMENU>(H(0)),arg(1),arg(2)),3);
   if(n=="GetWindowDC")return done(gr(::GetWindowDC(W2(0))),1);
   // Real USER32 scalar mapping for fresh pilot-name entry.
   if(n=="MapVirtualKeyA")return done(::MapVirtualKeyA(arg(0),arg(1)),2);
   if(n=="ToAscii"){
    const unsigned keys=arg(2),out=arg(3);
    if(keys&&!readable(keys,256))deny("ToAscii key state outside the memory contract",keys);
    if(!writable(out,2))deny("ToAscii output outside the memory contract",out);
    BYTE state[256]{};if(keys)for(unsigned i=0;i<256;++i)state[i]=runtime.memory().load<unsigned char>({keys+i});
    WORD translated{};int count{};{LastError error(host);count=::ToAscii(arg(0),arg(1),keys?state:nullptr,&translated,arg(4));}
    if(count)runtime.memory().store<unsigned short>({out},translated);
    return done(unsigned(count),5);
   }
   if(n=="GetKeyState")return done(unsigned(std::int32_t(::GetKeyState(int(arg(0))))),1);
   if(n=="GetAsyncKeyState")return done(unsigned(std::int32_t(::GetAsyncKeyState(int(arg(0))))),1);
   if(n=="GetKeyboardState"){const unsigned a=arg(0);if(!writable(a,256))deny("GetKeyboardState buffer outside the memory contract",a);BYTE k[256]{};BOOL ok=::GetKeyboardState(k);if(ok)for(unsigned i=0;i<256;++i)runtime.memory().store<unsigned char>({a+i},k[i]);return done(ok?1U:0U,1);}
   if(n=="ClientToScreen"||n=="ScreenToClient"){const unsigned a=arg(1);if(!writable(a,8))deny(n+" POINT outside the memory contract",a);POINT pt{LONG(load(a)),LONG(load(a+4))};if(n=="ClientToScreen")frontend_input_point(pt,true,W2(0));BOOL ok=n=="ClientToScreen"?::ClientToScreen(W2(0),&pt): ::ScreenToClient(W2(0),&pt);if(ok&&n=="ScreenToClient")frontend_input_point(pt,false,W2(0));store(a,unsigned(pt.x));store(a+4,unsigned(pt.y));return done(ok?1U:0U,2);}
   if(n=="MapWindowPoints"){const unsigned a=arg(2),k=arg(3);if(k>64||!writable(a,8*k))deny("MapWindowPoints points outside the memory contract",a);std::vector<POINT>p(k);for(unsigned i=0;i<k;++i)p[i]={LONG(load(a+8*i)),LONG(load(a+8*i+4))};
    const int r=::MapWindowPoints(W2(0),W2(1),p.data(),k);for(unsigned i=0;i<k;++i){store(a+8*i,unsigned(p[i].x));store(a+8*i+4,unsigned(p[i].y));}return done(unsigned(r),4);}
   if(n=="GetWindowThreadProcessId"){DWORD pid{};const DWORD t=::GetWindowThreadProcessId(W2(0),&pid);if(arg(1)){if(!writable(arg(1),4))deny("GetWindowThreadProcessId output outside the memory contract",arg(1));store(arg(1),pid);}return done(t,2);}
   if(n=="GetClassNameA"){const unsigned a=arg(1),z=arg(2);if(!z)return done(0,3);if(!writable(a,z))deny("GetClassNameA buffer outside the memory contract",a);std::vector<char>c(z);const int k=::GetClassNameA(W2(0),c.data(),int(z));for(int i=0;i<=k&&unsigned(i)<z;++i)runtime.memory().store<unsigned char>({a+unsigned(i)},static_cast<unsigned char>(c[size_t(i)]));return done(unsigned(k),3);}
   if(n=="IsWindowUnicode")return done(::IsWindowUnicode(W2(0))?1U:0U,1);
   if(n=="GetLastActivePopup")return done(wr(::GetLastActivePopup(W2(0))),1);
   if(n=="RedrawWindow"){RECT r{};const bool has=arg(1)!=0;if(has){if(!readable(arg(1),16))deny("RedrawWindow RECT outside the memory contract",arg(1));r={LONG(load(arg(1))),LONG(load(arg(1)+4)),LONG(load(arg(1)+8)),LONG(load(arg(1)+12))};}
    if(arg(2))deny("RedrawWindow with a region is not modelled",arg(2));return done(::RedrawWindow(W2(0),has?&r:nullptr,nullptr,arg(3))?1U:0U,4);}
   if(n=="SetTimer"){if(arg(3))deny("SetTimer with a timer callback is not modelled",arg(3));return done(unsigned(::SetTimer(W2(0),UINT_PTR(arg(1)),arg(2),nullptr)),4);}
   if(n=="KillTimer")return done(::KillTimer(W2(0),UINT_PTR(arg(1)))?1U:0U,2);
   if(n=="MessageBeep")return done(::MessageBeep(arg(0))?1U:0U,1);
   if(n=="InSendMessage")return done(::InSendMessage()?1U:0U,0);
   if(n=="GetQueueStatus")return done(::GetQueueStatus(arg(0)),1);
   if(n=="WaitMessage")return done(::WaitMessage()?1U:0U,0);
   if(n=="GetUpdateRect"){RECT r{};const BOOL ok=::GetUpdateRect(W2(0),arg(1)?&r:nullptr,BOOL(arg(2)));if(arg(1)){if(!writable(arg(1),16))deny("GetUpdateRect RECT outside the memory contract",arg(1));store(arg(1),unsigned(r.left));store(arg(1)+4,unsigned(r.top));store(arg(1)+8,unsigned(r.right));store(arg(1)+12,unsigned(r.bottom));}return done(ok?1U:0U,3);}
   // PAINTSTRUCT (x86 64 bytes: hdc, fErase, rcPaint, fRestore, fIncUpdate, rgbReserved[32]).
   if(n=="BeginPaint"){const unsigned a=arg(1);if(!writable(a,64))deny("BeginPaint PAINTSTRUCT outside the memory contract",a);PAINTSTRUCT ps{};HDC d=::BeginPaint(W2(0),&ps);
    const std::array<unsigned,8>v{gr(d),unsigned(ps.fErase),unsigned(ps.rcPaint.left),unsigned(ps.rcPaint.top),unsigned(ps.rcPaint.right),unsigned(ps.rcPaint.bottom),unsigned(ps.fRestore),unsigned(ps.fIncUpdate)};for(unsigned i=0;i<8;++i)store(a+4*i,v[i]);
    for(unsigned i=0;i<32;++i)runtime.memory().store<unsigned char>({a+32+i},ps.rgbReserved[i]);host.paints[a]=ps;return done(gr(d),2);}
   if(n=="EndPaint"){auto it=host.paints.find(arg(1));if(it==host.paints.end())deny("EndPaint without its BeginPaint",arg(1));const BOOL ok=::EndPaint(W2(0),&it->second);host.paints.erase(it);return done(ok?1U:0U,2);}
   if(n=="FillRect"){if(!readable(arg(1),16))deny("FillRect RECT outside the memory contract",arg(1));const RECT r{LONG(load(arg(1))),LONG(load(arg(1)+4)),LONG(load(arg(1)+8)),LONG(load(arg(1)+12))};
    return done(unsigned(::FillRect(static_cast<HDC>(H(0)),&r,reinterpret_cast<HBRUSH>(std::intptr_t(std::int32_t(arg(2)))))),3);}
   // GDI
   if(n=="SelectObject")return done(gr(::SelectObject(static_cast<HDC>(H(0)),H(1))),2);
   if(n=="CreateCompatibleDC")return done(gr(::CreateCompatibleDC(static_cast<HDC>(H(0)))),1);
   if(n=="CreateCompatibleBitmap")return done(gr(::CreateCompatibleBitmap(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)))),3);
   if(n=="DeleteDC")return done(::DeleteDC(static_cast<HDC>(H(0)))?1U:0U,1);
   if(n=="CreateSolidBrush")return done(gr(::CreateSolidBrush(arg(0))),1);
   if(n=="CreatePen")return done(gr(::CreatePen(int(arg(0)),int(arg(1)),arg(2))),3);
   if(n=="BitBlt")return done(::BitBlt(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),static_cast<HDC>(H(5)),int(arg(6)),int(arg(7)),arg(8))?1U:0U,9);
   if(n=="StretchBlt")return done(::StretchBlt(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),static_cast<HDC>(H(5)),int(arg(6)),int(arg(7)),int(arg(8)),int(arg(9)),arg(10))?1U:0U,11);
   if(n=="PatBlt")return done(::PatBlt(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),arg(5))?1U:0U,6);
   if(n=="SetBkMode")return done(unsigned(::SetBkMode(static_cast<HDC>(H(0)),int(arg(1)))),2);
   if(n=="SetTextColor")return done(::SetTextColor(static_cast<HDC>(H(0)),arg(1)),2);
   if(n=="SetBkColor")return done(::SetBkColor(static_cast<HDC>(H(0)),arg(1)),2);
   if(n=="SetTextAlign")return done(::SetTextAlign(static_cast<HDC>(H(0)),arg(1)),2);
   if(n=="SetMapMode")return done(unsigned(::SetMapMode(static_cast<HDC>(H(0)),int(arg(1)))),2);
   if(n=="SaveDC")return done(unsigned(::SaveDC(static_cast<HDC>(H(0)))),1);
   if(n=="RestoreDC")return done(::RestoreDC(static_cast<HDC>(H(0)),int(arg(1)))?1U:0U,2);
   if(n=="GetPixel")return done(::GetPixel(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2))),3);
   if(n=="SetPixel")return done(::SetPixel(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)),arg(3)),4);
   if(n=="TextOutA"){const unsigned k=arg(4);if(k>4096||!readable(arg(3),k))deny("TextOutA text outside the memory contract",arg(3));std::string t(k,'\0');for(unsigned i=0;i<k;++i)t[i]=char(runtime.memory().load<unsigned char>({arg(3)+i}));
    return done(::TextOutA(static_cast<HDC>(H(0)),int(arg(1)),int(arg(2)),t.data(),int(k))?1U:0U,5);}
   if(n=="GetTextExtentPoint32A"||n=="GetTextExtentPointA"){const unsigned k=arg(2),out=arg(3);if(k>4096||!readable(arg(1),k)||!writable(out,8))deny(n+" arguments outside the memory contract",arg(1));std::string t(k,'\0');for(unsigned i=0;i<k;++i)t[i]=char(runtime.memory().load<unsigned char>({arg(1)+i}));
    SIZE z{};const BOOL ok=::GetTextExtentPoint32A(static_cast<HDC>(H(0)),t.data(),int(k),&z);store(out,unsigned(z.cx));store(out+4,unsigned(z.cy));return done(ok?1U:0U,4);}
   if(n=="GetTextMetricsA"){const unsigned a=arg(1);static_assert(sizeof(TEXTMETRICA)==56);if(!writable(a,56))deny("GetTextMetricsA output outside the memory contract",a);TEXTMETRICA tm{};const BOOL ok=::GetTextMetricsA(static_cast<HDC>(H(0)),&tm);
    if(ok)for(unsigned i=0;i<56;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&tm)[i]);return done(ok?1U:0U,2);}
   if(n=="CreateFontIndirectA"){const unsigned a=arg(0);static_assert(sizeof(LOGFONTA)==60);if(!readable(a,60))deny("LOGFONTA outside the memory contract",a);LOGFONTA lf{};for(unsigned i=0;i<60;++i)reinterpret_cast<unsigned char*>(&lf)[i]=runtime.memory().load<unsigned char>({a+i});return done(gr(::CreateFontIndirectA(&lf)),1);}
  }
  if(n=="GetLogicalDriveStringsA"){const unsigned z=arg(0),a=arg(1);std::vector<char>b(std::max(z,1U));DWORD k{};{LastError l(host);k=::GetLogicalDriveStringsA(z,b.data());}
    std::vector<char>out;out.push_back('B');out.push_back(':');out.push_back('\\');out.push_back('\0');
    for(DWORD i=0;i<k;++i)out.push_back(b[i]);
    if(out.empty()||out.back()!='\0')out.push_back('\0');
    DWORD total=DWORD(out.size()>0?out.size()-1:0);
    if(z==0||z<=total){apis.back()+="(virtual B: + drives need "+std::to_string(total+1)+")";return done(total+1,2);}
    if(!writable(a,DWORD(out.size())))deny("GetLogicalDriveStringsA buffer outside the memory contract",a);
    for(size_t i=0;i<out.size();++i)runtime.memory().store<unsigned char>({a+unsigned(i)},static_cast<unsigned char>(out[i]));
    std::string list;for(size_t i=0;i<total;++i)list.push_back(out[i]?out[i]:' ');apis.back()+="("+list+")";return done(total,2);}
  if(n=="GetDriveTypeA"){const std::string r=arg(0)?guest_string(arg(0)):std::string();UINT t{};
    if(_strnicmp(r.c_str(),"B:",2)==0||_strnicmp(r.c_str(),"B:\\",3)==0||_strnicmp(r.c_str(),"Z:",2)==0||_strnicmp(r.c_str(),"Z:\\",3)==0){
     t=DRIVE_CDROM;
    }else{LastError l(host);t=::GetDriveTypeA(arg(0)?r.c_str():nullptr);}
    apis.back()+="("+r+")="+std::to_string(t);return done(t,1);}
  if(n=="GetVolumeInformationA"){const std::string r=arg(0)?guest_string(arg(0)):std::string();const unsigned nb=arg(1),nz=arg(2),ser=arg(3),mcl=arg(4),fl=arg(5),fb=arg(6),fz=arg(7);
    if(_strnicmp(r.c_str(),"B:",2)==0||_strnicmp(r.c_str(),"B:\\",3)==0||_strnicmp(r.c_str(),"Z:",2)==0||_strnicmp(r.c_str(),"Z:\\",3)==0){
     std::string volName="MW3";
     const char*pm=std::getenv("MW34_PIRATES_MOON");
     if(pm&&*pm)volName="MW3 PM";
     else{std::string gd=game_dir();for(char&c:gd)c=char(std::tolower(static_cast<unsigned char>(c)));if(gd.find("pirate")!=std::string::npos)volName="MW3 PM";}
     const std::string fsName="CDFS";const DWORD s1=0xFE05F614,m1=255,f1=FS_CASE_IS_PRESERVED|FS_UNICODE_STORED_ON_DISK;
     auto put=[&](unsigned addr,const std::string&s,unsigned maxz){if(!addr||!maxz)return;if(!writable(addr,maxz))deny("GetVolumeInformationA buffer outside the memory contract",addr);const unsigned lim=std::min<unsigned>(maxz,unsigned(s.size()+1));for(unsigned i=0;i<lim;++i)runtime.memory().store<unsigned char>({addr+i},i<s.size()?static_cast<unsigned char>(s[i]):0);};
     put(nb,volName,nz);put(fb,fsName,fz);if(ser&&writable(ser,4))store(ser,s1);if(mcl&&writable(mcl,4))store(mcl,m1);if(fl&&writable(fl,4))store(fl,f1);apis.back()+="("+r+" virtual CD)="+volName;return done(1U,8);}
    std::vector<char>vn(std::max(nz,1U)),fn(std::max(fz,1U));DWORD s1{},m1{},f1{};BOOL ok{};
    {LastError l(host);ok=::GetVolumeInformationA(arg(0)?r.c_str():nullptr,nb?vn.data():nullptr,nz,ser?&s1:nullptr,mcl?&m1:nullptr,fl?&f1:nullptr,fb?fn.data():nullptr,fz);}apis.back()+="("+r+")="+std::to_string(ok);
    if(ok){auto put=[&](unsigned a,const std::vector<char>&v,unsigned z){if(!a)return;if(!writable(a,z))deny("GetVolumeInformationA buffer outside the memory contract",a);for(unsigned i=0;i<z;++i){runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(v[i]));if(!v[i])break;}};
     put(nb,vn,nz);put(fb,fn,fz);for(auto[a,v]:{std::pair<unsigned,DWORD>{ser,s1},{mcl,m1},{fl,f1}})if(a){if(!writable(a,4))deny("GetVolumeInformationA output outside the memory contract",a);store(a,v);}}return done(ok?1U:0U,8);}
  // Time conversions: FILETIME (8), SYSTEMTIME (16) and TIME_ZONE_INFORMATION (172) share the x86/x64 layout.
  {auto rd=[&](unsigned a,void*p,unsigned z){if(!readable(a,z))deny(n+" input outside the memory contract",a);get_bytes(a,p,z);};auto wrb=[&](unsigned a,const void*p,unsigned z){if(!writable(a,z))deny(n+" output outside the memory contract",a);const auto*b=static_cast<const unsigned char*>(p);for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);};
   if(n=="FileTimeToLocalFileTime"||n=="LocalFileTimeToFileTime"){FILETIME i{},o{};rd(arg(0),&i,8);BOOL ok=n=="FileTimeToLocalFileTime"?::FileTimeToLocalFileTime(&i,&o): ::LocalFileTimeToFileTime(&i,&o);if(ok)wrb(arg(1),&o,8);return done(ok?1U:0U,2);}
   if(n=="FileTimeToSystemTime"){FILETIME i{};SYSTEMTIME o{};rd(arg(0),&i,8);BOOL ok=::FileTimeToSystemTime(&i,&o);if(ok)wrb(arg(1),&o,16);return done(ok?1U:0U,2);}
   if(n=="SystemTimeToFileTime"){SYSTEMTIME i{};FILETIME o{};rd(arg(0),&i,16);BOOL ok=::SystemTimeToFileTime(&i,&o);if(ok)wrb(arg(1),&o,8);return done(ok?1U:0U,2);}
   if(n=="FileTimeToDosDateTime"){FILETIME i{};rd(arg(0),&i,8);WORD d{},t{};BOOL ok=::FileTimeToDosDateTime(&i,&d,&t);if(ok){wrb(arg(1),&d,2);wrb(arg(2),&t,2);}return done(ok?1U:0U,3);}
   if(n=="DosDateTimeToFileTime"){FILETIME o{};BOOL ok=::DosDateTimeToFileTime(WORD(arg(0)),WORD(arg(1)),&o);if(ok)wrb(arg(2),&o,8);return done(ok?1U:0U,3);}
   if(n=="CompareFileTime"){FILETIME a1{},a2{};rd(arg(0),&a1,8);rd(arg(1),&a2,8);return done(unsigned(::CompareFileTime(&a1,&a2)),2);}
   if(n=="GetTimeZoneInformation"){TIME_ZONE_INFORMATION z{};static_assert(sizeof(z)==172);const DWORD r=::GetTimeZoneInformation(&z);wrb(arg(0),&z,172);return done(r,1);}
   auto vfile=[&]{const std::uint64_t ft=125911584000000000ULL+host.vclock_query()*10;return FILETIME{DWORD(ft),DWORD(ft>>32)};};  // 2000-01-01 UTC + virtual time
   if(n=="GetSystemTime"||n=="GetLocalTime"){SYSTEMTIME t{};if(host.vclock()){const FILETIME f=vfile();::FileTimeToSystemTime(&f,&t);}else if(n=="GetSystemTime")::GetSystemTime(&t);else ::GetLocalTime(&t);wrb(arg(0),&t,16);return done(0,1);}
   if(n=="GetSystemTimeAsFileTime"){FILETIME t{};if(host.vclock())t=vfile();else ::GetSystemTimeAsFileTime(&t);wrb(arg(0),&t,8);return done(0,1);}
   if(n=="GetFileTime"){if(!owned_file(arg(0)))deny("GetFileTime on a handle the guest does not own",arg(0));FILETIME c{},a2{},w{};BOOL ok=::GetFileTime(hhandle(arg(0)),&c,&a2,&w);if(ok){if(arg(1))wrb(arg(1),&c,8);if(arg(2))wrb(arg(2),&a2,8);if(arg(3))wrb(arg(3),&w,8);}return done(ok?1U:0U,4);}
  }
  if(n=="WideCharToMultiByte"){const unsigned cp=arg(0),fl=arg(1),ws=arg(2),wl=arg(3),mb=arg(4),ml=arg(5),dc=arg(6),ud=arg(7);std::vector<wchar_t>w;
   if(int(wl)==-1){for(unsigned i=0;;++i){if(!readable(ws+2*i,2))deny("WideCharToMultiByte input outside the memory contract",ws);const wchar_t c=wchar_t(runtime.memory().load<unsigned short>({ws+2*i}));w.push_back(c);if(!c)break;if(i>0x100000)deny("Unterminated wide input",ws);}}
   else{if(!readable(ws,2*wl))deny("WideCharToMultiByte input outside the memory contract",ws);for(unsigned i=0;i<wl;++i)w.push_back(wchar_t(runtime.memory().load<unsigned short>({ws+2*i})));}
   std::string defc;if(dc){defc=std::string(1,char(runtime.memory().load<unsigned char>({dc})));}BOOL used{};std::vector<char>out(std::max(ml,1U));int k{};
   {LastError l(host);k=::WideCharToMultiByte(cp,fl,w.data(),int(w.size()),ml?out.data():nullptr,int(ml),dc?defc.c_str():nullptr,ud?&used:nullptr);}
   if(k>0&&ml){if(!writable(mb,unsigned(k)))deny("WideCharToMultiByte output outside the memory contract",mb);for(int i=0;i<k;++i)runtime.memory().store<unsigned char>({mb+unsigned(i)},static_cast<unsigned char>(out[size_t(i)]));}
   if(ud){if(!writable(ud,4))deny("WideCharToMultiByte used-default outside the memory contract",ud);store(ud,unsigned(used));}return done(unsigned(k),8);}
  if(n=="MultiByteToWideChar"){const unsigned cp=arg(0),fl=arg(1),ms=arg(2),mlen=arg(3),ws=arg(4),wl=arg(5);std::string m;
   if(int(mlen)==-1){m=guest_string(ms,0x100000);m.push_back('\0');}else{if(!readable(ms,mlen))deny("MultiByteToWideChar input outside the memory contract",ms);m.resize(mlen);for(unsigned i=0;i<mlen;++i)m[i]=char(runtime.memory().load<unsigned char>({ms+i}));}
   std::vector<wchar_t>out(std::max(wl,1U));int k{};{LastError l(host);k=::MultiByteToWideChar(cp,fl,m.data(),int(m.size()),wl?out.data():nullptr,int(wl));}
   if(k>0&&wl){if(!writable(ws,2*unsigned(k)))deny("MultiByteToWideChar output outside the memory contract",ws);for(int i=0;i<k;++i)runtime.memory().store<unsigned short>({ws+2*unsigned(i)},static_cast<unsigned short>(out[size_t(i)]));}return done(unsigned(k),6);}
  // LoadMenuA: the RT_MENU template from the mapped guest image, built by the real LoadMenuIndirectA.
  if(n=="LoadMenuA"){const unsigned h=arg(0)?arg(0):0x400000,id=arg(1);if(!host.paths.count(h))deny("LoadMenuA on a module without a mapped image",h);std::string key;
   if(id>=0x10000){key=guest_string(id);std::transform(key.begin(),key.end(),key.begin(),[](unsigned char c){return char(std::toupper(c));});}
   const std::pair<unsigned,std::string>nm=id>=0x10000?(key.size()>1&&key[0]=='#'?std::pair<unsigned,std::string>{unsigned(std::stoul(key.substr(1))),{}}:std::pair<unsigned,std::string>{0xffffffffU,key}):std::pair<unsigned,std::string>{id,{}};
   const unsigned d=resource(h,{4U,{}},nm);if(!d){host.last_error=ERROR_RESOURCE_NAME_NOT_FOUND;return done(0,2);}const unsigned a=h+load(d),z=load(d+4);std::vector<unsigned char>t(z);for(unsigned i=0;i<z;++i)t[i]=runtime.memory().load<unsigned char>({a+i});
   HMENU m{};{LastError l(host);m=::LoadMenuIndirectA(t.data());}return done(m?ghandle(m):0,2);}
  if(n=="DestroyMenu"){BOOL ok{};{LastError l(host);ok=::DestroyMenu(static_cast<HMENU>(hhandle(arg(0))));}return done(ok?1U:0U,1);}
  if(n=="SetMenu"){BOOL ok{};{LastError l(host);ok=::SetMenu(hwnd_of(arg(0)),static_cast<HMENU>(hhandle(arg(1))));}return done(ok?1U:0U,2);}
  if(n=="CreateDIBSection"){const unsigned bi=arg(1),usage=arg(2),pbits=arg(3);if(arg(4)||arg(5))deny("CreateDIBSection over a file mapping is not modelled",arg(4));if(!readable(bi,40)||load(bi)!=40)deny("CreateDIBSection header outside the contract",bi);
   const unsigned comp=load(bi+16),bpp=load(bi+12)>>16,used=load(bi+32);const unsigned extra=comp==BI_BITFIELDS?12:(bpp<=8?4*(used?used:(1U<<bpp)):0);if(!readable(bi,40+extra)||!writable(pbits,4))deny("CreateDIBSection arguments outside the memory contract",bi);
   std::vector<unsigned char>info(40+extra);get_bytes(bi,info.data(),unsigned(info.size()));void*bits{};HBITMAP h{};{LastError l(host);h=::CreateDIBSection(static_cast<HDC>(hhandle(arg(0))),reinterpret_cast<BITMAPINFO*>(info.data()),usage,&bits,nullptr,0);}
   if(!h){store(pbits,0);return done(0,6);}const int w=int(load(bi+4)),ht=int(load(bi+8));const unsigned stride=((unsigned(w)*bpp+31)/32)*4,bytes=stride*unsigned(std::abs(ht));const unsigned g2=pages(bits,bytes);host.dibs.push_back({h,bits,g2,bytes});store(pbits,g2);
   apis.back()+="("+std::to_string(w)+"x"+std::to_string(ht)+"x"+std::to_string(bpp)+")";return done(ghandle(h),6);}
  if(n=="GetObjectA"){const unsigned h=arg(0),z=arg(1),out=arg(2);const HGDIOBJ ho=hhandle(h);for(const auto&d:host.dibs)if(ghandle(d.bitmap)==h){BITMAP b{};if(!::GetObjectA(ho,sizeof(b),&b))return done(0,3);if(!out)return done(24,3);if(z<24||!writable(out,24))deny("GetObjectA BITMAP output outside the memory contract",out);
     const std::array<unsigned,6>v{unsigned(b.bmType),unsigned(b.bmWidth),unsigned(b.bmHeight),unsigned(b.bmWidthBytes),unsigned(b.bmPlanes)|(unsigned(b.bmBitsPixel)<<16),d.guest};for(unsigned i=0;i<6;++i)store(out+4*i,v[i]);return done(24,3);}
   const DWORD type=::GetObjectType(ho);if(type==OBJ_FONT){LOGFONTA lf{};const int k=::GetObjectA(ho,sizeof(lf),&lf);if(!out)return done(unsigned(k),3);if(!writable(out,std::min<unsigned>(z,60)))deny("GetObjectA LOGFONT output outside the memory contract",out);for(unsigned i=0;i<std::min<unsigned>(z,60);++i)runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&lf)[i]);return done(std::min<unsigned>(z,60),3);}
   if(type==OBJ_PEN){LOGPEN lp{};const int k=::GetObjectA(ho,sizeof(lp),&lp);if(!out)return done(unsigned(k),3);if(z<16||!writable(out,16))deny("GetObjectA LOGPEN output outside the memory contract",out);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&lp)[i]);return done(16,3);}
   if(type==OBJ_BITMAP){BITMAP b{};if(!::GetObjectA(ho,sizeof(b),&b))return done(0,3);if(b.bmBits)deny("GetObjectA of a bitmap with host bits outside the DIB model",h);if(!out)return done(24,3);if(z<24||!writable(out,24))deny("GetObjectA BITMAP output outside the memory contract",out);
    const std::array<unsigned,6>v{unsigned(b.bmType),unsigned(b.bmWidth),unsigned(b.bmHeight),unsigned(b.bmWidthBytes),unsigned(b.bmPlanes)|(unsigned(b.bmBitsPixel)<<16),0};for(unsigned i=0;i<6;++i)store(out+4*i,v[i]);return done(24,3);}
   deny("GetObjectA object type not modelled: "+std::to_string(type),type);}
  // Preserve the original MCI commands. A configured local PCM player replaces only cdaudio;
  // movie devices retain WinMM. Marshal active x86 fields to x64, including the actual callback HWND.
  if(n=="mciSendCommandA"){const unsigned dev=arg(0),msg=arg(1),fl=arg(2),pa=arg(3);MCIERROR r{};apis.back()+="("+std::to_string(msg)+")";
   auto cbw=[&]()->DWORD_PTR{return (fl&MCI_NOTIFY)?reinterpret_cast<DWORD_PTR>(hwnd_of(load(pa))):0;};
   auto send=[&](DWORD_PTR params)->MCIERROR{auto&cd=host.music();bool local=cd.owns(dev);
    if(msg==MCI_OPEN&&cd.enabled()&&(fl&MCI_OPEN_TYPE)){const auto&o=*reinterpret_cast<const MCI_OPEN_PARMSA*>(params);
     local=(fl&MCI_OPEN_TYPE_ID)?reinterpret_cast<std::uintptr_t>(o.lpstrDeviceType)==MCI_DEVTYPE_CD_AUDIO:o.lpstrDeviceType&&Host::same_name(o.lpstrDeviceType,"cdaudio");}
    return local?cd.send(dev,msg,fl,params): ::mciSendCommandA(dev,msg,fl,params);};
   if(msg==MCI_OPEN){if(!writable(pa,20))deny("MCI_OPEN parameters outside the memory contract",pa);MCI_OPEN_PARMSA o{};o.dwCallback=cbw();std::string type,elem,alias;
    if(fl&MCI_OPEN_TYPE){if(fl&MCI_OPEN_TYPE_ID)o.lpstrDeviceType=reinterpret_cast<LPCSTR>(std::uintptr_t(load(pa+8)));else{type=guest_string(load(pa+8));o.lpstrDeviceType=type.c_str();}}
    if(fl&MCI_OPEN_ELEMENT){if(fl&MCI_OPEN_ELEMENT_ID)deny("MCI_OPEN element id is not modelled",fl);elem=guest_string(load(pa+12));o.lpstrElementName=elem.c_str();}
    if(fl&MCI_OPEN_ALIAS){alias=guest_string(load(pa+16));o.lpstrAlias=alias.c_str();}
    {LastError l(host);r=send(reinterpret_cast<DWORD_PTR>(&o));}if(!r)store(pa+4,o.wDeviceID);apis.back()+="("+type+")="+std::to_string(r);return done(r,4);}
   if(msg==MCI_SET){if(!readable(pa,12))deny("MCI_SET parameters outside the memory contract",pa);MCI_SET_PARMS p{cbw(),(fl&MCI_SET_TIME_FORMAT)?load(pa+4):0U,(fl&(MCI_SET_AUDIO|MCI_SET_ON|MCI_SET_OFF))?load(pa+8):0U};{LastError l(host);r=send(reinterpret_cast<DWORD_PTR>(&p));}return done(r,4);}
   if(msg==MCI_STATUS){if(!writable(pa,16))deny("MCI_STATUS parameters outside the memory contract",pa);MCI_STATUS_PARMS p{cbw(),0,(fl&MCI_STATUS_ITEM)?load(pa+8):0U,(fl&MCI_TRACK)?load(pa+12):0U};{LastError l(host);r=send(reinterpret_cast<DWORD_PTR>(&p));}
    if(!r){if(p.dwReturn>0xffffffffull)deny("MCI_STATUS result not representable",unsigned(p.dwReturn>>32));store(pa+4,unsigned(p.dwReturn));}return done(r,4);}
   if(msg==MCI_PLAY){if(pa&&!readable(pa,12))deny("MCI_PLAY parameters outside the memory contract",pa);MCI_PLAY_PARMS p{};if(pa){p.dwCallback=cbw();if(fl&MCI_FROM)p.dwFrom=load(pa+4);if(fl&MCI_TO)p.dwTo=load(pa+8);}{LastError l(host);r=send(pa?reinterpret_cast<DWORD_PTR>(&p):0);}return done(r,4);}
   if(msg==MCI_SEEK){if(pa&&!readable(pa,8))deny("MCI_SEEK parameters outside the memory contract",pa);MCI_SEEK_PARMS p{};if(pa){p.dwCallback=cbw();if(fl&MCI_TO)p.dwTo=load(pa+4);}{LastError l(host);r=send(pa?reinterpret_cast<DWORD_PTR>(&p):0);}return done(r,4);}
   if(msg==MCI_STOP||msg==MCI_CLOSE||msg==MCI_PAUSE||msg==MCI_RESUME){if(pa&&!readable(pa,4))deny("MCI generic parameters outside the memory contract",pa);MCI_GENERIC_PARMS p{};if(pa)p.dwCallback=cbw();{LastError l(host);r=send(pa?reinterpret_cast<DWORD_PTR>(&p):0);}return done(r,4);}
   deny("MCI command not modelled: "+std::to_string(msg),msg);}
  if(n=="mciGetErrorStringA"){const unsigned a=arg(1),z=arg(2);if(!z||!writable(a,z))deny("mciGetErrorStringA buffer outside the memory contract",a);std::vector<char>b(z);BOOL ok=::mciGetErrorStringA(arg(0),b.data(),z);for(unsigned i=0;i<z;++i){runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(b[i]));if(!b[i])break;}return done(ok?1U:0U,3);}
  // Put the private CD AUX first: the original stops at the first CD-volume device.
  // Other AUX IDs shift by one; no physical mixer volume writes are enabled.
  if(n=="auxGetNumDevs"){auto&cd=host.music();return done(::auxGetNumDevs()+(cd.enabled()?1U:0U),0);}
  if(n=="auxGetDevCapsA"){const unsigned a=arg(1),z=arg(2);static_assert(sizeof(AUXCAPSA)==48);if(z<48||!writable(a,48))deny("auxGetDevCapsA output outside the memory contract",a);AUXCAPSA c{};auto&cd=host.music();const MMRESULT r=cd.enabled()&&arg(0)==cd.aux_id()?cd.aux_caps(c): ::auxGetDevCapsA(UINT_PTR(cd.enabled()&&arg(0)!=0xffffffffU?arg(0)-1U:arg(0)),&c,sizeof(c));
   if(!r)for(unsigned i=0;i<48;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&c)[i]);return done(r,3);}
  if(n=="auxGetVolume"){DWORD v{};auto&cd=host.music();const MMRESULT r=cd.enabled()&&arg(0)==cd.aux_id()?cd.aux_get_volume(v): ::auxGetVolume(cd.enabled()&&arg(0)!=0xffffffffU?arg(0)-1U:arg(0),&v);if(!writable(arg(1),4))deny("auxGetVolume output outside the memory contract",arg(1));store(arg(1),v);return done(r,2);}
  if(n=="auxSetVolume"){auto&cd=host.music();if(cd.enabled()&&arg(0)==cd.aux_id())return done(cd.aux_set_volume(arg(1)),2);
   if(!audio::valid_host_aux_device(arg(0),cd.enabled(),::auxGetNumDevs()))return done(MMSYSERR_BADDEVICEID,2);
   deny("auxSetVolume would change the host CD-audio mixer level; not authorized",arg(1));}
  // WINMM mixer (CD volume): real queries with field-wise x86<->x64 marshalling; setting levels would change
  // the host system volume and stops typed.
  if(n=="mixerGetNumDevs")return done(::mixerGetNumDevs(),0);
  if(n=="mixerOpen"){const unsigned ph=arg(0),fl=arg(4);if(!writable(ph,4))deny("mixerOpen output outside the memory contract",ph);if((fl&CALLBACK_TYPEMASK)!=CALLBACK_NULL&&(fl&CALLBACK_TYPEMASK)!=CALLBACK_WINDOW)deny("mixerOpen callback kind not modelled",fl);
   HMIXER h{};MMRESULT r{};{LastError l(host);r=::mixerOpen(&h,arg(1),(fl&CALLBACK_TYPEMASK)==CALLBACK_WINDOW?DWORD_PTR(std::intptr_t(std::int32_t(arg(2)))):0,DWORD_PTR(arg(3)),fl);}if(!r)store(ph,handle_token(h));return done(r,5);}
  if(n=="mixerClose"){MMRESULT r{};{LastError l(host);r=::mixerClose(reinterpret_cast<HMIXER>(token_handle(arg(0))));}return done(r,1);}
  if(n=="mixerGetLineInfoA"){const unsigned a=arg(1),fl=arg(2);if(!writable(a,168)||load(a)!=168)deny("MIXERLINEA outside the contract or with a wrong cbStruct",a);MIXERLINEA m{};m.cbStruct=sizeof(m);
   m.dwDestination=load(a+4);m.dwSource=load(a+8);m.dwLineID=load(a+12);m.dwComponentType=load(a+24);m.Target.dwType=load(a+120);m.Target.dwDeviceID=load(a+124);m.Target.wMid=WORD(load(a+128));m.Target.wPid=WORD(load(a+128)>>16);m.Target.vDriverVersion=load(a+132);
   for(unsigned i=0;i<32;++i)m.Target.szPname[i]=char(runtime.memory().load<unsigned char>({a+136+i}));
   MMRESULT r{};{LastError l(host);r=::mixerGetLineInfoA(mixer_obj(arg(0)),&m,fl);}
   if(!r){const std::array<unsigned,10>v{168,m.dwDestination,m.dwSource,m.dwLineID,m.fdwLine,unsigned(m.dwUser),m.dwComponentType,m.cChannels,m.cConnections,m.cControls};for(unsigned i=0;i<10;++i)store(a+4*i,v[i]);
    for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+40+i},static_cast<unsigned char>(m.szShortName[i]));for(unsigned i=0;i<64;++i)runtime.memory().store<unsigned char>({a+56+i},static_cast<unsigned char>(m.szName[i]));
    store(a+120,m.Target.dwType);store(a+124,m.Target.dwDeviceID);store(a+128,unsigned(m.Target.wMid)|(unsigned(m.Target.wPid)<<16));store(a+132,m.Target.vDriverVersion);for(unsigned i=0;i<32;++i)runtime.memory().store<unsigned char>({a+136+i},static_cast<unsigned char>(m.Target.szPname[i]));}
   return done(r,3);}
  if(n=="mixerGetLineControlsA"){const unsigned a=arg(1),fl=arg(2);if(!writable(a,24)||load(a)!=24)deny("MIXERLINECONTROLSA outside the contract or with a wrong cbStruct",a);const unsigned cnt=load(a+12),cb=load(a+16),arr=load(a+20);
   static_assert(sizeof(MIXERCONTROLA)==148);if(cb!=148||cnt>64||!writable(arr,148*cnt))deny("MIXERLINECONTROLSA control array outside the model",arr);std::vector<MIXERCONTROLA>c(std::max(cnt,1U));
   MIXERLINECONTROLSA l2{};l2.cbStruct=sizeof(l2);l2.dwLineID=load(a+4);l2.dwControlID=load(a+8);l2.cControls=cnt;l2.cbmxctrl=sizeof(MIXERCONTROLA);l2.pamxctrl=c.data();
   MMRESULT r{};{LastError l(host);r=::mixerGetLineControlsA(mixer_obj(arg(0)),&l2,fl);}
   if(!r){store(a+4,l2.dwLineID);store(a+8,l2.dwControlID);for(unsigned k=0;k<cnt;++k)for(unsigned i=0;i<148;++i)runtime.memory().store<unsigned char>({arr+148*k+i},reinterpret_cast<const unsigned char*>(&c[k])[i]);}return done(r,3);}
  if(n=="mixerGetControlDetailsA"){const unsigned a=arg(1),fl=arg(2);if(!writable(a,24)||load(a)!=24)deny("MIXERCONTROLDETAILS outside the contract or with a wrong cbStruct",a);const unsigned ch=load(a+8),multi=load(a+12),cb=load(a+16),pd=load(a+20);
   const unsigned items=std::max(ch,1U)*std::max(multi,1U);if(cb>64||items>256||!writable(pd,cb*items))deny("Mixer control details outside the model",pd);std::vector<unsigned char>buf(size_t(cb)*items);
   MIXERCONTROLDETAILS d{};d.cbStruct=sizeof(d);d.dwControlID=load(a+4);d.cChannels=ch;d.cMultipleItems=multi;d.cbDetails=cb;d.paDetails=buf.data();
   MMRESULT r{};{LastError l(host);r=::mixerGetControlDetailsA(mixer_obj(arg(0)),&d,fl);}if(!r)for(unsigned i=0;i<buf.size();++i)runtime.memory().store<unsigned char>({pd+i},buf[i]);return done(r,3);}
  // Since Vista the legacy mixer API is virtualized to this application's own audio-session volume, so the
  // real call changes no system-wide setting.
  if(n=="mixerSetControlDetails"){const unsigned a=arg(1),fl=arg(2);if(!readable(a,24)||load(a)!=24)deny("MIXERCONTROLDETAILS outside the contract or with a wrong cbStruct",a);const unsigned ch=load(a+8),multi=load(a+12),cb=load(a+16),pd=load(a+20);
   const unsigned items=std::max(ch,1U)*std::max(multi,1U);if(cb>64||items>256||!readable(pd,cb*items))deny("Mixer control details outside the model",pd);std::vector<unsigned char>buf(size_t(cb)*items);get_bytes(pd,buf.data(),unsigned(buf.size()));
   MIXERCONTROLDETAILS d{};d.cbStruct=sizeof(d);d.dwControlID=load(a+4);d.cChannels=ch;d.cMultipleItems=multi;d.cbDetails=cb;d.paDetails=buf.data();MMRESULT r{};{LastError l(host);r=::mixerSetControlDetails(mixer_obj(arg(0)),&d,fl);}return done(r,3);}
  // Synchronization objects: real kernel objects owned by the guest (closed with CloseHandle).
  if(n=="CreateMutexA"||n=="CreateEventA"||n=="CreateSemaphoreA"){if(arg(0))deny(n+" security attributes are not modelled",arg(0));const unsigned nm=n=="CreateSemaphoreA"?arg(3):(n=="CreateMutexA"?arg(2):arg(3));const std::string name=nm?guest_string(nm):std::string();HANDLE h{};
   {LastError l(host);h=n=="CreateMutexA"?::CreateMutexA(nullptr,BOOL(arg(1)),nm?name.c_str():nullptr):n=="CreateEventA"?::CreateEventA(nullptr,BOOL(arg(1)),BOOL(arg(2)),nm?name.c_str():nullptr): ::CreateSemaphoreA(nullptr,LONG(arg(1)),LONG(arg(2)),nm?name.c_str():nullptr);}
   apis.back()+="("+name+")";if(!h)return done(0,n=="CreateMutexA"?3:4);const unsigned g2=ghandle(h);host.files.push_back(g2);if(n=="CreateMutexA"){if(host.last_error==ERROR_ALREADY_EXISTS)deny("CreateMutexA of an existing named mutex is not modelled",g2);host.mutexes[g2]={arg(1)?cur_tid():0U,arg(1)?1U:0U};}return done(g2,n=="CreateMutexA"?3:4);}
  if(n=="WaitForSingleObject"&&host.mutexes.count(arg(0))){auto&[own,cnt]=host.mutexes[arg(0)];const unsigned me=cur_tid();if(own&&own!=me)deny("Wait on a mutex owned by another guest thread would block; cooperative thread switching is not modelled",arg(0));
   DWORD r{};{LastError l(host);r=::WaitForSingleObject(hhandle(arg(0)),0);}if(r!=WAIT_OBJECT_0)deny("Real acquisition of a guest-unowned mutex failed",r);own=me;++cnt;return done(r,2);}
  if(n=="ReleaseMutex"&&host.mutexes.count(arg(0))){auto&[own,cnt]=host.mutexes[arg(0)];if(own!=cur_tid()){host.last_error=ERROR_NOT_OWNER;return done(0,1);}BOOL ok{};{LastError l(host);ok=::ReleaseMutex(hhandle(arg(0)));}if(ok&&--cnt==0)own=0;return done(ok?1U:0U,1);}
  if(n=="ReleaseMutex"||n=="SetEvent"||n=="ResetEvent"||n=="PulseEvent"){if(!owned_file(arg(0)))deny(n+" on a handle the guest does not own",arg(0));BOOL ok{};{LastError l(host);const HANDLE h=hhandle(arg(0));
    ok=n=="ReleaseMutex"?::ReleaseMutex(h):n=="SetEvent"?::SetEvent(h):n=="ResetEvent"?::ResetEvent(h): ::PulseEvent(h);}return done(ok?1U:0U,1);}
  if(n=="ReleaseSemaphore"){if(!owned_file(arg(0)))deny("ReleaseSemaphore on a handle the guest does not own",arg(0));LONG prev{};BOOL ok{};{LastError l(host);ok=::ReleaseSemaphore(hhandle(arg(0)),LONG(arg(1)),&prev);}if(arg(2)){if(!writable(arg(2),4))deny("ReleaseSemaphore output outside the memory contract",arg(2));store(arg(2),unsigned(prev));}return done(ok?1U:0U,3);}
  // Real wait on the guest's own handles plus the thread's message queue (the guest's handles map to host handles).
  if(n=="MsgWaitForMultipleObjects"){const unsigned cnt=arg(0),ph=arg(1);if(cnt>MAXIMUM_WAIT_OBJECTS-1||(cnt&&!readable(ph,4*cnt)))deny("MsgWaitForMultipleObjects handle array outside the model",ph);
   std::vector<HANDLE>hs2(cnt);for(unsigned i=0;i<cnt;++i){const unsigned g2=load(ph+4*i);if(!owned_file(g2))deny("MsgWaitForMultipleObjects on a handle the guest does not own",g2);hs2[i]=hhandle(g2);}
   DWORD r{};{LastError l(host);r=::MsgWaitForMultipleObjects(cnt,cnt?hs2.data():nullptr,BOOL(arg(2)),arg(3),arg(4));}return done(r,5);}
  if(n=="WaitForSingleObject"){if(!owned_file(arg(0)))deny("WaitForSingleObject on a handle the guest does not own",arg(0));DWORD r{};{LastError l(host);r=::WaitForSingleObject(hhandle(arg(0)),arg(1)==INFINITE?0:arg(1));}
   if(r==WAIT_TIMEOUT&&arg(1)==INFINITE)deny("Infinite wait that would block the single guest thread forever",arg(0));if(r==WAIT_TIMEOUT&&arg(1)&&host.thread_tid)deny("A secondary guest thread would block; cooperative thread switching is not modelled",arg(0));return done(r,2);}
  if(n=="DrawTextA"){const int len=int(arg(2));std::string t;if(len<0)t=guest_string(arg(1));else{if(!readable(arg(1),unsigned(len)))deny("DrawTextA text outside the memory contract",arg(1));t.resize(size_t(len));for(int i=0;i<len;++i)t[size_t(i)]=char(runtime.memory().load<unsigned char>({arg(1)+unsigned(i)}));}
   const unsigned ra=arg(3);if(!writable(ra,16))deny("DrawTextA RECT outside the memory contract",ra);RECT r{LONG(load(ra)),LONG(load(ra+4)),LONG(load(ra+8)),LONG(load(ra+12))};if(arg(4)&DT_MODIFYSTRING)deny("DrawTextA DT_MODIFYSTRING is not modelled",arg(4));
   if(text_rec_active)text_record(static_cast<HDC>(hhandle(arg(0))),t,r,arg(4));  /* GPU HUD text recipe (gpu_hud.inc) */
   int h{};{LastError l(host);h=::DrawTextA(static_cast<HDC>(hhandle(arg(0))),t.data(),int(t.size()),&r,arg(4));}store(ra,unsigned(r.left));store(ra+4,unsigned(r.top));store(ra+8,unsigned(r.right));store(ra+12,unsigned(r.bottom));return done(unsigned(h),5);}
  // AVIFile / Video for Windows: the real x64 libraries; stream and codec handles are guest tokens.
  if(n=="AVIFileInit"){::AVIFileInit();return done(0,0);}
  if(n=="AVIFileExit"){::AVIFileExit();return done(0,0);}
  if(n=="AVIStreamOpenFromFileA"){const unsigned out=arg(0);const std::string original=resolve(arg(1));const std::string q=cinematic_path(original);if(q!=original&&(arg(4)&3))deny("Cinematic replacement write access is not authorized",arg(4));GUID h{};const GUID*ph=nullptr;if(arg(5)){h=guest_guid(arg(5));ph=&h;}if(!writable(out,4))deny("AVIStreamOpenFromFileA output outside the memory contract",out);
   PAVISTREAM st{};HRESULT hr{};{LastError l(host);hr=::AVIStreamOpenFromFileA(&st,q.c_str(),arg(2),LONG(arg(3)),arg(4),ph?const_cast<CLSID*>(ph):nullptr);}apis.back()+="("+q+")="+std::to_string(unsigned(hr));store(out,SUCCEEDED(hr)?handle_token(st):0);return done(unsigned(hr),6);}
  auto avs=[&](unsigned v){auto*p2=static_cast<PAVISTREAM>(token_handle(v));if(!p2)deny(n+" on an object that is not a guest AVI stream",v);return p2;};
  if(n=="AVIStreamRelease")return done(unsigned(::AVIStreamRelease(avs(arg(0)))),1);
  if(n=="AVIStreamLength")return done(unsigned(::AVIStreamLength(avs(arg(0)))),1);
  if(n=="AVIStreamFindSample")return done(unsigned(::AVIStreamFindSample(avs(arg(0)),LONG(arg(1)),LONG(arg(2)))),3);
  if(n=="AVIStreamInfoA"){const unsigned a=arg(1),z=arg(2);static_assert(sizeof(AVISTREAMINFOA)==140);if(z<140||!writable(a,140))deny("AVIStreamInfoA output outside the memory contract",a);AVISTREAMINFOA i{};const HRESULT hr=::AVIStreamInfoA(avs(arg(0)),&i,sizeof(i));
   if(SUCCEEDED(hr))for(unsigned k=0;k<140;++k)runtime.memory().store<unsigned char>({a+k},reinterpret_cast<const unsigned char*>(&i)[k]);char fcc[5]{};std::memcpy(fcc,&i.fccHandler,4);apis.back()+="(handler "+std::string(fcc)+")";return done(unsigned(hr),3);}
  if(n=="AVIStreamReadFormat"){const unsigned buf=arg(2),pz=arg(3);if(!writable(pz,4))deny("AVIStreamReadFormat size outside the memory contract",pz);LONG z=LONG(load(pz));std::vector<unsigned char>b(std::max<LONG>(z,1));
   const HRESULT hr=::AVIStreamReadFormat(avs(arg(0)),LONG(arg(1)),buf?b.data():nullptr,&z);if(SUCCEEDED(hr)&&buf){if(!writable(buf,unsigned(z)))deny("AVIStreamReadFormat buffer outside the memory contract",buf);for(LONG k=0;k<z;++k)runtime.memory().store<unsigned char>({buf+unsigned(k)},b[size_t(k)]);}store(pz,unsigned(z));return done(unsigned(hr),4);}
  if(n=="AVIStreamRead"){const unsigned buf=arg(3),cb=arg(4),pb=arg(5),ps=arg(6);if(buf&&!writable(buf,cb))deny("AVIStreamRead buffer outside the memory contract",buf);std::vector<unsigned char>b(std::max(cb,1U));LONG nb{},ns{};
   const HRESULT hr=::AVIStreamRead(avs(arg(0)),LONG(arg(1)),LONG(arg(2)),buf?b.data():nullptr,LONG(cb),&nb,&ns);if(SUCCEEDED(hr)&&buf)for(LONG k=0;k<nb;++k)runtime.memory().store<unsigned char>({buf+unsigned(k)},b[size_t(k)]);
   for(auto[a2,v]:{std::pair<unsigned,LONG>{pb,nb},{ps,ns}})if(a2){if(!writable(a2,4))deny("AVIStreamRead counts outside the memory contract",a2);store(a2,unsigned(v));}return done(unsigned(hr),7);}
  auto bih=[&](unsigned a2,std::vector<unsigned char>&v)->LPBITMAPINFOHEADER{if(!a2)return nullptr;if(!readable(a2,40))deny("BITMAPINFOHEADER outside the memory contract",a2);const unsigned z=load(a2);if(z<40||z>1064||!readable(a2,z))deny("BITMAPINFOHEADER size outside the model",z);
   v.resize(z+1024);get_bytes(a2,v.data(),z);return reinterpret_cast<LPBITMAPINFOHEADER>(v.data());};
  // ---- staged IV50 codec (native) ----
  constexpr unsigned codec_hdrv=0x3f800010U;
  auto codec_drv=[&](unsigned id,unsigned msg,unsigned p1,unsigned p2,unsigned below)->unsigned{return call_guest(host.codec.driverproc,{id,codec_hdrv,msg,p1,p2},true,"Ir50_32 DriverProc",below);};
  auto is_iv50=[](unsigned fcc){return (fcc|0x20202020U)==(unsigned('i')|unsigned('v')<<8|unsigned('5')<<16|unsigned('0')<<24);};
  auto codec_scratch=[&](){return ((state.gpr.rsp.dword-0x2000)&~15U);};
  auto codec_open=[&](unsigned type,unsigned handler,unsigned mode)->unsigned{
   if(!host.codec.loaded){auto li=std::find_if(host.loadable.begin(),host.loadable.end(),[](const auto&l){return _stricmp(l.name.c_str(),"Ir50_32.dll")==0;});if(li==host.loadable.end())return 0;
    // Only a lifted codec is used (its entry and DriverProc must have bodies); otherwise no IV50 decoder exists, as before.
    {const unsigned cb=0x11000000U,ep=cb+pe::u32(li->bytes,pe::u32(li->bytes,0x3c)+24+16),dp=cb+pe::export_rva(li->bytes,"DriverProc");if(!find(ep)||!find(dp)){apis.back()+="(staged codec not lifted)";return 0;}}
    host.codec.base=load_module(*li);host.codec.driverproc=host.codec.base+pe::export_rva(li->bytes,"DriverProc");if(!find(host.codec.driverproc))deny("Codec DriverProc has no lifted body",host.codec.driverproc);host.codec.loaded=true;}
   const unsigned sc=codec_scratch();
   if(!host.codec.enabled){if(!codec_drv(0,DRV_LOAD,0,0,sc))return 0;(void)codec_drv(0,DRV_ENABLE,0,0,sc);host.codec.enabled=true;}
   const unsigned io=sc+64;const std::array<unsigned,9>icopen{36,type,handler,0x104,mode,0,0,0,0};for(unsigned i=0;i<9;++i)store(io+4*i,icopen[i]);
   const unsigned id=codec_drv(0,DRV_OPEN,0,io,sc);if(!id)return 0;const unsigned tok=0x3f000000U+16U*(++host.codec.serial);host.codec.open[tok]=id;return tok;};
  auto codec_close=[&](unsigned tok){const unsigned id=host.codec.open.at(tok);const unsigned r=codec_drv(id,DRV_CLOSE,0,0,codec_scratch());host.codec.open.erase(tok);
   if(host.codec.open.empty()&&host.codec.enabled){(void)codec_drv(0,DRV_DISABLE,0,0,codec_scratch());(void)codec_drv(0,DRV_FREE,0,0,codec_scratch());host.codec.enabled=false;}return r;};
  static const bool staged_codec=[]{const char*v=std::getenv("MW34_STAGED_CODEC");return !(v&&*v=='0');}();  // MW34_STAGED_CODEC=0 disables it
  if(n=="ICLocate"&&is_iv50(arg(1))&&staged_codec){if(arg(0)!=ICTYPE_VIDEO||WORD(arg(4))!=ICMODE_DECOMPRESS)deny("ICLocate of the IV50 codec outside the decompression model",arg(4));
   const unsigned tok=codec_open(arg(0),arg(1),ICMODE_DECOMPRESS);unsigned found=0;
   if(tok){const unsigned q=codec_drv(host.codec.open[tok],ICM_DECOMPRESS_QUERY,arg(2),arg(3),codec_scratch());if(q==ICERR_OK)found=tok;else(void)codec_close(tok);}
   apis.back()+=std::string("(vidc/IV50, staged codec)=")+(found?"found":"none");return done(found,5);}
  if(host.codec.open.count(arg(0))&&(n=="ICSendMessage"||n=="ICClose"||n=="ICDecompress")){const unsigned tok=arg(0),id=host.codec.open[tok];
   if(n=="ICClose")return done(codec_close(tok),1);
   if(n=="ICSendMessage")return done(codec_drv(id,arg(1),arg(2),arg(3),codec_scratch()),4);
   const unsigned sc=codec_scratch(),icd=sc+64;const std::array<unsigned,6>v{arg(1),arg(2),arg(3),arg(4),arg(5),0};for(unsigned i=0;i<6;++i)store(icd+4*i,v[i]);
   return done(codec_drv(id,ICM_DECOMPRESS,icd,24,sc),0);}  // ICDecompress is VFWAPIV (cdecl)
  // Installable-driver default handling, as winmm's DefDriverProc.
  if(n=="DefDriverProc"){const unsigned msg=arg(2);unsigned r=0;if(msg==DRV_LOAD||msg==DRV_FREE||msg==DRV_ENABLE||msg==DRV_DISABLE)r=1;else if(msg==DRV_INSTALL||msg==DRV_REMOVE)r=DRV_OK;return done(r,5);}
  // Environment block: a guest copy of the process environment in the guest heap, released by the Free call.
  if(n=="GetEnvironmentStringsW"||n=="GetEnvironmentStrings"||n=="GetEnvironmentStringsA"){std::vector<unsigned char>b;
   if(n=="GetEnvironmentStringsW"){LPWCH e=::GetEnvironmentStringsW();if(!e)return done(0,0);const wchar_t*p=e;while(*p)p+=std::wcslen(p)+1;b.resize(size_t(p-e+1)*2);std::memcpy(b.data(),e,b.size());::FreeEnvironmentStringsW(e);}
   else{LPCH e=::GetEnvironmentStringsA();if(!e)return done(0,0);const char*p=e;while(*p)p+=std::strlen(p)+1;b.assign(reinterpret_cast<const unsigned char*>(e),reinterpret_cast<const unsigned char*>(p+1));::FreeEnvironmentStringsA(e);}
   const unsigned g2=gheap_alloc(unsigned(b.size()),false);if(!g2){host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(0,0);}write_bytes(g2,b.data(),unsigned(b.size()));host.env_blocks.insert(g2);return done(g2,0);}
  if(n=="FreeEnvironmentStringsW"||n=="FreeEnvironmentStringsA"){if(!host.env_blocks.erase(arg(0))){host.last_error=ERROR_INVALID_PARAMETER;return done(0,1);}gheap_free(arg(0));return done(1,1);}
  // ---- guest virtual memory ----
  if(n=="VirtualAlloc"){const unsigned want=arg(0),size=arg(1),type=arg(2),prot=arg(3);auto&vm=host.vm;
   if(type&~(MEM_RESERVE|MEM_COMMIT|MEM_TOP_DOWN)||!(type&(MEM_RESERVE|MEM_COMMIT)))deny("VirtualAlloc allocation type outside the model",type);if(prot!=PAGE_READWRITE)deny("VirtualAlloc protection outside the model",prot);if(!size){host.last_error=ERROR_INVALID_PARAMETER;return done(0,4);}
   unsigned base=0;
   if(type&MEM_RESERVE){const unsigned rs=(size+0xffffU)&~0xffffU;unsigned at=want?(want&~0xffffU):vm.lo;
    auto free_at=[&](unsigned b){if(b<vm.lo||std::uint64_t(b)+rs>vm.hi)return false;for(const auto&[r0,rn]:vm.reserved)if(b<r0+rn&&r0<b+rs)return false;return true;};
    if(want){if(!free_at(at)){host.last_error=ERROR_INVALID_ADDRESS;return done(0,4);}}else{while(at<vm.hi&&!free_at(at))at+=0x10000U;if(at>=vm.hi){host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(0,4);}}
    vm.reserved[at]=rs;base=at;}
   const unsigned start=(type&MEM_RESERVE)?base:(want&~4095U),end=(type&MEM_RESERVE)?base+((size+4095U)&~4095U):((want+size+4095U)&~4095U);
   if(!(type&MEM_RESERVE)){auto it=vm.reserved.upper_bound(want);if(it==vm.reserved.begin()){host.last_error=ERROR_INVALID_ADDRESS;return done(0,4);}--it;if(end>it->first+it->second){host.last_error=ERROR_INVALID_ADDRESS;return done(0,4);}base=start;}
   if(type&MEM_COMMIT)for(unsigned p=start;p<end;p+=4096U)if(!vm.committed.count(p)){bool bad{};try{runtime.memory().map({p},4096,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked guest page commit",p);vm.committed.insert(p);}
   return done((type&MEM_RESERVE)?base:(want?want:base),4);}
  if(n=="VirtualFree"){const unsigned a=arg(0),size=arg(1),type=arg(2);auto&vm=host.vm;
   auto drop=[&](unsigned s0,unsigned e0){for(unsigned p=s0;p<e0;p+=4096U)if(vm.committed.erase(p)){bool bad{};try{runtime.memory().unmap({p});}catch(...){bad=true;}if(bad)deny("Checked guest page decommit",p);}};
   if(type==MEM_RELEASE){auto it=vm.reserved.find(a);if(it==vm.reserved.end()||size){host.last_error=ERROR_INVALID_PARAMETER;return done(0,3);}drop(it->first,it->first+it->second);vm.reserved.erase(it);return done(1,3);}
   if(type==MEM_DECOMMIT){auto it=vm.reserved.upper_bound(a);if(it==vm.reserved.begin()){host.last_error=ERROR_INVALID_ADDRESS;return done(0,3);}--it;const unsigned s0=a&~4095U,e0=size?((a+size+4095U)&~4095U):it->first+it->second;
    if(e0>it->first+it->second){host.last_error=ERROR_INVALID_PARAMETER;return done(0,3);}drop(s0,e0);return done(1,3);}
   deny("VirtualFree type outside the model",type);}
  // ---- guest heaps (HeapCreate) ----
  if(n=="HeapCreate"){if(arg(0)&~(HEAP_NO_SERIALIZE|HEAP_GENERATE_EXCEPTIONS))deny("HeapCreate flags outside the model",arg(0));const unsigned tok=0x3f400000U+16U*(++host.guest_heap_serial);host.guest_heaps[tok];return done(tok,3);}
  if(host.guest_heaps.count(arg(0))&&(n=="HeapAlloc"||n=="HeapFree"||n=="HeapSize"||n=="HeapReAlloc"||n=="HeapDestroy")){auto&blocks=host.guest_heaps[arg(0)];
   if(n=="HeapDestroy"){for(unsigned b2:blocks)gheap_free(b2);host.guest_heaps.erase(arg(0));return done(1,1);}
   const unsigned flags=arg(1);if(flags&~(HEAP_ZERO_MEMORY|HEAP_NO_SERIALIZE|HEAP_GENERATE_EXCEPTIONS|HEAP_REALLOC_IN_PLACE_ONLY))deny(n+" flags outside the model",flags);
   if(n=="HeapAlloc"){const unsigned g2=gheap_alloc(arg(2),flags&HEAP_ZERO_MEMORY,arg(0));if(!g2){host.last_error=ERROR_NOT_ENOUGH_MEMORY;return done(0,3);}blocks.insert(g2);return done(g2,3);}
   const unsigned ptr=arg(2);if(!blocks.count(ptr))deny(n+" of a pointer that is not a block of this guest heap",ptr);
   if(n=="HeapSize")return done(host.gheap.live.at(ptr),3);
   if(n=="HeapFree"){blocks.erase(ptr);gheap_free(ptr);return done(1,3);}
   if(flags&HEAP_REALLOC_IN_PLACE_ONLY){if(arg(3)<=host.gheap.live.at(ptr)){host.gheap.live[ptr]=arg(3);return done(ptr,4);}return done(0,4);}
   const unsigned old=host.gheap.live.at(ptr),g2=gheap_alloc(arg(3),flags&HEAP_ZERO_MEMORY,arg(0));if(!g2)return done(0,4);std::vector<std::byte>vb(std::min(old,arg(3)));if(!vb.empty()){runtime.memory().read({ptr},vb);runtime.memory().write({g2},vb);}
   blocks.erase(ptr);gheap_free(ptr);blocks.insert(g2);return done(g2,4);}
  if(n=="ICLocate"){std::vector<unsigned char>i1,o1;HIC h{};{LastError l(host);h=::ICLocate(arg(0),arg(1),bih(arg(2),i1),bih(arg(3),o1),WORD(arg(4)));}char t[5]{},f[5]{};const unsigned ty=arg(0),fh=arg(1);std::memcpy(t,&ty,4);std::memcpy(f,&fh,4);
   apis.back()+="("+std::string(t)+"/"+std::string(f)+")="+(h?"found":"none");return done(h?handle_token(h):0,5);}
  auto hic=[&](unsigned v){auto*h=static_cast<HIC>(token_handle(v));if(!h)deny(n+" on an object that is not a guest codec handle",v);return h;};
  if(n=="ICClose")return done(unsigned(::ICClose(hic(arg(0)))),1);
  if(n=="ICDecompress"&&!arg(0)){DWORD r{};{LastError l(host);r=::ICDecompress(nullptr,arg(1),nullptr,nullptr,nullptr,nullptr);}apis.back()+="(NULL codec)="+std::to_string(std::int32_t(r));return done(r,0);}  /* VFWAPIV: cdecl */
  if(n=="ICDecompress"){std::vector<unsigned char>i1,o1;auto*bi=bih(arg(2),i1);auto*bo=bih(arg(4),o1);const unsigned in=arg(3),outp=arg(5);if(!bi||!bo)deny("ICDecompress without formats",0);
   const unsigned isz=bi->biSizeImage,osz=bo->biSizeImage?bo->biSizeImage:unsigned(std::abs(bo->biHeight))*((unsigned(bo->biWidth)*bo->biBitCount/8+3)&~3U);if(!readable(in,isz)||!writable(outp,osz))deny("ICDecompress buffers outside the memory contract",in);
   std::vector<unsigned char>ib(std::max(isz,1U)),ob(std::max(osz,1U));get_bytes(in,ib.data(),isz);const DWORD r=::ICDecompress(hic(arg(0)),arg(1),bi,ib.data(),bo,ob.data());if(r==ICERR_OK)for(unsigned k=0;k<osz;++k)runtime.memory().store<unsigned char>({outp+k},ob[k]);return done(r,0);}
  // ICSendMessage on a NULL codec (no decoder for the stream on this platform, e.g. Indeo 5 on x64) returns
  // the real platform error; messages to real codec handles need per-message marshalling.
  if(n=="ICSendMessage"){if(arg(0))deny("ICSendMessage to a codec handle is not modelled yet: message "+std::to_string(arg(1)),arg(1));LRESULT r{};{LastError l(host);r=::ICSendMessage(nullptr,arg(1),0,0);}
   apis.back()+="(NULL codec, "+std::to_string(arg(1))+")="+std::to_string(std::int32_t(r));return done(unsigned(std::int32_t(r)),4);}
  if(n=="GetOEMCP")return done(::GetOEMCP(),0);
  if(n=="GetACP")return done(::GetACP(),0);
  if(n=="GetSystemMetrics"){int v{};{LastError l(host);v=::GetSystemMetrics(int(arg(0)));}return done(unsigned(v),1);}
  if(n=="GetSysColor"){DWORD v{};{LastError l(host);v=::GetSysColor(int(arg(0)));}return done(v,1);}
  if(n=="GetSysColorBrush"){HBRUSH v{};{LastError l(host);v=::GetSysColorBrush(int(arg(0)));}return done(ghandle(v),1);}
  if(n=="GetStockObject"){HGDIOBJ v{};{LastError l(host);v=::GetStockObject(int(arg(0)));}return done(ghandle(v),1);}
  if(n=="CreateFontA"){const std::string face=arg(13)?guest_string(arg(13),LF_FACESIZE):std::string();HFONT f{};
   {LastError l(host);f=::CreateFontA(int(arg(0)),int(arg(1)),int(arg(2)),int(arg(3)),int(arg(4)),arg(5),arg(6),arg(7),arg(8),arg(9),arg(10),arg(11),arg(12),arg(13)?face.c_str():nullptr);}
   apis.back()+="("+face+")";return done(f?ghandle(f):0,14);}
  if(n=="DeleteObject"){BOOL ok{};{LastError l(host);ok=::DeleteObject(static_cast<HGDIOBJ>(hhandle(arg(0))));}
   if(ok)for(auto it=host.dibs.begin();it!=host.dibs.end();++it)if(ghandle(it->bitmap)==arg(0)){release(it->guest);host.dibs.erase(it);break;}return done(ok?1U:0U,1);}
  if(n=="GetDC"&&!arg(0)){HDC v{};{LastError l(host);v=::GetDC(nullptr);}return done(ghandle(v),1);}
  if(n=="ReleaseDC"&&!arg(0)){int v{};{LastError l(host);v=::ReleaseDC(nullptr,static_cast<HDC>(hhandle(arg(1))));}return done(unsigned(v),2);}
  if(n=="GetDeviceCaps"){int v{};{LastError l(host);v=::GetDeviceCaps(static_cast<HDC>(hhandle(arg(0))),int(arg(1)));}return done(unsigned(v),2);}
  if(n=="GetCPInfo"){CPINFO c{};BOOL ok{};{LastError l(host);ok=::GetCPInfo(arg(0),&c);}static_assert(sizeof(CPINFO)==20);if(ok){const unsigned a=arg(1);if(!writable(a,20))deny("GetCPInfo output outside the memory contract",a);
    for(unsigned i=0;i<20;++i)runtime.memory().store<unsigned char>({a+i},reinterpret_cast<const unsigned char*>(&c)[i]);}return done(ok?1U:0U,2);}
  // The guest process image is Mech3.exe (mapped at 400000), not the host worker: its subsystem version.
  if(n=="GetProcessVersion"){if(arg(0)&&arg(0)!=::GetCurrentProcessId())deny("GetProcessVersion of another process",arg(0));const unsigned opt=0x400000+load(0x40003c)+24;
   const unsigned v=load(opt+48);return done((v&0xffff)<<16|(v>>16),1);}
  if((n=="LoadCursorA"||n=="LoadIconA")&&arg(0)){const unsigned h=arg(0),id=arg(1);const bool icon=n=="LoadIconA";if(!host.paths.count(h))deny(n+" on a module without a mapped image",h);
   std::string key;if(id>=0x10000){key=guest_string(id);std::transform(key.begin(),key.end(),key.begin(),[](unsigned char c){return char(std::toupper(c));});}
   const std::string ck=std::to_string(h)+(icon?"I":"C")+(id>=0x10000?key:std::to_string(id));if(auto it=host.shared_images.find(ck);it!=host.shared_images.end())return done(it->second,2);
   const std::pair<unsigned,std::string>nm=id>=0x10000?(key.size()>1&&key[0]=='#'?std::pair<unsigned,std::string>{unsigned(std::stoul(key.substr(1))),{}}:std::pair<unsigned,std::string>{0xffffffffU,key}):std::pair<unsigned,std::string>{id,{}};
   const unsigned gd=resource(h,{icon?14U:12U,{}},nm);if(!gd){host.last_error=ERROR_RESOURCE_NAME_NOT_FOUND;return done(0,2);}
   auto bytes=[&](unsigned d){const unsigned a=h+load(d),z=load(d+4);std::vector<BYTE>v(z);for(unsigned i=0;i<z;++i)v[i]=runtime.memory().load<unsigned char>({a+i});return v;};
   auto dir=bytes(gd);int rid{};{LastError l(host);rid=::LookupIconIdFromDirectoryEx(dir.data(),icon,0,0,LR_DEFAULTCOLOR);}if(!rid)return done(0,2);
   const unsigned ri=resource(h,{icon?3U:1U,{}},{unsigned(rid),{}});if(!ri)deny(n+" group entry without its image resource",unsigned(rid));auto img=bytes(ri);HICON hi{};
   {LastError l(host);hi=::CreateIconFromResourceEx(img.data(),DWORD(img.size()),icon,0x00030000,0,0,LR_DEFAULTCOLOR|LR_DEFAULTSIZE);}const unsigned g2=hi?ghandle(hi):0;if(g2)host.shared_images[ck]=g2;return done(g2,2);}
  if(n=="LoadCursorA"||n=="LoadIconA"){const unsigned h=arg(0),id=arg(1);if(h||id>=0x10000)deny(n+" of a module resource is not modelled yet (system resources only)",id);
   void*v{};{LastError l(host);v=n=="LoadCursorA"?static_cast<void*>(::LoadCursorA(nullptr,MAKEINTRESOURCEA(id))):static_cast<void*>(::LoadIconA(nullptr,MAKEINTRESOURCEA(id)));}return done(ghandle(v),2);}
  if(n=="GetCursorPos"){POINT pt{};BOOL ok{};if(host.scripted){pt=host.vcursor;ok=TRUE;}else{LastError l(host);ok=::GetCursorPos(&pt);}const unsigned a=arg(0);if(!writable(a,8))deny("GetCursorPos output outside the memory contract",a);if(ok){store(a,unsigned(pt.x));store(a+4,unsigned(pt.y));}return done(ok?1U:0U,1);}
  if(n=="GetTickCount")return done(host.vclock()?unsigned(host.vclock_query()/1000):host.guest_tick(),0);
  if(n=="GetMessageTime")return done(host.guest_tick_of(DWORD(::GetMessageTime())),0);
  if(n=="GetMessagePos")return done(::GetMessagePos(),0);
  if(n=="GetCurrentThread")return done(ghandle(::GetCurrentThread()),0);
  if(n=="GetCurrentProcess")return done(ghandle(::GetCurrentProcess()),0);
  if(n=="GetCurrentProcessId")return done(::GetCurrentProcessId(),0);
  // Guest structured exception dispatch: x86 SEH through the TEB exception list (FS:[0]).
  // RaiseException builds the guest EXCEPTION_RECORD and CONTEXT (control, integer and segment registers) below ESP
  // and calls each registered handler as a nested guest call, handler(record, registration, context, dispatcher
  // context), cdecl. ExceptionContinueSearch moves to the next registration; ExceptionContinueExecution resumes the
  // caller with the context registers (its own return point only). A handler that takes the exception does not return
  // here: it unwinds through RtlUnwind and transfers to its __except block or catch continuation, and the abandoned
  // host frames are released when the guest returns past them (GuestReturn). At the end of the chain the top-level
  // filter runs and the process terminates with the exception code. RtlUnwind calls each handler with
  // EXCEPTION_UNWINDING up to the target registration, unlinking each, and returns to its caller. Nested and collided
  // dispositions and transfers to other contexts stop typed.
  if(n=="RaiseException"||n=="RtlUnwind"||n=="UnhandledExceptionFilter"){const unsigned teb=runtime.fs_base().value;
   auto put_context=[&](unsigned c,unsigned eip,unsigned esp,unsigned eax){for(unsigned o=0;o<0x2cc;o+=4)store(c+o,0);const auto&f=state.aflag;
    const unsigned fl=unsigned(state.rflag.flat&~0xcd5ULL)|unsigned(f.cf)|unsigned(f.pf)<<2|unsigned(f.af)<<4|unsigned(f.zf)<<6|unsigned(f.sf)<<7|unsigned(f.df)<<10|unsigned(f.of)<<11;
    store(c,0x10007);store(c+0x8c,0x2b);store(c+0x90,0x53);store(c+0x94,0x2b);store(c+0x98,0x2b);store(c+0x9c,g.rdi.dword);store(c+0xa0,g.rsi.dword);store(c+0xa4,g.rbx.dword);
    store(c+0xa8,g.rdx.dword);store(c+0xac,g.rcx.dword);store(c+0xb0,eax);store(c+0xb4,g.rbp.dword);store(c+0xb8,eip);store(c+0xbc,0x23);store(c+0xc0,fl);store(c+0xc4,esp);store(c+0xc8,0x2b);};
   auto registration=[&](unsigned reg){if(reg<e||(reg&3)||!writable(reg,8))deny("SEH registration outside the active guest stack",reg);return load(reg+4);};
   auto top_filter=[&](unsigned ptrs,unsigned below)->unsigned{const unsigned f=heap.unhandled_filter;return f?call_guest(f,{ptrs},true,"top-level exception filter",below):0U;};
   if(n=="UnhandledExceptionFilter"){const unsigned ptrs=arg(0),r=top_filter(ptrs,0);if(r==1U||r==0xffffffffU)return done(r,1);
    // No host OS reporting/debugger policy is implemented. Do not turn
    // CONTINUE_SEARCH into EXECUTE_HANDLER or claim that a dialog was shown.
    if(r!=0U)deny("Invalid top-level exception filter disposition",r);
    deny("UnhandledExceptionFilter OS reporting/debugger policy is not modelled",load(load(ptrs)));}
   const unsigned A=(e-0x380)&~15U,ctx=A,dc=A-16;if(!writable(dc-16,e-(dc-16)))deny("Exception record area outside the stack contract",dc);store(dc,0);
   if(n=="RtlUnwind"){const unsigned target=arg(0),tip=arg(1),rv=arg(3),uflags=2U|(target?0U:4U);unsigned rec=arg(2);
    if(!rec){rec=A+0x2d0;store(rec,0xC0000027U);store(rec+4,uflags);store(rec+8,0);store(rec+12,token);store(rec+16,0);}else store(rec+4,load(rec+4)|uflags);
    put_context(ctx,tip,e+20,rv);++host.unwinds;
    unsigned reg=load(teb);while(reg!=0xffffffffU&&reg!=target){if(target&&target<reg)deny("RtlUnwind target registration is not on the exception chain",target);const unsigned h=registration(reg);
     const unsigned r=call_guest(h,{rec,reg,ctx,dc},false,"SEH unwind handler",dc);if(r!=1U)deny("Collided unwind disposition is not modelled",r);reg=load(reg);store(teb,reg);}
    if(target&&reg!=target)deny("RtlUnwind target registration is not on the exception chain",target);
    if(tip!=ret)deny("RtlUnwind to an instruction other than its return address is not modelled",tip);
    return done(rv,4);}
   const unsigned code=arg(0),flags=arg(1)&1U,np=std::min(arg(2),15U),ap=arg(3),rec=A+0x2d0,resume=e+20;
   store(rec,code);store(rec+4,flags);store(rec+8,0);store(rec+12,token);store(rec+16,np);for(unsigned i=0;i<15;++i)store(rec+20+4*i,i<np&&ap?load(ap+4*i):0U);
   put_context(ctx,ret,resume,g.rax.dword);++host.raises;
   if(const char*q=std::getenv("MW34_SEH_LOG");q&&*q)std::fprintf(stderr,"RaiseException 0x%08x flags %u params %u from 0x%08x\n",code,flags,np,ret);
   auto resume_context=[&]{if(flags&1U)deny("ContinueExecution of a noncontinuable exception",code);if(load(ctx+0xb8)!=ret||load(ctx+0xc4)!=resume)deny("ContinueExecution into a different context is not modelled",load(ctx+0xb8));
    const unsigned fl=load(ctx+0xc0);state.rflag.flat=fl;auto&f=state.aflag;f.cf=fl&1;f.pf=(fl>>2)&1;f.af=(fl>>4)&1;f.zf=(fl>>6)&1;f.sf=(fl>>7)&1;f.df=(fl>>10)&1;f.of=(fl>>11)&1;
    g.rbx.dword=load(ctx+0xa4);g.rsi.dword=load(ctx+0xa0);g.rdi.dword=load(ctx+0x9c);g.rbp.dword=load(ctx+0xb4);g.rcx.dword=load(ctx+0xac);g.rdx.dword=load(ctx+0xa8);return done(load(ctx+0xb0),4);};
   for(unsigned reg=load(teb);reg!=0xffffffffU;reg=load(reg)){const unsigned h=registration(reg),r=call_guest(h,{rec,reg,ctx,dc},false,"SEH handler",dc);
    if(r==0U)return resume_context();if(r!=1U)deny("Nested or collided exception disposition is not modelled",r);}
   const unsigned ptrs=dc-16;store(ptrs,rec);store(ptrs+4,ctx);if(top_filter(ptrs,ptrs)==0xffffffffU)return resume_context();
   deny("Guest unhandled exception: the process terminates with the exception code",code);}
  if(n=="IsProcessorFeaturePresent"){BOOL v{};{LastError l(host);v=::IsProcessorFeaturePresent(arg(0));}return done(unsigned(v),1);}  // MSVCRT FDIV initializer (feature 0)
  if(n=="RegisterWindowMessageA"){const std::string m=guest_string(arg(0));UINT v{};{LastError l(host);v=::RegisterWindowMessageA(m.c_str());}return done(v,1);}
  if(n=="RegisterClipboardFormatA"){const std::string m=guest_string(arg(0));UINT v{};{LastError l(host);v=::RegisterClipboardFormatA(m.c_str());}return done(v,1);}
  if(n=="GetModuleHandleA"){if(!arg(0))return done(0x400000,1);const std::string m=guest_string(arg(0));const unsigned h=module(m);if(!h){host.last_error=ERROR_MOD_NOT_FOUND;}return done(h,1);}
  if(n=="GetProcAddress"){const unsigned h=arg(0),q=arg(1);if(q<0x10000)deny("GetProcAddress by ordinal is not modelled",q);const std::string f=guest_string(q);std::string dll;
   for(const auto&md:host.modules)if(md.base==h){unsigned rva{};bool found=true;try{rva=pe::export_rva(*md.bytes,f);}catch(const std::exception&){found=false;}
    if(!found){host.last_error=ERROR_PROC_NOT_FOUND;return done(0,2);}host.last_error=0;return done(md.base+rva,2);}
   for(const auto&[k,v]:system_modules())if(v==h)dll=k;if(dll.empty())deny("GetProcAddress on a module outside the system-module model",h);
   HMODULE real=::GetModuleHandleA(dll.c_str());if(!real)real=::LoadLibraryA(dll.c_str());FARPROC fp=real?::GetProcAddress(real,f.c_str()):nullptr;if(!fp){host.last_error=ERROR_PROC_NOT_FOUND;return done(0,2);}
   for(const auto&i:host.imports)if(same(i.dll,dll)&&i.name==f)return done(i.bound,2);
   unsigned tokens=0;for(const auto&i:host.imports)if(i.bound>=token_base&&i.bound<token_end)++tokens;const unsigned t=token_base+16*tokens;if(t>=token_end)deny("Import token space",t);host.imports.push_back({0,t,dll,f});return done(t,2);}
  auto put_string=[&](unsigned a,const std::string&t){if(!writable(a,unsigned(t.size())+1))deny(n+" output outside the memory contract",a);for(unsigned i=0;i<t.size();++i)runtime.memory().store<unsigned char>({a+i},static_cast<unsigned char>(t[i]));runtime.memory().store<unsigned char>({a+unsigned(t.size())},0);};
  if(n=="GetSystemDirectoryA"){char sys[MAX_PATH]{};UINT k{};{LastError l(host);k=::GetSystemDirectoryA(sys,MAX_PATH);}if(!k||k>=MAX_PATH)deny("Real GetSystemDirectoryA failed",k);const unsigned a=arg(0),size=arg(1);
   if(k+1>size)return done(k+1,2);put_string(a,sys);return done(k,2);}
  if(n=="lstrcpyA"){const std::string t=guest_string(arg(1));put_string(arg(0),t);return done(arg(0),2);}
  if(n=="lstrcatA"){const std::string t=guest_string(arg(0))+guest_string(arg(1));put_string(arg(0),t);return done(arg(0),2);}
  if(n=="lstrcpynA"){const unsigned k=arg(2);if(!k)return done(arg(0),3);std::string t=guest_string(arg(1));if(t.size()>k-1)t.resize(k-1);put_string(arg(0),t);return done(arg(0),3);}
  // Resources from the literally mapped guest image: HRSRC is the IMAGE_RESOURCE_DATA_ENTRY address
  // and the resource HGLOBAL is the data address, as on Win32.
  if(n=="FindResourceA"){const unsigned h=arg(0)?arg(0):0x400000;if(!host.paths.count(h))deny("FindResourceA on a module without a mapped image",h);
   auto key=[&](unsigned v)->std::pair<unsigned,std::string>{if(v<0x10000)return {v,{}};std::string t=guest_string(v);if(t.size()>1&&t[0]=='#')return {unsigned(std::stoul(t.substr(1))),{}};
    std::transform(t.begin(),t.end(),t.begin(),[](unsigned char c){return char(std::toupper(c));});return {0xffffffffU,t};};
   const unsigned e=resource(h,key(arg(2)),key(arg(1)));if(!e)host.last_error=ERROR_RESOURCE_NAME_NOT_FOUND;return done(e,3);}
  if(n=="LoadResource"||n=="SizeofResource"){const unsigned h=arg(0)?arg(0):0x400000,r=arg(1);const unsigned rva=rsrc_rva(h);if(!rva||r<h+rva)deny(n+" of a handle outside the module's resources",r);
   return done(n=="LoadResource"?h+load(r):load(r+4),2);}
  if(n=="LockResource")return done(arg(0),1);
  // LoadStringA: RT_STRING block id/16+1, entry id%16 of 16 counted UTF-16 strings, converted with the
  // real ANSI code page and truncated to the buffer like Win32.
  if(n=="LoadStringA"){const unsigned h=arg(0)?arg(0):0x400000,id=arg(1),a=arg(2),size=arg(3);if(!host.paths.count(h))deny("LoadStringA on a module without a mapped image",h);if(!size)deny("LoadStringA with a zero-sized buffer",a);
   const unsigned d=resource(h,{6U,{}},{id/16+1,{}});std::wstring w;if(d){unsigned q=h+load(d);for(unsigned i=0;i<id%16;++i)q+=2+2*(load(q)&0xffff);const unsigned len=load(q)&0xffff;for(unsigned c=0;c<len;++c)w.push_back(wchar_t(load(q+2+2*c)&0xffff));}
   if(w.empty()){put_string(a,"");host.last_error=ERROR_RESOURCE_NAME_NOT_FOUND;return done(0,4);}
   std::string t(w.size()*2+1,'\0');int k{};{LastError l(host);k=::WideCharToMultiByte(CP_ACP,0,w.data(),int(w.size()),t.data(),int(t.size()),nullptr,nullptr);}if(k<=0)deny("Real WideCharToMultiByte failed",id);t.resize(unsigned(k));
   if(t.size()>size-1)t.resize(size-1);put_string(a,t);return done(unsigned(t.size()),4);}
  if(n=="lstrlenA"){const unsigned a=arg(0);return done(a?unsigned(guest_string(a).size()):0,1);}
  stop(m4_runtime::FaultReason::unresolved_import,"Unimplemented host service: "+imp->dll+"!"+n,token);}
 // The guest's rounding mode is mirrored into the host x87 CW and MXCSR while the stage runs; the host's
 // own control state is restored afterwards (normal return or fault).
 struct FpControl{unsigned short cw;unsigned mx;FpControl(){__asm__ volatile("fnstcw %0":"=m"(cw));__asm__ volatile("stmxcsr %0":"=m"(mx));}~FpControl(){__asm__ volatile("fldcw %0"::"m"(cw));__asm__ volatile("ldmxcsr %0"::"m"(mx));}};
   // Publishes this Stage's checked values for the inlined bridge fast paths for exactly the duration of run().
  // Flat guest memory (memory/guest_memory.hpp fork, inline_objects.py --flat-mem): recompiled code accesses guest
  // memory as token + address. An access to an unmapped or protected page faults in hardware; this handler turns a
  // fault inside the active Stage's reservation into the Stage's typed deny, by simulating a call from the faulting
  // instruction into flat_fault_throw (the recompiled frames unwind through their unwind tables as for any deny).
  static inline thread_local unsigned flat_fault_address{};static inline thread_local bool flat_fault_write{};
  void texture_fault_evidence(){
   try{
    const auto&h=host.gheap;std::uint64_t live=0,free=0;for(const auto&[p,n]:h.live)live+=n;for(const auto&[p,n]:h.free_blocks)free+=n;
    std::fprintf(stderr,"Texture fault heap: mapped=%08x top=%08x limit=%08x live_bytes=%llu free_bytes=%llu blocks=%zu failures=%u last_failed_bytes=%08x owner=%08x\n",h.mapped,h.top,h.hi,(unsigned long long)live,(unsigned long long)free,h.live.size(),host.heap_failures,host.failed_heap_bytes,host.failed_heap_owner);
    const auto&history=host.texture_seeks;std::fprintf(stderr,"Texture fault seeks: count=%u open_replacements=%zu widened=%u\n",history.count,host.replacement_bank_files.size(),host.large_texture_seeks);
    const unsigned first=history.count>8?history.count-8:0;for(unsigned i=first;i<history.count;++i){const auto&s=history.entries[i%8];std::fprintf(stderr,"  seek handle=%08x offset=%08x high_ptr=%08x origin=%u result=%08x error=%u replacement=%u texture_caller=%u widened=%u\n",s.handle,s.offset,s.high_pointer,s.origin,s.result,s.error,unsigned(s.replacement),unsigned(s.texture_caller),unsigned(s.widened));}
    const auto f=mw34::texture_diagnostics::read_frame(std::span<const unsigned>(returns.data(),depth),std::span<const unsigned>(returns_sp.data(),depth),[&](unsigned a,unsigned n){return readable(a,n);},[&](unsigned a){return load(a);});
    const auto entry=mw34::texture_diagnostics::lookup_entry(std::span<const unsigned>(returns.data(),depth),std::span<const unsigned>(returns_sp.data(),depth),[&](unsigned a,unsigned n){return readable(a,n);},[&](unsigned a){return load(a);});
    if(entry){char name[33]{};bool text=true;for(unsigned i=0;i<32;++i){const auto c=runtime.memory().load<unsigned char>({entry+i});if(!c)break;if(c<32||c>126){text=false;break;}name[i]=char(c);}if(text)std::fprintf(stderr,"Texture fault table: name=%s offset=%08x palette_index=%08x\n",name,load(entry+32),load(entry+36));}
    if(f.found){std::fprintf(stderr,"Texture fault fread: site=%08x destination=%08x size=%u count=%u stream=%08x object=%08x\n",f.site,f.destination,f.size,f.count,f.stream,f.object);
     if(f.object&&readable(f.object,28)){const unsigned dims=load(f.object+4),flags=load(f.object+8),pal=load(f.object+12);std::fprintf(stderr,"Texture fault descriptor: pixels=%u width=%u height=%u flags=%08x palette_fields=%08x palette_count=%d pixel_ptr=%08x alpha_ptr=%08x palette_ptr=%08x\n",load(f.object),dims&65535,dims>>16,flags,pal,int(short(pal>>16)),load(f.object+16),load(f.object+20),load(f.object+24));}
     if(f.stream&&readable(f.stream,28))std::fprintf(stderr,"Texture fault FILE: ptr=%08x remaining=%08x base=%08x flags=%08x fd=%u buffer_size=%u\n",load(f.stream),load(f.stream+4),load(f.stream+8),load(f.stream+12),load(f.stream+16),load(f.stream+24));
    }
   }catch(...){std::fprintf(stderr,"Texture fault metadata unavailable; preserving original fault\n");}
  }
  [[noreturn]] static void flat_fault_throw(){if(const char*q=std::getenv("MW34_SEH_LOG");q&&*q){owner->texture_fault_evidence();const auto&g=owner->state.gpr;std::fprintf(stderr,"SEH flat fault address=%08x esp=%08x ebp=%08x eax=%08x ecx=%08x edx=%08x esi=%08x edi=%08x depth=%u\n",flat_fault_address,g.rsp.dword,g.rbp.dword,g.rax.dword,g.rcx.dword,g.rdx.dword,g.rsi.dword,g.rdi.dword,owner->depth);for(unsigned i=0;i<owner->depth;++i)std::fprintf(stderr,"  return[%u]=%08x slot=%08x\n",i,owner->returns[i],owner->returns_sp[i]);}owner->deny(std::string("Guest ")+(flat_fault_write?"write":"read")+" outside mapped guest memory (hardware fault in recompiled code)",flat_fault_address);}
  // MW34_HUD_WATCH=<file> (diagnostic): while the game holds the render target locked its host pages are read-only; the
 // first write to each page per lock records the writing host instruction (an exe offset) and makes the page writable.
 static inline std::uintptr_t hud_watch_lo{},hud_watch_hi{};static inline std::map<std::uint64_t,unsigned>hud_watch_hits;
 static void hud_watch_save(){static const char*p=std::getenv("MW34_HUD_WATCH");if(!p||!*p)return;if(FILE*f=std::fopen(p,"w")){for(auto&[k,v]:hud_watch_hits)std::fprintf(f,"0x%llx %u\n",(unsigned long long)k,v);std::fclose(f);}}
 // Sync on touch (lazy 3D-target residency): a guest access to the stale resident target or z-buffer saves the CPU
 // context, runs touch_sync() on a host thunk (HUD draws so far are rendered, the GPU image is copied back, pages are
 // unprotected) and resumes the faulting instruction with the saved context.
 static inline CONTEXT touch_ctx{};static inline std::uint64_t touch_count{};
 static void touch_thunk(){if(owner)owner->touch_sync();::RtlRestoreContext(&touch_ctx,nullptr);}
 void touch_sync(){++touch_count;if(hud_gpu_active){if(wide_on()&&hud_fallbacks<8){if(FILE*log=wide_log_file()){std::fprintf(log,"touch frame %u pc %06x rt %08x bt",host.frames,state.gpr.rip.dword,hud_rt_mem);for(unsigned i=depth;i>0&&i+12>depth;--i)std::fprintf(log," %06x",returns[i-1]);std::fprintf(log,"\n");std::fflush(log);}}hud_fallback();}else gpu_sync(0);}
 bool touch_range(std::uintptr_t a)const{if(!host.res_dirty)return false;const auto b=reinterpret_cast<std::uintptr_t>(runtime.memory().flat_base());if(!b)return false;
  for(const unsigned g:{host.res_rt,host.res_zb})if(g)for(const auto&v:host.vsurfaces)if(v.guest==g&&a>=b+v.mem&&a<b+v.mem+v.bytes)return true;return false;}
 static LONG CALLBACK flat_fault_handler(EXCEPTION_POINTERS*e){if(e->ExceptionRecord->ExceptionCode!=EXCEPTION_ACCESS_VIOLATION||e->ExceptionRecord->NumberParameters<2)return EXCEPTION_CONTINUE_SEARCH;if(Stage*ts=owner;ts&&ts->active&&ts->touch_range(std::uintptr_t(e->ExceptionRecord->ExceptionInformation[1]))){touch_ctx=*e->ContextRecord;touch_ctx.ContextFlags=CONTEXT_FULL;auto*c=e->ContextRecord;c->Rsp=((c->Rsp-0x200)&~DWORD64(15))-8;c->Rip=reinterpret_cast<DWORD64>(&touch_thunk);return EXCEPTION_CONTINUE_EXECUTION;}if(hud_watch_hi&&e->ExceptionRecord->ExceptionInformation[0]==1){const auto a=std::uintptr_t(e->ExceptionRecord->ExceptionInformation[1]);if(a>=hud_watch_lo&&a<hud_watch_hi){++hud_watch_hits[e->ContextRecord->Rip-reinterpret_cast<std::uintptr_t>(::GetModuleHandleW(nullptr))];DWORD old{};::VirtualProtect(reinterpret_cast<void*>(a&~std::uintptr_t(4095)),4096,PAGE_READWRITE,&old);return EXCEPTION_CONTINUE_EXECUTION;}}
   Stage*s=owner;if(!s||!s->active)return EXCEPTION_CONTINUE_SEARCH;const auto*at=reinterpret_cast<const std::byte*>(e->ExceptionRecord->ExceptionInformation[1]);const auto&m=s->runtime.memory();
   if(!m.owns_host(at))return EXCEPTION_CONTINUE_SEARCH;flat_fault_address=unsigned(at-m.flat_base());flat_fault_write=e->ExceptionRecord->ExceptionInformation[0]==1;
   auto*c=e->ContextRecord;c->Rsp-=8;*reinterpret_cast<DWORD64*>(c->Rsp)=c->Rip;c->Rip=reinterpret_cast<DWORD64>(&flat_fault_throw);return EXCEPTION_CONTINUE_EXECUTION;}
  struct FastGateScope{explicit FastGateScope(Stage&s){auto&g=mw34_fast_gate;g=Mw34FastGate{};g.thread=::GetCurrentThreadId();g.owner_slot=reinterpret_cast<void*const*>(&owner);
    g.stage=&s;g.token=s.token_ptr;g.active=&s.active;g.complete=&s.complete;g.low=s.low;
    if(s.kind==Kind::initterm){g.read_top=g.write_top=game_stack_top;g.image_lo=0x400000;g.image_hi=game_end;g.data_lo=game_data;g.data_hi=game_data_end;}  // frame(), read_fast, write_fast
    else{g.read_top=s.entry_esp+16;g.write_top=s.entry_esp;g.image_lo=g.data_lo=1;g.image_hi=g.data_hi=0;}
    g.gheap_lo=GuestHeap::lo;g.gheap_mapped=&s.host.gheap.fast_mapped;g.memory=&s.runtime.memory();g.hits=mw34::fastmem::hits.data();g.generation=&mw34::fastmem::generation;
    g.reads=&s.reads;g.writes=&s.writes;g.enabled=1;}
   ~FastGateScope(){mw34_fast_gate.enabled=0;}};
void run(){static const PVOID flat_veh=::AddVectoredExceptionHandler(1,&flat_fault_handler);(void)flat_veh;if(owner||hs::owner)deny("Exactly one native Stage");FpControl fp_control;owner=this;active=true;FastGateScope fast_gate(*this);
  try{if(from_entry){const Body b=find(crt_entry);if(!b)deny("Game CRT entry has no lifted body",crt_entry);++bodies;(void)b(&state,crt_entry,token_ptr);}
   else if(kind==Kind::initterm){(void)hs::mw34_attach_g_thunk_initterm_body(&state,initterm_thunk,token_ptr);
    // The main initializer table returned: the entry continues natively (command line, GetStartupInfoA, WinMain).
    if(initterm_returned){const Body b=find(entry_continuation);if(!b)deny("Entry continuation has no lifted body",entry_continuation);++bodies;(void)b(&state,entry_continuation,token_ptr);}}
    else if(kind==Kind::call){const unsigned pc=state.gpr.rip.dword;const Body b=find(pc);if(!b)deny("In-place provider call has no lifted body",pc);++bodies;(void)b(&state,pc,token_ptr);}else{const Body b=find(mod->entry);if(!b)deny("Provider entry has no lifted body",mod->entry);(void)b(&state,mod->entry,token_ptr);}}catch(...){active=false;owner=nullptr;throw;}
  active=false;owner=nullptr;if(!complete)deny(kind==Kind::initterm?"Main _initterm body ended without its RET":kind==Kind::call?"In-place provider call ended without its RET":"_DllMainCRTStartup body ended without its DllMain RET");if(kind==Kind::attach){mod->attached=true;host.attached=host.all_attached();}}
 // Game import lookup by IAT word. After binding the IAT cells lie outside the guest's writable contract, so
 // their words cannot change while the stage runs: a raw-word table built on first use answers exactly
 // (rebuilt if the import list changes; without that guarantee the scan is used).
 mutable std::unordered_map<unsigned,const Import*>import_by_raw;mutable size_t import_by_raw_n{};mutable bool import_table_ok{};
 const Import*game_import(unsigned raw)const{
  if(import_by_raw_n!=host.game_imports.size()+1){import_by_raw.clear();import_table_ok=true;for(const auto&i:host.game_imports)if(i.cell){if(writable(i.cell,4)){import_table_ok=false;break;}import_by_raw.emplace(game_raw(i),&i);}import_by_raw_n=host.game_imports.size()+1;}
  if(import_table_ok){auto it=import_by_raw.find(raw);return it!=import_by_raw.end()&&game_raw(*it->second)==raw?it->second:nullptr;}
  for(const auto&i:host.game_imports)if(i.cell&&raw==game_raw(i))return &i;return nullptr;}
 unsigned game_raw(const Import&i)const{return const_cast<Stage*>(this)->load(i.cell);}
};
}

