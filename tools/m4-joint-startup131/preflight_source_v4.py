"""Archive-free equivalence check of the proof-only boundary instrumentation."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
parent=ROOT/'tools/m4-joint-startup131/preflight_source_v2.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='579c21eda5402d260d48a13a5c10df281aab75813ac9b21155bdc7e53804185d'
text=parent.read_text();assert text.count('mfc_source_v2.py')==1
text=text.replace('mfc_source_v2.py','mfc_source_v3.py')
old="assert br['source_PCs']==e.normal_PCs and len(br['defined_flag_consumers'])==11 and all(c['all_consumers_defined']for c in br['defined_flag_consumers'])"
new=old+"\n  assert [r['PC']for r in e._snapshots]==list(M.BOUNDARIES) and all(len(bytes.fromhex(r['State_hex']))==3504 and len(bytes.fromhex(r['FX_hex']))==512 and len(bytes.fromhex(r['ENV28_hex']))==28 and len(bytes.fromhex(r['frame64_hex']))==64 for r in e._snapshots)\n  q=out/'proof-only-boundaries.json';q.write_text(json.dumps(e._snapshots,indent=2)+'\\n');pin(q)"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('pin(__file__);pin(sys.executable)',"pin(ROOT/'tools/m4-joint-startup131/preflight_source_v4.py');pin(ROOT/'tools/m4-joint-startup131/preflight_source_v2.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
