"""Prepare additive initialized FDIV -> real CRT data consumer, without execution."""
import argparse,hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-entry-prefix'
PREFIX=ROOT/'reports/m4-crt-entry/prefix-preparation-r3/prefix.cpp'
SEED=ROOT/'tools/m4-crt-fdiv-replay/replay.cpp'
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def save(p,v):
 with pathlib.Path(p).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def replace(s,a,b):need(s.count(a)==1,'One exact ancestor site: '+a[:80]);return s.replace(a,b)
def main(out):
 out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private composition preparation');files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact frozen dependency '+str(p));need(str(p)not in files or files[str(p)]==v,'Nonconflicting binding');files[str(p)]=v
 bind(PREFIX,'afe9c0404c711d1efdc0c574174df281c7beb9aa296550b1e8ef7e658b2c13dc');bind(SEED,'02dfca02aa9cc59df4f65b44190ea51249acb6d1b2faf75b06d5b7fa3cca8a0b')
 for p,h in [(ROOT/'reports/m4-crt-fdiv-replay/author-review-r1/report.json','98cbad107c29a8e88f087fca9a1bb9f41cb0867c72720a3c174fa4448632ca68'),(ROOT/'reports/m4-crt-entry/native-preparation-r1/report.json','4c1174a4a68e6d6ea00c75bb053a4f16f68767d841132be9d6defeaecd5c7ed3')]:bind(p,h)
 for p in (ROOT/'reports/m4-crt-fdiv-replay/author-review-r1/pins.json',ROOT/'reports/m4-crt-entry/native-preparation-r1/pins.json'):
  for f,h in json.loads(p.read_text(encoding='utf-8-sig'))['files'].items():bind(f,h)
  bind(p)
 s=PREFIX.read_text();s=s[:s.index('int main(int argc,char**argv)')]
 s=replace(s,'#include "crt_services.hpp"','#include "crt_services.hpp"\n#include "seed.hpp"')
 s=replace(s,'std::vector<Event>events_;bool running_{};unsigned data_iat_{};','std::vector<Event>events_;bool running_{};unsigned data_iat_{};fd::Registry&fdiv_;\npublic:struct DataRoute{unsigned pc,slot,raw,guest_address,value;};\nprivate:std::vector<DataRoute>data_routes_;')
 s=replace(s,'Context(Runtime&r,const std::string&native_sha):r_(r),s_(*std::construct_at(reinterpret_cast<State*>(r.remill_state().data()))){','Context(Runtime&r,fd::Registry&fdiv,const std::string&native_sha):r_(r),s_(*reinterpret_cast<State*>(r.remill_state().data())),fdiv_(fdiv){')
 begin=s.index('  for(unsigned i=0;i<3504;++i)');end=s.index('  r.register_translation',begin)
 s=s[:begin]+'''  require(r.remill_seeded()&&fdiv_.ready(),"Existing completed writer and persistent State required; no entry reseed");
  require(s_.addr.ds_base.dword==0&&s_.addr.ss_base.dword==0&&s_.addr.fs_base.dword==r.fs_base().value,"Carried flat DS/SS and owned guest FS required");
''' +s[end:]
 s=replace(s,'project(s_,r_.cpu());running_=true;', '''auto pending=r_.cpu();auto carried=cpu(s_);carried.esp=pending.esp;carried.eip=pending.eip;require(std::memcmp(&carried,&pending,sizeof(Cpu32))==0,"Only declared outer ESP/EIP transition permitted");s_.gpr.rsp.dword=pending.esp;s_.gpr.rip.dword=pending.eip;running_=true;''')
 old='if(a==0x5bb508){require(s_.gpr.rip.dword==0x5ac408&&v==data_iat_,"Actual unpublished FDIV data import read");throw Fault(FaultReason::unresolved_import,{s_.gpr.rip.dword},{a},"Required initialized FDIV data import is not connected in this prefix");}return v;'
 new='''if(a==0x5bb508){require(s_.gpr.rip.dword==0x5ac408&&v==data_iat_,"Exact raw FDIV data import read");auto resolved=fdiv_.resolve_data({a});require(resolved&&resolved->value==fd::global&&fdiv_.ready(),"Only actual initialized owned FDIV data may resolve");auto value=r_.memory().load<unsigned>(*resolved);require(fdiv_.lookups().size()==3&&value==fdiv_.lookups()[2].raw_result,"Source-written data bound to actual query receipt");data_routes_.push_back({s_.gpr.rip.dword,a,v,resolved->value,value});return resolved->value;}if(a==fd::global){require(s_.gpr.rip.dword==0x5ac40d&&data_routes_.size()==1&&v==data_routes_[0].value&&fdiv_.ready(),"Actual dependent load of initialized FDIV data");}return v;'''
 s=replace(s,old,new)
 s=replace(s,' const auto&events()const{return events_;}State&state(){return s_;}', ''' void*direct(State*s,unsigned target){guard();require(s==&s_&&target==0x5ac5c0&&!events_.empty(),"Exact next required source helper");const auto&w=events_.back();require(w.pc==0x5ac415&&w.write==1&&w.width==4&&w.address==s_.gpr.rsp.dword&&w.value==0x5ac41a&&r_.memory().load<unsigned>({w.address})==w.value,"True source direct CALL frame/return word");r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=w.pc;r_.call_direct({target},{w.value});throw std::runtime_error("Unreviewed helper unexpectedly returned");}
 const auto&events()const{return events_;}const auto&data_routes()const{return data_routes_;}State&state(){return s_;}''')
 s=replace(s,'extern "C" void*mw34_crte_direct(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required direct-call bridge");}','extern "C" void*mw34_crte_direct(State*s,unsigned a,void*p) noexcept(false) {return static_cast<Context*>(p)->direct(s,a);}')
 s += '\n#include "composition_main.inc"\n'
 helper=SEED.read_text();helper=helper[:helper.index('int main(int argc,char**argv)')]
 need('State s;auto*p='in helper and 'std::memcpy(r.remill_state().data(),&s,3504)'in helper,'Exact reviewed seed helper excerpt')
 out.mkdir(parents=True)
 for source,name in ((PREFIX,'prefix-ancestor.cpp'),(SEED,'seed-ancestor.cpp')):shutil.copyfile(source,out/name);bind(out/name,files[str(source)])
 (out/'composition.cpp').write_text(s);(out/'seed.hpp').write_text(helper)
 for p in (out/'composition.cpp',out/'seed.hpp',pathlib.Path(__file__).resolve(),ROOT/'tools/m4-crt-fdiv-entry-prefix/composition_main.inc',ROOT/'tools/m4-crt-fdiv-entry-prefix/CMakeLists.txt'):bind(p)
 save(out/'report.json',{'passed':True,'scope':'Additive source preparation only: actual completed FDIV writer into translated CRT data consumer then missing helper','native_executed':False,'original_executed':False,
  'ancestor_prefix_sha256':sha(PREFIX),'ancestor_seed_sha256':sha(SEED),'composition_source_sha256':sha(out/'composition.cpp'),'literal_seed_excerpt_sha256':sha(out/'seed.hpp'),
  'state_policy':'One initial reviewed BEFORE seed, then borrowed complete3504 State/softwareFX/pages; Context has no construct_at/memset/full seed. Explicit outer Runtime ESP1904/EIPexternal transition, source invoke writes return at1900, Context projects only ESP/EIP at entry.',
  'data_policy':'Raw game IAT1DED32 retained; Registry.resolve_data after actual writer produces guest78037C2C, source MOV5AC40D reads it, source MOV5AC40F writes game9A17E4. Record raw read and separate typed data receipt.',
  'next_fault':'After actual source CALL5AC415 pushes5AC41A, r9 same-word frame route to untranslated5AC5C0 rejects; no helper or matherr success substitute',
  'whole_CRT_or_M4_complete':False});bind(out/'report.json');save(out/'pins.json',{'files':files})
 print(json.dumps({'passed':True,'bindings':len(files),'composition_source_sha256':sha(out/'composition.cpp'),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
