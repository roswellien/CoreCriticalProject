"""Exact native own-input adapter to current141 selected chronology.

Preparation only. Paired relational reuse requires actual current original18
and ROOT admission of the resulting fullsource derivation, not isolated37.
"""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/native-constructor-adapter-preparation-r1';assert not out.exists();out.mkdir();p=R/'tools/m4-138-validation-review/constructor_native_input_v7.py';q=R/'tools/m4-startup141-paired/constructor_native_input141_v1.py';assert not q.exists();a=p.read_text();b=a
 changes=[('Ordinary sealed native37 own BEFORE adapter','Ordinary sealed current native141 own BEFORE adapter'),('def build(a,level,seq,root):','def build(a,level,seq,root,current_source):'),('table=a.words("selected-table.bin",37);phase=table.index(root)','table=a.words("selected-table.bin",141);phase=table.index(root);need(phase=={0x4103f0:13,0x410440:14,0x459b40:39}[root],"Exact current physical selected constructor141 chronology")')]
 for old,new in changes:assert b.count(old)==1;b=b.replace(old,new)
 needle=' need(cpu==native[36:76]and fx==native[116:628],"Same genuine phase/component BEFORE architecture")\n'
 added=''' need(current_source['level']==level and current_source['sequence']==seq and current_source['root']==root and current_source['phase']==phase,"Exact current carried native source row")
 need(current_source['AFTER_seed']is False and current_source['source_seed']is False and current_source['whole_native_component_journals_compared']is True and current_source['whole_native_State_CPU_FX_compared']is True,"Current fullcarried source component gate, no isolated current-result substitution")
 import hashlib
 need(hashlib.sha256(state).hexdigest()==current_source['computed_before_State_sha256']and list(struct.unpack('<10I',cpu))==current_source['computed_before_CPU']and hashlib.sha256(fx).hexdigest()==current_source['computed_before_FX_sha256'],"Every genuine fullownBEFORE equals independently carried literal source projection")
'''
 assert b.count(needle)==1;b=b.replace(needle,needle+added);ast.parse(b);q.write_text(b);back=b.replace(needle+added,needle)
 for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
 assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n');files={str(x):sha(x)for x in[p,q,out/'inverse.json',R/'tools/m4-138-validation-review/constructor_source_pair_v9.py',R/'reports/m4-startup141-source/combined-source-provider-r6/report.json',R/'reports/m4-startup141-source/combined-source-provider-r6/Constructor-carried-source-derivations.json',Path(__file__).resolve()]}
 (out/'ROOT-recipe.txt').write_text('ROOT review/admit adapter before any imports or ordinaryraw access. Current source6 branch O0/O2 only; actual paired original must be new sourcePASS18 from currentstrict3. Native adapter preserves exact genuine API5, initial allocation16B/source request and extent, CS24 guest input and no40B outputcopy, shim VOID EAX/ESP/EIP source return, fullown17fixed+extra+provider source input pages and5F2000, actual firstFSread beforeFSwrite. New table141/phase13/14/39 and fullbefore StateCPUFX against independent carried source36 mandatory. Derive native model current version under fulladmission, then compare full owncomputed afterCPU/FX/State/pages/owners against actual independent source6 targets before structural pair_v9 rules. Do not claim nativecarry from this finite owninput replay: current source6 already proves carry and is separately bound. Existing pair_v9 static initial8owner/order assumptions need actual current generation/lifetime/role closure before adapting; never silently use isolated37 reports.\n')
 files[str(out/'ROOT-recipe.txt')]=sha(out/'ROOT-recipe.txt');r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,exact_whole_parent_inverse=True,inverse_hunks=len(d),current_constructor_phases={0x4103f0:13,0x410440:14,0x459b40:39},actual_current_fullcarry_required=True,new_original18_source_PASS_pending=True,full_constructor_paired_semantics_admitted=False,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r))))
if __name__=='__main__':main()
