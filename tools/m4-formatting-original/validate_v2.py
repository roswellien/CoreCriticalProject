"""Fresh small original probe validation. Observed string/owner effects; no generic formatter proof."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-formatting-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical source');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(path,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh additive validation');out.mkdir(parents=True);passed=False;bundle=None;counts=collections.Counter();events=[];owners=[];root_rows=[]
 try:
  execution=read(path,digest);need(execution['passed'],'Actual bounded original execution');build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and build['sequences']==1 and build['phases']==build['roots']==3,'Three-root fresh worker');pin(build['worker'],build['worker_sha256'])
  prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['format_event_bytes']==2244 and not prep['source_output_seed'] and not prep['predicted_counts_supplied_to_execution'],'Exact capture schema and no predicted observation input')
  for p,h in prep['files'].items():pin(p,h)
  roots=read(ROOT/'reports/m4-formatting-frontier/recovery-r1/roots.json');pages=prep['observed_pages'];need(len(pages)==43,'Unchanged ordinary43 pages')
  spec=importlib.util.spec_from_file_location('format_original_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));direct=importlib.util.module_from_spec(spec);spec.loader.exec_module(direct);bundle=direct.DirectSet(Path(execution['original_capture']),pin)
  targets=words(bundle.data('formatting/import-targets.bin'),0,3);need(targets==(0x780264a9,0x780012b3,0x78022b9a),'Actual named staged CRT identities')
  initial_by_index={};previous_owners={};phase_pages=[]
  for phase,r in enumerate(roots):
   data=bundle.data(f'phase/0/{phase}.bin');need(len(data)==356992 and words(data,0,9)==(0,0,phase,r['slot'],r['entry'],0x7f,0,0,1),'Actual successful root and full hardware host restoration')
   def image(side,address,size):
    need((address&4095)+size<=4096,'Whole-page field');o=(2276 if side=='before' else 178404)+pages.index(address&~4095)*4096+(address&4095);return data[o:o+size]
   need(image('before',r['object'],r['object_extent'])==bytes(r['object_extent']),'Genuine untouched object BEFORE')
   root_before=words(data,36,10);root_after=words(data,76,10);need(root_before[4]==root_after[4]-4 and root_after[9]==0x410a80,'Actual top-level source RET')
   need(data[116:628]==data[628:1140] and data[2164:2192]==data[2192:2220],'Actual root architectural FP/ENV conservation')
   for page in prep['extra_whole_source_pages']:
    a=bundle.data(f'phase/0/{phase}/extra-before/{page}.bin');b=bundle.data(f'phase/0/{phase}/extra-after/{page}.bin');raw=pin(ROOT/f'reports/m4-formatting-frontier/recovery-r1/game-{page:08x}-raw-page.bin').read_bytes();need(len(a)==len(b)==4096 and a==b==raw,'Complete actual source asset page identity');counts['extra_whole_page_endpoint_relations']+=2
   ledger=list(struct.iter_unpack('<26I',bundle.data(f'phase/0/{phase}/api-ledger.bin')));need(words(bundle.data(f'phase/0/{phase}/api-count.bin'))[0]==len(ledger),'Actual full API ledger');counts['actual_Win32_API_records']+=len(ledger)
   stem=f'phase/0/{phase}/formatting';raw=bundle.data(stem+'/events.bin');n=words(bundle.data(stem+'/count.bin'))[0];need(n and len(raw)==n*2244,'Bounded actual full cdecl boundary array');sides=[]
   for i in range(n):
    row=raw[i*2244:(i+1)*2244];head=words(row,0,16);cpu=words(row,64,10);frame=words(row,644,8);kind=head[3];need(head[:3]==(1,i,r['entry']) and kind<6 and head[7]==targets[kind//2] and cpu[9]==head[4],'Actual root/API boundary labels and named targets')
    strings=[]
    for j in range(4):
     o=676+j*136;p,l=words(row,o,2);need(l<=128,'Actual bounded string extent');v=row[o+8:o+8+l];need(not p or l and v[-1]==0,'Actual whole NUL-terminated input string');strings.append(dict(pointer=p,length=l,bytes_hex=v.hex()))
    evt=dict(phase=phase,index=i,root=r['entry'],kind=kind,actual_source_pc=head[4],actual_provider=head[7],CALL_pc=head[8],header=list(head),cpu=list(cpu),frame32_hex=row[644:676].hex(),strings=strings,FX512_hex=row[104:616].hex(),ENV28_hex=row[616:644].hex(),owned_hex=row[1220:1220+head[15]].hex(),actual_provider_return_to_game_observed=bool(kind&1),original_post_source_cleanup_observed=False)
    events.append(evt);sides.append((head,cpu,row,frame));counts['actual_cdecl_boundaries']+=1
   need([h[3]for h,c,b,f in sides]==[0,1,2,3,4,5],'Actual observed cdecl CALL/return order')
   for type_,(callpc,retpc,nargs)in enumerate([(0x4dea15,0x4dea1b,2),(0x4deab1,0x4deab7,1),(0x4dead1,0x4dead7,4)]):
    h,c,b,f=sides[type_*2];q,d,a,g=sides[type_*2+1];need(c[4]+4==d[4] and f[0]==retpc and q[4]==d[9]==retpc,'Actual cdecl frame and genuine return-to-caller ESP/PC');need(all(c[j]==d[j]for j in (3,5,6,7)),'Actual cdecl callee-saved CPU');need(f[1:nargs+1]==g[:nargs],'Actual caller-owned arguments carried over RET');counts['actual_cdecl_frame_and_return_pairs']+=1
   h,c,b,f=sides[0];q,d,a,g=sides[1];need(f[1:3]==(r['filename'],0x2e) and not d[0],'Actual default strrchr NULL result');need(b[104:644]==a[104:644] and not(c[8]&0x400)and not(d[8]&0x400),'Actual complete strrchr FP/ENV and source DF0')
   mh,mc,mb,mf=sides[2];rh,rc,rb,rf=sides[3];sh,sc,sb,sf=sides[4];th,tc,tb,tf=sides[5]
   need(mf[1]==r['statically_derived_default_request'] and sf[1]==rc[0] and sf[2]==0x5e37f0 and sf[3]==r['filename'],'Actual malloc request and sprintf destination/format/filename args')
   actual_owner_count=words(bundle.data(stem+'/owner-count.bin'))[0];need(actual_owner_count>len(previous_owners) and actual_owner_count<=16,'Actual owner occurrence count grew')
   for index in range(actual_owner_count):
    base=stem+f'/owner/{index}';meta=words(bundle.data(base+'/meta.bin'),0,16);initial=bundle.data(base+'/initial.bin');final=bundle.data(base+'/bytes.bin');need(meta[:2]==(1,index) and len(initial)==len(final)==meta[6]>=meta[4],'Actual whole capacity owner observation')
    if index in previous_owners:need(meta==previous_owners[index]['meta'] and initial==previous_owners[index]['initial'] and final==previous_owners[index]['final'],'Persistent actual full owner bytes');counts['whole_carried_owner_relations']+=1;continue
    need(meta[2]==r['entry'] and meta[3]==0x4deab1 and meta[4]==mf[1] and meta[5]==rc[0] and meta[7]==rh[14],'Unique actual malloc occurrence/source frame/HeapAlloc attribution');api=ledger[meta[7]];need(api[24]==0 and api[10]==meta[5] and api[20]==meta[8] and api[22]==meta[9] and meta[4]<=meta[9]<=meta[6],'Actual HeapAlloc result/heap/request/capacity relation')
    need(initial==bundle.data(f'phase/0/{phase}/api-initial/{meta[7]}/bytes.bin') and len(initial)==words(bundle.data(f'phase/0/{phase}/api-initial/{meta[7]}/size.bin'))[0],'Whole original allocator initial backing')
    output=r['statically_derived_default_output'].encode()+b'\0';need(final[:len(output)]==output and final[len(output):]==initial[len(output):],'Actual formatted output and untouched complete capacity tail');need(tc[0]==len(output)-1 and tb[1220:1220+meta[6]]==final and rb[1220:1220+meta[6]]==initial,'Actual sprintf return count/final bytes and actual malloc-return initial bytes');need(words(image('after',r['owned_pointer_field'],4))[0]==meta[5],'Actual game owner publication')
    owned=dict(index=index,root=r['entry'],meta=list(meta),pointer=meta[5],request=meta[4],actual_HeapAlloc_request=meta[9],capacity=meta[6],API_index=meta[7],initial_hex=initial.hex(),final_hex=final.hex(),output_hex=output.hex());owners.append(owned);previous_owners[index]=dict(meta=meta,initial=initial,final=final);counts['actual_allocator_occurrences']+=1;counts['full_owned_initial_final_relations']+=1;counts['source_owner_publications']+=1
   obj=words(image('after',r['object'],r['object_extent']),0,r['object_extent']//4);need(obj[0]==r['vtable'] and obj[1]==rc[0] and obj[2:9]==(0,0,0,128,100,0,1)and(r['object_extent']==36 or obj[9]==0),'Actual complete object fields');root_rows.append(dict(phase=phase,entry=r['entry'],BEFORE_CPU=list(root_before),AFTER_CPU=list(root_after),object_address=r['object'],object_DWORDs=list(obj),request=mf[1],sprintf_result=tc[0],source_strlen_plus4_verified=True));counts['actual_root_phases']+=1
   for name in ('lockit-count.bin','fs-count.bin'):
    # These APIs may expose FS inside registry/free; per-kind boundaries retained separately.
    if f'phase/0/{phase}/{name}'in bundle.entries:counts['actual_'+name.split('-')[0]+'_observations']+=words(bundle.data(f'phase/0/{phase}/{name}'))[0]
  registry=words(bundle.data('cleanup/0/registry.bin'),0,3);need(registry==tuple(r['registration']['callback']for r in roots),'Actual callback registrations in source order');counts['actual_callbacks_registered']=len(registry)
  owner_count=words(bundle.data('cleanup/formatting-owner-count.bin'))[0];need(owner_count==len(owners),'Actual full cleanup owner extent')
  for o in owners:
   base=f'cleanup/formatting/{o["index"]}';need(words(bundle.data(base+'/meta.bin'),0,16)==tuple(o['meta']) and bundle.data(base+'/before.bin').hex()==o['final_hex'] and words(bundle.data(base+'/returned.bin'))==(1,),'Actual source CRT free returned after complete final backing capture');counts['actual_source_free_returns']+=1
  need(bundle.data('COMPLETE.txt')==b'complete','Actual worker completion');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if bundle:bundle.close()
  for fn,value in [('actual-cdecl-boundaries.json',events),('actual-owners.json',owners),('actual-root-relations.json',root_rows)]:p=out/fn;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  pin(__file__);report=dict(passed=passed,scope='Genuine original formatting3 actual cdecl calls/returns, complete source inputs, allocator initial/capacity/backing/publication and source CRT cleanup; reached literal _output semantics remain pending, no generic formatter or native execution claim',execution_path=str(path),execution_sha256=digest,build_sha256=execution.get('build_sha256'),preparation_sha256=build.get('preparation_sha256'),counts=dict(counts),reader_closed=True,original_source_instruction_trace_pending=True,native_executed=False,initializer_credit=False,source_output_seed=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
