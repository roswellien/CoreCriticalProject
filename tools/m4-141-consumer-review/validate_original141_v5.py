"""Authenticate original141 observations while preserving all inherited138 checks."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
from collections import Counter
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-original141';CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
sys.path.insert(0,str(ROOT/'tools/m4-tree-original'));from full_tree_phase import observe as observe_tree
sys.path.insert(0,str(ROOT/'tools/m4-startup130-original'));from family_phase_v2 import observe as observe_family,cleanup as cleanup_family
sys.path.insert(0,str(ROOT/'tools/m4-141-consumer-review'));from mfc_phase141_v1 import observe as observe_mfc,constructor as observe_constructor
sys.path.insert(0,str(Path(__file__).resolve().parent));from widget_phase141_v1 import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES
from mfc_transition141_v1 import Transition
from named_loader141_v2 import prove as prove_named_loader
from constructor_supplement141_v4 import observe as observe_constructor_supplement
sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));from paired_exports import Export
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'));from paths_capture_storage import STORAGE_ROOT
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,digest,execution,preflight_path,preflight_digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;counts=Counter();paired_exports=[];export=None;transport=None
 def need(x,w):
  if not x:raise ValueError(w)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact pin '+str(p));need(str(p)not in files or files[str(p)]==v,'No conflicting pin');files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 try:
  need(build==ROOT/'reports/m4-original141/build-r1/build.json'and digest=='088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b','Exact current compiled original141 worker only')
  admission=read(pin(preflight_path,preflight_digest));need(admission['passed'] and admission.get('original141_validator_admitted') is True and admission['files'].get(str(build))==digest,'ROOT independent final compiled observer/validator admission required before reader')
  for dependency,identity in admission['files'].items():pin(dependency,identity)
  need(admission['files'].get(str(Path(__file__).resolve()))==sha(Path(__file__).resolve()),'Actual validator code belongs to exact ROOT admission')
  b=read(pin(build,digest));need(b['passed'],'Actual x86 build');
  for p,h in read(Path(build).parent/'pins.json')['files'].items():pin(p,h)
  prep=Path(b['preparation']);current=read(pin(prep/'report.json',b['preparation_sha256']));need(current['passed']and current['Record_bytes']==356992 and current['root_count']==141 and b['preparation_sha256']=='7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8','Exact actual compiled original141 ABI/order');p=read(pin(ROOT/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'));need(p['original_roots']==138 and p['record_bytes']==356992 and current['callback_count']==111 and current['phases']==846,'Retained original138 physical fixed/extra page schema plus exact additive141 geometry');p['files']={**p.get('files',{}),**current['files']};oldmeta=read(pin(ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b'));
  for key in ('genuine_DllMain_bootstrap_pages','Lockit_roots','Lockit_allocations'):p[key]=oldmeta[key]
  p['order']=read(prep/'selected-order.json');old125=read(ROOT/'reports/m4-tree-original/original125-preparation-r1/selected-order.json');need(len(p['order'])==141 and [p['order'][i]['entry']for i in(13,14,15,39)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40] and [r['entry']for r in p['order']if r['entry']not in(0x4103f0,0x410440,0x459b40,0x5ae3e4,0x4b64f0,0x4df610,0x4e0710,0x4e0810,0x4e1ca0,*WIDGET_ROOTS)]==[r['entry']for r in old125],'Exact accepted125 relative order plus current physical source additions')
  for q,h in p['files'].items():pin(q,h)
  e=Path(execution);run=read(e/'report.json');need(run['passed']and run['build_sha256']==digest,'Actual original141 execution');stage=read(e/'run/stage.json');need(stage['passed'],'Actual execution stage complete')
  readerpath=pin(ROOT/'tools/m4-crt-allocation-root/run_storage.py');spec=importlib.util.spec_from_file_location('lockit_original_direct_reader',readerpath);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);transport=Path(run['original_capture']).resolve();need(transport.is_relative_to(STORAGE_ROOT/'reports/m4-original141')and transport.name=='transport.json','Declared G original capture only');records=ds.DirectSet(transport,pin)
  try:
   need(records.data('COMPLETE.txt')==b'complete','Complete capture');header=records.data('header.bin');need(header[:8]==b'MW4J141O'and len(header)==32 and struct.unpack_from('<6I',header,8)==(1,6,141,846,43,356992),'Exact original header')
   provider=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes());bootstrap={a:records.data(f'lockit/post-DllMain/{a}-page.bin')for a in p['genuine_DllMain_bootstrap_pages']};need(all(len(r)==4096 for r in bootstrap.values()),'Complete post-DllMain pages')
   for a,raw in bootstrap.items():
    (out/f'post-DllMain-{a:08x}-page.bin').write_bytes(raw);pin(out/f'post-DllMain-{a:08x}-page.bin');need(records.data(f'lockit/restored/{a}-page.bin')==raw,'Whole authentic bootstrap restored after all sequences')
   need(struct.unpack_from('<7I',bootstrap[0x78145000],0x640)==(0xffffffff,0xffffffff,0,0,0,0x020007d0,2),'Genuine initialized state2/CS24 unheld same-worker bootstrap')
   tid=struct.unpack('<I',records.data('lockit/thread.bin'))[0];need(tid>0,'Actual source thread identity');imports=records.data('lockit/import-ledger.bin');need(len(imports)==7*20,'Seven exact owning provider import observations');physicalimports={provider.image_base+r['iat_rva']:dict(library=g['library'],**r)for g in provider.imports()for r in g['symbols']};targets={};import_rows=[]
   for k in range(7):
    cell,target,named,declared,owner=struct.unpack_from('<5I',imports,k*20);need(cell in physicalimports and target==named and declared and owner and struct.unpack_from('<I',bootstrap[0x78146000],cell&4095)[0]==target,'Actual original loaded named export and IAT identity');targets[cell]=target;import_rows.append(dict(cell=cell,target=target,symbol=physicalimports[cell]['name'],library=physicalimports[cell]['library'],declared_base=declared,actual_owner_base=owner))
    for base in set((declared,owner)):
     actualpath=records.data(f'lockit/modules/{base}/path.bin').decode('utf-16-le').rstrip('\0');image=records.data(f'lockit/modules/{base}/image.bin');disk=Path(re.sub(r'(?i)system32',lambda m:'SysWOW64',actualpath))if actualpath.lower().startswith('c:\\windows\\system32\\')else Path(actualpath);need(pin(disk).read_bytes()==image,'Actual32 owning/forwarder module image');need(PEImage(image).machine==0x14c,'Actual x86 provider module machine')
   (out/'loaded-imports.json').write_text(json.dumps(import_rows,indent=2)+'\n');pin(out/'loaded-imports.json');order=p['order'];roots={r['entry']:r for r in p['Lockit_roots']};allocspec=p['Lockit_allocations'];pages=p['observed_pages'];pageindex={a:n for n,a in enumerate(pages)}
   def page(data,a,after=False):return data[(178404 if after else 2276)+pageindex[a]*4096:(178404 if after else 2276)+(pageindex[a]+1)*4096]
   callback_roots=read(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json')+read(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json')+read(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json')+read(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json')+read(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json')+read(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json')['roots']+list(roots.values());callback_roots.sort(key=lambda r:r['slot']);callback_byentry={r['entry']:r['registration']['callback']for r in callback_roots};callback_byentry[0x4b7f70]=0x4b7fa0
   format_roots=read(ROOT/'reports/m4-formatting-frontier/recovery-r1/roots.json')+read(ROOT/'reports/m4-mixed-format-original/recovery-r1/roots.json');format_byentry={}
   game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes())
   for r in format_roots:
    callback_byentry[r['entry']]=r['registration']['callback'];f=bytes.fromhex(r['filename_bytes_hex'])if'filename_bytes_hex'in r else r['filename_text'].encode()+b'\0';off,_=game.rva_range(r['filename']-game.image_base,len(f));need(game.data[off:off+len(f)]==f,'Physical genuine filename input');r['filename_bytes']=f;format_byentry[r['entry']]=r
   need(len(callback_byentry)==101,'All101 inherited recovered callback source domains')
   widget_plan=read(ROOT/'reports/m4-fps-original/preparation-r1/normal-contracts.json')
   for row in widget_plan['roots']:need(row['root']not in callback_byentry,'Distinct new literal callback');callback_byentry[row['root']]=row['callback']
   need(len(callback_byentry)==108 and tuple(order[i]['entry']for i in WIDGET_PHASES)==WIDGET_ROOTS,'All108 inherited literal callbacks and current sorted seven-root chronology')
   for row in read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json')['roots']:
    need(row['entry']not in callback_byentry and row['entry']in(0x4103f0,0x410440,0x459b40),'Distinct three physically recovered constructor callbacks');callback_byentry[row['entry']]=row['callback']
   need(len(callback_byentry)==111,'All111 physical source callbacks')
   prelaunch=read(pin(preflight_path,preflight_digest));need(prelaunch['passed']and prelaunch['original141_validator_admitted']is True and prelaunch['files'].get(str(build))==digest and prelaunch['files'].get(str(Path(b['worker']).resolve()))==b['worker_sha256'],'Independent current final compiled worker observer attribution');need(run['preflight_sha256']==preflight_digest,'Actual execution bound current independent preflight')
   for file_,hash_ in prelaunch['files'].items():pin(file_,hash_)
   obs=read(ROOT/'reports/m4-original141/root-compiled-review-r1/physical-links.json');resolutions={}
   for row in obs:
    for rel in row['relocations']:
     if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
      symbol,value=rel['symbol'],rel['actual_symbol_address'];need(symbol not in resolutions or resolutions[symbol]==value,'Unique actual linked symbol identity');resolutions[symbol]=value
   format_shims={symbol:resolutions[symbol]for symbol in('_format_entry_strrchr','_format_entry_malloc','_format_entry_sprintf')};format_section=next(row for row in obs if row['symbol']=='format_observer_x86 whole source');need(all(format_section['address']<=v<format_section['address']+format_section['bytes']for v in format_shims.values()),'All three actual entry targets lie inside the wholly attributed current format observer');format_cells={0x5bb5a8:format_shims['_format_entry_strrchr'],0x5bb664:format_shims['_format_entry_malloc'],0x5bb658:format_shims['_format_entry_sprintf']};need(words_format_targets:=struct.unpack('<3I',records.data('formatting/import-targets.bin'))==(0x780264a9,0x780012b3,0x78022b9a),'Exact actual named formatting CRT targets')
   family_artifacts={k:[]for k in('cdecl','format_owners','mixed_owners','mixed_FS','mixed_CP','CRT_pages','cosine')};format_IAT_rows=[]
   geometry=[];snapshot_rows=[];allowners=[];mfc_artifacts=[];constructor_artifacts=[]
   contract=read(prep/'contracts.json');compiled_spec=pin(prep/'spec.hpp').read_text();match=re.search(r'std::array<unsigned,69> widget_whole_pages\{([^}]+)\};',compiled_spec);need(match is not None,'Current physically compiled source page order');whole=[int(x.strip(),16)for x in match[1].split(',')];need(whole[:43]==pages and len(set(whole))==69 and set(whole[43:])==set(p['extra_whole_source_pages']),'Source69 order/count agreement')
   fs_bindings={row['PC']:row for row in read(prep/'fs-hook-bindings.json')};need(len(fs_bindings)==108,'Every current exact source FS opcode binding')
   identity=struct.unpack('<15I',records.data('widget/identity.bin'));widget_targets=[];widget_section=next(row for row in obs if row['symbol']=='widget_observer_x86 whole source')
   for i,cell in enumerate((0x5bb070,0x5bb074,0x5bb068)):
    field,target,shim,declared,owner=identity[i*5:(i+1)*5];need(field==cell and target and declared and owner and widget_section['address']<=shim<widget_section['address']+widget_section['bytes'],'Actual GDI named loader target, module and wholly attributed observer range');widget_targets.append(target)
   fps_identity=struct.unpack('<4I',records.data('fps/identity.bin'));need(fps_identity==(0x5bb53c,0x780230dd,resolutions['_fps_entry'],0x78000000),'Actual staged named vsprintf and exact linked FPS entry target')
   declaration=read(pin(ROOT/'reports/m4-original141/transition-preparation-r1/patch-declarations.json'))
   shim_addresses=[resolutions['_registry_API_'+str(i)]for i in range(8)]
   crt_image=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
   patches,named_loader=prove_named_loader(records,PEImage,pin,shim_addresses,crt_image,declaration);transition=Transition(patches)
   target=out/'current-named-CRT-inputs.json';target.write_text(json.dumps(named_loader,indent=2)+'\n');pin(target)
   widget=Observer(records,contract,whole,pages,fs_bindings,counts,widget_targets,fps_identity[1],transition)
   for seq,(repeat,cw,top)in enumerate(CASES):
    carried=[];owners=[];formats={};mixed={};widget.begin_sequence(seq)
    for phase,item in enumerate(order):
     entry=item['entry'];data=records.data(f'phase/{seq}/{phase}.bin');need(len(data)==356992 and struct.unpack_from('<9I',data)==(seq,repeat,phase,item['slot'],entry,cw,top,0,1),'Authentic successful141 phase tag and host restore');need(struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80,'Actual caller rootRET machine boundary');counts['phases']+=1;widget.phase(data,seq,phase,entry)
     if entry in callback_byentry:carried.append(callback_byentry[entry])
     begin,nxt,capacity,mode=struct.unpack_from('<4I',data,356464);need(begin and nxt-begin==len(carried)*4<=capacity<=512 and mode==1 and struct.unpack_from('<'+str(len(carried))+'I',data,356480)==tuple(carried),'Exact source registry callbacks, capacity, original mode1')
     count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/lockit-count.bin'))[0];snapshots=records.data(f'phase/{seq}/{phase}/lockit-snapshots.bin');need(count==(78 if entry==0x4b7f70 else 6 if entry in roots or entry==0x4e1ca0 else 0)and len(snapshots)==count*12988,'Exactly six Lockit observations per selected four root')
     # Every phase endpoint carries the same opaque initialized provider pages.
     for a in(0x7810a000,0x78145000,0x78146000):need(page(data,a)==page(data,a,True),'Whole actual provider page carried at every root endpoint');counts['whole_provider_page_relations']+=1
     for cell,target in format_cells.items():
      before=struct.unpack_from('<I',page(data,0x5bb000),cell&4095)[0];after=struct.unpack_from('<I',page(data,0x5bb000,True),cell&4095)[0];need(before==after==target,'Each whole captured owning IAT DWORD equals the uniquely attributed final entry observer');format_IAT_rows.append(dict(sequence=seq,phase=phase,cell=cell,actual_before=before,actual_after=after,declared_entry_target=target));counts['exact_format_IAT_endpoint_relations']+=2
     observe_family(records,data,seq,phase,entry,page,formats,mixed,family_artifacts,counts,tid,targets,format_byentry)
     if entry==0x5ae3e4:observe_mfc(records,data,seq,phase,out,pin,counts,mfc_artifacts)
     if entry==0x4b7f70:observe_tree(records,data,seq,phase,owners,geometry,snapshot_rows,counts,page,tid,targets,read,ROOT)
     if entry in roots:
      r=roots[entry];before=page(data,r['header_global']&~4095);after=page(data,r['header_global']&~4095,True);oldheader,oldcounter=struct.unpack_from('<2I',before,r['header_global']&4095);head,counter=struct.unpack_from('<2I',after,r['header_global']&4095);obj=page(data,r['objects'][0]['address']&~4095,True);sentinel=struct.unpack_from('<I',obj,(r['objects'][0]['address']&4095)+4)[0]
      need(oldheader==oldcounter==0 and head and sentinel and counter==1 and head!=sentinel,'Authentic full relative-order BEFORENULL header/counter and two sourcepublished owners')
      phaseowners=[];ledger=records.data(f'phase/{seq}/{phase}/api-ledger.bin');apicount=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];need(len(ledger)==apicount*104,'Actual complete provider API ledger')
      registry_before=struct.unpack('<4I',records.data(f'phase/{seq}/{phase}/registry-before-meta.bin'));registry_before_backing=records.data(f'phase/{seq}/{phase}/registry-before-backing.bin')
      for ri in range(apicount):
       rw=struct.unpack_from('<26I',ledger,ri*104)
       if rw[24]!=3 or not rw[10]:continue
       need(rw[9]==rw[19]==0 and rw[25]==0x78011c2d and rw[21]==0 and all(rw[j]==rw[10+j]for j in(3,5,6,7))and rw[14]==rw[4]+20,'Actual named HeapReAlloc original shim ledger schema, exact source saved return and stdcall effect')
       size=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-initial/{ri}/size.bin'))[0];initial=records.data(f'phase/{seq}/{phase}/api-initial/{ri}/bytes.bin');need(rw[23]<=size<=1024 and len(initial)==size,'Full successful HeapReAlloc API-return backing before any guest writes')
       if rw[22]==registry_before[0]:need(initial[:len(registry_before_backing)]==registry_before_backing and size>=registry_before[2],'Exact complete old current registry prefix preserved at reallocation seam')
       counts['actual_HeapReAlloc_initial_full_backing_witnesses']+=1
      for a in[s for s in allocspec if s['root']==entry]:
       index=len(owners);meta=struct.unpack('<9I',records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin'));need(meta[:5]==(1,index,entry,a['CALL_pc'],a['requested'])and meta[7]==(head if a['kind']=='shared-header'else sentinel)and meta[8]>=a['requested'],'Genuine owner identity from actual MFCCALL/HeapAlloc frame');owned=records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin');need(len(owned)==meta[8]<=512,'Complete actual owned backing')
       api=ledger[meta[6]*104:(meta[6]+1)*104];apiw=struct.unpack('<26I',api);need(apiw[24]==0 and apiw[10]==meta[7] and apiw[4]+104==meta[5] and apiw[25]==0x78001385,'Exact actual allocator entry/return/providerframe identity');initial=records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/bytes.bin');size=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/size.bin'))[0];need(size==len(initial)==meta[8],'Complete actual initial owner backing before sourcewrites')
       expected=bytearray(initial);struct.pack_into('<III',expected,0,0 if a['kind']=='shared-header'else sentinel,0 if a['kind']=='shared-header'else head,0 if a['kind']=='shared-header'else sentinel);struct.pack_into('<I',expected,a['requested']-4,1 if a['kind']=='shared-header'else 0);need(owned==expected,'Exact source-owned writes and untouched initial bytes')
       phaseowners.append(meta);owners.append((meta,owned));counts['owners']+=1;counts['actual_initial_allocations']+=1;geometry.append(dict(sequence=seq,phase=phase,root=entry,kind=a['kind'],CALL_pc=a['CALL_pc'],requested=a['requested'],pointer=meta[7],capacity=meta[8],source_frame=meta[5],API_index=meta[6],BEFORE_header=oldheader,BEFORE_counter=oldcounter,header=head,sentinel=sentinel))
      entrypoints={0:0x7810a290,1:targets[0x78146198],2:0x7810a311,3:0x7810a350,4:targets[0x78146184],5:0x7810a364};local=[]
      for k in range(6):
       raw=snapshots[k*12988:(k+1)*12988];w=struct.unpack_from('<16I',raw);cpu=struct.unpack_from('<10I',raw,64);cs=struct.unpack_from('<6I',raw,676);frame=struct.unpack_from('<8I',raw,644);depth=0 if k in(0,1,5)else 1
       need(w[:4]==(1,k,entry,k)and w[6]==tid and w[7]==2 and w[8]==r['objects'][0]['address']and w[13:15]==(0x7810a290,0x7810a350)and cpu[9]==entrypoints[k],'Genuine full boundary and read-time game imports');need(cs==(0xffffffff,0xfffffffe if depth else 0xffffffff,depth,tid if depth else 0,0,0x020007d0),'Actual resourceheld/unheld lifecycle')
       need(raw[700+4096+0x640:700+4096+0x658]==raw[676:700],'Whole current provider page CS joins')
       if k in(1,4):need(frame[:2]==(0x7810a311 if k==1 else 0x7810a364,0x78145640),'Authentic sourceCALL return/CS argument frame');counts['actual_API_frames']+=1
       local.append(dict(index=k,PC=cpu[9],ESP=cpu[4],ECX=cpu[1],EAX=cpu[0],depth=depth,frame=list(frame),FX_sha256=hashlib.sha256(raw[104:616]).hexdigest(),ENV_sha256=hashlib.sha256(raw[616:644]).hexdigest()));counts['Lockit_snapshots']+=1
      need(local[1]['ESP']==local[0]['ESP']-16 and local[2]['ESP']==local[0]['ESP']-8 and local[4]['ESP']==local[3]['ESP']-8 and local[5]['ESP']==local[3]['ESP'],'Ctor/dtor actual CALL and returned frame geometry');need(local[0]['ECX']==local[3]['ECX'],'Same source stack scratch object ctor/dtor');snapshot_rows.append(dict(sequence=seq,phase=phase,root=entry,snapshots=local))
      fsraw=records.data(f'phase/{seq}/{phase}/fs-events.bin');fscount=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/fs-event-count.bin'))[0];need(len(fsraw)==fscount*1216,'Full original FS event ABI');gamefs=[fsraw[i*1216:(i+1)*1216]for i in range(fscount)if struct.unpack_from('<I',fsraw,i*1216+8)[0]<0x78000000];need(len(gamefs)==3 and [struct.unpack_from('<I',x,12)[0]for x in gamefs]==[0,1,2],'Actual full new game FS read/install/restore')
      install=gamefs[1];restore=gamefs[2];need(struct.unpack_from('<I',install,20)[0]==struct.unpack_from('<I',install,48)[0] and struct.unpack_from('<I',restore,20)[0]==struct.unpack_from('<I',install,16)[0] and install[112:124]==install[124:136] and restore[112:124]==restore[124:136],'Actual full12-byte active gameFS frame and restore');counts['new_FS_records']+=3
     for index,(meta,owned)in enumerate(owners):need(records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin')==struct.pack('<9I',*meta)and records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin')==owned,'Persistent source-owned identity/full backing');counts['owner_phase_relations']+=1
    need(len(owners)==15 and records.data(f'cleanup/{seq}/registry.bin')==struct.pack('<111I',*[callback_byentry[r['entry']]for r in order if r['entry']in callback_byentry]),'Complete15 inherited owners and111 literal callbacks per sequence')
    for index,(meta,owned)in enumerate(owners):need(records.data(f'cleanup/{seq}/lockit-allocation-{index}-before.bin')==struct.pack('<9I',*meta)and records.data(f'cleanup/{seq}/lockit-allocation-{index}-owned.bin')==owned and records.data(f'cleanup/{seq}/lockit-allocation-{index}-returned.bin')==struct.pack('<I',1),'Actual bounded original825 source cleanup per15 measured owners')
    cleanup_family(records,seq,formats,mixed,counts);widget.cleanup(seq)
    allowners.extend(owners)
   observe_constructor(records,out,pin,counts,constructor_artifacts)
   spec=importlib.util.spec_from_file_location('current_constructor_input_phase',pin(ROOT/'tools/m4-138-validation-review/constructor_input_capture_phase_v1.py'));ctor_helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(ctor_helper)
   supplemental=observe_constructor_supplement(records,prep,order,pages,callback_byentry,counts,pin,read,ctor_helper,shim_addresses)
   for label,value in supplemental.items():
    target=out/('supplement-'+label+'.json');target.write_text(json.dumps(value,indent=2)+'\n');pin(target)
   need(counts['MFC_original_phases']==6 and counts['MFC_full_normal_boundaries']==42 and counts['MFC_full_named_API_pairs']==24 and counts['MFC_true_root_TIB8192_endpoints']==12 and counts['constructor_prerequisite_graph_endpoints']==12,'Complete genuine new six-domain MFC and constructor prerequisite observation extents')
   for name_,rows_ in [('fresh-MFC-observations.json',mfc_artifacts),('fresh-constructor-prerequisites.json',constructor_artifacts)]:q_=out/name_;q_.write_text(json.dumps(rows_,indent=2)+'\n');pin(q_)
   need(counts['phases']==846 and counts['Lockit_snapshots']==612 and counts['owners']==90 and counts['new_FS_records']==198 and counts['actual_API_frames']==204,'Exact retained-family execution counts')
   need(counts['format_cdecl_boundaries']==144 and counts['format_cdecl_frames']==72 and counts['format_owners']==24 and counts['mixed_owners']==18 and counts['mixed_owned_stores']==60 and counts['mixed_publications']==18 and counts['mixed_FS_records']==36 and counts['mixed_Lockit_snapshots']==36 and counts['mixed_API_frames']==12 and counts['cosine_phases']==6 and counts['cosine_observed_results']==18 and counts['extra_whole_page_endpoint_relations']==5076 and counts['exact_format_IAT_endpoint_relations']==5076 and counts['format_current_CRT_page_endpoints']==3072 and counts['format_source_free_returns']==24 and counts['mixed_MFC825_free_returns']==18,'Complete fresh five-family normal observation extents')
   need(counts['widget_exact_MFC_CRT_transition_page_relations']==768 and counts['widget_actual_root_phases']==42 and counts['widget_whole_source_page_endpoints']==116748 and counts['widget_whole_CRT_phase_page_endpoints']==108288 and counts['widget_whole_nonstack_carried_page_relations']==57120,'Complete actual141 whole69 source and64 CRT endpoints with same-branch nonstack chronology')
   need(counts['widget_complete_GDI_boundary_sides']>0 and counts['widget_actual_stdcall_RETURN_relations']*2==counts['widget_complete_GDI_boundary_sides'] and counts['widget_actual_GetStockObject_calls']>0 and counts['widget_actual_CreateFontA_calls']>0 and counts['widget_complete_FPS_boundary_sides']>0 and counts['widget_actual_FPS_cdeclRET_relations']*2==counts['widget_complete_FPS_boundary_sides']and counts['widget_actual_FS_instruction_events']>0,'Genuine normal GDI/FPS/FS paths reached; all counts measured, no predicted API totals')
   for label,value in(('exact-MFC-hook-page-transitions',transition.rows),('widget-GDI-observations',widget.events),('widget-FS-observations',widget.fs),('FPS-observations',widget.fps),('widget-root-observations',widget.phases),('whole-source-page-relations',widget.page_relations),('whole-registry-BEFORE',widget.registry),('font-resource-lifetimes',widget.lifetimes),('new-root-heap-observations',widget.allocations)):
    target=out/(label+'.json');target.write_text(json.dumps(value,indent=2)+'\n');pin(target)
   need(not(STORAGE_ROOT/'reports/m4-original141'/name/'paired-exports').exists(),'Fresh same-session raw equality export only');export=Export(STORAGE_ROOT/'reports/m4-original141'/name/'paired-exports','original',transport,pin);export.copy(records);paired_exports.append(export.finish())
   for key,value in family_artifacts.items():(out/('fresh-'+key+'.json')).write_text(json.dumps(value,indent=2)+'\n');pin(out/('fresh-'+key+'.json'))
   (out/'format-IAT-relations.json').write_text(json.dumps(format_IAT_rows,indent=2)+'\n');pin(out/'format-IAT-relations.json')
   for name,data in [('allocation-geometry.json',geometry),('Lockit-snapshot-relations.json',snapshot_rows)]: (out/name).write_text(json.dumps(data,indent=2)+'\n');pin(out/name)
   pin(__file__);pin(ROOT/'tools/m4-tree-original/full_tree_phase.py');pin(ROOT/'tools/m4-startup130-original/family_phase_v2.py');pin(ROOT/'tools/m4-startup131-original/mfc_phase_v3.py');pin(Path(__file__).resolve().parent/'widget_phase141_v1.py');pin(Path(__file__).resolve().parent/'mfc_transition141_v1.py');pin(Path(__file__).resolve().parent/'mfc_phase141_v1.py');pin(Path(__file__).resolve().parent/'named_loader141_v2.py');pin(Path(__file__).resolve().parent/'constructor_supplement141_v4.py');pin(ROOT/'tools/m4-joint-startup131/paired_exports.py');pin(ROOT/'tools/analysis/pe.py');
   for tool in('run_storage.py',):pin(ROOT/'tools/m4-crt-allocation-root'/tool)
   for tool in('capture_bundle_storage.py','paths_capture_storage.py','stages_capture_storage.py','paths.py','manifests.py'):pin(ROOT/'tools/m4-pipeline'/tool)
   pin(sys.executable);passed=True
  finally:
   if export is not None:export.close()
   records.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual original141 six persistent relative-order sequences, all retained original138 observations plus full constructor input/ownership/body/frame/getter/cleanup gates on one reader; whole69 source/64 CRT pages plus5F2000,111 callbacks. Literal native proofs and accepted credit remain separate',build_path=str(build),build_sha256=digest,execution_path=str(execution),execution_sha256=sha(Path(execution)/'report.json'),preparation_path=str(prep)if'prep'in locals()else None,preparation_sha256=b.get('preparation_sha256')if'b'in locals()else None,original_capture=str(transport)if transport is not None else None,paired_exports=paired_exports,paired_export_readers_closed=True,record_bytes=356992,observed_pages=43,external_whole_pages=26,combined_pages=69,callbacks=111,counts=counts,original_executed=True,native_executed=False,initialized_state=2,state_seeded=False,per_phase_reseed=False,AFTER_machine_seed=False,allocation_null_path=False,reader_closed=True,reader_scope='Only fresh original141 canonical capture once, with same-session whole raw equality export on G; all DirectSet/export handles closed in finally',source_model_equivalence=False,full_reached_source_instruction_trace=False,source_shutdown_callbacks_executed=False,source_failure_unwind_admitted=False,manual_cleanup_is_source_callback=False,borrowed_stock_deleted_as_owned=False,initializer_credit=0,Lockit_observation_scope='Ctor actual entry/APIentry/sourceAPIreturn at7810A311 before epilogue, actual dtor entry/APIentry/preRET; original postRET remains source-derived only',files=files)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),Path(sys.argv[4]).resolve(),sys.argv[5],sys.argv[6])
