"""Record bounded command-line acceptance without weakening M4 requirements."""
import hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PINS = {}

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p, expected=None):
    p=Path(p).resolve(); got=sha(p)
    assert expected is None or got==expected,str(p)
    assert str(p) not in PINS or PINS[str(p)]==got
    PINS[str(p)]=got
    return p

def requirements(text):
    rows=[line.split('|')[1:3] for line in text.splitlines() if re.match(r'^\| M4-\d\d \|',line)]
    assert len(rows)==12
    return rows

def main():
    before=ROOT/'reports/m4-startup/status-before-commandline-review-r1'
    out=ROOT/'reports/m4-startup/status-after-commandline-review-r1'
    assert not out.exists()
    for p,h in json.loads(pin(before/'pins.json').read_text())['files'].items():
        pin(p,h)
    stages=[('independent-final-review-r1','28cc793ab1e27f6ef8dc31638ed2528a72495fd8ee3c3a524aa618dd820e2e8a','e91dff9f9f8a60a592199db061dd6df0b348d8f9153705f1f64941c80ec117de',2221),('independent-service-fp-r1','cef5844050cb7d3c9fd8a5d896b290bb4f64cd90b2f745d5f0b8d3448e61e5b8','ae23a363e5ec2e9f5bd0917fa9c3989d11b835dd7820dac442b653c3543df006',2224)]
    for name,rh,ph,count in stages:
        base=ROOT/'reports/m4-crt-commandline-native'/name
        report=json.loads(pin(base/'report.json',rh).read_text());assert report['passed'] and not report['whole_M4_complete']
        files=json.loads(pin(base/'pins.json',ph).read_text())['files'];assert len(files)==count
        for p,h in files.items():pin(p,h)
    fdiv=ROOT/'reports/m4-crt-fdiv/source-recovery-r1'
    pin(fdiv/'report.json','c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd');pin(fdiv/'pins.json','6b0327531d1932e19ee2376ff7bb2a41b1b6b8b20f27288e5f73dd24cbd7fa07')
    for p,h in json.loads((fdiv/'pins.json').read_text())['files'].items():pin(p,h)
    plan=(ROOT/'docs/m4-startup-plan.md').read_text()
    assert requirements(plan)==requirements((before/'m4-startup-plan.md').read_text())
    register=(ROOT/'docs/project-milestones.md').read_text()
    old=(before/'project-milestones.md').read_text()
    current=next(x for x in register.splitlines() if x.startswith('| M4 |'))
    previous=next(x for x in old.splitlines() if x.startswith('| M4 |'))
    assert current.split('|')[-2]==previous.split('|')[-2] and 'Active' in current
    assert '118' in plan and '26' in plan and 'registration leaf' in plan and 'pending' in plan
    out.mkdir();documents=[]
    for name in ('project-milestones.md','roadmap.md','m4-startup-plan.md','m4-crt-commandline-native-review.md'):
        p=pin(ROOT/'docs'/name);copy=out/name;copy.write_bytes(p.read_bytes());pin(copy)
        documents.append(dict(path=str(p),sha256=sha(p),literal_snapshot=str(copy)))
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py');pin(Path(__file__))
    report=dict(passed=True,scope='Bounded actual command-line writer accepted; fdiv static recovery only; complete M4 remains active',documents=documents,unchanged_required_proof_columns=12,unchanged_M4_definition_of_done=True,original_records=384,native_records=768,independent_compiled_checks=638,independent_compiled_scenarios=56,selected_initializer_roots=26,remaining_outside_connected_gate=118,matherr_independent_acceptance_pending=True,whole_M4_complete=False)
    rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp)
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(rp),bindings=len(PINS),M4_complete=False)))

if __name__=='__main__':main()
