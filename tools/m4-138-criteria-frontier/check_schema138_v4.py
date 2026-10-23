"""Narrow current physical schema measurements; never grants acceptance allowances."""
from pathlib import Path
import argparse, ast, collections, hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sparse(data):
 assert len(data)>=12
 count=struct.unpack_from('<I',data,8)[0];assert len(data)==12+count*4104
 result={struct.unpack_from('<I',data,12+i*4104)[0]:(struct.unpack_from('<I',data,16+i*4104)[0],data[20+i*4104:4116+i*4104])for i in range(count)}
 assert len(result)==count
 return result
def unique(rows,key):
 d={key(x):x for x in rows};assert len(d)==len(rows),'No duplicate physical identity';return d
def main(a):
 out=R/'reports/m4-138-criteria-frontier'/a.name;assert not out.exists()
 pins={};passed=False;measurements={};links=[];counts=collections.Counter();unresolved=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip') and p.name!='transport.json'
  assert p.stat().st_size<=32*1024*1024,'Bounded ordinary input only'
  v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p,h=None):return pin(p,h).read_bytes()
 def module(p,name):
  s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 prepdir=Path(a.preparation).resolve()
 out.mkdir(parents=True)
 try:
  pr=read(prepdir/'report.json',a.preparation_sha)
  assert pr['passed'] and pr['whole_extracted_baseline_predicates_preserved']
  review=read(a.review,a.review_sha)
  assert review['passed'] is True and review['files'][str(Path(__file__).resolve())]==sha(__file__)
  assert review['files'][str(prepdir/'report.json')]==a.preparation_sha
  for p,h in pr['files'].items():
   if Path(p).suffix.lower()=='.py':pin(p,h)
  blocks={}
  for n in('native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py'):
   q=pin(prepdir/n,pr['files'][str(prepdir/n)]);blocks[n]=q.read_text();ast.parse(blocks[n])
  identities=read(prepdir/'inputs.json',pr['files'][str(prepdir/'inputs.json')])
  receipts={k:read(R/p,h)for k,(p,h)in identities.items()}
  for x in receipts.values():assert x['passed'] is True
  native_prelaunch=receipts['native_prelaunch'];prep=receipts['native_preparation'];build=receipts['native_build']
  assert build['preparation_sha256']==identities['native_preparation'][1]
  assert native_prelaunch['build_sha256']==identities['native_build'][1] and native_prelaunch['preparation_sha256']==identities['native_preparation'][1]
  folder=(R/identities['native_preparation'][0]).parent
  parent=read(R/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')
  component=pin(folder/'connected_component.cpp',native_prelaunch['files'][str(folder/'connected_component.cpp')]).read_text()
  oldfolder=R/'reports/m4-joint-startup131/preparation-r1'
  old_component=pin(oldfolder/'connected_component.cpp').read_text()
  assert component==old_component.replace(oldfolder.as_posix(),folder.as_posix()),'Whole current component source, only admitted generated-path substitution'
  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')
  C=module(R/'tools/m4-tree-review/amd64_coff.py','schema138_coff')
  M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','schema138_amd64')
  N=module(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','schema138_boundary')
  env=dict(R=R,pin=pin,read=read,blob=blob,module=module,prep=prep,build=build,folder=folder,parent=parent,component=component,lift=lift,C=C,M=M,N=N,re=re,struct=struct,Path=Path,counts=counts,links=links)
  exec(compile(blocks['native-inputs.py'],str(prepdir/'native-inputs.py'),'exec'),env)
  exec(compile(blocks['native-TLS.py'],str(prepdir/'native-TLS.py'),'exec'),env)
  exec(compile(blocks['native-boundary.py'],str(prepdir/'native-boundary.py'),'exec'),env)
  all_deps=[]
  for level,w in build['workers'].items():
   assert level in('O0','O2')
   bf=Path(w['path']).parent;image=M.AMD64Image(blob(w['path'],w['sha256']))
   graph=pin(bf/'build.ninja').read_text()
   env.update(level=level,w=w,bf=bf,image=image,graph=graph)
   exec(compile(blocks['native-graph.py'],str(prepdir/'native-graph.py'),'exec'),env)
   exec(compile(blocks['native-linked.py'],str(prepdir/'native-linked.py'),'exec'),env)
   # Preserve the baseline actual Ninja dependency-occurrence domain.
   pin(bf/'.ninja_deps');ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
   result=subprocess.run([str(ninja),'-C',str(bf),'-t','deps'],capture_output=True,timeout=30,creationflags=0x08000000)
   assert result.returncode==0 and len(result.stdout)<16*1024*1024
   consumed=[Path(s.strip())for s in result.stdout.decode().splitlines()if s.startswith('    ')and Path(s.strip()).is_file()]
   assert any(p.resolve()==(folder/'connected_component.cpp').resolve()for p in consumed) and any(p.resolve()==(folder/'native_main.cpp').resolve()for p in consumed)
   for p in consumed:pin(p)
   counts['current_compiler_dependency_paths']+=len(consumed)
   all_deps.extend(dict(level=level,path=str(p.resolve()),sha256=pins[str(p.resolve())])for p in consumed)
  # Complete unchanged positive source component domain, excluding ONLY the
  # exact three main/protocol/CMake files excluded by the accepted checker.
  pf=R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5'
  # Two exact current positive-file extensions are proved independently of
  # the otherwise byte-identical source domain. No changed file is skipped.
  original_widget=read(R/'reports/m4-fps-original/preparation-r1/report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1')
  wc=read(prep['widget_component_preparation'],prep['widget_component_preparation_sha256']);assert wc['passed'] is True
  wp=Path(prep['widget_component_preparation']).parent
  contracts=read(wp/'contracts.json',wc['files'][str(wp/'contracts.json')]);newroots=[x['root']for x in contracts['roots']]
  assert newroots==wc['roots'] and len(newroots)==7 and len(set(newroots))==7
  fixed=[int(v,16)for v in re.search(r' pages\{([^}]+)',blob(pf/'joint_protocol.hpp').decode())[1].split(',')];assert len(fixed)==17
  service=read(prep['borrowed_service_preparation'],prep['borrowed_service_preparation_sha256']);assert service['passed'] is True
  service_header=Path(prep['borrowed_service_preparation']).parent/'session.hpp'
  assert blob(folder/'onexit_session.hpp')==blob(service_header,service['files'][str(service_header)])
  positive_relations=[]
  def prove_positive_file(rel,before,after):
   if rel.as_posix()=='onexit_session.hpp':
    added=b' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);\r\n'
    at=b' void finish();void dump(Sink,void*)const;'
    assert before.count(at)==1 and before.count(added)==0 and after.count(added)==1
    assert after==before.replace(at,added+at) and after.replace(added,b'')==before
    return 'exact_one_method_declaration_no_fields_or_class_layout_change'
   assert rel.as_posix()=='registration_contract.hpp'
   old_pages=[int(v,16)for v in re.search(rb'registration_pages\{([^}]+)',before)[1].split(b',')]
   old_roots=[int(v,16)for v in re.search(rb'registration_roots\{([^}]+)',before)[1].split(b',')]
   assert len(old_pages)==29 and len(set(old_pages))==29 and len(old_roots)==101 and len(set(old_roots))==101 and not set(old_roots)&set(newroots)
   expected_pages=sorted((set(original_widget['observed_pages'])|set(original_widget['external_pages'])|set(old_pages)|set(fixed)|{0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000})-set(fixed))
   assert len(expected_pages)==52
   expected=before
   for name,count,values in [('registration_pages',29,expected_pages),('registration_roots',101,old_roots+newroots)]:
    pattern=rb'constexpr std::array<unsigned,'+str(count).encode()+rb'> '+name.encode()+rb'\{[^}]+\};'
    replacement=('constexpr std::array<unsigned,'+str(len(values))+'> '+name+'{'+','.join(hex(x)for x in values)+'};').encode()
    expected,n=re.subn(pattern,replacement,expected);assert n==1
   # The generator's whole registration header also normalizes CR bytes.
   assert before.replace(b'\r',b'').count(b'\n')==3+1
   assert expected.replace(b'\r',b'')==after
   page_union=read(folder/'source-page-union.json',prep['files'][str(folder/'source-page-union.json')]);assert page_union['fixed']==fixed and page_union['extra']==expected_pages
   phase_map=read(folder/'widget-phase-map.json',prep['files'][str(folder/'widget-phase-map.json')]);assert [x['root']for x in phase_map]==newroots
   assert [x for x in prep['selected_order']if x['entry']in newroots]==[dict(entry=x['root'],slot=x['slot'])for x in sorted(contracts['roots'],key=lambda z:z['slot'])]
   return 'exact101_callback_prefix_plus7_and29_page_source_inventory_union52'

  for p in pf.rglob('*'):
   if not p.is_file()or p.name=='report.json':continue
   rel=p.relative_to(pf)
   if rel.as_posix()in('native_main.cpp','joint_protocol.hpp','CMakeLists.txt'):continue
   before=blob(p).replace(pf.as_posix().encode(),folder.as_posix().encode());after=blob(folder/rel)
   if before==after:counts['whole_unchanged_positive_component_files']+=1;relation='whole_bytes_equal'
   else:relation=prove_positive_file(rel,before,after);counts['whole_exact_inverse_positive_component_files']+=1
   counts['whole_inherited_positive_file_domain']+=1
   positive_relations.append(dict(file=rel.as_posix(),relation=relation,parent_sha256=pins[str(p.resolve())],current_sha256=pins[str((folder/rel).resolve())]))
  assert counts['whole_exact_inverse_positive_component_files']==2
  measurements['positive_file_relations']=positive_relations
  main_code=pin(folder/'native_main.cpp').read_text()
  assert 'mfc_connected_hardware_call(&guarded,mfc_hardware.data())'in main_code and 'writer.append(prefix+"MFC-caller-hardware.bin"'in main_code
  assert 'const Inputs input;'in component and 'input(i)'in component
  assert 'for(const auto&row:input.new_mappings)observed(row.address,unsigned(row.before.size()),row.permissions)'in component
  assert 'observed(0x78037000,4096,3)'in component
  measurements['native_prelaunch']=dict(counts=dict(counts),worker_launched=False,source_AFTER_seed=False,whole_new_manager_CRT_TIB_endpoint_observations_declared=True)
  # Source preparation predicates remain specifically the inherited TIB
  # repair, not a false claim that the entire widget extension leaves memory unchanged.
  closure=receipts['source_closure'];assert closure['source_provider_sha256']=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
  sourcep=R/'reports/m4-joint-startup131-source/preparation-r6/report.json'
  sp=read(sourcep,'fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8')
  fields=('retained_failure_sha256','nonTIB_memory_change','persistent_original_layout_restored','candidate_AFTER_machine_seed','per_phase_BEFORE_machine_seed')
  for p,h in sp['files'].items():assert closure['files'].get(p)==h;pin(p,h)
  code=pin(R/'tools/m4-138-controls-review/seal_source6_closure.py',closure['files'][str(R/'tools/m4-138-controls-review/seal_source6_closure.py')]).read_text()
  assert "for record in(current_preparation,current_preflight):"in code
  measurements['source_preparation_inherited_TIB']={f:sp[f]for f in fields}
  # Original pack comparisons preserve the actual132 baseline owner/pages.
  op=receipts['original_preparation'];ob=receipts['original_build'];orr=receipts['original_prelaunch']
  of=(R/identities['original_preparation'][0]).parent
  assert ob['preparation_sha256']==identities['original_preparation'][1] and orr['preparation_sha256']==identities['original_preparation'][1] and orr['build_sha256']==identities['original_build'][1]
  p130=R/'reports/m4-startup130-original/preparation-r2';o130=read(p130/'report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
  current=sparse(blob(of/'pages.bin',op['pack_sha256']));prior=sparse(blob(p130/'pages.bin',o130['pack_sha256']))
  PE=module(R/'tools/analysis/pe.py','schema138_source_pe');game=PE.PEImage(blob(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  def physical(image,address,size):offset,_=image.rva_range(address-image.image_base,size);return image.data[offset:offset+size]
  spans=op['source_spans'];literal={}
  for row in spans:
   if row['origin']:continue
   data=physical(game,row['pc'],row['size'])
   assert game.data[row['image_offset']:row['image_offset']+row['size']]==data
   for i,z in enumerate(data):
    addr=row['pc']+i;assert addr not in literal or literal[addr]==z;literal[addr]=z
  oc=collections.Counter();pack_delta=[]
  for page,(rights,raw)in prior.items():
   assert page in current and current[page][0]==rights
   for i,(old,new)in enumerate(zip(raw,current[page][1])):
    if old==new:continue
    assert rights==1 and old==0xcc and literal.get(page+i)==new
    oc['exact_literal_pack_delta_bytes']+=1;pack_delta.append(dict(address=page+i,old=old,new=new))
   oc['whole_inherited_pack_pages']+=1
  oldof=R/'reports/m4-startup131-original/preparation-r4';changed=[]
  for n in('preserve_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','original_broker.hpp','fs-hook-bindings.json'):
   if blob(of/n)==blob(oldof/n):oc['whole_unchanged_accepted_observers']+=1
   else:changed.append(n)
  assert changed==['fs_observer_x86.asm','original_broker.hpp','fs-hook-bindings.json']
  for n in('reference_x86.asm','boundaries.asm','api_boundaries.asm'):assert blob(of/n)==blob(oldof/n);oc['whole_chronological_MFC_ASM_relations']+=1
  # Six formatter targets are a named subset of a current whole linked ASM
  # section, rather than a count of the11 all-observer sections.
  cp=of/'format_observer_x86.asm';assert blob(cp)==blob(oldof/'format_observer_x86.asm')
  proofs=read((R/identities['original_prelaunch'][0]).parent/'compiled-observers.json',orr['files'][str((R/identities['original_prelaunch'][0]).parent/'compiled-observers.json')])
  formatwhole=[x for x in proofs if x['symbol']=='format_observer_x86 whole source'];assert len(formatwhole)==1
  objpaths=[p for p in orr['files']if p.endswith('/format_observer_x86.obj')or p.endswith('\\format_observer_x86.obj')];assert len(objpaths)==1
  X=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','schema138_x86_coff');sy,se=X.coff(blob(objpaths[0],orr['files'][objpaths[0]]))
  for label in('strrchr','malloc','sprintf'):
   for kind in('entry','return'):
    name='_format_'+kind+'_'+label;rows=[s for s in sy.values()if s['name']==name];assert len(rows)==1 and rows[0]['section']>0;oc['whole_current_format_targets']+=1
  tlogs=[Path(p)for p in orr['files']if p.endswith('CL.read.1.tlog')];assert len(tlogs)==1
  consumed=set()
  for line in pin(tlogs[0],orr['files'][str(tlogs[0])]).read_text(encoding='utf-16').splitlines():
   p=Path(line.strip().lstrip('^'))
   if p.is_absolute()and p.is_file():consumed.add(pin(p,orr['files'][str(p.resolve())]))
  oc['actual_compiler_input_files']=len(consumed)
  assert oc['actual_compiler_input_files']==orr['counts']['actual_consumed_compiler_inputs']
  measurements['original_prelaunch']=dict(counts=dict(oc),changed_old_observer_files=changed,changed_observer_inverse_review_required=True)
  assert op['observed_pages']==read(oldof/'report.json')['observed_pages'] and len(op['observed_pages'])==ob['pages']==43
  assert blob(of/'connected_observer.hpp')==blob(oldof/'connected_observer.hpp')
  assert ob['MFC_domain_extra_regions']==12
  asm=pin(of/'reference_x86.asm').read_text();cpp=pin(of/'reference.cpp').read_text()
  for t in('mov ecx,2048','rep movsd','mov esi,DWORD PTR fs:[18h]'):assert t.lower()in asm.lower()
  for t in('mixed_teb_before_pages,8192','mixed_teb_after_pages,8192'):assert t in cpp
  assert not {0x4103f0,0x410440,0x459b40}&{x['entry']for x in op['selected_order']}
  measurements['original_preparation']=dict(ordinary_record_pages=len(op['observed_pages']),MFC_domain_extra_regions=ob['MFC_domain_extra_regions'],true_TIB8192_from_reviewed_current_ASM=True,constructor_prerequisites_observation_only=True,MFC_region_field_scope='Unchanged accepted declared domain layout/serializer; no invented region count from module page total')
  for leaf,value in(('whole-native-linked.json',links),('compiler-dependency-occurrences.json',all_deps),('original-pack-delta.json',pack_delta)):
   p=out/leaf;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  pin(Path(__file__).with_name('check_schema138_v1.py'),'f549f36a03a2a6c5123b2f29dc86f76eec14f2c445f1307972afbadc0d895ea8');pin(Path(__file__).with_name('check_schema138_v2.py'),'6a25b1108de0cbf5bfab9eef54a2266af782877b94a26a70d52e84b65e2ff1f2');pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Current bounded physical schema measurements in preserved baseline named domains; typed finite changes require separate ROOT criteria review',measurements=measurements,unresolved=unresolved,worker_launched=False,source_machine_executed=False,archive_reader_opened=False,fullraw_report_opened=False,configuration_created=False,allowance_created=False,acceptance_executed=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('preparation');p.add_argument('preparation_sha');p.add_argument('review');p.add_argument('review_sha');main(p.parse_args())
