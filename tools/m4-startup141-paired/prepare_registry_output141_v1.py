"""Prepare-only generator for registry_output141_v1.py; reads no export.

The consumer's registry body is mechanically extracted from the exact passing
producer replay_original141_v10.py (source-r7) with two documented deltas:
  D1 drop the observed69/constructor-global page-geometry reads (out of scope);
  D2 replace the compact row serializer with the prepared output-only child row
     from registry-output-preparation-r1/inverse.json (no new input or predicate).
Everything else in that block is byte-identical. ROOT admission re-derives it.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PRODUCER=R/'tools/m4-original141-source/replay_original141_v10.py'
PRODUCER_SHA='65421344550b0e133967d21becb2b7b120f58f653a0bca2a2432d42e315c1553'
INVERSE=R/'reports/m4-startup141-paired/registry-output-preparation-r1/inverse.json'
INVERSE_SHA='65dcfcf8badd733cc7d583e16130c656fee8c6686425b0d7db9518c6ec8740d5'
START="  registry_model=load(R/'tools/m4-startup138-paired/registry_backing_policy.py','original141_registry')\n"
END_PREFIX="   need(len(carried)==111 and reader.data(f'cleanup/{seq}/registry.bin')"
D1_LINES=("    for i,p in enumerate(whole):\n","     for side,offset in(('before',2276),('after',178404)):\n","      b=record[offset+i*4096:","    for side in('before','after'):need(len(reader.data(stem+f'/constructor-global-{side}.bin'))")
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def derive_block(producer_text,inverse):
 """Exact producer block -> consumer block; raises on any anchor drift."""
 assert producer_text.count(START)==1,'Unique producer registry start'
 at=producer_text.index(START);lines=producer_text[at:].splitlines(keepends=True);block=[]
 for line in lines:
  block.append(line)
  if line.startswith(END_PREFIX):break
 else:raise AssertionError('Producer cleanup-vector end anchor')
 dropped=[l for l in block if l.startswith(D1_LINES)];assert len(dropped)==4,dropped
 kept=[l for l in block if not l.startswith(D1_LINES)]
 parent=' '*4+inverse[0]['parent']+'\n';child=' '*4+inverse[0]['child']+'\n'
 assert kept.count(parent)==1,'Exact compact parent serializer'
 kept[kept.index(parent)]=child
 return ''.join(block),''.join(kept),dropped
HEADER='''"""ROOT-admitted registry-only original141 ordinary-export consumer (v1).

Re-derives the846 own registry predictions with the unchanged pure
registry_backing_policy over each genuine own whole-registry BEFORE, the
111 literal callback bindings, each26-DWORD API ledger and every actual
successful HeapReAlloc APIinitial backing, then joins each whole AFTER registry
endpoint, the chronological carry and the actual cleanup vector, exactly as the
passing source-r7 producer did. It additionally serializes the source BEFORE/
computed AFTER metadata, backing, literal store and complete realloc input.
Rows are corroborated against source-r7's pinned compact rows. No x86/family
replay, worker, capture, canonical reader or page-geometry claim.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
SCOPE='original141_registry_output_consumer'
SHARED=('sequence','phase','root','callback','growth','full_source_registry_bytes','source_backing_sha256','candidate_AFTER_input')
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def corroborate(rows,producer_rows):
 """Pure: every shared compact field equals the passing producer's own row."""
 need(len(rows)==len(producer_rows)==846,'Complete846 rows on both sides')
 for mine,theirs in zip(rows,producer_rows):
  need(set(theirs)==set(SHARED),'Exact producer compact schema')
  for k in SHARED:need(type(mine[k])is type(theirs[k])and mine[k]==theirs[k],'Producer compact row '+k)
  need(mine['source_backing_sha256']==hashlib.sha256(bytes.fromhex(mine['source_computed_after_backing_hex'])).hexdigest(),'Serialized AFTER backing is the hashed prediction')
  need((mine['source_store']is None)==(mine['callback']is None)and(mine['source_realloc_input']is None)==(not mine['growth']),'Store iff callback; realloc input iff growth')
 return dict(rows_corroborated=len(rows),shared_fields=len(SHARED))
