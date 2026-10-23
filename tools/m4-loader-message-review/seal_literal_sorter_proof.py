"""Pin every evaluator source and audit whole ordinary compressed ledgers.

This is an author finite-source proof seal, not independent ROOT admission.
No native tool/object/DLL/source machine is executed by this sealing review.
"""
from pathlib import Path
import collections,gzip,hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];T=Path(__file__).parent
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/literal-sorter-source-proof-r1';need(not out.exists(),'Fresh proof seal');out.mkdir(parents=True);pins={};passed=False;counts=collections.Counter();controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact ordinary source proof physical pin');need(str(p)not in pins or pins[str(p)]==v,'Stable source proof identity');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def bad(name,fn):
  try:fn()
  except ValueError as e:controls.append(dict(name=name,passed=True,expected='refusal',reason=str(e)));return
  raise ValueError('Adverse source control unexpectedly passed '+name)
 try:
  directory=R/'reports/m4-loader-message-review/literal-sorter-evaluation-r4';d=read(directory/'report.json','a8b7f4c27d853db8724003c649a57bf7b1dc4e037f291e5382a3c524cb512de0');need(d['passed']and d['ambient_CALL_machine_synthetic']and d['static_literal_instructions']==952 and d['source_table_endpoint_equal']and not d['DLL_loaded'],'Exact finite source domain')
  for p,h in d['files'].items():pin(p,h)
  for i in range(1,9):pin(T/('evaluate_literal_sorter.py'if i==1 else'evaluate_literal_sorter_v'+str(i)+'.py'))
  # The v7 wrapper defines the fully materialized namespace but does not call
  # main; v8's only extra action was the separately recorded source evaluation.
  ns={'__file__':str(T/'evaluate_literal_sorter_v8.py'),'__name__':'source_materialization_only'};wrapper=(T/'evaluate_literal_sorter_v7.py').read_text();exec(compile(wrapper,str(T/'evaluate_literal_sorter_v7.py'),'exec'),ns);actual=ns['ns']['s'];p=out/'evaluation-materialized.py';p.write_text(actual);pin(p)
  program=read(directory/'source-program.json');pcs={r['pc']for r in program['rows']};need(len(pcs)==952,'All952 physical operand/width declarations')
  reached=set();previous=None;step=0;boundary=d['endpoints'][0]['steps'];expected=sum(x['steps']for x in d['endpoints'])
  with gzip.open(pin(directory/'source-PC-CPU-before-after.bin.gz'),'rb')as f:
   while raw:=f.read(84):
    need(len(raw)==84,'Every complete exact PC/CPU record');row=struct.unpack('<I20I',raw);pc=row[0];before=row[1:11];after=row[11:21];need(pc in pcs and before[9]==pc,'Every dynamic CPU record physically belongs to source PC');reached.add(pc)
    if previous is not None:
     if step==boundary:
      need(pc==0x10001000 and before[:4]==previous[:4]and before[5:9]==previous[5:9]and before[4]+4==previous[4],'Only explicit persistent second CALL frame projection')
     else:need(before[:9]==previous[:9],'Every projected CPU register/flag carries without per-instruction reseed')
    previous=after;step+=1
  need(step==expected==2188286 and len(reached)==d['actually_reached_distinct_source_PCs']==805,'All-and-only whole dynamic source extent');counts['whole_PC_CPU_records']=step;counts['whole_reached_source_PCs']=len(reached)
  with gzip.open(pin(directory/'source-operands.bin.gz'),'rb')as f:
   while raw:=f.read(20):
    need(len(raw)==20,'Every complete exact operand record');pc,address,value,width,write=struct.unpack('<5I',raw);need(pc in reached and width in(1,4)and write in(0,1),'Every source operand width/PC identity');need(0x10003000<=address and address+width<=0x1000e400 or 0x20000000<=address and address+width<=0x20020000,'Exact physical data or declared stack ownership')
    if write:need(0x10003010<=address and address+width<=0x10006158 or 0x20000000<=address and address+width<=0x20020000,'No source store beyond table/stack');counts['whole_operands']+=1
    else:counts['whole_operands']+=1
  need(counts['whole_operands']==d['source_operands']==638716,'Complete physical operand ledger')
  with gzip.open(pin(directory/'source-defined-flag-joins.bin.gz'),'rb')as f:
   while raw:=f.read(12):
    need(len(raw)==12,'Every complete flag-def record');consumer,producer,bit=struct.unpack('<3I',raw);need(consumer in reached and producer in reached and bit in(0,2,4,6,7,11),'Every flag join belongs to physical reached source');counts['whole_flag_definition_joins']+=1
  need(counts['whole_flag_definition_joins']==676292==d['counts']['source_defined_flag_consumers'],'All consumed flags have current source definitions')
  expected_table=pin(R/'reports/m4-loader-message-review/physical-r4/current-sorted-table-design.bin').read_bytes()
  for i in range(2):need(pin(directory/('source-sorted-table-'+str(i)+'.bin')).read_bytes()==expected_table and len(expected_table)==1577*8,'Whole finite1577 table endpoint, no sampled checksum shortcut')
  # Actual inherited base semantics are whole-byte identical except the finite
  # loop budget. Local SAR branch body only rebinds that base and same budget.
  old=pin(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py').read_text();new=pin(directory/'bounded-integer.py').read_text();need(new.replace('self.steps<=40000000','self.steps<=1000000')==old,'Exact inverse retained integer semantics')
  changed=expected_table[:-1]+bytes([expected_table[-1]^1]);bad('one_endpoint_byte_mutation_refused',lambda:need(changed==expected_table,'Whole table bytes equal'));bad('non_source_PC_refused',lambda:need(0x10001710 in reached,'Reached literal sort domain'))
  before=read(R/'reports/m4-loader-message-review/physical-r4/current-name-id-table.json');need(len(before['rows'])==1577 and before['whole_initial_table_sha256']!=d['endpoints'][0]['table_sha256'],'Authentic unsorted table changes through source')
  clone=read(R/'reports/m4-loader-message-review/recursive-lifter-build-r2/report.json','8d3458569ebe11786443b198bba58163de24ef8c818d10972753d44e8fdbed72');need(clone['passed']and not clone['clone_executed']and not clone['helper_retry_admitted'],'Compiled recursive tool remains unadmitted')
  for p,h in clone['files'].items():pin(p,h)
  for leaf in('lift_literal_sorter.py','build_recursive_lifter.py','build_recursive_lifter.ps1','build_recursive_lifter_v2.py','build_recursive_lifter_v2.ps1'):pin(T/leaf)
  notes=out/'claim-frontier.md';notes.write_text('''The source sorter algorithm now predicts the entire authentic1577 name-pointer/id table from file BEFORE, with literal952-row static closure and805 actually reached instructions across two persistent calls. Complete lossless PC/CPU,638716 operand and676292 source-defined flag joins are retained; all image bytes outside the table including resources remain unchanged. First call1351191 steps/162 recursive calls; second837095/127. Both table endpoints SHA101b909b2bb36780417a2a127a8aaee726f76466ea810439e14aeb3e195af615.

This is finite physical source evaluation using a declared synthetic ambient CALL/State/CPU/FX at preferred PE base. It does not authenticate actual Windows DllMain caller State, rebased module, actual executable load, host CRT allocation owner, notification/lifecycle effects, native insertion-sort program equivalence or connected47F760 acceptance. Source undefined flag representatives do not enter any consumed flag: every actual consumer is source-defined. Literal host entry objects exist O0/O2, but recursive helper lift timed out and is not closed.

The workspace-local recursive tool clone changes only completed-trace cache lookup before first-entry discovery; cache publication happens after body closure in TraceLifter.cpp. Baseline tool, semantics, project artifacts and installed Ghidra/REA are unchanged. ROOT must independently review the exact source/cache and linked tool before one bounded helper-lift retry. No new tool execution is admitted by this author seal. Native literal adapter integration, actual loader source-frame/provider proof and current paired/carry evidence remain separate future gates. Accepted count remains131/144.
''');pin(notes);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__);pin(sys.executable)
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Author physical finite-source sorter proof and whole ordinary lossless ledgers; not independent ROOT admission',counts=dict(counts),controls=controls,all_ordinary_ledger_readers_closed=True,whole_finite_table_source_prediction=passed,authentic_actual_DLL_caller_claim=False,whole_native_provider_source_equivalence=False,recursive_helper_lift_closed=False,clone_retry_admitted=False,archive_reader_opened=False,DLL_loaded=False,native_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main()
