"""Independent full131 original pack/source/whole compiled observer admission."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb'
BH='f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=Counter();links=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def raw(p,h=None):return pin(p,h).read_bytes()
 def read(p,h=None):return json.loads(raw(p,h))
 def module(p,name):
  spec=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def sparse(data):
  count=struct.unpack_from('<I',data,8)[0];assert len(data)==12+count*4104
  rows={struct.unpack_from('<I',data,12+i*4104)[0]:(struct.unpack_from('<I',data,16+i*4104)[0],data[20+i*4104:4116+i*4104])for i in range(count)};assert len(rows)==count;return rows
 try:
  folder=R/'reports/m4-startup131-original/preparation-r4';bf=R/'reports/m4-startup131-original/build-r3'
  p=read(folder/'report.json',PH);b=read(bf/'build.json',BH);assert p['passed']and b['passed']and b['preparation_sha256']==PH and Path(b['preparation'])==folder
  for j,key in ((p,'files'),(b,'sources')):
   for q,h in j[key].items():pin(q,h)
  assert (p['original_roots'],p['original_sequences'],p['original_phases'],p['callback_count'],p['record_bytes'],p['source_frame'])==(131,6,786,101,356992,0x20001800)
  for key in ('provider_preinvoked','predicted_values_supplied_to_execution','source_output_seed','original_executed','capture_reader_opened','initializer_credit'):assert not p[key],key
  oldfolder=R/'reports/m4-startup130-original/preparation-r2';mfcfolder=R/'reports/m4-mfc1168-connected-original/preparation-r3'
  old=read(oldfolder/'report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
  selected=p['selected_order'];assert selected==sorted(old['selected_order']+[dict(slot=0x5e0040,entry=0x5ae3e4)],key=lambda row:row['slot'])
  assert selected[13]==dict(slot=0x5e0040,entry=0x5ae3e4)and len({v['entry']for v in selected})==131
  PE=module(R/'tools/analysis/pe.py','original131_physical')
  game=PE.PEImage(raw(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  cp=PE.PEImage(raw(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'))
  def physical(image,a,n):o,_=image.rva_range(a-image.image_base,n);return image.data[o:o+n]
  pack=sparse(raw(folder/'pages.bin',p['pack_sha256']));prior=sparse(raw(oldfolder/'pages.bin',old['pack_sha256']));assert len(pack)==134 and len(prior)==132
  rows=read(R/'reports/m4-mfc1168-original/recovery-r2/game-graphs.json');new={r['pc']:r for g in rows.values()for r in g['instructions']};assert len(new)==25
  delta={r['pc']+i:v for r in new.values()for i,v in enumerate(bytes.fromhex(r['bytes']))}
  for page,(perm,bytes_)in prior.items():
   assert pack[page][0]==perm
   for i,(a,z)in enumerate(zip(bytes_,pack[page][1])):
    if a!=z:assert perm==1 and a==0xcc and delta.get(page+i)==z;counts['exact_literal_pack_delta_bytes']+=1
   counts['whole_inherited_pack_pages']+=1
  assert set(pack)-set(prior)=={0x5ae000,0x5f2000}
  assert pack[0x5f2000]==(2,physical(game,0x5f2000,4096))
  for row in p['source_spans']:
   image=cp if row['origin']else game;source=physical(image,row['pc'],row['size']);assert image.data[row['image_offset']:row['image_offset']+row['size']]==source
   for i,z in enumerate(source):assert pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==z
   counts['whole_physical_source_spans']+=1
  for row in selected:assert struct.unpack('<I',physical(game,row['slot'],4))[0]==row['entry']==struct.unpack_from('<I',pack[row['slot']&~4095][1],row['slot']&4095)[0];counts['physical_selected_pairs']+=1
  broker=pin(folder/'original_broker.hpp').read_text();bases=[int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')];assert all(page&~65535 in bases for page in pack)
  for file in ('preserve_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','original_broker.hpp','fs-hook-bindings.json'):
   assert pin(folder/file).read_text()==pin(oldfolder/file).read_text();counts['whole_unchanged_accepted_observers']+=1
  for file in ('reference_x86.asm','boundaries.asm','api_boundaries.asm'):assert pin(folder/file).read_text()==pin(mfcfolder/file).read_text();counts['whole_chronological_MFC_ASM_relations']+=1
  cpp=pin(folder/'reference.cpp').read_text();main_cpp=cpp[cpp.index('int main('):];obs=pin(folder/'connected_observer.hpp').read_text();prereq=pin(folder/'prerequisite_observer.hpp').read_text();contracts=read(folder/'contracts.json')
  assert contracts['all_provider_pages_carried_across_sequences']and contracts['coherent_true_root_TIB8192']and contracts['MFC_phase']==13 and contracts['callbacks']==101
  assert 'sequences=6, roots=131'in pin(folder/'protocol.hpp').read_text()
  assert main_cpp.count('if(page_permissions[i]==2)std::memcpy')==1 and 'if(phase){mixed_input=mixed_after;'in main_cpp
  assert main_cpp.index('mixed_input.pc=0x78004482')<main_cpp.index('for(unsigned phase=0;phase<entries.size();++phase)')
  mfc_before=main_cpp[main_cpp.index('if(mfc_phase){require(phase==13'):main_cpp.index('auto r=std::make_unique<Record>();')]
  assert mfc_before.index('remove_CRT_hooks();restore_registry_hooks();')<mfc_before.index('connected_named_identity();')<mfc_before.index('module_pages("BEFORE/MFC"')
  assert main_cpp.index('if(mfc_phase){named_IAT(true);connected_patch_sources(true);}')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('named_IAT(false);connected_patch_sources(false);')<main_cpp.index('}copy_pages(r->memory_after);')<main_cpp.index('reinstall_registry_hooks();install_CRT_hooks();')
  for t in ('module_pages("BEFORE/CRT"','module_pages("AFTER/MFC"','module_pages("AFTER/CRT"','connected_lock("BEFORE/CRT-codepage-lock")','connected_lock("AFTER/CRT-codepage-lock")','constructor_graph(phase_stem+"/BEFORE-MFC")','constructor_graph(phase_stem+"/AFTER-MFC")','if(phase<13)constructor_collect','constructor_collect(0xffffffffU,cboot)','mixed_teb_before_pages,8192','mixed_teb_after_pages,8192'):
   assert t in main_cpp,t
  assert 'binding.root<=entries[phase]'not in main_cpp
  assert main_cpp.count('std::find(entries.begin(),entries.begin()+phase+1,binding.root)!=entries.begin()+phase+1')==2
  assert 'Current producer ledger bound before any export'in main_cpp and main_cpp.index('Current producer ledger bound before any export')<main_cpp.index('producer-api-ledger.bin')
  assert 'Named actual owning IAT restore protection'in obs or 'Named actual owning IAT restore protection'.replace('restore protection','restore protection') in obs
  for t in ('initial_bytes','registry_initial_bytes[i],initial','constructor_live(heap,pointer)','capacity==allocation_occurrence->capacity','constructor_dump(stem+"/5F2000.bin"','static_cast<unsigned>(seen.size())','if(previous)require(prev==previous','dword(header+4)==previous'):
   assert t in prereq,t
  patches=contracts['active_new_code_patches'];assert len(patches)==5
  for row in patches:
   assert physical(game,row['PC'],row['size']).hex()==row['raw']
   for other in contracts['inherited_active_code_patches']:assert row['PC']+row['size']<=other['PC']or other['PC']+other['size']<=row['PC']
  C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','original131_coff');worker=PE.PEImage(raw(b['worker'],b['worker_sha256']));assert worker.machine==0x14c and worker.image_base==0x18000000
  release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
  for file in ('reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86'):
   sy,se=C.coff(raw(release/(file+'.obj')));indexes=[i for i,s in se.items()if s['flags']&0x20000000 and s['bytes']];assert len(indexes)==1
   fake={0:dict(name=file+' whole source',value=0,section=indexes[0],type=0x20,storage=2)};proof=C.linked_function(worker,fake,se,file+' whole source');links.append(dict(proof,family='whole-ASM',target=proof['address']));counts['whole_linked_ASM_sections']+=1;counts['whole_linked_ASM_bytes']+=proof['bytes']
  sy,se=C.coff(raw(release/'reference.obj'))
  names=['_main','_observe_boundary','_observe_named_API']+[s['name']for s in sy.values()if s['type']==0x20 and s['section']>0 and any(s['name'].startswith(a)for a in ('?constructor_collect@@','?constructor_graph@@'))]
  assert len(names)==5
  for n in names:proof=C.linked_function(worker,sy,se,n);links.append(dict(proof,family='CPP',target=proof['address']));counts['whole_linked_CPP_functions']+=1
  sy,se=C.coff(raw(release/'format_observer_x86.obj'))
  for label in ('strrchr','malloc','sprintf'):
   for kind in ('entry','return'):
    n='_format_'+kind+'_'+label;proof=C.linked_function(worker,sy,se,n);links.append(dict(proof,family='format',target=proof['address']));counts['whole_current_format_targets']+=1
  consumed=set();tlogs=list(release.rglob('CL.read.1.tlog'));assert len(tlogs)==1
  for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
   q=Path(line.strip().lstrip('^'))
   if q.is_absolute()and q.is_file():consumed.add(pin(q))
  assert all((folder/f).resolve()in consumed for f in('spec.hpp','protocol.hpp','connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','original_broker.hpp'))
  counts['actual_compiler_input_files']=len(consumed)
  log=pin(bf/'compile.log').read_text();assert '/MACHINE:X86'in log and '/W4 /WX'in log and '0 Warning(s)'in log and '0 Error(s)'in log
  pin(R/'tools/m4-startup131-original/run.py');pin(__file__);pin(sys.executable)
  for q,h in pins.items():assert sha(q)==h,q
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'compiled-observers.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  report=dict(passed=passed,scope='Independent current full131 original first-writer physical and source/observer review; actual six-sequence domains and full paired/source equality require execution',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),files=pins,worker_launched=False,capture_archive_reader_opened=False,initializer_credit=0)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),files=len(pins),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
