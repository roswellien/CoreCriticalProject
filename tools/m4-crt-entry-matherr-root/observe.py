"""Root source-only observer of the actual FDIV -> CRT -> matherr composition.

The old twelve causal cases reuse the frozen root code object with explicit
fourteen-page projection bindings. No candidate fixture/model is imported.
"""
import copy,json,struct,sys,traceback,types
from pathlib import Path
sys.dont_write_bytecode=True
import model as M
D,F,R,N=M.D,M.F,M.R,M.N
ROOT=M.ROOT;pin=M.pin;sha=M.sha

def base_memory(payload,provider_pages,game_page,source_pages):
    memory=D.base_memory(payload,provider_pages,game_page,source_pages)
    memory.update({a:bytearray(source_pages[a]) for a in M.MATH_PAGES})
    memory[M.MATH_ENTRY]=bytearray(source_pages[M.MATH_ENTRY])
    return memory

def stage(state,fx,runtime_cpu,memory):
    result=D.stage(state,fx,runtime_cpu,memory)
    for a in M.MATH_PAGES:result[f'page-{a}.bin']=bytes(memory[a])
    result['matherr-source.bin']=bytes(memory[0x7800b000][0x38f:0x3a0])
    return result

def expected(row,payload,writer_program,provider_pages,game_page,program,providers,math_program,source_pages,control=0):
    assert pin(row/'input.bin').read_bytes()==payload
    record=pin(row/'writer-record.bin').read_bytes()
    writer=R.observe(record,payload,writer_program,provider_pages,game_page)
    initial,fx,cpu0,_,_=R.seed(payload)
    memory=base_memory(payload,provider_pages,game_page,source_pages)
    stages={'writer-before':stage(initial,fx,struct.pack('<10I',*cpu0),memory)}
    final=bytearray(initial)
    for o,name in zip(N.OFFSETS,N.REGS):F.put(final,o,writer.r[name])
    for o,b in N.FLAGS:final[o]=(writer.flags>>b)&1
    F.put(final,2472,writer.pc);F.put(final,2768,writer.cw,2);F.put(fx,0,writer.cw,2)
    for i,a in enumerate(N.PAGES):memory[a]=writer.memory[4096*i:4096*(i+1)]
    stages['writer-after']=stage(final,fx,D.cpu(final),memory)
    entry=M.Entry(program,providers,math_program,final,memory,control)
    before=copy.deepcopy(memory)
    if control==13:F.put(before[0x7800b000],0x38f,0)
    if control==14:F.put(before[0x5bb000],0x50c,0x1ded1e^1)
    if control==22:F.put(before[0x78039000],0x2b8,F.word(before[0x78039000],0x2b8)^1)
    if control==23:F.put(before[0x7803b000],0xc4,F.word(before[0x7803b000],0xc4)^1)
    outer=bytearray(D.cpu(final));F.put(outer,16,D.FRAME+4);F.put(outer,36,0xfffffff0)
    stages['entry-before-invoke']=stage(final,fx,outer,before)
    stages['entry-projected']=stage(entry.projected[0],fx,entry.projected[1],entry.projected[2])
    entry.run()
    for tag,value in (('matherr-before',entry.math_before),('matherr-projected',entry.math_projected),('matherr-after',entry.math_after)):
        if value is not None:stages[tag]=stage(value[0],fx,value[1],value[2])
    stages['entry-after-fault']=stage(entry.state,fx,entry.runtime_cpu,entry.mem)
    stages['retry-after']=stages['entry-after-fault']
    return entry,stages

def check_stages(row,stages):
    actual={p.name for p in row.iterdir() if p.is_dir()}
    assert actual==stages.keys(),'Exact checkpoint inventory'
    for tag,value in stages.items():D.equal(D.read_stage(row,tag),value,tag+' whole source prediction')

def expected_evidence(entry):
    math=b''.join(struct.pack('<4I',*v) for v in entry.math_events)
    return {'entry-events.bin':b''.join(struct.pack('<5I',*v) for v in entry.events),
            'matherr-events.bin':math+bytes(80-len(math)),
            'matherr-job.bin':struct.pack('<12I',*entry.math_status),
            'data-routes.bin':b''.join(struct.pack('<5I',*v) for v in entry.data_routes),
            'undefined-events.bin':struct.pack('<I',0x5ac41f),
            'calls.json':[{('import' if k=='import_' else k):v for k,v in route.items()} for route in entry.routes]}

def evidence_equal(actual,expected,name):
    assert actual==expected,name+' source prediction'

def check_evidence(row,entry,control):
    for name,value in expected_evidence(entry).items():
        actual=pin(row/name).read_bytes()
        evidence_equal(json.loads(actual) if name.endswith('.json') else actual,value,name)
    result=json.loads(pin(row/'result.json').read_text())
    fault=(0,0x5ac431,0x5ac5a0) if control==0 else ((2,0x5ac428,0x5bb50c) if control==14 else (4,0x5bb50c,0x5bb50c))
    assert (result['fault_reason'],result['fault_site'],result['fault_target'])==fault
    assert result['passed'] and result['control']==control and result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
    assert result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1
    assert result['actual_query_BOOL']==entry.raw_load(0x78037c2c)
    reasons={15:'Matherr checked write fault',16:'Matherr checked write fault',18:'Matherr return word changed',19:'Matherr actual RET/CPU/frame closure rejected',20:'Matherr actual RET/CPU/frame closure rejected',21:'Matherr unexpected required read'}
    assert pin(row/'matherr-reason.txt').read_text().strip()==reasons.get(control,'')
    for name in ('writer','entry'):D.host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
    return fault

