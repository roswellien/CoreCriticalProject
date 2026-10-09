"""Independent fourteen-page source comparison of the connected control path."""
import copy,json,struct,sys,traceback,types
from pathlib import Path
sys.dont_write_bytecode=True
import model as M
D,F,R,N=M.D,M.F,M.R,M.N
ROOT=M.ROOT;pin=M.pin;sha=M.sha

# Bind the frozen observer's explicit model import to its actual frozen model.
# This is isolated module loading, never an author expected-value import.
_own=sys.modules['model'];sys.modules['model']=M.M
try:OLD=M.module('frozen_matherr_observer',ROOT/'tools/m4-crt-entry-matherr-root/observe.py','8a55f96c298f19ff1ccbe6c24a449378064b678cea07da3fd6aa83a79a58445f')
finally:sys.modules['model']=_own

def base_memory(payload,provider_pages,game_page,source_pages):
    memory=OLD.base_memory(payload,provider_pages,game_page,source_pages)
    for a in (M.WRAPPER,M.THUNK):memory[a]=bytearray(source_pages[a])
    return memory

def stage(state,fx,runtime_cpu,memory):
    value=OLD.stage(state,fx,runtime_cpu,memory)
    value['control-wrapper.bin']=bytes(memory[M.WRAPPER]);value['control-thunk.bin']=bytes(memory[M.THUNK])
    value['control-hot.bin']=bytes(memory[0x78004000][0x2e1:0x410])
    value['control-cold.bin']=bytes(memory[0x78011000][0x29b:0x318])
    return value

def writer_result(row,payload,wp,pp,gp,source):
    assert pin(row/'input.bin').read_bytes()==payload
    writer=R.observe(pin(row/'writer-record.bin').read_bytes(),payload,wp,pp,gp)
    initial,fx,cp,_,_=R.seed(payload);memory=base_memory(payload,pp,gp,source)
    phases={'writer-before':stage(initial,fx,struct.pack('<10I',*cp),memory)}
    final=bytearray(initial)
    for o,name in zip(N.OFFSETS,N.REGS):F.put(final,o,writer.r[name])
    for o,b in N.FLAGS:final[o]=(writer.flags>>b)&1
    F.put(final,2472,writer.pc);F.put(final,2768,writer.cw,2);F.put(fx,0,writer.cw,2)
    for i,a in enumerate(N.PAGES):memory[a]=bytearray(writer.memory[4096*i:4096*(i+1)])
    phases['writer-after']=stage(final,fx,D.cpu(final),memory)
    return final,fx,memory,phases

def expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,source,control=0):
    final,fx,memory,phases=writer_result(row,payload,wp,pp,gp,source)
    entry=M.Entry(program,providers,maths,ctrl,final,memory,fx,control)
    before=copy.deepcopy(memory)
    mutation={25:(M.WRAPPER,0),26:(M.THUNK,0),27:(0x5bb000,0x578),28:(0x78004000,0x2e1),29:(0x78011000,0x29b)}.get(control)
    if mutation:
        a,o=mutation;F.put(before[a],o,0x1ded8a^1 if control==27 else 0)
    outer=bytearray(D.cpu(final));F.put(outer,16,D.FRAME+4);F.put(outer,36,0xfffffff0)
    phases['entry-before-invoke']=stage(final,fx,outer,before)
    entry.run()
    phases['entry-projected']=stage(entry.projected[0],fx,entry.projected[1],entry.projected[2])
    for tag,value in (('matherr-before',entry.math_before),('matherr-projected',entry.math_projected),('matherr-after',entry.math_after)):
        if value is not None:phases[tag]=stage(value[0],fx,value[1],value[2])
    for tag,value in (('control-before',entry.control_before),('control-projected',entry.control_projected),('control-provider-before',entry.provider_before),('control-provider-projected',entry.provider_projected),('control-provider-after',entry.provider_after),('control-after',entry.control_after)):
        if value is not None:phases[tag]=stage(value[0],value[3],value[1],value[2])
    phases['entry-after-fault']=stage(entry.state,entry.fx,entry.runtime_cpu,entry.mem)
    phases['retry-after']=phases['entry-after-fault']
    return entry,phases

def evidence(entry):
    value=OLD.expected_evidence(entry)
    value['undefined-events.bin']=struct.pack('<I',0x5ac41f) if 0x5ac41f in entry.visited else b''
    events=b''.join(struct.pack('<4I',*v) for v in entry.control_events)
    accesses=b''.join(struct.pack('<5I',*v) for v in entry.control_source)
    value['control-events.bin']=events+bytes(256-len(events))
    value['control-accesses.bin']=accesses+bytes(5120-len(accesses))
    value['control-job.bin']=struct.pack('<12I',*entry.control_status)
    return value

