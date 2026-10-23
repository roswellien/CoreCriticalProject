"""Whole-file common caller application reconstruction, no worker/capture IO."""
from pathlib import Path
import ast,json
R=Path(__file__).resolve().parents[2]
RECIPE='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'
def review(pin,read,counts):
 root=R/'reports/m4-version-source';recipe=read(root/'common-caller-preparation-r1/report.json',RECIPE);header=pin(recipe['caller_header'],recipe['caller_header_sha256']).read_bytes()
 assert recipe['application_count_per_worker']==1 and not recipe['source_after_seed']and not recipe['provider_or_heap_pages_seeded']and not recipe['source_reseed']
 source=pin(R/'tools/m4-version-source/prepare_common_pair_v1.py','c81511aff86682a99f863d31d45c1043900c161e881bb8dd10363c99d32a27bd').read_text();tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 parent_original=root/'original-preparation-r6';parent_native=root/'fixture-preparation-r3';current_original=root/'original-preparation-r8';current_native=root/'fixture-preparation-r4'
 op=read(parent_original/'report.json','37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6');np=read(parent_native/'report.json','ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee');co=read(current_original/'report.json','fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f');cn=read(current_native/'report.json','d42a831e4d123021470ba99bc6589081f90dbf1f3e3bab5664c76356ab630bc6')
 for d in(op,np,co,cn,recipe):
  for path,h in d['files'].items():pin(path,h)
 def once(s,a,b):assert s.count(a)==1,a[:100];return s.replace(a,b,1)
 env=dict(original=parent_original,native=parent_native,caller_sha=recipe['caller_header_sha256'],once=once)
 selected=[]
 for n in main.body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in('os','ns','seam','projection','code'):selected.append(n)
 assert len(selected)==12,len(selected)
 exec(compile(ast.Module(body=selected,type_ignores=[]),'frozen-common-source-only-expressions','exec'),env)
 expected_original=env['os'];before='std::vector<unsigned char>common_bootstrap_pages(memory_size);copy_pages(common_bootstrap_pages);out.append("common-caller/bootstrap-pages.bin",common_bootstrap_pages.data(),common_bootstrap_pages.size());';after='auto common_bootstrap_pages=std::make_unique<std::array<std::uint8_t,memory_size>>();copy_pages(*common_bootstrap_pages);out.append("common-caller/bootstrap-pages.bin",common_bootstrap_pages->data(),common_bootstrap_pages->size());';expected_original=once(expected_original,before,after)
 assert pin(current_original/'reference.cpp').read_text()==expected_original,'Exact complete original8 CPP rebuilt from original6 plus authored caller and sole fixed-array type correction'
 assert pin(current_native/'fixture.cpp').read_text()==env['ns'],'Exact complete native4 fixture rebuilt from native3 plus authored caller'
 extra=dict(common_caller_recipe_sha256=RECIPE,common_caller_header_sha256=recipe['caller_header_sha256'],common_caller_applied_once_after_own_real_producer=True,whole_bootstrap_BEFORE_preserved=True,no_per_source_reseed=True)
 assert json.loads(pin(current_original/'contracts.json').read_bytes())==dict(json.loads(pin(parent_original/'contracts.json').read_bytes()),**extra)
 for current,parent,d,changed in((current_original,parent_original,op,{'reference.cpp','contracts.json'}),(current_native,parent_native,np,{'fixture.cpp'})):
  for p in parent.iterdir():
   if not p.is_file()or p.name in('report.json','pins.json','failure.txt')or p.name in changed:continue
   assert pin(current/p.name).read_bytes()==pin(p).read_bytes(),p.name;counts['whole_common_retained_source_files']+=1
  assert pin(current/'common_caller.hpp').read_bytes()==header
 counts['whole_exact_common_application_CPP_relations']+=2;counts['whole_common_header_relations']+=2;counts['whole_common_contract_relation']+=1
 return dict(original_parent=op,native_parent=np,original_parent_CPP=pin(parent_original/'reference.cpp').read_text(),common_caller_recipe_sha256=RECIPE)
