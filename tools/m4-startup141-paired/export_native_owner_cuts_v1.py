"""ROOT-admitted bounded existing-native-capture owner export; never a worker/model."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
SOURCE_SHA='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'
EXEC_SHA='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,name):
 admission_path=Path(admission_path).resolve();assert sha(admission_path)==admission_sha;A=json.loads(admission_path.read_bytes());assert A['passed']is True and A['independent_review']is True and A['scope_identity']=='native141_constructor_owner_cut_export'
 admitted={}
 for p,h in A['files'].items():
  p=str(Path(p).resolve());assert p not in admitted and sha(p)==h;admitted[p]=h
 admitted[str(admission_path)]=admission_sha
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();files={};exports=[];cases=[];reader=None;export=None;passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert p.is_relative_to(out)or admitted.get(str(p))==v;assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0;reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:
   if p.suffix.lower()=='.pyc':raise PermissionError('ROOT-admitted source only, no cached bytecode')
   assert p.is_relative_to(out)or str(p)in admitted,('Unadmitted external read',str(p))
 sys.addaudithook(audit)
 try:
  source=json.loads(pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json',SOURCE_SHA).read_bytes());execution=json.loads(pin(R/'reports/m4-startup141-root/execution-r2/report.json',EXEC_SHA).read_bytes());assert source['passed']and source['reader_closed']and source['paired_export_readers_closed']and execution['passed']
  D=load('tools/m4-crt-allocation-root/run_v2.py','owner_cut_canonical_reader');EX=load('reports/m4-startup141-source/preparation-r6/paired_exports.py','owner_cut_raw_export')
  for level in('O0','O2'):
   identity=next(v for v in source['paired_exports']if v['branch']==level);capture=Path(execution['runs'][level]['capture']).resolve();assert capture==Path(identity['transport_path']).resolve();reader=D.DirectSet(capture,pin);assert sha(reader.path)==identity['transport_sha256'];export=EX.Export(out/'paired',level,reader.path,pin)
   table=reader.words('selected-table.bin',141)
   for seq in range(6):
    base=f'sequence-{seq}/selected/';names={};number={}
    for key in reader.entries:
     m=re.fullmatch(re.escape(base)+r'registry-checkpoint-(\d+)-name.bin',key)
     if m:
      prefix=key[:-9];n=int(m[1]);number[prefix]=n;names.setdefault(reader.data(key).decode(),[]).append(prefix)
    starts=sorted(names['constructor-mfc-before'],key=lambda p:number[p]);ends=sorted(names['constructor-mfc-after'],key=lambda p:number[p]);assert len(starts)==len(ends)==8
    for which,root in enumerate((0x4103f0,0x410440,0x459b40)):
     assert table.index(root)==(13,14,39)[which];before=starts[(0,3,6)[which]];after=min((p for p in names['widget-onexit-after']if number[p]>number[ends[(2,5,7)[which]]]),key=lambda p:number[p]);keys={}
     for side,prefix in(('owner_input',before),('endpoint',after)):
      pages=sorted(k for k in reader.entries if k.startswith(prefix+'-page-')and 0x31000000<=int(k[len(prefix)+6:-4])<0x32000000);assert pages
      keys[side]=pages
      for key in [prefix+'-name.bin']+pages:
       if key not in export.entries:export.write(key,reader.data(key))
     cases.append(dict(level=level,sequence=seq,root=root,phase=table.index(root),checkpoint_prefix=before,checkpoint_name='constructor-mfc-before',source_owner_prefix_proof_required=True,static_or_stack_checkpoint_bytes_seeded=False,endpoint_checkpoint_prefix=after,keys=keys))
   row=export.finish();export=None;exports.append(row);reader.close();reader=None
  assert len(cases)==36;pin(__file__);pin(admission_path,admission_sha);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if export is not None:export.close()
  if reader is not None:reader.close()
  for p,h in files.items():assert sha(p)==h
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Existing current native141 exact first constructor-MFC BEFORE dynamic-owner pages and separately typed terminal endpoint pages; carry requires literal zero-owner-write prefix, no source/model executed',source_sha256=SOURCE_SHA,execution_sha256=EXEC_SHA,cases=cases,paired_exports=exports,reader_closed=True,paired_export_readers_closed=True,canonical_reader_sessions=2 if passed else None,worker_launched=False,model_executed=False,source_AFTER_seed=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
