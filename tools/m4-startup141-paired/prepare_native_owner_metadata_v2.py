"""Prepare causal metadata/adapter4 and source6 bindings; no imports/models/readers."""
from pathlib import Path
import ast,difflib,hashlib,json,re
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def change(parent,child,edits,out,label):
 a=parent.read_text();b=a
 for x,y in edits:assert b.count(x)==1,(label,x);b=b.replace(x,y)
 ast.parse(b);assert not child.exists();child.write_text(b);back=b
 for x,y in reversed(edits):assert back.count(y)==1;back=back.replace(y,x)
 assert back==a;delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 inv=out/(label+'-inverse.json');inv.write_text(json.dumps(delta,indent=2)+'\n');return [parent,child,inv],len(delta)
def main():
 out=R/'reports/m4-startup141-paired/native-owner-metadata-preparation-r2';assert not out.exists();out.mkdir();paths=[]
 contract_path=R/'reports/m4-startup141-runway/service-preparation-r2/source_contract.inc';registry_contract=contract_path.with_name('registry_contract.inc');text=contract_path.read_text()+'\n'+registry_contract.read_text();contracts={}
 for match in re.finditer(r'\{(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(\d+),"([A-Za-z0-9_]+)",(\d+)\}',text):
  pc,slot,raw,argc,name,tail=match.groups();pc=int(pc,0);row=[name,int(slot,0),int(raw,0),int(argc),int(tail)];assert pc not in contracts or contracts[pc]==row;contracts[pc]=row
 assert contracts and any(v[0]=='InitializeCriticalSection'and v[1]==0x7802e03c for v in contracts.values())and any(v[0]=='HeapAlloc'and v[1]==0x7802e094 for v in contracts.values());cp=out/'physical-API-contracts.json';cp.write_text(json.dumps(contracts,indent=2)+'\n');paths.extend([contract_path,registry_contract,cp])
 p=R/'tools/m4-startup141-paired/constructor_native_input141_v3.py';q=p.with_name('constructor_native_input141_v4.py')
 old=' allocation_rows=rows(a.data(base+"locale-allocations.bin"),"<16Q");byguest={v[1]:v for v in allocation_rows};owners=[]'
 new=''' normal_facts=[list(a.words(base+'locale-api-'+str(i)+'-witness.bin',32,'Q'))for i in range(current_source['API_after'])]
 mfc_births=[list(v)for v in rows(a.data(base+'mfc-allocation-witnesses.bin'),'<32Q')];string_births=[list(v)for v in rows(a.data(base+'strings-witnesses.bin'),'<32Q')];resource=list(a.words(base+'lockit-resource.bin',8,'Q'));growth=[]
 for key in a.entries:
  if key.startswith(base+'registry-growth-')and key.endswith('-witness.bin'):growth.append(list(a.words(key,32,'Q')))
 before_metadata=metadata_model.derive(normal_facts,mfc_births,string_births,resource,growth,current_source['API_before'],physical_contracts);after_metadata=metadata_model.derive(normal_facts,mfc_births,string_births,resource,growth,current_source['API_after'],physical_contracts)
 def table(meta):
  result={}
  for guest,o in meta['owners'].items():
   v=[0]*16;v[:9]=[1,guest,o['requested'],o['extent'],o['mapped_bytes'],o['generation'],o['kind'],o['acquired'],o['native']];result[guest]=v
  return result
 byguest=table(before_metadata);birth_table=table(after_metadata);owners=[]'''
 edits=[('def build(a,level,seq,root,current_source,owner_cut):','def build(a,level,seq,root,current_source,owner_cut,metadata_model,physical_contracts):'),(old,new),('need(sum(v[\'kind\']==4 for v in owners)=={0x4103f0:8,0x410440:10,0x459b40:19}[root],"Exact current root-entry MFC owner roles; later allocation generations excluded")','need(len(owners)=={0x4103f0:8,0x410440:10,0x459b40:19}[root] and sum(v[\'kind\']==1 for v in owners)==1,"Exact current total root-entry owner roles including registry; future births excluded")'),('v=byguest[w[12]];initial=', 'v=birth_table[w[12]];initial='),('static_pages_from_actual_root_BEFORE=True)','static_pages_from_actual_root_BEFORE=True,causal_owner_metadata=before_metadata,metadata_API_cut=current_source[\'API_before\'],future_allocation_summary_used=False)')]
 ps,n=change(p,q,edits,out,'adapter4');paths.extend(ps)
 p=R/'tools/m4-startup141-paired/constructor_native36_source141_v5.py';q=p.with_name('constructor_native36_source141_v6.py')
 edits=[('constructor_native_input141_v3.py','constructor_native_input141_v4.py'),("  supplement=json.loads(pin(owner_export_path,owner_export_sha).read_bytes());", "  MD=load('tools/m4-startup141-paired/native_owner_metadata_v3.py','causal_current_native_owner_metadata');physical_contracts={int(k):v for k,v in json.loads(pin(ROOT_CONTRACT).read_bytes()).items()}\n  supplement=json.loads(pin(owner_export_path,owner_export_sha).read_bytes());"),('inp=A.build(f,level,seq,root,carried,owner_cut);write','inp=A.build(f,level,seq,root,carried,owner_cut,MD,physical_contracts);write')]
 # Use the report namespace's immutable physical contract, before any reader.
 edits[1]=(edits[1][0],edits[1][1].replace('ROOT_CONTRACT',repr(str(cp.resolve()))))
 ps,ns=change(p,q,edits,out,'source6');paths.extend(ps)
 provider=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';rows=json.loads(provider.read_bytes())['instructions'];assert next(v for v in rows if v['pc']==0x78004482)['bytes_hex']=='6880000000'and next(v for v in rows if v['pc']==0x78004487)['bytes_hex']=='e827ceffff'
 for name in('locale_batch.hpp','locale_batch_operations.inc','lockit_operations.inc','registry_api.inc','mfc_operations.inc','strings_operations.inc','session_impl.inc'):paths.append(R/'reports/m4-startup141-runway/service-preparation-r2'/name)
 paths.extend([provider,R/'tools/m4-startup141-paired/native_owner_metadata_v1.py',R/'tools/m4-startup141-paired/native_owner_metadata_v3.py',Path(__file__).resolve()]);report=out/'report.json';report.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,reader_opened=False,source_execution=False,root_admission_minted=False,adapter_inverse_hunks=n,source_inverse_hunks=ns,whole_parent_inverses=True,causal_metadata_derived_before_cut=True,source_birth_request_and_generation_required=True,final_allocation_summary_not_input=True,future_growth_old_fields_corroboration_only=True,physical_bootstrap_PUSH128_CALLmalloc_bound=True,distinct_initial_Lockit_generation_bound=True,actual_causal_metadata_execution_pending=True,complete_constructor_acceptance_gate=False,initializer_credit=0,files={str(v.resolve()):sha(v)for v in paths}),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),adapter_sha256=sha(out.parents[2]/'tools/m4-startup141-paired/constructor_native_input141_v4.py')if False else sha(R/'tools/m4-startup141-paired/constructor_native_input141_v4.py'),source_sha256=sha(R/'tools/m4-startup141-paired/constructor_native36_source141_v6.py'))))
if __name__=='__main__':main()
