"""One authored external caller after each own bootstrap; prepare only."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
OP=R/'reports/m4-version-source/original-preparation-r6'
NP=R/'reports/m4-version-source/fixture-preparation-r3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def once(s,a,b):need(s.count(a)==1,'Exact common caller seam '+a[:100]);return s.replace(a,b,1)
def main(original_name,native_name,recipe_name):
 original=R/'reports/m4-version-source'/original_name;native=R/'reports/m4-version-source'/native_name;recipe=R/'reports/m4-version-source'/recipe_name
 need(not any(p.exists()for p in(original,native,recipe)),'Fresh matched caller preparations');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive payload read in caller preparation');v=sha(p);need(h is None or h==v,'Exact frozen caller/source input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 od=read(OP/'report.json','37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6');nd=read(NP/'report.json','ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee');need(od['passed']and nd['passed'],'Actual frozen original6 and native2 caller lineage')
 for d in(od,nd):
  for p,h in d['files'].items():pin(p,h)
 read(R/'reports/m4-version-source/original6-relation-correction-r1/report.json','298b8ba1c253a3bd82e514757112dc25199ebfe6d8962d69806421d1a09cbac7')
 caller=read(R/'reports/m4-version-source/comparison-preparation-r1/common-caller.json');ch=pin(T/'common_caller_v1.hpp');caller_sha=sha(ch);recipe.mkdir();shutil.copyfile(ch,recipe/'common_caller.hpp');shutil.copyfile(R/'reports/m4-version-source/comparison-preparation-r1/common-caller.json',recipe/'common-caller.json')
 caller['current_passing_native_or_original_changed']=False;caller['application_scope']='Exactly once after each own real loader/bootstrap BEFORE, before root4AF240, never between source bodies';caller['native_stack_return_word']='Recipe publishes the native terminal token at rootESP; Runtime::invoke independently commits the same own token';caller['native_ENV_provenance']='Legacy ENV fields projected once into persistent FXSAVE32 state, then observed from that actual State under empty-tag guard; complete raw State and FX retained'
 (recipe/'role-recipes.json').write_text(json.dumps(caller,indent=2)+'\n');pin(__file__)
 for p in recipe.iterdir():pin(p)
 recipe_report=dict(passed=True,scope='One complete independently authored common caller, consumed identically by isolated original/native pair; no provider/candidate outputs',caller_header=str(recipe/'common_caller.hpp'),caller_header_sha256=caller_sha,caller_JSON_sha256=sha(recipe/'common-caller.json'),CPU_bytes=40,FX_bytes=512,ENV_bytes=28,stack_bytes=4096,application_count_per_worker=1,source_after_seed=False,provider_or_heap_pages_seeded=False,source_reseed=False,native_ENV_role=caller['native_ENV_provenance'],files=dict(pins))
 (recipe/'report.json').write_text(json.dumps(recipe_report,indent=2)+'\n');pin(recipe/'report.json')
 originals={};natives={}
 for src,out,records in((OP,original,originals),(NP,native,natives)):
  out.mkdir()
  for p in src.iterdir():
   if p.is_file()and p.name not in('report.json','pins.json','failure.txt'):
    q=out/p.name;shutil.copyfile(p,q);records[q.name]=p
  shutil.copyfile(recipe/'common_caller.hpp',out/'common_caller.hpp')
 os=(original/'reference.cpp').read_text();os=once(os,'#include "version_provider_isolation.hpp"','#include "version_provider_isolation.hpp"\n#include "common_caller.hpp"')
 seam='''        // One external game-caller projection, preserving producerFX/pages/owners.
        mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};'''
 projection='''        // One independently authored external caller after the own real producer.
        namespace Common=mw34::m4_version_common;
        require(sequence==0&&entries.size()==1&&frame==Common::cpu[4]&&capture_pc==Common::original_return,"Exact one authored caller frame/terminal identity");
        out.append("common-caller/bootstrap-CPU.bin",&mixed_after,sizeof(mixed_after));out.append("common-caller/bootstrap-FX.bin",mixed_fx_after,512);out.append("common-caller/bootstrap-ENV.bin",mixed_env_after,28);
        std::vector<unsigned char>common_bootstrap_pages(memory_size);copy_pages(common_bootstrap_pages);out.append("common-caller/bootstrap-pages.bin",common_bootstrap_pages.data(),common_bootstrap_pages.size());
        const auto common_FX=Common::fx();std::memcpy(&mixed_input,Common::cpu.data(),sizeof(mixed_input));std::memcpy(mixed_guest_fx,common_FX.data(),common_FX.size());std::memcpy(mixed_guest_env,Common::env.data(),Common::env.size());mixed_env_ready=1;
        std::memcpy(reinterpret_cast<void*>(Common::stack_low),Common::stack.data(),Common::stack.size());std::memcpy(reinterpret_cast<void*>(Common::cpu[4]),&Common::original_return,4);
        const std::array<unsigned,8>common_application{1,1,0x4af240,Common::cpu[4],Common::original_return,512,28,4096};out.append("common-caller/application.bin",common_application.data(),sizeof(common_application));
        out.append("common-caller/authored-CPU.bin",Common::cpu.data(),40);out.append("common-caller/authored-FX.bin",common_FX.data(),512);out.append("common-caller/authored-ENV.bin",Common::env.data(),28);out.append("common-caller/authored-stack.bin",Common::stack.data(),4096);out.append("common-caller/header-sha.txt","@CALLERSHA@",64);'''.replace('@CALLERSHA@',caller_sha)
 os=once(os,seam,projection);os=once(os,'            if(phase){mixed_input=mixed_after;std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;}','            require(phase==0,"One root receives the single complete common external caller; no per-source reseed");');(original/'reference.cpp').write_text(os)
 oc=read(OP/'contracts.json');oc.update(common_caller_recipe_sha256=sha(recipe/'report.json'),common_caller_header_sha256=caller_sha,common_caller_applied_once_after_own_real_producer=True,whole_bootstrap_BEFORE_preserved=True,no_per_source_reseed=True);(original/'contracts.json').write_text(json.dumps(oc,indent=2)+'\n')
 ns=(native/'fixture.cpp').read_text();ns=once(ns,'#include "admission.hpp"','#include "admission.hpp"\n#include "common_caller.hpp"');code='''std::array<unsigned char,28>version_guest_environment(const State&s){namespace Common=mw34::m4_version_common;auto e=Common::env;version_need(!s.x87.fxsave.ftw.flat,"Actual version guest empty tags for exact legacy ENV correspondence");const auto&f=s.x87.fxsave;std::memcpy(e.data(),&f.cwd.flat,2);std::memcpy(e.data()+4,&f.swd.flat,2);std::memcpy(e.data()+12,&f.ip,4);std::memcpy(e.data()+16,&f.cs.flat,2);const unsigned short opcode=f.fop&0x7ff;std::memcpy(e.data()+18,&opcode,2);std::memcpy(e.data()+20,&f.dp,4);std::memcpy(e.data()+24,&f.ds.flat,2);return e;}
void version_common_caller(mw34::m4_runtime::Runtime&r,VersionWriter&w){namespace Common=mw34::m4_version_common;static unsigned applications{};version_need(!applications&&r.remill_seeded()&&!r.poisoned()&&r.memory().load<unsigned>({0x9a17f0})==UINT32_MAX,"One post-bootstrap independently authored external version caller");auto&s=*reinterpret_cast<State*>(r.remill_state().data());const auto f=Common::fx();std::memcpy(&r.cpu(),Common::cpu.data(),40);r.cpu().esp+=4;s.gpr.rax.dword=Common::cpu[0];s.gpr.rcx.dword=Common::cpu[1];s.gpr.rdx.dword=Common::cpu[2];s.gpr.rbx.dword=Common::cpu[3];s.gpr.rsp.dword=r.cpu().esp;s.gpr.rbp.dword=Common::cpu[5];s.gpr.rsi.dword=Common::cpu[6];s.gpr.rdi.dword=Common::cpu[7];s.gpr.rip.dword=Common::cpu[9];s.rflag.flat=Common::cpu[8];s.aflag.cf=0;s.aflag.pf=0;s.aflag.af=0;s.aflag.zf=0;s.aflag.sf=0;s.aflag.df=0;s.aflag.of=0;
 std::memcpy(&s.x87.fxsave,f.data(),512);std::memcpy(r.fx().data(),f.data(),512);const auto environment=version_guest_environment(s);version_need(environment==Common::env,"One recipe ENV projected into actual persistent guest FXSAVE fields");r.memory().write({Common::stack_low},std::as_bytes(std::span(Common::stack)));r.memory().store<unsigned>({Common::cpu[4]},Common::native_return);++applications;
 const std::array<unsigned,8>a{1,applications,0x4af240,Common::cpu[4],Common::native_return,512,28,4096};w.bytes("common-caller/application.bin",a.data(),sizeof(a));w.bytes("common-caller/authored-CPU.bin",Common::cpu.data(),40);w.bytes("common-caller/authored-FX.bin",f.data(),512);w.bytes("common-caller/authored-ENV.bin",Common::env.data(),28);w.bytes("common-caller/authored-stack.bin",Common::stack.data(),4096);w.bytes("common-caller/header-sha.txt","@CALLERSHA@",64);}
'''.replace('@CALLERSHA@',caller_sha)
 ns=once(ns,'void version_whole(',code+'void version_whole(');ns=once(ns,'w.bytes(std::string(stem)+"/FX.bin",r.fx().data(),512);','w.bytes(std::string(stem)+"/FX.bin",r.fx().data(),512);const auto environment=version_guest_environment(*reinterpret_cast<State*>(r.remill_state().data()));w.bytes(std::string(stem)+"/ENV-from-State.bin",environment.data(),environment.size());')
 ns=once(ns,'registry.bootstrap();registry.dump(&VersionWriter::sink,&writer);V::Component component','registry.bootstrap();registry.dump(&VersionWriter::sink,&writer);version_whole(r,writer,"common-caller/bootstrap");version_common_caller(r,writer);V::Component component');(native/'fixture.cpp').write_text(ns)
 def relations(out,parents):
  result=[]
  for p in out.iterdir():
   if p.is_file():
    pin(p);parent=parents.get(p.name);result.append(dict(child=str(p),sha256=sha(p),parent=str(parent)if parent else None,parent_sha256=sha(parent)if parent else None,unchanged=parent is not None and parent.read_bytes()==p.read_bytes()))
  return result
 origrelations=relations(original,originals);nativerelations=relations(native,natives)
 for label,out,parent,d,rel in(('original',original,OP,od,origrelations),('native',native,NP,nd,nativerelations)):
  result={k:v for k,v in d.items()if k not in('files','source_relations','parent_preparation_sha256','scope')};result.update(passed=True,scope='Matched '+label+' one-version-root caller projected exactly once after its own genuine bootstrap; complete raw endpoints and all existing source/API/ownership guards retained; prepare only',parent_preparation_sha256=sha(parent/'report.json'),common_caller_recipe=str(recipe/'report.json'),common_caller_recipe_sha256=sha(recipe/'report.json'),common_caller_header_sha256=caller_sha,source_relations=rel,complete_own_bootstrap_BEFORE_preserved=True,common_caller_application_count=1,source_after_seed=False,per_source_reseed=False,original_executed=False,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=dict(pins));q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(role=label,path=str(q),sha256=sha(q),executed=False)))
 print(json.dumps(dict(common_recipe=str(recipe/'report.json'),sha256=sha(recipe/'report.json'),caller_header_sha256=caller_sha)))
if __name__=='__main__':main(*sys.argv[1:])
