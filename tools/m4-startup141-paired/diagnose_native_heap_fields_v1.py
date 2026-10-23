"""Bounded code-independent plain ordinary heap field chronology; no model/reader."""
from pathlib import Path
import json,hashlib,struct
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-heap-field-diagnostic-r1';assert not out.exists();out.mkdir()
 np=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';assert sha(np)=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3';N=json.loads(np.read_bytes());e=next(v for v in N['paired_exports']if v['branch']=='O0');ip=Path(e['index_path']);pp=Path(e['payload_path']);assert sha(ip)==e['index_sha256'];index=json.loads(ip.read_bytes());assert pp.stat().st_size==e['payload_bytes']==index['payload_bytes'];reads={}
 sp=np.parent/'Constructor-carried-source-derivations.json';assert sha(sp)==N['files'][str(sp.resolve())];source=json.loads(sp.read_bytes());prior=R/'reports/m4-startup141-paired/native36-source-r5/report.json';assert sha(prior)=='b19061cdbacf66e253f08147395a94ff296a4eb14d41f09933dbcfa9158da589';P=json.loads(prior.read_bytes());assert P['passed']is False and P['ordinary_reader_closed']is True and P['files'][str(pp)]==e['payload_sha256']
 with pp.open('rb')as f:
  def get(key):
   x=index['entries'][key];assert x['bytes']<=600000 and x['offset']+x['bytes']<=index['payload_bytes'];f.seek(x['offset']);b=f.read(x['bytes']);assert len(b)==x['bytes']and hashlib.sha256(b).hexdigest()==x['sha256'];reads[key]=x;return b
  base='sequence-0/selected/';heap=list(struct.iter_unpack('<5I',get(base+'heap-source-accesses.bin')));heap=[list(v)for v in heap if any(v)];raw=[list(v)for v in struct.iter_unpack('<IIQII',get(base+'locale-source-accesses.bin'))];create=list(struct.unpack('<16Q',get(base+'heap-create-witness.bin')));assert len(heap)==36 and heap==raw[:36];assert heap[8]==[0x780039d8,0x78035000,0x48450001,4,1]and heap[31]==[0x780039eb,0x78035004,1,4,1];writes=[(j,v)for j,v in enumerate(raw)if v[4]and v[1]<0x78035008 and v[1]+v[3]>0x78035000];assert writes==[(8,heap[8]),(31,heap[31])];cases=[]
  for r in source:
   if r['level']!='O0'or r['sequence']!=0:continue
   v=r['provider_source_accesses'];hits=[j for j in range(len(raw)-len(v)+1)if raw[j]==v[0]and raw[j:j+len(v)]==v];assert len(hits)==1;fields=[]
   for address,value,pc in [(0x78035000,0x48450001,0x78001379),(0x78035004,1,0x78001306)]:
    indices=[j for j,v in enumerate(r['whole_literal_source_accesses'])if v[1]<address+4 and v[1]+v[3]>address];assert indices;first=r['whole_literal_source_accesses'][indices[0]];assert first==[pc,address,value,4,0]and not any(r['whole_literal_source_accesses'][j][4]for j in indices);fields.append(dict(address=address,predicted_from_initializer=value,first_actual_whole_operand=first,first_whole_operand_index=indices[0],no_own_overlapping_write=True))
   cases.append(dict(root=r['root'],provider_raw_start=hits[0],entire_provider_rows=len(v),fields=fields))
 assert len(cases)==3 and sha(ip)==e['index_sha256'];files={str(v.resolve()):sha(v)for v in [np,ip,sp,prior,Path(__file__)]};q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Limited independent arithmetic O0sequence0 actual raw bootstrap and3constructor provider/scalar chronology; not ROOT admission or source execution',cases=cases,bootstrap_publications=writes,create_words=create,ordinary_selected_entry_identities=reads,ordinary_bytes_read=sum(v['bytes']for v in reads.values()),payload_declared_sha256=e['payload_sha256'],payload_whole_hash_recomputed_by_this_diagnostic=False,ROOT_closed_failed_source_payload_pin_sha256=sha(prior),model_executed=False,canonical_reader_opened=False,worker_launched=False,whole_page_claim=False,initializer_credit=0,files=files),indent=2)+'\n');print(dict(report_sha256=sha(q),cases=len(cases),bytes_read=sum(v['bytes']for v in reads.values())))
if __name__=='__main__':main()
