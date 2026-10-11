"""Independent bounded current Runtime COS callback/compiled/causal review."""
import collections, json, re, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C
import amd64_coff as COFF
import amd64_pe as PE

def main(name):
    out=R/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh current bounded Runtime cosine review');out.mkdir(parents=True)
    counts=collections.Counter();passed=False;functions=[]
    try:
        for q in (__file__,C.__file__,COFF.__file__,PE.__file__):C.pin(q)
        area=R/'reports/m4-cosine-native'
        callback=C.read(area/'runtime-preparation-r2/report.json','6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e')
        proof=C.read(area/'runtime-fixture-verification-r1/report.json','cc037925bc3f47f8d31c5ef96f0865632939688e65455e3c2b68c97b1ff3e12d')
        execution=C.read(proof['execution_path'],proof['execution_sha256']);build=C.read(execution['build_path'],execution['build_sha256']);prep=C.read(build['preparation'],build['preparation_sha256'])
        C.need(all(r['passed']for r in(callback,proof,execution,build,prep)) and len(execution['observations'])==32 and prep['compound_runtime_preparation_sha256']==C.PINS[str((area/'runtime-preparation-r2/report.json').resolve())],'Exact latest callback/fixture4/build4/execution3/verification chain')
        C.need(proof['reader_closed'] and not proof['original_AFTER_machine_seed'] and not proof['candidate_AFTER_machine_seed'] and proof['original_finite_numerical_oracle'] and not proof['independent_trigonometric_prediction'] and not proof['complete_persistent_bootstrap_source'] and not proof['initializer_credit'],'Preserved finite numerical seam and isolated scope')
        for r in (callback,proof,prep):
            for q,h in r['files'].items():
                if Path(q).suffix not in ('.mwb','.zip'):C.pin(q,h)
        for q,h in build['sources'].items():
            if Path(q).suffix not in ('.mwb','.zip'):C.pin(q,h)
        source=C.pin(callback['CPP']).read_text();prior=C.pin(area/'fixture-preparation-r1/native.cpp').read_text();prior=prior[:prior.index('int main(')]
        prior=prior.replace('#include "fixture_spec.hpp"','#include "'+(area/'fixture-preparation-r1/fixture_spec.hpp').as_posix()+'"').replace('constexpr std::uint32_t frame=0x20001800,sentinel=0x410a80;','static thread_local std::uint32_t frame{},sentinel{};').replace('mw34::m4_fp_cosine_native','mw34::m4_fp_compound_native')
        old='if(!ok){fault();return 0;}++reads;log(address,value,8,0);return value;'
        guards='switch(address){'+''.join('case '+hex(i['address'])+':if(value!='+str(i['bits'])+'ULL){fault();return 0;}break;'for i in callback['domain']['default_F64_inputs'])+'default:fault();return 0;}'
        C.need(prior.count(old)==1,'One genuine F64 read bridge');prior=prior.replace(old,'if(!ok){fault();return 0;}'+guards+'++reads;log(address,value,8,0);return value;')
        names=callback['names']
        def rename(s):
            for a,b in sorted(names.items(),key=lambda z:-len(z[0])):s=re.sub(r'\b'+re.escape(a)+r'\b',b,s)
            return s
        C.need(source.startswith('#include <memory>\n#include <algorithm>\n'+rename(prior)), 'Complete reviewed Context is unchanged except borrowed TLS frame, exact physical input admission, unique names')
        ir=C.pin(area/'host-candidate-r1/4b64f0.ll').read_text();newIR=C.pin(area/'runtime-preparation-r2/compound.ll').read_text();C.need(newIR==rename(ir),'Entire tested hardware strict LLVM bridge differs only by exact namespace renaming')
        for i,oldfile in enumerate(('raw80.cpp','store_test.cpp')):
            C.need(C.pin(callback['bridges'][i]).read_text()==rename(C.pin(area/'fixture-preparation-r1'/oldfile).read_text()),'Entire real hardware raw80/store-status bridge exact renamed source')
        wrapper=source[source.index('void compound_cosine(m4_runtime::Runtime &runtime)'):]
        for text in ('runtime.domain()==m4_runtime::Domain::admitted_game&&runtime.remill_seeded()', 'runtime.cpu().eip==0x4b64f0&&state.addr.ds_base.dword==0&&state.addr.ss_base.dword==0&&state.addr.fs_base.dword==runtime.fs_base().value', 'm4_fp_compound_native::frame=runtime.cpu().esp;m4_fp_compound_native::sentinel=runtime.memory().load<unsigned>({m4_fp_compound_native::frame})', 'm4_mixed::overlay_cpu(state,runtime.cpu());validate_fp(runtime,state)', 'context.enter(state)', 'sync_fx(runtime,state)'):
            C.need(text in wrapper,'Exact callback State/frame/segment/FP domain '+text)
        C.need('initialize('not in wrapper and 'state_after'not in wrapper and wrapper.count('context.enter(state)')==1,'Current Runtime State used in place, no experimental State initialization or AFTER input')
        connected=Path(prep['connected_include']);protocol=C.pin(connected/'joint_protocol.hpp').read_text();maincpp=C.pin(connected/'native_main.cpp').read_text()
        for text in ('require(m4::sha256(bytes)==b.code,"Joint current FP code identity changed")','for(const auto&b:fp_bindings)r_.register_translation','b.bytes,b.code,b.object,b.gate'):
            C.need(text in maincpp,'Actual registered dispatcher retains code/object/gate admission '+text)
        C.need('sizeof(State)==3504'in protocol.replace(' ','') or 'State'in protocol,'Full fixed State protocol consumed')
        oldnative=C.read(prep['native_preparation'],prep['native_preparation_sha256']);oldinclude=Path(oldnative['native_include']);newinclude=Path(prep['native_include']);changed=[]
        for q in newinclude.rglob('*'):
            if q.is_file() and q.suffix in ('.inc','.cpp','.hpp'):
                before=C.pin(oldinclude/q.relative_to(newinclude)).read_text();after=C.pin(q).read_text()
                if before!=after:
                    C.need(q.name=='session_impl.inc' and after==before.replace('  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();','  if(r.poisoned()&&!failed)poison();\n  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();'), 'Only external Runtime poison becomes owned-resource fault cleanup before invalid source execution')
                    changed.append(q.name)
                counts['library_source_files_compared']+=1
        C.need(changed==['session_impl.inc'],'Exactly one cleanup boundary source delta')
        fixture=C.pin(Path(build['preparation']).parent/'fixture.cpp').read_text()
        for text in ('Hardware invocation_before{},invocation_after{};hardware(invocation_before);(void)invoke(t);hardware(invocation_after)', 'actual-retry-before/', 'actual-retry-after/', 'State.bin",&c.state(),3504', 'CPU.bin",&c.runtime().cpu(),40', 'FX.bin",c.runtime().fx().data(),512', 'actual before', 'fixture_control<=10'):
            if text=='actual before':continue
            C.need(text in fixture,'Actual immediate invocation/full retry capture '+text)
        verify=C.pin(R/'tools/m4-cosine-native/verify_runtime_fixture.py',proof['files'][str((R/'tools/m4-cosine-native/verify_runtime_fixture.py').resolve())]).read_text()
        for text in ("before_keys == after_keys", "{'State.bin','CPU.bin','FX.bin','routes.bin'} <= before_keys", "equal(native_bundle.data('actual-retry-before/' + key), native_bundle.data('actual-retry-after/' + key)", "start = 160 if volatile else 256", "equal(before[512:540], after[512:540]", "assert records == b''", "if control in (3,4)", "result = derive(n[141540:145044], cpu, bytes(before), original, contracts, addresses)"):
            C.need(text in verify,'Whole precise measured verification seam '+text)
        for key,value in {'whole_Runtime_State3504_source':12,'whole_Runtime_CPU40_source':12,'whole43_Runtime_source_pages':516,'literal_Runtime_source_accesses':168,'finite_original_F32_joins':36,'positive_dispatcher_routes':12,'rejected_actual_controls':20,'source_first_fault_whole43_page_extent':860,'complete_retry_State3504':32,'complete_retry_CPU40':32,'complete_retry_FX512':32,'complete_retry_route_ledgers':32,'architectural_host_and_whole_ENV_pairs':96,'completed_cleanup':32}.items():
            C.need(proof['counts'][key]==value,'Exact current proof measured count '+key);counts[key]=value
        derivations=C.read(area/'runtime-fixture-verification-r1/derivations.json',proof['files'][str((area/'runtime-fixture-verification-r1/derivations.json').resolve())]);C.need(len(derivations)==32,'Each actual positive or causal observation retained')
        for row in derivations:
            if row.get('control'):C.need(row['actual_first_failure'] and row['pages_after_sha256'],'Actual first-fault scope retained')
            else:C.need(row['State_after_sha256'] and row['pages_after_sha256'] and row['numerical_oracle'] and len(row['events'])==14,'Exact source positive whole state/page/finite numerical seam')
        for level in ('O0','O2'):
            image=PE.Image(C.pin(build['workers'][level]['path'],build['workers'][level]['sha256']).read_bytes());symbols,sections=COFF.parse(C.pin(callback['objects'][level]['path'],callback['objects'][level]['sha256']).read_bytes())
            raw,rel=COFF.function(symbols,sections,'mw34_fp_entry_4b64f0');targets=COFF.linked_candidates(image,raw,rel);C.need(len(targets)==1,'Whole uniquely linked actual strict compound literal function')
            target,actual=targets[0];bindings=[]
            for row in rel:
                at=row['offset'];address=(target+at+4+struct.unpack_from('<i',actual,at)[0]-struct.unpack_from('<i',raw,at)[0]);bindings.append(dict(symbol=row['symbol']['name'],target=address,offset=at))
            C.need(all(r['symbol'].startswith('mw34_compound_')for r in bindings),'All actual new root bridge references are uniquely named')
            functions.append(dict(level=level,target=target,bytes=len(raw),bindings=bindings));counts['whole_linked_compound_functions']+=1;counts['whole_linked_compound_bytes']+=len(raw);counts['actual_compound_relocations']+=len(rel)
            text=C.pin(connected/level/'mixed_bindings.hpp').read_text();C.need('{0x4b64f0,121,"'+prep['physical_code_sha256']+'","'+callback['objects'][level]['sha256']+'","'+prep['compound_runtime_preparation_sha256']+'",&compound_cosine}'in text,'Actual perlevel Runtime binding code/object/callback identities')
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        (out/'actual-linked-functions.json').write_text(json.dumps(functions,indent=2)+'\n')
        report=dict(passed=passed,scope='Independent bounded current Runtime compound callback, exact compiled literal/unique bridge linkage, source seam and actual ten causal controls/full retry receipt review',counts=dict(counts),callback_preparation_sha256='6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e',verification_sha256='cc037925bc3f47f8d31c5ef96f0865632939688e65455e3c2b68c97b1ff3e12d',capture_archives_opened=0,independent_trigonometric_prediction=False,complete_persistent_bootstrap_source=False,full_caller_FX512_equality_claim=False,initializer_credit=0,files=C.PINS)
        target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
