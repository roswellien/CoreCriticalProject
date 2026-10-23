"""Independent scalar recomputation of all current original registry backings."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup138-paired/original-registry-independent-r1';assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p);pins[str(p)]=v;return p
 proofpath=pin(R/'reports/m4-startup138-paired/original-registry-backings-r4/report.json','e90c569fa71b0a8dbdbb857eb079eb39295181241cc443d47723fbdef70727f5');proof=json.loads(proofpath.read_bytes())
 assert proof['passed']and proof['root_predictions']==828 and proof['callback_stores']==648 and proof['full_APIinitial_growths']==114
 for p,h in proof['files'].items():pin(p,h)
 valpath=R/'reports/m4-startup138-original/original-validation-r3/report.json';val=json.loads(valpath.read_bytes());e=val['paired_exports'][0];payload=pin(e['payload_path'],e['payload_sha256']);idx=pin(e['index_path'],e['index_sha256'])
 readerpath=R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py';sp=importlib.util.spec_from_file_location('root_registry_entry_reader',pin(readerpath));reader=importlib.util.module_from_spec(sp);sp.loader.exec_module(reader)
 entries=reader.entries(idx,re.compile(r'phase/[0-5]/\d+(\.bin|/(api-ledger\.bin|api-initial/\d+/(size|bytes)\.bin))'))
 order=json.loads((R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes())['selected_order']
 rows=json.loads((proofpath.parent/'relations.json').read_bytes());before=json.loads((valpath.parent/'whole-registry-BEFORE.json').read_bytes())
 callbacks={}
 for leaf in ['m4-onexit-batch-recovery/recovery-r3/registration-roots.json','m4-strings-source/recovery-r7/string-roots.json','m4-mfc-source/recovery-r4/mfc-roots.json','m4-fs-source/recovery-r3/fs-roots.json','m4-container-source/recovery-r3/container-roots.json','m4-formatting-frontier/recovery-r1/roots.json','m4-mixed-format-original/recovery-r1/roots.json']:
  for r in json.loads((R/'reports'/leaf).read_bytes()):callbacks[r['entry']]=r['registration']['callback']
 for r in json.loads((R/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['roots']+json.loads((R/'reports/m4-lockit-source/recovery-r1/lockit-roots.json').read_bytes()):callbacks[r['entry']]=r['registration']['callback']
 callbacks[0x4b7f70]=0x4b7fa0
 for r in json.loads((R/'reports/m4-fps-original/preparation-r1/normal-contracts.json').read_bytes())['roots']:callbacks[r['root']]=r['callback']
 assert len(callbacks)==108 and len(rows)==len(before)==828
 calls=growth=whole=0
 with payload.open('rb')as f:
  def data(key):
   x=entries[key];f.seek(x['offset']);b=f.read(x['bytes']);assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256'];return b
  for seq in range(6):
   previous=None;used=[]
   for phase,item in enumerate(order):
    n=seq*138+phase;r=rows[n];b=before[n];assert (r['sequence'],r['phase'],r['root'])==(seq,phase,item['entry'])==(b['sequence'],b['phase'],b['root'])
    begin,nxt,capacity,mode=b['BEFORE_metadata'];raw=bytes.fromhex(b['BEFORE_backing_hex']);assert begin and mode==1 and len(raw)==capacity
    offset=nxt-begin;assert 0<=offset<=capacity and offset%4==0 and raw[:4*len(used)]==struct.pack('<'+str(len(used))+'I',*used)
    if previous is not None:assert ([begin,nxt,capacity,mode],raw)==previous
    cb=callbacks.get(item['entry']);assert cb==r['callback'];births=[]
    for ai,x in enumerate(struct.iter_unpack('<26I',data(f'phase/{seq}/{phase}/api-ledger.bin'))):
     if x[24]==3 and x[22]==begin and x[10]:births.append((ai,x))
    assert len(births)==int(cb is not None and offset==capacity)
    if births:
     ai,x=births[0];assert x[9]==x[19]==0 and x[23]==capacity+16 and x[25]==0x78011c2d
     initial=data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');size,=struct.unpack('<I',data(f'phase/{seq}/{phase}/api-initial/{ai}/size.bin'));assert len(initial)==size>=capacity+16 and initial[:capacity]==raw
     raw=initial;begin=x[10];capacity=size;growth+=1
    expected=bytearray(raw)
    if cb is not None:expected[offset:offset+4]=cb.to_bytes(4,'little');used.append(cb);calls+=1;offset+=4
    metadata=[begin,begin+offset,capacity,mode];actual=data(f'phase/{seq}/{phase}.bin');assert len(actual)==356992
    assert list(struct.unpack_from('<4I',actual,356464))==metadata and actual[356480:356480+capacity]==expected
    assert r['AFTER_bytes_used_as_input']is False and r['source_backing_sha256']==hashlib.sha256(expected).hexdigest()and r['whole_source_backing_bytes']==capacity
    previous=metadata,bytes(expected);whole+=capacity
   assert len(used)==108
 for p,h in pins.items():assert sha(p)==h
 pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Independent scalar arithmetic full828 original registry prediction from own BEFORE, actual pre-write API birth and literal typed callback sources; complete AFTER equality only',original_registry_source_sha256=sha(proofpath),root_predictions=828,callback_stores=calls,APIinitial_growths=growth,whole_backing_bytes=whole,all108_callbacks_source_joined=True,own_interphase_full_backing_carried=True,AFTER_seed=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
