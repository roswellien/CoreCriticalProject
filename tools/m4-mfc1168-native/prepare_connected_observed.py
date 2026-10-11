"""Additive current-Context full caller and declared extra-memory observations.

Parent prep3/build1 remains immutable. This revision still has no writer
authorization and grants no whole131 source or initializer acceptance.
"""
from pathlib import Path
import hashlib,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(t,a,b):
 if t.count(a)!=1:raise ValueError('Exact one additive transition '+a[:100])
 return t.replace(a,b)
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};generated={};passed=False;parent={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(v.encode()if isinstance(v,str)else v);generated[str(p.resolve())]=sha(p)
 try:
  pp=pin(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r3/report.json','278be74db3998e7396ba46696a59f5e6fbd9acc43f71e0ca1eaedd272822ce4f');parent=json.loads(pp.read_bytes());assert parent['passed']
  for p,h in parent['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.suffix in('.cpp','.hpp','.inc','.json','.txt')and p.name not in('report.json',):write(out/p.relative_to(pp.parent),pin(p).read_bytes().replace(pp.parent.as_posix().encode(),out.as_posix().encode()))
  component=(out/'connected_component.cpp').read_text()
  # This private input snapshot is constructed from the admitted current input;
  # no caller-owned Inputs reference may change a live resource/source domain.
  component=one(component,'Runtime&r;const Inputs&input;State&s;','Runtime&r;const Inputs input;State&s;')
  needle='void checkpoint(std::string_view stem){std::string p(stem);'
  extra='''void checkpoint(std::string_view stem){std::string p(stem);
   std::vector<std::array<unsigned,3>>regions;
   auto observed=[&](unsigned address,unsigned size,unsigned permission){require(size&&size<=8192,"Complete bounded extra source region observation");std::vector<std::byte>b(size);r.memory().read({address},b);regions.push_back({address,size,permission});dump(p+"/memory/"+std::to_string(address)+".bin",b.data(),b.size());};
   for(const auto&row:input.new_mappings)observed(row.address,unsigned(row.before.size()),row.permissions);
   observed(0x78037000,4096,3);observed(r.fs_base().value,4,3);observed(r.fs_base().value+4,8,1);observed(r.fs_base().value+0x18,4,1);
   dump(p+"/memory/index.bin",regions.data(),regions.size()*sizeof(regions[0]));'''
  component=one(component,needle,extra);write(out/'connected_component.cpp',component)
  native=(out/'native_main.cpp').read_text();needle='struct DirectPhaseWriter {'
  helper='''struct MFCConnectedGuarded {mw34::m4_mixed::Context*context;unsigned sequence,repeat,top;std::vector<mw34::m4_mixed::Native>*records;bool completed;};
extern "C" void mfc_connected_invoke_guarded(MFCConnectedGuarded*p){p->completed=p->context->invoke_selected_table(p->sequence,p->repeat,p->top,*p->records);}
extern "C" void mfc_connected_hardware_call(MFCConnectedGuarded*,void*);
struct DirectPhaseWriter {'''
  native=one(native,needle,helper)
  old='const bool ok=context.invoke_selected_table(seq,repeat,top,records);'
  new='alignas(16)std::array<std::byte,1632>mfc_hardware{};MFCConnectedGuarded guarded{&context,seq,repeat,top,&records,false};mfc_connected_hardware_call(&guarded,mfc_hardware.data());const bool ok=guarded.completed;writer.append(prefix+"MFC-caller-hardware.bin",mfc_hardware.data(),mfc_hardware.size());'
  native=one(native,old,new);write(out/'native_main.cpp',native)
  assembly=pin(R/'reports/m4-mfc1168-native/resource-preparation-r3/hardware_boundary.s','28fc561ef10eb32d92a5fd3480d5aef78dced91736ba55c3a4c9a4a0b9f1dfa3')
  text=assembly.read_text().replace('mfc_hardware_call','mfc_connected_hardware_call').replace('mfc_invoke_guarded','mfc_connected_invoke_guarded');write(out/'connected_hardware_boundary.s',text)
  cm=(out/'CMakeLists.txt').read_text();cm=one(cm,'LANGUAGES CXX)','LANGUAGES CXX ASM)');cm=one(cm,'"${MW34_PREP}/connected_component.cpp"','"${MW34_PREP}/connected_component.cpp" "${MW34_PREP}/connected_hardware_boundary.s"');write(out/'CMakeLists.txt',cm)
  for p,h in generated.items():pin(p,h)
  pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(parent);report.update(passed=passed,scope='Additive current130 Context chronological14 fixture with full ASM hardware caller observation/restoration and whole declared new loader regions/CRT/minimalFS checkpoints; no execution',parent_fixture_preparation=str(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r3/report.json'),parent_fixture_preparation_sha256='278be74db3998e7396ba46696a59f5e6fbd9acc43f71e0ca1eaedd272822ce4f',generated_sources=generated,files=pins,changes=['Private immutable admitted Inputs snapshot','Complete eight new loader-region endpoints plus CRT4096 and three minimalFS regions per component checkpoint','Exact historical85B assembly wrapper around actual current14 Context invocation including MFC owned resource creation/source/release'],whole_caller_boundary='Assembly wraps actual current14 invoke_selected_table; Context construction/old registry cleanup outside; MFC TLS/CS construction and release inside',worker_executed=False,execution_admitted=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
