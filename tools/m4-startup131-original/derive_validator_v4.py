from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
base=T/'mfc_phase_v2.py';p=T/'mfc_phase_v3.py';assert not p.exists();s=base.read_text()
old=" and after[0]==1,'Actual initializer return and full caller framing'";assert s.count(old)==1
s=s.replace(old,",'Actual initializer return and full caller framing; root EAX retained observed and derived later from literal root tail'")
p.write_text(s)
base2=T/'validate_v3.py';p2=T/'validate_v4.py';assert not p2.exists();s=base2.read_text();assert s.count('from mfc_phase_v2 import')==1;s=s.replace('from mfc_phase_v2 import','from mfc_phase_v3 import');assert s.count("/'mfc_phase_v2.py'")==1;s=s.replace("/'mfc_phase_v2.py'","/'mfc_phase_v3.py'");p2.write_text(s)
q=T/'validator-v4-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),validator_generated=str(p2),validator_generated_sha256=hashlib.sha256(p2.read_bytes()).hexdigest(),failed_validation=str(R/'reports/m4-startup131-original/validation-r1/report.json'),failed_validation_sha256=hashlib.sha256((R/'reports/m4-startup131-original/validation-r1/report.json').read_bytes()).hexdigest(),change='Remove unsupported helper-EAX1 assumption at enclosing initializer root return. Exact root caller ESP/PC and complete actual CPU retained; subsequent current literal source must derive full root tail CPU. Genuine current EAX7365A4 also matches historical chronological source3, not used as a seed.',worker_changed=False,writer_rerun=False),indent=2)+'\n')
print(p2)
