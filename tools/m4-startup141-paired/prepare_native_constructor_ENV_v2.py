"""Strengthen explicit ownENV/API-FX source cut without running source."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-constructor-source-preparation-r2';assert not out.exists();out.mkdir();inverses=[];files={}
 specs=[]
 p=R/'tools/m4-startup141-paired/constructor_native_input141_v1.py';q=p.with_name('constructor_native_input141_v2.py');assert not q.exists();a=p.read_text();b=a
 anchor='  if not observed_return:\n';addition='  before_fx=a.data(prefix+"-fx.bin");after_fx=a.data(retpoint+"-fx.bin");need(len(before_fx)==len(after_fx)==512 and before_fx==after_fx,"Whole actual own API entry/return FX512 conservation, no FP output copied");fact["actual_API_before_FX512_hex"]=before_fx.hex();fact["actual_API_after_FX512_hex"]=after_fx.hex()\n';assert b.count(anchor)==1;b=b.replace(anchor,addition+anchor)
 old='BEFORE_FX_hex=fx.hex(),BEFORE_memory=';new='BEFORE_FX_hex=fx.hex(),BEFORE_ENV28_hex=native[2164:2192].hex(),BEFORE_memory=';assert b.count(old)==1;b=b.replace(old,new);ast.parse(b);q.write_text(b);assert b.replace(new,old).replace(addition+anchor,anchor)==a;specs.append((p,q,a,b))
 p=R/'tools/m4-startup141-paired/constructor_native36_source141_v1.py';q=p.with_name('constructor_native36_source141_v2.py');assert not q.exists();a=p.read_text();b=a;changes=[]
 def edit(old,new):
  nonlocal b
  assert b.count(old)==1,(old,b.count(old));b=b.replace(old,new);changes.append((old,new))
 edit('constructor_native_input141_v1.py','constructor_native_input141_v2.py')
 old="     stage['operation']='literal execution';result=D.derive(inp,preparation);write(case/'source-derivation.json',result)"
 new="""     stage['operation']='literal execution';result=D.derive(inp,preparation)
     program,_=D.M.source_program(preparation);need(all(not program[pc]['mnemonic'].startswith('f')for pc in result['PCs']),'Every reached literal instruction integer-only before endpoint opens')
     need(len(bytes.fromhex(inp['BEFORE_ENV28_hex']))==28 and len(inp['APIs'])==5 and all(len(bytes.fromhex(v['actual_API_before_FX512_hex']))==512 and v['actual_API_before_FX512_hex']==v['actual_API_after_FX512_hex']for v in inp['APIs']),'Complete actual all5 API FX preservation proves source noFP seam scope')
     result['source_computed_ENV28_hex']=inp['BEFORE_ENV28_hex'];result['source_ENV_input_cut']='Genuine own phase BEFORE28 plus complete integer-only literal path and whole5 actual API FX conservation; no endpoint input'
     write(case/'source-derivation.json',result)"""
 edit(old,new)
 old="     program,_=D.M.source_program(preparation);need(all(not program[pc]['mnemonic'].startswith('f')for pc in result['PCs']),'Every reached literal constructor/provider instruction integer-only; wholeENV source carry not inferred from changed output');need(raw[2164:2192]==raw[2192:2220],'Every actual current root entireENV28 unchanged under literal noFP scope')"
 new="     need(result['source_computed_ENV28_hex']==raw[2192:2220].hex()and inp['BEFORE_ENV28_hex']==raw[2164:2192].hex(),'Entire own literal-derived ENV28 result equals actual endpoint; before field separately authenticated')"
 edit(old,new)
 edit('whole_own_pages_and_backings=True,source_AFTER_seed=False','whole_own_pages_and_backings=True,source_ENV28_derived_from_BEFORE=True,actual_all5_API_FX_conserved=True,previous_checkpoint_nonphase_owner_carry_independently_proven=False,source_AFTER_seed=False')
 ast.parse(b);q.write_text(b);back=b
 for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
 assert back==a;specs.append((p,q,a,b))
 for p,q,a,b in specs:
  before=a.splitlines(True);after=b.splitlines(True);d=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
   if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
  inverses.append(dict(parent=str(p),child=str(q),exact_whole_inverse=True,hunks=len(d),deltas=d));files[str(p)]=sha(p);files[str(q)]=sha(q)
 (out/'inverse.json').write_text(json.dumps(inverses,indent=2)+'\n');files[str(out/'inverse.json')]=sha(out/'inverse.json');files[str(Path(__file__).resolve())]=sha(Path(__file__))
 r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,initializer_credit=0,whole_inverse_files=inverses,explicit_ENV28_from_own_BEFORE_before_endpoint_open=True,actual_all5_API_FX_entry_return_conservation_required=True,all_literal_reached_instructions_integer_only_required=True,previous_checkpoint_nonphase_owner_carry_proven=False,input_carry_policy_review_pending=True,all_parent_complete_endpoint_and_borrowed_operand_guards_retained=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r))))
if __name__=='__main__':main()
