"""Validate fresh normal observations, retaining source/model and trace gaps."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-font479590-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact current input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def diffs(a,b):return[dict(offset=i,before=x,after=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]
def main(path,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh original validation');out.mkdir(parents=True);rawdir=out/'raw-observations';rawdir.mkdir();capture=None;passed=False;counts=collections.Counter();roots=[];events=[];fsrows=[];lifetimes=[];page_relations=[];input_index=[];font_domains=[];source_inputs=[]
 try:
  execution=read(path,digest);need(execution['passed'],'Passed actual original worker');build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and(build['sequences'],build['roots'],build['phases'],build['record_bytes'])==(1,6,6,356992),'Fixed bounded sequence geometry');pin(build['worker'],build['worker_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['snapshot_bytes']==266964 and prep['combined_source_pages']==64 and not prep['source_after_seed']and not prep['predicted_counts_supplied_to_execution']and not prep['provider_preinvoked'],'No-prediction normal preparation')
  for p,h in prep['files'].items():pin(p,h)
  contract=read(Path(build['preparation'])/'normal-contracts.json');whole=contract['whole_pages'];ordinary=prep['observed_pages'];extra=prep['external_pages'];need(len(whole)==64 and len(ordinary)==43 and len(extra)==21 and set(whole)==set(ordinary+extra),'Exact whole page inventory')
  fsbind={v['PC']:v for v in read(Path(build['preparation'])/'fs-hook-bindings.json')}
  spec=importlib.util.spec_from_file_location('widget_actual_direct',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D);capture=D.DirectSet(Path(execution['original_capture']),pin);pin(__file__);pin(R/'tools/m4-font479590-original/derive_validate_v2.py');pin(R/'tools/m4-font479590-original/validate.py','39ae5649d3578fde1ce20b789d696fd0a6455b08ba18b04128392705a4694e75');pin(R/'tools/m4-font479590-original/derive_controllers.py');pin(R/'tools/m4-widget-original/validate.py','951f71671c1ca506dba723c5d52796fcce3055f5fc79486e61b9478a399cbdd7');pin(sys.executable);need(capture.data('COMPLETE.txt')==b'complete','Actual writer finished')
  identity=words(capture.data('widget/identity.bin'),0,15);need(all(identity[i*5]==[0x5bb070,0x5bb074,0x5bb068][i]and all(identity[i*5+j]for j in range(1,5))for i in range(3)),'Three actual named import and loaded module identities');targets=[identity[i*5+1]for i in range(3)]
  header=capture.data('header.bin');need(len(header)==32 and header[:8]==b'MW4J124O'and words(header,8,6)==(1,1,6,6,43,356992),'Original normal header exact geometry')
  source_returns=[0x5a0142,0x5a0645,0x5a0751];argc=[1,1,14];prior_pages=None;created=[];live={};seen_stock={}
  for phase,root in enumerate(contract['roots']):
   stem=f'phase/0/{phase}/';raw=capture.data(f'phase/0/{phase}.bin');need(len(raw)==356992 and words(raw,0,9)==(0,0,phase,root['slot'],root['root'],0x37f,0,0,1),'Successful genuine root normal endpoint');before=words(raw,36,10);after=words(raw,76,10);need(before[9]==root['root']and before[4]==0x20001800 and after[9]==0x410a80 and after[4]==0x20001804,'Actual source root caller/RET framing');need(raw[2220:2248]==raw[2248:2276],'Outside caller full hardware environment restored')
   phase_pages={}
   for side,offset in [('before',2276),('after',178404)]:
    pages={p:raw[offset+i*4096:offset+(i+1)*4096]for i,p in enumerate(ordinary)}
    for p in extra:pages[p]=capture.data(stem+f'extra-{side}/{p}.bin')
    need(all(len(pages[p])==4096 for p in whole),'Every complete64 phase page');phase_pages[side]=pages;counts['whole_phase_page_endpoints']+=64
   for p in whole:
    a,b=phase_pages['before'][p],phase_pages['after'][p];page_relations.append(dict(phase=phase,page=p,before_sha256=hashlib.sha256(a).hexdigest(),after_sha256=hashlib.sha256(b).hexdigest(),differences=diffs(a,b)))
    if prior_pages is not None and p!=0x20001000:need(prior_pages[p]==a,'Persistent full source page carry '+hex(p));counts['whole_nonstack_carried_page_relations']+=1
   prior_pages=phase_pages['after']
   actual_input_dir=out/'actual-inputs'/f'phase-{phase}';page_exports=[]
   for side in('before','after'):
    for page,value in phase_pages[side].items():
     q=actual_input_dir/side.upper()/f'{page}.bin';q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(value);pin(q);page_exports.append(dict(side=side.upper(),page=page,path=str(q),sha256=sha(q)))
   if root['root']==0x479590:
    need(phase==5 and words(phase_pages['before'][0x638000],0x4e8)==(0,),'Actual carried479590 BEFORE zero font registry; no seeded domain')
    object_before=phase_pages['before'][0x608000][0x628:0xad8];object_after=phase_pages['after'][0x608000][0x628:0xad8];need(len(object_before)==len(object_after)==0x4b0,'Complete current newroot object source extent')
    font_domains.append(dict(phase=phase,root=root['root'],object=0x608628,extent=0x4b0,font_registry_BEFORE=0,font_registry_AFTER=words(phase_pages['after'][0x638000],0x4e8)[0],object_BEFORE_hex=object_before.hex(),object_AFTER_observed_hex=object_after.hex(),source_after_seed=False,source_model_equivalence=False))
   source_inputs.append(dict(phase=phase,root=root['root'],CPU_BEFORE_hex=raw[36:76].hex(),FX_BEFORE_hex=raw[116:628].hex(),ENV_BEFORE_hex=raw[2164:2192].hex(),whole_source_BEFORE_pages=64,whole_source_AFTER_comparison_pages=64,page_exports=page_exports))
   if not phase:need(words(phase_pages['before'][0x638000],0x4e8)==(0,),'Authentic untouched first-root font registry input')
   count=words(capture.data(stem+'widget-count.bin'))[0];blob=capture.data(stem+'widget-snapshots.bin');segments=capture.data(stem+'widget-segments.bin');need(count<=384 and count%2==0 and len(blob)==count*266964 and len(segments)==count*40,'Complete bounded actual GDI pairs/selectors')
   def source_bytes(raw,address,n):
    page=address&~4095;need(page in whole and(address&4095)+n<=4096,'Current exact source extent');start=4820+whole.index(page)*4096+(address&4095);return raw[start:start+n]
   paired=[]
   for i in range(count):
    rawsnap=blob[i*266964:(i+1)*266964];h=words(rawsnap,0,16);cpu=words(rawsnap,64,10);fx=rawsnap[104:616];env=rawsnap[616:644];frame=rawsnap[644:708];view=rawsnap[708:724];api=h[3]//2;side=h[3]%2;need(api<3 and h[:3]==(1,i,root['root'])and h[4]==cpu[9]and h[7]==targets[api]and h[8]==cpu[4]and h[11]==cpu[6]and h[12]==argc[api],'Actual GDI raw CPU and named target attribution');need(0x20001000<=cpu[4]and cpu[4]+64<=0x20002000 and frame==source_bytes(rawsnap,cpu[4],64),'True source live cdecl/stdcall frame joined to complete stack');need(len(rawsnap[4820:])==64*4096,'Every snapshot complete64 source pages')
    if h[14]:need(view==source_bytes(rawsnap,h[5],16),'Complete actual current FS16 view')
    seg=segments[i*40:(i+1)*40];sw=words(seg,0,4);need(sw[0]==i and not(cpu[8]&0x400),'True current segment occurrence and source DF0')
    for j in range(3):
     descriptor=seg[16+j*8:24+j*8];base=struct.unpack_from('<H',descriptor,2)[0]|descriptor[4]<<16|descriptor[7]<<24;limit=struct.unpack_from('<H',descriptor)[0]|(descriptor[6]&15)<<16
     if descriptor[6]&128:limit=(limit<<12)|4095
     need(base==0 and limit==0xffffffff and descriptor[5]&128 and descriptor[6]&64 and descriptor[5]&16 and not(descriptor[5]&8)and descriptor[5]&2,'Actual flat32 readable/writable data segment descriptor')
    counts['actual_flat_DS_ES_SS_descriptor_relations']+=3
    rp=rawdir/f'root-{phase}-GDI-{i}.bin';rp.write_bytes(rawsnap);pin(rp);row=dict(phase=phase,root=root['root'],index=i,API=('GetStockObject','DeleteObject','CreateFontA')[api],side=('entry','first-source-return')[side],header=list(h),CPU=list(cpu),FX512_hex=fx.hex(),ENV28_hex=env.hex(),frame64_hex=frame.hex(),FS_view16_hex=view.hex(),raw_snapshot=str(rp),raw_snapshot_sha256=sha(rp),page_sha256=[hashlib.sha256(rawsnap[4820+j*4096:4820+(j+1)*4096]).hexdigest()for j in range(64)],actual_provider_postRET=bool(side),post_source_replay_observed=False)
    if not side:
     need(cpu[9]==targets[api]and words(frame)[0]==source_returns[api],'True selected game CALL saved return');args=words(frame,4,argc[api]);row['arguments']=list(args)
     if api==0:need(args==(10,),'Actual OEM_FIXED_FONT stock request')
     if api==1:
      need(source_bytes(rawsnap,cpu[6]+0x258,4)==frame[4:8],'Delete arg equals actual source instance field');row['resource_origin']='owned-created'if(cpu[6],args[0])in live else'borrowed-stock'if seen_stock.get(cpu[6])==args[0]else'unclassified';need(row['resource_origin']!='unclassified','Every actual deleted handle linked to earlier observed same-instance acquisition')
     if api==2:
      need(args==(0xfffffff6,6,0,0,500,0,0,0,0,4,0,1,2,0x5e15dc),'All14 actual CreateFontA args');need(source_bytes(rawsnap,0x5e15dc,6)==b'Arial\0','Exact whole source face string')
    else:
     need(paired and paired[-1]['side']=='entry'and paired[-1]['API']==row['API'],'Actual noninterleaved same source API pair');entry=paired[-1];need(cpu[9]==source_returns[api]and cpu[4]==entry['CPU'][4]+4*(argc[api]+1)and h[5]==entry['header'][5],'Actual stdcall provider RET and hidden FS head');need(all(cpu[j]==entry['CPU'][j]for j in(3,5,6,7)),'True API callee saved registers')
     if api==0:seen_stock[cpu[6]]=cpu[0]
     if api==2:
      need(cpu[0]!=0,'Current actual font success domain; NULL remains unadmitted failure path');need(all(handle!=cpu[0]for _,handle in live),'No unexpired owned handle alias across current instances');resource=dict(occurrence=len(created),phase=phase,root=root['root'],instance=cpu[6],handle=cpu[0],created_event=i,live=True,deleted_event=None);created.append(resource);live[(cpu[6],cpu[0])]=resource
     if api==1:
      row['BOOL_result']=cpu[0];row['resource_origin']=entry['resource_origin']
      if cpu[0]and entry['resource_origin']=='owned-created':r=live.pop((cpu[6],entry['arguments'][0]));r['live']=False;r['deleted_event']=i
     counts['actual_'+row['API']+'_calls']+=1;counts['actual_stdcall_RET_joins']+=1
    events.append(row);paired.append(row);counts['complete_GDI_CPU_FX_ENV_frame_FS_page_observations']+=1;counts['whole_GDI_snapshot_page_endpoints']+=64
   fcount=words(capture.data(stem+'fs-event-count.bin'))[0];fblob=capture.data(stem+'fs-events.bin');need(fcount<=2048 and len(fblob)==fcount*1224,'Complete repeated current source FS events')
   for i in range(fcount):
    f=fblob[i*1224:(i+1)*1224];w=words(f,0,8);a=words(f,32,10);b=words(f,72,10);need(w[0]==1 and w[1]==root['root']and w[2]in fsbind and w[3]==fsbind[w[2]]['kind']and a[9]==b[9]==w[2],'Exact selected literal FS opcode binding');need(all(a[j]==b[j]for j in(1,2,3,4,5,6,7,8))and(a[0]==b[0]if w[3]else b[0]==w[4]),'Literal FS CPU effect only');need(w[5]==(w[4]if w[3]==0 else a[4]if w[3]==1 else a[1]),'Exact observed FS head effect');need(f[112:128]==f[128:144]and f[144:656]==f[656:1168]and f[1168:1196]==f[1196:1224],'Complete16B raw frame view and FX/ENV conserved by literal FS instruction');fsrows.append(dict(phase=phase,index=i,root=root['root'],words=list(w),CPU_before=list(a),CPU_after=list(b),record_before_hex=f[112:128].hex(),record_after_hex=f[128:144].hex(),FX_before_hex=f[144:656].hex(),FX_after_hex=f[656:1168].hex(),ENV_before_hex=f[1168:1196].hex(),ENV_after_hex=f[1196:1224].hex(),source_raw=fsbind[w[2]]['raw_bytes'],CPU_PC_is_source_instruction_projection=True));counts['actual_FS_instruction_observations']+=1
   registry_before=words(capture.data(stem+'registry-before-meta.bin'),0,4);initial_registry=capture.data(stem+'registry-before-backing.bin');need(len(initial_registry)==registry_before[2]and registry_before[1]>=registry_before[0]and registry_before[1]-registry_before[0]<=registry_before[2]<=512,'Genuine complete registry BEFORE capacity input')
   crt_before={};crt_after={}
   for j in range(64):
    p=0x78000000+j*4096;crt_before[p]=capture.data(stem+f'CRT-before/{p}.bin');crt_after[p]=capture.data(stem+f'CRT-after/{p}.bin');need(len(crt_before[p])==len(crt_after[p])==4096,'Both complete actual current CRT endpoint pages');counts['whole_CRT_phase_page_endpoints']+=2
   need(words(crt_before[0x78037000],0x888)==(registry_before[1],)and words(crt_before[0x78037000],0x88c)==(registry_before[0],)and words(crt_before[0x78035000],4)==(registry_before[3],),'Registry BEFORE fields joined to current real loaded provider pages')
   begin,next_,capacity,mode=words(raw,356464,4);need(next_>=begin and next_-begin<=capacity<=512,'Actual whole source callback registry capacity');need(raw[356480:356480+next_-begin]==capture.data('cleanup/0/registry.bin')[:next_-begin],'Source callback vector prefix carried to current actual final cleanup');counts['root_callback_endpoint_observations']+=1
   observed_callbacks=words(raw,356480,(next_-begin)//4);source_callbacks=tuple(v['callback']for v in contract['roots'][:phase+1]);need(observed_callbacks==source_callbacks,'Exact source-derived one callback publication per carried initializer, original order')
   source_inputs[-1].update(registry_BEFORE_metadata=list(registry_before),registry_BEFORE_backing_hex=initial_registry.hex(),actual_registered_callbacks=list(observed_callbacks))
   if root['root']==0x479590:font_domains[-1].update(actual_registered_callback=observed_callbacks[-1],actual_initializer_CPU_BEFORE=list(before),actual_initializer_CPU_AFTER=list(after),actual_GDI_boundary_count=count,actual_FS_event_count=fcount)
   rp=rawdir/f'root-{phase}-record.bin';rp.write_bytes(raw);pin(rp);roots.append(dict(phase=phase,root=root['root'],slot=root['slot'],CPU_before=list(before),CPU_after=list(after),FX_before_hex=raw[116:628].hex(),FX_after_hex=raw[628:1140].hex(),ENV_before_hex=raw[2164:2192].hex(),ENV_after_hex=raw[2192:2220].hex(),GDI_boundaries=count,FS_events=fcount,registry=dict(begin=begin,next=next_,capacity=capacity,mode=mode,callback_hex=raw[356480:356480+next_-begin].hex()),raw_record=str(rp),raw_record_sha256=sha(rp)));counts['actual_root_phases']+=1
  final=capture.data('cleanup/0/resources.bin');need(len(final)==len(created)*32,'Every measured CreateFont ownership occurrence retained');lifetimes=created
  for i,r in enumerate(created):
   w=words(final,i*32,8);need(w[:6]==(1,i,r['root'],r['instance'],r['handle'],r['created_event']),'Actual per-occurrence owned font resource identity')
   if r['live']:
    c=capture.data(f'cleanup/0/owned-font/{i}.bin');need(len(c)==1112 and words(c,0,8)[:4]==(1,i,r['instance'],r['handle'])and words(c,16)[0]!=0 and words(c,28)==(1,)and w[6:]==(0,0xfffffffe),'Actual owned-only successful manual DeleteObject cleanup');r['manual_cleanup_BOOL']=words(c,16)[0];r['manual_cleanup_FX_before_hex']=c[32:544].hex();r['manual_cleanup_FX_after_hex']=c[544:1056].hex();r['manual_cleanup_ENV_before_hex']=c[1056:1084].hex();r['manual_cleanup_ENV_after_hex']=c[1084:1112].hex();counts['actual_manual_owned_font_cleanups']+=1
   else:need(w[6:]==(0,r['deleted_event']),'Exact measured source owned deletion')
  need(counts['actual_root_phases']==6 and len(font_domains)==1,'Complete actual six-root plus new current-instance domain extent')
  # Export immutable actual transport inputs in this same bounded reader. Whole
  # GDI snapshots already have exact independent raw exports above.
  for logical_name in sorted(capture.entries):
   if logical_name.endswith('widget-snapshots.bin'):continue
   relative=Path(logical_name);need(not relative.is_absolute()and'..'not in relative.parts,'Strict actual logical input name')
   q=out/'actual-capture'/relative;q.parent.mkdir(parents=True,exist_ok=True);value=capture.data(logical_name);q.write_bytes(value);pin(q);input_index.append(dict(logical_capture_name=logical_name,bytes=len(value),export_path=str(q.resolve()),sha256=sha(q)))
  counts['whole_current_source_BEFORE_export_pages']=64*len(source_inputs);counts['whole_current_source_AFTER_comparison_export_pages']=64*len(source_inputs);counts['complete_current_logical_capture_exports']=len(input_index)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if capture is not None:capture.close();capture.entries.clear();capture.bundles.clear();capture=None
  for fn,value in [('actual-root-endpoints.json',roots),('actual-GDI-boundaries.json',events),('actual-source-FS-events.json',fsrows),('actual-owned-font-lifetimes.json',lifetimes),('actual-whole-page-endpoints.json',page_relations),('actual-font479590-domain.json',font_domains),('whole-original-inputs.json',source_inputs),('logical-capture-export-index.json',input_index)]:p=out/fn;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  report=dict(passed=passed,scope='Current authentic original normal GDI/resource/FS/root observations only; independent literal, virtual/array trace, source shutdown/unwind and native proofs remain open',execution_path=str(path),execution_sha256=digest,counts=dict(counts),source_after_seed=False,provider_preinvoked=False,predicted_counts_used=False,source_model_equivalence=False,full_reached_source_instruction_trace=False,source_shutdown_callbacks_executed=False,source_failure_unwind_admitted=False,manual_cleanup_is_source_callback=False,borrowed_stock_deleted_as_owned=False,initializer_credit=0,reader_closed=True,all_reader_aliases_closed=True,current_font_domain_observed=True,whole_current_source_BEFORE_exported=True,whole_current_CRT_BEFORE_exported=True,files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
