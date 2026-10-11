"""Read-only finite control source/guard scope; actual effects checked separately."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-vtable-controls'/name;need(not out.exists(),'Fresh static control review');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact static input');pins[str(p)]=v;return p
 build=R/'reports/m4-vtable-controls/build-r1';b=json.loads(pin(build/'build.json','ffb1d2ba01313fafe3628c9ef071d67117488fe0975f2a8ded0d5d2ef5acda36').read_bytes());need(b['passed'],'Frozen control build')
 n=R/'reports/m4-vtable-native/preparation-r4';pin(n/'report.json','b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93')
 fixture=pin(build/'fixture.cpp').read_text();hook=pin(build/'hooks.hpp').read_text();capture=pin(build/'capture.s').read_text();ops=pin(n/'vtable_operations.inc').read_text();binding=pin(n/'locale_batch_binding.inc').read_text();session=pin(n/'session_impl.inc').read_text()
 scope=fixture[fixture.index('[[clang::noinline]] unsigned invoke('):fixture.index('struct NativeBackingSink')];need(scope.index('ErrorBoundary errors')<scope.index('NumericHostBoundary boundary')<scope.index('try{')<scope.index('catch(...)')<scope.index('return t.okay'),'Caller boundary encloses source and actual exception catch')
 need('Naked throwing Session replay'in fixture and 'if(t.retry)t.c->registry().replay(vtable_roots[0])'in fixture,'Explicit bounded caller hardware guarantee; exact same Session retry')
 need('constexpr unsigned vtable_roots[]{0x40f0e0,0x4795f0,0x47f5f0,0x4b5220}'in fixture and 'header[]{1,27,54,sizeof(Sample),4,6}'in fixture,'Finite authored source-call/scenario extent')
 need('reinterpret_cast<const void*>(row[8]),row[3]'in fixture and 'current-page-addresses.bin'in fixture,'Complete full-width actual native owner and current admitted pages retained')
 need('fxrstor64 (%r9)'in capture and 'fldenv 512(%r9)'in capture and capture.index('fxsave64 (%rsi)')<capture.index('callq data_boundary_initialize')<capture.index('fxsave64 (%rdi)'),'Exact rich hardware sampled immediately around authored boundary')
 need('private_before.assign(b.begin(),b.end())'in hook and 'const_cast<std::byte*>(b.data())'in hook and 'private_after.assign(b.begin(),b.end())'in hook,'Actual private backing flips captured fully before and after')
 need('if(selected==16||selected==19)wanted_pc=0x40e820'in hook and 'if(selected==20)wanted_pc=0x59fbb1'in hook,'Target-entry and genuine return selectors use actual source State PC')
 body=binding[binding.index('void Binding::stable_hook'):binding.index('\n}',binding.index('void Binding::stable_hook'))]
 for name_ in('vtable_records_','vtable_stores_','vtable_read_probe_','vtable_vptr_','vtable_store_probe_','vtable_active_'):need(body.count(name_)>=2,'Every new private source witness snapshotted and compared')
 need('if(spec->site==0x59ff6e&&'in ops and 'spec->site==0x59ff6e?vtable_vptr_[5]:0'in ops,'Actual instance-read requirement confined to truevirtual source call')
 need('publication->pc!=spec->publication_pc'in ops and 'source_accesses_.rbegin()'in ops,'Fixed and virtual calls retain exact earlier source publication')
 need('Normal finite indirect constructor pointer argument must be zero before pointee dereference'in ops,'Nonzero helper pointer domain explicitly refused')
 need('checkpoint(runtime,("vtable-call-"'in ops and '-entered' in ops and '-returned'in ops,'Complete native source checkpoints at genuine CALL/RET boundaries')
 need('void Binding::vtable_hook(unsigned point){stable_hook(point);}'in ops,'New hooks use generic whole-State/FX/private witness guards')
 need('w[18]=state.gpr.rsp.dword' in ops and 'frame+4+w[17]'in ops and 'native_apis_.size()!=w[26]'in ops and 'fs_expected_!=w[24]'in ops,'Complete exact source RET cleanup/owner/API/chain admission')
 replay=session[session.index(' void replay('):session.index(' void probe_string(')];need(replay.index('check();')<replay.index('InvocationHostBoundary host'),'Early refusal scope stays outside naked callee hardware guarantee')
 pin(__file__);report=dict(passed=True,build=str(build/'build.json'),build_sha256=sha(build/'build.json'),guarded_private_fields=6,controls_scenarios=27,caller_boundary_includes_catch=True,naked_throw_metadata_preservation_claimed=False,nonzero_copy_domain_admitted=False,source_bound_indirect_cases=True,files=pins,physical_closure=verify_manifest(pins),initializer_credit=False,scope='Finite control source/guard/caller-wrapper admission only; whole actual causes and complete retained bytes are separate execution/check gates.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
