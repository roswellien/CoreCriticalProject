"""Fresh bounded current130 complete provider-input/domain proof; no archives."""
from pathlib import Path
import collections,hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Bounded page/export inputs only');v=sha(p);need(h is None or v==h,'Physical current input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def output(receipt,path,name):
 p=path.parent/name;return read(p,receipt['files'][str(p.resolve())])
def overlap(address,width,lo,hi):return address<hi and address+width>lo
def main(name,source_path,source_sha):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh loaded-input gate');out.mkdir(parents=True);passed=False;counts=collections.Counter();observations=[]
 try:
  prep_path=R/'reports/m4-tree-review/loaded-input130-preparation-r1/report.json';prep=read(prep_path,'678e719aa7a9b9c51504fd1cfee8f76b0ae146f9c8b755d892ff70a25d12f4e7');need(prep['passed']and prep['selected_operand_disjointness_claimed']is False and prep['prior125_difference_list_reused']is False,'Fresh complete physical difference declaration')
  declaration=read(prep['input_domain_path'],prep['input_domain_sha256']);ob=pin(prep['whole_original_input_page'],prep['whole_original_input_page_sha256']).read_bytes();nb=pin(prep['whole_native_input_page'],prep['whole_native_input_page_sha256']).read_bytes();need(len(ob)==len(nb)==4096 and declaration['whole_original_hex']==ob.hex()and declaration['whole_native_hex']==nb.hex(),'Both entire physical page bytes match exact declaration')
  diff=[dict(offset=i,address=0x78145000+i,original=x,native=y)for i,(x,y)in enumerate(zip(ob,nb))if x!=y];need(diff==declaration['differences'],'Every actual differing byte offset and both values retained');domain={x['address']for x in diff};need(len(domain)==71 and len(declaration['differing_DWORDs'])==25 and ob[0x640:0x65c]==nb[0x640:0x65c]and struct.unpack_from('<I',ob,0x658)[0]==2,'Fresh observed finite domain and complete identical CS24/state2 fields')
  counts.update(whole_bootstrap_input_pages=2,whole_input_bytes=8192,explicit_loaded_input_difference_bytes=len(diff),explicit_loaded_input_difference_DWORDs=len(declaration['differing_DWORDs']),identical_source_CS24_bytes=24,identical_source_state2_bytes=4)
  execution_path=R/'reports/m4-joint-startup130-root/execution-r2/report.json';execution=read(execution_path,'57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1');np=read(R/'reports/m4-formatting-native/preparation-r19/report.json',prep['native_preparation_sha256']);jp=read(R/'reports/m4-joint-startup130/preparation-r2/report.json',prep['broad_preparation_sha256']);build=read(R/'reports/m4-joint-startup130/build-r2/build.json',execution['build_sha256']);need(all(x['passed']for x in(execution,np,jp,build))and build['preparation_sha256']==sha(R/'reports/m4-joint-startup130/preparation-r2/report.json')and jp['native_preparation_sha256']==sha(R/'reports/m4-formatting-native/preparation-r19/report.json'),'Current corrected19/broad130 actual compile/run chain')
  source_path=Path(source_path).resolve();source=read(source_path,source_sha);lineage=source['executed_lineage'];need(source['passed']and source['reader_closed']and source['source_and_provider_combined']and not source['candidate_AFTER_machine_seed']and not source['per_phase_BEFORE_machine_seed']and source['files'][str(execution_path.resolve())]==sha(execution_path),'Actual final persistent source/provider proof bound to current execution2')
  scopes=output(source,source_path,'Loaded-provider-source-scope.json');need(len(scopes)==12 and {(r['level'],r['sequence'])for r in scopes}=={(l,s)for l in('O0','O2')for s in range(6)},'Every optimized current130 sequence exported')
  for case in scopes:
   need(case['source_ledger_compared']and case['bootstrap_complete_page_scope_compared'],'Actual whole source ledger/bootstrap scope already compared')
   need(len(bytes.fromhex(case['bootstrap_State_hex']))==3504 and len(bytes.fromhex(case['bootstrap_CPU_hex']))==40 and len(bytes.fromhex(case['bootstrap_FX_hex']))==512,'One true complete bootstrap machine input')
   before=bytes.fromhex(case['bootstrap_provider_pages'][str(0x78145000)]);after=bytes.fromhex(case['source_provider_after_pages'][str(0x78145000)]);need(before==after==nb and case['bootstrap_page_sha256'][str(0x78145000)]==sha(prep['whole_native_input_page']),'Entire current native bootstrap/source-final RW input page conserved')
   counts['current_native_whole_RW_input_and_final_pages']+=2
   reads=[];imports=[]
   for row in case['source_RW_IAT_operands']:
    pc,address,value,width,write=(row[k]for k in('PC','address','value','width','write'));need(overlap(address,width,0x78145000,0x78147000),'Export retains exactly overlapping RW/IAT source operands');need(not(domain&set(range(address,address+width))),'No source operand touches any differing input byte')
    if overlap(address,width,0x78145000,0x78146000):need(pc in(0x7810a290,0x7810a350)and(address,value,width,write)==(0x78145658,2,4,0),'Only identical complete state2 read is reached in RW page');reads.append([pc,address,value]);counts['native_literal_state2_operand_joins']+=1
    else:
     slot={0x7810a30b:0x78146198,0x7810a35e:0x78146184}.get(pc);iat=bytes.fromhex(case['bootstrap_provider_pages'][str(0x78146000)]);need(slot==address and width==4 and not write and value==struct.unpack_from('<I',iat,address-0x78146000)[0],'Exact owning source Enter/Leave loaded IAT DWORD');imports.append(row);counts['native_named_IAT_operand_joins']+=1
   need(len(reads)==len(imports)==36 and reads==case['Lockit_state_reads'],'All36 source state reads and36 retained loaded IAT uses per current sequence')
   relations=case['Lockit_API_relations'];need(len(relations)==36,'All36 actual source/API relations per current sequence');want=[]
   for relation in relations:
    w=relation['actual_API_words'];need(len(w)==32 and w[2]==relation['source_PC']in(0x7810a30b,0x7810a35e)and w[20]==relation['guest_CS']==0x78145640 and w[13]==24 and w[29:31]==[1,1],'Actual complete source API witness binds exact guest24 input/output')
    typed=bytes.fromhex(relation['derived_CS24_hex']);need(len(typed)==24 and len(bytes.fromhex(relation['actual_native_CS40_hex']))==40,'Typed guest24 independently measured native40, no opaque copy')
    for offset in range(0,24,4):want.append([relation['source_PC'],0x78145640+offset,struct.unpack_from('<I',typed,offset)[0],4,1])
    counts['native_API_disjoint_CS24_joins']+=1
   need(case['provider_API_transports']==want,'Complete ordered actual typed API output transport contains only all24 declared bytes for each call');counts['native_typed_CS24_DWORD_transports']+=len(want)
   observations.append(dict(branch='native',level=case['level'],sequence=case['sequence'],RW_state_reads=reads,named_IAT_source_operands=imports,typed_API_CS24_relations=relations))
  combined_path=R/'reports/m4-startup130-original/combined-source-r3/report.json';combined=read(combined_path,'2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624');old_path=R/'reports/m4-startup130-original/old-Lockit-source-r1/report.json';old=read(old_path,'2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7');need(old['passed']and combined['passed']and combined['original_validation_sha256']==prep['original_validation_sha256'],'Current original130 literal source proofs')
  original_ledgers=[]
  for row in output(old,old_path,'original-source-access-ledgers.json'):original_ledgers.append(('original-old4',(row['sequence'],row['root']),row['rows'],2))
  for row in output(combined,combined_path,'original-Tree-source-derivations.json'):original_ledgers.append(('original-tree',row['sequence'],row['source']['source_accesses'],26))
  for row in output(combined,combined_path,'original-Formatting-source-derivations.json'):
   if row['root']==0x4e1ca0:original_ledgers.append(('original-mixed',row['sequence'],row['source_accesses'],2))
  for branch,case,ledger,expected in original_ledgers:
   operands=[r for r in ledger if overlap(r[1],r[3],0x78145000,0x78146000)];need(len(operands)==expected,'Exact original branch full RW source operand extent')
   for pc,address,value,width,write in operands:need(pc in(0x7810a290,0x7810a350)and(address,value,width,write)==(0x78145658,2,4,0)and not(domain&set(range(address,address+width))),'Every original reached operand is identical state2 disjoint from differing bytes');counts['original_literal_state2_operand_joins']+=1
   observations.append(dict(branch=branch,case=case,RW_operands=operands))
  need(counts['native_literal_state2_operand_joins']==counts['native_API_disjoint_CS24_joins']==counts['native_named_IAT_operand_joins']==432 and counts['original_literal_state2_operand_joins']==216 and counts['native_typed_CS24_DWORD_transports']==2592,'Full current finite domain and actual API extent')
  declaration['physical_differences_with_addresses']=declaration['differences'];declaration['differences']=[dict(offset=r['offset'],original=r['original'],native=r['native'])for r in diff];declaration['observations']=observations;artifact=out/'input-domain.json';artifact.write_text(json.dumps(declaration,indent=2)+'\n');pin(artifact);pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Fresh complete authentic original130/native19 loaded input RW pages, every finite exact byte/DWORD difference and current persistent source/API disjointness; paired whole endpoint carry remains separate',counts=dict(counts),native_execution_sha256=sha(execution_path)if'execution_path'in locals()else None,native_source_sha256=sha(source_path)if'source'in locals()else None,original_validation_sha256=prep['original_validation_sha256']if'prep'in locals()else None,input_domain_path=str((out/'input-domain.json').resolve()),input_domain_sha256=sha(out/'input-domain.json')if(out/'input-domain.json').is_file()else None,whole_original_input_page=prep['whole_original_input_page']if'prep'in locals()else None,whole_original_input_page_sha256=prep['whole_original_input_page_sha256']if'prep'in locals()else None,whole_native_input_page=prep['whole_native_input_page']if'prep'in locals()else None,whole_native_input_page_sha256=prep['whole_native_input_page_sha256']if'prep'in locals()else None,capture_archives_opened=0,paired_endpoint_capture_reads=0,endpoint_carry_acceptance=False,whole_page_mask=False,opaque_pointer_target_equivalence=False,native_DllMain_credit=False,prior125_difference_list_reused=False,initializer_credit=0,files=PINS)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
