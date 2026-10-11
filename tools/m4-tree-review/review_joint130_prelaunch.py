"""Bounded independent current130 schedule, composition, consumed build/link and runner review."""
import ast, collections, hashlib, importlib.util, json, re, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent));import review_connected125_v2 as C
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh130 integration review');out.mkdir(parents=True)
 passed=False;counts=collections.Counter()
 try:
  C.pin(__file__);C.pin(C.__file__)
  area=R/'reports/m4-joint-startup130';pd=area/'preparation-r1';bd=area/'build-r1';old=R/'reports/m4-joint-startup125/preparation-r4'
  p=C.read(pd/'report.json','21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f');b=C.read(bd/'build.json','4ccb1347bd85872f06ff6a57d1bd539effcd6d24de1c302b7cb2e4758b3ea976')
  prior=C.read(old/'report.json',p['parent_preparation_sha256']);accepted=C.read(p['parent_acceptance'],p['parent_acceptance_sha256']);native=C.read(p['native_preparation'],p['native_preparation_sha256']);cos=C.read(p['compound_runtime_preparation'],p['compound_runtime_preparation_sha256'])
  C.need(all(x['passed']for x in(p,b,prior,accepted,native,cos))and b['preparation_sha256']==C.PINS[str((pd/'report.json').resolve())]and not p['native_executed']and not b['guest_executed']and not p['initializer_credit'],'Exact current unexecuted native130 preparation/build and accepted125 lineage')
  C.need((p['packed_Native_bytes'],p['State_bytes'],p['FX_bytes'],p['CPU_bytes'],p['whole_source_pages'],p['registration_callbacks'],p['normal_owner_bound'])==(159716,3504,512,40,46,101,92)and p['full_dependency_acceptance_rehash_required']and not p['source_bodies_modified']and not p['per_phase_reseed']and not p['AFTER_machine_seed'],'Immutable ABI, finite owner bound and full acceptance obligation')
  for q,h in p['generated_sources'].items():C.pin(q,h);counts['generated_source_identities']+=1
  for q,h in b['artifacts'].items():C.pin(q,h);counts['actual_build_artifacts']+=1
  for q,h in b['tools'].items():C.pin(q,h)
  for q,h in(native['files']|cos['files']).items():
   path=Path(q)
   if str(path).startswith(str(Path(p['native_include'])))or str(path).startswith(str(Path(p['compound_runtime_preparation']).parent)):C.pin(q,h)
  loaderpath=C.pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('joint130_review_physical',loaderpath);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe);game=pe.PEImage(C.pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  def physical(a,n):off,_=game.rva_range(a-game.image_base,n);return game.data[off:off+n]
  added={0x4df610:0x5e01c8,0x4e0710:0x5e01cc,0x4e0810:0x5e01d0,0x4e1ca0:0x5e01d4,0x4b64f0:0x5e0160};selected=p['selected_order']
  C.need(len(selected)==130 and len({x['entry']for x in selected})==130 and selected==sorted(selected,key=lambda x:x['slot'])and [x for x in selected if x['entry']not in added]==prior['selected_order'],'Exact genuine130 relative order with every accepted125 entry retained')
  for x in selected:C.need(struct.unpack('<I',physical(x['slot'],4))[0]==x['entry'],'Every current130 physical table DWORD');counts['physical_table_pairs']+=1
  C.need(p['registration_roots']==prior['registration_roots']+[0x4df610,0x4e0710,0x4e0810,0x4e1ca0]and len(set(p['registration_roots']))==101 and 0x4b64f0 not in p['registration_roots'],'Exactly101 literal registration roots; COS registered only as Runtime numerical root')
  C.need(p['extra_pages']==prior['extra_pages']+[0x5cd000,0x5e3000,0x5e9000]and len(set(p['extra_pages']))==29,'Fixed17 plus29 current external pages, no ABI migration')
  prepcode=C.pin(R/'tools/m4-joint-startup130/prepare.py').read_text();buildcode=C.pin(R/'tools/m4-joint-startup130/build.py').read_text();parentbuild=C.pin(R/'tools/m4-joint-startup125/build.py').read_text();runner=C.pin(R/'tools/m4-joint-startup130/run.py').read_text();parentrunner=C.pin(R/'tools/m4-joint-startup125/run.py').read_text()
  tree=ast.parse(runner);assignment=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(y,ast.Name)and y.id=='replacements'for y in x.targets));replacements=ast.literal_eval(assignment.value);transformed=parentrunner
  for before,after in replacements:C.need(before in transformed,'Each explicit runner replacement exists');transformed=transformed.replace(before,after)
  C.need('125'not in transformed.replace('tools/m4-joint-startup125/run.py','')and 'finally:records.close()'in transformed and '(1,6,130,780,17,159716)'in transformed and "registration-roots.bin',101"in transformed and "pin(ROOT/'tools/m4-joint-startup125/run.py')"in transformed and 'verify_stage(stage' in transformed and "records.data('COMPLETE.txt')"in transformed,'Only explicit current counts changed in strict inherited stage/transport runner')
  counts['exact_runner_replacements']=len(replacements)
  C.need("parent.read_text().replace('startup125', 'startup130').replace('connected125', 'connected130').replace('changed125', 'changed130')"in buildcode and "sources[str(ROOT/'tools/m4-joint-startup125/build.py')]=sha"in buildcode,'Actual current build derives and seals exact parent builder')
  current=C.pin(pd/'native_main.cpp').read_text();parent=C.pin(old/'native_main.cpp').read_text().replace(old.as_posix(),pd.as_posix())
  parent=parent.replace('phase==125&&r_.calls().size()==128&&r_.translation_count()==126','phase==130&&r_.calls().size()==133&&r_.translation_count()==131')
  for a,z in [('selected125','selected130'),('Connected125','Connected130'),('connected125','connected130'),('persistent125','persistent130'),('Joint125','Joint130'),('records.reserve(125)','records.reserve(130)'),('records.size()==125','records.size()==130'),('total==750','total==780'),('750native','780native'),('1,6,125,750,17,sizeof(Native)','1,6,130,780,17,sizeof(Native)'),('125-root','130-root')]:parent=parent.replace(a,z)
  C.need(current==parent,'Full actual native worker changes only exact130 route/count/completion dimensions')
  C.need(C.pin(pd/'onexit_session.hpp').read_bytes()==C.pin(Path(p['native_include'])/'session.hpp').read_bytes(),'Current producer Session exactly native18 interface')
  for source in [cos['CPP']]+cos['bridges']:C.need(C.pin(pd/'derived'/Path(source).name).read_text()==C.pin(source).read_text(),'Whole compiled compound callbacks/bridges identical to independently reviewed Runtime2');counts['whole_compound_source_files']+=1
  for q,h in p['generated_sources'].items():
   path=Path(q);rel=path.relative_to(pd)
   if rel.as_posix()not in('native_main.cpp','joint_protocol.hpp','registration_contract.hpp','onexit_session.hpp','CMakeLists.txt','O0/registration_bindings.inc','O2/registration_bindings.inc','O0/mixed_bindings.hpp','O2/mixed_bindings.hpp','derived/compound.cpp','derived/compound-bridge-0.cpp','derived/compound-bridge-1.cpp'):
    C.need(path.read_text()==C.pin(old/rel).read_text().replace(old.as_posix(),pd.as_posix()),'Whole unchanged inherited consumed/generated source '+str(rel));counts['whole_inherited_source_relations']+=1
  for level in('O0','O2'):
   C.need(len(p['objects'][level])==397 and p['objects'][level][:371]==prior['objects'][level]and len(set(p['objects'][level]))==397 and b['workers'][level]['objects']==p['objects'][level],'Exact371 retained plus25 formatter/mixed plus1 compound object input perlevel')
   for obj in p['objects'][level]:C.pin(obj,b['sources'][str(Path(obj).resolve())]);counts['literal_object_input_identities']+=1
   cfg=next(x for x in b['commands']if any(str(v)=='-DMW34_LEVEL='+level for v in x['arguments']));args=cfg['arguments'];C.need(cfg['exit_code']==0 and '-DMW34_REGISTRY='+p['native_library']in args and '-DMW34_REGISTRY_INCLUDE='+p['native_include']in args and '-DMW34_OBJECTS='+';'.join(p['objects'][level])in args,'Actual successful configure consumed native18 and exact397 current literalobjects')
   ninja=C.pin(bd/('build-'+level)/'build.ninja').read_text().replace('\\','/');C.need(all(str(Path(x)).replace('\\','/').replace(':','$:')in ninja for x in p['objects'][level]),'Every actual397 literal path retained in generated Ninja link graph');counts['literal_link_graph_inputs']+=397
   worker=b['workers'][level];C.pin(worker['path'],worker['sha256']);image=pe.PEImage(Path(worker['path']).read_bytes());C.need(image.machine==0x8664,'Fresh actual native AMD64 worker');counts['actual_amd64_workers']+=1
   binding=C.pin(pd/level/'registration_bindings.inc').read_text();oldbinding=C.pin(old/level/'registration_bindings.inc').read_text().replace(old.as_posix(),pd.as_posix());C.need(binding.startswith(oldbinding),'Every97 old exact registration binding retained byte for byte')
   for row in p['exact_new_root_bindings'][level]:
    root=row['entry'];body=native['formatting_bodies'][str(root)];C.need(row['physical_code_bytes']==body['source_bytes']and row['physical_code_sha256']==hashlib.sha256(physical(root,body['source_bytes'])).hexdigest()and row['object_sha256']==body['objects'][level]['sha256']and '&registration_entry' in binding and p['native_preparation_sha256']in binding,'Exact physical source/object/current native preparation binding');counts['new_literal_root_bindings']+=1
   fp=C.pin(pd/level/'mixed_bindings.hpp').read_text();C.need('std::array<FpBinding,11>fp_bindings'in fp and fp.count('&compound_cosine')==1 and cos['objects'][level]['sha256']in fp and p['compound_runtime_preparation_sha256']in fp and hashlib.sha256(physical(0x4b64f0,121)).hexdigest()in fp,'Unique borrowed-frame exact Runtime compoundCOS callback binding');counts['new_compound_root_bindings']+=1
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent bounded unexecuted joint130 composition, complete relative-order/source/count and actual397-object-per-level consumed build/link graph review; execution, all-body compiled attribution and full source/provider/pair acceptance separate',counts=dict(counts),preparation_sha256='21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f',build_sha256='4ccb1347bd85872f06ff6a57d1bd539effcd6d24de1c302b7cb2e4758b3ea976',capture_archives_opened=0,full_dependency_union_rehashed=False,all_final_body_attribution_claim=False,native_execution_credit=False,initializer_credit=0,files=C.PINS)
  target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counts=dict(counts),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
