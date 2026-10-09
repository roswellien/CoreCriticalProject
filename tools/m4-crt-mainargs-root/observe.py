"""BEFORE-only full-state comparison of native startup to the named argv API stop."""
import copy,json,ntpath,struct,sys,traceback,types
from pathlib import Path
sys.dont_write_bytecode=True
import model as M
D,F,R,N=M.D,M.F,M.R,M.N;ROOT=M.ROOT;pin=M.pin;sha=M.sha
_own=sys.modules['model'];sys.modules['model']=M.M
try:OLD=M.module('frozen_null_initializer_observer',ROOT/'tools/m4-crt-entry-initterm-root/observe.py','453b0032ac308b090d1b77438a10d8fa66ed32d13e979fb991d4536ce44d769f')
finally:sys.modules['model']=_own

def base_memory(payload,provider_pages,game_page,source_pages):
    return OLD.base_memory(payload,provider_pages,game_page,source_pages)
def stage(state,fx,runtime_cpu,memory):
    files=OLD.stage(state,fx,runtime_cpu,memory)
    files['mainargs-provider.bin']=bytes(memory[0x7800b000][0xa5e:0xaa0])
    files['mainargs-builder.bin']=bytes(memory[0x7800b000][0xbbc:0xc48])
    return files
writer_result=types.FunctionType(OLD.writer_result.__code__,dict(OLD.writer_result.__globals__,pin=pin,stage=stage,base_memory=base_memory))

def expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,control=0,level='O0'):
    final,fx,memory,phases=writer_result(row,payload,wp,pp,gp,source)
    entry=M.Entry(program,providers,maths,ctrl,init,args,argv,final,memory,fx,control,level)
    before=copy.deepcopy(memory);outer=bytearray(D.cpu(final));F.put(outer,16,D.FRAME+4);F.put(outer,36,0xfffffff0)
    phases['entry-before-invoke']=stage(final,fx,outer,before)
    entry.run();phases['entry-projected']=stage(entry.projected[0],fx,entry.projected[1],entry.projected[2])
    for tag,value in (('matherr-before',entry.math_before),('matherr-projected',entry.math_projected),('matherr-after',entry.math_after)):
        if value is not None:phases[tag]=stage(value[0],fx,value[1],value[2])
    for tag,value in (('control-before',entry.control_before),('control-projected',entry.control_projected),('control-provider-before',entry.provider_before),('control-provider-projected',entry.provider_projected),('control-provider-after',entry.provider_after),('control-after',entry.control_after)):
        if value is not None:phases[tag]=stage(value[0],value[3],value[1],value[2])
    for values in (entry.init_phases,entry.args_phases):
        for tag,value in values.items():phases[tag]=stage(value[0],value[3],value[1],value[2])
    phases['entry-after-fault']=stage(entry.state,entry.fx,entry.runtime_cpu,entry.mem);phases['retry-after']=phases['entry-after-fault']
    return entry,phases
def evidence(entry):
    values=OLD.evidence(entry)
    events=b''.join(struct.pack('<4I',*v) for v in entry.args_events);accesses=b''.join(struct.pack('<5I',*v) for v in entry.args_accesses)
    values['mainargs-events.bin']=events+bytes(256-len(events));values['mainargs-accesses.bin']=accesses+bytes(1280-len(accesses));values['mainargs-job.bin']=struct.pack('<20I',*entry.args_job)
    return values
def compare(row,entry,phases,control=0):
    OLD.OLD.OLD.check_stages(row,phases)
    for name,value in evidence(entry).items():
        actual=pin(row/name).read_bytes();OLD.OLD.OLD.evidence_equal(json.loads(actual) if name.endswith('.json') else actual,value,str(row)+' '+name)
    result=json.loads(pin(row/'result.json').read_text())
    fault=(1,M.API_PC,M.API_SLOT) if not control else (4,M.SLOT,M.SLOT)
    assert (result['fault_reason'],result['fault_site'],result['fault_target'])==fault,(str(row),result,fault)
    assert result['passed'] and result['control']==control and result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
    assert result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1
    assert pin(row/'mainargs-reason.txt').read_text().strip()==entry.args_reason
    assert pin(row/'initterm-reason.txt').read_text().strip()==entry.init_reason
    assert pin(row/'control-reason.txt').read_text().strip()==entry.control_reason
    for name in ('writer','entry'):D.host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
def unused_args(row):
    assert not any((row/tag).exists() for tag in ('mainargs-before','mainargs-projected','mainargs-after','mainargs-builder-before','mainargs-builder-projected','mainargs-builder-after'))
    assert pin(row/'mainargs-events.bin').read_bytes()==bytes(256)
    assert pin(row/'mainargs-accesses.bin').read_bytes()==bytes(1280)
    assert pin(row/'mainargs-job.bin').read_bytes()==struct.pack('<20I',M.SLOT,M.RAW,*([0]*18))
    assert pin(row/'mainargs-reason.txt').read_text().strip()==''
def unused_early_args(row):
    assert not any((row/name).exists() for name in ('mainargs-before','mainargs-projected','mainargs-after','mainargs-builder-before','mainargs-builder-projected','mainargs-builder-after','mainargs-events.bin','mainargs-accesses.bin','mainargs-job.bin','mainargs-reason.txt'))
