"""Additive proof-name correction, retaining failed reader and immutable capture."""
from pathlib import Path
import ast,hashlib,json
T=Path(__file__).resolve().parent
def emit(old,new,transform):
 p=T/new;assert not p.exists();s=transform((T/old).read_text());ast.parse(s);p.write_text(s);return hashlib.sha256(p.read_bytes()).hexdigest()
def source(s):
 old="index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)"
 assert s.count(old)==1
 s=s.replace(old,"checkpoint_index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,checkpoint_index)")
 old='actual=C.checkpoint(a,index,checkpoint_name)';assert s.count(old)==1
 s=s.replace(old,'actual=C.checkpoint(a,checkpoint_index,checkpoint_name)')
 old='   finally:a.close()';assert s.count(old)==1
 return s.replace(old,'   finally:a.close();del a')
def bind(s):return s.replace('connected-native-source-r1','connected-native-source-r2')
pins={}
pins['compare_connected_v7.py']=emit('compare_connected_v6.py','compare_connected_v7.py',source)
for old,new in [('compare_FS_policy_v4.py','compare_FS_policy_v5.py'),('compare_paired_policy_v6.py','compare_paired_policy_v7.py'),('compare_owned_policy_v3.py','compare_owned_policy_v4.py'),('seal_indirect_source_v2.py','seal_indirect_source_v3.py'),('seal_receipts.py','seal_receipts_v2.py')]:
 pins[new]=emit(old,new,bind)
print(json.dumps(pins))
