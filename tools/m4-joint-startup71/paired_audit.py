"""Independent bounded audit of retained raw paired differences, no projections."""
from pathlib import Path
import collections,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup71-root'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def read(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return json.loads(p.read_bytes())
 base=ROOT/'reports/m4-strings-source/paired-initialization-policy-r2'
 r=read(base/'report.json','1f454d420cb4bad8ec8cbe6aa0466fc4b516aa71abc1236afa53e6f5210ce047');assert r['passed']and not r['blanket_page_mask']
 contract=read(ROOT/'reports/m4-strings-source/recovery-r7/instruction-contracts.json','e1a4a4e2a6f1d55b5a1a94b10254202e88304e67dfbedd77326e72f0986e97a9')
 order={x['entry']:i for i,x in enumerate(contract['selected_order'])};assert len(order)==71
 fields={x['objects'][0]['address']+4:order[x['entry']]for x in contract['roots']if x['entry']!=0x4e6a10};assert len(fields)==16
 iats={0x5bb4fc,0x5bb52c,0x5bb530,0x5bb6dc,0x5bb670};assert set(r['owning_IAT_projection_addresses'])==iats
 observations=read(base/'paired-observations.json');assert len(observations)==852;counts=collections.Counter();identities=set()
 for row in observations:
  phase=row['phase'];assert order[row['entry']]==phase;identities.add((row['level'],row['sequence'],phase));assert len(row['nonstack_pages'])==62
  for key in ('FX_before_differences','FX_after_differences'):
   # Stronger than the inherited hardwarefx projection: in these captures
   # metadata6..23 is equal too. Only measured capability-mask bytes differ.
   assert all(d['offset']in(28,29,30)for d in row[key]);counts['raw_FX_pairs_with_only_capability_differences']+=1
  for page in row['nonstack_pages']:
   assert page['page']!=0x20001000;assert page['side']in('before','after');allowed=set()
   for address in iats:
    if address&~4095==page['page']:allowed.update(range(address,address+4))
   for address,start in fields.items():
    if (phase>start or(phase==start and page['side']=='after'))and address&~4095==page['page']:allowed.update(range(address,address+4))
   if phase>order[0x49d5c0]or(phase==order[0x49d5c0]and page['side']=='after'):allowed.add(0x6099e8)
   assert len(page['original_sha256'])==len(page['native_sha256'])==64
   assert all(0<=d['offset']<4096 and page['page']+d['offset']in allowed for d in page['differences'])
   assert bool(page['differences'])==(page['original_sha256']!=page['native_sha256']);counts['raw_whole_page_difference_scopes']+=1
 assert len(identities)==852 and {x[0]for x in identities}=={'O0','O2'}
 for p,h in r['files'].items():
  # Do not reopen large immutable archives for this observation-scope audit.
  # Their full physical checks remain required in the parent and root gate.
  if not str(p).endswith('.mwb'):assert sha(p)==h;pins[str(p)]=h
 pins[str(Path(__file__).resolve())]=sha(__file__)
 value=dict(passed=True,scope='Independent retained raw difference bounds and stronger raw hardware metadata check; parent performs full archive/source/owner comparisons',counts=dict(counts),source_duplicate_pointer_fields=sorted(fields),owning_IAT_projection_addresses=sorted(iats),indeterminate_relation_address=0x6099e8,raw_archives_rehashed=False,parent_full_archive_validation_required=True,blanket_page_mask=False,whole_game_alias_liveness=False,files=pins)
 (out/'report.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
