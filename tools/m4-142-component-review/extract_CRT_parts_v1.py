"""Unexecuted ROOT-admitted exact-key extraction, one CaptureBundle at a time."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission,admission_sha,output):
 ap=Path(admission).resolve();assert sha(ap)==admission_sha;A=json.loads(ap.read_text());assert A['passed']is True and A['independent_review']is True and A['scope_identity']=='hypot142_native_CRT_exact_parts'
 admitted={str(Path(p).resolve()):h for p,h in A['files'].items()};out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True);pins={};reader=None;closed=[];results=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert p.is_relative_to(out)or admitted.get(str(p))==v;assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
  reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading and(p.is_relative_to(R)or p.drive.upper()=='G:'):
   if p.suffix.lower()=='.pyc':raise FileNotFoundError('Exact cold project source imports only')
   assert p.is_relative_to(out)or str(p)in admitted,('Unadmitted project/capture read',str(p))
 sys.addaudithook(audit)
 try:
  source=json.loads(pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3').read_text())
  assert source['passed']and source['reader_closed']and source['paired_export_readers_closed']
  module=pin(R/'tools/m4-pipeline/capture_bundle_storage.py');pin(R/'tools/m4-pipeline/paths_capture_storage.py');sys.path.insert(0,str(module.parent));s=importlib.util.spec_from_file_location('unchanged_single_part_reader',module);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  for level in ('O0','O2'):
   retained=next(x for x in source['paired_exports']if x['branch']==level);manifest=pin(retained['transport_path'],retained['transport_sha256']);value=json.loads(manifest.read_text());assert value['passed']and value['format']=='mw34.capture.direct.v1'
   wanted=A['exact_keys'][level];assert len(wanted)==len(set(wanted))and 1<=len(wanted)<=288
   assert all(re.fullmatch(r'sequence-[0-5]/(?:phase-(?:81|82)\.bin|selected/registry-checkpoint-\d+-(?:name|state|fx|cpu|runtime-cpu|page-(?:2013458432|2013507584))\.bin)',key)for key in wanted),'Exact phase81/82 and two CRT checkpoint diagnostic keys only'
   # ROOT must substantively bind each checkpoint key to phase81/82 chronology.
   assert A['key_timing_recipe_sha256']==sha(pin(A['key_timing_recipe_path']))
   inventory={};observed=set();total_files=0;total_payload=0
   for part in value['parts']:
    assert Path(part['bundle']).name==part['bundle']and part['bundle'].endswith('.mwb');p=pin(manifest.parent/part['bundle'],part['sha256']);assert str(p)not in inventory;inventory[str(p)]=part['sha256'];total_files+=part['logical_files'];total_payload+=part['payload_bytes']
   assert total_files==value['logical_files']and total_payload==value['payload_bytes']
   physical={manifest.name}|{p['bundle']for p in value['parts']};assert {p.name for p in manifest.parent.iterdir()}==physical
   for part in value['parts']:
    p=manifest.parent/part['bundle'];reader=m.CaptureBundle(p,part['sha256'])
    try:
     assert len(reader.names())==part['logical_files']and p.stat().st_size==part['bundle_bytes']
     for key in wanted:
      if not reader.exists(key):continue
      assert key not in observed;data=reader.read_bytes(key);q=out/level/key;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);pin(q);observed.add(key)
    finally:reader.close();reader=None;closed.append(str(p))
   assert observed==set(wanted),'Every exact timed requested key genuinely exists once'
   for p,h in inventory.items():pin(p,h)
   pin(manifest,retained['transport_sha256']);results.append(dict(level=level,whole_parts_freshly_rehashed=True,part_count=len(inventory),requested_keys=wanted,all_keys_found=True,loaded_CRT_input_admitted=False,source_phase_timing_proven_by_this_transport=False))
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader=None
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Existing exact canonical part bytes transported under retained strict source6 plus fresh ALLpart physicalSHA; unchanged CaptureBundle validates each opened part, one live mapping maximum',ROOT_admission_path=str(ap),ROOT_admission_sha256=admission_sha,reader_closed=reader is None,parts_closed=closed,results=results,State_created=False,source_executed=False,worker_launched=False,accepted_credit=0,files=pins),indent=2)+'\n');print(str(q))
if __name__=='__main__':main(*sys.argv[1:])
