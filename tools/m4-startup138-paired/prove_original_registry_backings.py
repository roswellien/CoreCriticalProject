"""All current original registry whole backing predictions, ordinary sealed exports."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 m=load('registry_literal',R/'tools/m4-startup138-paired/registry_backing_policy.py');d=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');gp=pin(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');gate=json.loads(gp.read_bytes());assert gate['passed']and gate['reader_closed'];pr=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes());order=pr['selected_order'];roots=[]
 for path in('reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json','reports/m4-strings-source/recovery-r7/string-roots.json','reports/m4-mfc-source/recovery-r4/mfc-roots.json','reports/m4-fs-source/recovery-r3/fs-roots.json','reports/m4-container-source/recovery-r3/container-roots.json','reports/m4-formatting-frontier/recovery-r1/roots.json','reports/m4-mixed-format-original/recovery-r1/roots.json'):
  roots+=json.loads(pin(R/path).read_bytes())
 roots+=json.loads(pin(R/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['roots']+pr['Lockit_roots'];callbacks={r['entry']:r['registration']['callback']for r in roots};callbacks[0x4b7f70]=0x4b7fa0
 for r in json.loads(pin(R/'reports/m4-fps-original/preparation-r1/normal-contracts.json').read_bytes())['roots']:callbacks[r['root']]=r['callback']
 assert len(callbacks)==108 and sum(r['entry']in callbacks for r in order)==108
 actual=json.loads(pin(gp.parent/'whole-registry-BEFORE.json',gate['files'][str((gp.parent/'whole-registry-BEFORE.json').resolve())]).read_bytes());assert len(actual)==828
 export=gate['paired_exports'][0];idx=pin(export['index_path'],export['index_sha256']);payload=Path(export['payload_path']);assert payload.stat().st_size==export['payload_bytes'];index=d.entries(idx,re.compile(r'phase/[0-5]/\d+(\.bin|/(api-ledger\.bin|api-initial/\d+/(size|bytes)\.bin))'))
 with payload.open('rb')as f:
  def data(key):
   e=index[key];f.seek(e['offset']);raw=f.read(e['bytes']);assert len(raw)==e['bytes']and hashlib.sha256(raw).hexdigest()==e['sha256'];return raw
  for seq in range(6):
   carried=[];last=None
   for phase,item in enumerate(order):
    before=actual[seq*138+phase];assert before['sequence']==seq and before['phase']==phase and before['root']==item['entry'];meta=before['BEFORE_metadata'];backing=bytes.fromhex(before['BEFORE_backing_hex']);assert backing[:len(carried)*4]==struct.pack('<'+str(len(carried))+'I',*carried)
    if last is not None:assert meta==last['metadata']and backing==last['backing']
    cb=callbacks.get(item['entry']);birth=None;ledger=data(f'phase/{seq}/{phase}/api-ledger.bin')
    for ai,rw in enumerate(struct.iter_unpack('<26I',ledger)):
     if rw[24]==3 and rw[22]==meta[0]and rw[10]:
      assert birth is None and rw[9]==rw[19]==0 and rw[25]==0x78011c2d;initial=data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');size=struct.unpack('<I',data(f'phase/{seq}/{phase}/api-initial/{ai}/size.bin'))[0];assert len(initial)==size;birth=dict(old_begin=rw[22],requested=rw[23],source_CALL_pc=0x78011c27,return_word=rw[25],pointer=rw[10],initial=initial,API_index=ai)
    prediction=m.derive(meta,backing,cb,birth);record=data(f'phase/{seq}/{phase}.bin');assert len(record)==356992;after=struct.unpack_from('<4I',record,356464);assert list(after)==prediction['metadata']and record[356480:356480+after[2]]==prediction['backing'];last=prediction
    if cb is not None:carried.append(cb)
    rows.append(dict(sequence=seq,phase=phase,root=item['entry'],callback=cb,growth=prediction['growth'],source_store=prediction['source_store'],whole_source_backing_bytes=len(prediction['backing']),source_backing_sha256=hashlib.sha256(prediction['backing']).hexdigest(),APIinitial_source_input=birth is not None,AFTER_bytes_used_as_input=False))
   assert len(carried)==108
 assert sha(idx)==export['index_sha256'];contracts=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_bytes());contracts=contracts['instructions']if isinstance(contracts,dict)else contracts;assert all(any(r['pc']==pc for r in contracts)for pc in(0x78004a67,0x78004a69,0x7801e2aa,0x7801e2b5));controls=[]
 for label,meta,backing,cb,birth in [('wrong-mode',[1,1,4,2],bytes(4),2,None),('missing-growth',[1,5,4,1],bytes(4),2,None),('nonfull-unexpected-growth',[1,1,4,1],bytes(4),2,{}),('missing-prefix',[1,5,4,1],b'abcd',2,dict(old_begin=1,requested=20,source_CALL_pc=0x78011c27,return_word=0x78011c2d,pointer=8,initial=bytes(20)))]:
  try:m.derive(meta,backing,cb,birth)
  except ValueError:controls.append(dict(name=label,refused=True))
  else:raise AssertionError(label)
 rp=out/'relations.json';rp.write_text(json.dumps(rows,indent=2)+'\n');pin(rp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All828 original own registry full backings from actual own BEFORE or exact APIinitial reallocation and literal single callback MOV; AFTER bytes equality targets only',original_validation_sha256=sha(gp),all108_callbacks_source_derived=True,root_predictions=len(rows),callback_stores=sum(r['callback']is not None for r in rows),full_APIinitial_growths=sum(r['growth']for r in rows),whole_backing_bytes=sum(r['whole_source_backing_bytes']for r in rows),negative_controls=controls,ordinary_readers_closed=True,archive_reader_opened=False,crossbranch_padding_equality_claimed=False,CPU_provider_execution_claimed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
