"""Independent additive original font initializer first-writer review; no launch."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
A=R/'reports/m4-font479590-original';OLD=R/'reports/m4-widget-original/preparation-r9'
PH='56dab048c049f8cf634c494ed894a8444bba8c50da0d4dc99c7a22cfeab50ab9'
BH='619213ef264aa0f104062a98c0b59c8c7683f94309d38930de27823a13f62624'
PINS={}
def need(v,m):
 if not v:raise ValueError(m)
def eq(a,b,m):need(a==b,m)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.iso'),'No archive reader');v=sha(p)
 need(h is None or h==v,'Exact physical pin '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def load(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def mod(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def text(p):return pin(p).read_text()
def main(name):
 out=R/'reports/m4-tree-review'/name;need(re.fullmatch('font479590-prelaunch-r[1-9][0-9]*',name)and not out.exists(),'Fresh review');out.mkdir()
 passed=False;counts=Counter();linked=[];pack_changes=[];compiled_relations=[]
 try:
  prior=load(R/'reports/m4-tree-review/widget-prelaunch-r9/report.json','59bdcd9b3e5bc5260aa71dca6bfcffe110c18b2f79c84cc108c916e3c6b3ede5')
  old=load(OLD/'report.json','ad3a1d2b6527a9ca19904743364273c366ea2a8565e627b9453a0d263c73ab6c')
  p=load(A/'preparation-r1/report.json',PH);b=load(A/'build-r1/build.json',BH)
  need(all(j['passed']for j in(prior,old,p,b)),'Passed inherited/current source and build')
  for j in(prior,old,p,b,load(A/'build-r1/pins.json')):
   for key in('files','sources'):
    for q,h in j.get(key,{}).items():pin(q,h)
  directory=A/'preparation-r1';builddir=A/'build-r1'
  eq(b['preparation_sha256'],PH,'Actual current compiler source identity');eq(Path(b['preparation']).resolve(),directory.resolve(),'Exact compiler preparation path')
  eq([b[k]for k in('roots','sequences','phases','record_bytes','pages','external_pages','combined_pages','snapshot_bytes')],[6,1,6,356992,43,21,64,266964],'Finite shared six-root schedule and frozen geometry')
  need(all(c['exit_code']==0 for c in b['commands']),'Actual clean configure/compiler/linker stages')
  for key in('original_executed','trace_executed','trace_admitted','source_after_seed','predicted_counts_supplied_to_execution','provider_preinvoked','sequence_reseeding'):
   need(p[key]is False,'Unexecuted BEFORE-only finite domain '+key)
  need(p['initializer_credit']==0 and p['FS_hooks']==72 and p['FS_event_bytes']==1224 and p['snapshot_count_bound']==384 and p['FS_event_bound']==2048,'Inherited observer bounds; no credit')
  W=mod(R/'tools/m4-tree-review/review_widget_prelaunch.py','font_widget_helpers')
  C=mod(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','font_x86_coff')
  F=mod(R/'tools/m4-fs-source/observer_attribution.py','font_fs_builder')
  PE=mod(R/'tools/analysis/pe.py','font_pe')
  game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  cp=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes());crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
  worker=PE.PEImage(pin(b['worker'],b['worker_sha256']).read_bytes())
  def physical(image,va,n):
   off,_=image.rva_range(va-image.image_base,n);return image.data[off:off+n]
  eq((worker.machine,worker.image_base),(0x14c,0x18000000),'Actual fixed-base x86 worker')
  pe=struct.unpack_from('<I',worker.data,60)[0];size=struct.unpack_from('<I',worker.data,pe+24+56)[0]
  need(worker.image_base+size<0x20000000,'Complete worker BSS/code stays below guest stack')
  contract=load(directory/'normal-contracts.json');previous=load(OLD/'normal-contracts.json')
  eq(contract['roots'][:5],previous['roots'],'Same five genuine widget relative order')
  eq(contract['roots'][5],dict(root=0x479590,slot=0x5e00cc,callback=0x4795d0,registration_CALL_pc=0x4795c5,registration_return_PC=0x4795ca,callback_executed=False),'Source-derived sixth registration identity')
  for row in contract['roots']:eq(struct.unpack('<I',physical(game,row['slot'],4))[0],row['root'],'All6 exact physical initializer table cells')
  rows=contract['instructions'];eq(rows[:1081],previous['instructions'],'Every prior source instruction descriptor retained');eq(len(rows),1093,'1081 inherited +12 new instructions')
  eq(sum(r['width']for r in rows),3391,'Whole1093 source rows/3391 physical bytes')
  for row in rows: eq(physical(game,row['pc'],row['width']),bytes.fromhex(row['bytes_hex']),'All whole physical game source rows')
  newrows=rows[1081:];need(len(newrows)==12 and sum(r['width']for r in newrows)==41 and all('fs:'not in r['operands']for r in newrows),'Exactly41 source bytes, no new FS patch')
  newgraph=load(directory/'new-game-graphs.json');eq(set(map(int,newgraph)),{0x479590,0x4795a0},'Exactly new root and direct helper graphs')
  object_=contract['new_font_object'];eq(object_,dict(base=0x608628,extent=0x4b0,constructor=0x40e840,constructor_CALL_pc=0x4795ab,arguments=[0,0,0],source_vptr=0x5bc598,source_vptr_store_PC=0x40e880,virtual_CALL_pc=0x5a0669,slot_offset=0x8c,physical_target=0x5a0680),'Finite constructor/vptr interface')
  eq(struct.unpack('<I',physical(game,0x5bc598+0x8c,4))[0],0x5a0680,'Exact dominating constructor vptr target readonly slot')
  by={r['pc']:r for r in rows}
  eq(bytes.fromhex(by[0x40e880]['bytes_hex']),bytes.fromhex('c70698c55b00'),'Exact literal derived vptr store through source ESI')
  eq(bytes.fromhex(by[0x5a0669]['bytes_hex']),bytes.fromhex('ff908c000000'),'Exact source virtual CALL slot')
  eq(struct.unpack_from('<i',bytes.fromhex(by[0x4795ab]['bytes_hex']),1)[0]+0x4795b0,0x40e840,'Exact constructor CALL target')
  eq(struct.unpack_from('<i',bytes.fromhex(by[0x4795c5]['bytes_hex']),1)[0]+0x4795ca,0x5ac140,'Exact register wrapper CALL')
  eq(contract['normal_patch_spans'],previous['normal_patch_spans'],'All81 observer patch identities unchanged')
  for i,x in enumerate(contract['normal_patch_spans']):
   for y in contract['normal_patch_spans'][i+1:]:need(x['PC']+x['size']<=y['PC']or y['PC']+y['size']<=x['PC'],'All active patches remain disjoint')
   if x['raw']is not None:
    image=cp if x['PC']>=0x78100000 else crt if x['PC']>=0x78000000 else game
    eq(physical(image,x['PC'],x['size']),bytes.fromhex(x['raw']),'Every whole physical patched span')
  before=W.sparse(pin(OLD/'pages.bin',old['pack_sha256']).read_bytes());after=W.sparse(pin(directory/'pages.bin',p['pack_sha256']).read_bytes())
  eq(list(before),list(after),'Same ordered159 sparse pages and geometry');eq(len(after),159,'Finite complete pack inventory')
  overlay=load(directory/'new-source-overlay.json');expected={r['pc']+i:(byte,r['pc'])for r in newrows for i,byte in enumerate(bytes.fromhex(r['bytes_hex']))}
  for page,(rights,blob)in after.items():
   eq(rights,before[page][0],'Every physical permission tag preserved')
   for i,(a,z)in enumerate(zip(before[page][1],blob)):
    if a==z:continue
    va=page+i;need(va in expected and a==0xcc and z==expected[va][0] and rights==1,'Only exact new physical instruction replaces old RX sparse padding')
    pack_changes.append(dict(address=va,old=a,new=z,source_PC=expected[va][1]))
  eq(sorted(pack_changes,key=lambda x:x['address']),sorted(overlay,key=lambda x:x['address']),'Entire exact41-byte sparse difference list')
  eq(len(pack_changes),41,'All and only41 new literal bytes in whole pack')
  eq(p['source_spans'][:-12],old['source_spans'],'All inherited source spans preserved')
  need({(r['pc'],r['size'])for r in p['source_spans'][-12:]}=={(r['pc'],r['width'])for r in newrows},'Whole exact new source spans')
  # Every prepared compiler input except schedule/spec is byte-identical.
  differences=[]
  for q in OLD.iterdir():
   if not q.is_file()or q.name in('report.json','pins.json'):continue
   new=directory/q.name;need(new.is_file(),'Complete prior source input inventory')
   if pin(q).read_bytes()!=pin(new).read_bytes():differences.append(q.name)
  eq(sorted(differences),['normal-contracts.json','pages.bin','protocol.hpp','reference.cpp','spec.hpp'],'Exact finite additive input differences only')
  eq(text(OLD/'reference.cpp').replace('Five genuine widget initializer endpoints captured','Six genuine widget/font initializer endpoints captured'),text(directory/'reference.cpp'),'Entire real execution/observer/cleanup program unchanged except terminal message')
  eq(text(OLD/'protocol.hpp').replace('sequences=1, roots=5','sequences=1, roots=6'),text(directory/'protocol.hpp'),'Only protocol root count, record geometry unchanged')
  spec=text(directory/'spec.hpp');oldspec=text(OLD/'spec.hpp')
  for field in('entries','table_slots'):
   m=re.search(r'inline constexpr std::array<std::uint32_t,6> '+field+r'\{([^}]+)\};',spec);need(m,'Exact current compiled six-root array')
   values=[int(z,0)for z in m[1].split(',')];eq(values,[r['root'if field=='entries'else'slot']for r in contract['roots']],'Compiler exact selected sequence')
  broker=text(directory/'original_broker.hpp');m=re.search(r'inline constexpr std::array<std::uint32_t,(\d+)> bases\{([^}]+)\};',broker);bases=[int(z,16)for z in m[2].split(',')]
  need(len(bases)==35 and len(set(bases))==35 and all(page&~65535 in bases for page in after),'Whole159page reservation coverage unchanged')
  eq(contract['whole_pages'],previous['whole_pages'],'Every64 observed source page retained');eq(p['observed_pages'],old['observed_pages'],'Exact immutable43 ordinary page ABI')
  eq(p['external_pages'],old['external_pages'],'Exact21 external pages');need(not contract['zero_font_registry_domain']['value_supplied_to_execution']and contract['zero_font_registry_domain']['actual_value_required_by_later_validation'],'Font-zero condition observed by later validator, never seeded')
  need('r->tag.status=execute();'in text(directory/'reference.cpp')and 'mixed_input=mixed_after;'in text(directory/'reference.cpp'),'Actual chronological execution within same worker, no perphase reset')
  release=builddir/'build-x86/mw34_joint_startup124_original.dir/Release';oldrelease=R/'reports/m4-widget-original/build-r6/build-x86/mw34_joint_startup124_original.dir/Release'
  for filename in('widget_observer_x86.obj','fs_observer_x86.obj','reference_x86.obj'):
   a=pin(oldrelease/filename).read_bytes();z=pin(release/filename).read_bytes();sa,aa=C.coff(a);sz,zz=C.coff(z)
   eq(sa,sz,'Complete assembler symbol identities/values/sections equal');eq(set(aa),set(zz),'Whole assembler section inventory')
   for section in (1,2):eq(aa[section],zz[section],'Every actual code/data/relocation byte conserved')
   old_debug=aa[3]['bytes'];new_debug=zz[3]['bytes'];old_name=str((oldrelease/filename).resolve()).encode();new_name=str((release/filename).resolve()).encode()
   need(aa[3]['flags']==zz[3]['flags']==0x42100040 and not aa[3]['relocations']and not zz[3]['relocations'],'Exact nonexecutable CodeView section')
   need(struct.unpack_from('<3I',old_debug)==(4,0xf1,len(old_debug)-12-((-struct.unpack_from('<I',old_debug,8)[0])%4)),'Whole CodeView symbols subsection geometry')
   record_length,kind=struct.unpack_from('<2H',old_debug,12);need(kind==0x1101 and struct.unpack_from('<I',old_debug,16)[0]==0 and old_debug[20:20+len(old_name)+1]==old_name+b'\0','Typed CodeView S_OBJNAME actual compiler object path')
   need(record_length==2+4+len(old_name)+1 and old_debug.count(old_name+b'\0')==1,'Entire exact S_OBJNAME record')
   delta=len(new_name)-len(old_name);expected=bytearray(old_debug.replace(old_name+b'\0',new_name+b'\0',1));struct.pack_into('<I',expected,8,struct.unpack_from('<I',old_debug,8)[0]+delta);struct.pack_into('<H',expected,12,record_length+delta)
   eq(bytes(expected),new_debug,'Entire debug section differs only actual object pathname and both typed record lengths')
   compiled_relations.append(dict(object=filename,prior_sha256=sha(oldrelease/filename),current_sha256=sha(release/filename),all_symbols_code_data_relocations_equal=True,CodeView_object_path_before=old_name.decode(),CodeView_object_path_after=new_name.decode(),whole_debug_section_relation=True,raw_COOff_headers_claim_equal=False))
  symbols,sections=C.coff(pin(release/'widget_observer_x86.obj').read_bytes());resolved={}
  for api,label in enumerate(('stock','delete','create')):
   for side,suffix in enumerate(('entry','return')):
    name_='_widget_'+label+'_'+suffix;definition=next(r for r in symbols.values()if r['name']==name_ and r['section']>0);sec=sections[definition['section']]
    raw,rel=W.expected_widget(api,side);eq(sec['bytes'][definition['value']:definition['value']+len(raw)],raw,'Entire independentGDI wrapper byte derivation')
    eq([(r['offset']-definition['value'],r['symbol']['name'],r['type'])for r in sec['relocations']if definition['value']<=r['offset']<definition['value']+len(raw)],rel,'All GDI physical relocation identities')
    row=C.linked_function(worker,symbols,sections,name_);eq(row['bytes'],len(raw),'Whole linked wrapper extent')
    for z in row['relocations']:
     value=z['actual_symbol_address'];need(z['symbol']not in resolved or resolved[z['symbol']]==value,'One actual shared wrapper target per symbol');resolved[z['symbol']]=value
    linked.append(row)
  fs=load(directory/'fs-hook-bindings.json');eq(fs,load(OLD/'fs-hook-bindings.json'),'All72FS source sites unchanged')
  symbols,sections=C.coff(pin(release/'fs_observer_x86.obj').read_bytes())
  for row in fs:
   name_='_'+row['declared_observer'];d=next(z for z in symbols.values()if z['name']==name_ and z['section']>0);sec=sections[d['section']]
   raw,rel,_=F.expected_function(row['PC'],row['kind'],bytes.fromhex(row['raw_bytes']));eq(sec['bytes'][d['value']:d['value']+len(raw)],raw,'Entire independent72FS wrapper bytes')
   eq([(z['offset']-d['value'],z['symbol']['name'],z['type'])for z in sec['relocations']if d['value']<=z['offset']<d['value']+len(raw)],rel,'All physical FS relocation identities')
   function=C.linked_function(worker,symbols,sections,name_);eq(function['bytes'],len(raw),'Whole actualFS wrapper extent');linked.append(function)
  symbols,sections=C.coff(pin(release/'reference.obj').read_bytes());observer=C.linked_function(worker,symbols,sections,'_widget_observe');eq(observer['address'],resolved['_widget_observe'],'All six GDI wrappers call actual reviewed observer');linked.append(observer)
  for api,(pc,raw)in enumerate(W.GDI):eq(struct.unpack('<I',physical(worker,resolved['_widget_continues']+api*4,4))[0],pc+len(raw),'Actual exact GDI continuation initializer')
  compiletext=text(builddir/'compile.log');need('/MACHINE:X86'in compiletext and '/W4 /WX'in compiletext and '0 Warning(s)'in compiletext and '0 Error(s)'in compiletext,'Current strict clean x86 compilation')
  tlogs=list(release.rglob('CL.read.1.tlog'));eq(len(tlogs),1,'One compiler actual read log');consumed=set()
  for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
   q=line.strip().lstrip('^')
   if q and Path(q).is_absolute()and Path(q).is_file():consumed.add(pin(q))
  for suffix in('spec.hpp','protocol.hpp','original_broker.hpp','widget_observer.hpp'):need((directory/suffix).resolve()in consumed,'Actual current forced/compiler header '+suffix)
  linkfiles=list(release.rglob('link.command.1.tlog'));eq(len(linkfiles),1,'Actual one final link command');linktext=pin(linkfiles[0]).read_text(encoding='utf-16').upper()
  need(all(n.upper()in linktext for n in('widget_observer_x86.obj','fs_observer_x86.obj','reference_x86.obj','reference.obj')),'All reviewed objects actually linked')
  controller=text(R/'tools/m4-font479590-original/run.py');need("q['files'].get(str(build.resolve()))!=digest"in controller and "q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']"in controller,'Firstwriter directbinds exact independent review/build/worker')
  pin(R/'tools/m4-font479590-original/prepare.py');pin(R/'tools/m4-font479590-original/validate_v2.py');pin(R/'tools/m4-pipeline/stages.py');pin(__file__);pin(sys.executable)
  counts.update(physical_game_rows=1093,physical_game_bytes=3391,new_game_rows=12,new_game_bytes=41,whole_sparse_pages=159,reserved_bases=35,source_pages=64,actual_compiler_inputs=len(consumed),linked_GDI_functions=6,linked_FS_functions=72,linked_CPP_observers=1)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,data in(('compiled-observers.json',linked),('whole-assembler-object-relations.json',compiled_relations),('exact-source-overlay.json',pack_changes)):
   q=out/filename;q.write_text(json.dumps(data,indent=2)+'\n');pin(q)
  report=dict(passed=passed,prelaunch_justified=passed,preparation_sha256=PH,build_sha256=BH,counts=dict(counts),worker_launched=False,archive_reader_opened=False,source_AFTER_seed=False,source_callback_execution=False,initializer_credit=0,
   scope='Independent first-writer admission of measured five-widget relative order followed by479590. Entire exact41-byte physical addition, unchanged source inputs/permissions/observers and current whole linked wrappers/compiler dependencies are authenticated. This relative sequence is not whole original startup order. Zero font registry, new actual GDI values/handles/selector/lifetimes/root effects and all source/virtual semantics require fresh observed validators and source comparison. No registered shutdown callback, failure unwind, caller cleanup conservation or native initializer credit.',files=PINS)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),files=len(PINS),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
