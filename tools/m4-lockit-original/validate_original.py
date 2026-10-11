"""Authenticate actual original124 bootstrap, Lockit frames, owners and schedule."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-lockit-original';CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(build,digest,execution,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;counts=dict(phases=0,Lockit_snapshots=0,owners=0,owner_phase_relations=0,actual_initial_allocations=0,new_FS_records=0,actual_API_frames=0,whole_provider_page_relations=0)
 def need(x,w):
  if not x:raise ValueError(w)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact pin '+str(p));need(str(p)not in files or files[str(p)]==v,'No conflicting pin');files[str(p)]=v;return p
 def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
 try:
  b=read(pin(build,digest));need(b['passed'],'Actual x86 build');
  for p,h in read(Path(build).parent/'pins.json')['files'].items():pin(p,h)
  prep=Path(b['preparation']);p=read(pin(prep/'report.json',b['preparation_sha256']));need(p['passed']and p['record_bytes']==356992 and len(p['order'])==124,'Exact original124 ABI/order')
  for q,h in p['files'].items():pin(q,h)
  e=Path(execution);run=read(e/'report.json');need(run['passed']and run['build_sha256']==digest,'Actual original124 execution');stage=read(e/'run/stage.json');need(stage['passed'],'Actual execution stage complete')
  readerpath=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('lockit_original_direct_reader',readerpath);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);records=ds.DirectSet(e/'original/transport.json',pin)
  try:
   need(records.data('COMPLETE.txt')==b'complete','Complete capture');header=records.data('header.bin');need(header[:8]==b'MW4J124O'and struct.unpack_from('<6I',header,8)==(1,6,124,744,43,356992),'Exact original header')
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
   callback_roots=read(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json')+read(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json')+read(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json')+read(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json')+read(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json')+read(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json')['roots']+list(roots.values());callback_roots.sort(key=lambda r:r['slot']);callback_byentry={r['entry']:r['registration']['callback']for r in callback_roots};need(len(callback_byentry)==96,'96 exact recovered callbacks')
   geometry=[];snapshot_rows=[];allowners=[]
   for seq,(repeat,cw,top)in enumerate(CASES):
    carried=[];owners=[]
    for phase,item in enumerate(order):
     entry=item['entry'];data=records.data(f'phase/{seq}/{phase}.bin');need(len(data)==356992 and struct.unpack_from('<9I',data)==(seq,repeat,phase,item['slot'],entry,cw,top,0,1),'Authentic successful phase tag and host restore');need(struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80,'Actual caller rootRET machine boundary');counts['phases']+=1
     if entry in callback_byentry:carried.append(callback_byentry[entry])
     begin,nxt,capacity,mode=struct.unpack_from('<4I',data,356464);need(begin and nxt-begin==len(carried)*4<=capacity<=512 and mode==1 and struct.unpack_from('<'+str(len(carried))+'I',data,356480)==tuple(carried),'Exact source registry callbacks, capacity, original mode1')
     count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/lockit-count.bin'))[0];snapshots=records.data(f'phase/{seq}/{phase}/lockit-snapshots.bin');need(count==(6 if entry in roots else 0)and len(snapshots)==count*12988,'Exactly six Lockit observations per selected four root')
     # Every phase endpoint carries the same opaque initialized provider pages.
     for a in(0x7810a000,0x78145000,0x78146000):need(page(data,a)==page(data,a,True),'Whole actual provider page carried at every root endpoint');counts['whole_provider_page_relations']+=1
     if entry in roots:
      r=roots[entry];before=page(data,r['header_global']&~4095);after=page(data,r['header_global']&~4095,True);oldheader,oldcounter=struct.unpack_from('<2I',before,r['header_global']&4095);head,counter=struct.unpack_from('<2I',after,r['header_global']&4095);obj=page(data,r['objects'][0]['address']&~4095,True);sentinel=struct.unpack_from('<I',obj,(r['objects'][0]['address']&4095)+4)[0]
      need(oldheader==oldcounter==0 and head and sentinel and counter==1 and head!=sentinel,'Authentic full relative-order BEFORENULL header/counter and two sourcepublished owners')
      phaseowners=[];ledger=records.data(f'phase/{seq}/{phase}/api-ledger.bin');apicount=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];need(len(ledger)==apicount*104,'Actual complete provider API ledger')
      for a in[s for s in allocspec if s['root']==entry]:
       index=len(owners);meta=struct.unpack('<9I',records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin'));need(meta[:5]==(1,index,entry,a['CALL_pc'],a['requested'])and meta[7]==(head if a['kind']=='shared-header'else sentinel)and meta[8]>=a['requested'],'Genuine owner identity from actual MFCCALL/HeapAlloc frame');owned=records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin');need(len(owned)==meta[8]<=512,'Complete actual owned backing')
       api=ledger[meta[6]*104:(meta[6]+1)*104];apiw=struct.unpack('<26I',api);need(apiw[24]==0 and apiw[10]==meta[7] and apiw[4]+104==meta[5] and apiw[25]==0x78001385,'Exact actual allocator entry/return/providerframe identity');initial=records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/bytes.bin');size=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/size.bin'))[0];need(size==len(initial)==meta[8],'Complete actual initial owner backing before sourcewrites')
       expected=bytearray(initial);struct.pack_into('<III',expected,0,0 if a['kind']=='shared-header'else sentinel,0 if a['kind']=='shared-header'else head,0 if a['kind']=='shared-header'else sentinel);struct.pack_into('<I',expected,a['requested']-4,1 if a['kind']=='shared-header'else 0);need(owned==expected,'Exact source-owned writes and untouched initial bytes')
       phaseowners.append(meta);owners.append((meta,owned));counts['owners']+=1;counts['actual_initial_allocations']+=1;geometry.append(dict(sequence=seq,phase=phase,root=entry,kind=a['kind'],CALL_pc=a['CALL_pc'],requested=a['requested'],pointer=meta[7],capacity=meta[8],source_frame=meta[5],API_index=meta[6],BEFORE_header=oldheader,BEFORE_counter=oldcounter,header=head,sentinel=sentinel))
      entrypoints={0:0x7810a290,1:targets[0x78146198],2:0x7810a311,3:0x7810a350,4:targets[0x78146184],5:0x7810a364};local=[]
      for k in range(6):
       raw=snapshots[k*12988:(k+1)*12988];w=struct.unpack_from('<16I',raw);cpu=struct.unpack_from('<10I',raw,64);cs=struct.unpack_from('<6I',raw,676);frame=struct.unpack_from('<8I',raw,644);depth=0 if k in(0,1,5)else1
       need(w[:4]==(1,k,entry,k)and w[6]==tid and w[7]==2 and w[8]==r['objects'][0]['address']and w[13:15]==(0x7810a290,0x7810a350)and cpu[9]==entrypoints[k],'Genuine full boundary and read-time game imports');need(cs==(0xffffffff,0xfffffffe if depth else 0xffffffff,depth,tid if depth else0,0,0x020007d0),'Actual resourceheld/unheld lifecycle')
       need(raw[700+4096+0x640:700+4096+0x658]==raw[676:700],'Whole current provider page CS joins')
       if k in(1,4):need(frame[:2]==(0x7810a311 if k==1 else0x7810a364,0x78145640),'Authentic sourceCALL return/CS argument frame');counts['actual_API_frames']+=1
       local.append(dict(index=k,PC=cpu[9],ESP=cpu[4],ECX=cpu[1],EAX=cpu[0],depth=depth,frame=list(frame),FX_sha256=hashlib.sha256(raw[104:616]).hexdigest(),ENV_sha256=hashlib.sha256(raw[616:644]).hexdigest()));counts['Lockit_snapshots']+=1
      need(local[1]['ESP']==local[0]['ESP']-16 and local[2]['ESP']==local[0]['ESP']-8 and local[4]['ESP']==local[3]['ESP']-8 and local[5]['ESP']==local[3]['ESP'],'Ctor/dtor actual CALL and returned frame geometry');need(local[0]['ECX']==local[3]['ECX'],'Same source stack scratch object ctor/dtor');snapshot_rows.append(dict(sequence=seq,phase=phase,root=entry,snapshots=local))
      fsraw=records.data(f'phase/{seq}/{phase}/fs-events.bin');fscount=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/fs-event-count.bin'))[0];need(len(fsraw)==fscount*1216,'Full original FS event ABI');gamefs=[fsraw[i*1216:(i+1)*1216]for i in range(fscount)if struct.unpack_from('<I',fsraw,i*1216+8)[0]<0x78000000];need(len(gamefs)==3 and [struct.unpack_from('<I',x,12)[0]for x in gamefs]==[0,1,2],'Actual full new game FS read/install/restore')
      install=gamefs[1];restore=gamefs[2];need(struct.unpack_from('<I',install,20)[0]==struct.unpack_from('<I',install,48)[0] and struct.unpack_from('<I',restore,20)[0]==struct.unpack_from('<I',install,16)[0] and install[112:124]==install[124:136] and restore[112:124]==restore[124:136],'Actual full12-byte active gameFS frame and restore');counts['new_FS_records']+=3
     for index,(meta,owned)in enumerate(owners):need(records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin')==struct.pack('<9I',*meta)and records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin')==owned,'Persistent source-owned identity/full backing');counts['owner_phase_relations']+=1
    need(len(owners)==8 and records.data(f'cleanup/{seq}/registry.bin')==struct.pack('<96I',*[callback_byentry[r['entry']]for r in order if r['entry']in callback_byentry]),'Complete eight owners and96 callbacks per sequence')
    for index,(meta,owned)in enumerate(owners):need(records.data(f'cleanup/{seq}/lockit-allocation-{index}-before.bin')==struct.pack('<9I',*meta)and records.data(f'cleanup/{seq}/lockit-allocation-{index}-owned.bin')==owned and records.data(f'cleanup/{seq}/lockit-allocation-{index}-returned.bin')==struct.pack('<I',1),'Actual bounded original825 source cleanup per eight owner')
    allowners.extend(owners)
   need(counts['phases']==744 and counts['Lockit_snapshots']==144 and counts['owners']==48 and counts['new_FS_records']==72 and counts['actual_API_frames']==48,'Exact execution counts')
   for name,data in [('allocation-geometry.json',geometry),('Lockit-snapshot-relations.json',snapshot_rows)]: (out/name).write_text(json.dumps(data,indent=2)+'\n');pin(out/name)
   pin(__file__);pin(sys.executable);passed=True
  finally:records.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual original124 six persistent relative-order sequences, genuine MSVCP50 loaded provider pages/state2/CS, eight new originalowners, normal FS and96callbackregistration schedule; no nativecredit',build_path=str(build),build_sha256=digest,execution_path=str(execution),execution_sha256=sha(Path(execution)/'report.json'),preparation_path=str(prep)if'prep'in locals()else None,preparation_sha256=b.get('preparation_sha256')if'b'in locals()else None,original_capture=str(Path(execution)/'original/transport.json'),record_bytes=356992,observed_pages=43,callbacks=96,counts=counts,original_executed=True,native_executed=False,initialized_state=2,state_seeded=False,per_phase_reseed=False,AFTER_machine_seed=False,allocation_null_path=False,Lockit_observation_scope='Ctor actual entry/APIentry/sourceAPIreturn at7810A311 before epilogue, actual dtor entry/APIentry/preRET; original postRET remains source-derived only',files=files)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=counts)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
