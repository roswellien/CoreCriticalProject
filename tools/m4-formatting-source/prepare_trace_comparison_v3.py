"""Strengthen literal original byte joins and deny undefined control inputs."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=R/'tools/m4-formatting-source/compare_trace_v2.py'
    source=base.read_text()
    def one(a,b):
        nonlocal source
        assert source.count(a)==1,a
        source=source.replace(a,b)
    one("before=list(self.projected_cpu());begin=len(self.accesses);preimage={};flag_before=dict(getattr(self,'undefined_flag_domain',{}));flag_after=F.advance(self,self.program[pc],flag_before)","""before=list(self.projected_cpu());begin=len(self.accesses);preimage={};flag_before=dict(getattr(self,'undefined_flag_domain',{}));flag_after=F.advance(self,self.program[pc],flag_before)
                    consumed={'je':('ZF',),'jne':('ZF',),'ja':('CF','ZF'),'jae':('CF',),'jb':('CF',),'jbe':('CF','ZF'),'jg':('ZF','SF','OF'),'jge':('SF','OF'),'jl':('SF','OF'),'jle':('ZF','SF','OF'),'js':('SF',),'jns':('SF',),'jo':('OF',),'jno':('OF',),'adc':('CF',),'sbb':('CF',),'scasb':('DF',)}.get(self.program[pc]['mnemonic'],())
                    need(not set(consumed)&set(flag_before),'No conditional/repeat/carry source use of an architecturally undefined flag')
                    if consumed:counts['source_defined_control_flag_uses']+=1""")
    one("operands.append(dict(**cell,source_rows=matched));counts['literal_actual_memory_operand_joins']+=1", """ambient=None
                    for address,bytes_ in derived['preimage'].items():
                        offset=cell['address']-address
                        if 0<=offset and offset+cell['width']<=len(bytes_):
                            ambient=int.from_bytes(bytes_[offset:offset+cell['width']],'little');break
                    if cell['write']:
                        need(ambient is not None,'Every actual source write has whole literal BEFORE backing')
                        eq(ambient,cell['before'],'Entire write operand BEFORE bytes from literal preceding source state')
                        counts['literal_actual_write_before_joins']+=1
                    operands.append(dict(**cell,source_rows=matched,source_before_value=ambient));counts['literal_actual_memory_operand_joins']+=1""")
    one("pin(R/'tools/m4-formatting-source/compare_trace.py')", "pin(R/'tools/m4-formatting-source/compare_trace.py');pin(R/'tools/m4-formatting-source/compare_trace_v2.py');pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v3.py')")
    one("source_post_state_seed=False)","source_post_state_seed=False,write_operand_before_from_literal_backing=True,undefined_flag_control_denied=True)")
    generated=base.with_name('compare_trace_v3.py');assert not generated.exists();generated.write_text(source)
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
    files={str(p.resolve()):sha(p)for p in(base,generated,Path(__file__))}
    report=dict(passed=True,scope='Additive full source write BEFORE and source-defined control flag checks; unchanged literal model',source=str(generated),source_sha256=sha(generated),files=files)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
