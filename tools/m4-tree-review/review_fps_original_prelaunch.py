"""Independent first-writer review of the real nonnull FPS formatter probe."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];A=R/'reports/m4-fps-original';OLD=R/'reports/m4-font479590-original/preparation-r1'
PH='7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1'
BH='21d9da208c51fd07341ab197ba06992b6e0d99fd58ff00cc3f7834cce0b621d2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert re.fullmatch('fps-original-prelaunch-r[1-9][0-9]*',name)and not out.exists();out.mkdir();pins={};counts=Counter();links=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip','.iso');v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p,h=None):return pin(p,h).read_bytes()
 def text(p):return pin(p).read_text()
 def module(p,name):
  s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  prior=read(R/'reports/m4-tree-review/font479590-prelaunch-r2/report.json','f6a38a04a81fbbf9a185d9a38ed20d5ac50f83baf4a411c651802d4834a32423')
  old=read(OLD/'report.json','56dab048c049f8cf634c494ed894a8444bba8c50da0d4dc99c7a22cfeab50ab9');prep=read(A/'preparation-r1/report.json',PH);build=read(A/'build-r1/build.json',BH)
  for j in(prior,old,prep,build,read(A/'build-r1/pins.json')):
   assert j.get('passed',True)
   for k in('files','sources'):
    for p,h in j.get(k,{}).items():pin(p,h)
  folder=A/'preparation-r1';bf=A/'build-r1';release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
  assert build['preparation_sha256']==PH and Path(build['preparation']).resolve()==folder.resolve()
  assert [build[k]for k in('roots','sequences','phases','record_bytes','pages','external_pages','combined_pages','snapshot_bytes')]==[7,1,7,356992,43,21,64,266964]
  assert all(c['exit_code']==0 for c in build['commands'])and prep['original_roots']==7 and prep['FS_hooks']==75 and prep['fps_snapshot_bytes']==529700
  assert all(prep[k]is False for k in('original_executed','trace_executed','trace_admitted','source_after_seed','provider_preinvoked','predicted_counts_supplied_to_execution','sequence_reseeding'))and prep['initializer_credit']==0
  W=module(R/'tools/m4-tree-review/review_widget_prelaunch.py','fps_widget');C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','fps_coff');F=module(R/'tools/m4-fs-source/observer_attribution.py','fps_fs');P=module(R/'tools/analysis/pe.py','fps_pe')
  game=P.PEImage(blob(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  crt=P.PEImage(blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'));cp=P.PEImage(blob(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'));worker=P.PEImage(blob(build['worker'],build['worker_sha256']))
  def physical(image,va,size):
   off,_=image.rva_range(va-image.image_base,size);return image.data[off:off+size]
  assert(worker.machine,worker.image_base)==(0x14c,0x18000000)
  nt=struct.unpack_from('<I',worker.data,60)[0];assert worker.image_base+struct.unpack_from('<I',worker.data,nt+24+56)[0]<0x20000000
  contracts=read(folder/'normal-contracts.json');oldcontracts=read(OLD/'normal-contracts.json')
  assert contracts['roots'][:6]==oldcontracts['roots'] and contracts['roots'][6]==dict(root=0x40f000,slot=0x5e0050,callback=0x40f030,push_PC=0x40f020,CALL_pc=0x40f025,return_PC=0x40f02a,callback_executed=False)
  for row in contracts['roots']:assert struct.unpack('<I',physical(game,row['slot'],4))[0]==row['root']
  rows=contracts['instructions'];assert rows[:1093]==oldcontracts['instructions']and len(rows)==1147 and sum(r['width']for r in rows)==3596
  for row in rows:assert physical(game,row['pc'],row['width'])==bytes.fromhex(row['bytes_hex']);counts['whole_physical_source_rows']+=1
  newrows=rows[1093:];assert len(newrows)==54 and sum(r['width']for r in newrows)==205
  fps=contracts['fps'];assert(fps['root'],fps['slot'],fps['object'],fps['extent'],fps['format'],fps['IAT'],fps['physical_target'],fps['CALL_pc'],fps['return_PC'],fps['argc'],fps['caller_cleanup'])==(0x40f000,0x5e0050,0x5fc378,0x4bc,0x5e1590,0x5bb53c,0x780230dd,0x5a2f68,0x5a2f6e,3,12)
  assert physical(game,0x5e1590,4)==b'fps\0' and physical(game,0x5a2f6e,6)==bytes.fromhex('8b8638020000') and physical(game,0x5a2f68,6)==bytes.fromhex('ff153cb55b00')
  assert physical(game,0x5a2f74,3)==bytes.fromhex('83c40c')and physical(game,0x5cfd48,4)==struct.pack('<I',0x409b30)and physical(game,0x409b30,1)==b'\xc3'
  assert fps['new_virtual']==dict(CALL_pc=0x5a2f86,source_vptr=0x5cfd28,source_vptr_store_PC=0x5a0114,slot=0x5cfd48,target=0x409b30,measured=False)
  # The PE export table proves the physical provider selected by the worker's
  # GetProcAddress and loaded-module base guard; no response is predicted.
  exports=crt.exports();match=[r for r in exports if r.get('name')=='vsprintf'];assert len(match)==1
  assert match[0]['rva']+crt.image_base==0x780230dd
  before=W.sparse(blob(OLD/'pages.bin',old['pack_sha256']));after=W.sparse(blob(folder/'pages.bin',prep['pack_sha256']));assert list(before)==list(after)and len(after)==159
  expected={r['pc']+i:byte for r in newrows for i,byte in enumerate(bytes.fromhex(r['bytes_hex']))};delta=[]
  for page,(rights,data)in after.items():
   assert rights==before[page][0]
   for i,(a,b)in enumerate(zip(before[page][1],data)):
    if a!=b:assert page+i in expected and a==0xcc and b==expected[page+i]and rights==1;delta.append(page+i)
  assert len(delta)==205
  assert prep['observed_pages']==old['observed_pages']and prep['external_pages']==old['external_pages']and contracts['whole_pages']==oldcontracts['whole_pages']
  assert contracts['normal_patch_spans'][:len(oldcontracts['normal_patch_spans'])]==oldcontracts['normal_patch_spans']
  for i,a in enumerate(contracts['normal_patch_spans']):
   for b in contracts['normal_patch_spans'][i+1:]:assert a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC']
   if a['raw']is not None:
    image=cp if a['PC']>=0x78100000 else crt if a['PC']>=0x78000000 else game;assert physical(image,a['PC'],a['size'])==bytes.fromhex(a['raw'])
  fs=read(folder/'fs-hook-bindings.json');oldfs=read(OLD/'fs-hook-bindings.json');assert fs[:72]==oldfs and len(fs)==75 and [r['PC']for r in fs[72:]]==[0x40f157,0x40f15e,0x40f1e0]
  for filename in('original_broker.hpp','reference_x86.asm','widget_observer.hpp','widget_observer_x86.asm','null_broker_x86.asm','preserve_x86.asm','vtable_x86.asm','lockit_observer_x86.asm'):
   assert blob(folder/filename)==blob(OLD/filename),filename
  # Derive the two whole FPS assembly wrappers from the independently encoded
  # identical GDI CPU/flags/FP/segment boundary with explicit FPS-only changes.
  symbols,sections=C.coff(blob(release/'fps_observer_x86.obj'));targets={}
  for side,label in enumerate(('_fps_entry','_fps_return')):
   raw,rel=W.expected_widget(0,side);raw=bytearray(raw)
   if side:
    pcfields=[o for o,n,t in rel if n=='_widget_cpu'and struct.unpack_from('<I',raw,o)[0]==36];assert len(pcfields)==1;struct.pack_into('<I',raw,pcfields[0]+4,0x5a2f6e)
    assert raw[-12:-6]==W.GDI[0][1];raw[-12:-6]=bytes.fromhex('8b8638020000')
   rel=[(o,n.replace('_widget_targets','_fps_target').replace('_widget_continues','_fps_continue').replace('_widget_','_fps_'),t)for o,n,t in rel]
   d=next(s for s in symbols.values()if s['name']==label and s['section']>0);sec=sections[d['section']]
   assert sec['bytes'][d['value']:d['value']+len(raw)]==raw
   assert[(r['offset']-d['value'],r['symbol']['name'],r['type'])for r in sec['relocations']if d['value']<=r['offset']<d['value']+len(raw)]==rel
   row=C.linked_function(worker,symbols,sections,label);assert row['bytes']==len(raw)
   for r in row['relocations']:
    v=r['actual_symbol_address'];assert r['symbol']not in targets or targets[r['symbol']]==v;targets[r['symbol']]=v
   links.append(row);counts['whole_FPS_observer_functions']+=1
  assert physical(worker,targets['_fps_continue'],4)==struct.pack('<I',0x5a2f74)
  symbols,sections=C.coff(blob(release/'fs_observer_x86.obj'))
  for row in fs:
   label='_'+row['declared_observer'];d=next(s for s in symbols.values()if s['name']==label and s['section']>0);sec=sections[d['section']]
   raw,rel,_=F.expected_function(row['PC'],row['kind'],bytes.fromhex(row['raw_bytes']));assert sec['bytes'][d['value']:d['value']+len(raw)]==raw
   assert[(r['offset']-d['value'],r['symbol']['name'],r['type'])for r in sec['relocations']if d['value']<=r['offset']<d['value']+len(raw)]==rel
   linked=C.linked_function(worker,symbols,sections,label);assert linked['bytes']==len(raw);links.append(linked);counts['whole_FS_observer_functions']+=1
  symbols,sections=C.coff(blob(release/'widget_observer_x86.obj'))
  for api,label in enumerate(('stock','delete','create')):
   for side,suffix in enumerate(('entry','return')):
    name_='_widget_'+label+'_'+suffix;d=next(s for s in symbols.values()if s['name']==name_ and s['section']>0);sec=sections[d['section']];raw,rel=W.expected_widget(api,side)
    assert sec['bytes'][d['value']:d['value']+len(raw)]==raw
    assert[(r['offset']-d['value'],r['symbol']['name'],r['type'])for r in sec['relocations']if d['value']<=r['offset']<d['value']+len(raw)]==rel
    linked=C.linked_function(worker,symbols,sections,name_);assert linked['bytes']==len(raw);links.append(linked);counts['whole_GDI_observer_functions']+=1
  symbols,sections=C.coff(blob(release/'reference.obj'));observer=C.linked_function(worker,symbols,sections,'_fps_observe');assert observer['address']==targets['_fps_observe'];links.append(observer)
  source=text(folder/'fps_observer.hpp');assert source==text(R/'tools/m4-fps-original/fps_observer.hpp')
  for line in('static_assert(sizeof(FpsSnapshot)==529700)','fps_cpu.esp<0x20001000','fps_cpu.esp+64>0x20002000','s.cpu.esp','e.cpu.esp+4!=s.cpu.esp','s.cpu.pc!=0x5a2f6e','f[0]!=0x5a2f6e','std::memcpy(s.destination','std::memcpy(s.format_input','std::memcpy(s.va_input','std::memcpy(s.CRT_pages','GetThreadSelectorEntry','s.header[13+i]=e.header[13+i]'):
   assert line in source,line
  ref=text(folder/'reference.cpp')
  for line in('fps_target=reinterpret_cast<unsigned>(GetProcAddress(crt,"vsprintf"))','require(fps_target==0x780230dd','*reinterpret_cast<unsigned*>(0x5bb53c)=fps_target','reinterpret_cast<unsigned>(&fps_entry)','reinterpret_cast<unsigned>(&fps_return)-0x5a2f73','FPS named import restored','ExactFPSreturn source restored','fps_count=0;fps_error=0','r->tag.status=execute();','mixed_input=mixed_after;','fps/identity.bin','fps_count*sizeof(FpsSnapshot)'):
   assert line in ref,line
  for field in('entries','table_slots'):
   match=re.search(r'inline constexpr std::array<std::uint32_t,7> '+field+r'\{([^}]+)\};',text(folder/'spec.hpp'));assert match
   assert[int(x,0)for x in match[1].split(',')]==[r['root'if field=='entries'else'slot']for r in contracts['roots']]
  assert text(folder/'protocol.hpp')==text(OLD/'protocol.hpp').replace('sequences=1, roots=6','sequences=1, roots=7')
  compilelog=text(bf/'compile.log');assert all(x in compilelog for x in('/MACHINE:X86','/W4 /WX','0 Warning(s)','0 Error(s)'))
  logfiles=list(release.rglob('CL.read.1.tlog'));assert len(logfiles)==1;consumed=set()
  for line in pin(logfiles[0]).read_text(encoding='utf-16').splitlines():
   q=line.strip().lstrip('^')
   if q and Path(q).is_absolute()and Path(q).is_file():consumed.add(pin(q))
  assert all((folder/q).resolve()in consumed for q in('spec.hpp','protocol.hpp','widget_observer.hpp','fps_observer.hpp'))
  linklog=list(release.rglob('link.command.1.tlog'));assert len(linklog)==1;linktext=pin(linklog[0]).read_text(encoding='utf-16').upper()
  assert all(q.upper()in linktext for q in('fps_observer_x86.obj','fs_observer_x86.obj','widget_observer_x86.obj','reference_x86.obj','reference.obj'))
  controller=text(R/'tools/m4-fps-original/run.py');assert "q['files'].get(str(build.resolve()))!=digest"in controller and "q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']"in controller
  pin(R/'tools/m4-fps-original/prepare.py');pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h,p
  counts.update(physical_source_bytes=3596,new_physical_rows=54,new_physical_bytes=205,whole_sparse_pages=159,source_pages=64,whole_CPP_FPS_observers=1,compiler_inputs=len(consumed))
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'whole-linked-observers.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  report=dict(passed=passed,prelaunch_justified=passed,preparation_sha256=PH,build_sha256=BH,counts=dict(counts),files=pins,worker_launched=False,archive_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,scope='First-writer admission of seven relative roots, true nonnull FPS vsprintf entry/return observations and whole caller-preserving wrappers; genuine formatter outputs/CRT byteflows/virtual source execution require fresh actual validation. Full startup order, native implementation and acceptance remain unclaimed.')
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
