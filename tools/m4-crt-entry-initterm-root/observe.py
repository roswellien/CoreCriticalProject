"""BEFORE-only complete sixteen-page comparison of actual null _initterm."""
import copy,json,struct,sys,traceback,types
from pathlib import Path
sys.dont_write_bytecode=True
import model as M
D,F,R,N=M.D,M.F,M.R,M.N;ROOT=M.ROOT;pin=M.pin;sha=M.sha
_own=sys.modules['model'];sys.modules['model']=M.M
try:OLD=M.module('frozen_control_observer',ROOT/'tools/m4-crt-entry-control-root/observe.py','aaee1da9ef938d9d8bb176bb2b26944c02fcdf8f881447fe568b5f5d11056e60')
finally:sys.modules['model']=_own

def base_memory(payload,provider_pages,game_page,source_pages):
    memory=OLD.base_memory(payload,provider_pages,game_page,source_pages)
    for a in (M.THUNK,*M.NEW_PAGES):memory[a]=bytearray(source_pages[a])
    return memory
def stage(state,fx,runtime_cpu,memory):
    files=OLD.stage(state,fx,runtime_cpu,memory)
    files['initterm-thunk.bin']=bytes(memory[M.THUNK]);files['initterm-provider.bin']=bytes(memory[0x78001000][0x4f8:0x514])
    for a in M.NEW_PAGES:files[f'page-{a}.bin']=bytes(memory[a])
    return files
writer_result=types.FunctionType(OLD.writer_result.__code__,dict(OLD.__dict__,stage=stage,base_memory=base_memory))

def expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,source,control=0,level='O0'):
    final,fx,memory,phases=writer_result(row,payload,wp,pp,gp,source)
    entry=M.Entry(program,providers,maths,ctrl,init,final,memory,fx,control,level)
    before=copy.deepcopy(memory)
    mutation={37:(0x78001000,0x4f8,0),38:(M.THUNK,0,0),39:(0x5bb000,0x510,0x1ded12^1),40:(0x5e0000,0x248,0x51e7b0)}.get(control)
    if mutation:
        a,o,value=mutation;F.put(before[a],o,value)
    outer=bytearray(D.cpu(final));F.put(outer,16,D.FRAME+4);F.put(outer,36,0xfffffff0)
    phases['entry-before-invoke']=stage(final,fx,outer,before)
    entry.run()
    phases['entry-projected']=stage(entry.projected[0],fx,entry.projected[1],entry.projected[2])
    for tag,value in (('matherr-before',entry.math_before),('matherr-projected',entry.math_projected),('matherr-after',entry.math_after)):
        if value is not None:phases[tag]=stage(value[0],fx,value[1],value[2])
    for tag,value in (('control-before',entry.control_before),('control-projected',entry.control_projected),('control-provider-before',entry.provider_before),('control-provider-projected',entry.provider_projected),('control-provider-after',entry.provider_after),('control-after',entry.control_after)):
        if value is not None:phases[tag]=stage(value[0],value[3],value[1],value[2])
    for tag,value in entry.init_phases.items():phases[tag]=stage(value[0],value[3],value[1],value[2])
    phases['entry-after-fault']=stage(entry.state,entry.fx,entry.runtime_cpu,entry.mem);phases['retry-after']=phases['entry-after-fault']
    return entry,phases

def evidence(entry):
    values=OLD.evidence(entry)
    events=b''.join(struct.pack('<4I',*v) for v in entry.init_events)
    accesses=b''.join(struct.pack('<5I',*v) for v in entry.init_accesses)
    values['initterm-events.bin']=events+bytes(256-len(events));values['initterm-accesses.bin']=accesses+bytes(640-len(accesses))
    values['initterm-job.bin']=struct.pack('<16I',*entry.init_job)
    values['initterm-undefined.bin']=b''.join(struct.pack('<I',pc) for pc in entry.init_undefined)
    return values
def compare(row,entry,phases,control=0):
    OLD.OLD.check_stages(row,phases)
    for name,value in evidence(entry).items():
        actual=pin(row/name).read_bytes();OLD.OLD.evidence_equal(json.loads(actual) if name.endswith('.json') else actual,value,str(row)+' '+name)
    result=json.loads(pin(row/'result.json').read_text())
    fault=(1,0x5ac468,0x5bb514) if not control else ((4,M.THUNK,M.THUNK) if control in (37,38,39,47) else (4,M.SLOT,M.THUNK))
    assert (result['fault_reason'],result['fault_site'],result['fault_target'])==fault
    assert result['passed'] and result['control']==control and result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
    assert result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1
    assert pin(row/'initterm-reason.txt').read_text().strip()==entry.init_reason
    assert pin(row/'control-reason.txt').read_text().strip()==entry.control_reason
    for name in ('writer','entry'):D.host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
