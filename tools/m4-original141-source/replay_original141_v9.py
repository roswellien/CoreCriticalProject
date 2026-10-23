"""Independently admitted finite original141 source orchestration; ordinary only.

Full chronology means846 own registry predictions and complete observed page
geometry. Literal whole constructor18 replay is a separate subset. Retained
family child receipts must be current141; this never relabels original138 proof.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(admission_path,admission_sha,configuration_path,configuration_sha,name):
 admission_path=Path(admission_path).resolve();need(sha(admission_path)==admission_sha,'Exact independently supplied ROOT admission')
 admission=json.loads(admission_path.read_bytes());need(admission['passed']is True and admission['independent_review']is True and admission['scope_identity']=='original141_finite_source_replay','Independent source admission before every import/reader')
 need(admission['configuration_sha256']==configuration_sha,'Exact reviewed current input configuration')
 admitted={}
 for p,h in admission['files'].items():
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Only sealed ordinary source inputs')
  need(str(p)not in admitted and sha(p)==h,'Unique whole admitted ordinary file before import');admitted[str(p)]=h
 admitted[str(admission_path)]=admission_sha
 out=R/'reports/m4-original141-source'/name;ctorout=out.parent/(name+'-constructors');need(not out.exists()and not ctorout.exists(),'Fresh original141 aggregate and exact constructor child namespaces');out.mkdir(parents=True)
 childdirs={suffix:out.parent/(name+'-'+suffix)for suffix in('constructors','formatters','old4','MFC','widgets')}
 need(all(not p.exists()for p in childdirs.values()),'All exact five source output children fresh')
 def own_output(p):return p.is_relative_to(out.resolve())or any(p.is_relative_to(q.resolve())for q in childdirs.values())
 pins={str(admission_path):admission_sha};reader=None;passed=False;rows=[];children=[];counts={};stage='input admission'
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','Never open canonical capture')
  actual=sha(p);need(own_output(p)or admitted.get(str(p))==actual,'Exact ROOT-admitted external input/code, no fallback')
  need(h is None or h==actual,'Exact field physical identity');need(str(p)not in pins or pins[str(p)]==actual,'Stable ordinary source input');pins[str(p)]=actual;return p
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
  pin(__file__);C=read(configuration_path,configuration_sha);need(C['schema']=='mw34-original141-source-input-contract-v1','Exact current141 configuration schema')
  sys.addaudithook(audit)
  V=read(C['validation']['path'],C['validation']['sha256']);need(V['passed']and V['reader_closed']and V['counts']['phases']==846 and V['callbacks']==111 and V['record_bytes']==356992 and V['combined_pages']==69,'Current genuine846 strict ordinary export')
  prep=read(C['source_preparation']['path'],C['source_preparation']['sha256']);order=read(C['selected_order']['path'],C['selected_order']['sha256']);need(len(order)==141 and len({r['entry']for r in order})==141,'Physical current selected141 table')
  need([order[i]['entry']for i in(13,14,15,39,86)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40,0x4b7f70],'Current literal constructor/MFC/tree chronology')
  need(C['source_preparation']['sha256']==V['preparation_sha256'],'Same actually compiled original source preparation')
  callback=read(C['callbacks']['path'],C['callbacks']['sha256']);need(callback['schema']=='mw34-source-callback111-v1'and len(callback['rows'])==111,'Distinct111 literal source callback bindings')
  callback_byroot={r['root']:r['callback']for r in callback['rows']};need(len(callback_byroot)==111 and all(r in {v['entry']for v in order}for r in callback_byroot),'Complete actual selected callback roots')
  for r in callback['rows']:
   authority=read(r['authority_path'],r['authority_sha256']);need(r['callback']>0 and r['authority_row']is not None,'Explicit physical source callback authority')
   node=authority
   for part in r['authority_row']:node=node[part]
   need(node==r['callback'],'Exact named source contract callback value; no candidate output')
  reuse=read(R/'reports/m4-original141-source/retained-positive-family-r2/manifest.json','2e6ba0bb9c6fcbe9546ee7e12a196643863b2b38551581578b67a67226153262');need(reuse['schema']=='mw34-current141-retained-positive-families-v1'and reuse['configuration_sha256']==configuration_sha and reuse['original_validation_sha256']==C['validation']['sha256']and reuse['failed_parent_passed']is False and reuse['failed_parent_reader_closed']is True,'Only four actual closed current positive children, failed parent never passes')
  prior=read(reuse['failed_parent_path'],reuse['failed_parent_sha256']);need(prior['passed']is False and prior['reader_closed']and prior['configuration_sha256']==configuration_sha and prior['original_validation_sha256']==C['validation']['sha256'],'Exact failed same-input parent identity/closure only')
  reused={row['domain']:row for row in reuse['rows']};need(len(reuse['rows'])==len(reused)==4 and set(reused)=={'constructor18','formatter4','old4','new_MFC'},'Exactly distinct four retained positive domains')
  for dep,h in reuse['files'].items():pin(dep,h)
  for domain,row in reused.items():
   pin(row['helper_path'],row['helper_sha256']);g=read(row['path'],row['sha256']);need(g['passed']and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False and g['files'][row['helper_path']]==row['helper_sha256'],'Actual current passed helper/source family, no historical outcome oracle')
   need(any(v['domain']==domain and v['receipt']==row['path']and v['sha256']==row['sha256']for v in prior['children']),'Exact positive child physically recorded by failed parent')
   for dep,h in g['files'].items():pin(dep,h)
  E=load(R/'tools/m4-startup138-original/export_reader_r2.py','original141_export');reader=E.ExportReader(C['validation']['path'],C['validation']['sha256'],'original',pin)
  reader.words=lambda logical,n:struct.unpack('<'+'I'*n,reader.data(logical))
  header=reader.data('header.bin');need(len(header)==32 and header[:8]==bytes.fromhex(C['physical_header_magic_hex'])and struct.unpack_from('<6I',header,8)==(1,6,141,846,43,356992),'Actual physical writer header and all numeric141 geometry')
  need(reader.data('COMPLETE.txt')==b'complete','Terminal original capture copied by sealed export')
  metadata=read(C['source_input_metadata']['path'],C['source_input_metadata']['sha256']);need(metadata['source_metadata_view']and metadata['actual_compiled_preparation_sha256']==C['source_preparation']['sha256']and metadata['selected_order']==order,'Exact physically reviewed current source metadata view')
  whole=C['whole69_page_order'];need(len(whole)==len(set(whole))==69 and whole==metadata['observed_pages']+metadata['extra_whole_source_pages'],'Exact compiled whole69 page inventory')
  continuity=load(R/'tools/m4-original141-source/retained_corpus141_v2.py','original141_source_continuity').prove(C,pin);need(continuity['passed'],'All3980 accepted131 physical source spans/current141 exact body and table continuity');counts.update({k:v for k,v in continuity.items()if type(v)is int})
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
    for i,p in enumerate(whole):
     for side,offset in(('before',2276),('after',178404)):
      b=record[offset+i*4096:offset+(i+1)*4096]if i<43 else reader.data(stem+f'/extra-{side}/{p}.bin');need(len(b)==4096,'Complete observed source endpoint page, not an additional literalCPU claim')
    for side in('before','after'):need(len(reader.data(stem+f'/constructor-global-{side}.bin'))==4096,'Complete every-phase observed constructor-global endpoint')
    rows.append(dict(sequence=seq,phase=phase,root=item['entry'],callback=cb,growth=prediction['growth'],full_source_registry_bytes=len(prediction['backing']),source_backing_sha256=hashlib.sha256(prediction['backing']).hexdigest(),candidate_AFTER_input=False))
   need(len(carried)==111 and reader.data(f'cleanup/{seq}/registry.bin')==struct.pack('<111I',*carried),'Exact111 source-derived callback vector at actual cleanup')
  counts.update(phases=len(rows),callbacks=111,registry_callback_stores=sum(r['callback']is not None for r in rows),registry_growths=sum(r['growth']for r in rows),observed_source_page_endpoints=846*69*2,observed_global5F2000_endpoints=1692)
  stage='literal current constructor18 source and computed11point PUSHFD'
  child=Path(reused['constructor18']['path']);pin(child,reused['constructor18']['sha256'])
  # Fresh outputs are scoped to this single aggregate's derived child directory.
  childdir=child.parent.resolve()
  need(childdir==Path(reused['constructor18']['path']).parent.resolve(),'Exact immutable retained positive constructor namespace')
  receipt=read(child);need(receipt['passed']and len(receipt['cases'])==18 and all(r['whole_GPR_EIP']and r['defined_EFLAGS']and r['whole_FX512']and r['whole_ENV28']for r in receipt['cases']),'All18 current own-BEFORE literal constructor endpoints')
  for p,h in receipt['files'].items():pin(p,h)
  children.append(dict(domain='constructor18',receipt=str(child),path=str(child),sha256=sha(child)));counts['literal_constructor_cases']=18
  stage='actual current retained finite-family literal source replay'
  for domain,suffix,tool,n in [('formatter4','formatters','format_source141_v2.py',24),('old4','old4','old4_source141_v2.py',24),('new_MFC','MFC','mfc_source141_v1.py',6),('widget','widgets','widget_source141_v4.py',42)]:
   childmodule=None
   if domain in reused:
    child=Path(reused[domain]['path']);g=read(child,reused[domain]['sha256']);need(reused[domain]['source_case_extent']==n and reused[domain]['helper_path']==str((R/'tools/m4-original141-source'/tool).resolve()),'Exact current positive extent/helper for retained domain')
   else:
    childmodule=load(R/'tools/m4-original141-source'/tool,'current141_'+domain)
    if domain=='new_MFC':childmodule.main(name+'-'+suffix,C,pin)
    else:childmodule.main(name+'-'+suffix,reader,C,pin)
    child=childdirs[suffix]/'report.json';g=read(child)
   need(g['passed']and g['original_validation_sha256']==C['validation']['sha256']and g['source_case_extent']==n and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False,'Actual current finite source family extent '+domain)
   for p,h in g['files'].items():pin(p,h)
   children.append(dict(domain=domain,receipt=str(child),path=str(child),sha256=sha(child)));counts[domain+'_source_cases']=n
   if domain=='formatter4':
    derived=read(child.parent/'source-derivations.json');need(len(derived)==24,'Fresh24 formatter own-source derivations');q=out/'original-Formatting-source-derivations.json';q.write_text(json.dumps(derived,indent=2)+'\n');pin(q)
   del childmodule
  tree=C['current_tree_source'];g=read(tree['path'],tree['sha256']);need(g['passed']and g['source_case_extent']==6 and g['original_validation_sha256']==C['validation']['sha256']and g['source_AFTER_seed']is False and g['canonical_reader_opened']is False,'Independent current six-source tree gate; no old138/native-original substitution')
  for p,h in g['files'].items():pin(p,h)
  children.append(dict(domain='tree',receipt=tree['path'],path=tree['path'],sha256=tree['sha256']));counts['tree_source_cases']=6
  derived=read(Path(tree['path']).parent/'original-Tree-source-derivations.json');need(len(derived)==6 and all(r['source']['phase']==86 for r in derived),'Current six own-source tree derivations');q=out/'original-Tree-source-derivations.json';q.write_text(json.dumps(derived,indent=2)+'\n');pin(q)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
  for p,h in pins.items():need(sha(p)==h,'Whole final physical source input conservation')
  q=out/'registry-source-relations.json';q.write_text(json.dumps(rows,indent=2)+'\n');pins[str(q.resolve())]=sha(q)
  report=dict(passed=passed,frontier=stage,configuration_sha256=configuration_sha,original_validation_path=str(C['validation']['path'])if'C'in locals()else None,raw_export_report_path=str(C['validation']['path'])if'C'in locals()else None,raw_export_report_sha256=C['validation']['sha256']if'C'in locals()else None,reader_closed=True,archive_sessions_opened=0,capture_archive_opened=False,candidate_AFTER_machine_seed=False,original_postRET_observed=False,original_postRET_source_derived=True,formatter_full_registration_provider_CPU_executed_by_model=False,original_validation_sha256=C['validation']['sha256']if'C'in locals()else None,counts=counts,children=children,cases=[r for r in children if r['domain']!='constructor18'],scope='846 registry source/backing predictions plus18 whole literal constructors and explicitly current retained finite-family proofs. Observed69+global endpoint geometry is not846fullCPU execution.',source_AFTER_seed=False,whole_original_State_claim=False,whole_original_TIB_claim=False,full_original846_CPU_execution_claim=False,ordinary_reader_closed=True,canonical_reader_opened=False,native_worker_launched=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(q),frontier=stage)))

if __name__=='__main__':main(*sys.argv[1:])
