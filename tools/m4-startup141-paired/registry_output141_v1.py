"""ROOT-admitted registry-only original141 ordinary-export consumer (v1).

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
  registry_model=load(R/'tools/m4-startup138-paired/registry_backing_policy.py','original141_registry')
  registry_before=read(Path(C['validation']['path']).parent/'whole-registry-BEFORE.json');need(len(registry_before)==846,'Every current own registry input')
  stage='whole846 own registry source and measured page domains'
  for seq in range(6):
   last=None;carried=[]
   for phase,item in enumerate(order):
    stem=f'phase/{seq}/{phase}';before=registry_before[seq*141+phase];need((before['sequence'],before['phase'],before['root'])==(seq,phase,item['entry']),'Exact current phase/root input')
    meta=before['BEFORE_metadata'];backing=bytes.fromhex(before['BEFORE_backing_hex']);need(backing[:len(carried)*4]==struct.pack('<'+'I'*len(carried),*carried),'Source callback prefix reaches current own BEFORE')
    if last is not None:need(meta==last['metadata']and backing==last['backing'],'Whole own registry source chronological carry')
    ledger=reader.data(stem+'/api-ledger.bin');need(len(ledger)%104==0,'Whole26DWORD API records');birth=None
    for ai,w in enumerate(struct.iter_unpack('<26I',ledger)):
     need(w[9]==w[19]==0,'Raw API PC zero is exact producer schema, not CPU exclusion')
     if w[24]==3 and w[22]==meta[0]and w[10]:
      need(birth is None and w[25]==0x78011c2d,'One exact source registrar successful growth boundary')
      initial=reader.data(stem+f'/api-initial/{ai}/bytes.bin');size=reader.words(stem+f'/api-initial/{ai}/size.bin',1)[0];need(len(initial)==size,'Full genuine APIinitial backing before guest writes')
      birth=dict(old_begin=w[22],requested=w[23],source_CALL_pc=0x78011c27,return_word=w[25],pointer=w[10],initial=initial,API_index=ai)
    cb=callback_byroot.get(item['entry']);prediction=registry_model.derive(meta,backing,cb,birth)
    # No equality target data is opened until this phase prediction terminates.
    record=reader.data(stem+'.bin');need(len(record)==356992 and struct.unpack_from('<5I',record)==(seq,seq//3,phase,item['slot'],item['entry']),'Actual current fixed root record identity')
    after=list(struct.unpack_from('<4I',record,356464));need(after==prediction['metadata']and record[356480:356480+after[2]]==prediction['backing'],'Whole source-derived registry endpoint')
    last=prediction
    if cb is not None:carried.append(cb)
    rows.append(dict(sequence=seq,phase=phase,root=item['entry'],callback=cb,growth=prediction['growth'],source_before_metadata=list(meta),source_before_backing_hex=backing.hex(),source_computed_after_metadata=list(prediction['metadata']),source_computed_after_backing_hex=prediction['backing'].hex(),source_store=prediction['source_store'],source_realloc_input=None if birth is None else dict(old_begin=birth['old_begin'],requested=birth['requested'],source_CALL_pc=birth['source_CALL_pc'],return_word=birth['return_word'],pointer=birth['pointer'],API_index=birth['API_index'],whole_initial_bytes=len(birth['initial']),initial_hex=birth['initial'].hex()),full_source_registry_bytes=len(prediction['backing']),source_backing_sha256=hashlib.sha256(prediction['backing']).hexdigest(),candidate_AFTER_input=False))
   need(len(carried)==111 and reader.data(f'cleanup/{seq}/registry.bin')==struct.pack('<111I',*carried),'Exact111 source-derived callback vector at actual cleanup')
  counts.update(phases=len(rows),callbacks=111,registry_callback_stores=sum(r['callback']is not None for r in rows),registry_growths=sum(r['growth']for r in rows),source_realloc_inputs=sum(r['source_realloc_input']is not None for r in rows))
  stage='corroborate against passing source-r7 compact rows'
  corroboration=corroborate(rows,read(A['producer_rows']['path'],A['producer_rows']['sha256']))
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader_reads=len(reader.reads);reader.entries.clear();reader.bundles.clear()
  else:reader_reads=0
  for p,h in pins.items():need(sha(p)==h,'Whole final physical input conservation')
  q=out/'registry-output-rows.json';q.write_text(json.dumps(rows,indent=2)+'\n');pins[str(q.resolve())]=sha(q)
  report=dict(passed=passed,frontier=stage,scope_identity=SCOPE,ROOT_admission_path=str(admission_path),ROOT_admission_sha256=admission_sha,configuration_sha256=A['configuration']['sha256'],original_validation_sha256=C['validation']['sha256']if'C'in locals()else None,reader_closed=reader is None or reader.closed,ordinary_export_targets_read=reader_reads,counts=counts,corroboration=corroboration,output=dict(path=str(q),sha256=pins[str(q.resolve())],fields=['source_before_metadata','source_before_backing_hex','source_computed_after_metadata','source_computed_after_backing_hex','source_store','source_realloc_input']),source_AFTER_seed=False,candidate_AFTER_machine_seed=False,canonical_reader_opened=False,capture_archive_opened=False,native_worker_launched=False,x86_or_family_replay=False,page_geometry_claim=False,whole_original_State_claim=False,full_original846_CPU_execution_claim=False,initializer_credit=0,accepted_function_credit=0,scope='846 source registry predictions with source before/after metadata, backing, literal store and complete realloc input; whole AFTER registry endpoint, carry and cleanup-vector joins. Not CRT whole-page policy, lock13 counts or paired141 credit.',files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(q),report_sha256=sha(q),frontier=stage)))
if __name__=='__main__':main(*sys.argv[1:])
