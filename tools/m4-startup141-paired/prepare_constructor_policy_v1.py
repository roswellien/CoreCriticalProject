"""Extract whole retained structural rules as pure admitted-current function."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/constructor-policy-preparation-r1';assert not out.exists();out.mkdir();p=R/'tools/m4-138-validation-review/constructor_source_pair_v9.py';q=R/'tools/m4-startup141-paired/constructor_relations141_v1.py';assert not q.exists();text=p.read_text();start=text.index('     def calls(result,inp):');stop=text.index('\n  assert len(cases)==36;',start);parent=text[start:stop]
 # Mechanical IO removal only. Each historical relation remains identical;
 # its finite inputs are now supplied by an admitted current141 loader.
 changes=[("     firsta=get(base/f'constructor-original18-source-r4/original-{seq}-4260848/input.json');firstb=get(base/f'constructor-native36-source-r6/{level}-{seq}-4260848/input.json')\n",''),("      earlier=get(base/f'constructor-original18-source-r4/original-{seq}-{earlier_root}/source-derivation.json')","      earlier=earlier_original_derivations[earlier_root]"),("     cases.append(dict(**frontier,exact_literal_PC_call_return_path=True,exact_flag_consumers=True,whole_typed_global5F2000=True,whole_source_logical_owner_fields=owner_rows,exact_source_owned_writes=len(a['constructor_owned_writes']),exact_balanced_FS_events=len(a['constructor_FS']),source_API_occurrences=5,original_whole_State_claim=False))","     return dict(sequence=seq,root=root,branch=level,exact_literal_PC_call_return_path=True,exact_flag_consumers=True,whole_typed_global5F2000=True,whole_source_logical_owner_fields=owner_rows,exact_source_owned_writes=len(a['constructor_owned_writes']),exact_balanced_FS_events=len(a['constructor_FS']),source_API_occurrences=5,original_whole_State_claim=False,complete_constructor_acceptance_gate=False)")]
 body=parent
 for old,new in changes:assert body.count(old)==1;body=body.replace(old,new)
 rawbody=body
 body='\n'.join(line[4:]if line.startswith('    ')else line for line in body.splitlines())+'\n'
 header='''"""Pure current141 constructor structural relation, all retained v9 rules.

No IO/model/eval; complete original/current native endpoint admissions are
caller prerequisites. Unread sentinel payloads retain exact own source carry;
unmodeled intervening-owner fields never gain a new crossbranch equality claim.
"""
import struct

def compare(seq,root,level,a,b,ain,binp,firsta,firstb,earlier_original_derivations,original_endpoint,native_endpoint,native_carried):
 assert type(seq)is int and 0<=seq<6 and root in(0x4103f0,0x410440,0x459b40)and level in('O0','O2')
 assert a['root']==b['root']==ain['root']==binp['root']==root and a['branch']==ain['branch']=='original'and b['branch']==binp['branch']==level
 assert a['source_AFTER_seed']is False and b['source_AFTER_seed']is False and ain['source_AFTER_seed']is False and binp['source_AFTER_seed']is False
 assert original_endpoint['sequence']==native_endpoint['sequence']==native_carried['sequence']==seq and original_endpoint['root']==native_endpoint['root']==native_carried['root']==root
 assert all(original_endpoint[k]is True for k in('source_complete','whole_GPR_EIP','defined_EFLAGS','whole_FX512','whole_ENV28'))and original_endpoint['source_AFTER_seed']is False
 assert native_endpoint['whole_own_CPU40']is True and native_endpoint['defined_EFLAGS']is True and native_endpoint['whole_own_State3504']is True and native_endpoint['whole_own_FX512']is True and native_endpoint['whole_own_ENV28']is True and native_endpoint['whole_own_pages_and_backings']is True and native_endpoint['source_AFTER_seed']is False
 assert native_carried['level']==level and native_carried['phase']=={0x4103f0:13,0x410440:14,0x459b40:39}[root]and native_carried['AFTER_seed']is False and native_carried['source_seed']is False and native_carried['whole_native_component_journals_compared']is True and native_carried['whole_native_State_CPU_FX_compared']is True
 assert firsta['root']==firstb['root']==0x4103f0 and firsta['branch']=='original'and firstb['branch']==level
 assert set(earlier_original_derivations)==set((0x4103f0,0x410440,0x459b40)[:(0x4103f0,0x410440,0x459b40).index(root)+1])
'''
 q.write_text(header+body);ast.parse(q.read_text());restored=rawbody
 for old,new in reversed(changes):
  if new:assert restored.count(new)==1;restored=restored.replace(new,old)
  else:
   anchor='     for current,first in((aa,firsta),(bb,firstb)):';assert restored.count(anchor)==1;restored=restored.replace(anchor,old+anchor)
 assert restored==parent
 (out/'mechanical-deltas.json').write_text(json.dumps([dict(parent=a,child=b)for a,b in changes],indent=2)+'\n')
 # Independent AST relation inventory retains all parent assertions even where
 # IO assignments have been removed. New incoming-current admission assertions
 # are additive, and deliberately do not supply source-derived endpoint fields.
 def guards(source):return [ast.dump(n.test,include_attributes=False)for n in ast.walk(ast.parse('def f():\n'+source))if isinstance(n,ast.Assert)]
 pg=guards('\n'.join(' '+line[4:]for line in parent.splitlines())+'\n');cg=guards(body);assert pg==cg
 (out/'retained-assertions.json').write_text(json.dumps(pg,indent=2)+'\n');files={str(x):sha(x)for x in[p,q,out/'mechanical-deltas.json',out/'retained-assertions.json',R/'tools/m4-startup141-paired/constructor_native_input141_v1.py',Path(__file__).resolve()]}
 (out/'ROOT-recipe.txt').write_text('UNEXECUTED pure policy. ROOT independently audits exact retained parent assertionAST/order and mechanical IO removal. Current original18 endpoint records must be exactly actual current strict3/configC451d; native36 own source endpoint records must first be generated from current adapter and checked fully against independently carried source6 component StateCPUFX/ENV/pages/backings/source operands. Metadata booleans are required output fields of a yet-unexecuted admitted endpoint checker, not fabricated inputs. This policy keeps initial8 actualroles, uniquegenerationoffset/bijection, exactrequests4/12/128, sourcebirth accounting, full source-owned writes, exactFSandgetter roles, wholetyped5F2000, conserved unreadsentinel tails and explicit interveningnonctorowner nonclaims. Actual original first8 observed:128Bmanager plus7 full16B selfcycles; thirdctor input19/output21. Currentnative roleproof still pending. No acceptance or scope extension. All53 inherited whole paired relations remain separately mandatory.\n');files[str(out/'ROOT-recipe.txt')]=sha(out/'ROOT-recipe.txt')
 r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,all_parent_assertion_ASTs_exactly_retained=True,retained_parent_assertions=len(pg),whole_extracted_relation_body_inverse=True,finite_IO_replacements=len(changes),native_current36_complete_endpoint_records_pending=True,current_full_paired53_relations_unmodified=True,complete_constructor_acceptance_gate=False,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),retained_assertions=len(pg))))
if __name__=='__main__':main()
