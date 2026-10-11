"""Bounded all-hook overlap diagnosis for a frozen failed original trace worker."""
from pathlib import Path
import hashlib, json, re, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,str(p);PINS[str(p)]=v;return p
def main(name):
    prep=R/'reports/m4-hypot-original/trace-preparation-r6'
    p=pin(prep/'report.json','4328b1b5a0672c829cc6e5a4e8a2f6ccc2dae9ced3924085ea9598307e9ad56f')
    source=pin(prep/'reference.cpp').read_text();kernel=pin(prep/'hypot_trace.hpp').read_text()
    rows=json.loads(pin(prep/'trace-instruction-contracts.json').read_bytes())['instructions']
    families=[];allrows=[]
    for typ,name,count in [('FsHook','fs_hooks',42),('NullHook','null_hooks',2),('VtableHook','vtable_hooks',6),('LockitHook','lockit_hooks',4)]:
        match=re.search(r'const std::array<'+typ+r',([0-9]+)>\s*'+name+r'\{\{(.*?)\}\};',source)
        assert match and int(match[1])==count,'Actual finite active source table '+name
        pattern=r'\{(0x[0-9a-f]+),([0-9]+,)?([0-9]+,)?&([A-Za-z_0-9]+),\{([^{}]+)\}\}'
        hooks=[]
        for pc,size,kind,entry,raw in re.findall(pattern,match[2]):
            b=bytes(int(x.strip(),0)for x in raw.split(','));pc=int(pc,16)
            assert typ=='NullHook' or int(size[:-1])==len(b)
            affected=[dict(pc=x['pc'],width=x['width'],bytes_hex=x['bytes_hex'],mnemonic=x['mnemonic'])for x in rows if pc<x['pc']+x['width']and pc+len(b)>x['pc']]
            hooks.append(dict(family=name,PC=pc,size=len(b),entry=entry,raw_hex=b.hex(),overlapping_instructions=affected))
        assert len(hooks)==count,'Every actual source hook row accounted'
        families.append(dict(family=name,count=count,overlapping_hooks=sum(bool(h['overlapping_instructions'])for h in hooks)));allrows+=hooks
    overlaps=[x for x in allrows if x['overlapping_instructions']]
    assert [(x['family'],x['PC'])for x in overlaps]==[('null_hooks',0x78001390),('null_hooks',0x78001420)]
    for pc,size,label in [(0x410a80,5,'actual endpoint broker'),(0x5ac3ec,5,'source sentinel terminal broker')]:
        assert not any(pc<x['pc']+x['width']and pc+size>x['pc']for x in rows),label
    stderr=pin(R/'reports/m4-hypot-original/trace-execution-r1/run/stderr.bin').read_text()
    assert 'Original124 producerstart' in stderr and 'Exact physical source first opcode before trace' in stderr and 'checkpoints=0' in stderr
    assert 'require(*b==p.opcode' in kernel and '*b=0xcc' in kernel and kernel.index('require(*b==p.opcode')<kernel.index('*b=0xcc')<kernel.index('hypot_trace_active=1')
    pin(R/'reports/m4-hypot-original/trace-execution-r1/report.json','ccd8d6f7e00d12113384b4b6fd17d32b568ced390109e7c01be57ebcbcc451a0')
    pin(__file__);pin(sys.executable)
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
    artifact=out/'all-active-hooks.json';artifact.write_text(json.dumps(allrows,indent=2)+'\n');pin(artifact)
    report=dict(passed=True,diagnostic_only=True,failed_preparation_sha256=sha(p),failed_execution_sha256='ccd8d6f7e00d12113384b4b6fd17d32b568ced390109e7c01be57ebcbcc451a0',families=families,actual_source_hooks=54,remaining_source_overlap_hooks=2,first_sorted_candidate_mismatch_PC=0x78001390,first_mismatch_not_observed_directly=True,root_source_steps_observed=0,producer_bootstrap_reached=True,partial_breakpoints_on_early_assertion_possible=True,secondary_access_violation_cause_unmeasured=True,recommendation='Remove both exact NULL-free source hooks from this trace-only worker; preserve strict assertion with PC/expected/actual diagnostic and validate all source bytes before patching any. Failed worker/code/receipt remain frozen. Actual refusal is observed; first specific PC and secondary fault cause are source-derived diagnostics until a fresh run.',archive_reader_opened=False,guest_executed=False,acceptance_credit=0,files=PINS)
    target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(target),sha256=sha(target),overlapping_hooks=2)))
if __name__=='__main__':main(sys.argv[1])
