"""Current full131 physical admission; original six-sequence proof remains separate."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
adapter=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch.py')
prefix=adapter.read_text().split("checks = r'''",1)[0]
assert prefix.count('C7D6B430')==2
prefix=prefix.replace('C7D6B430','BCC7028')
scope={'__file__':str(__file__),'__name__':'only_materialize'}
exec(compile(prefix,str(adapter),'exec'),scope)
text=scope['text'];globals().update({k:scope['scope'][k]for k in('BASE','V2','V3','V4')})
checks=r'''
  positive=receipt(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5/report.json','a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924')
  pf=Path(positive['generated_sources'].__iter__().__next__()).parent
  assert pf==R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5'
  for path in pf.rglob('*'):
   if not path.is_file()or path.name=='report.json':continue
   relative=path.relative_to(pf)
   if relative.as_posix()in('native_main.cpp','joint_protocol.hpp','CMakeLists.txt'):continue
   assert blob(folder/relative)==blob(path).replace(pf.as_posix().encode(),folder.as_posix().encode()),relative
   counts['whole_unchanged_positive_component_files']+=1
  selected=prep['selected_order']
  assert len(selected)==131 and selected==sorted(selected,key=lambda row:row['slot'])and len({row['entry']for row in selected})==131
  for row in selected:
   assert physical('game',row['slot'])==row['entry'];counts['all_physical_initializer_table_pairs']+=1
  protocol=pin(folder/'joint_protocol.hpp').read_text()
  values=re.search(r'constexpr std::array<std::uint32_t,131> entries\{([^\n]+)\};',protocol)[1]
  assert [int(v,0)for v in values.split(',')]==[row['entry']for row in selected]
  assert prep['Runtime_calls_per_selected_sequence']==134 and prep['current_registration_callbacks']==101
  old=pin(pf/'native_main.cpp').read_text().replace(pf.as_posix(),folder.as_posix())
  for a,b in [('phase==14&&r_.calls().size()==14','phase==131&&r_.calls().size()==134'),('records.reserve(14)','records.reserve(131)'),('records.size()==14','records.size()==131'),('seq==1&&total==14','seq==6&&total==786'),('1,1,14,14,17,sizeof(Native)','1,6,131,786,17,sizeof(Native)'),('1,1,sizeof(SequenceRecord),17','1,6,sizeof(SequenceRecord),17'),('const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}};','const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}};'),('One genuine-domain persistent14-root native prefix and owned cleanup complete; fullM4 incomplete','Six persistent131-root sequences and source growth/owned cleanup complete; fullM4 incomplete'),('14native phases in1persistent connected MFC prefix','786native phases in6persistent131-root sequences')]:
   assert old.count(a)>=1,a;old=old.replace(a,b)
  inherited=pin(Path(prep['parent_preparation']).parent/'native_main.cpp').read_text()
  begin=inherited.index('  // Genuine source root replay is a separate growth experiment, outside selected-table credit.')
  end=inherited.index('DirectPhaseWriter::current=nullptr;total+=records.size();++seq;',begin)
  old=old.replace('  context.registry().finish();direct.prefix=prefix+"registry-cleaned/";context.registry().dump(&DirectPhaseWriter::sink,&direct);need(!context.registry().live_handle(),"Current registry owner cleanup");',inherited[begin:end])
  assert old==main,'Whole current main is the exact stated finite schedule and inherited growth/cleanup delta'
  assert pin(folder/'CMakeLists.txt').read_text()==pin(pf/'CMakeLists.txt').read_text().replace('mw34_mfc1168_connected','mw34_joint_startup131')
  assert pin(folder/'registration_contract.hpp').read_bytes()==pin(Path(prep['parent_preparation']).parent/'registration_contract.hpp').read_bytes()
  assert not prep['current131_acceptance']and prep['pending_genuine_full131_scope']
'''
physical=r'''
   for prefix in ('main','?growth_and_cleanup@@'):
    candidates=[s['name']for s in sy.values()if s['name'].startswith(prefix)and s['section']>0 and s['type']==32];assert len(candidates)==1,prefix
    raw,relocs=C.function(sy,se,candidates[0]);matches=linked_candidates(image,raw,relocs);assert len(matches)==1,(prefix,len(matches));TLS_relations(image,raw,matches[0][1],relocs,se)
    links.append(dict(level=level,symbol=candidates[0],address=matches[0][0],whole_bytes=len(raw),relocation_DWORDs=len(relocs)));counts['whole_current_main_growth_functions']+=1
'''
edits=[
 ("B=R/'reports/m4-mfc1168-native'","B=R/'reports/m4-joint-startup131'"),
 ("'7f426089ae1c974d4e2b5c3e5500efe283d8634a54e6d934a428710fe078d309'","'6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5'"),
 ("'a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924'","'2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25'"),
 ('connected-fixture-build-r2/build.json','build-r1/build.json'),
 ("prep['source_roots']==14 and prep['source_sequences']==1","prep['source_roots']==131 and prep['source_sequences']==6"),
 ("prep['selected_order']==parent['selected_order'][:13]+[dict(entry=0x5ae3e4,slot=0x5e0040)]","prep['selected_order']==sorted(parent['selected_order']+[dict(entry=0x5ae3e4,slot=0x5e0040)],key=lambda row:row['slot'])"),
 ('phase==14&&r_.calls().size()==14&&r_.translation_count()==132','phase==131&&r_.calls().size()==134&&r_.translation_count()==132'),
 ('const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}}','const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}}'),
 ("  C=module(R/'tools/m4-tree-review/amd64_coff.py'",checks+"  C=module(R/'tools/m4-tree-review/amd64_coff.py'"),
 ('CMakeFiles/mw34_mfc1168_connected.dir','CMakeFiles/mw34_joint_startup131.dir'),
 ("   db=pin(bf/'.ninja_deps')",physical+"   db=pin(bf/'.ninja_deps')"),
 ("  pin(BASE);pin(V2);pin(V3);pin(V4);","  pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_native_prefix_v11.py');pin(BASE);pin(V2);pin(V3);pin(V4);pin(R/'tools/m4-joint-startup131/run.py');"),
 ('Independent first positive connected14 prefix prelaunch only','Independent full131 current physical admission; original six-sequence/provider/paired gates remain required')
]
for a,b in edits:
 assert text.count(a)>=1,(a,text.count(a));text=text.replace(a,b)
exec(compile(text,str(__file__),'exec'),globals())
