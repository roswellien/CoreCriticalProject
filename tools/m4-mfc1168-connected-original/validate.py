"""Bounded actual chronological observations; literal/native credit stays separate."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-connected-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Immutable identity');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(path,digest,name):
 out=B/name;need(not out.exists(),'Fresh validation');out.mkdir(parents=True);capture=None;passed=False;counts=collections.Counter();phases=[];boundaries=[];apis=[];domains={};artifacts={}
 try:
  execution=read(path,digest);need(execution['passed'],'Actual writer completion');build=read(execution['build_path'],execution['build_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(build['passed']and prep['passed']and(prep['original_roots'],prep['original_sequences'],prep['record_bytes'],prep['source_frame'])==(14,1,356992,0x20001800),'Exact chronological preparation');pin(build['worker'],build['worker_sha256'])
  for p,h in prep['files'].items():pin(p,h)
  contract=read(prep['contracts']);need(not contract['MFC_provider_discovery_precall']and not contract['source_AFTER_seed'],'Genuine inputs only');pages=contract['fixed_current_source_pages'];extras=contract['external_source_pages'];need(len(pages)==43 and len(extras)==3,'Current46 whole pages')
  spec=importlib.util.spec_from_file_location('MFC_current_direct',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D);capture=D.DirectSet(Path(execution['original_capture']),pin);pin(__file__);pin(sys.executable)
  need(capture.data('MFC1168/COMPLETE.txt')==b'complete','Final original completion');header=capture.data('header.bin');need(len(header)==32 and header[:8]==b'MW4M131P'and w(header,8,6)==(1,1,14,14,43,356992),'Exact phase ABI')
  target=w(capture.data('MFC1168/named-API/targets.bin'),0,4);imports=w(capture.data('MFC1168/loaded/owning-game-imports.bin'),0,6);need(imports==(0x5bb210,0x5f401083,0x5f400000,0x5bb674,0x78003ddb,0x78000000),'Two physical loaded owning game imports')
  def retain(key):
   data_=capture.data(key);p=out/'actual-inputs'/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data_);pin(p);artifacts[key]=dict(path=str(p),sha256=sha(p),bytes=len(data_));return data_
  previous=None;previous_cpu=None;previous_fx=None;previous_env=None
  for phase,row in enumerate(contract['selected_order']):
   stem=f'phase/0/{phase}';raw=retain(stem+'.bin');need(len(raw)==356992 and w(raw,0,9)==(0,0,phase,row['slot'],row['entry'],0x7f,0,0,1),'Actual normal phase endpoint');before=w(raw,36,10);after=w(raw,76,10);need(before[4]==0x20001800 and before[9]==row['entry']and after[4]==0x20001804 and after[9]==0x410a80,'Actual source caller and root RET');need(raw[2220:2248]==raw[2248:2276],'Outside caller full raw ENV restored')
   current={}
   for side,off in [('before',2276),('after',178404)]:
    values={p:raw[off+i*4096:off+(i+1)*4096]for i,p in enumerate(pages)}
    for p in extras:values[p]=retain(stem+f'/extra-{side}/{p}.bin')
    need(all(len(v)==4096 for v in values.values()),'Every complete physical page');current[side]=values;counts['whole_current_source_page_endpoints']+=46
   if previous is not None:
    for p in pages+extras:
     if p==0x20001000:continue
     need(previous[p]==current['before'][p],'Persistent chronological page carry '+hex(p));counts['whole_nonstack_page_carry_relations']+=1
    need(all(before[j]==previous_cpu[j]for j in range(10)if j not in(4,9))and raw[116:628]==previous_fx and raw[2164:2192]==previous_env,'Whole incoming CPU/FX/ENV carry with only declared caller framing');counts['complete_chronological_machine_carry_relations']+=1
   previous=current['after'];previous_cpu=after;previous_fx=raw[628:1140];previous_env=raw[2192:2220]
   for side in('before','after'):
    stack=retain(stem+f'/stack-{side}.bin');need(stack==current[side][0x20001000],'Whole actual live stack duplicate exact join')
    base=w(retain(stem+f'/TEB-{side}-base.bin'))[0];teb=retain(stem+f'/TEB-{side}.bin');need(base%4096==0 and len(teb)==8192 and w(teb,0x18)==(base,),'Coherent actual assembly TEB full8192B and self');counts['complete_coherent_actual_TEB_endpoints']+=1
   regmeta=w(retain(stem+'/registry-before/meta.bin'),0,5);initial=retain(stem+'/registry-before/bytes.bin');endmeta=w(retain(stem+'/registry-after/meta.bin'),0,5);end=retain(stem+'/registry-after/bytes.bin');need(len(initial)==regmeta[2]<=512 and regmeta[1]>=regmeta[0]and regmeta[1]-regmeta[0]<=len(initial),'Complete actual source registry BEFORE backing');need(len(end)==endmeta[2]<=512 and endmeta[1]>=endmeta[0]and endmeta[1]-endmeta[0]<=len(end),'Complete actual registry AFTER backing');need(w(raw,356464,4)==endmeta[:4]and raw[356480:356480+endmeta[2]]==end,'Fixed phase registry joined to same actual complete capacity');counts['complete_actual_registry_endpoints']+=2
   phases.append(dict(phase=phase,slot=row['slot'],root=row['entry'],CPU_before=list(before),CPU_after=list(after),FX_before_hex=raw[116:628].hex(),FX_after_hex=raw[628:1140].hex(),ENV_before_hex=raw[2164:2192].hex(),ENV_after_hex=raw[2192:2220].hex(),registry_BEFORE=list(regmeta),registry_AFTER=list(endmeta)))
  for side in('BEFORE','AFTER'):
   domain=retain('MFC1168/'+side+'/domain/domain.bin');need(len(domain)==40,'Actual current graph domain geometry');domains[side]=dict(metadata=list(w(domain,0,10)),blocks={})
   for kind in('MFC','CRT'):
    meta=retain('MFC1168/'+side+'/'+kind+'/metadata.bin');need(len(meta)%16==0,'Actual complete loaded page metadata');base,end=(0x5f400000,0x5f4ed000)if kind=='MFC'else(0x78000000,0x78040000)
    for i in range(len(meta)//16):
     page,protection,type_,owner=w(meta,i*16,4);need(base<=page<end and page%4096==0 and type_==0x1000000 and owner==base,'Actual preferred loaded page identity');need(len(retain(f'MFC1168/{side}/{kind}/{page}.bin'))==4096,'Whole real loader page');counts['whole_actual_loaded_'+kind+'_page_endpoints']+=1
   for role in('manager','manager-array','thread','thread-array','thread-object','thread-object-plus4','global-object'):
    key=f'MFC1168/{side}/domain/{role}/meta.bin'
    if key not in capture.entries:continue
    meta=w(retain(key),0,8);info=dict(metadata=list(meta),whole_capacity_observed=bool(meta[6]and meta[7]))
    if meta[6]and meta[7]:need(len(retain(key.replace('/meta.bin','/bytes.bin')))==meta[6],'Actual whole borrowed backing capacity');counts['whole_borrowed_backing_endpoints']+=1
    elif meta[5]!=0x1000000:need(len(retain(key.replace('/meta.bin','/unresolved-page.bin')))==4096,'Explicit unresolved backing page retained')
    domains[side]['blocks'][role]=info
   lm=w(retain(f'MFC1168/{side}/CRT-codepage-lock/meta.bin'),0,4);need(lm[0]==0x7803708c and lm[2]==24 and lm[3]==bool(lm[1]),'Actual current lock25 pointer');domains[side]['lock25_metadata']=list(lm)
   if lm[1]:need(len(retain(f'MFC1168/{side}/CRT-codepage-lock/bytes.bin'))==24,'Complete current CS24 bytes');counts['whole_current_codepage_CS24_endpoints']+=1
  n=w(retain('MFC1168/boundaries/count.bin'))[0];blob=retain('MFC1168/boundaries/records.bin');need(n<=16 and len(blob)==n*664,'Every actual normal boundary');pcs=[0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca];need(n==len(pcs),'Complete normally reached seven boundaries')
  for i,pc in enumerate(pcs):
   b=blob[i*664:(i+1)*664];cpu=w(b,0,10);need(cpu[9]==pc,'Exact measured source boundary order');frame=b[580:644];meta=w(b,644,5);row=dict(index=i,CPU=list(cpu),FX512_hex=b[40:552].hex(),ENV28_hex=b[552:580].hex(),frame64_hex=frame.hex(),metadata=list(meta))
   if i==0:need(w(frame)==(0x5ae3ad,),'Actual provider CALL saved return')
   if i==5:need(w(frame,0,2)==(0x5ae3ca,0xfffffffd),'Actual cdecl setmbcp−3 argument')
   if i in(1,2,3,4):row['whole_provider_before_write_hex']=retain('MFC1168/boundaries/'+str(i)+'-whole-provider.bin').hex();need(len(bytes.fromhex(row['whole_provider_before_write_hex']))==meta[4]>=0x1044,'Actual whole provider field backing')
   boundaries.append(row);counts['full_actual_MFC_game_boundaries']+=1
  n=w(retain('MFC1168/named-API/count.bin'))[0];blob=retain('MFC1168/named-API/records.bin');need(n<=64 and n%2==0 and len(blob)==n*668,'Complete bounded actual named API pairs')
  for i in range(n):
   b=blob[i*668:(i+1)*668];cpu=w(b,0,10);kind,side,argc,thread,error,head=w(b,644,6);need(kind<4 and side==i%2 and argc==(0 if kind==2 else 1),'Actual named API geometry');frame=b[580:644];row=dict(index=i,API=['TlsGetValue','EnterCriticalSection','GetACP','LeaveCriticalSection'][kind],kind=kind,side=side,argc=argc,thread=thread,last_error=error,FShead=head,CPU=list(cpu),FX512_hex=b[40:552].hex(),ENV28_hex=b[552:580].hex(),frame64_hex=frame.hex())
   if not side:need(cpu[9]==target[kind],'Real named target CPU entry');row['saved_source_return']=w(frame)[0]
   else:
    a=apis[-1];need(a['kind']==kind and a['side']==0 and cpu[9]==a['saved_source_return']and cpu[4]==a['CPU'][4]+4*(argc+1),'Actual same named API callee cleanup and saved source continuation');need(all(cpu[j]==a['CPU'][j]for j in(3,5,6,7)),'Actual API callee-saved registers');counts['full_actual_named_API_pairs']+=1
   apis.append(row)
  counts['actual_chronological_root_phases']=14;passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if capture is not None:capture.close();capture.entries.clear();capture.bundles.clear();capture=None
  for fn,v in [('actual-root-endpoints.json',phases),('actual-MFC-boundaries.json',boundaries),('actual-named-API-boundaries.json',apis),('actual-borrowed-domains.json',domains),('retained-actual-inputs.json',artifacts)]:p=out/fn;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
  report=dict(passed=passed,scope='Genuine chronological13-prefix and normally reached MFC original source/resource/CPU/FX/ENV observations only; literal original source, typed connected alias/input merge, native and full six-domain comparison remain subsequent gates',execution_path=str(path),execution_sha256=digest,counts=dict(counts),source_after_seed=False,provider_preinvoked=False,source_model_equivalence=False,full_reached_instruction_trace=False,initializer_credit=0,reader_closed=True,files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
