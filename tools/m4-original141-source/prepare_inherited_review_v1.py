"""Immutable current141 reviewer derivative; no reader/model execution."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/inherited-review-preparation-r1';assert not out.exists();out.mkdir();p=R/'tools/m4-startup138-paired/review_inherited_current.py';q=R/'tools/m4-original141-source/review_inherited141_v1.py';assert not q.exists();before=p.read_text();text=before;changes=[]
 def edit(a,b,n=1):
  global_unused=None
  nonlocal text
  assert text.count(a)==n,(a,text.count(a));text=text.replace(a,b);changes.append((a,b,n))
 edit('import collections,hashlib,json,struct,sys,traceback','import collections,hashlib,json,re,struct,sys,traceback')
 edit("p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture/archive opened');a=sha(p)","p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json','No capture/archive/transport opened');a=sha(p);need(p.is_relative_to(OUTPUT)or ADMITTED.get(str(p))==a,'Every physical external reviewer input ROOT admitted, no fallback')")
 edit('def main(name):', '''def main(admission_path,admission_sha,configuration_path,configuration_sha,source_path,source_sha,name):
 global ADMITTED,OUTPUT
 ap=Path(admission_path).resolve();need(sha(ap)==admission_sha,'Exact ROOT independent post-source admission');ad=json.loads(ap.read_bytes());need(ad['passed']is True and ad['independent_review']is True and ad['scope_identity']=='original141_post_source_inherited_review'and ad['configuration_sha256']==configuration_sha and ad['original_source_sha256']==source_sha,'No cached original138 or self admission')
 ADMITTED={}
 for path,h in ad['files'].items():
  path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json','Ordinary closure only');need(str(path)not in ADMITTED and sha(path)==h,'Whole unique ROOT closure before any source record');ADMITTED[str(path)]=h
 OUTPUT=(R/'reports/m4-original141-source'/name).resolve();PINS[str(ap)]=admission_sha
 C=read(configuration_path,configuration_sha)
 need(C['schema']=='mw34-original141-source-input-contract-v1','Actual current source configuration')''')
 edit("out=R/'reports/m4-tree-review'/name",'out=OUTPUT')
 edit('p=Path(sys.argv[2]).resolve();a=read(p,sys.argv[3])',"p=Path(source_path).resolve();a=read(p,source_sha);need(a['configuration_sha256']==configuration_sha and a['original_validation_sha256']==C['validation']['sha256']and a['counts']['phases']==846 and a['counts']['callbacks']==111,'Actual new original141 source report, all846 registry relations and111callbacks')")
 edit("for receipt in [a]+[read(c['receipt'],c['sha256'])for c in a['cases']]:","for receipt in [a]+[read(c['receipt'],c['sha256'])for c in a['children']]:")
 edit("if Path(q).suffix.lower()in('.mwb','.zip'):","if Path(q).suffix.lower()in('.mwb','.mwi','.zip')or Path(q).name=='transport.json':")
 edit("'Current inherited source/physical table continuity'","'Historical accepted131 exact3955-span/table131 invariant retained; fresh current3980 physical source continuity separately required'")
 old="  raw_export=next(row for row in producer['paired_exports']if row['branch']=='original');need(Path(raw_export['transport_path']).resolve()==Path(v['original_capture']).resolve()and raw_export['transport_sha256']==sha(pin(v['original_capture'])),'Whole canonical original transport identity retained by raw exporter')"
 new="""  raw_export=next(row for row in producer['paired_exports']if row['branch']=='original');need(a['raw_export_report_sha256']==C['validation']['sha256']and raw_export['transport_path']==v['original_capture']and producer['counts']['phases']==846 and producer['callbacks']==111,'Same current original141 strict producer/transport metadata; no old138 export substitution')
  need(raw_export['logical_files']==261543 and raw_export['payload_bytes']==1540126431,'Exact current sealed ordinary geometry')
  for field in('index','payload'):pin(raw_export[field+'_path'],raw_export[field+'_sha256'])
  need(a['counts']['current_physical_131_root_table_pairs']==131 and a['counts']['current_exact_retained_source_spans']==3980 and a['counts']['current_total_source_spans']==6411,'Actual current source corpus retained3955 plus25declared spans, not historical result oracle')
  corpus=pin(R/'tools/m4-original141-source/retained_corpus141_v1.py').read_text();need("len(rows)==3980"in corpus and "len(current)==int(match[1])==6411"in corpus and "oldpages[page][1]"in corpus and "newpages[page][1]"in corpus,'Physical whole-span/table/byte continuity implementation explicitly retained')"""
 edit(old,new)
 edit("R/'reports/m4-startup138-original/original-validation-r3/fresh-cdecl.json'","Path(C['validation']['path']).parent/'fresh-cdecl.json'")
 edit("R/'tools/m4-startup138-original/format_source_v4_r5.py'","R/'tools/m4-original141-source/format_source141_v1.py'")
 edit("R/'tools/m4-startup138-original/current_inherited_source_v2_r6.py'","R/'tools/m4-original141-source/replay_original141_v3.py'")
 edit("R/'tools/m4-startup138-original/tree_source_r5.py'","R/'tools/m4-original141-tree-source/tree_source_v3.py'")
 edit('need(tree_phase==83','need(tree_phase==86')
 edit('asserted83','asserted86')
 edit("R/'reports/m4-startup138-original/preparation-r8/format_observer_x86.asm'","Path(C['source_preparation']['path']).parent/'format_observer_x86.asm'")
 edit("case['phase']==83 and s['phase']==83","case['phase']==86 and s['phase']==86")
 edit("scope='Independent physical bounded current original138","scope='Independent physical bounded current original141")
 edit("  q=out/'report.json';q.write_text", "  for path,h in PINS.items():need(sha(path)==h,'Final whole ordinary dependency conservation')\n  report.update(ROOT_admission_path=str(ap),ROOT_admission_sha256=admission_sha,configuration_sha256=configuration_sha,canonical_transport_file_hashed=False,canonical_transport_identity_deferred_to_acceptance_union=True,current_source_report_only=True,full_original846_CPU_execution_claim=False)\n  q=out/'report.json';q.write_text")
 edit("if __name__=='__main__':main(sys.argv[1])","if __name__=='__main__':main(*sys.argv[1:])")
 q.write_text(text);restored=text
 for a,b,n in reversed(changes):assert restored.count(b)==n,(b,restored.count(b));restored=restored.replace(b,a)
 assert restored==before
 a=before.splitlines(True);b=text.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a[i:j]),child=''.join(b[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n');files={str(p):sha(p),str(q):sha(q),str(out/'inverse.json'):sha(out/'inverse.json'),str(Path(__file__).resolve()):sha(Path(__file__))}
 (out/'ROOT-recipe.txt').write_text('UNEXECUTED. Wait for actual current source3 PASS/closed report and its exact SHA; never supply cached original138. ROOT independently reviews whole inverse plus authenticates current configuration/source report/all children/full files union, historical continuity3955 proof, current source corpus3980 code/spans, actual cdecl144, new source summaries, actual compiled formatter ASM and tree3/formatter1/controller3 code, all four retained tree-review footer files and index+payload before records. Fresh ROOT admission scope original141_post_source_inherited_review binds configuration_sha256 and original_source_sha256 and exact ordinary files. Canonical transport bytes deferred final acceptance union; exact current strict/export metadata retained. Invoke Python -B review_inherited141_v1.py ADMISSION SHA CONFIG SHA CURRENT_SOURCE SHA FRESH_NAME. No models/readers/native worker; whole source owner preimages/untouched tails and all six tree scopes independently replayed as scalar evidence. Full original846 CPU execution false; no credit.\n');files[str(out/'ROOT-recipe.txt')]=sha(out/'ROOT-recipe.txt')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,initializer_credit=0,exact_whole_parent_inverse=True,inverse_hunks=len(d),retained_historical_span_count=3955,actual_current_retained_source_span_requirement=3980,current_total_source_spans=6411,current_expected_tree_phase=86,current_expected_formatter_derivations=24,current_expected_cdecl_boundaries=144,current_source_report_sha256_unresolved=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),inverse_hunks=len(d))))
if __name__=='__main__':main()
