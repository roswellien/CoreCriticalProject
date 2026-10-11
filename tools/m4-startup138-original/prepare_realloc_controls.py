"""Freeze current realloc writer/strict validator after independent prelaunch."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
PREP='9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161';BUILD='da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'
OLDPREP='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2';OLDBUILD='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69';OLDREVIEW='efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name,review_path,review_hash):
 out=R/'reports/m4-startup138-original'/name;assert not out.exists();pins={};deltas={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name not in('payload.bin','index.json','transport.json');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 bp=R/'reports/m4-startup138-original/build-r5/build.json';b=json.loads(pin(bp,BUILD).read_text(encoding='utf-8-sig'));assert b['passed']and b['preparation_sha256']==PREP
 rp=pin(review_path,review_hash);q=json.loads(rp.read_text(encoding='utf-8-sig'));assert q['passed']and q['build_sha256']==BUILD and q['files'][str(bp.resolve())]==BUILD and q['files'][str(Path(b['worker']).resolve())]==b['worker_sha256']
 for p,h in q['files'].items():pin(p,h)
 pin(Path(b['preparation'])/'report.json',PREP);pin(Path(b['worker']),b['worker_sha256']);pin(rp.parent/'compiled-observers.json')
 def derive(filename,target_name,extra):
  base=pin(R/'tools/m4-startup138-original'/filename);text=base.read_text();changes=[]
  def one(old,new,count=1):
   nonlocal text
   assert text.count(old)==count,(filename,old[:90],text.count(old));positions=[];start=0
   for _ in range(count):
    pos=text.index(old,start);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):];start=pos+len(new)
  for old,new in(('build-r4/build.json','build-r5/build.json'),(OLDBUILD,BUILD),(OLDPREP,PREP)):
   one(old,new,text.count(old))
  if filename=='run_v2.py':
   one('preparation-r7/report.json','preparation-r8/report.json');one('Only exact final preparation7','Only exact final preparation8')
   one(' out=BASE/name'," if preflight.resolve()!=R/"+repr(str(rp.relative_to(R)).replace('\\','/'))+" or preflight_digest!="+repr(review_hash)+":raise ValueError('Only independently reviewed current realloc observer is admitted')\n out=BASE/name")
  else:
   one('reports/m4-tree-review/original138-prelaunch-r5/report.json',str(rp.relative_to(R)).replace('\\','/'))
   one(OLDREVIEW,review_hash);one('from widget_phase_v3 import','from widget_phase_realloc_v1 import');one("parent/'widget_phase_v3.py'","parent/'widget_phase_realloc_v1.py'")
   anchor="phaseowners=[];ledger=records.data(f'phase/{seq}/{phase}/api-ledger.bin');apicount=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];need(len(ledger)==apicount*104,'Actual complete provider API ledger')"
   addition="""
      registry_before=struct.unpack('<4I',records.data(f'phase/{seq}/{phase}/registry-before-meta.bin'));registry_before_backing=records.data(f'phase/{seq}/{phase}/registry-before-backing.bin')
      for ri in range(apicount):
       rw=struct.unpack_from('<26I',ledger,ri*104)
       if rw[24]!=3 or not rw[10]:continue
       need(rw[9]==rw[19]==0 and rw[25]==0x78011c2d and rw[21]==0 and all(rw[j]==rw[10+j]for j in(3,5,6,7))and rw[14]==rw[4]+20,'Actual named HeapReAlloc original shim ledger schema, exact source saved return and stdcall effect')
       size=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-initial/{ri}/size.bin'))[0];initial=records.data(f'phase/{seq}/{phase}/api-initial/{ri}/bytes.bin');need(rw[23]<=size<=1024 and len(initial)==size,'Full successful HeapReAlloc API-return backing before any guest writes')
       if rw[22]==registry_before[0]:need(initial[:len(registry_before_backing)]==registry_before_backing and size>=registry_before[2],'Exact complete old current registry prefix preserved at reallocation seam')
       counts['actual_HeapReAlloc_initial_full_backing_witnesses']+=1
"""
   one(anchor,anchor+addition.rstrip())
  extra(one)
  reverse=text
  for d in reversed(changes):
   pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
  assert reverse==base.read_text();ast.parse(text);target=base.with_name(target_name);assert not target.exists();target.write_text(text);pin(target);deltas[target_name]=changes
  return target
 # The observer keeps every inherited kind0 initial/final check. Kind3 facts
 # are authenticated centrally above and recorded independently, with no final
 # backing supplied as an initial witness.
 hp=pin(R/'tools/m4-startup138-original/widget_phase_v3.py');ht=hp.read_text();target=hp.with_name('widget_phase_realloc_v1.py');assert not target.exists();target.write_text(ht);assert target.read_text()==hp.read_text();pin(target)
 writer=derive('run_v2.py','run_realloc_v1.py',lambda one:None);validator=derive('validate_v3.py','validate_realloc_v1.py',lambda one:None)
 assert 'self.branch==\'original\'or selected(key)'in pin(R/'tools/m4-joint-startup131/paired_exports.py').read_text()
 pin(__file__);out.mkdir();report=dict(passed=True,scope='Unexecuted frozen realloc observer writer and strict original138 validator; all inherited checks retained',controller_path=str(writer),controller_sha256=sha(writer),validator_path=str(validator),validator_sha256=sha(validator),build_path=str(bp),build_sha256=BUILD,preparation_sha256=PREP,preflight_path=str(rp),preflight_sha256=review_hash,exact_inverse_restores_parents=True,helper_byte_identical=True,all_original_logical_files_exported=True,source_model_equivalence=False,archive_reader_opened=False,original_executed=False,initializer_credit=0,changes=deltas,files=pins);path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(path,sha(path))
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]),sys.argv[3])