def unused_init(row):
    assert not any((row/tag).exists() for tag in ('initterm-thunk-before','initterm-thunk-projected','initterm-thunk-after','initterm-before','initterm-projected','initterm-after'))
    assert pin(row/'initterm-events.bin').read_bytes()==bytes(256)
    assert pin(row/'initterm-accesses.bin').read_bytes()==bytes(640)
    assert pin(row/'initterm-job.bin').read_bytes()==struct.pack('<16I',M.SLOT,0x1ded12,*([0]*14))
    assert pin(row/'initterm-undefined.bin').read_bytes()==b'' and pin(row/'initterm-reason.txt').read_text().strip()==''
def corruptions(phases,values,level,control):
    rows=OLD.corruptions(phases,values,level,control)
    for tag,files in phases.items():
        for name in ('initterm-thunk.bin','initterm-provider.bin',*(f'page-{a}.bin' for a in M.NEW_PAGES)):
            for offset in (0,len(files[name])-1):
                altered=dict(files);b=bytearray(altered[name]);b[offset]^=1;altered[name]=bytes(b)
                try:D.equal(altered,files,'Corrupted added initializer observation')
                except AssertionError:rows.append(dict(level=level,control=control,phase=tag,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Added corrupted checkpoint accepted')
    return rows

def main(build,capture,out):
    assert out.parent==ROOT/'reports/m4-crt-entry-initterm' and not out.exists();out.mkdir()
    try:
        b=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in b[group].items():pin(p,h)
        program,providers,maths,ctrl,init,source,commands=M.source_material(out);wp,pp,gp=R.source_material()
        original=R.originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        payloads=[R.project(v) for v in original[:24]];positives=[];causals=[];denials=[]
        old_causal=types.FunctionType(D.causal.__code__,dict(D.__dict__,stage=stage,base_memory=base_memory))
        math_expected=types.FunctionType(OLD.OLD.expected.__code__,dict(OLD.OLD.__dict__,stage=stage,base_memory=base_memory))
        control_expected=types.FunctionType(OLD.expected.__code__,dict(OLD.__dict__,stage=stage,base_memory=base_memory,writer_result=writer_result))
        for level in ('O0','O2'):
            root=capture/f'native-{level}';assert pin(root/'COMPLETE').read_bytes()==b'COMPLETE'
            for i,payload in enumerate(payloads):
                row=root/f'row-{i}';entry,phases=expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,source)
                compare(row,entry,phases)
                positives.append(dict(level=level,id=i,game_events=len(entry.events),initterm_accesses=len(entry.init_accesses),initterm_routes=len(entry.init_events),initterm_source_PCs=entry.init_PCs,whole_State=3504,whole_FX=512,whole_pages=16))
                if i==0:denials.extend(corruptions(phases,evidence(entry),level,0))
            for control in range(1,49):
                row=root/f'row-{control+23}'
                if control<=12:
                    value=old_causal(row,payloads[0],wp,pp,gp,program,providers,source,control)
                    if control>=4:OLD.unused_control(row);unused_init(row)
                elif control<=24:
                    entry,phases=math_expected(row,payloads[0],wp,pp,gp,program,providers,maths,source,control)
                    OLD.OLD.check_stages(row,phases);fault=OLD.OLD.check_evidence(row,entry,control);OLD.unused_control(row);unused_init(row)
                    value=dict(control=control,whole_source_prefix_predicted=True,first_fault=fault,terminal_retry=True)
                elif control<=36:
                    entry,phases=control_expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,source,control)
                    OLD.compare(row,entry,phases,control);unused_init(row)
                    value=dict(control=control,whole_source_prefix_predicted=True,terminal_retry=True)
                else:
                    entry,phases=expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,init,source,control,level)
                    compare(row,entry,phases,control)
                    value=dict(control=control,whole_source_prefix_predicted=True,initterm_job=entry.init_job,initterm_source_PCs=entry.init_PCs,terminal_retry=True,artifact_specific_injected_operand=control==43,architectural_source_equivalence_credited=control!=43)
                    denials.extend(corruptions(phases,evidence(entry),level,control))
                value['level']=level;causals.append(value)
        for m in (M.M,M.M.M,D,R,N,D.E,F,M.C):M.PINS.update(m.PINS)
        pin(__file__);pin(M.__file__);pin(sys.executable)
        result=dict(passed=True,scope='BEFORE-only whole-State actual first null _initterm composition and stopped causal prefixes; mode43 follows separately reviewed per-artifact observer-injection operands',positive_records=48,causal_records=96,positives=positives,causals=causals,positive_writer_events=4656,positive_game_events=sum(v['game_events'] for v in positives),initterm_accesses=sum(v['initterm_accesses'] for v in positives),initterm_route_events=sum(v['initterm_routes'] for v in positives),whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=16,source_identity_bytes=934,direct_host_boundary_pairs=282,observer_corruption_denials=denials,source_commands=commands,author_model_imported=False,mode43_generalized_source_equivalence=False,selected_initializer_count=27,callbacks_executed=False,full_CRT=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        for p in out.iterdir():
            if p.is_file():pin(p)
        for p,h in list(M.PINS.items()):assert sha(p)==h,p
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(M.PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,positives=48,causals=96,accesses=result['initterm_accesses'],denials=len(denials),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
