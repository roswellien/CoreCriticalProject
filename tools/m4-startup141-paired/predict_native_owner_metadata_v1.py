"""ROOT-admitted bounded ordinary scalar metadata replay; no CPU/source machine."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
N_SHA='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'
O_SHA='d9b356af5dbec93b333c43bb11a335833ed4b74d6f118110b7f405d55c6a7e3f'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,name):
 ap=Path(admission_path).resolve();assert sha(ap)==admission_sha;A=json.loads(ap.read_bytes());assert A['passed']and A['independent_review']and A['scope_identity']=='current_native141_owner_metadata'
 admitted={}
 for p,h in A['files'].items():
  p=str(Path(p).resolve());assert p not in admitted and sha(p)==h;assert Path(p).suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and Path(p).name!='transport.json';admitted[p]=h
 admitted[str(ap)]=admission_sha;out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();files={};reader=None;owner_reader=None;predictions=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert p.is_relative_to(out)or admitted.get(str(p))==v;assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0;reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:
   if p.suffix.lower()=='.pyc':raise PermissionError('No cached bytecode; physical source only')
   assert p.is_relative_to(out)or str(p)in admitted
 sys.addaudithook(audit)
 try:
  np=pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json',N_SHA);N=json.loads(np.read_bytes());assert N['passed']and N['reader_closed']and N['paired_export_readers_closed'];jp=np.parent/'Constructor-carried-source-derivations.json';rows=json.loads(pin(jp,N['files'][str(jp.resolve())]).read_bytes());assert len(rows)==36
  op=pin(R/'reports/m4-startup141-paired/native-owner-cuts-r3/report.json',O_SHA);O=json.loads(op.read_bytes());assert O['passed']and O['reader_closed']and O['paired_export_readers_closed'];contracts=json.loads(pin(R/'reports/m4-startup141-paired/native-owner-metadata-preparation-r2/physical-API-contracts.json').read_bytes());contracts={int(k):v for k,v in contracts.items()}
  physical={}
  for name in('source_contract.inc','registry_contract.inc'):
   text=pin(R/'reports/m4-startup141-runway/service-preparation-r2'/name).read_text()
   for m in re.finditer(r'\{(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(\d+),"([A-Za-z0-9_]+)",(\d+)\}',text):
    pc,slot,raw,argc,service,tail=m.groups();pc=int(pc,0);v=[service,int(slot,0),int(raw,0),int(argc),int(tail)];assert pc not in physical or physical[pc]==v;physical[pc]=v
  assert physical==contracts
  M=load('tools/m4-startup141-paired/native_owner_metadata_v5.py','current_causal_owner_metadata');E=load('tools/m4-startup138-original/export_reader_r2.py','sealed_ordinary_metadata')
  for level in('O0','O2'):
   reader=E.ExportReader(np,N_SHA,level,pin);owner_reader=E.ExportReader(op,O_SHA,level,pin)
   for seq in range(6):
    base=f'sequence-{seq}/selected/';rs=[v for v in rows if v['level']==level and v['sequence']==seq];assert len(rs)==3;maximum=max(v['API_after']for v in rs)
    words=lambda key,n:list(struct.unpack('<'+'Q'*n,reader.data(key)));facts=[words(base+'locale-api-'+str(i)+'-witness.bin',32)for i in range(maximum)];mfc=[list(v)for v in struct.iter_unpack('<32Q',reader.data(base+'mfc-allocation-witnesses.bin'))];strings=[list(v)for v in struct.iter_unpack('<32Q',reader.data(base+'strings-witnesses.bin'))];resource=words(base+'lockit-resource.bin',8);growth=[words(k,32)for k in reader.entries if k.startswith(base+'registry-growth-')and k.endswith('-witness.bin')]
    for r in rs:
     before=M.derive(facts,mfc,strings,resource,growth,r['API_before'],contracts);after=M.derive(facts,mfc,strings,resource,growth,r['API_after'],contracts);cut=next(v for v in O['cases']if(v['level'],v['sequence'],v['root'])==(level,seq,r['root']));keys=cut['keys']['owner_input'];actual={int(k.rsplit('-page-',1)[1][:-4]):owner_reader.entries[k]['bytes']for k in keys};assert actual=={g:o['mapped_bytes']for g,o in before['owners'].items()};assert len(actual)=={0x4103f0:8,0x410440:10,0x459b40:19}[r['root']]and sum(o['kind']==1 for o in before['owners'].values())==1
     call=r['constructor_call_results'][0];js=r['whole_literal_source_accesses'];indices=[i for i,v in enumerate(js)if v==[call[1],call[3],call[4],4,1]];assert len(indices)==1 and not any(v[4]and v[1]<0x32000000 and v[1]+v[3]>0x31000000 for v in js[:indices[0]+1]);assert owner_reader.data(cut['checkpoint_prefix']+'-name.bin')==b'constructor-mfc-before'
     # Bytes are authenticated only as the genuine carried owner input. They
     # never determine request/generation/native-pointer metadata.
     hashes={str(g):hashlib.sha256(owner_reader.data(cut['checkpoint_prefix']+'-page-'+str(g)+'.bin')).hexdigest()for g in actual};predictions.append(dict(level=level,sequence=seq,root=r['root'],phase=r['phase'],before_metadata=before,after_metadata=after,actual_owner_cut_sha256=hashes,source_prefix_no_owner_write=True,future_summary_used=False,metadata_before_derived_before_after=True))
   reader.close();reader=None;owner_reader.close();owner_reader=None
  assert len(predictions)==36;pin(__file__);pin(ap,admission_sha);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close()
  if owner_reader is not None:owner_reader.close()
  output=out/'predictions.json';output.write_text(json.dumps(predictions,indent=2)+'\n');pin(output)
  for p,h in files.items():assert sha(p)==h
  report=out/'report.json';report.write_text(json.dumps(dict(passed=passed,scope='Current36 causal allocation metadata from actual prior API/source births; full same own dynamic BEFORE backing extents/prefix joined, no CPU/source machine run',predictions_path=str(output),predictions_sha256=sha(output),metadata_cases=len(predictions),native_source_sha256=N_SHA,owner_export_sha256=O_SHA,ordinary_readers_closed=True,canonical_reader_opened=False,source_machine_executed=False,worker_launched=False,future_allocation_summary_used=False,complete_constructor_acceptance_gate=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report))))
if __name__=='__main__':main(*sys.argv[1:])
