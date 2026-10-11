"""Read-only review of frozen container owner guards and authored controls."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-container-control-audit'/name;need(not out.exists(),'Fresh source review');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen input '+str(p));pins[str(p)]=v;return p
 native=R/'reports/m4-container-native/preparation-r2';build=R/'reports/m4-container-controls/build-r3'
 need(json.loads(pin(native/'report.json','4d1eb214d383b99a857e927e90768e3de4f87429f1c4def90c49067340e02164').read_bytes())['passed'],'Final native derivative')
 need(json.loads(pin(build/'build.json','f0b73a3f4b66a0505cc584eac6042f9416c4773596f6972937684912bc58276d').read_bytes())['passed'],'Final actual control build')
 ops=pin(native/'container_operations.inc').read_text();binding=pin(native/'locale_batch_binding.inc').read_text();source=pin(native/'locale_batch_operations.inc').read_text();header=pin(native/'locale_batch.hpp').read_text();session=pin(native/'session_impl.inc').read_text();fixture=pin(build/'fixture.cpp').read_text();hook=pin(build/'hooks.hpp').read_text();asm=pin(build/'capture.s').read_text();pages=pin(build/'current_pages.hpp').read_text()
 stable=binding[binding.index('void Binding::stable_hook('):binding.index('void Binding::record(')]
 fields=('container_nulls_','container_borrowed_','container_imports_','container_stores_','container_probe_','container_null_active_','container_borrowed_active_')
 for field in fields:need(stable.count(field)>=2,'Generic observer snapshots and compares actual private field '+field)
 need(stable.index('hook(point)')<stable.index('Container observer changed private'),'Private immutability comparison follows actual observer')
 need('static_assert(sizeof(ContainerRecord)==256' in ops and 'std::as_bytes(std::span(container_nulls_))'in ops and 'std::as_bytes(std::span(container_borrowed_))'in ops,'Actual complete32Q records exposed rather than copied aggregate witnesses')
 for field in ('container_null_active_','container_borrowed_active_'):need('std::span(&'+field+',1)'in ops,'Actual4B active scalar is exposed '+field)
 body=source[source.index('void Binding::write('):source.index('void Binding::write(')+1800]
 need(body.index('container_write_before')<body.index('runtime.memory().write')<body.index('expected_store')<body.index('source_access')<body.index('container_write_after'),'Observers surround real source store, committed mirror and literal ledger in exact order')
 need('Normal empty-container fields carry only literal zero input and committed owned endpoint stores'in ops and 'value!=wanted'in ops and 'a->generation!=record->words[18]'in ops,'Exact empty input, requested endpoint and current native generation admitted')
 need('native_apis_.size()!=w[23]||live_allocations()!=w[25]||generation_!=w[10]||fs_expected_!=w[19]'in ops and 'w[29]=result'in ops and 'w[30]=result'in ops,'Void zero free conserves actual API/owner/generation/chain and retains literal source EAX')
 need('frame!=w[5]-8' in ops and 'runtime.memory().load<unsigned>({frame+4})'in ops and 'w[13]=runtime.memory().load<unsigned>({frame})'in ops,'Genuine free NULL cdecl source argument and return frames checked')
 need('value!=container_borrowed_loaded' in ops and 'result!=w[7]'in ops and 'address!=w[7]||value!=w[15]'in ops,'Borrowed scalar provenance, exact ECX publication and constructor object return checked')
 need('5f4ce000'not in ops.lower()and '5f4ce000'not in header.lower(),'Producer does not map or dereference the borrowed pointee page')
 wrapper=fixture[fixture.index('[[clang::noinline]] unsigned invoke('):fixture.index('struct NativeBackingSink')]
 need(wrapper.index('ErrorBoundary errors')<wrapper.index('NumericHostBoundary boundary')<wrapper.index('try{')<wrapper.index('catch(...)')<wrapper.index('return t.okay'),'Authored caller numerical/error scopes enclose source invocation and catch')
 need('Naked throwing Session replay' in fixture and 'if(t.retry)t.c->registry().replay(container_roots[0])'in wrapper,'Excluded naked-throw metadata behavior and actual same Session retry remain explicit')
 need('0x5f4ce000' in wrapper and 'MemoryFaultReason::unmapped'in wrapper,'Ordinary control measures the genuine absent borrowed pointee mapping')
 need('c.runtime().memory().read({address},b)'in fixture and 'reinterpret_cast<const void*>(row[8]),row[3]'in fixture,'Entire current admitted pages and actual complete private native extents measured directly')
 need('protect({0x5e0000},mw34::Permissions::read)'in hook and 'protect({0x5bb000},mw34::Permissions::read|mw34::Permissions::write)'in hook and 'protect({0x5bb000},mw34::Permissions::read)'in hook,'RO controls use exact existing region starts and IAT writes restore read permissions')
 need('reinterpret_cast<unsigned char*>(trigger_mfc[17])[trigger_mfc[19]-1]^=0x55'in hook and 'trigger_native_after.resize(trigger_mfc[19])'in hook,'Actual final native byte mutation and entire before/after evidence retained')
 need('words[word]^=1'in hook and 'bytes.size()==4'in hook and 'words[0]^=1'in hook,'Real record/import/probe/active backing is deliberately mutated')
 need('boundary_equal=hardware_equal(before,after);restore.restore()'in fixture and 'hardware_equal(cleanup_before,cleanup_after)'in fixture,'Strict actual hardware comparisons precede restoration and cover cleanup')
 need('fxsave64 (%rsi)'in asm and 'fxsave64 (%rdi)'in asm and 'fldenv 512(%r9)'in asm,'Exact assembly loads and captures full finite caller hardware input')
 inventory=tuple(int(x,16)for x in re.search(r'current_pages\{([^}]+)\}',pages)[1].split(','));need(len(inventory)==len(set(inventory))==59 and 0x5f4ce000 not in inventory and 0x7ffde000 not in inventory,'59 whole already-admitted pages, no expanded TIB/pointee ownership')
 pin(R/'tools/m4-container-control-audit/audit.py');pin(__file__);pin(R/'tools/m4-pipeline/manifests.py')
 copies=[]
 for path in list(pins):
  p=Path(path)
  if p.suffix in ('.py','.cpp','.hpp','.inc','.s'):
   dest=out/'sources'/p.parent.name/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());pin(dest,pins[path]);copies.append(dict(source=str(p),copy=str(dest),sha256=pins[path]))
 physical=verify_manifest(pins);need(physical['passed'],'Current actual source physical closure')
 report=dict(passed=True,scope='Read-only frozen producer and control-source review. New ordinary NULL frees retain literal CPU/frame/FS effects; borrowed source scalar never grants pointee ownership. Every private witness is guarded at all generic observer boundaries. Finite authored caller NumericHostBoundary includes actual source calls and C++ catch.',guarded_private_fields=len(fields),current_whole_page_inventory=len(inventory),control_scenarios_per_level=34,caller_boundary_includes_catch=True,naked_throw_metadata_preservation_claimed=False,pointee_mapping_admitted=False,API_response_injection=False,native_executed=False,initializer_credit=0,copied_sources=copies,files=pins,current_physical_closure=physical)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),copies=len(copies))))
if __name__=='__main__':main(*sys.argv[1:])