def corruptions(stages,evidence,level,control):
    rows=[]
    # Every checkpoint's opaque State, FX, GPR/flags projection and every page
    # are challenged; rejection is against an independently predicted value.
    for tag,files in stages.items():
        for name,offset in [('state.bin',3400),('state.bin',2472),('fx.bin',24),('runtime-cpu.bin',36),('state-cpu.bin',32)]+[(f'page-{a}.bin',0) for a in tuple(D.PAGES)+M.MATH_PAGES]+[('crt-globals.bin',4),('tib-0.bin',0),('entry-source.bin',0),('matherr-source.bin',0)]:
            altered=dict(files);b=bytearray(altered[name]);b[offset]^=1;altered[name]=bytes(b)
            try:D.equal(altered,files,'Corrupted source checkpoint')
            except AssertionError:rows.append(dict(level=level,control=control,phase=tag,file=name,offset=offset,rejected=True))
            else:raise AssertionError('Corrupted independent checkpoint accepted')
    for name,value in evidence.items():
        if name=='calls.json':
            for i,route in enumerate(value):
                for key in ('site','target','return_pc','import','completed'):
                    altered=copy.deepcopy(value);v=altered[i][key];altered[i][key]=not v if isinstance(v,bool) else v^1
                    try:evidence_equal(altered,value,name)
                    except AssertionError:rows.append(dict(level=level,control=control,file=name,route=i,key=key,rejected=True))
                    else:raise AssertionError('Corrupted source call ledger accepted')
        else:
            # Challenge each event field, diagnostic field and unused suffix.
            for offset in range(0,len(value),4):
                altered=bytearray(value);altered[offset]^=1
                try:evidence_equal(bytes(altered),value,name)
                except AssertionError:rows.append(dict(level=level,control=control,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Corrupted source event/diagnostic accepted')
    return rows

def main(build,capture,out):
    assert out.parent==ROOT/'reports/m4-crt-entry-matherr' and not out.exists();out.mkdir()
    try:
        receipt=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert receipt['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in receipt[group].items():pin(p,h)
        program,providers,math_program,source_pages,commands=M.source_material(out)
        writer_program,provider_pages,game_page=R.source_material()
        original=R.originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        payloads=[R.project(v) for v in original[:24]]
        old_causal=types.FunctionType(D.causal.__code__,dict(D.__dict__,stage=stage,base_memory=base_memory,Entry=lambda p,pr,s,m,c:M.Entry(p,pr,math_program,s,m,c)))
        positives=[];causals=[];denials=[]
        for level in ('O0','O2'):
            root=capture/f'native-{level}';assert pin(root/'COMPLETE').read_bytes()==b'COMPLETE'
            for i in range(48):
                row=root/f'row-{i}';control=0 if i<24 else i-23
                if 1<=control<=12:
                    value=old_causal(row,payloads[0],writer_program,provider_pages,game_page,program,providers,source_pages,control)
                    if control>=4:
                        assert pin(row/'matherr-events.bin').read_bytes()==bytes(80)
                        assert pin(row/'matherr-job.bin').read_bytes()==struct.pack('<12I',0x5bb50c,0x1ded1e,*([0]*10))
                        assert not any((row/tag).exists() for tag in ('matherr-before','matherr-projected','matherr-after'))
                    value['level']=level;causals.append(value);continue
                entry,stages=expected(row,payloads[i] if i<24 else payloads[0],writer_program,provider_pages,game_page,program,providers,math_program,source_pages,control)
                check_stages(row,stages);fault=check_evidence(row,entry,control)
                value=dict(level=level,id=i,control=control,whole_State=3504,whole_FX=512,whole_pages=14,game_events=len(entry.events),matherr_events=len(entry.math_events),matherr_status=entry.math_status,source_PCs=entry.visited,matherr_PCs=entry.math_PCs,first_fault=fault,terminal_retry=True)
                (causals if control else positives).append(value)
                if i==0 or control>=13:denials.extend(corruptions(stages,expected_evidence(entry),level,control))
        for module in (D,R,N,D.E,F):M.PINS.update(module.PINS)
        pin(__file__);pin(Path(M.__file__));pin(sys.executable)
        report=dict(passed=True,scope='Independent BEFORE-only actual FDIV and game CRT caller through compiled matherr registration to unresolved control wrapper',positive_records=len(positives),causal_records=len(causals),positives=positives,causals=causals,whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=14,source_identity_bytes=447,original_BEFORE_rows=24,positive_writer_events=48*97,positive_game_events=sum(v['game_events'] for v in positives),positive_matherr_events=sum(v['matherr_events'] for v in positives),direct_host_boundary_pairs=186,observer_corruption_denials=denials,source_commands=commands,author_model_imported=False,AF_undefined_representative_generalized=False,original_entry_executed=False,full_CRT=False,callback_executed=False,full_joint_startup=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json')
        for p in out.iterdir():
            if p.is_file():pin(p)
        for p,h in list(M.PINS.items()):assert sha(p)==h,p
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(M.PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,positive_records=len(positives),causal_records=len(causals),denials=len(denials),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
