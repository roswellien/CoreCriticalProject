"""Full bounded physical named GDI-owner proof on existing ordinary subtrees."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();pins={};cases=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');k=str(p)
  if k not in pins:pins[k]=sha(p)
  assert h is None or pins[k]==h,k;return p
 def raw(p):return pin(p).read_bytes()
 sp=importlib.util.spec_from_file_location('controls_owner_header',pin(R/'tools/m4-138-controls-review/readiness.py'));header=importlib.util.module_from_spec(sp);sp.loader.exec_module(header)
 ep=R/'reports/m4-joint-startup138/context-controls-execution-r1/report.json';pin(ep,'43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863');e=header.header(ep)
 assert e['passed']and e['all_workers_terminal']and not e['archive_reader_opened']
 sp=importlib.util.spec_from_file_location('independent_current_gdi_owner',pin(R/'tools/m4-widget-growth-review/gdi_identity.py'));gdi=importlib.util.module_from_spec(sp);sp.loader.exec_module(gdi)
 owners=set()
 for run in e['runs']:
  f=Path(run['capture'])
  def component(stem):
   p=[p/stem for p in(f/'Widget').glob('root-*')if(p/stem).is_dir()];assert len(p)==1;return p[0]
  ca=component('input-after');clean=component('cleaned');fault=component('same-context-before')
  fonts=list(struct.iter_unpack('<IIIIQBB6x',raw(ca/'fonts.bin')));owned=sorted([x for x in fonts if x[5]and x[6]],key=lambda x:x[1],reverse=True);assert len(owned)==15
  status=struct.unpack('<12Q',raw(fault/'status.bin'));manual=[]
  for x in owned:
   row=raw(f/'Widget/manual-font-cleanup'/(str(x[1])+'-row.bin'));w=struct.unpack('<8Q',row);assert w[:5]==x[:5]and w[5]==status[0]and w[6]and w[7]==1
   manual.append((row,raw(f/'Widget/manual-font-cleanup'/(str(x[1])+'-hardware.bin'))))
  subtree=f/'Widget/GDI-provider';inventory={str(p.relative_to(f)).replace('\\','/')for p in subtree.rglob('*')if p.is_file()}
  # Helper queries only its exact GDI-provider prefix, so this is its complete
  # inventory, rather than a requested-name subset or an inferred DLL name.
  proof=gdi.verify(lambda n:raw(f/n),pin,prefix='Widget/',source_records=raw(clean/'APIs.bin'),manual_records=manual,logical_names=inventory,expected_thread=status[0]);cases.append(dict(level=run['level'],mode=run['mode'],full_GDI_provider_subtree_files=len(inventory),proof=proof))
  for p in subtree.glob('*/before-path.txt'):owners.add(raw(p).decode())
 report=R/'reports/m4-joint-startup138/context-controls-verification-r1/report.json';pin(report,'88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb')
 embedded={};inside=False;targets=dict(pins)
 with report.open(encoding='utf-8')as stream:
  for line in stream:
   if line=='  "files": {\n':inside=True;continue
   if not inside:continue
   if line=='  }\n':break
   k,v=next(iter(json.loads('{'+line.strip().removesuffix(',')+'}').items()))
   if k in targets:assert k not in embedded;embedded[k]=v
 excluded={str(report.resolve()),str((R/'tools/m4-138-controls-review/readiness.py').resolve())};assert set(embedded)==set(targets)-excluded
 for p,h in embedded.items():assert pins[p]==h and sha(p)==h
 pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Independent complete16case named GDI provider identity subtrees, actual measured owner PE/exports and exact source/manual cleanup joins only',
  counts=dict(cases=len(cases),actual_source_calls=sum(x['proof']['actual_source_calls']for x in cases),whole_identity_sides=sum(x['proof']['whole_identity_sides']for x in cases),manual_owned_cleanup_calls=240,authenticated_selected_physical_files=len(embedded)),
  cases=cases,actual_measured_owner_paths=sorted(owners),physical_named_exports_and_relocated_entry64_reverified=True,
  no_forwarder_origin_chain_claim=True,native_worker_executed=False,verifier_rerun=False,archive_reader_opened=False,initializer_credit=0,full_raw_inventory_review=False,whole_private_provider_retry_review=False,current_native3_full_link_join=False,files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),counts=d['counts'])))
if __name__=='__main__':main(sys.argv[1])
