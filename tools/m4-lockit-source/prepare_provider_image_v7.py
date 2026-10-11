"""Prevent inherited numeric cp result from shadowing the physical PE image."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'tools/m4-lockit-source';paths=[Path(__file__)]
for stem in ('connected','provider124'):
 prior=BASE/f'compare_{stem}_v6.py';out=BASE/f'compare_{stem}_v7.py';assert not out.exists()
 s=prior.read_text();assert s.count('cp=PE.PEImage(provider)')==1
 s=s.replace('cp=PE.PEImage(provider)','physical_provider_image=PE.PEImage(provider)').replace('cp.sections','physical_provider_image.sections').replace('cp.image_base','physical_provider_image.image_base')
 out.write_text(s);paths.extend((prior,out))
receipt=ROOT/'reports/m4-lockit-source/image-preparation-r1';assert not receipt.exists();receipt.mkdir()
(receipt/'report.json').write_text(json.dumps(dict(passed=True,scope='Comparer preparation only: distinct physical provider PE image name; inherited numeric cp result untouched; no candidate or source semantic change',native_executed=False,initializer_credit=False,files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((receipt/'report.json').read_bytes()).hexdigest())))
