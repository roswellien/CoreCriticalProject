#pragma once
// Connects the already-lifted staged MSVCRT ordinary command-line parser
// (0x7800BC48, reports/m4-crt-mainargs/recovery-r3 normal_parser object) at the
// builder's CALL 0x7800BBF7 (counting pass: argv/args NULL) and, after the real
// malloc, its CALL 0x7800BC2D (filling pass). Both read only the owned command line
// and the multibyte class table, use their own frame and update the count words;
// the filling pass may also store exactly argv[0..numargs) and args[0..numchars)
// inside the returned block. Every other access and any other RET is refused.
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <thread>
namespace mw34::m4_crt_parser_carry {
namespace mg=m4_crt_entry_mainargs;
inline constexpr unsigned parser=0x7800bc48,site=0x7800bbf7,ret=0x7800bbfc;
// test byte ptr [reg+0x780379E1],4 indexes the provider _mbctype class bytes by
// an unsigned command-line byte; this is the only table operand in the body.
inline constexpr unsigned table=0x780379e1,table_bytes=256;
inline constexpr unsigned malloc_site=0x7800bc06,malloc_target=0x780012b3,malloc_ret=0x7800bc0b,fill_site=0x7800bc2d,fill_ret=0x7800bc32;
extern "C" void*mw34_mainargs_normal_parser_body(State*,unsigned,void*) noexcept(false);
struct Stage;
inline thread_local Stage*owner{};
struct Stage {
 mg::Context&context;
 unsigned entry_esp{},cmdline{},cmdline_bytes{},numargs_ptr{},numchars_ptr{},return_pc=ret,argv{},args{},argv_words{},args_bytes{},byte_writes{};
 unsigned saved_ebx{},saved_esi{},saved_edi{},saved_ebp{},undefined_count{},byte_reads{},word_reads{},word_writes{};
 bool active{},returned{};std::thread::id thread=std::this_thread::get_id();
 // Filling pass: argv/args are the block returned by the real malloc and the counts
 // come from the counting pass the builder just carried into its request.
 Stage(mg::Context&c,unsigned esp,unsigned line,unsigned line_bytes,unsigned block,unsigned words,unsigned bytes):context(c),entry_esp(esp),cmdline(line),cmdline_bytes(line_bytes),return_pc(fill_ret),argv(block),args(block+4U*words),argv_words(words),args_bytes(bytes){
  auto&m=c.runtime.memory();
  if(!block||!words||m.load<unsigned>({esp})!=fill_ret||m.load<unsigned>({esp+4})!=line||m.load<unsigned>({esp+8})!=argv||m.load<unsigned>({esp+12})!=args)c.deny("Parser filling-pass frame required",esp,fill_site);
  numargs_ptr=m.load<unsigned>({esp+16});numchars_ptr=m.load<unsigned>({esp+20});
  if(!c.stack(numargs_ptr)||!c.stack(numchars_ptr)||numargs_ptr==numchars_ptr)c.deny("Parser count words must be distinct guest stack words",esp,fill_site);
  saved_ebx=c.state.gpr.rbx.dword;saved_esi=c.state.gpr.rsi.dword;saved_edi=c.state.gpr.rdi.dword;saved_ebp=c.state.gpr.rbp.dword;
 }
 Stage(mg::Context&c,unsigned esp,unsigned line,unsigned line_bytes):context(c),entry_esp(esp),cmdline(line),cmdline_bytes(line_bytes){
  auto&m=c.runtime.memory();
  // Arguments: [esp]=return,[+4]=cmdline,[+8]=argv,[+12]=args,[+16]=&numargs,[+20]=&numchars.
  if(m.load<unsigned>({esp})!=ret||m.load<unsigned>({esp+4})!=line||m.load<unsigned>({esp+8})||m.load<unsigned>({esp+12}))c.deny("Parser counting-pass frame required",esp,site);
  numargs_ptr=m.load<unsigned>({esp+16});numchars_ptr=m.load<unsigned>({esp+20});
  if(!c.stack(numargs_ptr)||!c.stack(numchars_ptr)||numargs_ptr==numchars_ptr)c.deny("Parser count words must be distinct guest stack words",esp,site);
  saved_ebx=c.state.gpr.rbx.dword;saved_esi=c.state.gpr.rsi.dword;saved_edi=c.state.gpr.rdi.dword;saved_ebp=c.state.gpr.rbp.dword;
 }
 void guard()const{if(owner!=this||!active||returned||mg::owner!=&context||thread!=std::this_thread::get_id())context.deny("Exact current active parser owner required",context.state.gpr.rip.dword);}
 bool frame(unsigned a)const{return a%4==0&&a>=entry_esp-16&&std::uint64_t(a)+4<=std::uint64_t(entry_esp)+24;}
 unsigned char read8(unsigned a,void*p){guard();if(p!=&context)context.deny("Exact parser byte-read token",a);
  // AND BYTE PTR [ESI],0 / [ESI-1],0 are read-modify-write: the filling pass reads its own args bytes.
  const bool line=a>=cmdline&&a<cmdline+cmdline_bytes,klass=a>=table&&a<table+table_bytes,own=args&&a>=args&&std::uint64_t(a)<std::uint64_t(args)+args_bytes;
  if(!line&&!klass&&!own)context.deny("Parser byte read outside owned command line, class table or filling-pass args",a);
  unsigned char v{};bool bad{};try{v=context.runtime.memory().load<unsigned char>({a});}catch(...){bad=true;}if(bad)context.deny("Checked parser byte read fault",a);++byte_reads;return v;}
 unsigned read32(unsigned a,void*p){guard();if(p!=&context)context.deny("Exact parser read token",a);
  // AND DWORD PTR [EDI],0 (the terminating argv NULL) is read-modify-write on the vector.
  const bool vector=argv&&a%4==0&&a>=argv&&std::uint64_t(a)+4<=std::uint64_t(argv)+4U*argv_words;
  if(!frame(a)&&!vector&&a!=numargs_ptr&&a!=numchars_ptr)context.deny("Parser DWORD read outside own frame/count words/filling-pass argv",a);
  unsigned v{};bool bad{};try{v=context.runtime.memory().load<unsigned>({a});}catch(...){bad=true;}if(bad)context.deny("Checked parser read fault",a);++word_reads;return v;}
 void write32(unsigned a,unsigned v,void*p){guard();if(p!=&context)context.deny("Exact parser write token",a);
  // Own pushes, the two argument slots the source reuses ([ebp+8], [ebp+18h]),
  // and the count words. The argv slot [ebp+0Ch] is written only when argv!=0.
  const bool push=a%4==0&&a>=entry_esp-16&&a<entry_esp,slot=a==entry_esp+4||a==entry_esp+20||(argv&&a==entry_esp+8);
  const bool vector=argv&&a%4==0&&a>=argv&&std::uint64_t(a)+4<=std::uint64_t(argv)+4U*argv_words;
  if(!push&&!slot&&!vector&&a!=numargs_ptr&&a!=numchars_ptr)context.deny("Parser DWORD store outside its pass contract",a);
  bool bad{};try{context.runtime.memory().store<unsigned>({a},v);}catch(...){bad=true;}if(bad)context.deny("Checked parser store fault",a);++word_writes;}
 void write8(unsigned a,unsigned char v,void*p){guard();if(p!=&context)context.deny("Exact parser byte-write token",a);
  if(!args||a<args||std::uint64_t(a)+1>std::uint64_t(args)+args_bytes)context.deny("Parser byte store outside the filling-pass args buffer",a);
  bool bad{};try{context.runtime.memory().store<unsigned char>({a},v);}catch(...){bad=true;}if(bad)context.deny("Checked parser byte store fault",a);++byte_writes;}
 void returned_to(State*s,unsigned a,void*p){guard();if(p!=&context||s!=&context.state)context.deny("Exact parser return token",a);
  const auto&g=context.state.gpr;
  if(a!=return_pc||g.rip.dword!=return_pc||g.rsp.dword!=entry_esp+4||g.rbx.dword!=saved_ebx||g.rsi.dword!=saved_esi||g.rdi.dword!=saved_edi||g.rbp.dword!=saved_ebp)context.deny("Parser RET must return to its builder site with entry ESP+4 and restored nonvolatiles",a);
  returned=true;}
 // TEST/AND leave AF undefined; the body has no AF consumer (no LAHF/PUSHF/DAA/
 // DAS/AAA/AAS; branches use ZF only), so the representative is never observed.
 unsigned char undefined(){guard();++undefined_count;return 0;}
};
}
