"""Add contemporaneous physical GDI identity to the sorted58 component.

Only ordinary source files are read. No provider calls, workers or captures are
performed by this generator. The actual call still uses the already resolved
component-owned target and the existing assembly hardware observer.
"""
from pathlib import Path
import hashlib,json,shutil,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(t,a,b):need(t.count(a)==1,'One exact GDI observer hunk '+a[:80]);return t.replace(a,b)
def main(name):
 pp=R/'reports/m4-fps-native/connected-component-preparation-r1/report.json';out=pp.parent.parent/name;need(not out.exists(),'Fresh GDI component revision');out.mkdir();pins={};copies=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary inputs only');v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  pin(pp,'17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae');d=json.loads(pp.read_bytes());need(d['passed']and d['literal_bodies']==58,'Reviewed sorted58 input');review=pin(R/'reports/m4-tree-review/widget138-component-source-r2/report.json','a27c2c18d626389c14585545cc2553a51526008a08df5ebc63a3e86f3d289cba');need(json.loads(review.read_bytes())['passed'],'Independent sorted source gate')
  for p,h in d['files'].items():pin(p,h)
  for p in pp.parent.iterdir():
   if p.is_file()and p.name!='report.json':
    q=out/p.name;shutil.copyfile(pin(p),q);copies.append(dict(name=p.name,source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),initial_copy_sha256=sha(q)))
  helper=pin(R/'tools/m4-fps-native/gdi_provider_witness.hpp');shutil.copyfile(helper,out/helper.name)
  cpp=(out/'component.cpp').read_text();cpp=one(cpp,'#include <vector>','#include <vector>\n#include <fstream>\n#include "image_loader.hpp"')
  anchor='struct Component::Impl {';need(cpp.count(anchor)==1,'Exact Impl anchor');cpp=cpp.replace(anchor,'#include "gdi_provider_witness.hpp"\n\n'+anchor)
  cpp=one(cpp,'unsigned selected{},root_frame{},saved_return{}','unsigned provider_serial{},selected{},root_frame{},saved_return{}')
  cpp=one(cpp,'const auto error_before=GetLastError();mw34_widget_native_api(providers[index],args.data(),&rec.hardware);const auto error_after=GetLastError();unsigned result{};', 'const auto serial=provider_serial++;const auto error_before=GetLastError();provider_identity(serial,index,providers[index],"before");SetLastError(error_before);mw34_widget_native_api(providers[index],args.data(),&rec.hardware);const auto error_after=GetLastError();provider_identity(serial,index,providers[index],"after");SetLastError(error_after);const std::array<std::uint64_t,11>identity_call{1,serial,index,0,root->root,e.pc,f.frame,instance,reinterpret_cast<std::uintptr_t>(providers[index]),thread,rec.hardware.after.rax};dump("GDI-provider/"+std::to_string(serial)+"/call.bin",identity_call.data(),sizeof(identity_call));unsigned result{};')
  cpp=one(cpp,'ApiHardware hardware{};mw34_widget_native_api(providers[1],args.data(),&hardware);require(hardware.after.rax,', 'ApiHardware hardware{};const auto serial=provider_serial++;const auto error_before=GetLastError();provider_identity(serial,1,providers[1],"before");SetLastError(error_before);mw34_widget_native_api(providers[1],args.data(),&hardware);const auto actual_error=GetLastError();provider_identity(serial,1,providers[1],"after");SetLastError(actual_error);const std::array<std::uint64_t,11>identity_call{1,serial,1,1,it->root,0,0,it->instance,reinterpret_cast<std::uintptr_t>(providers[1]),thread,hardware.after.rax};dump("GDI-provider/"+std::to_string(serial)+"/call.bin",identity_call.data(),sizeof(identity_call));require(hardware.after.rax,')
  anchor=' void instruction(unsigned pc)';at=cpp.index(anchor);cpp=cpp[:at]+' void provider_identity(unsigned serial,unsigned kind,void*target,const char*side){observe_gdi_identity(serial,kind,target,side,[this](std::string_view name,const void*p,std::size_t n){dump(name,p,n);});}\n'+cpp[at:];(out/'component.cpp').write_text(cpp)
  for row in copies:row['current_sha256']=sha(row['target']);row['byte_identical']=row['current_sha256']==row['source_sha256'];need(row['byte_identical']or row['name']=='component.cpp','Only actual observer CPP changes')
  need((out/'component.hpp').read_bytes()==(pp.parent/'component.hpp').read_bytes(),'Whole public service/header identity');need((out/'contracts.json').read_bytes()==(pp.parent/'contracts.json').read_bytes(),'Whole normal source contracts identity');irs=[str((out/Path(p).name).resolve())for p in d['IRs']];need(len(irs)==58 and all(sha(p)==sha(pp.parent/Path(p).name)for p in irs),'All58 IRs unchanged')
  changes=[dict(name='component.cpp',relation='One new provider serial and read-only identity callback; contemporaneous before/after metadata surrounds the exact same source and manual API calls; LastError explicitly restored',before_sha256=sha(pp.parent/'component.cpp'),after_sha256=sha(out/'component.cpp')),dict(name=helper.name,relation='New exact owning-image/path/SHA/MBI/full entry64 observer; physical export and DIR64 validator remains separate',sha256=sha(out/helper.name))]
  d.update(IRs=irs,namespace_relations=[dict(x,component_IR=str((out/Path(x['component_IR']).name).resolve()),component_sha256=sha(out/Path(x['component_IR']).name))for x in d['namespace_relations']])
  for p in out.iterdir():
   if p.is_file():pin(p)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,scope='Unexecuted sorted58 component with exact real GDI source/manual target before/after owning-image observations; no source/numerical reseed or execution credit',parent_component_preparation=str(pp.resolve()),parent_component_preparation_sha256=sha(pp),prior_copy_relations=copies,changed_generated_files=changes if passed else [],files=pins,native_executed=False,initializer_credit=0,current_Context_fault_proof_pending=True,actual_GDI_owner_export_proof_pending=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
