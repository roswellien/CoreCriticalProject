"""Pure retained original-MFC predicate adverse controls; no machine or archive."""
from pathlib import Path
import ast,collections,copy,hashlib,importlib.util,json,sys,textwrap
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 producer=pin(R/'tools/m4-138-criteria-frontier/current_policy_fields_v2.py')
 baseline=pin(R/'tools/m4-tree-review/review_paired131_preparation_v2.py').read_text();start=baseline.index('  for row in original:');end=baseline.index('  for marker in ',start);block=textwrap.dedent(baseline[start:end]);ast.parse(block)
 rp=pin(R/'reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801');receipt=json.loads(rp.read_bytes());dp=R/'reports/m4-startup138-original/mfc-source-r2/source-derivations.json';rows=json.loads(pin(dp,receipt['files'][str(dp)]).read_bytes())
 hp=pin(R/'tools/m4-startup131-paired/mfc_relations_v2.py','4ab2c11a89b47d8f380d348dab8a548d3a71c529ecafc25282d362064c0dc67b');spec=importlib.util.spec_from_file_location('exact_mfc_preflight',hp);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 expected={'original_role_value_corroborations':24,'original_FS_value_corroborations':24,'original_import_operand_corroborations':42,'original_whole_role_byteflows_reviewed':30,'genuine_source_cases_reviewed':6,'genuine_source_PC_occurrences_reviewed':852,'genuine_source_operands_reviewed':678}
 def test(value):
  c=collections.Counter();assert len(value)==6
  def need(v,m):assert v,m
  exec(compile(block,'exact retained accepted original-MFC predicates','exec'),dict(original=value,M=M,counts=c,static=[],need=need))
  assert dict(c)==expected
 test(rows);results=[]
 changes=[('AFTER_seed',lambda r:r[0].__setitem__('source_AFTER_seed',True)),('carried_before',lambda r:r[0].__setitem__('actual_prefix_carried_BEFORE',False)),('root',lambda r:r[0].__setitem__('root',0)),('phase',lambda r:r[0].__setitem__('phase',14)),('missing_PC',lambda r:r[0]['source_PCs'].pop()),('missing_operand',lambda r:r[0]['source_accesses'].pop()),('boundary_PC',lambda r:r[0]['source_normal_boundary_relations'][0].__setitem__('PC',0)),('missing_API',lambda r:r[0]['source_API_relations'].pop()),('role_identity',lambda r:r[0]['source_borrowed_backings'][0].__setitem__('role','wrong')),('role_pointer',lambda r:r[0]['source_accesses'][18].__setitem__(2,0)),('FS_predecessor',lambda r:r[0]['source_accesses'][30].__setitem__(2,0)),('import_width',lambda r:r[0]['source_accesses'][5].__setitem__(3,1)),('global_CMP_PC',lambda r:r[0]['source_accesses'][45].__setitem__(0,0)),('FS_restore',lambda r:r[0].__setitem__('source_FS_AFTER',0)),('postRET_seed',lambda r:r[0]['source_API_relations'][0].__setitem__('no_postRET_memory_seed',False)),('intermediate_FS',lambda r:r[0]['source_API_relations'][0].__setitem__('intermediate_source_FS_observation',True)),('missing_case',lambda r:r.pop())]
 for label,change in changes:
  x=copy.deepcopy(rows);change(x);rejected=False
  try:test(x)
  except (AssertionError,ValueError,KeyError,IndexError):rejected=True
  assert rejected,label;results.append(dict(name=label,rejected=True))
 # Producer source bindings/inverses are separately physically reviewed; reject
 # a derivative that silently drops either per-level whole binding comparison.
 source=producer.read_text();assert "for level in ('O0','O2')"in source and "whole_inverse(cp.read_text(),hunks)==parent.read_text()"in source
 pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Exact accepted MFC original-case predicates on six current sealed rows plus17 adverse mutations; no broader cold-domain or actual paired execution proof',positive_cases=6,adverse_controls=results,retained_counts=expected,source_machine_executed=False,worker_executed=False,archive_reader_opened=False,allowance_created=False,accepted_function_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
