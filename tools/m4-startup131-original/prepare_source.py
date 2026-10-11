"""Additive six-domain literal original adapter; only sealed small exports are read."""
from pathlib import Path
import hashlib,json,sys,ast
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
base=R/'tools/m4-mfc1168-connected-original/compare_source_v3.py';p=T/'compare_source.py';assert not p.exists()
s=base.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
one("B=R/'reports/m4-mfc1168-connected-original'","B=R/'reports/m4-startup131-original'")
one("v['counts']['actual_chronological_root_phases']==14","v['counts']['MFC_original_phases']==6 and v['counts']['phases']==786")
start=s.index("  current=read(Path(validation).parent/")
literal=s.index("  I=load(R/'tools/m4-crt-locale-batch-model-review",start)
end=s.index("  for module in list(sys.modules.values()):",literal)
block=s[literal:end]
tail="  q=out/'source-derivations.json';q.write_text(json.dumps(result,indent=2)+'\\n');pin(q)\n"
assert block.count(tail)==1;block=block.replace(tail,'  results.append(result)\n')
block=block.replace("counts['source_FS_install_restore_writes']=2;counts['ordered_source_operands']=len(m.accesses)","counts['source_FS_install_restore_writes']+=2;counts['ordered_source_operands']+=len(m.accesses)")
assert block.count('result=dict(root=0x5ae3e4,phase=13')==1
block=block.replace('result=dict(root=0x5ae3e4,phase=13','result=dict(sequence=seq,root=0x5ae3e4,phase=13')
adapter="""  current_cases=read(Path(validation).parent/'fresh-MFC-observations.json',v['files'][str((Path(validation).parent/'fresh-MFC-observations.json').resolve())]);need(len(current_cases)==6 and [x['sequence']for x in current_cases]==list(range(6)),'Exact six current original MFC domains')
  contracts=read(prep['contracts']);contract=dict(fixed_current_source_pages=prep['observed_pages'],external_source_pages=prep['extra_whole_source_pages']);need(len(contract['fixed_current_source_pages'])==43 and len(contract['external_source_pages'])==3,'Fixed original13146-page endpoint inventory')
  results=[]
  for seq,actual in enumerate(current_cases):
   phase={**actual,'slot':contracts['selected_order'][13]['slot']};boundaries=actual['boundaries'];api=actual['APIs'];domains=actual['domains'];eq((phase['root'],phase['slot']),(0x5ae3e4,0x5e0040),'Actual chronological source table cell')
   def raw(key):
    if key.startswith('MFC1168/'):key=f'phase/{seq}/13/'+key
    elif key.startswith('phase/0/13'):key=key.replace('phase/0/13',f'phase/{seq}/13',1)
    path=(Path(validation).parent/'actual-MFC-inputs'/key).resolve();need(str(path)in v['files'],'Exactly sealed current bounded source input '+key);return pin(path,v['files'][str(path)]).read_bytes()
"""
block=''.join(' '+line if line.strip()else line for line in block.splitlines(keepends=True))
after="  eq((counts['literal_source_instructions'],counts['ordered_source_operands'],counts['whole_normal_CPU_FX_ENV_frame64_boundary_joins'],counts['whole_actual_named_API_entry_return_frame_joins'],counts['whole_borrowed_backing_byteflows']),(852,678,42,24,30),'Complete source-derived six current normal-domain extents')\n  q=out/'source-derivations.json';q.write_text(json.dumps(results,indent=2)+'\\n');pin(q)\n"
s=s[:start]+adapter+block+after+s[end:]
one("pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v3.py');pin(__file__)","pin(R/'tools/m4-mfc1168-connected-original/derive_compare_v3.py');pin(R/'tools/m4-mfc1168-connected-original/compare_source_v3.py');pin(R/'tools/m4-startup131-original/prepare_source.py');pin(__file__)")
one("scope='Current genuine13-root-carried normal MFC cached-domain literal replay;7 complete normal and4 named API boundaries,whole source-derived borrowed backings/nonstack pages. Per-instruction chronological trace,opaque OS stack/TEB internals,lazy/cold paths and native integration remain separate.'","scope='Current genuine full131 six-domain MFC phase13 literal replay from each own carried BEFORE;42complete normal and24namedAPIpairs,30wholeborrowedbyteflows/nonstackpages. This is source-derived normal control, without new actual per-instruction trace,opaque OS stack/TEB/CS internal equivalence,lazy/cold or native acceptance.'")
ast.parse(s,filename=str(p));p.write_text(s)
q=T/'source-adapter-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes=['Six current authentic full131 MFC phase13 original domains from sealed small exporter only','Every source page/whole owner/TIB/CS input bound to final current original validation files','Actual bounded API volatile response inputs preserve literal CPU cleanup and no AFTER memory','All142literalcachedPCs/113operands percase remain required;30wholeborrowedbyteflows'],archive_reader_opened=False,original_worker_launched=False,native_credit=0),indent=2)+'\n')
print(p)
