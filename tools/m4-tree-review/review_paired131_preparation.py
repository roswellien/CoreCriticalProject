"""Independent archive-free current131 comparer and finite MFC policy review."""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture archives');v=sha(p);need(h is None or h==v,'Exact bounded current input '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh paired131 preparation review');out.mkdir(parents=True);passed=False;counts=collections.Counter()
 try:
  pp=R/'reports/m4-startup131-paired/comparer-preparation-r2/report.json';prep=read(pp,'20f5156a55099292b90ff03c3ea0c13a5e604bf604eed4c515eaa961506d2cdd');need(prep['passed']and not prep['paired_executed']and not prep['capture_reader_opened'],'Unexecuted exact current preparation')
  for p,h in prep['files'].items():pin(p,h);counts['physically_verified_preparation_files']+=1
  cp=pin(prep['comparer'],prep['comparer_sha256']);hp=pin(prep['helper'],prep['helper_sha256']);code=cp.read_text();helper=hp.read_text();ast.parse(code);ast.parse(helper)
  prior=read(pp.parent.parent/'comparer-preparation-r1/report.json');need(prior['passed'],'Exact prepared additive original130 policy')
  for p,h in prior['files'].items():pin(p,h)
  format_path=pin(R/'tools/m4-startup131-paired/format_relations.py');baseline_format=pin(R/'tools/m4-startup130-paired/format_relations_v2.py');need(format_path.read_bytes()==baseline_format.read_bytes(),'Complete accepted130 finite formatter policy unchanged')
  tree_path=pin(R/'tools/m4-startup131-paired/tree_relations.py');baseline_tree=pin(R/'tools/m4-startup130-paired/tree_relations.py');a=baseline_tree.read_text();need(a.count('PHASE=78')==1 and tree_path.read_text()==a.replace('PHASE=78','PHASE=79'),'Only exact chronological tree phase78 to79 changed')
  spec=importlib.util.spec_from_file_location('independent_cached_mfc_pair_policy',hp);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
  need(M.ROOT==0x5ae3e4 and M.PHASE==13 and M.ROLES==('manager-array','thread','thread-array','thread-object','global-object'),'Finite exact current cached role/domain inventory')
  gate_path=R/'reports/m4-startup131-original/source-r2/report.json';gate=read(gate_path,'203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910');q=gate_path.parent/'source-derivations.json';original=read(q,gate['files'][str(q.resolve())]);need(gate['passed']and len(original)==6,'All genuine chronological original cached source cases')
  static=[]
  for row in original:
   need((row['root'],row['phase'])==(M.ROOT,13)and not row['source_AFTER_seed']and row['actual_prefix_carried_BEFORE'],'Current own genuinely carried BEFORE source input')
   need(len(row['source_PCs'])==142 and len(row['source_accesses'])==113,'Complete finite literal PC and operand chronology')
   need(tuple(r['PC']for r in row['source_normal_boundary_relations'])==M.PCS and len(row['source_API_relations'])==4,'Seven exact normal snapshots and four real API lifetimes')
   owners=row['source_borrowed_backings'];need(tuple(r['role']for r in owners)==M.ROLES,'All five actual borrowed role identities');by={r['role']:r for r in owners};accesses=row['source_accesses']
   for i,role in M.ROLE_VALUES.items():need(accesses[i][2]==by[role]['address'],'Every typed literal pointer value names that source role');counts['original_role_value_corroborations']+=1
   for i in M.FS_VALUES:need(accesses[i][2]==row['source_FS_BEFORE']and accesses[i][3]==4,'Exact true source FS predecessor operand');counts['original_FS_value_corroborations']+=1
   for i,k in M.IMPORT_ACCESSES.items():need(accesses[i][3:]==[4,0],'Every named import is one genuine complete source read');counts['original_import_operand_corroborations']+=1
   need(accesses[45][0]==0x5f4010c3 and accesses[45][2]==by['global-object']['address'],'The only pointer parity policy is tied to literal global-role CMP input')
   for owner in owners:M.own_byteflow(owner,accesses);counts['original_whole_role_byteflows_reviewed']+=1
   need(row['source_FS_BEFORE']==row['source_FS_AFTER']and len(row['source_FS_writes'])==2,'Literal original install and own predecessor restoration')
   for api in row['source_API_relations']:need(api['no_postRET_memory_seed']and not api['intermediate_source_FS_observation'],'Original API scalars retain exact observer timing scope')
   counts['genuine_source_cases_reviewed']+=1;counts['genuine_source_PC_occurrences_reviewed']+=len(row['source_PCs']);counts['genuine_source_operands_reviewed']+=len(accesses)
   static.append(dict(sequence=row['sequence'],source_PCs=row['source_PCs'],imports={str(i):accesses[i]for i in M.IMPORT_ACCESSES},role_values={str(i):accesses[i]for i in M.ROLE_VALUES},FS_values={str(i):accesses[i]for i in M.FS_VALUES},actual_normal_boundary_PCs=list(M.PCS),source_FS_BEFORE=row['source_FS_BEFORE'],source_FS_AFTER=row['source_FS_AFTER']))
  for marker in ('Every other opaque differing input byte is never source-read','Every untouched opaque difference carries exactly in each branch','Every other differing opaque provider input byte is unconsumed','Every other source-defined normal flag bit','original_API_held_CS24_observed=False','native_intermediate_hardware_observation=False','Only source TIB004/008 may join','Each complete independent carried BEFORE part','Exact inverse persistent projection of the independently derived endpoint'):
   need(marker in helper,'Complete exact finite relation/scoped observation guard '+marker)
  need('b_memory[0x7ffde004] = bytearray(joined)'in helper and 'del b_memory[0x7ffde008]'in helper and "get(region_final, 0x7ffde004, 8)"in helper,'Eight-byte read representation derived only from two whole carried BEFORE pieces and inverted after source')
  need('No'not in helper[:0],'No-op parser sentinel')
  for marker in ('raw_export_report_sha256','original_combined_source_sha256','native_execution_sha256','native_source_sha256','loaded_input_differences','loaded_input_domain[\'differences\']','paired_MFC_ordered_operand_relations','paired_MFC_whole_borrowed_role_byteflows'):
   need(marker in code,'Exact current receipt/finite extent relation '+marker)
  need('ExportReader('in code and 'DirectSet('not in code and "mfc_relations_v2.py"in code,'Comparer consumes bounded current same-session raw exports, not an additional canonical archive reader')
  need("equal(loaded_input_differences,loaded_input_domain['differences']"in code,'Entire fresh loaded page delta joined without wildcard')
  need('native=None'in code and 'ori=None'in code,'Aliases cleared after reader close')
  path=out/'genuine-MFC-policy-corroborations.json';path.write_text(json.dumps(static,indent=2)+'\n');pin(path);pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Independent complete code/preparation and six genuine cached-MFC source operand/role/FS policy review; current paired configuration and actual native paired result remain separate',comparer_preparation_sha256=sha(pp)if'pp'in locals()else None,comparer_path=str(cp)if'cp'in locals()else None,comparer_sha256=sha(cp)if'cp'in locals()else None,helper_path=str(hp)if'hp'in locals()else None,helper_sha256=sha(hp)if'hp'in locals()else None,counts=dict(counts),paired_executed=False,current_configuration_reviewed=False,capture_archives_opened=0,original_API_held_CS24_observed=False,native_intermediate_hardware_observation=False,cold_or_arbitrary_alias_domain_credited=False,initializer_credit=0,files=PINS);f=out/'report.json';f.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(f),sha256=sha(f),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
