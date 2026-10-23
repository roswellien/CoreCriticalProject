"""Freeze additive current138 loaded-input review before endpoint invocation."""
from pathlib import Path
import ast,hashlib,json,runpy,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=R/'tools/m4-tree-review/review_loaded_input131.py'
s=runpy.run_path(str(base),run_name='definition_only')['s']
changes=[
('loaded-input131-preparation-r2','loaded-input138-preparation-r1'),
('88aa9f5cede4176128903e0d98e871ce2cc4ede03304e0cde30fd72712561f1f','a7fa318f52c5bd38a1500b39107f331c601e33c8bf951a90db189fc82f21afbb'),
('m4-joint-startup131-root/execution-r1','m4-joint-startup138-root/execution-r3'),
('e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57','2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6'),
('m4-joint-startup131/preparation-r1','m4-joint-startup138/preparation-r4'),
('m4-joint-startup131/build-r1','m4-joint-startup138/build-r5'),
('len(domain)==71','len(domain)==48'),
]
for a,b in changes:
    assert a in s,a
    s=s.replace(a,b)
a="Path(jp['native_library']).resolve()==(R/'reports/m4-formatting-native/preparation-r19/registry_library.cpp').resolve() and build['files'][str(Path(jp['native_library']).resolve())]==np['files'][str(Path(jp['native_library']).resolve())]"
b="Path(jp['native_library']).resolve()==(R/'reports/m4-fps-native/service-preparation-r3/registry_library.cpp').resolve() and build['files'][str(Path(jp['native_library']).resolve())]==sha(pin(jp['native_library'])) and jp['borrowed_service_preparation_sha256']=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9'"
assert s.count(a)==1
s=s.replace(a,b)
anchor="  need(counts['native_literal_state2_operand_joins']=="
assert s.count(anchor)==1
extra="""  widget_path=R/'reports/m4-startup138-original/widget-complete-source-r1/report.json'
  widget=read(widget_path,'4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684')
  need(widget['passed'] and widget['finite_current42_widget_source_relations_passed'] and not widget['AFTER_machine_or_memory_seed'] and widget['files'][str((R/'reports/m4-startup138-original/original-validation-r3/report.json').resolve())]==prep['original_validation_sha256'],'Current literal original widget own-BEFORE/source receipt')
  original_widgets=output(widget,widget_path,'source-derivations.json')
  native_widgets=output(source,source_path,'Widget-source-derivations.json')
  roots={0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0}
  need(len(original_widgets)==42 and len(native_widgets)==84 and {r['root']for r in original_widgets}=={r['root']for r in native_widgets}==roots,'All seven new widget families in both source branches')
  for branch,items in(('original',original_widgets),('native',native_widgets)):
   for row in items:
    ledger=row['source_accesses']
    need(ledger and all(len(v)==5 for v in ledger),'Whole new widget literal source access ledger')
    need(not any(overlap(v[1],v[3],0x78145000,0x78147000)for v in ledger),'No new widget source operand consumes any differing provider RW/IAT input')
    counts[branch+'_widget_operand_disjointness_cases']+=1
    counts[branch+'_widget_operands_checked']+=len(ledger)
  need(counts['original_widget_operand_disjointness_cases']==42 and counts['native_widget_operand_disjointness_cases']==84,'Every new widget root checked for loaded input consumption')
"""
s=s.replace(anchor,extra+anchor)
s=s.replace('pin(artifact);pin(prior);pin(__file__);passed=True',"pin(artifact);pin(R/'tools/m4-tree-review/review_loaded_input130.py');pin(R/'tools/m4-tree-review/review_loaded_input131.py');pin(__file__);passed=True")
s=s.replace('current131','current138').replace('original131/native19','original138/native19')
s=s.replace('R=Path(__file__).resolve().parents[2];PINS={}', 'R=Path(__file__).resolve().parents[3];PINS={}')
ast.parse(s)
out=R/'reports/m4-tree-review'/sys.argv[1]
assert not out.exists()
out.mkdir()
tool=out/'review.py';tool.write_text(s)
pins={str(p.resolve()):sha(p)for p in(base,R/'tools/m4-tree-review/review_loaded_input130.py',Path(__file__),tool)}
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Additive current138 complete finite loaded difference and all literal widget operand review preparation; equality target not opened',entrypoint=str(tool),source_machine_executed=False,archive_reader_opened=False,review_executed=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(q,sha(q))
