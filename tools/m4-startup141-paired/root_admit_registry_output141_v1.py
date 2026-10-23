"""ROOT independent admission of registry_output141_v1; runs no consumer main.

Independent of the generator: re-derives the consumer registry block from the
exact producer by fixed measured line numbers (75..102), requires every consumer
input to equal the hash the passing source-r7 producer itself pinned, and runs
pure adverse controls against the consumer's corroboration predicate.
"""
from pathlib import Path
import hashlib,importlib.util,json,random,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 producer=pin(R/'tools/m4-original141-source/replay_original141_v10.py','65421344550b0e133967d21becb2b7b120f58f653a0bca2a2432d42e315c1553')
 inverse=pin(R/'reports/m4-startup141-paired/registry-output-preparation-r1/inverse.json','65dcfcf8badd733cc7d583e16130c656fee8c6686425b0d7db9518c6ec8740d5')
 locations=pin(R/'reports/m4-startup141-paired/registry-output-preparation-r1/source-locations.json')
 consumer=pin(R/'tools/m4-startup141-paired/registry_output141_v1.py');generator=pin(R/'tools/m4-startup141-paired/prepare_registry_output141_v1.py')
 prep=pin(R/'reports/m4-startup141-paired/registry-output-consumer-preparation-r1/report.json');P=json.loads(prep.read_bytes())
 assert P['consumer']['sha256']==pins[str(consumer)]and P['prepared_only']and not P['consumer_executed']and not P['export_opened']
 # 1. Independent block derivation by measured line numbers.
 L=json.loads(locations.read_bytes());assert L['source_sha256']==pins[str(producer)]and L['locations']['model_load']==75 and L['locations']['old_rows_output']==101
 lines=producer.read_text().splitlines(keepends=True);block=lines[74:102]
 assert block[0].startswith("  registry_model=load(")and block[-1].startswith("   need(len(carried)==111")
 assert block[22].startswith('    for i,p in enumerate(whole):')and block[25].startswith("    for side in('before','after'):need(len(reader.data(stem+f'/constructor-global-")
 inv=json.loads(inverse.read_bytes());assert len(inv)==1 and block[26]=='    '+inv[0]['parent']+'\n'
 derived=block[:22]+['    '+inv[0]['child']+'\n']+block[27:]
 text=consumer.read_text();expected=''.join(derived);assert text.count(expected)==1,'Consumer block is the exact producer block with D1/D2 only'
 assert P['consumer_block_lines']==len(derived)and P['producer_block_lines']==len(block)
 # Child serializer adds only already-computed source values (no record/after).
 child=inv[0]['child'];assert 'record'not in child and 'after'not in child.replace('computed_after','').replace('source_computed_after_backing_hex','')
 # 2. Inputs must be exactly what the passing producer source-r7 pinned.
 r7=pin(R/'reports/m4-original141-source/source-r7/report.json');S=json.loads(r7.read_bytes());assert S['passed']is True and S['reader_closed']is True and S['counts']['phases']==846 and S['counts']['registry_growths']==120
 produced=S['files'];assert produced[str(producer)]==pins[str(producer)],'Same producer code as passing receipt'
 rows_path=R/'reports/m4-original141-source/source-r7/registry-source-relations.json';pin(rows_path);assert produced[str(rows_path.resolve())]==pins[str(rows_path.resolve())]
 cfg=R/'reports/m4-original141-source/configuration-preparation-r3/configuration.json';cfg_sha='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0';assert S['configuration_sha256']==cfg_sha;pin(cfg,cfg_sha);C=json.loads(cfg.read_bytes())
 inputs=[cfg,Path(C['validation']['path']),Path(C['selected_order']['path']),Path(C['callbacks']['path']),Path(C['validation']['path']).parent/'whole-registry-BEFORE.json',R/'tools/m4-startup138-original/export_reader_r2.py',R/'tools/m4-startup138-paired/registry_backing_policy.py']
 cb=json.loads(Path(C['callbacks']['path']).read_bytes());inputs+=[Path(r['authority_path'])for r in cb['rows']]
 V=json.loads(Path(C['validation']['path']).read_bytes());row=[x for x in V['paired_exports']if x['branch']=='original'];assert len(row)==1;row=row[0]
 inputs+=[Path(row['index_path']),Path(row['payload_path'])]
 for p in inputs:
  key=str(p.resolve());assert key in produced,('Not consumed by passing producer',key);pin(p,produced[key])
 assert produced[str(Path(row['payload_path']).resolve())]==row['payload_sha256']and produced[str(Path(row['index_path']).resolve())]==row['index_sha256']
 # 3. Pure adverse controls on the consumer's corroboration predicate.
 spec=importlib.util.spec_from_file_location('registry_output141_review',consumer);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 rng=random.Random(141)
 def synth():
  mine=[];theirs=[]
  for i in range(846):
   cbv=rng.choice([None,0x401000+i]);growth=cbv is not None and i%7==0;b=rng.randbytes(16+4*(i%5))
   t=dict(sequence=i//141,phase=i%141,root=0x400000+i,callback=cbv,growth=growth,full_source_registry_bytes=len(b),source_backing_sha256=hashlib.sha256(b).hexdigest(),candidate_AFTER_input=False)
   m=dict(t,source_before_metadata=[1,1,len(b),1],source_before_backing_hex=b.hex(),source_computed_after_metadata=[1,5,len(b),1],source_computed_after_backing_hex=b.hex(),source_store=None if cbv is None else dict(PC=0x78004a67,address=1,width=4,value=cbv),source_realloc_input=dict(old_begin=1)if growth else None)
   mine.append(m);theirs.append(t)
  return mine,theirs
 mine,theirs=synth();ok=M.corroborate(mine,theirs);assert ok['rows_corroborated']==846
 adverse=[]
 def refuse(label,mutate):
  a,b=synth();mutate(a,b)
  try:M.corroborate(a,b)
  except ValueError:adverse.append(label);return
  raise AssertionError('Admitted adverse '+label)
 refuse('callback_changed',lambda a,b:a[5].__setitem__('callback',(a[5]['callback']or 0)+4))
 refuse('growth_flipped',lambda a,b:a[7].__setitem__('growth',not a[7]['growth']))
 refuse('after_backing_not_hashed_prediction',lambda a,b:a[3].__setitem__('source_computed_after_backing_hex','00'+a[3]['source_computed_after_backing_hex'][2:]if a[3]['source_computed_after_backing_hex'][:2]!='00'else'11'+a[3]['source_computed_after_backing_hex'][2:]))
 refuse('missing_row',lambda a,b:(a.pop(),b.pop()))
 refuse('store_without_callback',lambda a,b:next(r for r in a if r['callback']is None).__setitem__('source_store',dict(PC=0x78004a67,address=1,width=4,value=1)))
 refuse('realloc_without_growth',lambda a,b:next(r for r in a if not r['growth']).__setitem__('source_realloc_input',dict(old_begin=1)))
 refuse('type_drift_bool_to_int',lambda a,b:a[0].__setitem__('candidate_AFTER_input',0))
 refuse('extra_producer_field',lambda a,b:b[2].__setitem__('extra',1))
 bad=expected.replace('need(after==prediction','need(after!=prediction',1);assert text.replace(expected,bad).count(expected)==0;adverse.append('static_block_mutation_detected')
 for p,h in list(pins.items()):assert sha(p)==h,p
 pins[str(Path(__file__).resolve())]=sha(__file__)
 out=R/'reports/m4-startup141-paired/ROOT-registry-output-admission-r1';assert not out.exists();out.mkdir()
 value=dict(passed=True,independent_review=True,scope_identity='original141_registry_output_consumer',configuration=dict(path=str(cfg.resolve()),sha256=cfg_sha),producer_rows=dict(path=str(rows_path.resolve()),sha256=pins[str(rows_path.resolve())]),
  independent_block_derivation='producer lines 75..102 by measured line numbers; D1 drops lines 97..100; D2 replaces line 101 with inverse child',inputs_equal_passing_producer_pins=len(inputs),adverse_controls=adverse,consumer_executed=False,export_opened=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(admission=str(q),sha256=sha(q),adverse=len(adverse),inputs=len(inputs))))
if __name__=='__main__':main()
