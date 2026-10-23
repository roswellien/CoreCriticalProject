"""Prepared ROOT-admitted ordinary-only finite ENV probe; no source/model/canonical worker."""
from pathlib import Path
import hashlib,json,struct,sys,types,re,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,name):
 ap=Path(admission_path).resolve();assert sha(ap)==admission_sha;A=json.loads(ap.read_bytes());assert A['passed']is True and A['independent_review']is True and A['scope_identity']=='current141_widget_ENV_ordinary_probe';admitted={};pins={}
 for path,h in A['files'].items():
  p=Path(path).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and str(p)not in admitted and sha(p)==h;admitted[str(p)]=h
 admitted[str(ap)]=admission_sha
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert admitted.get(str(p))==v and(h is None or h==v);pins[str(p)]=v;return p
 def report(p,h):return json.loads(pin(R/p,h).read_bytes())
 N=report('reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');O=report('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c');S=report('reports/m4-original141-source/source-r7/report.json','44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334');W=report('reports/m4-original141-source/source-r7-widgets/report.json','bfc217783dd1e5869f2b9b247fe509343a0c3edec26f53ff42cb0c605e1a1d5a');assert N['passed']and N['reader_closed']and N['paired_export_readers_closed']and O['passed']and O['reader_closed']and O['paired_export_readers_closed']and S['passed']and W['passed'];assert W['counts']['original_only_finite_GDI_ENV_metadata_clear_responses']==1 and W['counts']['actual_GDI_whole_FX512_conservation_relations']==894 and W['counts']['actual_GDI_whole_ENV28_conservation_relations']==893
 def module(path):
  p=pin(R/path);m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
 K=module('tools/m4-startup141-paired/widget_ENV_relation141_v1.py');E=module('tools/m4-startup141-paired/native_ENV28_v1.py');C=module('reports/m4-original141-fp-review/source-preparation-r1/finite_env_contract_v1.py');order=json.loads(pin(R/'reports/m4-original141/source-preparation-r6/selected-order.json').read_bytes());assert len(order)==141
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();selected_metadata={};phase_bytes={};scans={};passed=False;relations=[]
 try:
  def select(row,branch,keys,size):
   index=pin(row['index_path'],row['index_sha256']);payload=pin(row['payload_path'],row['payload_sha256']);assert payload.stat().st_size==row['payload_bytes'];got={};scanned=0
   # Entire index is authenticated; selector retains only twelve exact logical entries.
   with index.open('rb')as f:
    for line in f:
     scanned+=len(line)
     m=re.match(rb'    "([^"\\]+)": \{\s*$',line)
     if not m:continue
     key=m[1].decode()
     if key not in keys:continue
     assert key not in got;body=b'{\n'
     for line in f:
      scanned+=len(line);body+=line;assert len(body)<=4096
      if line.startswith(b'    }'):break
     got[key]=json.loads(body.rstrip().rstrip(b','));v=got[key];assert type(v['offset'])is int and type(v['bytes'])is int and v['bytes']==size and 0<=v['offset']and v['offset']+size<=row['payload_bytes']and re.fullmatch('[0-9a-f]{64}',v['sha256'])
   assert set(got)==set(keys);values={}
   with payload.open('rb')as f:
    for key,v in got.items():
     f.seek(v['offset']);b=f.read(v['bytes']);assert len(b)==size and hashlib.sha256(b).hexdigest()==v['sha256'];values[key]=b
   selected_metadata[branch]=got;scans[branch]=dict(index_bytes_scanned=scanned,retained_selector_entries=len(got),maximum_entry_metadata_bytes=4096,whole_index_SHA_recomputed=True,whole_payload_SHA_recomputed=True);return values
  ori=next(v for v in O['paired_exports']if v['branch']=='original');original=select(ori,'current_original141',[f'phase/0/{p}.bin'for p in range(137,141)],356992)
  for level in('O0','O2'):
   row=next(v for v in N['paired_exports']if v['branch']==level);native=select(row,level,[f'sequence-0/phase-{p}.bin'for p in range(137,141)],159716);epoch=native['sequence-0/phase-137.bin'][141540:145044];first_native_FX=native['sequence-0/phase-137.bin'][116:628];first_original_FX=original['phase/0/137.bin'][116:628];assert first_original_FX.hex()==C.EXPECTED['FX512_hex']
   for phase in range(137,141):
    a=original[f'phase/0/{phase}.bin'];b=native[f'sequence-0/phase-{phase}.bin'];slot=order[phase]['slot'];root=order[phase]['entry'];assert struct.unpack_from('<5I',a)[0:1]+struct.unpack_from('<5I',a)[2:]==(0,phase,slot,root)and struct.unpack_from('<5I',b)[0:1]+struct.unpack_from('<5I',b)[2:]==(0,phase,slot,root)
    for side,eo,so,fo in [('before',2164,141540,116),('after',2192,145044,628)]:
     original_env=a[eo:eo+28];native_env=b[eo:eo+28];state=b[so:so+3504];assert a[fo:fo+512]==first_original_FX and b[fo:fo+512]==first_native_FX;result=K.compare(0,phase,side,root,epoch,state,original_env,native_env,E.project);relations.append(dict(level=level,sequence=0,phase=phase,root=root,side=side,original_ENV_hex=original_env.hex(),native_ENV_hex=native_env.hex(),native_State_sha256=hashlib.sha256(state).hexdigest(),native_epoch_BEFORE_State_sha256=hashlib.sha256(epoch).hexdigest(),whole_own_FX512_conserved_each_branch=True,**result))
  assert len(relations)==16 and sum(v['typed_original_metadata_clear']for v in relations)==14;passed=True
 finally:
  pin(__file__);pin(ap,admission_sha)
  for p,h in pins.items():assert sha(p)==h
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Ordinary finite current141 ENV endpoint/sourceState-input hypothesis probe; full source lastwriter/independent policy admission and all53paired gates remain separate',relations=relations,selected_logical_metadata=selected_metadata,scans=scans,raw_phase_payload_bytes=4*356992+8*159716,source_models_executed=False,native_worker_launched=False,canonical_reader_opened=False,ordinary_readers_closed=True,whole53_pair_admitted=False,source_lastwriter_policy_independently_admitted=False,initializer_credit=0,files=pins),indent=2)+'\n');print(dict(report=str(q),sha256=sha(q),passed=passed))
if __name__=='__main__':main(*sys.argv[1:])
