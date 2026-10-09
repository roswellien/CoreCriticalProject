"""New numerical-host-boundary derivative; frozen r5 remains literal."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'tools/m4-fp-numeric-max-integration'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'reports/m4-fp-numeric-max-host-boundary' and not out.exists();out.mkdir(parents=True)
report=ROOT/'reports/m4-fp-numeric-max-integration/author-review-r1/report.json';pins=ROOT/'reports/m4-fp-numeric-max-integration/author-review-r1/pins.json';assert sha(report)=='e17867b6a788e02522cb65fbe1abab9a8dbea24e08e418bee72614b5b8ef31c3'
frozen=json.loads(pins.read_text())['files'];files={};changes=[]
for name in ('session.hpp','native.cpp'):
 p=OLD/name;assert sha(p)==frozen[str(p)];(out/(name+'.ancestor')).write_bytes(p.read_bytes());files[str(p)]=sha(p);files[str(out/(name+'.ancestor'))]=sha(out/(name+'.ancestor'))
header=(OLD/'session.hpp').read_text()
guard='''// This scope owns numerical host FP state; guest State remains software-owned.
struct NumericHostBoundary {
 struct alignas(16) Fx {std::array<std::byte,512>b{};};Fx fx{};std::array<std::byte,28>env{};
 explicit NumericHostBoundary(std::uint16_t cw){const unsigned mx=0x1f80;__asm__ volatile("fxsave64 %0\\n\\tfnstenv %1\\n\\tfninit\\n\\tfldcw %2\\n\\tldmxcsr %3":"=m"(fx),"=m"(env):"m"(cw),"m"(mx):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)");}
 ~NumericHostBoundary(){__asm__ volatile("fxrstor64 %0\\n\\tfldenv %1"::"m"(fx),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 NumericHostBoundary(const NumericHostBoundary&)=delete;NumericHostBoundary&operator=(const NumericHostBoundary&)=delete;
};
'''
assert header.count('class Session;')==1;header=header.replace('class Session;',guard+'class Session;')
needle=' [[noreturn]]void deny';assert header.count(needle)==1
invoke=''' // The explicit outer numerical boundary catches internal C++ exceptions before
 // restoration. Failure is a status return: no subsequent external unwind can
 // replace the caller's separately retained legacy ENV with an FX-only image.
 bool invoke(GuestAddress target,GuestAddress return_pc,bool acquire_borrow=true)noexcept{
  NumericHostBoundary host_boundary(static_cast<std::uint16_t>(s_.x87.fxsave.cwd.flat));bool ok=false;
  try{if(acquire_borrow){Borrow borrow(*this);r_.call_direct(target,return_pc);}else r_.call_direct(target,return_pc);ok=true;}catch(...){ok=false;}
  return ok;
 }
'''
header=header.replace(needle,invoke+needle)
target=out/'session.hpp';target.write_text(header);files[str(target)]=sha(target);changes.append({'production':'Session-owned outer invoke API catches internal C++ exceptions and returns bool after numerical FX/legacy/CW/MXCSR restoration. Bypassing this API has no preservation claim. Guest IR/domain/State/events/r9 unchanged.'})
native=(OLD/'native.cpp').read_text();start=native.index('struct Host {');end=native.index('\nstatic void seed',start)
host='''struct Host {
 struct alignas(16) Image{std::array<std::byte,512>b{};};Image before{},after{},cleanup{};std::array<std::byte,28>env{},env_after{},cleanup_env{};
 explicit Host(std::uint16_t cw){std::array<unsigned char,512>seed{};std::array<unsigned char,28>seed_env{};old::seed(cw,7,2,0,seed.data(),seed_env.data());const unsigned sw=0xffff3a20;const std::uint16_t short_sw=0x3a20;std::memcpy(seed.data()+2,&short_sw,2);std::memcpy(seed_env.data()+4,&sw,4);struct alignas(16) Aligned{std::array<unsigned char,512>b;};Aligned aligned{seed};
  __asm__ volatile("fxsave64 %[cleanup]\\n\\tfnstenv %[cleanup_env]\\n\\tfxrstor64 %[seed]\\n\\tfldenv %[seed_env]\\n\\tfxsave64 %[before]\\n\\tfnstenv %[env]\\n\\tfldenv %[env]":[cleanup]"=m"(cleanup),[cleanup_env]"=m"(cleanup_env),[before]"=m"(before),[env]"=m"(env):[seed]"m"(aligned),[seed_env]"m"(seed_env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void restore(){__asm__ volatile("fxrstor64 %0\\n\\tfldenv %1"::"m"(cleanup),"m"(cleanup_env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void capture(){__asm__ volatile("fxsave64 %0\\n\\tfnstenv %1\\n\\tfldenv %1":"=m"(after),"=m"(env_after)::"memory");bool equal=std::memcmp(before.b.data(),after.b.data(),5)==0&&std::memcmp(before.b.data()+24,after.b.data()+24,4)==0&&env==env_after;for(unsigned i=0;i<8;++i)equal=equal&&std::memcmp(before.b.data()+32+i*16,after.b.data()+32+i*16,10)==0;if(!equal){auto dump=[](const auto&v){std::ostringstream text;text<<std::hex;for(auto b:v){const unsigned n=std::to_integer<unsigned>(b);text<<\"0123456789abcdef\"[n>>4]<<\"0123456789abcdef\"[n&15];}return text.str();};std::cerr<<\"DIRECT_HOST_BEFORE_FX=\"<<dump(before.b)<<'\\n'<<\"DIRECT_HOST_AFTER_FX=\"<<dump(after.b)<<'\\n'<<\"DIRECT_HOST_BEFORE_ENV=\"<<dump(env)<<'\\n'<<\"DIRECT_HOST_AFTER_ENV=\"<<dump(env_after)<<'\\n';}need(equal,"Session-owned numerical host restoration measured before harness cleanup");}
 ~Host(){restore();}
};'''
native=native[:start]+host+native[end:]
replacements=[
('{ni::Session::Borrow borrow(c);f.r.call_direct({ni::root},{0x410a80});}host.capture();','need(c.invoke({ni::root},{0x410a80}),"Complete Session-owned bounded invocation");host.capture();'),
('try{if(borrow){ni::Session::Borrow b(c);f.r.call_direct({target},{ret});}else f.r.call_direct({target},{ret});}catch(const std::exception&){denied=true;}host.capture();','denied=!c.invoke({target},{ret},borrow);host.capture();'),
('try{ni::Session::Borrow b(c);f.r.call_direct({ni::root},{0x410a80});}catch(const std::exception&){stop=true;}retry.capture();','stop=!c.invoke({ni::root},{0x410a80});retry.capture();')]
for a,b in replacements:assert native.count(a)==1,(a,native.count(a));native=native.replace(a,b)
target=out/'native.cpp';target.write_text(native);files[str(target)]=sha(target);changes.append({'observer':'Two occupied host values, PE+C1 and caller CW seeded; direct numerical after capture BEFORE any cleanup; volatile SIMD retained raw but ABI-unspecified; all positive and actual fault/retry execution uses the new owned invocation API'})
correction={'supersedes_host_claim_only':str(report),'frozen_r5_host_evidence':'Explicit harness cleanup/self-restore; no Session restoration. Native State/numeric/memory/event/carry results remain literal.','actual_finding':'Independent direct success/FSTP-write fault captures show numerical host sticky flags and legacy metadata clobbered.','independent_report':'reports/m4-fp-numeric-max-integration/independent-direct-host-r1/report.json','independent_report_sha256':'49a5d97801d3f6827a9d46e87b1f25e107961f9208ac905a3cf42417d649abaa','new_derivative':'New owned numerical-host scope; unchanged r9/guest IR/input domain','original_executed':False}
(out/'correction.json').write_text(json.dumps(correction,indent=2)+'\n');files[str(out/'correction.json')]=sha(out/'correction.json');files[str(report)]=sha(report);files[str(pins)]=sha(pins);files[str(Path(__file__))]=sha(__file__)
(out/'derivation.json').write_text(json.dumps({'passed':True,'changes':changes,'files':files},indent=2)+'\n');print(json.dumps({'derivation_sha256':sha(out/'derivation.json'),'correction_sha256':sha(out/'correction.json')}))