def corruptions(phases,values,level,control):
    rows=OLD.corruptions(phases,values,level,control)
    for tag,files in phases.items():
        for name in ('mainargs-provider.bin','mainargs-builder.bin'):
            for offset in (0,len(files[name])-1):
                altered=dict(files);value=bytearray(altered[name]);value[offset]^=1;altered[name]=bytes(value)
                try:D.equal(altered,files,'Corrupted mainargs source observation')
                except AssertionError:rows.append(dict(level=level,control=control,phase=tag,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Corrupted mainargs checkpoint accepted')
    return rows
def clone(fn,**replacements):return types.FunctionType(fn.__code__,dict(fn.__globals__,pin=pin,stage=stage,base_memory=base_memory,**replacements))

def main(build,capture,out):
    assert out.parent==ROOT/'reports/m4-crt-mainargs' and not out.exists();out.mkdir()
    try:
        b=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for path,digest in b[group].items():pin(path,digest)
        program,providers,maths,ctrl,init,args,argv,source,commands=M.source_material(out);wp,pp,gp=R.source_material()
        original=R.originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        payloads=[R.project(v) for v in original[:24]];positives=[];causals=[];denials=[]
        old_causal=clone(D.causal)
        math_expected=clone(OLD.OLD.OLD.expected)
        control_expected=clone(OLD.OLD.expected,writer_result=writer_result)
        init_expected=clone(OLD.expected,writer_result=writer_result)
        for level in ('O0','O2'):
            root=capture/f'native-{level}';assert pin(root/'COMPLETE').read_bytes()==b'COMPLETE'
            for index,payload in enumerate(payloads):
                row=root/f'row-{index}';entry,phases=expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,0,level)
                compare(row,entry,phases)
                positives.append(dict(level=level,id=index,game_events=len(entry.events),mainargs_accesses=len(entry.args_accesses),mainargs_routes=len(entry.args_events),mainargs_source_PCs=entry.args_PCs,whole_State=3504,whole_FX=512,whole_pages=16))
                if index==0:denials.extend(corruptions(phases,evidence(entry),level,0))
            for control in range(1,61):
                row=root/f'row-{control+23}'
                if control<=12:
                    value=old_causal(row,payloads[0],wp,pp,gp,program,providers,source,control)
                    if control>=4:OLD.OLD.unused_control(row);OLD.unused_init(row);unused_args(row)
                    else:unused_early_args(row)
                elif control<=24:
                    entry,phases=math_expected(row,payloads[0],wp,pp,gp,program,providers,maths,source,control)
                    OLD.OLD.OLD.check_stages(row,phases);fault=OLD.OLD.OLD.check_evidence(row,entry,control);OLD.OLD.unused_control(row);OLD.unused_init(row);unused_args(row)
                    value=dict(control=control,whole_source_prefix_predicted=True,first_fault=fault,terminal_retry=True)
                elif control<=36:
                    entry,phases=control_expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,source,control)
                    OLD.OLD.compare(row,entry,phases,control);OLD.unused_init(row);unused_args(row)
                    value=dict(control=control,whole_source_prefix_predicted=True,terminal_retry=True)
                elif control<=48:
                    entry,phases=init_expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,init,source,control,level)
                    OLD.compare(row,entry,phases,control);unused_args(row)
                    value=dict(control=control,whole_source_prefix_predicted=control!=43,terminal_retry=True,artifact_specific_injected_operand=control==43,architectural_source_equivalence_credited=control!=43)
                else:
                    entry,phases=expected(row,payloads[0],wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,control,level)
                    compare(row,entry,phases,control)
                    value=dict(control=control,whole_source_prefix_predicted=True,mainargs_job=entry.args_job,mainargs_source_PCs=entry.args_PCs,terminal_retry=True)
                    denials.extend(corruptions(phases,evidence(entry),level,control))
                value['level']=level;causals.append(value)
        for module in (M.M,M.M.M,M.M.M.M,D,R,N,D.E,F,M.C):
            for path,digest in module.PINS.items():
                key=ntpath.normcase(ntpath.normpath(path));assert key not in M.PINS or M.PINS[key]==digest,key
                M.PINS[key]=digest
        pin(__file__);pin(M.__file__);pin(sys.executable)
        result=dict(passed=True,scope='Independent original-FDIV-BEFORE source composition to named provider API stop; prior mode43 remains two separately reviewed artifact fixtures',positive_records=48,causal_records=120,positives=positives,causals=causals,positive_writer_events=4656,positive_game_events=sum(v['game_events'] for v in positives),mainargs_accesses=sum(v['mainargs_accesses'] for v in positives),mainargs_route_events=sum(v['mainargs_routes'] for v in positives),whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=16,source_identity_bytes=1140,direct_host_boundary_pairs=330,observer_corruption_denials=denials,source_commands=commands,author_model_imported=False,mode43_generalized_source_equivalence=False,selected_initializer_count=27,callbacks_executed=False,argument_initialization_complete=False,provider_API_executed=False,full_CRT=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        for path in out.iterdir():
            if path.is_file():pin(path)
        for path,digest in list(M.PINS.items()):assert sha(path)==digest,path
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(M.PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,positives=48,causals=120,accesses=result['mainargs_accesses'],denials=len(denials),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(path).resolve() for path in sys.argv[1:]])
