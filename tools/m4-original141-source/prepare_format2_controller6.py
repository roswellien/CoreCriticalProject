"""Exact five physical linked shim identities replacing obsolete range only."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/format-preparation-r2';assert not out.exists();out.mkdir();files={};inverses=[]
 p=R/'tools/m4-original141-source/format_source141_v1.py';q=p.with_name('format_source141_v2.py');assert not q.exists();a=p.read_text()
 needle="        source_imports.update({(0x7810a30b,0x78146198):cp_targets[0x78146198],(0x7810a35e,0x78146184):cp_targets[0x78146184]})\n"
 addition="""        compiled_review=read(C['current_compiled_review']['path'],C['current_compiled_review']['sha256']);compiled_links=read(C['current_compiled_links']['path'],C['current_compiled_links']['sha256'])
        need(compiled_review['passed']and compiled_review['whole_linked_observer_source_attribution']is True and Path(compiled_review['actual_compiled_preparation']).resolve()==Path(C['source_preparation']['path']).parent.resolve(),'Actual current original141 complete linked observer attribution')
        need(compiled_review['files'][str(Path(C['current_compiled_links']['path']).resolve())]==C['current_compiled_links']['sha256']and compiled_review['files'][str(Path(validation['build_path']).resolve())]==validation['build_sha256'],'Whole physical current links and actual worker build bound by independent compiled review')
        named_shim_symbols={(0x4dea15,0x5bb5a8):'_format_entry_strrchr',(0x4deab1,0x5bb664):'_format_entry_malloc',(0x4dead1,0x5bb658):'_format_entry_sprintf',(0x7810a30b,0x78146198):'_lockit_api_Enter',(0x7810a35e,0x78146184):'_lockit_api_Leave'}
        need(set(source_imports)==set(named_shim_symbols),'Only exact five unchanged source CALL/IAT/provider semantic pairs')
        resolved={}
        for record in compiled_links:
            for relocation in record['relocations']:
                symbol=relocation['symbol']
                if symbol not in named_shim_symbols.values():continue
                target=relocation['actual_symbol_address'];need(relocation['resolution_kind']=='virtual address'and type(target)is int and target>0,'Physical current named linked shim resolution')
                need(symbol not in resolved or resolved[symbol]==target,'Every repeated current named shim relocation agrees');resolved[symbol]=target
        need(set(resolved)==set(named_shim_symbols.values()),'All five physical named observer/Lockit shims present')
        compiled_shims={key:resolved[symbol]for key,symbol in named_shim_symbols.items()}
"""
 assert a.count(needle)==1;b=a.replace(needle,needle+addition)
 old="need(0x18000000<=value<0x19000000,'Actual original observer IAT cell has declared worker owner')"
 new="need(value==compiled_shims[(source_pc,address)],'Actual original exact source CALL/IAT value equals its independently attributed current linked named shim')"
 assert b.count(old)==1;b=b.replace(old,new);ast.parse(b);q.write_text(b);assert b.replace(new,old).replace(needle+addition,needle)==a
 def record(p,q,a,b):
  before=a.splitlines(True);after=b.splitlines(True);d=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
   if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
  inverses.append(dict(parent=str(p),child=str(q),exact_whole_inverse=True,hunks=len(d),deltas=d));files[str(p)]=sha(p);files[str(q)]=sha(q)
 record(p,q,a,b)
 p=R/'tools/m4-original141-source/replay_original141_v5.py';q=p.with_name('replay_original141_v6.py');assert not q.exists();a=p.read_text();assert a.count("'format_source141_v1.py'")==1;b=a.replace("'format_source141_v1.py'","'format_source141_v2.py'");ast.parse(b);q.write_text(b);assert b.replace("'format_source141_v2.py'","'format_source141_v1.py'")==a;record(p,q,a,b)
 linkpath=R/'reports/m4-original141/root-compiled-review-r2/physical-links.json';links=json.loads(linkpath.read_bytes());expected={'_format_entry_strrchr':0x280371e0,'_format_entry_malloc':0x2803735f,'_format_entry_sprintf':0x280374de,'_lockit_api_Enter':0x28037066,'_lockit_api_Leave':0x28037122};facts={}
 for name,target in expected.items():
  rows=[r for record in links for r in record['relocations']if r['symbol']==name];assert rows and all(r['actual_symbol_address']==target and r['resolution_kind']=='virtual address'for r in rows);facts[name]=dict(target=target,physical_relocations=len(rows))
 (out/'inverse.json').write_text(json.dumps(inverses,indent=2)+'\n');files[str(out/'inverse.json')]=sha(out/'inverse.json')
 for p in [linkpath,R/'reports/m4-original141/root-compiled-review-r2/report.json',R/'reports/m4-original141/build-r2/build.json',Path(__file__).resolve()]:files[str(p)]=sha(p)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,initializer_credit=0,whole_inverse_files=inverses,physical_named_shim_facts=facts,semantic_delta='Exact current independently linked five CALL/IAT named shim identities replace only obsolete address-range owner guard. All literal source target semantics, operand/CPUFXENV/frame, owner byteflows, registry suffix and output comparisons retained; controller6 binds only formatter2.',other_family_oldbase_range_guards_found=[],old4_missing_compiled_review_build_field_pending=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
