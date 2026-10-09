"""New admitted-PE/C1 unit variants; unchanged lifted numeric IR and frozen ancestors."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
out=Path(sys.argv[1]).resolve();mode=sys.argv[2];assert mode in ('baseline','repair') and out.parent==BASE and not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
ancestor=ROOT/'reports/m4-fp-numeric-max-host-boundary/derivation-r4';seal=ROOT/'reports/m4-fp-numeric-max-host-boundary/author-review-r1'
assert sha(seal/'report.json')=='efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a'
files=json.loads((seal/'pins.json').read_text())['files'];pins={str(seal/'report.json'):sha(seal/'report.json'),str(seal/'pins.json'):sha(seal/'pins.json')}
for name in ('session.hpp','native.cpp'):
 p=ancestor/name;assert sha(p)==files[str(p)];q=out/(name+'.ancestor');q.write_bytes(p.read_bytes());pins[str(p)]=sha(p);pins[str(q)]=sha(q)
s=(ancestor/'session.hpp').read_text()
a='(sticky!=0&&sticky!=2&&sticky!=34)';b='(sticky!=0&&sticky!=2&&sticky!=32&&sticky!=34&&sticky!=512&&sticky!=514&&sticky!=544&&sticky!=546)';assert s.count(a)==1;s=s.replace(a,b)
if mode=='repair':
 a='s_.x87.fxsave.ftw.flat|=1<<top;';assert s.count(a)==1;s=s.replace(a,a+'s_.sw.c1=0; /* FLD has no stack overflow in this admitted domain. */')
(out/'session.hpp').write_text(s);pins[str(out/'session.hpp')]=sha(out/'session.hpp')
report={'passed':True,'mode':mode,'changes':['Only guest incoming sticky0/DE/PE/DEPE and C1=0/1 admission in new scope']+(['Typed FLD tag-commit clears shadow C1 after the actual strict promotion in the admitted no-overflow domain'] if mode=='repair' else ['C1 semantics unchanged: measured baseline failure is required before repair credit']),
 'unchanged':'Exact compiled guest IR, provider/IAT ownership, all other numeric/State/route/event/context checks and required outer numerical invoke API',
 'domain':'Authored coherent fixed live depth0/1/7,TOP0/7,twelve maskedCWs,16 source f32 words,sticky0/2/32/34,C1=0/1; no incoming IE or other condition flags',
 'source_defined':'FLD C1 zero absent overflow. FSTP final C1 without new precision exception observed only; no incoming PE rounding-direction credit',
 'original_executed':False,'whole_M4_complete':False,'files':pins}
(out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');gate=sha(out/'preparation.json');pins[str(out/'preparation.json')]=gate
n=(ancestor/'native.cpp').read_text()
a='old::seed(t.cw,t.top,t.depth,t.sticky,fx.data(),env.data());';assert n.count(a)==1
n=n.replace(a,'old::seed(t.cw,t.top,t.depth,0,fx.data(),env.data());const auto carry_sw=static_cast<std::uint16_t>((t.top<<11)|t.sticky);std::memcpy(fx.data()+2,&carry_sw,2);')
start=n.index('static void original_before(');end=n.index('static unsigned fault_mode',start);n=n[:start]+n[end:]
n=n[:n.index('int main(int argc,char**argv)')]
n+='''
#pragma pack(push,1)
struct CarryRecord{Record core;unsigned incoming_c1,incoming_sticky;};
#pragma pack(pop)
static_assert(sizeof(CarryRecord)==46688);
static void incoming(Fixture&f,unsigned c1){f.s.sw.c1=static_cast<std::uint8_t>(c1);const auto v=ni::view(f.s);std::memcpy(f.r.fx().data(),v.fx.data(),512);}
static CarryRecord emit(Fixture&f,old::Tag t,unsigned sequence,unsigned phase){const auto sw=ni::status(f.s);return {execute(f,t,sequence,phase),(sw>>9)&1,sw&0x3f};}
int main(int argc,char**argv){try{
 need(argc==5,"Authored carry native game provider object fresh-directory");auto game=old::read(argv[1],2384384),provider=old::read(argv[2],565760),object=old::read(argv[3],16*1024*1024);const auto dir=std::filesystem::path(argv[4]);need(!std::filesystem::exists(dir)&&std::filesystem::create_directory(dir),"Fresh carry output required");schema(dir);
 ni::Proof proof{old::sha256(object),"GATE_SHA"};controls(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),proof,(dir/"compiled-controls.json").string().c_str());
 auto header=[](unsigned count){old::Header h{};std::memcpy(h.magic,"MW4NMCI1",8);h.version=1;h.count=count;h.stride=sizeof(CarryRecord);h.pages=4;return h;};
 {old::Output out((dir/"carry.bin").string().c_str());out.write(header(18432));unsigned index=0;
 for(unsigned rep=0;rep<2;++rep)for(unsigned inp=0;inp<16;++inp)for(unsigned depth:{0U,1U,7U})for(unsigned sticky:{0U,2U,32U,34U})for(auto cw:old::control_words)for(unsigned top:{0U,7U})for(unsigned c1:{0U,1U}){old::Tag t{rep,inp,ni::root,cw,top,depth,sticky,0,0,0};Fixture f(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),proof,t,ni::DataFixture{old::inputs[inp]});incoming(f,c1);out.write(emit(f,t,index++,0));}need(index==18432,"Exact new carry corpus schedule");out.commit();}
 {old::Output out((dir/"persistent.bin").string().c_str());out.write(header(2304));unsigned sequence=0,phases=0;
 for(unsigned rep=0;rep<2;++rep)for(unsigned depth:{0U,1U,7U})for(unsigned sticky:{0U,2U,32U,34U})for(auto cw:old::control_words)for(unsigned top:{0U,7U})for(unsigned c1:{0U,1U}){old::Tag t{rep,0,ni::root,cw,top,depth,sticky,0,0,0};Fixture f(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),proof,t);incoming(f,c1);for(unsigned phase=0;phase<2;++phase){if(phase){f.r.cpu().eip=0x410a80;f.r.cpu().esp=old::frame+4;f.s.gpr.rip.dword=ni::root;f.s.gpr.rsp.dword=old::frame;}out.write(emit(f,t,sequence,phase));++phases;}++sequence;}need(sequence==1152&&phases==2304,"Exact persistent carry schedule");out.commit();}
 std::cout<<"18432 authored new-domain calls / 2304 persistent phases; no original process executed\\n";return 0;
 }catch(const std::exception&e){ni::owner=nullptr;std::cerr<<e.what()<<'\\n';return 1;}}
'''.replace('GATE_SHA',gate)
(out/'native.cpp').write_text(n);pins[str(out/'native.cpp')]=sha(out/'native.cpp');pins[str(Path(__file__))]=sha(__file__)
(out/'generator-source.py').write_bytes(Path(__file__).read_bytes());pins[str(out/'generator-source.py')]=sha(out/'generator-source.py')
(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
print(json.dumps({'preparation_sha256':gate,'pins_sha256':sha(out/'pins.json')}))
