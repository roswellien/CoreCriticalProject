"""Additive own fixture derivative; imports no author model or fixture."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'tools/m4-fp-numeric-max-boundary-independent'
OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
def main():
 assert not (OUT/'controls.cpp').exists(),'Fresh additive derivative only'
 s=(SRC/'controls.cpp').read_text()
 s=replace(s,'s.sw.de=(sticky>>1)&1;s.sw.pe=(sticky>>5)&1;','s.sw.de=(sticky>>1)&1;s.sw.pe=(sticky>>5)&1;s.sw.c1=(sticky>>9)&1;')
 s=replace(s,'State t;std::memcpy(&t,&s,3504);','State t;std::memcpy(&t,&s,3504);t.sw.c1=0; // Independently specified bounded nonoverflow FLD effect.')
 s=replace(s,'constexpr unsigned invalid_sw[]{1,4,8,16,32,64,128,0x100,0x200,0x400,0x4000,0x8000};','constexpr unsigned invalid_sw[]{1,4,8,16,64,128,0x100,0x400,0x4000,0x8000};')
 s=replace(s,'for(unsigned mode=0;mode<29;++mode)','for(unsigned mode=0;mode<27;++mode)')
 s=replace(s,'else if(mode<17)full_status(f.s,invalid_sw[mode-5]);else if(mode==17)f.s.x87.fxsave.swd.flat=2<<11;else if(mode==18)f.s.x87.fxsave.ftw.flat=0xff;else if(mode==19)f.s.x87.fxsave.ftw.flat=5;else if(mode==20)f.s.x87.fxsave.mxcsr.flat=0xffffffff;else if(mode==21)f.s.addr.ds_base.dword=1;else if(mode==22)f.s.addr.ss_base.dword=1;else if(mode==23)f.s.seg.cs.flat=0x2b;else if(mode==24)f.s.seg.ds.flat=0x23;else if(mode==25)f.s.seg.ss.flat=0x23;else if(mode==26){std::uint64_t v=0x8000000000000001ULL;std::memcpy(&f.s.st.elems[0].val,&v,8);}else if(mode==27)f.s.addr.fs_base.dword^=1;',
 'else if(mode<15)full_status(f.s,invalid_sw[mode-5]);else if(mode==15)f.s.x87.fxsave.swd.flat=2<<11;else if(mode==16)f.s.x87.fxsave.ftw.flat=0xff;else if(mode==17)f.s.x87.fxsave.ftw.flat=5;else if(mode==18)f.s.x87.fxsave.mxcsr.flat=0xffffffff;else if(mode==19)f.s.addr.ds_base.dword=1;else if(mode==20)f.s.addr.ss_base.dword=1;else if(mode==21)f.s.seg.cs.flat=0x2b;else if(mode==22)f.s.seg.ds.flat=0x23;else if(mode==23)f.s.seg.ss.flat=0x23;else if(mode==24){std::uint64_t v=0x8000000000000001ULL;std::memcpy(&f.s.st.elems[0].val,&v,8);}else if(mode==25)f.s.addr.fs_base.dword^=1;')
 s=replace(s,'if(mode==28)f.r.fx()[0]^=std::byte{1};','if(mode==26)f.r.fx()[0]^=std::byte{1};')
 start=s.index('void nonboolean(');end=s.index('\nint main(',start)
 s=s[:start]+'''void nonboolean(std::span<const std::byte>g,std::span<const std::byte>d,const ni::Proof&p){
 for(unsigned field=0;field<11;++field)for(unsigned value:{2U,17U,34U,255U})for(unsigned coherent:{0U,1U}){++scenarios;Fixture f(g,d,p);std::array<std::uint8_t*,11>fields{&f.s.sw.ie,&f.s.sw.de,&f.s.sw.ze,&f.s.sw.oe,&f.s.sw.ue,&f.s.sw.pe,&f.s.sw.sf,&f.s.sw.c0,&f.s.sw.c1,&f.s.sw.c2,&f.s.sw.c3};*fields[field]=static_cast<std::uint8_t>(value);if(coherent){const auto soft=fx(f.s);std::memcpy(f.r.fx().data(),soft.data(),512);}const auto memory=f.memory();const auto calls=f.r.calls().size();boundary(*f.session,9,false);check(f.r.poisoned()&&f.session->failed()&&f.session->step()==0&&!f.session->running()&&!f.session->complete()&&ni::owner==nullptr,"Each noncanonical raw shadow byte denied before any numerical body");check(std::string(f.session->fault().reason)=="Noncanonical FP shadow flag byte rejected","Canonical guard causally precedes projected status and FX coherence checks");check(f.memory()==memory&&f.r.calls().size()==calls+1&&!f.r.calls().back().completed,"Malformed shadow denial leaves all pages and only unfinished outer call");++faults;
 seed(f.s,1,0,0,0x37f,f.r.fs_base().value);const auto fixed=fx(f.s);std::memcpy(f.r.fx().data(),fixed.data(),512);f.r.cpu()=cpu(f.s);f.r.cpu().esp+=4;f.r.cpu().eip=ret;f.r.memory().store<unsigned>({frame},ret);poisoned(f);
 }}''' + s[end:]
 s=replace(s,'for(unsigned sticky:{0U,2U,34U})','for(unsigned sticky:{0U,2U,32U,34U,512U,514U,544U,546U})')
 # The old fixture's gate-label typo is replaced by the physically pinned private preparation report.
 import re
 matched=re.search(r'const ni::Proof proof\{m4::sha256\(object\),"([0-9a-f]{64})"\}',s)
 assert matched
 actual_gate=sha(ROOT/'reports/m4-fp-numeric-max-integration/preparation-r4/report.json')
 s=s[:matched.start(1)]+actual_gate+s[matched.end(1):]
 (OUT/'controls.cpp').write_text(s)
 for name in ('boundary.s','CMakeLists.txt'):(OUT/name).write_bytes((SRC/name).read_bytes())
 b=(SRC/'build.py').read_text();b=replace(b,"BASE=ROOT/'reports/m4-fp-numeric-max-host-boundary'","BASE=ROOT/'reports/m4-fp-numeric-max-carry'");b=replace(b,"OUT=BASE/'independent-compiled-r1'","OUT=BASE/'independent-compiled-canonical-r1'");b=replace(b,"SESSION=BASE/'derivation-r4'","SESSION=BASE/'native-preparation-canonical-r1'")
 a="report=pin(BASE/'author-review-r1/report.json','efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a');pin(BASE/'author-review-r1/pins.json','4abbd1d60ef7bba49ac434279f79090924700da169450f77119b8bba3897011e');build=pin(BASE/'native-build-r3/build.json','118a7579fb096d211b9ddfdc4ee3d19ba522ea95de6e0715c60f6469aadb90ad')"
 b=replace(b,a,"pin(SESSION/'preparation.json','1c12b4f8f04d4bc26f09d2a8b9dd9f1afadcdfe51f177360a25885f6e7fe3927');build=pin(BASE/'native-canonical-r1/build.json','e50947fcf8c043d8f167e35c0e803f6a82b85e81313f4bab0339c9a7f1b3aa5b')")
 b=replace(b,"pin(SESSION/'session.hpp');src=", "pin(SESSION/'session.hpp','22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1');src=")
 b=b.replace("BASE/'native-build-r3'", "BASE/'native-canonical-r1'")
 (OUT/'build.py').write_text(b)
 report=dict(own_parent_sources={str(p):sha(p) for p in SRC.iterdir() if p.is_file()},derivative_sources={str(OUT/n):sha(OUT/n) for n in ('controls.cpp','boundary.s','CMakeLists.txt','build.py')},scope='Own additive fixture: independent 8 canonical sticky statuses, all 11 raw bytes x2/17/34/255 x separate coherent/incoherent FX, actual outside-return assembly host measurements; old failed normative fixture untouched',changes=['C1 seed from logical status; bounded no-overflow FLD explicitly clears shadow C1 in own expected State','PE32/C1 statuses positive rather than old unsupported negatives','88 shadow-byte causal denials and corrected poisoned retries','Proof gate label corrected from own prior typo to exact private preparation report hash'],prior_gate_label=matched.group(1),current_gate_label=actual_gate,author_model_fixture_executor_imported=False)
 (OUT/'derivation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
