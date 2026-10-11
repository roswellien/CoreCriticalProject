from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;base=T/'validate_v2.py';p=T/'validate_v3.py';assert not p.exists()
s=base.read_text();old="AFTER_machine_seed=False,allocation_null_path=False,Lockit_observation_scope=";assert s.count(old)==1
s=s.replace(old,"AFTER_machine_seed=False,allocation_null_path=False,reader_closed=True,reader_scope='Only fresh original131 capture in one bounded session; all DirectSet handles closed in finally',Lockit_observation_scope=")
p.write_text(s)
(T/'validator-v3-lineage.json').write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),change='Expose actual mandatory finally records.close in final receipt; no observation/validation predicate changed',reader_opened=False),indent=2)+'\n')
print(p)
