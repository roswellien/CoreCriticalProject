"""Additive validation repair: FNSTENV metadata is separate from raw FXSAVE."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p)
 if h is not None and h!=v:raise ValueError('Exact input '+str(p))
 files[str(p)]=v;return p
base=pin(R/'tools/m4-hypot-original/validate.py')
pin(R/'reports/m4-hypot-original/prefix-validation-r1/report.json','51888867b7a7ca9482816c39733f8803834359c034dfba33f8bfc5987741297a')
pin(R/'reports/m4-hypot-original/prefix-execution-r1/report.json','03683928949cbfcecbceda901e5f09d3a6449eb04add176582746d4d06e7f2d0')
pin(R/'reports/m4-hypot-original/root-preflight-r2/report.json','cc9f62f16ce9b945d9d8b0a0038d07c93aa944d1f5f4841831c2a804cb414680')
old="words(env1,12)[0]==words(fx1,8)[0]==0x4b5905 and words(env1,20)[0]==words(fx1,16)[0]==0x60b2e8"
new="words(env1,12)[0]==0x4b5905 and words(env1,20)[0]==0x60b2e8"
text=base.read_text();assert text.count(old)==1
target=R/'tools/m4-hypot-original/validate_v2.py';assert not target.exists();target.write_text(text.replace(old,new));pin(target)
out=R/'reports/m4-hypot-original/validation-preparation-r2';assert not out.exists();out.mkdir(parents=True)
pin(__file__);pin(sys.executable)
report=dict(passed=True,scope='Exact one-hunk repair of metadata join; genuine FNSTENV28 FIP/FDP is checked against final literal FSTP, raw FXSAVE512 remains physically retained without replacing its zero metadata fields',hunks=1,writer_unchanged=True,numerical_predictions_added=False,source_after_seed=False,FXSAVE_metadata_canonical_source_relation_claimed=False,files=files)
p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
