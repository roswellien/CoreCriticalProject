"""Independent whole58-retained source delta for contemporaneous GDI identity."""
from pathlib import Path
import collections,hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();files={};counts=collections.Counter();passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v,(p,h,v);files[str(p)]=v;return p
 def read(p,h):
  d=json.loads(pin(p,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
  return d
 try:
  old=R/'reports/m4-fps-native/connected-component-preparation-r1';new=R/'reports/m4-fps-native/connected-component-preparation-r4'
  read(R/'reports/m4-tree-review/widget138-component-source-r2/report.json','a27c2c18d626389c14585545cc2553a51526008a08df5ebc63a3e86f3d289cba')
  p=read(new/'report.json','c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21');b=read(R/'reports/m4-fps-native/connected-component-build-r4/build.json','d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119')
  assert b['preparation_sha256']=='c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21'
  for q in old.iterdir():
   if not q.is_file()or q.name in('report.json','component.cpp'):continue
   assert pin(q).read_bytes()==pin(new/q.name).read_bytes();counts['whole_unchanged_component_inputs']+=1
  current=pin(new/'component.cpp').read_text()
  def once(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
  reduced=once(current,'#define NOMINMAX\n','');reduced=once(reduced,'#include <fstream>\n#include "admission.hpp"\n','');reduced=once(reduced,'#include "gdi_provider_witness.hpp"\n\n','');reduced=once(reduced,'unsigned provider_serial{},selected{}','unsigned selected{}')
  reduced=once(reduced,' void provider_identity(unsigned serial,unsigned kind,void*target,const char*side){observe_gdi_identity(serial,kind,target,side,[this](std::string_view name,const void*p,std::size_t n){dump(name,p,n);});}\n','')
  new_call='const auto serial=provider_serial++;const auto error_before=GetLastError();provider_identity(serial,index,providers[index],"before");SetLastError(error_before);mw34_widget_native_api(providers[index],args.data(),&rec.hardware);const auto error_after=GetLastError();provider_identity(serial,index,providers[index],"after");SetLastError(error_after);const std::array<std::uint64_t,11>identity_call{1,serial,index,0,root->root,e.pc,f.frame,instance,reinterpret_cast<std::uintptr_t>(providers[index]),thread,rec.hardware.after.rax};dump("GDI-provider/"+std::to_string(serial)+"/call.bin",identity_call.data(),sizeof(identity_call));unsigned result{};'
  old_call='const auto error_before=GetLastError();mw34_widget_native_api(providers[index],args.data(),&rec.hardware);const auto error_after=GetLastError();unsigned result{};'
  reduced=once(reduced,new_call,old_call)
  new_cleanup='ApiHardware hardware{};const auto serial=provider_serial++;const auto error_before=GetLastError();provider_identity(serial,1,providers[1],"before");SetLastError(error_before);mw34_widget_native_api(providers[1],args.data(),&hardware);const auto actual_error=GetLastError();provider_identity(serial,1,providers[1],"after");SetLastError(actual_error);const std::array<std::uint64_t,11>identity_call{1,serial,1,1,it->root,0,0,it->instance,reinterpret_cast<std::uintptr_t>(providers[1]),thread,hardware.after.rax};dump("GDI-provider/"+std::to_string(serial)+"/call.bin",identity_call.data(),sizeof(identity_call));require(hardware.after.rax,'
  reduced=once(reduced,new_cleanup,'ApiHardware hardware{};mw34_widget_native_api(providers[1],args.data(),&hardware);require(hardware.after.rax,')
  assert reduced==pin(old/'component.cpp').read_text(),'Whole source delta consists only of exact declared read-only GDI observations and declarations'
  helper=pin(new/'gdi_provider_witness.hpp').read_text()
  for token in ['GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT','mbi.AllocationBase==owner&&mbi.Type==MEM_IMAGE&&mbi.State==MEM_COMMIT','address+64<=base+mbi.RegionSize','!(mbi.Protect&PAGE_GUARD)','file.read(reinterpret_cast<char*>(bytes.data()),n)','mw34::m4::sha256(bytes)','emit(prefix+"-entry64.bin",target,64)']:
   assert token in helper,token
  for token in ('State','Runtime','memory().write','SetLastError','GetProcAddress','CreateFontA','DeleteObject('):assert token not in helper,token
  assert p['literal_bodies']==58 and not p['native_executed']and p['initializer_credit']==0
  pin(__file__);pin(sys.executable)
  for q,h in files.items():pin(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d=dict(passed=passed,scope='Whole58 literal/contract inputs byte retained; exact read-only GDI provenance delta around same source/manual native targets, LastError restored immediately before actual calls; observations and physical-export validation remain separate',preparation_sha256='c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21',build_sha256='d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119',counts=dict(counts),initializer_credit=0,worker_launched=False,archive_reader_opened=False,files=files);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(files))))
if __name__=='__main__':main(sys.argv[1])
