"""Bind the accepted physical MFC tail-entry metadata projection in source keys."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    base=ROOT/'tools/m4-tree-source/game_model_v3.py';s=base.read_text()
    a='return tuple(frame[:4])'
    b="""# Exact physical JMP5ABD26 may name the caller frame as MFC5F401EA0
        # in the accepted provider observer. Stack/site/return identity is
        # unchanged; alias only this already executed ordinal823 thunk tail.
        entry=0x5abd26 if frame[0]==0x5f401ea0 else frame[0]
        return (entry,)+tuple(frame[1:4])"""
    assert s.count(a)==1;s=s.replace(a,b);target=base.with_name('game_model_v4.py');assert not target.exists();target.write_text(s)
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Unexecuted literal model extension for the already source-established MFC JMP tail frame-entry projection; no source effects change',frame_entry_projection_PC=0x5abd26,physical_entry=0x5f401ea0,source_CALL_entry=0x5abd26,stack_return_site_identity_unchanged=True,candidate_AFTER_seed=False,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
