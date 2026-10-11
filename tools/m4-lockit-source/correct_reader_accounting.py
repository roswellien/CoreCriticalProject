"""Add the separately hashed raw canonical index to code-derived byte totals."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prior=ROOT/'reports/m4-lockit-source/reader-efficiency-plan-r1/report.json'
d=json.loads(prior.read_bytes());assert hashlib.sha256(prior.read_bytes()).hexdigest()=='fefd965c57cdd12e66361359bc6b49af727ca777cdd0e9b8272c1e9df027d1a3'
out=ROOT/'reports/m4-lockit-source/reader-efficiency-plan-r2';assert not out.exists();out.mkdir()
levels=[]
for row in d['levels']:
 row=dict(row);row['mandatory_DirectSet_open_hash_bytes']+=row['index_bytes'];levels.append(row)
a=dict(d['accounting']);a['formula']='For each current DirectSet open: 2*A + 2*P + I SHA input bytes, excluding tiny manifest/receipt hashes; I is the separate raw canonical index SHA pass in CaptureBundle. Eager logical payload copies remain 2*P.'
total=sum(r['mandatory_DirectSet_open_hash_bytes']for r in levels)
a['both_native_levels_one_consumer_open_hash_bytes']=total;a['both_native_levels_one_consumer_open_hash_GiB']=total/2**30
a['three_native_consumers_open_hash_bytes']=3*total;a['three_native_consumers_open_hash_GiB']=3*total/2**30
a['root_structural_native_hash_bytes_from_code']+=sum(r['index_bytes']for r in levels)
a['root_structural_native_hash_GiB_from_code']=a['root_structural_native_hash_bytes_from_code']/2**30
a['root_structural_formula']='O0: 7*A0+2*P0+I0 (opening2 full archives plus one index, after-level stability2, O2-stage watch/verify3); O2: 3*A2+2*P2+I2 (opening2 plus one index, final stability1).'
correction='''# Accounting correction

The independent reviewer identified the additional explicit SHA of raw_index inside CaptureBundle. The earlier 2*A+2*P totals were lower bounds: exact code accounting for opening adds I, the sum of canonical index bytes. This correction excludes tiny manifest/receipt hashes and semantic per-access reads. It changes no reader proposal or implementation, and still makes no measured disk-I/O or elapsed-speedup claim. The lazy proposal retains this explicit index validation.
'''
(out/'correction.md').write_text(correction,encoding='utf-8')
inputs=[prior,ROOT/'reports/m4-lockit-source/reader-efficiency-plan-r1/proposal.md',ROOT/'tools/m4-pipeline/capture_bundle.py',Path(__file__),out/'correction.md']
report=dict(passed=True,scope='Additive code-derived SHA accounting correction only; no payload read, no reader or consumer change',prior_report=str(prior),prior_report_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),correction='Include separately hashed raw canonical index: +I per DirectSet open',levels=levels,accounting=a,native_executed=False,initializer_credit=False,files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs})
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),accounting=a),indent=2))
