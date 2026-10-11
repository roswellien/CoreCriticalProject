"""Bounded literal provider planning execution with explicit synthetic scratch.

This is a source-model preflight, not a genuine instruction/stack proof. Real
cdecl inputs and real initial owned bytes are used, but lower scratch bytes are
zero-filled here. The genuine full BEFORE trace must replace that assumption.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=R/'reports/m4-formatting-source'/name;need(not out.exists(),'Fresh additive model preflight');out.mkdir(parents=True);files={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No capture payload reader');v=sha(p);need(h is None or h==v,'Pinned bounded input '+str(p));files[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def module(p,n):
        s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def emit(n,x):p=out/n;p.write_text(json.dumps(x,indent=2)+'\n');pin(p)
    try:
        original=R/'reports/m4-formatting-original/prefix-validation-r1';receipt=read(original/'report.json','54199a2f52a1c7489ccc53a8722bf6dc1d06395e7c05c6043e84f82af5f1b3e4');need(receipt['passed'],'Measured genuine original cdecl inputs')
        rows=read(original/'actual-cdecl-boundaries.json',receipt['files'][str((original/'actual-cdecl-boundaries.json').resolve())]);owners=read(original/'actual-owners.json',receipt['files'][str((original/'actual-owners.json').resolve())])
        M=module(R/'tools/m4-formatting-source/provider_model.py','literal_format_preflight');rec=read(M.REC/'report.json',M.REC_SHA)
        for p,h in rec['files'].items():pin(p,h)
        tables=read(M.REC/'tables.json');results=[]
        for before in rows:
            if before['kind'] not in(0,4):continue
            phase,kind=before['phase'],before['kind'];memory={0x20001000:bytearray(4096)}
            def add(address,raw):
                for i,value in enumerate(raw):
                    page=(address+i)&~4095;memory.setdefault(page,bytearray(4096))[(address+i)&4095]=value
            add(before['cpu'][4],bytes.fromhex(before['frame32_hex']))
            for string in before['strings']:
                if string['pointer']:add(string['pointer'],bytes.fromhex(string['bytes_hex']))
            for table in tables:add(table['address'],bytes.fromhex(table['bytes_hex']))
            owner=owners[phase]
            if kind==4:add(owner['pointer'],bytes.fromhex(owner['initial_hex']))
            machine=M.from_boundary(before,memory);ret=int.from_bytes(machine.bytes(before['cpu'][4],4),'little')
            machine.run(lambda m:m.cursor==ret)
            after=next(r for r in rows if r['phase']==phase and r['kind']==kind+1)
            predicted=machine.projected_cpu();actual=tuple(after['cpu']);need(predicted==actual,'Full return CPU40 in planning scratch run '+str((phase,kind)))
            if kind==4:need(machine.bytes(owner['pointer'],owner['capacity']).hex()==owner['final_hex'],'Entire actual owned capacity final bytes from literal writes')
            need(machine.fx.hex()==after['FX512_hex'] and before['ENV28_hex']==after['ENV28_hex'],'Unchanged full provider FX/ENV in original observations')
            results.append(dict(phase=phase,kind=kind,source_instructions=len(machine.PCs),unique_source_PCs=sorted(set(machine.PCs)),CPU=predicted,accesses=machine.accesses,calls=machine.calls,string_iterations=machine.string_iterations,output_dispatches=machine.output_dispatches,full_return_CPU_matched=True,full_output_backing_matched=kind==4,synthetic_lower_scratch=True,genuine_lower_scratch_proved=False))
        emit('source-derivations.json',results);pin(__file__);pin(M.I.__file__);pin(sys.executable)
        report=dict(passed=True,scope='Literal six-call provider planning preflight against measured entry/return observations; lower scratch synthetic, no genuine trace or runtime credit',provider_calls=6,source_instructions=sum(x['source_instructions'] for x in results),source_accesses=sum(len(x['accesses']) for x in results),full_output_backings=3,files=files,capture_reader_opened=False,genuine_stack_proved=False,normal_reached_original_proved=False,native_executed=False,initializer_credit=0,source_post_state_seed=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),instructions=report['source_instructions'],calls=[len(x['calls']) for x in results],dispatches=[x['output_dispatches'] for x in results if x['kind']==4])))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
