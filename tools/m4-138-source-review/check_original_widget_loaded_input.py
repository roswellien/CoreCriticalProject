"""Bounded original42 literal ledger/input disjointness, no endpoint masks."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prep=read(R/'reports/m4-tree-review/loaded-input138-preparation-r1/report.json','a7fa318f52c5bd38a1500b39107f331c601e33c8bf951a90db189fc82f21afbb')
 wp=R/'reports/m4-startup138-original/widget-complete-source-r1/report.json'
 widget=read(wp,'4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684')
 assert prep['passed']and widget['passed']and not widget['AFTER_machine_or_memory_seed']
 assert widget['files'][str((R/'reports/m4-startup138-original/original-validation-r3/report.json').resolve())]==prep['original_validation_sha256']
 p=wp.parent/'source-derivations.json';rows=read(p,widget['files'][str(p.resolve())])
 assert len(rows)==42 and {(x['sequence'],x['root'])for x in rows}=={(s,r)for s in range(6)for r in(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)}
 counts=[]
 for row in rows:
  ledger=row['source_accesses'];assert ledger
  assert all(len(v)==5 and v[3]>0 for v in ledger)
  assert not any(v[1]<0x78147000 and v[1]+v[3]>0x78145000 for v in ledger),'Reached widget source touches loaded provider RW/IAT'
  counts.append(dict(sequence=row['sequence'],root=row['root'],entire_source_operand_rows=len(ledger),loaded_RW_IAT_consumed_operands=0))
 pin(__file__);pin(sys.executable)
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All42 current original literal widget operand ledgers are disjoint from complete MSVCP loaded RW/IAT pages; native/allphase endpoint carry remains separate',original_source_sha256=sha(wp),loaded_input_preparation_sha256=sha(R/'reports/m4-tree-review/loaded-input138-preparation-r1/report.json'),cases=counts,source_operands_checked=sum(x['entire_source_operand_rows']for x in counts),archive_reader_opened=False,endpoint_carry_acceptance=False,initializer_credit=0,files=pins),indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1])
