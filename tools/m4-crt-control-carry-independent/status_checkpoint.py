"""Preserve updated milestone docs after bounded carry acceptance only."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);assert want is None or h==want,str(p);PINS[str(p)]=h;return p
def required(text):
    rows=[line.split('|')[1:3] for line in text.splitlines() if re.match(r'^\| M4-\d\d \|',line)]
    assert len(rows)==12;return rows
def main():
    before=ROOT/'reports/m4-startup/status-before-control-carry-review-r1';out=ROOT/'reports/m4-startup/status-after-control-carry-review-r1';assert not out.exists()
    for p,h in json.loads(pin(before/'pins.json').read_text())['files'].items():pin(p,h)
    evidence=ROOT/'reports/m4-crt-control-carry/independent-source-r1/closure-r3';pin(evidence/'report.json','e29781d5f527ef0740f2363b5382948c40b00816cf4656fbad512bdacd4b8ca4');pin(evidence/'pins.json','f6929a2ebee1d4486376e777e327c41be020459e6e452276217acced3a1cc906')
    bindings=json.loads((evidence/'pins.json').read_text())['files'];assert len(bindings)==5857
    for p,h in bindings.items():pin(p,h)
    doc=ROOT/'docs/m4-startup-plan.md';assert required(doc.read_text())==required((before/doc.name).read_text())
    register=(ROOT/'docs/project-milestones.md').read_text();old=(before/'project-milestones.md').read_text()
    line=next(x for x in register.splitlines() if x.startswith('| M4 |'));prior=next(x for x in old.splitlines() if x.startswith('| M4 |'))
    assert line.split('|')[-2]==prior.split('|')[-2] and 'Active' in line
    assert '118' in doc.read_text() and '26' in doc.read_text()
    out.mkdir();documents=[]
    for name in ('project-milestones.md','roadmap.md','m4-startup-plan.md','m4-crt-control-carry-review.md'):
        src=pin(ROOT/'docs'/name);target=out/name;target.write_bytes(src.read_bytes());pin(target);documents.append(dict(path=str(src),sha256=sha(src),literal_snapshot=str(target)))
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py');pin(Path(__file__))
    report=dict(passed=True,scope='Bounded control-result carry prerequisite acceptance recorded; full M4 remains active',documents=documents,unchanged_required_proof_columns=12,unchanged_M4_definition_of_done=True,independent_physical_bindings_rehashed=len(bindings),original_phases=648,native_phases=1296,independent_compiled_checks=2016,independent_compiled_scenarios=84,selected_initializer_roots=26,remaining_outside_connected_gate=118,whole_M4_complete=False)
    rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(rp),docs=len(documents),required_proofs_unchanged=12,M4_complete=False)))
if __name__=='__main__':main()
