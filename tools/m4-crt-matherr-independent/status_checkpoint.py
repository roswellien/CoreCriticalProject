"""Freeze milestone documentation after isolated matherr acceptance."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PINS={}

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);assert want is None or h==want,str(p)
    assert str(p) not in PINS or PINS[str(p)]==h
    PINS[str(p)]=h;return p

def requirements(text):
    rows=[line.split('|')[1:3] for line in text.splitlines() if re.match(r'^\| M4-\d\d \|',line)]
    assert len(rows)==12;return rows

def main():
    before=ROOT/'reports/m4-startup/status-before-matherr-review-r1';out=ROOT/'reports/m4-startup/status-after-matherr-review-r1';assert not out.exists()
    for p,h in json.loads(pin(before/'pins.json').read_text())['files'].items():pin(p,h)
    evidence=ROOT/'reports/m4-crt-matherr/independent-final-closure-r5'
    report=json.loads(pin(evidence/'report.json','dc6a4a38749637385fcf45870e36f62e3cdfbf7d697e5efb27713780da4a3ead').read_text())
    assert report['passed'] and not report['whole_M4_complete']
    files=json.loads(pin(evidence/'pins.json','3dd4abd4ef55a1eaaccbff8293dfe4f6763835fdc5ab87a4994160e4ac14830b').read_text())['files'];assert len(files)==1437
    for p,h in files.items():pin(p,h)
    plan=(ROOT/'docs/m4-startup-plan.md').read_text();assert requirements(plan)==requirements((before/'m4-startup-plan.md').read_text())
    register=(ROOT/'docs/project-milestones.md').read_text();old=(before/'project-milestones.md').read_text()
    line=next(x for x in register.splitlines() if x.startswith('| M4 |'));prior=next(x for x in old.splitlines() if x.startswith('| M4 |'))
    assert line.split('|')[-2]==prior.split('|')[-2] and 'Active' in line
    assert '118' in plan and '26' in plan and 'm4-crt-matherr-review.md' in plan
    assert 'independent acceptance remain pending' not in plan
    out.mkdir();documents=[]
    for name in ('project-milestones.md','roadmap.md','m4-startup-plan.md','m4-crt-matherr-review.md'):
        src=pin(ROOT/'docs'/name);target=out/name;target.write_bytes(src.read_bytes());pin(target);documents.append(dict(path=str(src),sha256=sha(src),literal_snapshot=str(target)))
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py');pin(Path(__file__))
    result=dict(passed=True,scope='Isolated math-error registration accepted; no callback execution or full CRT/M4 credit',documents=documents,unchanged_required_proof_columns=12,unchanged_M4_definition_of_done=True,independent_physical_bindings_rehashed=len(files),original_records=1536,native_records=3072,independent_compiled_assertions=462,independent_compiled_scenarios=48,selected_initializer_roots=26,remaining_outside_connected_gate=118,whole_M4_complete=False)
    rp=out/'report.json';rp.write_text(json.dumps(result,indent=2)+'\n');pin(rp);(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(rp),bindings=len(PINS),M4_complete=False)))

if __name__=='__main__':main()
