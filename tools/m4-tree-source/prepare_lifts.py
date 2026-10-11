"""Additive reuse of the accepted literal lifting pipeline; preserve its source."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
def main():
    source=ROOT/'tools/m4-lockit-source/lift.py'
    raw=source.read_text()
    substitutions=[
        ("ROOT/'reports/m4-lockit-source'", "ROOT/'reports/m4-tree-source'"),
        ("ROOT/'reports/m4-lockit-source/recovery-r1'", "ROOT/'reports/m4-tree-source/recovery-r1'"),
        ("REC_SHA='25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d'", "REC_SHA='81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4'"),
        ("REC/'fs-roots.json'", "REC/'FS-frame-contracts.json'"),
        ("root_count=4", "root_count=1"),
    ]
    for old,new in substitutions:
        assert old in raw, old
        raw=raw.replace(old,new)
    raw=raw.replace('All accepted120 bodies remain unchanged; lift10 additive literal entries only.', 'All accepted124 bodies remain unchanged; lift eight physical tree entries.')
    target=ROOT/'tools/m4-tree-source/lift.py'
    assert not target.exists()
    target.write_text(raw)
    out=ROOT/'reports/m4-tree-source/lift-preparation-r1'
    assert not out.exists()
    out.mkdir(parents=True)
    files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(source,target,Path(__file__))}
    report=dict(passed=True,source_tool=str(source),adapted_tool=str(target),substitutions=substitutions,files=files,
                scope='Literal lift pipeline adaptation only; no native execution credit')
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':main()
