#pragma once
// MSVCRT DLL attach (heap, version globals, _mtinit) and the mode-1 malloc closure for
// the retail entry route. Lifted objects: reports/m4-crt-attach/lifts-r1 (attach entry
// through its _mtinit call site, _mtinit, _mtinitlocks, calloc, _initptd; this tool's
// lift_attach.py) plus the already reviewed reports/m4-crt-heap-{init,mode,version}/
// preparation-r2 and reports/m4-crt-allocation/lifts-r1 bodies.
//
// Kind::attach runs _CRTDLL_INIT(hinst=78000000, DLL_PROCESS_ATTACH, reserved!=0) from
// its real entry 0x780017FD. The run covers GetVersion, _heap_init(1), the
// _osver/_winver/_winmajor/_winminor stores and _mtinit: four static
// InitializeCriticalSection calls, TlsAlloc, calloc of the per-thread data,
// TlsSetValue, _initptd and GetCurrentThreadId; then _ioinit: source malloc of 32
// ioinfo entries, GetStartupInfoA, GetStdHandle/GetFileType for the three standard
// handles and SetHandleCount; then __crtGetEnvironmentStringsA (real GetEnvironmentStringsW,
// WideCharToMultiByte and FreeEnvironmentStringsW, source malloc) and the _aenvptr store.
// It stops at 0x7800188C, the _acmdln writer that the command-line carry executes next.
// Kind::resume continues the same _CRTDLL_INIT after that writer (0x78001897) from the saved
// end-of-attach registers and live frame, with EAX = the writer's _acmdln result: the wide
// command line (two real GetCommandLineW calls returning one guest copy) and the _wcmdln
// store; then __initmbctable -> _setmbcp(-3): lazy _lock(25) (source malloc, static lock-table
// lock, InitializeCriticalSection), GetACP, GetCPInfo and setSBUpLow with __crtGetStringTypeA
// and __crtLCMapStringA (MultiByteToWideChar, GetStringTypeW, LCMapStringW, WideCharToMultiByte,
// _chkstk buffers), then _unlock(25); then _setenvp: _environ from one source malloc per
// variable (strlen/strcpy) and free(_aenvptr) through real HeapFree; then _cinit: its FDIV callback
// CALL is the call the accepted FDIV registry already executed natively at the BEFORE point (its
// result, EAX = the flag it stored, is carried; it is not run twice), then _initterm over MSVCRT's
// own tables (__initstdio, __onexitinit, the clock base, SetUnhandledExceptionFilter), the
// proc_attached increment and the attach epilogue RET 0Ch with TRUE: MSVCRT attach completes. The BEFORE pack holds no attach frame and the FDIV registry
// requires its data page literal until the entry's data read, so the caller schedules
// this at the __getmainargs service on a declared projection frame and restores the
// captured State, CPU and stack page afterwards. These attach effects commute with the
// entry prefix, which uses no heap, lock, TLS or version global. Attach order itself
// remains a stated limitation.
//
// Kind::initterm runs the game's second _initterm CALL (thunk 0x5AC598, table 5E0000..5E0244)
// through the MSVCRT _initterm loop. Root 1 (40FFE0) runs: STL container ctor 4C7B80 with MFC42
// operator new (ordinal 823) -> MSVCRT malloc -> real HeapAlloc, then atexit(410010) -> game
// _onexit -> MSVCRT _onexit (_lockexit on static lock 13, _msize via real HeapSize, the native
// onexit table, _unlockexit). Roots 2..7 repeat that shape with ctor 4D8540 on five more
// objects. The next root is the typed frontier.
//
// Kind::call runs the source malloc closure for the builder's own CALL 780012B3.
// Real Windows APIs run with the guest's exact arguments. Heap blocks are real
// HeapAlloc blocks; the guest sees a checked page-aligned arena address whose mapped
// bytes equal the block's initial bytes. Guest CRITICAL_SECTIONs are 24-byte guest
// objects backed one-to-one by real host critical sections. Any other route, access,
// mode or helper is a typed refusal.
#include <remill/Arch/X86/Runtime/State.h>
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstring>
#include <memory>
#include <thread>
#include <utility>
#include <vector>
namespace mw34::m4_crt_heap_carry {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned attach_entry=0x780017fd,attach_esp=0x20001810,attach_mid=0x7800187d,attach_mid2=0x78001882,attach_end=0x7800188c,hinst=0x78000000;
inline constexpr unsigned env_flag=0x780378c8,aenvptr=0x78037178,env_copy=0x32100000;
inline constexpr unsigned resume_entry=0x78001897,resume_mid=0x780018a1,resume_mid2=0x780018a6,resume_mid3=0x780018ab,resume_end=0x780018ab,fdiv_writer=0x78004254,fdiv_flag=0x78037c2c,proc_attached=0x7803716c,onexit_begin=0x7803788c,onexit_end=0x78037888,piob=0x78037884,time_base=0x78038ee0,prev_filter=0x78037890,guest_filter=0x7800b322,environ_cell=0x78037c04,free_raw=0x345ba,wcmdln=0x78037170,wcmd_flag=0x780378cc,wcmd_copy=0x32200000;
inline constexpr unsigned locktable=0x78037028,mb_lock_cell=0x7803708c,mbcodepage=0x780379c0,mb_system_set=0x78037ae8,mbctype=0x780379e0,mbcasemap=0x78037b00;
inline constexpr unsigned pioinfo=0x78037780,nhandle=0x780378c4,strings=0x32000000;
inline constexpr unsigned crtheap=0x78035000,active_heap=0x78035004,newmode=0x78037150,heap_page=0x78035000,lower_page=0x20000000;
inline constexpr unsigned tls_index_cell=0x7803717c,version_first=0x78037158,version_last=0x78037164;
inline constexpr std::array<unsigned,4>lock_cells{0x7803706c,0x7803705c,0x7803704c,0x7803702c};
inline constexpr std::array<unsigned,4>static_locks{0x78037100,0x78037130,0x78037118,0x780370e8};
inline constexpr unsigned malloc_entry=0x780012b3,builder_ret=0x7800bc0b,alloc_raw=0x345c6;
inline constexpr unsigned token=0x48450001,arena=0x31000000,arena_end=0x32000000;
extern "C" void*mw34_attach_attach_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_mtinit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_mtinitlocks_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_calloc_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initptd_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_attach2_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_attach3_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_envstrings_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_attachb1_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_wcmdln_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_onexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_lockexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_msize_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_unlockexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_thunk_initterm_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_root1_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_root1_ctor_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_thunk_new_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_root1_atexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_atexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_onexit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_m_new_body(State*,unsigned,void*) noexcept(false);

extern "C" void*mw34_attach_attachb4_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_attach_epilogue_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_cinit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initterm_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initstdio_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initstdio_cold_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initstdio_tail_471_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initstdio_tail_474_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_onexitinit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_inittime_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_allmul_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_setfilter_body(State*,unsigned,void*) noexcept(false);

extern "C" void*mw34_attach_attachb3_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_setenvp_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_strlen_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_strcpy_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_free_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_freecold_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_free_tail_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_free_epilogue_body(State*,unsigned,void*) noexcept(false);

extern "C" void*mw34_attach_attachb2_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_initmbctable_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_setmbcp_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_getsyscp_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_setsbuplow_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_lcmapa_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_gettypea_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_lock_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_lock_tail_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_lock_enter_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_unlock_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_memset_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_strncnt_body(State*,unsigned,void*) noexcept(false);

extern "C" void*mw34_attach_ioinit_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_ioinit_cold_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_ioinit_tail_cac_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_ioinit_tail_cb0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_init_provider_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_mode_selector_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_mode_probe_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_version_branch_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_version_mode1_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_heap_version_epilogue_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_malloc_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_size_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_worker_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_round_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_alloc_tail_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_allocation_worker_epilogue_body(State*,unsigned,void*) noexcept(false);
using Body=void*(*)(State*,unsigned,void*);
extern "C" void*mw34_attach_g_r410030_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410030_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410030_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410080_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410080_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410080_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4100d0_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4100d0_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4100d0_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410120_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410120_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410120_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410170_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410170_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410170_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4101c0_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4101c0_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4101c0_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_4d8540_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410210_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410210_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410210_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410260_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410260_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410260_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4102b0_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4102b0_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4102b0_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410300_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410300_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410300_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410350_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410350_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410350_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103a0_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103a0_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103a0_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_4105d0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_410610_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_410630_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_4c8750_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_410650_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_410680_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_ctor_4c8600_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103f0_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103f0_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r4103f0_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410440_a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410440_b_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_r410440_c_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4c0310_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4c0570_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4bf910_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f58b1c0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f58b160_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4d5120_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f58aec0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4d5110_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f475bf0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f475c20_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f40baf0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f4fd1c0_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f5abd1a_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_m_delete_body(State*,unsigned,void*) noexcept(false);
extern "C" void*mw34_attach_g_f40a850_body(State*,unsigned,void*) noexcept(false);

constexpr unsigned Runtime_external_return(){return m4_runtime::Runtime::external_return;}

// Privately owned real provider resources for one host run: CRT heap and blocks,
// the TLS slot and the critical sections behind guest CRITICAL_SECTION objects.
struct HostHeap {
 struct Block{unsigned guest{},bytes{};void*native{};bool freed{};};
 HANDLE handle{};unsigned create_calls{},alloc_calls{},next=arena;std::vector<Block>blocks;
 unsigned unhandled_filter{};bool tls_freed{};bool fdiv_done{};unsigned fdiv_value{};
 DWORD tls=TLS_OUT_OF_INDEXES;std::vector<std::pair<unsigned,std::unique_ptr<CRITICAL_SECTION>>>locks;unsigned strings_next=strings;
 HostHeap()=default;HostHeap(const HostHeap&)=delete;HostHeap&operator=(const HostHeap&)=delete;
 ~HostHeap(){for(auto&l:locks)::DeleteCriticalSection(l.second.get());if(tls!=TLS_OUT_OF_INDEXES&&!tls_freed){::TlsSetValue(tls,nullptr);::TlsFree(tls);}
  if(handle){for(auto&b:blocks)if(b.native&&!b.freed)::HeapFree(handle,0,b.native);::HeapDestroy(handle);}}
 bool block(unsigned a,unsigned n)const{for(const auto&b:blocks)if(!b.freed&&a>=b.guest&&std::uint64_t(a)+n<=std::uint64_t(b.guest)+b.bytes)return true;return false;}
 CRITICAL_SECTION*lock(unsigned guest)const{for(const auto&l:locks)if(l.first==guest)return l.second.get();return nullptr;}
};
inline thread_local HostHeap*heap{};
inline thread_local void(*attach_hook)(m4_runtime::Runtime&){};
inline thread_local void(*resume_hook)(m4_runtime::Runtime&){};
inline thread_local bool(*fdiv_ready_hook)(){};
// Loader order: runs the FDIV initializer in place (generic native stage) from the State at its call; returns at its RET.
inline thread_local void(*fdiv_inplace_hook)(){};
inline thread_local void*initterm_stage_result{};inline thread_local unsigned initterm_roots{},initterm_node{},initterm_frontier{};inline thread_local std::array<unsigned,16>initterm_nodes{};

enum class Kind{attach,call,resume,initterm};
struct ShapeRoot{unsigned addr,object,ctor,node_offset;Body a,b,c,ctor_body;};
// Roots of the shape A: CALL A+10 (MOV ECX,object; JMP ctor) / JMP A+20 (PUSH A+30; CALL atexit).
inline constexpr std::array<ShapeRoot,15>shape_roots{{{0x40ffe0,0x603fd8,0x4c7b80,4,mw34_attach_g_root1_body,mw34_attach_g_root1_ctor_body,mw34_attach_g_root1_atexit_body,mw34_attach_g_ctor_body},
 {0x410030,0x603fe8,0x4d8540,8,mw34_attach_g_r410030_a_body,mw34_attach_g_r410030_b_body,mw34_attach_g_r410030_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x410080,0x603ff8,0x4d8540,8,mw34_attach_g_r410080_a_body,mw34_attach_g_r410080_b_body,mw34_attach_g_r410080_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x4100d0,0x604048,0x4d8540,8,mw34_attach_g_r4100d0_a_body,mw34_attach_g_r4100d0_b_body,mw34_attach_g_r4100d0_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x410120,0x604078,0x4d8540,8,mw34_attach_g_r410120_a_body,mw34_attach_g_r410120_b_body,mw34_attach_g_r410120_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x410170,0x603f90,0x4d8540,8,mw34_attach_g_r410170_a_body,mw34_attach_g_r410170_b_body,mw34_attach_g_r410170_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x4101c0,0x604038,0x4d8540,8,mw34_attach_g_r4101c0_a_body,mw34_attach_g_r4101c0_b_body,mw34_attach_g_r4101c0_c_body,mw34_attach_g_ctor_4d8540_body},
 {0x410210,0x603fa0,0x4105d0,0,mw34_attach_g_r410210_a_body,mw34_attach_g_r410210_b_body,mw34_attach_g_r410210_c_body,mw34_attach_g_ctor_4105d0_body},
 {0x410260,0x604058,0x410610,0,mw34_attach_g_r410260_a_body,mw34_attach_g_r410260_b_body,mw34_attach_g_r410260_c_body,mw34_attach_g_ctor_410610_body},
 {0x4102b0,0x604028,0x410630,0,mw34_attach_g_r4102b0_a_body,mw34_attach_g_r4102b0_b_body,mw34_attach_g_r4102b0_c_body,mw34_attach_g_ctor_410630_body},
 {0x410300,0x604068,0x4c8750,0,mw34_attach_g_r410300_a_body,mw34_attach_g_r410300_b_body,mw34_attach_g_r410300_c_body,mw34_attach_g_ctor_4c8750_body},
 {0x410350,0x604088,0x410650,0,mw34_attach_g_r410350_a_body,mw34_attach_g_r410350_b_body,mw34_attach_g_r410350_c_body,mw34_attach_g_ctor_410650_body},
 {0x4103a0,0x604098,0x410680,0,mw34_attach_g_r4103a0_a_body,mw34_attach_g_r4103a0_b_body,mw34_attach_g_r4103a0_c_body,mw34_attach_g_ctor_410680_body},
// Roots 14..15: objects registered with a free ID from [10000,10100) in root 1's list and holding a
// one-element pointer vector (node_offset 0xFFFF marks these complex 0x20-byte roots).
 {0x4103f0,0x604008,0x4c0310,0xffff,mw34_attach_g_r4103f0_a_body,mw34_attach_g_r4103f0_b_body,mw34_attach_g_r4103f0_c_body,mw34_attach_g_f4c0310_body},
 {0x410440,0x603fb8,0x4c0570,0xffff,mw34_attach_g_r410440_a_body,mw34_attach_g_r410440_b_body,mw34_attach_g_r410440_c_body,mw34_attach_g_f4c0570_body}}};
inline constexpr std::array<std::pair<unsigned,Body>,11>complex_helpers{{{0x4bf910,mw34_attach_g_f4bf910_body},{0x58b1c0,mw34_attach_g_f58b1c0_body},{0x58b160,mw34_attach_g_f58b160_body},{0x4d5120,mw34_attach_g_f4d5120_body},{0x58aec0,mw34_attach_g_f58aec0_body},{0x4d5110,mw34_attach_g_f4d5110_body},{0x475bf0,mw34_attach_g_f475bf0_body},{0x475c20,mw34_attach_g_f475c20_body},{0x40baf0,mw34_attach_g_f40baf0_body},{0x4fd1c0,mw34_attach_g_f4fd1c0_body},{0x5abd1a,mw34_attach_g_f5abd1a_body}}};
inline constexpr unsigned game_delete_iat=0x5bb4c8,game_delete_raw=0x80000339,mfc_free_cell=0x5f498148,id_base_global=0x5f2a48;
// Derived ctors of roots 8..13 call this base ctor (vtable 5CB180, field 8 cleared, flag bit 0 cleared).
inline constexpr unsigned base_ctor=0x4c8600;

inline constexpr unsigned game_table=0x5e0000,game_table_end=0x5e0244,root1=0x40ffe0,root1_object=0x603fd8,root1_exit=0x410010,game_onexitbegin=0x9a17f0;
inline constexpr unsigned game_initterm_iat=0x5bb510,game_initterm_raw=0x1ded12,game_new_iat=0x5bb4bc,game_new_raw=0x80000337,game_onexit_iat=0x5bb52c,game_onexit_raw=0x1decb0;
inline constexpr unsigned mfc_malloc_cell=0x5f49814c,mfc_new_data=0x5f498970,heapsize_raw=0x34bd0;
struct Stage;
inline thread_local Stage*owner{};
struct Stage {
 struct Call{unsigned target,ret;Body body;};
 struct Next{unsigned target;Body body;};
 m4_runtime::Runtime&runtime;State&state;mg::Context*context;HostHeap&host;Kind kind;void*token_ptr;
 unsigned entry_esp{},low{},high{},depth{},undefined_count{},reads{},writes{},request{},rounded{},result{},fs_saved{},api_calls{};
 unsigned version_raw{},version_platform{},version_major{},version_minor{},version_ok{},thread_id{},ptd{},ioinfo{},std_handles{},startup_flags{};
 unsigned pending_request{},env_wide_chars{},env_copy_bytes{},env_block{},env_bytes{},env_conversions{};bool env_freed{};LPWCH env_host{};
 unsigned wcmd_calls{},wcmd_guest{},wcmd_chars{};
 unsigned acp{},cpinfo_calls{},mbwc_calls{},stringtype_calls{},lcmap_calls{},wcmb_calls{},lock_object{},enter_calls{},leave_calls{};
 unsigned roots_run{},root1_node{},root1_onexit_calls{},frontier_root{};std::array<unsigned,16>nodes{};
 bool root_object(unsigned a,unsigned n)const{for(const auto&r:shape_roots)if(a>=r.object&&std::uint64_t(a)+n<=std::uint64_t(r.object)+(r.node_offset==0xffff?0x20U:16U))return true;return false;}
 bool complex_root()const{return roots_run&&shape_roots[roots_run-1].node_offset==0xffff;}
 unsigned complex_allocs{},complex_frees{};
 unsigned environ_allocs{},free_calls{};bool in_setenvp{},in_cinit{},attach_returned{};unsigned initializers_run{},piob_block{},onexit_block{};
 std::array<unsigned,4>saved{};std::array<unsigned,16>returns{};
 bool active{},complete{};std::thread::id thread=std::this_thread::get_id();
 Stage(m4_runtime::Runtime&r,mg::Context*c,HostHeap&h,Kind k,void*t):runtime(r),state(*reinterpret_cast<State*>(r.remill_state().data())),context(c),host(h),kind(k),token_ptr(t){
  const auto&g=state.gpr;saved={g.rbx.dword,g.rsi.dword,g.rdi.dword,g.rbp.dword};entry_esp=g.rsp.dword;
  if(kind==Kind::attach){
   if(entry_esp!=attach_esp||g.rip.dword!=attach_entry||host.handle||host.create_calls||host.tls!=TLS_OUT_OF_INDEXES||!host.locks.empty()||load(entry_esp+4)!=hinst||load(entry_esp+8)!=DLL_PROCESS_ATTACH||!load(entry_esp+12))
    deny("Exact declared _CRTDLL_INIT(DLL_PROCESS_ATTACH) projection frame on fresh host resources required",entry_esp);
   low=entry_esp-0x1400;high=entry_esp+16;  // covers the selector's 0x122C-byte _chkstk frame
  } else if(kind==Kind::initterm){
   if(g.rip.dword!=0x5ac598||load(entry_esp)!=0x5ac480||load(entry_esp+4)!=game_table||load(entry_esp+8)!=game_table_end||!host.handle||!load(onexit_begin)||load(game_initterm_iat)!=game_initterm_raw||load(game_new_iat)!=game_new_raw||load(game_onexit_iat)!=game_onexit_raw||load(game_onexitbegin)!=0xffffffffU)
    deny("Exact game main _initterm CALL on completed native MSVCRT attach required",entry_esp);
   low=0x20001000;high=entry_esp+12;
  } else if(kind==Kind::resume){
   if(entry_esp!=attach_esp-8||g.rip.dword!=resume_entry||!host.handle||host.tls==TLS_OUT_OF_INDEXES||host.locks.size()!=4||load(entry_esp+8)!=Runtime_external_return()||load(entry_esp+12)!=hinst||load(crtheap)!=token||!load(0x78037174))
    deny("Exact _CRTDLL_INIT resume frame after the _acmdln writer required",entry_esp);
   low=attach_esp-0x1400;high=attach_esp+16;
  } else {
   if(g.rip.dword!=malloc_entry||load(entry_esp)!=builder_ret||!host.handle||load(crtheap)!=token||load(active_heap)!=1)deny("Exact builder malloc CALL on the initialized mode-1 CRT heap required",entry_esp);
   request=load(entry_esp+4);rounded=((request?request:1)+15U)&~15U;fs_saved=load(runtime.fs_base().value);
   low=entry_esp-80;high=entry_esp+8;
  }
 }
 [[noreturn]]void deny(const char*w,unsigned a=0){if(context)context->deny(w,a,state.gpr.rip.dword);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{state.gpr.rip.dword},{a},w);}
 unsigned load(unsigned a){unsigned v{};bool bad{};try{v=runtime.memory().load<unsigned>({a});}catch(...){bad=true;}if(bad)deny("Checked heap-stage load fault",a);return v;}
 void store(unsigned a,unsigned v){bool bad{};try{runtime.memory().store<unsigned>({a},v);}catch(...){bad=true;}if(bad)deny("Checked heap-stage store fault",a);}
 void guard(void*p)const{if(owner!=this||!active||complete||p!=token_ptr||thread!=std::this_thread::get_id())const_cast<Stage*>(this)->deny("Exact current active heap Stage token required",state.gpr.rip.dword);}
 bool stack(unsigned a,bool write)const{return a%4==0&&a>=low&&std::uint64_t(a)+4<=(write?entry_esp:high);}
 bool fs(unsigned a)const{return a==runtime.fs_base().value;}
 unsigned read32(unsigned a,void*p){guard(p);bool ok=stack(a,false)||host.block(a,4);
  if(kind==Kind::attach)ok=ok||fs(a)||a==crtheap||a==active_heap||a==tls_index_cell||std::find(lock_cells.begin(),lock_cells.end(),a)!=lock_cells.end()||
   a==newmode||a==pioinfo||a==nhandle||a==env_flag||a==0x7802e0c0||a==0x7802e030||a==0x7802e0bc||a==0x7802e0b8||a==0x7802e0f0||a==0x7802e0e8||a==0x7802e0e4||
   a==0x7802e038||a==0x7802e0a8||a==0x7802e0a0||a==0x7802e03c||a==0x7802e068||a==0x7802e058||a==0x7802e064||a==0x7802e094;
  else if(kind==Kind::initterm)ok=ok||fs(a)||(a>=game_table&&a<game_table_end&&a%4==0)||a==game_initterm_iat||a==game_new_iat||a==game_onexit_iat||a==game_onexitbegin||a==mfc_malloc_cell||a==mfc_new_data||a==mfc_free_cell||a==game_delete_iat||a==id_base_global||a==0x5bcc80||a==0x5cab78||a==0x5ca6f0||
   a==newmode||a==crtheap||a==active_heap||a==onexit_begin||a==onexit_end||(a>=locktable&&a<0x780370e8)||(a>=0x7802e000&&a<0x7802e228&&a%4==0)||root_object(a,4);
  else if(kind==Kind::resume)ok=ok||(a>=0x78037c00&&a<0x78037ed0)||(a>=0x78037880&&a<0x78037894)||a==proc_attached||a==time_base||a==time_base+4||a==pioinfo||fs(a)||a==aenvptr||a==environ_cell||a==newmode||a==crtheap||a==active_heap||a==wcmd_flag||(a>=0x7802e000&&a<0x7802e228&&a%4==0)||(a>=locktable&&a<0x780370e8)||a==0x78037180||a==0x780375b8||(a>=0x780378d0&&a<0x78037c04);
  else ok=stack(a,false)||fs(a)||a==newmode||a==crtheap||a==active_heap||a==0x7802e094;
  if(!ok)deny("Heap-stage DWORD read outside its source contract",a);++reads;return load(a);}
 void write32(unsigned a,unsigned v,void*p){guard(p);bool ok=stack(a,true)||fs(a);
  if(kind==Kind::attach)ok=ok||host.block(a,4)||a==crtheap||a==active_heap||a==tls_index_cell||a==pioinfo||a==nhandle||a==env_flag||a==aenvptr||(a>=version_first&&a<=version_last&&a%4==0);
  if(kind==Kind::initterm)ok=ok||host.block(a,4)||a==onexit_end||root_object(a,4);
  if(kind==Kind::resume)ok=ok||host.block(a,4)||(in_cinit&&((a>=0x78037c58&&a<0x78037cb8)||a==piob||a==onexit_begin||a==onexit_end||a==prev_filter||a==proc_attached||a==time_base||a==time_base+4))||(in_setenvp&&(a==environ_cell||a==aenvptr))||a==wcmd_flag||a==wcmdln||a==0x780375b8||(a==mb_lock_cell&&lock_object&&v==lock_object&&!load(mb_lock_cell))||(a>=mbcodepage&&a<0x78037c04);
  if(!ok)deny("Heap-stage DWORD store outside its source contract",a);store(a,v);++writes;}
 bool resume_bytes(unsigned a,bool write)const{return kind==Kind::resume&&((a>=low&&a<entry_esp)||host.block(a,1)||(write?(a>=mbctype&&a<0x78037c00):(a>=0x780378d0&&a<0x78037c04)));}
 unsigned char read8(unsigned a,void*p){guard(p);if(!(kind==Kind::initterm&&((a>=low&&a<high)||root_object(a,1)))&&!resume_bytes(a,false)&&(kind!=Kind::attach||!host.block(a,1)))deny("Heap-stage byte read outside a real heap block",a);unsigned char v{};bool bad{};try{v=runtime.memory().load<unsigned char>({a});}catch(...){bad=true;}if(bad)deny("Checked heap-stage byte load",a);++reads;return v;}
 void write8(unsigned a,unsigned char v,void*p){guard(p);if(!(kind==Kind::initterm&&root_object(a,1))&&!resume_bytes(a,true)&&(kind!=Kind::attach||!host.block(a,1)))deny("Heap-stage byte store outside a real heap block",a);bool bad{};try{runtime.memory().store<unsigned char>({a},v);}catch(...){bad=true;}if(bad)deny("Checked heap-stage byte store",a);++writes;}
 void write16(unsigned a,unsigned short v,void*p){guard(p);if(kind!=Kind::resume||!host.block(a,2))deny("Heap-stage word store outside a real heap block",a);bool bad{};try{runtime.memory().store<unsigned short>({a},v);}catch(...){bad=true;}if(bad)deny("Checked heap-stage word store",a);++writes;}
 unsigned short read16(unsigned a,void*p){guard(p);const bool frame=a%2==0&&a>=low&&std::uint64_t(a)+2<=entry_esp,env=env_copy_bytes&&!env_freed&&a%2==0&&a>=env_copy&&std::uint64_t(a)+2<=std::uint64_t(env_copy)+env_copy_bytes;
  if((kind!=Kind::attach&&kind!=Kind::resume)||(!frame&&!env))deny("Heap-stage word read outside its stack frame or the environment copy",a);unsigned short v{};bool bad{};try{v=runtime.memory().load<unsigned short>({a});}catch(...){bad=true;}if(bad)deny("Checked heap-stage word load",a);++reads;return v;}
 void*called(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact heap-stage CALL State",target);
  static constexpr std::array<Call,13>attach_calls{{{0x780039bf,0x78001843,mw34_heap_init_provider_body},{0x78003a0c,0x780039e8,mw34_heap_mode_selector_body},{0x780058b5,0x78003a19,mw34_heap_mode_probe_body},
   {0x78003b98,0x78001875,mw34_attach_mtinit_body},{0x78003bf4,0x78003b9e,mw34_attach_mtinitlocks_body},{0x780018f9,0x78003bbb,mw34_attach_calloc_body},{0x780019de,0x78003be2,mw34_attach_initptd_body},
   {0x78003c1d,0x78001882,mw34_attach_ioinit_body},{0x780012b3,0x78003c30,mw34_allocation_malloc_body},{0x780012c5,0x780012c2,mw34_allocation_size_body},{0x780012e3,0x780012d9,mw34_allocation_worker_body},
   {0x78003cf1,0x78001887,mw34_attach_envstrings_body},{0x780012b3,0x78003d68,mw34_allocation_malloc_body}}};
  static constexpr std::array<Call,2>call_calls{{{0x780012c5,0x780012c2,mw34_allocation_size_body},{0x780012e3,0x780012d9,mw34_allocation_worker_body}}};
  const unsigned ret=load(state.gpr.rsp.dword);if(target==malloc_entry)pending_request=load(state.gpr.rsp.dword+4);
  auto enter=[&](const auto&table)->void*{for(const auto&c:table)if(c.target==target&&c.ret==ret){if(depth>=returns.size())deny("Heap-stage call depth bound",target);returns[depth++]=ret;return c.body(s,target,p);}return nullptr;};
  static constexpr std::array<Next,23>resume_targets{{{0x78004227,mw34_attach_cinit_body},{0x780014f8,mw34_attach_initterm_body},{0x780044dd,mw34_attach_allmul_body},{0x780018f9,mw34_attach_calloc_body},{0x78004187,mw34_attach_setenvp_body},{0x78002f32,mw34_attach_strlen_body},{0x78002fab,mw34_attach_strcpy_body},{0x78001390,mw34_allocation_free_body},{0x78003d9a,mw34_attach_wcmdln_body},{0x78003dd2,mw34_attach_initmbctable_body},{0x78003ddb,mw34_attach_setmbcp_body},{0x78001055,mw34_attach_lock_body},
   {0x780012b3,mw34_allocation_malloc_body},{0x780012c5,mw34_allocation_size_body},{0x780012e3,mw34_allocation_worker_body},{0x7800129e,mw34_attach_unlock_body},{0x78003e84,mw34_attach_getsyscp_body},
   {0x78003eb1,mw34_attach_setsbuplow_body},{0x78002e20,mw34_attach_gettypea_body},{0x78003fba,mw34_attach_lcmapa_body},{0x7800415d,mw34_attach_strncnt_body},{0x780058b5,mw34_heap_mode_probe_body},{0x78001000,mw34_attach_memset_body}}};
  if(kind==Kind::initterm&&complex_root())for(const auto&[h,body]:complex_helpers)if(h==target){if(depth>=returns.size())deny("Initializer call depth bound",target);returns[depth++]=ret;return body(s,target,p);}
  if(kind==Kind::initterm&&roots_run&&target==base_ctor&&!shape_roots[roots_run-1].node_offset){if(depth>=returns.size())deny("Initializer call depth bound",target);returns[depth++]=ret;return mw34_attach_g_ctor_4c8600_body(s,target,p);}
  if(kind==Kind::initterm&&roots_run&&target==shape_roots[roots_run-1].addr+0x10){if(depth>=returns.size())deny("Initializer call depth bound",target);returns[depth++]=ret;return shape_roots[roots_run-1].b(s,target,p);}
  static constexpr std::array<Next,11>initterm_targets{{{0,nullptr},{0x5abd26,mw34_attach_g_thunk_new_body},{0x5ac140,mw34_attach_g_atexit_body},{0x5ac110,mw34_attach_g_onexit_body},
   {0x78001514,mw34_attach_lockexit_body},{0x78001055,mw34_attach_lock_body},{0x7800151d,mw34_attach_msize_body},{0x78003041,mw34_attach_unlockexit_body},{0x7800129e,mw34_attach_unlock_body},{0x780012c5,mw34_allocation_size_body},{0x780012e3,mw34_allocation_worker_body}}};
  if(kind==Kind::initterm){for(const auto&n:initterm_targets)if(n.target==target){if(depth>=returns.size())deny("Initializer call depth bound",target);returns[depth++]=ret;return n.body(s,target,p);}
   deny("Unadmitted helper CALL inside main initializer root",target);}
  if(kind==Kind::resume){if(target==0x78004187)in_setenvp=true;if(target==0x78004227){in_setenvp=false;in_cinit=true;}for(const auto&n:resume_targets)if(n.target==target){if(ret<0x78001000||ret>=0x7802e000||depth>=returns.size())deny("Resume CALL return word outside provider code or depth bound",target);returns[depth++]=ret;return n.body(s,target,p);}}
  else if(void*r=kind==Kind::attach?enter(attach_calls):enter(call_calls))return r;
  if(target==0x78003aad)deny("Small-block heap mode 2 initialization is not admitted on this host",target);
  if(target==0x78001055||target==0x780010b0||target==0x780019d5||target==0x78001000)deny("Mode-2 small-block calloc/malloc helpers are not admitted on this host",target);
  deny("Unadmitted heap-stage helper CALL remains unresolved",target);}
 void*returned(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact heap-stage RET State",target);
  if(depth){if(target!=returns[depth-1])deny("Heap-stage RET to a non-source return address",target);--depth;return p;}
  const auto&g=state.gpr;
  if(kind==Kind::initterm&&target==0x5ac480)deny("Main initializer table completion beyond root 1 is not admitted yet",target);
  if(kind==Kind::resume&&target==Runtime_external_return()&&g.rsp.dword==attach_esp+16&&g.rax.dword==1&&attach_initialized()){finish_resume();attach_returned=true;return p;}
  if(kind==Kind::call&&target==builder_ret&&g.rsp.dword==entry_esp+4&&g.rbx.dword==saved[0]&&g.rsi.dword==saved[1]&&g.rdi.dword==saved[2]&&g.rbp.dword==saved[3]&&load(runtime.fs_base().value)==fs_saved&&g.rax.dword==result&&result){complete=true;return p;}
  deny("Heap-stage outermost RET outside its source contract",target);}
 void*missing(State*s,unsigned target,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=target)deny("Exact heap-stage continuation State",target);
  static constexpr std::array<Next,11>attach_next{{{0x78003a31,mw34_heap_version_branch_body},{0x7800ccc5,mw34_heap_version_mode1_body},{0x78003a7d,mw34_heap_version_epilogue_body},
   {attach_mid,mw34_attach_attach2_body},{attach_mid2,mw34_attach_attach3_body},{0x7800cc97,mw34_allocation_round_body},{0x78001377,mw34_allocation_alloc_tail_body},{0x78001367,mw34_allocation_worker_epilogue_body},
   {0x7800e4ad,mw34_attach_ioinit_cold_body},{0x78003cac,mw34_attach_ioinit_tail_cac_body},{0x78003cb0,mw34_attach_ioinit_tail_cb0_body}}};
  static constexpr std::array<Next,3>call_next{{{0x7800cc97,mw34_allocation_round_body},{0x78001377,mw34_allocation_alloc_tail_body},{0x78001367,mw34_allocation_worker_epilogue_body}}};
  if(kind==Kind::attach){
   for(const auto&n:attach_next)if(n.target==target&&((target==attach_mid||target==attach_mid2)?depth==0:depth!=0))return n.body(s,target,p);
   if(target==attach_end&&depth==0){finish_attach();return p;}
   if(target==0x7800baa0)deny("Win32s attach path is not admitted",target);
   if(target==0x78003a4b)deny("Heap selection environment path requires GetVersionExA failure or a pre-NT5 platform",target);
   if(target==0x7800bac3||target==0x7800cddc)deny("Source _heap_init failure path (HeapCreate returned NULL)",target);
   if(target==0x7800baca||target==0x7800bfd9)deny("Source _mtinit failure path (TLS or per-thread data unavailable)",target);
   if(target==0x7800cdc0||target==0x7800cdd0||target==0x7800ce57)deny("Heap modes 2/3 are not admitted on this host",target);
   if(target==0x7800ce50||target==0x7800ce48||target==0x7800cea3)deny("Source calloc overflow/zero/NULL path is not admitted",target);
   if(target==0x7800cc3f)deny("Source malloc NULL/new-handler path is not admitted (HeapAlloc returned NULL)",target);
   if(target==0x7800e3c1)deny("Source _ioinit allocation failure path",target);
   if(target==0x7800e3ce||target==0x7800e4cf)deny("Inherited CRT handle table (STARTUPINFO cbReserved2) is not admitted",target);
   if(target==0x7800f13d||target==0x7800f0e5||target==0x7800f14d||target==0x7800f160)deny("Repeat, ANSI-fallback or failed environment-strings path is not admitted",target);
  } else if(kind==Kind::initterm){
   if(roots_run&&depth){const auto&r=shape_roots[roots_run-1];if(target==r.ctor)return r.ctor_body(s,target,p);if(target==r.addr+0x20)return r.c(s,target,p);}
   if(complex_root()&&depth){if(target==0x7800cc39)return mw34_allocation_freecold_body(s,target,p);if(target==0x78001428)return mw34_allocation_free_tail_body(s,target,p);if(target==0x78001416)return mw34_allocation_free_epilogue_body(s,target,p);}
   static constexpr std::array<Next,5>initterm_next{{{0,nullptr},{0,nullptr},{0x7800cc97,mw34_allocation_round_body},{0x78001377,mw34_allocation_alloc_tail_body},{0x78001367,mw34_allocation_worker_epilogue_body}}};
   for(const auto&n:initterm_next)if(n.body&&n.target==target&&depth)return n.body(s,target,p);
   if(target==0x7801e27b)deny("Source _onexit table growth (realloc) path is not admitted",target);
   if(target==0x5f41b01e)deny("MFC42 operator new failure/new-handler path is not admitted",target);
  } else if(kind==Kind::resume){
   static constexpr std::array<Next,12>resume_next{{{0x7800f945,mw34_attach_initstdio_cold_body},{0x78004471,mw34_attach_initstdio_tail_471_body},{0x78004474,mw34_attach_initstdio_tail_474_body},{0x7800cc39,mw34_allocation_freecold_body},{0x78001428,mw34_allocation_free_tail_body},{0x78001416,mw34_allocation_free_epilogue_body},{0x78001080,mw34_attach_lock_tail_body},{0x7800106d,mw34_attach_lock_enter_body},{0x7800cc97,mw34_allocation_round_body},{0x78001377,mw34_allocation_alloc_tail_body},{0x78001367,mw34_allocation_worker_epilogue_body},{0,nullptr}}};
   if(target==resume_mid&&depth==0)return mw34_attach_attachb2_body(s,target,p);
   if(target==resume_mid2&&depth==0)return mw34_attach_attachb3_body(s,target,p);
   if(target==resume_mid3&&depth==0)return mw34_attach_attachb4_body(s,target,p);
   if(target==0x7800181b&&depth==0&&attach_initialized())return mw34_attach_attach_epilogue_body(s,target,p);
   if(target==0x7800f919||target==0x7801e2d2)deny("Source MSVCRT initializer allocation failure path",target);
   for(const auto&n:resume_next)if(n.body&&n.target==target&&depth)return n.body(s,target,p);
   if(false&&target==resume_end){finish_resume();return p;}
   if(target==0x7800f0c9||target==0x7800f06c)deny("Repeat or unavailable wide command-line path is not admitted",target);
  } else {
   for(const auto&n:call_next)if(n.target==target&&depth==2)return n.body(s,target,p);
   if(target==0x7800cc3f)deny("Source malloc NULL/new-handler path is not admitted (HeapAlloc returned NULL)",target);
  }
  deny("Unadmitted heap-stage continuation remains unresolved",target);}
 void finish_attach(){const auto&g=state.gpr;
  if(g.rsp.dword!=attach_esp-8||g.rdi.dword!=saved[2]||g.rbp.dword!=saved[3]||load(crtheap)!=token||load(active_heap)!=1||!host.handle||host.tls==TLS_OUT_OF_INDEXES||load(tls_index_cell)!=host.tls||host.locks.size()!=4||!ptd||::TlsGetValue(host.tls)!=reinterpret_cast<void*>(std::uintptr_t(ptd))||load(ptd)!=thread_id||load(ptd+4)!=0xffffffffU)
   deny("_CRTDLL_INIT must reach the environment-strings CALL (78001882) with the heap, version globals, locks, TLS and per-thread data published",attach_end);
  if(!ioinfo||load(pioinfo)!=ioinfo||load(nhandle)!=0x20||std_handles!=3)deny("_ioinit must publish __pioinfo[0], _nhandle=32 and classify three standard handles",attach_end);
  if(!env_block||!env_freed||env_conversions!=2||load(aenvptr)!=env_block||load(env_flag)!=1||g.rax.dword!=env_block)deny("Environment strings must be converted, freed and published as _aenvptr",attach_end);
  complete=true;}
 // Kernel handle values are 32-bit significant; anything else is refused, never truncated.
 unsigned guest_handle(HANDLE h){const auto v=reinterpret_cast<std::intptr_t>(h);if(v!=std::intptr_t(std::int32_t(v)))deny("Host handle not representable as a guest handle",0);return static_cast<unsigned>(v);}
 unsigned guest_string(const char*text){if(!text)return 0;const std::size_t n=std::strlen(text)+1;if(host.strings_next==strings){bool bad{};try{runtime.memory().map({strings},4096,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked provider string page",strings);}
  if(std::uint64_t(host.strings_next)+n>strings+4096)deny("Provider string page exhausted",host.strings_next);const unsigned g=host.strings_next;
  runtime.memory().write({g},std::span<const std::byte>(reinterpret_cast<const std::byte*>(text),n));host.strings_next+=unsigned(n);return g;}
 bool attach_initialized(){return in_cinit&&initializers_run==4&&load(proc_attached)==1&&onexit_block&&load(onexit_begin)==onexit_block&&load(onexit_end)==onexit_block&&piob_block&&load(piob)==piob_block&&host.unhandled_filter==guest_filter;}
 unsigned env_block_guest()const{return host.blocks.size()>2?host.blocks[2].guest:0;}  // the attach _aenvptr block
 void finish_resume(){const auto&g=state.gpr;
  if(wcmd_calls!=2||!wcmd_guest||load(wcmdln)!=wcmd_guest||load(wcmd_flag)!=1)deny("Resumed attach must publish the wide command line as _wcmdln",resume_end);
  if(!acp||load(mbcodepage)!=acp||load(mb_system_set)!=1||!lock_object||load(mb_lock_cell)!=lock_object||!host.lock(lock_object)||host.lock(lock_object)->RecursionCount||enter_calls!=leave_calls||!cpinfo_calls||!stringtype_calls||lcmap_calls<2)
   deny("__initmbctable must publish the system code page and SBCS tables and release lock 25",resume_end);
  if(!environ_allocs||!load(environ_cell)||!host.block(load(environ_cell),4)||load(aenvptr)||free_calls!=1)deny("_setenvp must publish _environ and free _aenvptr",resume_end);
  complete=true;}
 unsigned publish(unsigned bytes,DWORD flags){void*block{};{DWORD e=GetLastError();block=::HeapAlloc(host.handle,flags,bytes);++host.alloc_calls;SetLastError(e);}
  if(!block)return 0;const unsigned pages=(bytes+4095U)&~4095U,guest=host.next;
  if(std::uint64_t(guest)+pages>arena_end){::HeapFree(host.handle,0,block);deny("Guest heap arena exhausted",guest);}
  host.blocks.push_back({guest,bytes,block});host.next+=pages;std::vector<std::byte>v(pages);std::memcpy(v.data(),block,bytes);
  bool bad{};try{runtime.memory().map({guest},pages,Permissions::read|Permissions::write);runtime.memory().write({guest},v);}catch(...){bad=true;}if(bad)deny("Checked guest heap block publication",guest);return guest;}
 void*api(State*s,unsigned raw,void*p){guard(p);if(s!=&state||state.gpr.rip.dword!=raw)deny("Exact heap-stage import State",raw);
  auto&g=state.gpr;const unsigned e=g.rsp.dword,ret=load(e);
  struct ErrorBoundary{DWORD v=GetLastError();~ErrorBoundary(){SetLastError(v);}};
  auto done=[&](unsigned eax,unsigned args){g.rax.dword=eax;g.rsp.dword=e+4+4*args;g.rip.dword=ret;++api_calls;return p;};
  if(kind==Kind::attach){
   if(raw==0x34440&&ret==0x78001829&&!version_raw){
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    {ErrorBoundary b;version_raw=::GetVersion();}
#pragma clang diagnostic pop
    return done(version_raw,0);}
   if(raw==0x3461e&&ret==0x780039d6){if(load(e+4)!=0||load(e+8)!=0x1000||load(e+12)!=0||host.handle)deny("Exact source HeapCreate(0,0x1000,0) frame required",raw);
    {ErrorBoundary b;host.handle=::HeapCreate(0,0x1000,0);++host.create_calls;}return done(host.handle?token:0,3);}
   if(raw==0x34600&&ret==0x78003a31){const unsigned info=load(e+4);
    if(info!=g.rbp.dword-0x98||!stack(info,true)||std::uint64_t(info)+0x94>entry_esp||load(info)!=0x94)deny("Exact source GetVersionExA(OSVERSIONINFOA) frame required",raw);
    OSVERSIONINFOA v{};v.dwOSVersionInfoSize=sizeof(v);static_assert(sizeof(OSVERSIONINFOA)==0x94);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    {ErrorBoundary b;version_ok=::GetVersionExA(&v)?1U:0U;}
#pragma clang diagnostic pop
    std::array<std::byte,sizeof(v)>bytes{};std::memcpy(bytes.data(),&v,sizeof(v));
    bool bad{};try{runtime.memory().write({info},bytes);}catch(...){bad=true;}if(bad)deny("Checked OSVERSIONINFOA output",info);
    version_major=v.dwMajorVersion;version_minor=v.dwMinorVersion;version_platform=v.dwPlatformId;return done(version_ok,1);}
   if(raw==0x3444e){static constexpr std::array<unsigned,4>rets{0x78003c03,0x78003c0b,0x78003c13,0x78003c1b};const auto n=host.locks.size();const unsigned cs=load(e+4);
    if(n>=4||ret!=rets[n]||cs!=static_locks[n]||load(lock_cells[n])!=cs||host.lock(cs))deny("Exact source _mtinitlocks InitializeCriticalSection order and static object required",raw);
    auto native=std::make_unique<CRITICAL_SECTION>();{ErrorBoundary b;::InitializeCriticalSection(native.get());}
    // Guest RTL_CRITICAL_SECTION (x86): DebugInfo, LockCount, RecursionCount, OwningThread, LockSemaphore, SpinCount.
    const auto debug=reinterpret_cast<std::uintptr_t>(native->DebugInfo);
    if((debug&&debug!=~std::uintptr_t{})||native->RecursionCount||native->OwningThread||native->LockSemaphore)deny("Host critical-section initial fields not representable in the guest object",cs);
    const std::array<unsigned,6>fields{debug?0xffffffffU:0U,static_cast<unsigned>(native->LockCount),0,0,0,static_cast<unsigned>(native->SpinCount)};
    for(unsigned i=0;i<6;++i)store(cs+4*i,fields[i]);host.locks.emplace_back(cs,std::move(native));return done(0,1);}
   if(raw==0x34522&&ret==0x78003ba4&&host.tls==TLS_OUT_OF_INDEXES){{ErrorBoundary b;host.tls=::TlsAlloc();}if(host.tls!=TLS_OUT_OF_INDEXES&&host.tls>=0x80000000U)deny("Host TLS index not representable",raw);return done(host.tls,0);}
   if(raw==0x345c6&&ret==0x780019c7){const unsigned size=load(e+12);if(load(e+4)!=token||load(e+8)!=HEAP_ZERO_MEMORY||size!=0x80||ptd)deny("Exact source calloc HeapAlloc(_crtheap,HEAP_ZERO_MEMORY,0x80) frame required",raw);
    ptd=publish(size,HEAP_ZERO_MEMORY);return done(ptd,3);}
   if(raw==0x344e2&&ret==0x78003bd4){if(load(e+4)!=host.tls||load(e+8)!=ptd||!ptd)deny("Exact source TlsSetValue(__tlsindex,ptd) frame required",raw);
    BOOL ok{};{ErrorBoundary b;ok=::TlsSetValue(host.tls,reinterpret_cast<void*>(std::uintptr_t(ptd)));}return done(ok?1U:0U,2);}
   if(raw==0x3450c&&ret==0x78003be9&&!thread_id){thread_id=::GetCurrentThreadId();return done(thread_id,0);}
   if(raw==alloc_raw&&ret==0x78001385){const unsigned size=load(e+12);if(load(e+4)!=token||load(e+8)!=0||size!=(((pending_request?pending_request:1)+15U)&~15U))deny("Exact source malloc HeapAlloc(_crtheap,0,rounded request) frame required",raw);
    if(!ioinfo){if(pending_request!=0x480)deny("First attach malloc must be the _ioinit table",raw);ioinfo=publish(size,0);return done(ioinfo,3);}
    if(!env_block&&env_wide_chars&&!env_freed){env_bytes=pending_request;env_block=publish(size,0);return done(env_block,3);}
    deny("Unadmitted attach allocation",raw);}
   if(raw==0x34758&&ret==0x78003d12&&!env_host){{ErrorBoundary b;env_host=::GetEnvironmentStringsW();}if(!env_host)return done(0,0);
    std::size_t n=0;while(env_host[n]||env_host[n+1])++n;n+=2;  // through the terminating double NUL
    env_wide_chars=unsigned(n);env_copy_bytes=unsigned(n*2);const unsigned pages=(env_copy_bytes+4095U)&~4095U;
    bool bad{};try{runtime.memory().map({env_copy},pages,Permissions::read|Permissions::write);runtime.memory().write({env_copy},std::span<const std::byte>(reinterpret_cast<const std::byte*>(env_host),env_copy_bytes));}catch(...){bad=true;}if(bad)deny("Checked guest environment copy",env_copy);
    return done(env_copy,0);}
   if(raw==0x3472a&&(ret==0x78003d5c||ret==0x78003d7e)){const unsigned cp=load(e+4),flags=load(e+8),wide=load(e+12),cch=load(e+16),out=load(e+20),cb=load(e+24);
    const bool sizing=ret==0x78003d5c;
    if(cp!=CP_ACP||flags||wide!=env_copy||env_freed||cch!=env_wide_chars||load(e+28)||load(e+32)||(sizing?(out||cb||env_conversions):(env_conversions!=1||out!=env_block||cb!=env_bytes||!host.block(out,cb))))
     deny("Exact source WideCharToMultiByte(CP_ACP) sizing/fill frame required",raw);
    std::vector<char>buffer(sizing?0:cb);int r{};{ErrorBoundary b;r=::WideCharToMultiByte(CP_ACP,0,env_host,int(cch),sizing?nullptr:buffer.data(),int(cb),nullptr,nullptr);}
    if(!sizing&&r>0){bool bad{};try{runtime.memory().write({out},std::span<const std::byte>(reinterpret_cast<const std::byte*>(buffer.data()),std::size_t(r)));}catch(...){bad=true;}if(bad)deny("Checked environment conversion output",out);}
    ++env_conversions;return done(unsigned(r),8);}
   if(raw==0x34710&&ret==0x78003d91){if(load(e+4)!=env_copy||!env_host||env_freed)deny("Exact source FreeEnvironmentStringsW(block) frame required",raw);BOOL ok{};{ErrorBoundary b;ok=::FreeEnvironmentStringsW(env_host);}
    env_freed=true;bool bad{};try{runtime.memory().unmap({env_copy});}catch(...){bad=true;}if(bad)deny("Checked guest environment copy release",env_copy);return done(ok?1U:0U,1);}
   if(raw==0x34678&&ret==0x78003c7d){const unsigned info=load(e+4);if(info!=g.rbp.dword-0x48||!stack(info,true)||std::uint64_t(info)+68>entry_esp)deny("Exact source GetStartupInfoA frame required",raw);
    STARTUPINFOA si{};si.cb=sizeof(si);{ErrorBoundary b;::GetStartupInfoA(&si);}startup_flags=si.dwFlags;
    if(si.cbReserved2||si.lpReserved2)deny("Inherited CRT handle table (STARTUPINFO lpReserved2) is not admitted",raw);
    // x86 STARTUPINFOA: strings are copied into the provider-owned guest string page.
    const std::array<unsigned,17>w{68,guest_string(si.lpReserved),guest_string(si.lpDesktop),guest_string(si.lpTitle),si.dwX,si.dwY,si.dwXSize,si.dwYSize,si.dwXCountChars,si.dwYCountChars,si.dwFillAttribute,si.dwFlags,
     unsigned(si.wShowWindow)|(unsigned(si.cbReserved2)<<16),0,guest_handle(si.hStdInput),guest_handle(si.hStdOutput),guest_handle(si.hStdError)};
    for(unsigned i=0;i<w.size();++i)store(info+4*i,w[i]);return done(0,1);}
   if(raw==0x3441e&&ret==0x78003c96){const unsigned n=load(e+4);static constexpr std::array<unsigned,3>ids{0xfffffff6U,0xfffffff5U,0xfffffff4U};if(std_handles>=3||n!=ids[std_handles])deny("Exact source GetStdHandle(-10,-11,-12) order required",raw);
    HANDLE h{};{ErrorBoundary b;h=::GetStdHandle(static_cast<DWORD>(n));}++std_handles;return done(guest_handle(h),1);}
   if(raw==0x3466a&&ret==0x78003ca4){const unsigned h=load(e+4);DWORD type{};{ErrorBoundary b;type=::GetFileType(reinterpret_cast<HANDLE>(std::intptr_t(std::int32_t(h))));}return done(type,1);}
   if(raw==0x34658&&ret==0x78003cec){if(load(e+4)!=0x20||std_handles!=3)deny("Exact source SetHandleCount(32) after the handle loop required",raw);
    using Fn=UINT(WINAPI*)(UINT);const auto fn=reinterpret_cast<Fn>(::GetProcAddress(::GetModuleHandleW(L"kernel32.dll"),"SetHandleCount"));if(!fn)deny("Host SetHandleCount export unavailable",raw);
    UINT r{};{ErrorBoundary b;r=fn(0x20);}return done(r,1);}
  } else if(kind==Kind::initterm){
   if(ret==0x78001510&&roots_run<shape_roots.size()&&raw==shape_roots[roots_run].addr){++roots_run;returns[depth++]=ret;return shape_roots[roots_run-1].a(s,raw,p);}
   if(ret==0x78001510&&raw>=0x401000&&raw<0x5bb000){frontier_root=raw;throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{0x7800150e},{raw},"Main C++ initializer after root 1 is not yet connected");}
   if(raw==0x780012b3&&ret==0x5f401eb7){pending_request=load(e+4);returns[depth++]=ret;return mw34_allocation_malloc_body(s,raw,p);}
   // Virtual GetID (vtable slot +18 = 40A850) called by the ID search over root 1's list.
   if(raw==0x40a850&&ret==0x58b186&&complex_root()){returns[depth++]=ret;return mw34_attach_g_f40a850_body(s,raw,p);}
   if(raw==0x78001390&&ret==0x5f40178c&&complex_root()){returns[depth++]=ret;return mw34_allocation_free_body(s,raw,p);}
   if(raw==0x345ba&&ret==0x78001436&&complex_root()){const unsigned ptr=load(e+12);if(load(e+4)!=token||load(e+8)!=0)deny("Exact source free HeapFree(_crtheap,0,p) frame required",raw);
    for(auto&b:host.blocks)if(!b.freed&&b.guest==ptr){BOOL ok{};{ErrorBoundary eb;ok=::HeapFree(host.handle,0,b.native);}b.freed=true;bool bad{};try{runtime.memory().unmap({ptr});}catch(...){bad=true;}if(bad)deny("Checked guest block release",ptr);++complex_frees;return done(ok?1U:0U,3);}
    deny("HeapFree of a pointer that is not a live real heap block",ptr);}
   if(raw==game_onexit_raw&&ret==0x5ac124){returns[depth++]=ret;return mw34_attach_onexit_body(s,0x78004a36,p);}
   if(raw==alloc_raw&&ret==0x78001385){const unsigned size=load(e+12);if(load(e+4)!=token||load(e+8)!=0||(complex_root()?size!=(((pending_request?pending_request:1)+15U)&~15U):(pending_request!=0xc||size!=0x10||!roots_run||!shape_roots[roots_run-1].node_offset||nodes[roots_run-1])))deny("Exact root operator new HeapAlloc(_crtheap,0,0x10) frame required",raw);if(complex_root()){++complex_allocs;return done(publish(size,0),3);}nodes[roots_run-1]=publish(size,0);if(roots_run==1)root1_node=nodes[0];return done(nodes[roots_run-1],3);}
   if(raw==0x34482||raw==0x3449a){const unsigned cs=load(e+4);auto*native=host.lock(cs);if(!native||cs!=0x78037130)deny("Root 1 Enter/LeaveCriticalSection must use the static exit lock",cs);
    {ErrorBoundary b;if(raw==0x34482)::EnterCriticalSection(native);else ::LeaveCriticalSection(native);}
    store(cs+4,static_cast<unsigned>(native->LockCount));store(cs+8,static_cast<unsigned>(native->RecursionCount));store(cs+12,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(native->OwningThread)));
    if(raw==0x34482)++enter_calls;else ++leave_calls;return done(0,1);}
   if(raw==heapsize_raw&&ret==0x780015bb){const unsigned ptr=load(e+12);if(load(e+4)!=token||load(e+8)!=0)deny("Exact source _msize HeapSize frame required",raw);
    for(const auto&b:host.blocks)if(!b.freed&&b.guest==ptr){SIZE_T n{};{ErrorBoundary eb;n=::HeapSize(host.handle,0,b.native);}++root1_onexit_calls;return done(unsigned(n),3);}deny("HeapSize of a pointer that is not a live real heap block",ptr);}
  } else if(kind==Kind::resume){
   auto in=[&](unsigned a,unsigned n){return (a>=low&&std::uint64_t(a)+n<=entry_esp)||host.block(a,n)||(a>=0x7802e000&&std::uint64_t(a)+n<=0x78030000);};
   auto get=[&](unsigned a,unsigned n){if(!in(a,n))deny("Import input buffer outside the resume contract",a);std::vector<std::byte>v(n);bool bad{};try{for(unsigned o=0;o<n;){const unsigned k=std::min(n-o,4096U-((a+o)&4095U));runtime.memory().read({a+o},std::span<std::byte>(v.data()+o,k));o+=k;}}catch(...){bad=true;}if(bad)deny("Checked import input",a);return v;};
   auto put=[&](unsigned a,const void*d,unsigned n){if(!n)return;if(!in(a,n)||(a>=0x7802e000&&a<0x78030000))deny("Import output buffer outside the resume contract",a);bool bad{};try{const auto*b=static_cast<const std::byte*>(d);for(unsigned o=0;o<n;){const unsigned k=std::min(n-o,4096U-((a+o)&4095U));runtime.memory().write({a+o},std::span<const std::byte>(b+o,k));o+=k;}}catch(...){bad=true;}if(bad)deny("Checked import output",a);};
   if(ret<0x78001000||ret>=0x7802e000)deny("Import return word outside provider code",raw);
   if(raw==fdiv_writer&&ret==0x78004232&&in_cinit&&!host.fdiv_done&&fdiv_inplace_hook){
    // Loader order (play path): _cinit calls the FDIV initializer here, as in the original process. This stage yields
    // ownership while the generic native stage runs the lifted initializer on this frame with real services
    // (GetModuleHandleA, GetProcAddress, IsProcessorFeaturePresent; the _controlfp helpers; FNCLEX), then resumes.
    {Stage*self=owner;owner=nullptr;struct Back{Stage*s;~Back(){owner=s;}}back{self};fdiv_inplace_hook();}
    if(g.rip.dword!=ret||g.rsp.dword!=e+4)deny("In-place FDIV initializer must return to its _cinit call",raw);
    host.fdiv_done=true;host.fdiv_value=load(fdiv_flag);++api_calls;return p;}
   if(raw==fdiv_writer&&ret==0x78004232&&in_cinit&&!host.fdiv_done){
    // The accepted FDIV registry already executed this exact callback natively (BEFORE point).
    if(!fdiv_ready_hook||!fdiv_ready_hook())deny("FDIV callback requires the completed accepted registry writer job",raw);
    host.fdiv_done=true;host.fdiv_value=load(fdiv_flag);return done(host.fdiv_value,0);}
   static constexpr std::array<Next,4>initializers{{{0x78004410,mw34_attach_initstdio_body},{0x78004482,mw34_attach_onexitinit_body},{0x780044a8,mw34_attach_inittime_body},{0x7800450c,mw34_attach_setfilter_body}}};
   for(const auto&n:initializers)if(n.target==raw&&in_cinit&&ret==0x78001510){if(depth>=returns.size())deny("Initializer depth bound",raw);returns[depth++]=ret;++initializers_run;return n.body(s,raw,p);}
   if(raw==0x34d08){const unsigned out=load(e+4);FILETIME ft{};{ErrorBoundary b;::GetSystemTimeAsFileTime(&ft);}put(out,&ft,8);return done(0,1);}
   if(raw==0x34392){const unsigned filter=load(e+4);if(filter!=guest_filter||host.unhandled_filter)deny("Exact source SetUnhandledExceptionFilter(7800B322) once required",raw);
    // Registered in the host-owned guest runtime model (the host process filter is untouched);
    // the previous guest filter of a fresh process is none.
    host.unhandled_filter=filter;return done(0,1);}
   if(raw==0x345c6&&ret==0x780019c7&&in_cinit&&!piob_block){const unsigned size=load(e+12);if(load(e+4)!=token||load(e+8)!=HEAP_ZERO_MEMORY||size!=0x800)deny("Exact source __initstdio calloc(512,4) frame required",raw);piob_block=publish(size,HEAP_ZERO_MEMORY);return done(piob_block,3);}
   if(raw==alloc_raw&&ret==0x78001385){const unsigned size=load(e+12);if(load(e+4)!=token||load(e+8)!=0||size!=(((pending_request?pending_request:1)+15U)&~15U))deny("Exact source malloc HeapAlloc(_crtheap,0,rounded request) frame required",raw);
    if(!lock_object&&!in_setenvp){if(pending_request!=0x18)deny("Exact source _lock object allocation required",raw);lock_object=publish(size,0);return done(lock_object,3);}
    if(in_setenvp){++environ_allocs;return done(publish(size,0),3);}
    if(in_cinit&&!onexit_block&&pending_request==0x80){onexit_block=publish(size,0);return done(onexit_block,3);}deny("Unadmitted resume allocation",raw);}
   if(raw==free_raw&&ret==0x78001436){const unsigned ptr=load(e+12);if(load(e+4)!=token||load(e+8)!=0||!in_setenvp||ptr!=env_block_guest())deny("Exact source free(_aenvptr) HeapFree frame required",raw);
    BOOL ok{};for(auto&b:host.blocks)if(!b.freed&&b.guest==ptr){{ErrorBoundary eb;ok=::HeapFree(host.handle,0,b.native);}b.freed=true;bool bad{};try{runtime.memory().unmap({ptr});}catch(...){bad=true;}if(bad)deny("Checked guest block release",ptr);}
    ++free_calls;return done(ok?1U:0U,3);}
   if(raw==0x3444e){const unsigned cs=load(e+4);if(cs!=lock_object||!host.block(cs,24)||host.lock(cs))deny("Exact lazily created lock InitializeCriticalSection required",raw);
    auto native=std::make_unique<CRITICAL_SECTION>();{ErrorBoundary b;::InitializeCriticalSection(native.get());}const auto debug=reinterpret_cast<std::uintptr_t>(native->DebugInfo);
    if((debug&&debug!=~std::uintptr_t{})||native->RecursionCount||native->OwningThread||native->LockSemaphore)deny("Host critical-section initial fields not representable in the guest object",cs);
    const std::array<unsigned,6>fields{debug?0xffffffffU:0U,static_cast<unsigned>(native->LockCount),0,0,0,static_cast<unsigned>(native->SpinCount)};for(unsigned i=0;i<6;++i)store(cs+4*i,fields[i]);host.locks.emplace_back(cs,std::move(native));return done(0,1);}
   if(raw==0x34482||raw==0x3449a){const unsigned cs=load(e+4);auto*native=host.lock(cs);if(!native)deny("Enter/LeaveCriticalSection on a guest object without a real host section",cs);
    {ErrorBoundary b;if(raw==0x34482)::EnterCriticalSection(native);else ::LeaveCriticalSection(native);}
    // Mirror the x86-visible LockCount/RecursionCount/OwningThread fields into the guest object.
    store(cs+4,static_cast<unsigned>(native->LockCount));store(cs+8,static_cast<unsigned>(native->RecursionCount));store(cs+12,static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(native->OwningThread)));
    if(raw==0x34482)++enter_calls;else ++leave_calls;return done(0,1);}
   if(raw==0x34696&&ret==0x78003df3){{ErrorBoundary b;acp=::GetACP();}return done(acp,0);}
   if(raw==0x3468a){const unsigned cp=load(e+4),out=load(e+8);CPINFO info{};BOOL ok{};{ErrorBoundary b;ok=::GetCPInfo(cp,&info);}static_assert(sizeof(CPINFO)==20);if(ok)put(out,&info,sizeof(info));++cpinfo_calls;return done(ok?1U:0U,2);}
   if(raw==0x346ce){const unsigned cp=load(e+4),flags=load(e+8),src=load(e+12),cb=load(e+16),out=load(e+20),cch=load(e+24);if(int(cb)<=0)deny("Unadmitted MultiByteToWideChar source length",raw);
    const auto bytes=get(src,cb);std::vector<wchar_t>w(cch);int r{};{ErrorBoundary b;r=::MultiByteToWideChar(cp,flags,reinterpret_cast<const char*>(bytes.data()),int(cb),out?w.data():nullptr,int(out?cch:0));}
    if(out&&r>0)put(out,w.data(),unsigned(r)*2);++mbwc_calls;return done(unsigned(r),6);}
   if(raw==0x347a0){const unsigned type=load(e+4),src=load(e+8),cch=load(e+12),out=load(e+16);if(int(cch)<=0)deny("Unadmitted GetStringTypeW length",raw);const auto w=get(src,cch*2);std::vector<WORD>t(cch);BOOL ok{};
    {ErrorBoundary b;ok=::GetStringTypeW(type,reinterpret_cast<LPCWCH>(w.data()),int(cch),t.data());}if(ok)put(out,t.data(),cch*2);++stringtype_calls;return done(ok?1U:0U,4);}
   if(raw==0x347c2){const unsigned lcid=load(e+4),flags=load(e+8),src=load(e+12),cch=load(e+16),out=load(e+20),cchout=load(e+24);if(int(cch)<=0)deny("Unadmitted LCMapStringW length",raw);const auto w=get(src,cch*2);std::vector<wchar_t>o(cchout);int r{};
    {ErrorBoundary b;r=::LCMapStringW(lcid,flags,reinterpret_cast<LPCWSTR>(w.data()),int(cch),out?o.data():nullptr,int(out?cchout:0));}if(out&&r>0)put(out,o.data(),unsigned(r)*2);++lcmap_calls;return done(unsigned(r),6);}
   if(raw==0x3472a){const unsigned cp=load(e+4),flags=load(e+8),src=load(e+12),cch=load(e+16),out=load(e+20),cb=load(e+24);if(int(cch)<=0||load(e+28)||load(e+32))deny("Unadmitted WideCharToMultiByte frame",raw);const auto w=get(src,cch*2);std::vector<char>o(cb);int r{};
    {ErrorBoundary b;r=::WideCharToMultiByte(cp,flags,reinterpret_cast<LPCWCH>(w.data()),int(cch),out?o.data():nullptr,int(out?cb:0),nullptr,nullptr);}if(out&&r>0)put(out,o.data(),unsigned(r));++wcmb_calls;return done(unsigned(r),8);}
   if(raw==0x346e4&&(ret==0x78003db9||ret==0x78003dcd)&&wcmd_calls<2){if(!wcmd_guest){LPWSTR w{};{ErrorBoundary b;w=::GetCommandLineW();}if(!w)return done(0,0);
     wcmd_chars=unsigned(std::wcslen(w)+1);const unsigned bytes=wcmd_chars*2,pages=(bytes+4095U)&~4095U;
     bool bad{};try{runtime.memory().map({wcmd_copy},pages,Permissions::read|Permissions::write);runtime.memory().write({wcmd_copy},std::span<const std::byte>(reinterpret_cast<const std::byte*>(w),bytes));runtime.memory().protect({wcmd_copy},Permissions::read);}catch(...){bad=true;}if(bad)deny("Checked guest wide command-line copy",wcmd_copy);
     wcmd_guest=wcmd_copy;}
    ++wcmd_calls;return done(wcmd_guest,0);}
  } else if(raw==alloc_raw&&ret==0x78001385){
   if(load(e+4)!=token||load(e+8)!=0||load(e+12)!=rounded||result)deny("Exact source HeapAlloc(_crtheap,0,rounded) frame required",raw);
   result=publish(rounded,0);return done(result,3);}
  deny("Unadmitted heap-stage import remains unresolved",raw);}
 void*jumped(State*s,unsigned target,void*p){guard(p);
  if(kind==Kind::initterm){const unsigned pc=state.gpr.rip.dword;
   if(target==game_initterm_raw){state.gpr.rip.dword=0x780014f8;return mw34_attach_initterm_body(s,0x780014f8,p);}
   if(target==game_new_raw){state.gpr.rip.dword=0x5f401ea0;return mw34_attach_m_new_body(s,0x5f401ea0,p);}
   if(target==game_delete_raw&&complex_root()){state.gpr.rip.dword=0x5f401782;return mw34_attach_m_delete_body(s,0x5f401782,p);}
   deny("Unadmitted game import thunk JMP",target);(void)pc;}
  if(kind!=Kind::resume||target>=0x78000000)deny("Heap-stage indirect JMP outside an import tail call",target);
  const unsigned ret=load(state.gpr.rsp.dword);void*r=api(s,target,p);if(depth&&returns[depth-1]==ret)--depth;else deny("Import tail call must return to the active caller",target);return r;}
 // Flag-producing instructions with an undefined AF (TEST/AND/IMUL); none of these
 // bodies has an AF consumer.
 unsigned char undefined(){if(owner!=this||!active)deny("Heap-stage undefined flag outside Stage");++undefined_count;return 0;}
 void run(){if(owner)deny("Exactly one heap Stage");owner=this;active=true;
  try{if(kind==Kind::initterm)(void)mw34_attach_g_thunk_initterm_body(&state,0x5ac598,token_ptr);else if(kind==Kind::attach)(void)mw34_attach_attach_body(&state,attach_entry,token_ptr);else if(kind==Kind::resume)(void)mw34_attach_attachb1_body(&state,resume_entry,token_ptr);else (void)mw34_allocation_malloc_body(&state,malloc_entry,token_ptr);}catch(...){active=false;owner=nullptr;throw;}
  active=false;owner=nullptr;if(kind==Kind::resume&&attach_returned)complete=true;if(!complete)deny(kind==Kind::call?"malloc body ended without its admitted RET":"_CRTDLL_INIT body ended without reaching its declared frontier");}
};
}
