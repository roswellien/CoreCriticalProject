"""Independent finite Context delta and physical O0/O2 admission of sorted138.

This admits bounded native observations only. Original chronology, connected
source equivalence, controls and acceptance remain separate obligations.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='d20bd38e5c4f8021e204808e37c4ef752b21053210b493bdad495bd3c4f7c7aa'
BH='b4cbd387ba718b52a900c5ff527749829f1936706c1b49c9e3a79a9765042ab6'
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
 pins={};counts=collections.Counter();links=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or v==h,(str(p),h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None,closure=True):
  d=json.loads(pin(p,h).read_bytes());assert d['passed']
  if closure:
   for q,h in d['files'].items():pin(q,h)
  return d
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def once(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
 try:
  folder=R/'reports/m4-joint-startup138/preparation-r2'
  p=read(folder/'report.json',PH);b=read(R/'reports/m4-joint-startup138/build-r3/build.json',BH)
  a=read(R/'reports/m4-joint-startup138/admission-map-r1/report.json','b096a804adf5dcb6567d092f27dfa0cd4661a446e7f76b198d037941fa89e91f')
  source=read(R/'reports/m4-tree-review/widget138-component-source-r2/report.json','a27c2c18d626389c14585545cc2553a51526008a08df5ebc63a3e86f3d289cba')
  read(R/'reports/m4-tree-review/joint131-prelaunch-r2/report.json','20245da873b39e5a7a029f7fc5e20ffe0995ff88962b21917387678523491568')
  read(R/'reports/m4-tree-review/fps7-prelaunch-r4/report.json','0948f36b4ca8c82bf8cb923b8965aa7cda99eb9901caf8f4ae0203deff970633')
  parent=read(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
  assert b['preparation_sha256']==PH and a['build_sha256']==BH and a['preparation_sha256']==PH
  assert not p['worker_executed']and not p['execution_admitted']and not p['initializer_credit']
  oldfolder=R/'reports/m4-joint-startup131/preparation-r1';old=pin(oldfolder/'native_main.cpp').read_text();cur=pin(folder/'native_main.cpp').read_text()
  # Invert only the inspected additions. The resulting whole main must be the
  # accepted131 main, including its untouched caller boundary and growth path.
  reduced=once(cur,'#include "widget_services.hpp"\n#include "widget_build_bindings.hpp"\n','')
  reduced=once(reduced,'std::span<const std::byte>widget_crt_;std::unique_ptr<AcceptedWidgetServices>widget_services_;std::unique_ptr<W::Component>widget_component_;bool widget_cleaned_{};','')
  reduced=once(reduced,'widget_crt_(crt),','')
  added=[]
  for marker in (' static void widget_entry(',' void setup_widgets(',' for(const auto&b:widget_bindings)r_.register_translation(',' void cleanup_widgets('):
   rows=[line for line in reduced.splitlines(True)if line.startswith(marker)];assert len(rows)==1
   added.append(rows[0]);reduced=once(reduced,rows[0],'')
  for x,y in [
   ('registry_->bootstrap();setup_widgets();','registry_->bootstrap();'),
   ('phase==138&&r_.calls().size()==141&&r_.translation_count()==139','phase==131&&r_.calls().size()==134&&r_.translation_count()==132'),
   ('failed_=true;if(widget_component_)widget_component_->context_fault();','failed_=true;'),
   ('1,6,138,828,17,sizeof(Native)','1,6,131,786,17,sizeof(Native)'),
   ('mfc_output.clear();widget_output.clear();','mfc_output.clear();'),
   ('records.reserve(138)','records.reserve(131)'),('records.size()==138','records.size()==131'),
   ('seq==6&&total==828','seq==6&&total==786'),
   ('Six persistent138-root sequences','Six persistent131-root sequences'),
   ('828native phases in6persistent138-root sequences','786native phases in6persistent131-root sequences')]:reduced=once(reduced,x,y)
  failure='try{context.cleanup_widgets();context.registry().finish();}catch(const std::exception&e){writer.append("CLEANUP-FAILURE.txt",e.what(),std::strlen(e.what()));}for(const auto&row:widget_output)writer.append(prefix+"Widget/"+row.name,row.bytes.data(),row.bytes.size());direct.prefix=prefix+"failed-cleaned/";context.registry().dump(&DirectPhaseWriter::sink,&direct);'
  reduced=once(reduced,failure,'');reduced=once(reduced,'Connected138 invocation refused','Connected130 invocation refused')
  reduced=once(reduced,'  context.cleanup_widgets();for(const auto&row:widget_output)writer.append(prefix+"Widget/"+row.name,row.bytes.data(),row.bytes.size());\n','')
  assert reduced==old,'Whole131 main retained outside the exact inspected additions'
  entry,setup,registration,cleanup=added
  for token in ['c&&&r==&c->r_&&observation&&c->widget_component_','overlay_cpu(c->s_,r.cpu());snapshot(r,c->s_,true);','if(b.root==r.cpu().eip){b.callback(r);routed=true;break;}','sync_fx(r,c->s_);snapshot(r,c->s_,false);']:
   assert entry.count(token)==1
  assert 'execute('not in entry and 'seed('not in entry and 'new State'not in entry
  assert setup.count('make_unique<W::Component>')==1 and setup.count('make_unique<AcceptedWidgetServices>(r_,*registry_)')==1
  assert 'r_.remill_state'not in setup and 'seed('not in setup
  assert '&widget_entry' in registration and 'b.source_size,b.source_sha256,widget_library_sha,widget_component_gate' in registration
  assert cleanup.index('context_fault()')<cleanup.index('cleanup_fonts(hardware)')<cleanup.index('widget_cleaned_=true')
  # A single original session/State/Runtime remains the only owner in Context.
  assert cur.count('make_unique<m4_onexit::Session>')==cur.count('std::construct_at(reinterpret_cast<State*>')==cur.count('seed(r_,repeat,cw,top)')==1
  assert cur.index('context.cleanup_widgets();for')<cur.index('Host growth_caller')
  helper=pin(folder/'widget_services.hpp').read_text()
  for token in ['&session.runtime()==&r','v[1]&&!v[3]&&!v[4]&&session.live_handle()','v[1]&&!v[4]&&session.live_handle()','call.site==0x5ac11e&&call.target==0x78004a36&&call.return_pc==0x5ac124&&!call.tail','session.borrow_widget_onexit(s,call.root,call.frame,call.return_pc);authority();']:
   assert token in helper
  assert 'initialize_current_caller'not in helper and 'new State'not in helper
  mapold=pin(R/'tools/m4-fps-native/fixture_v2.cpp','be1dd1e4745e5b82ebc305c0b17d5eebfffd467aaba13aff90a3ccd315f1e990').read_text()
  start=mapold.index('void map_current_formatter_sources(');end=mapold.index('\n} // namespace',start);mapping=mapold[start:end]
  mapping=mapping.replace('void map_current_formatter_sources(m4_runtime::Runtime&r,std::span<const std::byte>crt,Writer&w)','void map_current_formatter_sources(m4_runtime::Runtime&r,std::span<const std::byte>crt)').replace('need(','widget_require(').replace('w.bytes(','widget_dump(')
  mapping=mapping.replace('m4_runtime::','mw34::m4_runtime::').replace('m4::sha256','mw34::m4::sha256').replace('MemoryFaultReason::','mw34::MemoryFaultReason::').replace('const MemoryFault&','const mw34::MemoryFault&').replace('Permissions::','mw34::Permissions::').replace('static_cast<Permissions>','static_cast<mw34::Permissions>')
  assert helper.count(mapping)==1,'Whole previously observed own-page mapping only qualification/sink changes'
  assert len(a['source_page_map']['fixed'])==17 and len(a['source_page_map']['extra'])==52 and len(a['source_page_map']['union'])==69
  assert set(a['source_page_map']['union'])==set(a['source_page_map']['fixed'])|set(a['source_page_map']['extra'])
  # All copied prior inputs other than explicit protocol/build/count additions
  # remain whole byte-identical after their one directory relocation.
  for q in oldfolder.rglob('*'):
   if not q.is_file()or q.name=='report.json':continue
   rel=q.relative_to(oldfolder)
   if rel.as_posix()in ('native_main.cpp','joint_protocol.hpp','CMakeLists.txt','registration_contract.hpp','selected-order.json','integration-contracts.json','onexit_session.hpp'):continue
   assert pin(folder/rel).read_bytes()==pin(q).read_bytes().replace(oldfolder.as_posix().encode(),folder.as_posix().encode()),rel
   counts['whole_retained_prior_inputs']+=1
  assert pin(folder/'onexit_session.hpp').read_bytes()==pin(R/'reports/m4-fps-native/service-preparation-r2/session.hpp').read_bytes()
  cm=pin(oldfolder/'CMakeLists.txt').read_text().replace('mw34_joint_startup131','mw34_joint_startup138')
  cm=once(cm,'target_link_libraries(mw34_joint_startup138 PRIVATE bcrypt user32)','target_include_directories(mw34_joint_startup138 PRIVATE "${MW34_WIDGET_INCLUDE}")\ntarget_link_libraries(mw34_joint_startup138 PRIVATE "${MW34_WIDGET_LIBRARY}" bcrypt user32)')
  assert cm==pin(folder/'CMakeLists.txt').read_text()
  selected=p['selected_order'];assert len(selected)==138 and selected==sorted(selected,key=lambda x:x['slot'])
  newroots=[x['root']for x in a['root_phase_map']];assert len(newroots)==7 and [x for x in selected if x['entry']not in newroots]==parent['selected_order']
  S=load(R/'tools/analysis/pe.py','joint138_source_pe');game=S.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  for x in selected:assert struct.unpack('<I',game.read_va(x['slot'],4))[0]==x['entry'];counts['physical_sorted_initializer_slots']+=1
  C=load(R/'tools/m4-tree-review/amd64_coff.py','joint138_coff');PE=load(R/'tools/m4-tree-review/review_linked_mfc1168.py','joint138_image');N=load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','joint138_directories')
  for level,info in a['levels'].items():
   image=PE.AMD64Image(pin(info['worker'],info['worker_sha256']).read_bytes());definitions={}
   parent_objects=[pin(q)for q in info['parent_literal_objects']];assert len(parent_objects)==410 and list(map(str,parent_objects))==list(map(lambda q:str(Path(q).resolve()),parent['objects'][level]))
   widgets=[pin(q['path'],q['sha256'])for q in info['widget_objects']];assert len(widgets)==60
   objects=parent_objects+widgets+[pin(q)for q in info['actual_CMake_objects']if Path(q).name!='main.obj']+[pin(R/'reports/m4-joint-startup138/build-r3/connected_hardware_boundary.obj')]
   for q in objects:
    sy,se=C.parse(q.read_bytes());is_literal=q in parent_objects or q in widgets and q.name not in ('component.obj','native_api.obj')
    for s in sy.values():
     n=s['name']
     if q.name in ('native_api.obj','connected_hardware_boundary.obj')and n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call'):assert s['type']==0;s['type']=32
     if s['section']<=0 or s['type']!=32:continue
     selected_function=(is_literal and n.startswith(('sub_','mw34_'))and not n.startswith('__remill'))or n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call','mfc_connected_invoke_guarded','mw34_widget_invoke_guarded')or(q.name=='native_main.cpp.obj'and(n=='main'or '@Context@m4_mixed@mw34@@'in n and not n.startswith('??$')or '@AcceptedWidgetServices@@'in n and not n.startswith('??$')or n.startswith(('?map_current_formatter_sources','?widget_whole_checkpoint','?growth_and_cleanup'))))or(q.name=='component.obj'and(n.startswith('mw34_widget_')or '@Component@m4_widget_native@mw34@@'in n and not n.startswith(('??$','?size@','?data@'))))or n.startswith('?borrow_widget_onexit@')
     if not selected_function:continue
     raw,rels=C.function(sy,se,n)
     assert n not in definitions,(level,n,str(q))
     definitions[n]=(q,raw,rels,se)
   candidates={}
   for n,(q,raw,rels,se)in definitions.items():
    assert all(4<=x['type']<=9 or x['type']==11 and x['symbol']['section']>0 for x in rels),(level,n,[(x['type'],x['symbol']['name'])for x in rels])
    matches=C.linked_candidates(image,raw,[dict(x,type=4)for x in rels]);assert matches,(level,n,len(raw));candidates[n]=matches
   for n,(q,raw,rels,se)in definitions.items():
    matches=candidates[n]
    for x in rels:
     target=x['symbol']['name']
     if 4<=x['type']<=9 and target in candidates:
      dest={a for a,_ in candidates[target]};matches=[(a,z)for a,z in matches if a+x['offset']+4+x['type']-4+struct.unpack_from('<i',z,x['offset'])[0]in dest];assert matches,(level,n,target);counts['exact_current_linked_targets']+=1
    for address,actual in matches:
     for x in rels:
      if x['type']!=11:continue
      sym=x['symbol'];assert se[sym['section']]['bytes'][sym['value']:sym['value']+8]==bytes(8)
      offset=struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]-sym['value']
      d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
      assert offset>=0 and offset+sym['value']+8<=end-start+zero and N.image_bytes(image,start+offset+sym['value'],8)==bytes(8);counts['actual_initialized_current_TLS_relations']+=1
    links.append(dict(level=level,object=str(q),symbol=n,whole_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),addresses=[a for a,_ in matches]));counts['whole_linked_current_functions']+=1
   literals=[n for n in definitions if re.fullmatch('mw34_widget_game_f_[0-9a-f]+_body',n)];assert len(literals)==58
   for root in newroots:assert any(n.startswith('?entry_%x@'%root)for n in definitions)
   for marker in ('?widget_entry@Context@','?invoke_selected_body@Context@','?cleanup_widgets@Context@','?context_fault@Component@','?authority@AcceptedWidgetServices@','?cleanup_authority@AcceptedWidgetServices@','?borrow_widget_onexit@SessionImpl@'):
    assert any(n.startswith(marker)for n in definitions),(level,marker)
   # Literal archive member provenance is byte exact, not a basename assertion.
   library=pin(info['widget_library'],info['widget_library_sha256']).read_bytes();assert library.startswith(b'!<arch>\n');at=8;member_hashes=[]
   while at<len(library):
    hdr=library[at:at+60];assert len(hdr)==60 and hdr[-2:]==b'`\n';size=int(hdr[48:58]);body=library[at+60:at+60+size];assert len(body)==size
    if hdr[:16].strip()not in (b'/',b'//'):member_hashes.append(hashlib.sha256(body).hexdigest())
    at+=60+size+(size&1)
   assert at==len(library)and collections.Counter(member_hashes)==collections.Counter(pins[str(q)]for q in widgets)
   counts['whole_static_library_object_relations']+=60
   for h in info['actual_compiler_headers']:assert str(pin(h))in b['files'];counts['current_consumed_header_paths']+=1
   assert str(pin(info['forced_registry_header']))in info['actual_compiler_headers']and str(pin(info['widget_binding_header']))in info['actual_compiler_headers']
   cmds=[x for x in b['commands']if 'link.exe' in ' '.join(x['argv']).lower()and str(Path(info['worker']).parent)in' '.join(x['argv'])];assert len(cmds)==1 and cmds[0]['exit_code']==0
   response=cmds[0].get('expanded_response_arguments');assert response
   args={str(x).casefold()for x in response};assert all(str(q).casefold()in args for q in parent_objects)and info['widget_library'].casefold()in args
   counts['current_inherited_literal_inputs']+=410
   print(json.dumps(dict(level=level,whole_functions=len(definitions))),flush=True)
  pin(__file__);pin(sys.executable)
  for q,h in pins.items():pin(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'physical-links.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  d=dict(passed=passed,scope='Independent sorted138 single Context source delta and complete current selected function/target/TLS/static-library/compiler-input physical admission; only bounded native observation authorized',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),archive_reader_opened=False,actual_worker_launches=0,initializer_credit=0,current138_acceptance=False,requires=['fresh original chronology','connected whole source/provider/GDI and caller evidence','new Context refusal/retry and cleanup controls','current paired acceptance'],files=pins)
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