def main(admission_path,admission_sha,name):
 admission_path=Path(admission_path).resolve();need(sha(admission_path)==admission_sha,'Exact independently supplied ROOT admission')
 A=json.loads(admission_path.read_bytes());need(A['passed']is True and A['independent_review']is True and A['scope_identity']==SCOPE,'Independent registry-consumer admission before every import/reader')
 admitted={}
 for p,h in A['files'].items():
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Only sealed ordinary inputs')
  need(str(p)not in admitted and sha(p)==h,'Unique whole admitted ordinary file before import');admitted[str(p)]=h
 admitted[str(admission_path)]=admission_sha
 need(__import__('re').fullmatch('[A-Za-z0-9_-]{1,90}',name),'Simple fresh namespace');out=R/'reports/m4-startup141-paired'/name;need(not out.exists(),'Fresh output');out.mkdir(parents=True)
 def own_output(p):return p.is_relative_to(out.resolve())
 pins={str(admission_path):admission_sha};reader=None;passed=False;rows=[];counts={};stage='input admission';corroboration=None
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Never open canonical capture')
  actual=sha(p);need(own_output(p)or admitted.get(str(p))==actual,'Exact ROOT-admitted external input/code, no fallback')
  need(h is None or h==actual,'Exact field physical identity');need(str(p)not in pins or pins[str(p)]==actual,'Stable ordinary input');pins[str(p)]=actual;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  p=pin(p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
  reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:
   if p.suffix.lower()=='.pyc':raise FileNotFoundError('Compile exact admitted source; cached bytecode refused')
   need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No canonical read anywhere')
   if p.is_relative_to(R)or str(p)in admitted:need(own_output(p)or str(p)in admitted,'Every actual project/source read already physically ROOT admitted')
 try:
  pin(__file__);C=read(A['configuration']['path'],A['configuration']['sha256']);need(C['schema']=='mw34-original141-source-input-contract-v1','Exact current141 configuration schema')
  sys.addaudithook(audit)
  V=read(C['validation']['path'],C['validation']['sha256']);need(V['passed']and V['reader_closed']and V['counts']['phases']==846 and V['callbacks']==111 and V['record_bytes']==356992 and V['combined_pages']==69,'Current genuine846 strict ordinary export')
  order=read(C['selected_order']['path'],C['selected_order']['sha256']);need(len(order)==141 and len({r['entry']for r in order})==141,'Physical current selected141 table')
  need([order[i]['entry']for i in(13,14,15,39,86)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40,0x4b7f70],'Current literal constructor/MFC/tree chronology')
  need(C['source_preparation']['sha256']==V['preparation_sha256'],'Same actually compiled original source preparation')
  callback=read(C['callbacks']['path'],C['callbacks']['sha256']);need(callback['schema']=='mw34-source-callback111-v1'and len(callback['rows'])==111,'Distinct111 literal source callback bindings')
  callback_byroot={r['root']:r['callback']for r in callback['rows']};need(len(callback_byroot)==111 and all(r in {v['entry']for v in order}for r in callback_byroot),'Complete actual selected callback roots')
  for r in callback['rows']:
   authority=read(r['authority_path'],r['authority_sha256']);need(r['callback']>0 and r['authority_row']is not None,'Explicit physical source callback authority')
   node=authority
   for part in r['authority_row']:node=node[part]
   need(node==r['callback'],'Exact named source contract callback value; no candidate output')
  E=load(R/'tools/m4-startup138-original/export_reader_r2.py','original141_export');reader=E.ExportReader(C['validation']['path'],C['validation']['sha256'],'original',pin)
  reader.words=lambda logical,n:struct.unpack('<'+'I'*n,reader.data(logical))
  header=reader.data('header.bin');need(len(header)==32 and header[:8]==bytes.fromhex(C['physical_header_magic_hex'])and struct.unpack_from('<6I',header,8)==(1,6,141,846,43,356992),'Actual physical writer header and all numeric141 geometry')
  need(reader.data('COMPLETE.txt')==b'complete','Terminal original capture copied by sealed export')
'''
FOOTER='''  counts.update(phases=len(rows),callbacks=111,registry_callback_stores=sum(r['callback']is not None for r in rows),registry_growths=sum(r['growth']for r in rows),source_realloc_inputs=sum(r['source_realloc_input']is not None for r in rows))
  stage='corroborate against passing source-r7 compact rows'
  corroboration=corroborate(rows,read(A['producer_rows']['path'],A['producer_rows']['sha256']))
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader_reads=len(reader.reads);reader.entries.clear();reader.bundles.clear()
  else:reader_reads=0
  for p,h in pins.items():need(sha(p)==h,'Whole final physical input conservation')
  q=out/'registry-output-rows.json';q.write_text(json.dumps(rows,indent=2)+'\\n');pins[str(q.resolve())]=sha(q)
  report=dict(passed=passed,frontier=stage,scope_identity=SCOPE,ROOT_admission_path=str(admission_path),ROOT_admission_sha256=admission_sha,configuration_sha256=A['configuration']['sha256'],original_validation_sha256=C['validation']['sha256']if'C'in locals()else None,reader_closed=reader is None or reader.closed,ordinary_export_targets_read=reader_reads,counts=counts,corroboration=corroboration,output=dict(path=str(q),sha256=pins[str(q.resolve())],fields=['source_before_metadata','source_before_backing_hex','source_computed_after_metadata','source_computed_after_backing_hex','source_store','source_realloc_input']),source_AFTER_seed=False,candidate_AFTER_machine_seed=False,canonical_reader_opened=False,capture_archive_opened=False,native_worker_launched=False,x86_or_family_replay=False,page_geometry_claim=False,whole_original_State_claim=False,full_original846_CPU_execution_claim=False,initializer_credit=0,accepted_function_credit=0,scope='846 source registry predictions with source before/after metadata, backing, literal store and complete realloc input; whole AFTER registry endpoint, carry and cleanup-vector joins. Not CRT whole-page policy, lock13 counts or paired141 credit.',files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\\n');print(json.dumps(dict(passed=passed,report=str(q),report_sha256=sha(q),frontier=stage)))
if __name__=='__main__':main(*sys.argv[1:])
'''
def build():
 assert sha(PRODUCER)==PRODUCER_SHA and sha(INVERSE)==INVERSE_SHA
 producer=PRODUCER.read_text();inverse=json.loads(INVERSE.read_bytes())
 original,consumer_block,dropped=derive_block(producer,inverse)
 return HEADER+consumer_block+FOOTER,original,consumer_block,dropped
def main():
 text,original,block,dropped=build();target=R/'tools/m4-startup141-paired/registry_output141_v1.py'
 assert not target.exists(),'Fresh consumer version';target.write_bytes(text.encode())
 assert text.count(block)==1
 out=R/'reports/m4-startup141-paired/registry-output-consumer-preparation-r1';assert not out.exists();out.mkdir()
 value=dict(prepared_only=True,consumer_executed=False,export_opened=False,producer=dict(path=str(PRODUCER),sha256=PRODUCER_SHA),inverse=dict(path=str(INVERSE),sha256=INVERSE_SHA),
  deltas=dict(D1_dropped_page_geometry_lines=dropped,D2_serializer=dict(parent=json.loads(INVERSE.read_bytes())[0]['parent'],child=json.loads(INVERSE.read_bytes())[0]['child'])),
  producer_block_lines=len(original.splitlines()),consumer_block_lines=len(block.splitlines()),consumer=dict(path=str(target),sha256=sha(target)),accepted_function_credit=0,
  files={str(p):sha(p)for p in(PRODUCER,INVERSE,target,Path(__file__).resolve())})
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(consumer=str(target),consumer_sha256=sha(target),preparation=str(q),preparation_sha256=sha(q))))
if __name__=='__main__':main()
