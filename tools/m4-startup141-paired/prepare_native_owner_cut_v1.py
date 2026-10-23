"""Code-only owner-cut adapter preparation; no reader, imports or source execution."""
from pathlib import Path
import ast,hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-owner-cut-preparation-r1';assert not out.exists();out.mkdir()
 p=R/'tools/m4-startup141-paired/constructor_native_input141_v2.py';q=p.with_name('constructor_native_input141_v3.py');assert not q.exists();a=p.read_text();b=a;changes=[]
 def edit(x,y):
  nonlocal b
  assert b.count(x)==1;b=b.replace(x,y);changes.append((x,y))
 edit('def build(a,level,seq,root,current_source):','def build(a,level,seq,root,current_source,owner_cut):')
 x=' memory={int(key[len(prior)+6:-4]):a.data(key)for key in a.entries if key.startswith(prior+"-page-")}'
 y=x+'''
 # Native source6 intentionally omitted these checkpoint owner pages from its
 # ordinary export. The ROOT-admitted supplement exposes only the genuine first
 # MFC BEFORE cut; owner bytes carry back to root entry via the complete prefix.
 need(owner_cut['level']==level and owner_cut['sequence']==seq and owner_cut['root']==root and owner_cut['checkpoint_prefix']==starts[first] and owner_cut['checkpoint_name']=='constructor-mfc-before',"Exact genuine first borrowed MFC BEFORE owner cut")
 call=current_source['constructor_call_results'][0];journal=current_source['whole_literal_source_accesses'];need(call[0]==root and call[2]==0x5abd26 and call[4]==call[1]+5,"Exact first literal MFC allocator CALL")
 call_indices=[i for i,v in enumerate(journal)if v==[call[1],call[3],call[4],4,1]];need(len(call_indices)==1,"One whole source saved-return operand identifies first MFC cut")
 prefix=journal[:call_indices[0]+1];need(not any(v[4] and v[1]<0x32000000 and v[1]+v[3]>0x31000000 for v in prefix),"Complete current source root prefix changes no dynamic owner byte")
 need(owner_cut['pages'] and len({v['address']for v in owner_cut['pages']})==len(owner_cut['pages']),"Distinct complete dynamic owner cuts, never empty stack-only substitute")
 owner_input_addresses=[]
 for row in owner_cut['pages']:
  address=row['address'];raw=bytes.fromhex(row['hex']);need(type(address)is int and 0x31000000<=address<0x32000000 and row['logical_key']==starts[first]+'-page-'+str(address)+'.bin' and row['bytes']==len(raw) and len(raw)>0 and __import__('hashlib').sha256(raw).hexdigest()==row['sha256'],"Whole own actual checkpoint dynamic backing identity")
  need(address not in memory,"Supplement may not replace an existing own input region");memory[address]=raw;owner_input_addresses.append(address)
'''
 edit(x,y)
 x=' APIs=[]'
 y=''' need(all(v in byguest and byguest[v][4]==len(memory[v])for v in owner_input_addresses),"Every supplemental backing joins exact actual allocation mapped extent")
 need(sum(v['kind']==4 for v in owners)=={0x4103f0:8,0x410440:10,0x459b40:19}[root],"Exact current root-entry MFC owner roles; later allocation generations excluded")
 APIs=[]'''
 edit(x,y)
 edit('prior_checkpoint_nonphase_regions_carry_physical_review_pending=True)','prior_checkpoint_nonphase_regions_carry_physical_review_pending=True,owner_input_cut=owner_cut[\'checkpoint_prefix\'],owner_input_prefix_call_index=call_indices[0],owner_input_prefix_no_dynamic_write=True,owner_input_snapshot_is_constructor_MFC_BEFORE=True,static_pages_from_actual_root_BEFORE=True)')
 ast.parse(b);q.write_text(b);back=b
 for x,y in reversed(changes):assert back.count(y)==1;back=back.replace(y,x)
 assert back==a
 delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 inv=out/'inverse.json';inv.write_text(json.dumps(delta,indent=2)+'\n')
 source=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';receipt=json.loads(source.read_bytes());assert sha(source)=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'and receipt['passed']and receipt['paired_export_readers_closed']
 journalpath=source.parent/'Constructor-carried-source-derivations.json';assert sha(journalpath)==receipt['files'][str(journalpath.resolve())];rows=json.loads(journalpath.read_bytes());facts=[]
 for row in rows:
  c=row['constructor_call_results'][0];js=row['whole_literal_source_accesses'];hits=[i for i,v in enumerate(js)if v==[c[1],c[3],c[4],4,1]];assert len(hits)==1;pre=js[:hits[0]+1];assert not any(v[4]and v[1]<0x32000000 and v[1]+v[3]>0x31000000 for v in pre)
  facts.append(dict(level=row['level'],sequence=row['sequence'],root=row['root'],call_index=hits[0],source_prefix_operands=len(pre),dynamic_owner_writes=0,nonowner_writes=sum(bool(v[4])for v in pre)))
 assert len(facts)==36;f=out/'current-prefix-facts.json';f.write_text(json.dumps(facts,indent=2)+'\n')
 paths=[p,q,inv,source,journalpath,f,R/'reports/m4-startup141-source/preparation-r6/paired_exports.py',R/'reports/m4-startup141-runway/service-preparation-r2/session_impl.inc',R/'tools/m4-constructor-native/component_v5.cpp',Path(__file__).resolve()]
 r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,reader_opened=False,canonical_reader_opened=False,initializer_credit=0,adapter=str(q),whole_parent_inverse=True,inverse_hunks=len(delta),actual_source_prefix_cases=36,dynamic_owner_prefix_writes=0,static_before_pages_preserved=True,supplement_export_pending=True,supplement_and_adapter_admitted=False,previous_nonphase_full_region_carry_proven=False,control_recipe=['reject wrong level/sequence/root/prefix/name','reject zero or duplicate owner cuts','reject wrong key/address/length/hash','reject changed first-call PC/frame/return or duplicate operand','reject any overlapping prefix owner write including cross-boundary width','reject wrong mapped extent/unknown generation','reject missing or future MFC owner roles','preserve real static prefix writes without seeding them'],files={str(v.resolve()):sha(v)for v in paths}),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),adapter_sha256=sha(q))))
if __name__=='__main__':main()

