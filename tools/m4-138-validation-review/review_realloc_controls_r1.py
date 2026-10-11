"""Independent exact-inverse ordinary controller/validator review."""
from pathlib import Path
import hashlib,json,ast
R=Path(__file__).resolve().parents[2];P={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('payload.bin','index.json','transport.json');v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;P[str(p)]=v;return p
base=R/'reports/m4-startup138-original';p=pin(base/'realloc-controller-validation-preparation-r1/report.json','811c1bcf6736e02663cd41ec847c8d5ff12e92659f88e6c2e4ba0cc71827f4b0');report=json.loads(p.read_bytes());assert report['passed']and report['exact_inverse_restores_parents']and report['helper_byte_identical']
for path,h in report['files'].items():pin(path,h)
for name,deltas in report['changes'].items():
 source=R/'tools/m4-startup138-original'/name;t=source.read_text();ast.parse(t)
 for d in reversed(deltas):
  pos=d['position'];assert t[pos:pos+len(d['new'])]==d['new'];t=t[:pos]+d['old']+t[pos+len(d['new']):]
 parent=source.with_name('run_v2.py'if name.startswith('run_')else 'validate_v3.py');assert t==parent.read_text();pin(parent)
helper=R/'tools/m4-startup138-original/widget_phase_realloc_v1.py';assert helper.read_bytes()==(helper.with_name('widget_phase_v3.py')).read_bytes()
v=(R/'tools/m4-startup138-original/validate_realloc_v1.py').read_text();assert "rw[9]==rw[19]==0 and rw[25]==0x78011c2d"in v and "rw[14]==rw[4]+20"in v and "initial[:len(registry_before_backing)]==registry_before_backing"in v
preflight=pin(base/'realloc-controls-preflight-r1/report.json','f3abb4730a8e20e0cc5f24d85ee3b4537e159b4527fab174e1688092bb20c5cd');controls=json.loads(preflight.read_bytes());assert controls['passed']
pin(__file__);out=R/'reports/m4-138-validation-review/realloc-controls-review-r1';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,exact_inverse_restores_parent_validator_and_writer=True,widget_helper_byte_identical=True,inherited_allphase_source_resource_semantic_observation_checks_retained=True,realloc_scope='Successful kind3 typed API schema, original zeroPC fields, exact78011c2dreturn/stdcall, complete initial backing before guest writes, own old registry prefix preserved',limitations=['Heap identity, source-driven growth request and result ownership are later literal source gates; this validator exports observations and grants no source equivalence.','New observer addresses require current exact physical compiled transition attribution; old diagnostic addresses cannot be reused for continuity across phase13/14.'],source_model_equivalence=False,initializer_credit=0,archive_reader_opened=False,payload_reader_opened=False,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
