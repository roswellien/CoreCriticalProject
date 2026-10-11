"""Archive-free inherited literal scope and raw paired façade controls."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'));sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;counts={};rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  import flag_consumers as FC,paired_exports as EX
  for r in range(1,5):
   receipt=json.loads(pin(ROOT/f'reports/m4-joint-startup131-source/preparation-r{r}/report.json').read_bytes());assert receipt['passed']
   for p,h in receipt['files'].items():pin(p,h)
  model_receipt=json.loads(pin(ROOT/'reports/m4-formatting-source/persistent-family-model-r1/report.json','53c2a9f6dc3ede4ed5b089ff7c92490bbcdd4113679fc35ba830a4e359f50887').read_bytes());G=load(pin(model_receipt['model'],model_receipt['model_sha256']),'current130_unchanged_literal_scope');program,callbacks=G.source_program()
  J=load(ROOT/'tools/m4-joint-startup27-review/observe.py','current130_legacy_scope');m,c,inst,schedule=J.models();prepared=json.loads(pin(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes());old=json.loads(pin(ROOT/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c').read_bytes());assert [x for x in prepared['selected_order']if x['entry']!=0x5ae3e4]==old['selected_order']
  class Dummy:
   def reg(self,name):return 0
  # Every source conditional mnemonic has an explicit mapping. Dormant rows
  # remain uncredited; actual consumers are checked before each actual step.
  conditional=[r for r in program.values()if r['mnemonic'].startswith(('j','cmov','set'))]
  for r in conditional:rows.append(dict(PC=r['pc'],mnemonic=r['mnemonic'],flags=FC.names(Dummy(),r)))
  legacy=[]
  for item in prepared['selected_order']:
   entry=item['entry']
   if entry in inst:
    consumers=[r for r in inst[entry]if r['mnemonic'].startswith(('j','cmov','set'))or r['mnemonic']in('adc','sbb','cmc','lahf','pushf','pushfd','loopz','loope','loopnz','loopne','rcl','rcr')]
    legacy.append(dict(root=entry,instructions=len(inst[entry]),architectural_consumer_rows=consumers))
  # Exact current pure façade construction plus index/payload mutation controls.
  fake_transport=out/'synthetic-transport.json';fake_transport.write_text('{}\n');pin(fake_transport)
  class Synthetic:
   entries={'empty.bin':None,'whole.bin':None}
   def data(self,key):return b''if key=='empty.bin'else bytes(range(256))
  e=EX.Export(out/'synthetic','original',fake_transport,pin);e.copy(Synthetic());row=e.finish();f=EX.Facade(row,pin);assert f.data('whole.bin')==bytes(range(256))and f.data('empty.bin')==b'';f.close()
  mutation_controls=[]
  value=json.loads(Path(row['index_path']).read_bytes());bad=dict(row);q=out/'bad-index.json';value['entries']['whole.bin']['offset']=1;q.write_text(json.dumps(value));bad.update(index_path=str(q),index_sha256=sha(q))
  try:EX.Facade(bad,lambda p,h=None:Path(p))
  except ValueError as x:assert 'contiguous extent'in str(x);mutation_controls.append('overlapping/gapped directory denied')
  else:raise ValueError('Malformed export directory admitted')
  f=EX.Facade(row,pin);v=dict(f.entries['whole.bin']);f.entries['whole.bin']=dict(v,sha256='0'*64)
  try:f.data('whole.bin')
  except ValueError as x:assert 'per-access'in str(x);mutation_controls.append('individual changed digest denied')
  else:raise ValueError('Changed accessed payload digest admitted')
  finally:f.close()
  (out/'source-program-scope.json').write_text(json.dumps(dict(conditional_catalog=rows,legacy_source_catalog=legacy,current_literal_model_path=model_receipt['model'],current_literal_model_sha256=model_receipt['model_sha256'],callback_offsets=sorted(set(x for offsets in callbacks.values()for x in offsets))),indent=2)+'\n');pin(out/'source-program-scope.json')
  counts=dict(current130_order_unchanged=130,new131_inserted_phase=13,unchanged_literal_program_rows=len(program),conditional_mappings=len(rows),current_callback_PCs=len(callbacks),legacy_catalog_roots=len(legacy),export_contiguous_extent_and_full_digest_passed=True,export_mutation_controls=mutation_controls)
  pin(__file__);pin(sys.executable)
  for p,h in files.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Archive-free unchanged130 ordering/model literal construction, finite conditional mapping and paired export format mutation controls; actual flag/read/domain/byte equality remains full reader obligation',counts=counts,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
