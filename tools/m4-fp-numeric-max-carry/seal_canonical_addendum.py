"""Additive final-worker closure; the first candidate seal stays immutable."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();pins={}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or actual==h,(str(p),h,actual);assert str(p) not in pins or pins[str(p)]==actual;pins[str(p)]=actual;return actual
prior=BASE/'author-canonical-review-r1';control=BASE/'canonical-worker-controls-r1'
assert sha(prior/'report.json')=='624cedf34d980780016afac8de7234e9d3aa8cd29269c82f644caff276506ae7'
assert sha(prior/'pins.json')=='e1beea2b51f3059897da62bc2aec85832a12ff5cdd19fd767cdfa8b3353c7f10'
for directory in (prior,control):
 bind(directory/'report.json');bind(directory/'pins.json')
 for p,h in json.loads((directory/'pins.json').read_text())['files'].items():bind(p,h)
d=json.loads((control/'report.json').read_text());assert d['passed'] and d['worker_denials']==34 and d['actual_publisher_preservation_checks']==4 and d['recipe_no_mutation_controls']==3
assert len(d['rows'])==39 and sum(r['exit_code']==1 for r in d['rows'])==37
literal=[]
for p in (ROOT/'tools/m4-fp-numeric-max-carry/check_canonical_worker.py',Path(__file__).resolve()):
 q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=bind(p);bind(q,h);literal.append(dict(original_path=str(p),preserved_path=str(q),sha256=h))
report=dict(passed=True,scope='Additive final native worker/publisher/fresh recipe causal controls; candidate source and numeric semantics unchanged',prior_author_report=str(prior/'report.json'),prior_author_sha256=sha(prior/'report.json'),prior_pins_sha256=sha(prior/'pins.json'),prior_bindings=5346,control_report=str(control/'report.json'),control_report_sha256=sha(control/'report.json'),control_pins_sha256=sha(control/'pins.json'),counts=dict(worker_denials=34,publisher_existing_output_and_stage=4,early_no_mutation_recipe_report_or_build_collision=3),literal_sources=literal,acceptance='Author candidate sealed, separate independent review pending; no connected27/full startup admission',frozen_sources_or_runtime_changed=False,original_executed=False,whole_M4_complete=False)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':dict(sorted(pins.items()))},indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),bindings=len(pins))))
