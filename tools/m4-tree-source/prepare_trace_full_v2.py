"""Join literal instruction execution with finite original CRT volatile returns."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=ROOT/'tools/m4-tree-source/compare_trace_prefix.py';s=base.read_text()
    def one(a,b):
        nonlocal s
        assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    one("trace_points=read(ROOT/'reports/m4-tree-original/trace-preparation-r1/trace_points.json'", "trace_validation=read(ROOT/'reports/m4-tree-original/trace-validation-r2/report.json','1c099256ca7bdc076bffa23a37c9aab6975a4769337ce8c7cff64ba623bea463');need(trace_validation['passed'],'Independent genuine debugger trace validation');actual_trace=read(ROOT/'reports/m4-tree-original/trace-validation-r2/actual-instructions.json',trace_validation['files'][str((ROOT/'reports/m4-tree-original/trace-validation-r2/actual-instructions.json').resolve())]);CRT_returns=[r for r in actual_trace if r['PC']==0x5f401eb7];need(len(CRT_returns)==7,'Every genuine MFC malloc volatile return');CRT_registration=next(r for r in actual_trace if r['PC']==0x5ac124);frontier_facts=[]\n        trace_points=read(ROOT/'reports/m4-tree-original/trace-preparation-r1/trace_points.json'")
    one("model.reg('edx',fact[12]);model.api_return(site,0,fact[10]);alloc_index[0]+=1;counts['actual_initial_allocator_witnesses']+=1", """model.reg('edx',fact[12]);model.api_return(site,0,fact[10])
            frontier=CRT_returns[alloc_index[0]];actual=list(frontier['raw_debugger_before_cpu']);actual[8]&=~0x10100;actual[9]=frontier['PC'];modeled=list(model.projected_cpu());modeled[9]=model.cursor
            need(actual[0]==fact[10] and actual[2]==fact[12] and actual[3:8]==modeled[3:8] and actual[9]==model.cursor,'Finite malloc return keeps exact result/nonvolatiles/current cdecl source frame')
            modeled[1]=actual[1];modeled[8]=actual[8];projection.statecpu(model.state,modeled)
            frontier_facts.append(dict(service='genuine CRT malloc return',event=frontier['index'],caller=site,return_PC=model.cursor,actual_EAX=actual[0],actual_ECX=actual[1],actual_EDX=actual[2],actual_EFLAGS_without_debugger_TF_RF=actual[8],memory_effects_seeded=False))
            alloc_index[0]+=1;counts['actual_initial_allocator_witnesses']+=1""")
    one("machine.run(lambda model:model.cursor==0x78004a36,api=external);result=machine.tree_result()", "machine.run(lambda model:model.cursor==0x78004a36,api=external)")
    anchor="equal(machine.bytes(machine.reg('esp'),8),struct.pack('<2I',0x5ac124,0x4b7fa0),'Literal source callback CALL frame/value')"
    one(anchor,anchor+"""
        actual=list(CRT_registration['raw_debugger_before_cpu']);actual[8]&=~0x10100;actual[9]=CRT_registration['PC']
        need(actual[0]==0x4b7fa0,'Original registration scalar return is the exact literal callback')
        machine.api_return(0x5ac11e,0,actual[0]);modeled=list(machine.projected_cpu());modeled[9]=machine.cursor
        need(actual[3:8]==modeled[3:8] and actual[9]==machine.cursor,'Finite registration return keeps actual cdecl frame and source nonvolatiles')
        modeled[1:3]=actual[1:3];modeled[8]=actual[8];projection.statecpu(machine.state,modeled)
        frontier_facts.append(dict(service='genuine CRT registration return',event=CRT_registration['index'],caller=0x5ac11e,return_PC=machine.cursor,actual_EAX=actual[0],actual_ECX=actual[1],actual_EDX=actual[2],actual_EFLAGS_without_debugger_TF_RF=actual[8],memory_effects_seeded=False))
        G.complete_root(machine);result=machine.tree_result();counts['actual_finite_CRT_volatile_return_frontiers']=len(frontier_facts)
        need(len(literal_instructions)==len(actual_trace)==1198,'Complete genuine/literal selected source instruction extent')
        joins=[]
        for modeled,actual_row in zip(literal_instructions,actual_trace):
            need(modeled['PC']==actual_row['PC'],'Every reached source PC and occurrence equals genuine trace')
            for side in ('before','after'):
                actual_cpu=list(actual_row['raw_debugger_'+side+'_cpu']);actual_cpu[8]&=~0x10100
                if side=='before':actual_cpu[9]=actual_row['PC']
                if side=='after' and actual_row['instruction_kind']==1:continue
                equal(modeled['source_'+side+'_CPU'],actual_cpu,'Full source CPU matches actual debugger projection '+hex(modeled['PC'])+' '+side)
                counts['whole_projected_instruction_CPU_relations']+=1
            accesses=machine.accesses[modeled['source_access_first']:modeled['source_access_end']]
            if actual_row['instruction_kind']==1:
                need(len(accesses)==1 and accesses[0][1]==0x7ffde000,'FS source instruction separately joins its authoritative raw observer operation');counts['FS_instruction_separate_raw_joins']+=1
            else:
                actual_accesses=[]
                for cell in actual_row['cells']:
                    for direction in (0,1):
                        if cell['write' if direction else 'read']:
                            value=cell['after_value' if direction else 'before_value'];address=cell['address']
                            if not direction:
                                for slot,raw,target in O.MFC_IMPORTS:
                                    if address==slot:need(value==raw,'Physical owning MFC import before named source projection');value=target
                                normalized_IAT={0x5bb454:(0x5f4020b4,0x8000021c),0x5bb4c8:(0x5f401782,0x80000339),0x5bb4f8:(0x7810a290,0x1df582),0x5bb4f4:(0x7810a350,0x1df568),0x5bb52c:(0x78004a36,0x1decb0),0x5bb530:(0x780011be,0x1deca2)}
                                if address in normalized_IAT:
                                    raw,target=normalized_IAT[address];need(value==raw,'Exact loaded game import before named source projection');value=target
                            actual_accesses.append((actual_row['PC'],address,value,cell['width'],direction))
                equal([tuple(r)for r in accesses],actual_accesses,'Every instruction read/write/address/value/direction equals actual original '+hex(modeled['PC']));counts['whole_source_instruction_access_relations']+=len(actual_accesses)
            joins.append(dict(event=actual_row['index'],PC=modeled['PC'],source_access_first=modeled['source_access_first'],source_access_end=modeled['source_access_end'],actual_instruction_kind=actual_row['instruction_kind']))
        result['actual_instruction_joins']=joins;result['finite_original_CRT_returns']=frontier_facts
        need(result['candidate_AFTER_seed'] is False,'No tree AFTER seeding')""")
    # The tuple comparison helper gives useful diagnostics for tuple-valued rows.
    path=ROOT/'tools/m4-tree-source/compare_trace_full_v2.py';assert not path.exists();path.write_text(s)
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Unexecuted finite original CRT return and full instruction comparison binding; no AFTER memory or native credit',files={str(p.resolve()):sha(p)for p in(base,path,Path(__file__))})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
