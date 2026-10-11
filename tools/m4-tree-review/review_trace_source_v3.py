"""Independent bounded trace/source/native-contract review; no capture reader."""
from pathlib import Path
import collections,hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();a=sha(p);need(h is None or h==a,'Physical pinned input '+str(p));need(str(p)not in P or P[str(p)]==a,'Stable review input');P[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh bounded review');out.mkdir(parents=True)
 base=R/'reports/m4-tree-original/trace-validation-r2'
 t=read(base/'report.json','1c099256ca7bdc076bffa23a37c9aab6975a4769337ce8c7cff64ba623bea463')
 need(t['passed']and t['reader_closed']and not t['debugger_CONTEXT_is_raw_hardware_FX_claim'],'Sealed bounded trace scope')
 def artifact(n):
  p=base/n;return read(p,t['files'][str(p)])
 events=artifact('actual-instructions.json');cells=artifact('actual-source-access-ledger.json');owners=artifact('actual-owner-byteflows.json');scratch=artifact('actual-Lockit-scratch.json');imports=artifact('actual-register-imports.json');pubs=artifact('actual-pointer-publications.json')
 deriv=read(R/'reports/m4-tree-source/dynamic-contracts-r1/report.json','9a44bbb1c6be884f166837457e7db2619a1045efb2fb27ac398665e578df49d3')
 contracts=read(R/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',deriv['files'][str(R/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json')])
 source=read(R/'reports/m4-tree-source/original-source-r3/report.json','f214d298b40aa4f589d9a99b4083cdf954090486637a577b7db4d9358185a4ff')
 native=read(R/'reports/m4-tree-native/preparation-r5/report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2')
 need(source['passed']and deriv['passed']and native['passed'],'Passed literal source and current native preparation')
 # Every exported cell occurs literally in the measured instruction artifact.
 need([c for e in events for c in e['cells']]==cells,'Complete observation ledger joins actual instructions')
 need(len(events)==1198 and len(cells)==782 and len(owners)==7,'Finite genuine trace extent')
 for i,e in enumerate(events):
  need(e['index']==i and e['raw_debugger_before_cpu'][9]==e['PC']+1 and e['raw_debugger_after_cpu'][9]==e['next_PC'],'Exact debugger instruction ordinal/EIP')
 all_owned=[c for c in cells if c['owner_index']is not None]
 need(len(all_owned)==172 and sum(c['read']for c in all_owned)==96 and sum(c['write']for c in all_owned)==76,'Complete measured repeated-owner operation extent')
 expected=contracts['owned_causal_order'];need(len(expected)==172,'Complete literal contract extent')
 current={o['index']:bytearray.fromhex(o['initial_hex'])for o in owners};pointer={o['pointer']:o['index']for o in owners}
 rows=[]
 for c,s in zip(all_owned,expected):
  need((c['PC'],c['owner_index'],c['owner_offset'],c['width'],bool(c['write']))==(s['pc'],s['owner_role_index'],s['offset'],s['bytes'],s['write']),'Measured owner operation exactly follows literal PC/role/offset/order')
  o=owners[c['owner_index']];off=c['owner_offset'];width=c['width'];need(c['generation']==o['generation'] and c['address']==o['pointer']+off and off+width<=24,'Actual live allocation generation and requested24 extent')
  need(current[o['index']][off:off+width]==c['before_value'].to_bytes(width,'little'),'Whole backing before access derives genuine initial and earlier observed stores')
  value=c['after_value']if c['write']else c['before_value']
  if s['value_owner_role_index']is not None:need(pointer.get(value)==s['value_owner_role_index'],'Exact current pointer role carried by measured source value')
  if c['write']:current[o['index']][off:off+width]=value.to_bytes(width,'little')
  rows.append(dict(PC=c['PC'],role=o['index'],generation=o['generation'],offset=off,width=width,writing=bool(c['write']),value_role=s['value_owner_role_index']))
 for o in owners:
  need(len(current[o['index']])==32 and current[o['index']].hex()==o['derived_final_hex'],'All32 actual backing bytes independently derive complete observed history')
  need(current[o['index']][24:]==bytes.fromhex(o['initial_hex'])[24:],'Capacity tails remain genuine allocator input')
  need(o['source_CALL']['CALL_PC']==contracts['owners'][o['index']]['CALL_pc']and o['source_CALL']['invocation']==contracts['owners'][o['index']]['per_site_invocation_ordinal']+1,'Actual repeated allocator CALL occurrence independently resolves role')
 # Exact source branch and scratch, including both shared-dtor occurrences.
 need(len(scratch)==len(contracts['Lockit_call_order'])==26,'All actual Lockit source CALLs retained')
 for a,s in zip(scratch,contracts['Lockit_call_order']):
  need((a['CALL_PC'],a['target'],a['source_LEA']['PC'],a['affine'])==(s['CALL_pc'],s['target'],s['source_LEA_pc'],s['target_entry_ESP_bias']),'Actual reached LEA and exact source CALL branch match literal derivation')
 shared=[a for a in scratch if a['CALL_PC']==0x4badd0];need(len(shared)==2,'Two actual shared normal destructors')
 for a in shared:
  i=a['event'];need([e['PC']for e in events[i-3:i+1]]==[0x4badc7,0x4badc9,0x4badcc,0x4badd0]and a['affine']==24,'Shortest precise observed normal shared-dtor branch; no arbitrary scratch set')
 need(len(imports)==7,'Seven actual retained register imports')
 for a,s in zip(imports,contracts['register_import_derivations']):
  need((a['PC'],a['register'],a['definition']['PC'],a['definition']['IAT'],a['target'])==(s['CALL_pc'],s['register'],s['definition']['PC'],s['definition']['slot'],s['actual_register_value']),'Actual original loaded import definition/CALL resolves source identity')
  reg={'ebp':5,'ebx':3}[a['register']];v=a['target'];start=a['definition']['event'];stop=a['event']
  local=[e for e in events[start+1:stop]if e['PC']<0x5f400000]
  need(all(e['raw_debugger_before_cpu'][reg]==v and e['raw_debugger_after_cpu'][reg]==v for e in local),'Retained importing game register before/after every reached caller instruction')
  allocator=[e for e in events[start+1:stop]if e['PC']>=0x5f400000]
  if allocator:need(allocator[0]['raw_debugger_before_cpu'][reg]==v and allocator[-1]['raw_debugger_after_cpu'][reg]==v and allocator[-1]['mnemonic']=='ret','Authentic allocator callee may use its saved nonvolatile register and must restore at RET')
 # Primary publications use the actual child/parent generation; ordinary pointer
 # stores/rotations in the trace are not mislabeled as primary publications.
 primary=[]
 for c in cells:
  if c['PC']not in(0x4ba315,0x4ba347,0x4bab9c,0x4babac)or not c['write']:continue
  primary.append(c)
 need(len(primary)==7,'Exactly7 primary source publications among92 measured pointer stores')
 for c,s in zip(primary,contracts['publications']):
  need(c['PC']==s['pc']and pointer.get(c['after_value'])==s['owner_role_index'],'Actual primary child occurrence')
  if s['parent_owner_role_index']is None:need(c['address']==s['static_publication'],'Literal static publication cell')
  else:need((c['owner_index'],c['owner_offset'])==(s['parent_owner_role_index'],s['parent_offset']),'Actual parent role and branch edge')
 # Inspect/pin the entire executed source chains without opening capture bytes.
 for p in ('tools/m4-tree-review/review_trace_source_v2.py','tools/m4-tree-review/review_trace_source.py','tools/m4-tree-original/validate_trace_v2.py','tools/m4-tree-source/compare_prefix_v2.py','tools/m4-tree-source/game_model_v3.py','tools/m4-tree-original/trace_broker.cpp'):
  q=R/p
  if q.exists():pin(q)
 model=(R/'tools/m4-tree-source/compare_prefix_v2.py').read_text()
 need("if writes:need(expected==observed"in model and "elif expected!=observed:unused_frame_bytes.append"in model and "subsequent[0];need(access[4]"in model,'Original-only unused-frame policy rejects first later overlapping source read before overwrite')
 need('original_unused_frame_bytes_seeded=False'in model and 'whole_provider_stack_compared=False'in model,'Unwritten opaque original frames are observations, never machine seed or full original provider-stack credit')
 for p,h in native['files'].items():
  if Path(p).parent==Path(native['native_include']):pin(p,h)
 nc=(Path(native['native_include'])/'tree_contract.inc').read_text();segment=nc.split('constexpr TreeAccess tree_access_order[]{\n')[1].split('};')[0]
 parsed=[tuple(0xffffffff if x=='UINT32_MAX'else int(x=='true')if x in('true','false')else int(x)for x in row.split(','))for row in re.findall(r'\{([^}]+)\}',segment)]
 need(parsed==[(s['pc'],s['owner_role_index'],s['offset'],s['bytes'],0xffffffff if s['value_owner_role_index']is None else s['value_owner_role_index'],int(s['write']))for s in expected],'Final native172 owner rows physically equal exact independently corroborated source contract')
 pin(__file__)
 (out/'reviewed-owner-order.json').write_text(json.dumps(rows,indent=2)+'\n')
 result=dict(passed=True,scope='Independent bounded trace/source/native-contract review through sealed actual observation exports; no second capture reader or125 acceptance',trace_receipt_sha256=sha(base/'report.json'),source_receipt_sha256=sha(R/'reports/m4-tree-source/original-source-r3/report.json'),dynamic_receipt_sha256=sha(R/'reports/m4-tree-source/dynamic-contracts-r1/report.json'),native_preparation_sha256=sha(R/'reports/m4-tree-native/preparation-r5/report.json'),counts=dict(actual_instructions=1198,actual_owned_accesses=172,distinct_owned_tuples=135,actual_owners=7,whole_capacity_bytes=224,primary_publications=7,Lockit_CALLs=26,shared_normal_dtor_paths=2,register_imports=7),original_opaque_frame_bytes_seeded=False,original_whole_provider_stack_claim=False,native_full_stack_equality_required=True,native_executed_credit=False,initializer_credit=0,files=P)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
