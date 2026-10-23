"""Ordinary source/inverse review and adversarial metadata/target controls.

The reviewer authored the driver adaptation: this prepares ROOT review inputs
and deliberately does not grant admission or run the full source consumer.
"""
from pathlib import Path
import ast, collections, hashlib, importlib.util, json, struct, sys, traceback, types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/review-r3';assert not out.exists();out.mkdir(parents=True)
 pins={};checks=[];passed=False;findings=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v)
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def reject(name,fn):
  try:fn()
  except (ValueError,AssertionError):checks.append(dict(name=name,rejected=True));return
  raise AssertionError('Missing rejection: '+name)
 try:
  prep=R/'reports/m4-startup141-source/preparation-r2'
  d=json.loads(pin(prep/'report.json','c8be199dd1c7c9dc749907d9f2ed6bf15b7132ac8e0acb75ebf7fff9a784fcdb').read_bytes())
  for p,h in d['files'].items():pin(p,h)
  parent=pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py','093dbb3ddac7cab868058c45f6b7a14280a8a2a49ee33b06d5d931345b79e0d2')
  child=pin(prep/'compare_provider141.py','beb4665dc1a62c51374efb72089c9bcf4844216ba8c798f0ee2f76452ca0ac2f')
  deltas=json.loads(pin(prep/'driver-deltas.json').read_bytes());reverse=child.read_text()
  assert len(deltas)==27
  for row in reversed(deltas):assert reverse.count(row['new'])==row['count'];reverse=reverse.replace(row['new'],row['old'])
  assert reverse==parent.read_text()
  ast.parse(child.read_text());checks.append(dict(name='All27 exact driver replacements reverse to complete source6 body',passed=True))
  assert (d['expected_native_phases'],d['expected_constructor_executions'],d['expected_constructor_global_BEFORE'],d['expected_constructor_global_AFTER'],d['expected_constructor_global_endpoints_total'])==(1692,36,1692,1692,3384)
  t=child.read_text()
  for guard in ("counts['whole_page_BEFORE']==counts['whole_page_AFTER']==1692*69", "counts['whole_constructor_global_BEFORE']==counts['whole_constructor_global_AFTER']==1692", "len(constructor_rows)==36", "len(expected_callbacks)==111", "len(fs_observations)==84", "len(fsframes)==28 and len(rawrecords)==56", "F.COUNTS['complete130_provider_sequences']==12", "READS<=set(PINS)"):
   assert guard in t,guard
  checks.append(dict(name='All inherited phase/provider/whole69-page/dependency gates retained;3384 additional global endpoints',passed=True))
  oldparent=pin(R/'reports/m4-joint-startup138-source/preparation-r11/final_observer138.py')
  currentparent=pin(R/'reports/m4-native141-source/observer-preparation-r5/final_observer141_parent.py')
  x=currentparent.read_text()
  changes=[("_one('len(allocations)==len(responses.allocations)==85','len(allocations)==len(responses.allocations)==92')","_one('len(allocations)==len(responses.allocations)==85','len(allocations)==len(responses.allocations)==98')"),
   ('''_one("sum(a.get('kind',1)==4 for a in responses.allocations)==65","sum(a.get('kind',1)==4 for a in responses.allocations)==68")''','''_one("sum(a.get('kind',1)==4 for a in responses.allocations)==65","sum(a.get('kind',1)==4 for a in responses.allocations)==74")'''),
]
  # The cleanup lookup addition has a deliberately exact fresh-constructor union.
  added='_one("record=next(r for r in self.mfc if r[\'words\'][18]==owner[\'generation\'])","record=next(r for r in self.mfc+self.constructor_mfc if r[\'words\'][18]==owner[\'generation\'])")\n'
  assert x.count(added)==1;x=x.replace(added,'')
  for extra in ("_one('len(roots)==108','len(roots)==111')\n",'_one("COUNTS[\'selected_registration_closures\']+=108","COUNTS[\'selected_registration_closures\']+=111")\n'):
   assert x.count(extra)==1;x=x.replace(extra,'')
  for a,b in reversed(changes):assert x.count(b)==1,(b,x.count(b));x=x.replace(b,a)
  assert x==oldparent.read_text()
  wrapper=pin(R/'reports/m4-native141-source/observer-preparation-r5/final_observer141_parent_v2.py').read_text()
  assert wrapper.replace('import final_observer141_parent as F','import final_observer138 as F')==pin(R/'reports/m4-joint-startup138-source/preparation-r11/final_observer138_v2.py').read_text()
  checks.append(dict(name='Parent observer only98 owners/74kind4/111source callbacks/6cleanup lookup extension; old68 MFC and101+n replay body preserved',passed=True))
  C=load('consumer_review_carried_model',R/'tools/m4-native141-source/persistent_constructors_v4.py')
  def flag_machine(outer,arch):
   m=object.__new__(C.Machine);m._source_undefined_flags=outer;m.arch_undefined=arch;m.constructor_active=True;m.constructor_FS=[];m.constructor_root=C.ROOTS[0];return m
  outer={'AF':{'PC':0x58af8d,'source':True}}
  m=flag_machine(outer,{'AF':0x58af8d});m.end_constructor();assert m._source_undefined_flags==outer and not m.constructor_active
  checks.append(dict(name='Return preserves exact richer outer undefined-flag producer metadata',passed=True))
  reject('Wrong undefined producer cannot cross constructor return',lambda:flag_machine(outer,{'AF':0x58af8e}).end_constructor())
  reject('Missing undefined flag cannot cross constructor return',lambda:flag_machine(outer,{}).end_constructor())
  reject('Extra undefined flag cannot cross constructor return',lambda:flag_machine(outer,{'AF':0x58af8d,'OF':0x58af8d}).end_constructor())
  U=load('consumer_review_named_inputs',R/'tools/m4-native141-source/constructor_native_outputs141_v2.py')
  program,callbacks=C.source_program()
  class ImportMachine:
   def __init__(self):
    self.program=program;self.cells={0x5bb4c8:0x80000339,0x5bb4bc:0x80000337,0x5bb52c:0x1decb0};self.corrupt_opcode=False
   def bytes(self,a,n):
    if a in self.cells:return struct.pack('<I',self.cells[a])[:n]
    b=bytes.fromhex(program[a]['bytes_hex']);return bytes([b[0]^1])+b[1:]if self.corrupt_opcode else b
  im=ImportMachine();U.install_named(im,types.SimpleNamespace(pin=pin))
  for pc,a,raw,target in ((0x5abd1a,0x5bb4c8,0x80000339,0x5f401782),(0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0),(0x5ac11e,0x5bb52c,0x1decb0,0x78004a36)):
   assert im.constructor_named_input_prover(im,pc,a,raw,target)
  checks.append(dict(name='Three physically named carried opcode/raw-cell/import identity joins',passed=True))
  reject('Wrong named target',lambda:im.constructor_named_input_prover(im,0x5abd26,0x5bb4bc,0x80000337,0x5f401782))
  im.cells[0x5bb4bc]^=1
  reject('Changed carried raw import cell',lambda:im.constructor_named_input_prover(im,0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0));im.cells[0x5bb4bc]^=1
  im.corrupt_opcode=True
  reject('Changed physical import instruction byte',lambda:im.constructor_named_input_prover(im,0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0))
  controls=json.loads(pin(R/'reports/m4-141-consumer-review/observer-controls-r1/report.json','bd99686adb97d11c53ac6b12de563cfd772072f336086c53bc26ad198020442e').read_bytes());assert controls['passed']and len(controls['checks'])==12
  for p,h in controls['files'].items():pin(p,h)
  checks.append(dict(name='Fresh12 positive/adverse observer union/checkpoint/projection/35frame70record controls',passed=True))
  for path in (R/'reports/m4-startup141-source/consumer-wiring-preflight-r1/report.json',R/'reports/m4-startup141-source/export-root-review-r3/report.json',R/'reports/m4-native141-source/observer-preparation-r5/report.json'):
   receipt=json.loads(pin(path).read_bytes());assert receipt['passed']
   for p,h in receipt['files'].items():pin(p,h)
  findings.append(dict(kind='review_requirement',detail='ROOT must independently review the authored driver27 changes and admit the consumer; this reviewer authored the adaptation and cannot self-admit.'))
  findings.append(dict(kind='scope_limit',detail='No genuine original141 connected capture. Original138 supplies immutable accepted old numerical oracles only; no original-constructor equivalence or accepted-function credit is established.'))
  findings.append(dict(kind='runtime_pending',detail='Controls establish schemas and reject mutations; all actual141 checkpoints/owner/API/flag/FS joins must still pass in the ROOT-admitted source consumer.'))
  findings.append(dict(kind='export_limit',detail='Approved bounded exports omit nonstack registry checkpoint-page blobs and seal native branches only after846 phases; they are paired equality targets, not a replacement for canonical source authentication.'))
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 (out/'report.json').write_text(json.dumps(dict(passed=passed,driver_replacements=len(deltas)if 'deltas'in locals()else None,checks=checks,findings=findings,reviewer_authored_driver=True,ROOT_independent_admission_required=True,admitted=False,canonical_reader_opened=False,full_source_consumer_executed=False,bounded_method_controls_executed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(out/'report.json'));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