def compare(row,entry,phases,control=0):
    OLD.check_stages(row,phases)
    for name,value in evidence(entry).items():
        actual=pin(row/name).read_bytes();OLD.evidence_equal(json.loads(actual) if name.endswith('.json') else actual,value,name)
    result=json.loads(pin(row/'result.json').read_text())
    assert result['passed'] and result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
    fault=(0,0x5ac440,0x5ac598) if not control else ((4,0x5ac400,0x5ac3a0) if control in (28,29) else (4,0x5bb578,M.WRAPPER) if control in (30,31,32,33) else (4,0x5ac5af,M.WRAPPER) if control==35 else (4,M.WRAPPER,M.WRAPPER))
    assert (result['fault_reason'],result['fault_site'],result['fault_target'])==fault
    assert result['control']==control and result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==len(entry.data_routes)
    for name in ('writer','entry'):D.host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
    assert pin(row/'control-reason.txt').read_text().strip()==entry.control_reason

def unused_control(row):
    assert not any((row/tag).exists() for tag in ('control-before','control-projected','control-provider-before','control-provider-projected','control-provider-after','control-after'))
    assert pin(row/'control-events.bin').read_bytes()==bytes(256)
    assert pin(row/'control-accesses.bin').read_bytes()==bytes(5120)
    assert pin(row/'control-job.bin').read_bytes()==struct.pack('<12I',0x1ded8a,*([0]*11))
    assert pin(row/'control-reason.txt').read_text().strip()==''

def corruptions(phases,values,level,control):
    rows=OLD.corruptions(phases,values,level,control)
    for tag,files in phases.items():
        for name in ('control-wrapper.bin','control-thunk.bin','control-hot.bin','control-cold.bin'):
            for offset in (0,len(files[name])-1):
                altered=dict(files);b=bytearray(altered[name]);b[offset]^=1;altered[name]=bytes(b)
                try:D.equal(altered,files,'Corrupted added control identity')
                except AssertionError:rows.append(dict(level=level,control=control,phase=tag,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Corrupted added source identity accepted')
    return rows

def main(build,capture,out):
    assert out.parent==ROOT/'reports/m4-crt-entry-control' and not out.exists();out.mkdir()
    try:
        b=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in b[group].items():pin(p,h)
        program,providers,maths,ctrl,source,commands=M.source_material(out)
        wp,pp,gp=R.source_material()
        original=R.originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        payloads=[R.project(v) for v in original[:24]];positives=[];causals=[];denials=[]
        old_causal=types.FunctionType(D.causal.__code__,dict(D.__dict__,stage=stage,base_memory=base_memory))
        old_expected=types.FunctionType(OLD.expected.__code__,dict(OLD.__dict__,stage=stage,base_memory=base_memory))
        for level in ('O0','O2'):
            root=capture/f'native-{level}';assert pin(root/'COMPLETE').read_bytes()==b'COMPLETE'
            for i,payload in enumerate(payloads):
                entry,phases=expected(root/f'row-{i}',payload,wp,pp,gp,program,providers,maths,ctrl,source)
                compare(root/f'row-{i}',entry,phases)
                positives.append(dict(level=level,id=i,game_events=38,matherr_events=5,control_phase_events=len(entry.control_events),control_accesses=len(entry.control_source),provider_PCs=entry.control_pcs,output_CW=F.word(entry.state,2768,2),whole_State=3504,whole_FX=512,whole_pages=14))
                if i==0:denials.extend(corruptions(phases,evidence(entry),level,0))
            for control in range(1,37):
                row=root/f'row-{control+23}'
                if control<=12:
                    value=old_causal(row,payloads[0],wp,pp,gp,program,providers,source,control)
                    if control>=4:unused_control(row)
                elif control<=24:
                    entry,phases=old_expected(row,payloads[0],wp,pp,gp,program,providers,maths,source,control)
                    OLD.check_stages(row,phases);fault=OLD.check_evidence(row,entry,control);unused_control(row)
                    value=dict(control=control,whole_source_prefix_predicted=True,first_fault=fault,terminal_retry=True)
                else:
                    entry,phases=expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,source,control)
                    compare(row,entry,phases,control)
                    value=dict(control=control,whole_source_prefix_predicted=True,control_status=entry.control_status,provider_PCs=entry.control_pcs,terminal_retry=True)
                    denials.extend(corruptions(phases,evidence(entry),level,control))
                value['level']=level;causals.append(value)
        for m in (M.M,D,R,N,D.E,F,M.C):M.PINS.update(m.PINS)
        pin(__file__);pin(M.__file__);pin(sys.executable)
        result=dict(passed=True,scope='Independent BEFORE-only entire control composition and complete stopped causal prefixes',positive_records=48,causal_records=len(causals),positives=positives,causals=causals,positive_writer_events=4656,positive_game_events=1824,positive_matherr_events=240,control_phase_events=sum(v['control_phase_events'] for v in positives),control_source_accesses=sum(v['control_accesses'] for v in positives),whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=14,source_identity_bytes=900,direct_host_boundary_pairs=234,observer_corruption_denials=denials,source_commands=commands,author_model_imported=False,AF_undefined_representative_generalized=False,callback_executed=False,full_CRT=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        for p in out.iterdir():
            if p.is_file():pin(p)
        for p,h in list(M.PINS.items()):assert sha(p)==h,p
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(M.PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=48,accesses=result['control_source_accesses'],denials=len(denials),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
