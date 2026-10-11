"""Whole physical admission of current widget controls or seven-route FPS fixture.

Reuse the sealed successful widget's unchanged source inputs, then attribute
the new complete linked fixture, component, provider and assembly functions.
No observation reader or worker is opened by this admission.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH={
 'controls':'47af86a27b82f00b38b5da26eeb1017058f997d32bb89cac5d4ac81fa7a45663',
 'fps':'e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc',
}
BH={
 'controls':'63f6d56ce07bba98a5ec1decdbaf3e061751393807c15b3aa625292d38d34017',
 'fps':'fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7',
}

def main(kind,name):
 assert kind in PH
 out=R/'reports/m4-tree-review'/name; assert not out.exists();out.mkdir()
 files={};counts=collections.Counter();links=[];passed=False
 def pin(path,identity=None):
  path=Path(path).resolve();assert path.suffix.lower()not in('.zip','.mwb')
  with path.open('rb')as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
  assert identity is None or value==identity,(path,identity,value)
  assert str(path)not in files or files[str(path)]==value
  files[str(path)]=value;return path
 def read(path,identity=None,closure=True):
  d=json.loads(pin(path,identity).read_bytes())
  if closure:
   assert d['passed']
   for q,h in d['files'].items():pin(q,h)
  return d
 def load(path,name):
  spec=importlib.util.spec_from_file_location(name,pin(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  base=R/'reports'/('m4-widget-native'if kind=='controls'else'm4-fps-native')
  prepdir=base/('controls-preparation-r1'if kind=='controls'else'fixture-preparation-r1')
  builddir=base/('controls-build-r2'if kind=='controls'else'fixture-build-r1')
  prep=read(prepdir/'report.json',PH[kind]);build=read(builddir/'build.json',BH[kind])
  prior=read(R/'reports/m4-tree-review/widget6-prelaunch-r9/report.json','7bdd78f7db9e775dfa59a3aca1410ef750144ac1f21e9e8ec9057db7454ed42b')
  positive=read(R/'reports/m4-widget-native/fixture-preparation-r16/report.json','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401')
  assert build['preparation_sha256']==PH[kind] and not prep['native_executed'] and prep['initializer_credit']==0
  assert not prep['original_CPU_or_GDI_seeds'] and not prep['AFTER_machine_seed'] and not prep['per_root_State_or_page_seed']
  oldcpp=pin(R/'reports/m4-widget-native/fixture-preparation-r16/fixture.cpp').read_text()
  cpp=pin(prepdir/'fixture.cpp').read_text()
  oldinherit=pin(R/'reports/m4-widget-native/fixture-preparation-r16/inherited_main.cpp').read_text()
  inherit=pin(prepdir/'inherited_main.cpp').read_text()
  if kind=='controls':
   compdir=R/'reports/m4-widget-native/preparation-r6';compbuilddir=R/'reports/m4-widget-native/build-r7'
   comp=read(compdir/'report.json','714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9')
   cb=read(compbuilddir/'build.json','7bba3319abef8202d154229ba4243dadd6e2693381c86abcbd41bf41007d20bf')
   assert inherit==oldinherit and prep['parent_preparation_sha256']=='58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401'
   assert cpp[:cpp.index(' W::Component component(')]==oldcpp[:oldcpp.index(' W::Component component(')].replace('need(argc==7,"worker game CRT MFC MSVCP fresh-output independent-review-sha")','need(argc==8,"worker game CRT MFC MSVCP fresh-output independent-review-sha control-mode")')
   assert cpp[cpp.index(' }catch(const std::exception&e)'):]==oldcpp[oldcpp.index(' }catch(const std::exception&e)'):]
   assert prep['control_modes']==8 and not prep['whole_hidden_Runtime_private_retry_claim'] and not prep['whole_permissions_retry_claim']
   block=cpp[cpp.index(' W::Component component('):cpp.index(' }catch(const std::exception&e)')]
   for token in ('mode>=1&&mode<=8','if(mode==1)s.addr.ds_base.dword=4','s.aflag.df=1;r.cpu().eflags|=0x400;s.rflag.flat|=0x400','r.memory().store<unsigned>({0x5bb070},0)','b^1','if(mode==5)protect_image(0x5f4d78,Permissions::read)','if(mode==6)r.memory().protect({0x20001000},Permissions::read)','if(mode==7)r.memory().protect(r.fs_base(),Permissions::read)','mode==8?0x40ef50:0x40e250','refused&&r.poisoned()&&!reason.empty()','retry_refused&&r.poisoned()&&r.calls().size()==captured_calls','component.cleanup_fonts(cleanup);','registry.finish();'):
    assert block.count(token)==1,token
   assert block.count('component.execute(target,')==2 and block.count('whole_current_game(r,writer,"runtime")')==2
   assert block.count('component.checkpoint("component");registry.dump(&Writer::sink,&writer);')==2
   assert block.index('const auto captured_calls')<block.index('writer.prefix="retry-before/"')<block.index('try{component.execute(target,retry)')<block.index('writer.prefix="retry-after/"')<block.index('component.cleanup_fonts(cleanup)')
   for leaf in ('widget_bindings.hpp','contiguous-registration-spans.json'):
    assert pin(prepdir/leaf).read_bytes()==pin(R/'reports/m4-widget-native/fixture-preparation-r16'/leaf).read_bytes()
   current_prefix='?current@?A0x7BACD359@m4_widget_native@';registry_prefix='?A0xB08EDCB8@'
   counts['authored_refusal_seams']=8
  else:
   compdir=base/'component-preparation-r1';compbuilddir=base/'component-build-r1'
   comp=read(compdir/'report.json','294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18')
   cb=read(compbuilddir/'build.json','ec46a763da58431d8300b5f9493af5ecec1b25f33ffca837684ef0f851a4415f')
   assert (comp['literal_bodies'],comp['root_count'],comp['causal_operands'],comp['instructions'])==(58,7,25003,1246)
   assert (comp['physical_destination_offset'],comp['physical_post_return_pointer_offset'],comp['formatter_frame_offset'],comp['formatter_va_offset'])==(0x34,0x238,-140,-108)
   assert not comp['host_vsprintf_substitution'] and not comp['AFTER_State_or_memory_seed'] and not comp['original_handle_or_output_seed']
   relation=read(R/'tools/m4-fps-native/component-source-relations.json',closure=False)
   text=pin(relation['prior_cpp'],relation['prior_sha256']).read_text()
   assert len(relation['changes'])==16
   for row in relation['changes']:
    assert text.count(row['before'])==1;text=text.replace(row['before'],row['after']);counts['complete_reviewed_component_source_changes']+=1
   assert text==pin(compdir/'component.cpp').read_text()
   h=pin(R/'reports/m4-widget-native/preparation-r6/component.hpp').read_text()
   h=h.replace('std::array<Import, 6>','std::array<Import, 7>').replace('// Six explicit callbacks;','// Seven explicit callbacks;').replace('static void entry_479590(Runtime &);','static void entry_479590(Runtime &);\n  static void entry_40f000(Runtime &);')
   assert h==pin(compdir/'component.hpp').read_text()
   assert pin(compdir/'native_api.s').read_bytes()==pin(R/'reports/m4-widget-native/preparation-r6/native_api.s').read_bytes()
   for token in ('sizeof(FormatRecord)==2528','destination==root->object+0x34','fmt==0x5e1590&&va==root_frame-108','std::int64_t(f.frame)-root_frame==-140','last_return_PC==0x7802311e','format_dispatch_cursor==3','a==0x780103fa&&v==0x7800fe25','s.gpr.rax.dword==0','record.metadata[15]=1'):
    assert token in text,token
   service=read(base/'service-preparation-r2/report.json','d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2')
   assert service['root_extension']==0x40f000 and service['source_callback']==0x40f030 and service['extra_provider_API_calls']==0
   for row in service['copied_source_relations']:
    before=pin(row['prior_path'],row['prior_sha256']).read_text();after=pin(row['current_path'],row['current_sha256']).read_text()
    if row['name']=='session_impl.inc':
     before=before.replace('case 0x479590:callback=0x4795d0;break;','case 0x479590:callback=0x4795d0;break;case 0x40f000:callback=0x40f030;break;').replace('six normal widget roots','seven normal widget/FPS roots')
    assert before==after,row['name'];counts['whole_retained_or_exact_extended_service_files']+=1
   normalize=lambda x:re.sub(r'#include "[^"]*(session\.hpp)"','#include "session.hpp"',x)
   assert normalize(inherit)==normalize(oldinherit)
   assert 'registry.bootstrap();'in cpp and 'component.cleanup_fonts(hardware);'in cpp and 'registry.finish();'in cpp
   assert 'for(unsigned phase=0;phase<widget_bindings.size();++phase)'in cpp and 'status{1,unsigned(!failed),7,58,unsigned(r.poisoned())'in cpp
   assert cpp.count('initialize_current_caller(r);')==1
   current_prefix='?current@?A0x5F8EEB66@m4_widget_native@';registry_prefix='?A0x8F0C3198@'
  assert prep['component_preparation_sha256']==cb['preparation_sha256'] and prep['component_build_sha256']==files[str(pin(compbuilddir/'build.json'))]
  for i,row in enumerate(comp['namespace_relations']):
   before=pin(row['original_IR'],row['original_sha256']).read_bytes();after=pin(row['component_IR'],row['component_sha256']).read_bytes()
   assert before.replace(b'mw34_onexit_game_',b'mw34_widget_game_')==after;counts['whole_namespace_only_literal_IRs']+=1
   if kind=='fps'and i<52:
    oldcomp=read(R/'reports/m4-widget-native/preparation-r6/report.json','714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9',closure=False)
    oldrow=next(x for x in oldcomp['namespace_relations']if x['entry']==row['entry']);assert pin(oldrow['component_IR'],oldrow['component_sha256']).read_bytes()==after
  S=load(R/'tools/analysis/pe.py','extension_physical_i386')
  game=S.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  crt=S.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  def physical(image,pc,n):a,_=image.rva_range(pc-image.image_base,n);return image.data[a:a+n],a
  bindings=pin(prepdir/'widget_bindings.hpp').read_text()
  bound=[(int(a),int(b),c,int(d,16))for a,b,c,d in re.findall(r'\{(\d+),(\d+),"([0-9a-f]{64})",mw34::m4_widget_native::Component::entry_([0-9a-f]+)\}',bindings)]
  spans=read(prepdir/('contiguous-registration-spans.json'if kind=='controls'else'Runtime-physical-source-spans.json'),closure=False)
  spans=spans['spans']if isinstance(spans,dict)else spans
  assert len(bound)==len(spans)==(6 if kind=='controls'else 7)
  for row,b in zip(spans,bound):
   raw,offset=physical(game,row['root'],row['bytes']);assert raw.hex()==row['bytes_hex']and offset==row['file_offset']
   assert hashlib.sha256(raw).hexdigest()==row['sha256']and b==(row['root'],len(raw),row['sha256'],row['root'])
   assert row['final_RET']==row['end_exclusive']-1 and raw[-1]==0xc3;counts['whole_actual_registration_spans']+=1
  contract=read(compdir/'contracts.json',closure=False)
  for row in contract['instructions']:
   raw=bytes.fromhex(row['bytes_hex']);actual,_=physical(crt if row['pc']>=0x78000000 else game,row['pc'],len(raw));assert actual==raw;counts['whole_physical_source_rows']+=1
  C=load(R/'tools/m4-tree-review/amd64_coff.py','extension_actual_coff')
  PE=load(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','extension_actual_amd64')
  N=load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','extension_actual_image')
  for level in ('O0','O2'):
   image=PE.AMD64Image(pin(build['workers'][level]['path'],build['workers'][level]['sha256']).read_bytes())
   leveldir=builddir/level;objects=[leveldir/'fixture.obj',leveldir/'registry.obj',*[pin(x['path'],x['sha256'])for x in cb['levels'][level]['objects']]]
   parsed={str(q):C.parse(pin(q).read_bytes())for q in objects};definitions={}
   for q in objects:
    sy,se=parsed[str(q)]
    for s in sy.values():
     n=s['name']
     if s['section']<=0 or s['type']!=32:continue
     selected=(n=='main'or n.startswith(('?initialize_current_caller@','?whole_current_game@','?borrow_widget_onexit@'))or '@AcceptedServices@'in n or(q.name=='component.obj'and(n.startswith('mw34_widget_')or '@Impl@Component@m4_widget_native@mw34@@'in n and not n.startswith(('??$','?dtor$','?catch$','?size@','?data@'))or '@Component@m4_widget_native@mw34@@'in n and n.startswith(('?execute@','?cleanup_fonts@','?entry_','??0Component','??1Component'))or '@literal@m4_widget_native@mw34@@'in n))or n.startswith('mw34_widget_game_')and n.endswith('_body')or(q.name=='fixture.obj'and 'lambda' in n and 'main' in n and 'Permissions' in n))
     if selected:
      assert n not in definitions;raw,rels=C.function(sy,se,n);definitions[n]=(q,raw,rels,se)
   ap=next(q for q in objects if q.name=='native_api.obj');asy,ase=parsed[str(ap)]
   for s in asy.values():
    if s['name']in('mw34_widget_native_api','mw34_widget_hardware_call'):assert s['type']==0 and s['section']==1;s['type']=32
   for n in ('mw34_widget_native_api','mw34_widget_hardware_call'):
    raw,rels=C.function(asy,ase,n);definitions[n]=(ap,raw,rels,ase)
   candidates={}
   for n,(q,raw,rels,se)in definitions.items():
    assert all(4<=x['type']<=9 or x['type']==11 and x['symbol']['section']>0 for x in rels),(level,n)
    for x in rels:
     if x['type']==11:
      s=x['symbol'];assert s['name'].startswith((current_prefix,'?session_owner@'+registry_prefix,'?authority@'+registry_prefix,'?owner@m4_','?binding@m4_','?admitted_binding@m4_'));assert se[s['section']]['bytes'][s['value']:s['value']+8]==bytes(8)
    matches=C.linked_candidates(image,raw,[dict(x,type=4)for x in rels]);assert matches,(level,n,len(raw));candidates[n]=matches
   for n,(q,raw,rels,se)in definitions.items():
    matches=candidates[n]
    for x in rels:
     target=x['symbol']['name']
     if 4<=x['type']<=9 and target in candidates:
      dest={a for a,_ in candidates[target]};matches=[(a,b)for a,b in matches if a+x['offset']+4+x['type']-4+struct.unpack_from('<i',b,x['offset'])[0]in dest];assert matches,(level,n,target);counts['actual_linked_complete_function_relations']+=1
    for a,b in matches:
     for x in rels:
      if x['type']!=11:continue
      s=x['symbol'];v=struct.unpack_from('<i',b,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]-s['value']
      d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
      assert v>=0 and v+s['value']+8<=end-start+zero and N.image_bytes(image,start+v+s['value'],8)==bytes(8);counts['actual_initialized_TLS_cells']+=1
    links.append(dict(level=level,object=str(q),symbol=n,whole_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),whole_linked_candidates=[a for a,_ in matches]));counts['whole_linked_compiled_functions']+=1
   literals=[n for n in definitions if re.fullmatch('mw34_widget_game_f_[0-9a-f]+_body',n)];assert len(literals)==comp['literal_bodies']
   for root in prep['source_roots']:assert any(n.startswith('?entry_%x@'%root)for n in definitions)
   assert len(definitions['mw34_widget_native_api'][1])==211 and not definitions['mw34_widget_native_api'][2]
   assert len(definitions['mw34_widget_hardware_call'][1])==85 and [(x['offset'],x['type'],x['symbol']['name'])for x in definitions['mw34_widget_hardware_call'][2]]==[(25,4,'mw34_widget_invoke_guarded')]
   assert ase[5]['bytes']==struct.pack('<6I',0,211,0,211,296,12)
   ex=N.directories(image)[3];entries=list(struct.iter_unpack('<3I',N.image_bytes(image,image.image_base+ex[0],ex[1])))
   for n,length,uoff,usize in [('mw34_widget_native_api',211,0,12),('mw34_widget_hardware_call',85,12,8)]:
    assert len(candidates[n])==1;a=candidates[n][0][0];actual=[x for x in entries if image.image_base+x[0]==a];assert len(actual)==1 and image.image_base+actual[0][1]==a+length
    assert N.image_bytes(image,image.image_base+actual[0][2],usize)==ase[4]['bytes'][uoff:uoff+usize];counts['whole_actual_ASM_unwind_relations']+=1
   command=[x for x in build['commands']if x.get('expanded_response_arguments')and str(leveldir)in' '.join(x['argv'])];assert len(command)==1 and command[0]['exit_code']==0
   args={x.casefold()for x in command[0]['expanded_response_arguments']};assert all(str(q).casefold()in args for q in prep['levels'][level]['objects'])and prep['levels'][level]['component_library'].casefold()in args and prep['levels'][level]['fixed_objects']==427
   counts['actually_linked_inherited_COFFER_inputs']+=427
  pin(__file__);pin(sys.executable)
  for q,h in files.items():
   with Path(q).open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'physical-links.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  d=dict(passed=passed,kind=kind,scope='Independent current extension first-writer physical admission; no source/native equivalence or connected initializer credit',preparation_sha256=PH[kind],build_sha256=BH[kind],counts=dict(counts),actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=files)
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(files))))

if __name__=='__main__':main(sys.argv[1],sys.argv[2])
