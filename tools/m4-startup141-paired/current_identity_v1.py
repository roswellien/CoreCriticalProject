"""Finite actual paired141 branch identity cut; no readers/models/credit.

The returned reader declarations deliberately select original from strict3,
and O0/O2 from native source6. Native source6's old original138 row is never
opened or treated as current original evidence.
"""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
V_SHA='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
N_SHA='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'
E_SHA='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6'
def need(v,s):
 if not v:raise ValueError(s)
def prove(C,pin):
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 need(C['scope']=='current141-paired-frozen-gates','Exact current scope before any reader')
 for field,h in [('original_validation',V_SHA),('native_source',N_SHA),('native_execution',E_SHA)]:need(C[field]['sha256']==h,'Exact closed current producer gate '+field)
 V=read(C['original_validation']['path'],V_SHA);N=read(C['native_source']['path'],N_SHA);E=read(C['native_execution']['path'],E_SHA)
 need(V['passed']and V['reader_closed']and V['paired_export_readers_closed']and V['counts']['phases']==846 and V['callbacks']==111 and V['record_bytes']==356992 and V['combined_pages']==69,'Current original141 strict846/111/69 geometry')
 need(N['passed']and N['reader_closed']and N['paired_export_readers_closed']and N['complete_selected_source']and N['complete_persistent141_constructors']and N['per_phase_BEFORE_machine_seed']is False and N['candidate_AFTER_machine_seed']is False,'Current carried native141 source6, no reseed')
 need(N['counts']['persistent_phases']==1692 and N['counts']['literal_constructor_roots']==36 and N['counts']['whole_constructor_global_BEFORE']==N['counts']['whole_constructor_global_AFTER']==1692,'Actual native source69 plus separate current whole5F2000')
 need(E['passed']and set(E['runs'])=={'O0','O2'}and N['executed_lineage']['execution_sha256']==E_SHA and N['executed_lineage']['build_sha256']==E['build_sha256']and N['executed_lineage']['joint_preparation_sha256']==E['preparation_sha256'],'Same actual two-level native compile/execution/source lineage')
 # Original source hash remains a required frozen future current gate. There
 # is no default or original138 success substitution.
 A=read(C['original_combined_source']['path'],C['original_combined_source']['sha256']);need(A['passed']and A['reader_closed']and A['original_validation_sha256']==V_SHA and A['raw_export_report_sha256']==V_SHA and A['counts']['phases']==846 and A['counts']['callbacks']==111 and A['candidate_AFTER_machine_seed']is False and A['source_AFTER_seed']is False and A['full_original846_CPU_execution_claim']is False,'Genuine new source3 finite scope, no fullCPU inference')
 need(A['counts']['literal_constructor_cases']==18 and A['counts']['formatter4_source_cases']==24 and A['counts']['old4_source_cases']==24 and A['counts']['new_MFC_source_cases']==6 and A['counts']['widget_source_cases']==42 and A['counts']['tree_source_cases']==6,'All actual current finite original source families')
 originals=[r for r in V['paired_exports']if r['branch']=='original'];need(len(originals)==1,'One current original strict3 export');O=originals[0]
 need(O['transport_path']==V['original_capture']and O['logical_files']==261543 and O['payload_bytes']==1540126431 and O['index_sha256']=='ed0cc1d43b26c067f0af85dd153f5ce5fd38ae07f789d893bcbad812b97c13ae'and O['payload_sha256']=='8a23f0a6be87e38ff50f9591f57988fa5e87850e4429655a2357aa98f599331b','Current independently sealed original141 transport/index/payload geometry')
 native=[]
 for level in('O0','O2'):
  rows=[r for r in N['paired_exports']if r['branch']==level];need(len(rows)==1,'Exact current native branch');row=rows[0];need(row['transport_path']==E['runs'][level]['capture'],'Actual same-level source/export/execution identity');native.append(dict(level=level,path=C['native_source']['path'],sha256=N_SHA,branch=level,export=row))
 old=[r for r in N['paired_exports']if r['branch']=='original'];need(len(old)==1 and old[0]['transport_path']!=O['transport_path']and old[0]['index_sha256']!=O['index_sha256'],'Explicit source6 original138 row remains outside current141 reader declarations')
 for row in[O]+[r['export']for r in native]:
  for field in('index','payload'):pin(row[field+'_path'],row[field+'_sha256'])
 order=read(C['selected_order']['path'],C['selected_order']['sha256']);need(len(order)==141 and len({r['entry']for r in order})==141 and[order[i]['entry']for i in(13,14,15,39,86)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40,0x4b7f70],'Exact three constructor insertion chronology')
 need([order[i]['entry']for i in(17,18,19,50,137,138,139)]==[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0],'Actual seven widget chronology')
 return dict(original_reader=dict(path=C['original_validation']['path'],sha256=V_SHA,branch='original',export=O),native_readers=native,order=order,identity_cut_reviewed=True,paired_semantics_proven=False,canonical_reader_opened=False,ordinary_reader_opened=False,source_model_executed=False,initializer_credit=0)
if __name__=='__main__':raise SystemExit('Independent ROOT pair admission and fail-closed pin required; no standalone execution')
