"""Retain genuinely uncaptured source page as a domain gap, not a scalar input."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=D/'prefix_prerequisites.py';q=D/'prefix_prerequisites_v2.py'
 if q.exists():raise ValueError('Fresh additive source')
 s=p.read_text();a="  raw=value(address);observations.append"
 b="  if address&~4095 not in prep['observed_pages']:\n   observations.append(dict(address=address,role=role,observed=False,actual_scalar_unavailable=True,required_new_BEFORE_page=address&~4095,value_supplied_to_execution=False));continue\n  raw=value(address);observations.append"
 if s.count(a)!=1:raise ValueError('Exact missing-page domain hunk')
 s=s.replace(a,b,1).replace("row.get('control_target')==0x5abd26","row['operands']=='0x5abd26'")
 s=s.replace('observed_scalar_inputs=len(observations)','observed_scalar_inputs=sum(not v.get(\'actual_scalar_unavailable\',False)for v in observations),missing_actual_scalar_pages=sum(v.get(\'actual_scalar_unavailable\',False)for v in observations)')
 s=s.replace("pin(__file__)\n", "pin(__file__);pin(R/'tools/m4-remaining-service-source/derive_prefix_v2.py');pin(R/'tools/m4-remaining-service-source/prefix_prerequisites.py','"+sha(p)+"')\n")
 q.write_text(s);print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
