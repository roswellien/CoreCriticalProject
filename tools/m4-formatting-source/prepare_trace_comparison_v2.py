"""Additive explicit architectural undefined-flag projection for raw original trace."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    p=R/'tools/m4-formatting-source/compare_trace.py';assert sha(p)=='74da6a498f418f98f6086df035321c934281135b30551aae9e194d0acf739dc3'
    source=p.read_text()
    def one(a,b):
        nonlocal source
        assert source.count(a)==1,a;source=source.replace(a,b)
    one("M=load(R/'tools/m4-formatting-source/provider_model.py','literal_formatter_machine');rec=read(M.REC/'report.json',M.REC_SHA)","M=load(R/'tools/m4-formatting-source/provider_model.py','literal_formatter_machine');F=load(R/'tools/m4-formatting-source/flag_domain.py','original_architectural_flag_domain');rec=read(M.REC/'report.json',M.REC_SHA)")
    one("game=read(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json');roots=game['roots'];program,callbacks=M.source_program()", "frontier=read(R/'reports/m4-formatting-frontier/recovery-r1/report.json','8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15');game_path=R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json';game=read(game_path,frontier['files'][str(game_path.resolve())]);roots=game['roots'];program,callbacks=M.source_program()")
    one("before=list(self.projected_cpu());begin=len(self.accesses);preimage={}","before=list(self.projected_cpu());begin=len(self.accesses);preimage={};flag_before=dict(getattr(self,'undefined_flag_domain',{}));flag_after=F.advance(self,self.program[pc],flag_before)")
    one("result=super().step()\n                    if pc in instruction_PCs:literal.append(dict(PC=pc,next_PC=self.cursor,CPU_before=before,CPU_after=list(self.projected_cpu()),source_accesses=[list(r)for r in self.accesses[begin:]],preimage=preimage))", "result=super().step();self.undefined_flag_domain=flag_after\n                    if pc in instruction_PCs:literal.append(dict(PC=pc,next_PC=self.cursor,CPU_before=before,CPU_after=list(self.projected_cpu()),source_accesses=[list(r)for r in self.accesses[begin:]],preimage=preimage,undefined_flags_before=flag_before,undefined_flags_after=flag_after))")
    one("model.reg('ecx',actual_after[1]);model.reg('edx',actual_after[2])", "model.reg('ecx',actual_after[1]);model.reg('edx',actual_after[2]);model.undefined_flag_domain={}")
    one("eq(derived['CPU_before'],event['CPU_before_projected'],'Whole projected instruction-entry CPU '+str((phase,index,hex(derived['PC']))))", "eq(F.project(derived['CPU_before'],derived['undefined_flags_before']),F.project(event['CPU_before_projected'],derived['undefined_flags_before']),'Whole source-defined instruction-entry CPU '+str((phase,index,hex(derived['PC']))))")
    one("eq(derived['CPU_after'],event['CPU_after_projected'],'Whole projected instruction-return CPU '+str((phase,index,hex(derived['PC']))))", "eq(F.project(derived['CPU_after'],derived['undefined_flags_after']),F.project(event['CPU_after_projected'],derived['undefined_flags_after']),'Whole source-defined instruction-return CPU '+str((phase,index,hex(derived['PC']))))")
    one("joins.append(dict(phase=phase,index=index,PC=derived['PC'],next_PC=derived['next_PC'],CPU_before=derived['CPU_before'],CPU_after=derived['CPU_after'],operands=operands));counts['whole_projected_CPU_sides']+=2;counts['literal_actual_provider_instructions']+=1", "joins.append(dict(phase=phase,index=index,PC=derived['PC'],next_PC=derived['next_PC'],CPU_before=derived['CPU_before'],CPU_after=derived['CPU_after'],actual_CPU_before=event['CPU_before_projected'],actual_CPU_after=event['CPU_after_projected'],undefined_flags_before=derived['undefined_flags_before'],undefined_flags_after=derived['undefined_flags_after'],operands=operands));counts['whole_projected_CPU_sides']+=2;counts['literal_actual_provider_instructions']+=1;counts['architectural_undefined_flag_projected_sides']+=int(bool(derived['undefined_flags_before']))+int(bool(derived['undefined_flags_after']))")
    one("pin(__file__);pin(M.I.__file__);pin(sys.executable)","pin(__file__);pin(M.I.__file__);pin(sys.executable);pin(R/'tools/m4-formatting-source/prepare_trace_comparison_v2.py');pin(R/'tools/m4-formatting-source/compare_trace.py')")
    one("reader_closed=True,generic_formatter_closed=False", "reader_closed=True,original_undefined_flags='Only current source-dominated logical/shift undefined bits; exact source cause/lifetime retained, literal representatives unchanged',generic_formatter_closed=False")
    q=p.with_name('compare_trace_v2.py');assert not q.exists();q.write_text(source)
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
    files={str(x.resolve()):sha(x)for x in(p,q,Path(__file__),R/'tools/m4-formatting-source/flag_domain.py')}
    report=dict(passed=True,scope='Additive bounded current architectural undefined flag lifetime policy; no source state or observed values changed',source=str(q),source_sha256=sha(q),files=files)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
