"""Authenticate genuine finite hypot observations; no numeric prediction/model."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-hypot-original';PINS={}
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def hw(b,o=0):return struct.unpack_from('<H',b,o)[0]
def difference(a,b):return[dict(offset=i,before=x,after=y)for i,(x,y)in enumerate(zip(a,b))if x!=y]
def main(path,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh bounded original validation');out.mkdir(parents=True);rawdir=out/'raw-observations';rawdir.mkdir();passed=False;capture=None;rows=[];page_rows=[];counts=collections.Counter()
 try:
  execution=read(path,digest);need(execution['passed'],'Passed genuine writer');build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and build['record_bytes']==356992 and build['roots']==1 and build['phases']==6,'Exact six-case root worker');pin(build['worker'],build['worker_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['snapshot_bytes']==271012 and prep['game_rows']==65 and prep['game_bytes']==211 and not prep['predicted_outputs_supplied_to_execution']and not prep['provider_preinvoked']and not prep['source_after_seed'],'Exact no-prediction source/capture geometry')
  for p,h in prep['files'].items():pin(p,h)
  contract=read(Path(build['preparation'])/'instruction-contracts.json');pages=prep['observed_pages'];need(len(pages)==43,'Full inherited observation43-page geometry')
  spec=importlib.util.spec_from_file_location('hypot_actual_direct',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D);capture=D.DirectSet(Path(execution['original_capture']),pin);pin(__file__);pin(sys.executable);need(capture.data('COMPLETE.txt')==b'complete','Actual worker completion');identity=words(capture.data('hypot/identity.bin'),0,4);need(identity[0]==0x5bb5b0 and identity[1]==0x7802a122 and identity[2]and identity[3]==0x78000000,'Exact actual named loaded CRT export and observer target')
  stores=read(BASE/'recovery-r1/root-contract.json')['whole_F32_store_instructions'];need(len(stores)==9,'Nine actual source publication instructions');final_store=next(v for v in contract['instructions']if v['pc']==0x4b5905);need(final_store['bytes_hex']=='d95e20'and final_store['mnemonic']=='fstp','Exact physical final source FSTP overwrites observer replay metadata')
  for seq,(repeat,cw,top)in enumerate(CASES):
   stem=f'phase/{seq}/0/';data=capture.data(f'phase/{seq}/0.bin');need(len(data)==356992 and words(data,0,9)==(seq,repeat,0,0x5e0154,0x4b5910,cw,top,0,1),'Exact actual successful case and host restored');before=words(data,36,10);after=words(data,76,10);need(before[4]==0x20001800 and before[9]==0x4b5910 and after[0]==0x60b2c8 and after[4]==before[4]+4 and after[9]==0x410a80,'Actual game helper RET16 then root RET to original broker');need(all(before[i]==after[i]for i in (3,5,6,7)),'Actual source callee saved registers')
   need(data[1140:1652]==data[1652:2164]and data[2220:2248]==data[2248:2276],'Complete outside caller hardware FP/environment restored');fx0,fx1=data[116:628],data[628:1140];env0,env1=data[2164:2192],data[2192:2220];need(hw(fx0)==hw(env0)==cw and hw(fx0,2)>>11&7==hw(env0,4)>>11&7==top,'Actual requested starting CW/TOP');need(words(env1,12)[0]==words(fx1,8)[0]==0x4b5905 and words(env1,20)[0]==words(fx1,16)[0]==0x60b2e8,'Actual final canonical source FIP/FDP overwrite earlier observer FLD/FXCH replay');counts['actual_final_canonical_FIP_FDP_overwrite_relations']+=1
   need(words(capture.data(stem+'hypot-count.bin'))==(4,),'Four actual cdecl observation occurrences');snapshots=capture.data(stem+'hypot-snapshots.bin');need(len(snapshots)==4*271012,'Exact complete snapshot byte extent');calls=[]
   for index,(kind,pc)in enumerate(((0,0x7802a122),(1,0x4b58be),(0,0x7802a122),(2,0x4b58e9))):
    raw=snapshots[index*271012:(index+1)*271012];h=words(raw,0,16);cpu=words(raw,64,10);fx=raw[104:616];env=raw[616:644];frame=raw[644:676];stack=raw[676:4772];source_page=raw[4772:8868];crt=raw[8868:];need(len(crt)==64*4096 and h[:5]==(1,index,0x4b5910,kind,pc)and h[7]==0x7802a122 and h[8]==cpu[4]and cpu[9]==pc,'Actual full source CPU/frame/PC occurrence');need(frame==stack[cpu[4]-0x20001000:cpu[4]-0x20001000+32],'Snapshot frame comes from exact full live stack');need(hw(fx)==hw(env) and (hw(fx,2)>>11&7)==(hw(env,4)>>11&7),'Both independently captured hardware views agree on CW/TOP')
    rp=rawdir/f'case-{seq}-boundary-{index}.bin';rp.write_bytes(raw);pin(rp);record=dict(index=index,kind=kind,CPU=list(cpu),header=list(h),FX512_hex=fx.hex(),ENV28_hex=env.hex(),frame32_hex=frame.hex(),whole_stack_hex=stack.hex(),source_page_sha256=hashlib.sha256(source_page).hexdigest(),CRT_page_sha256=[hashlib.sha256(crt[i*4096:(i+1)*4096]).hexdigest()for i in range(64)],raw_snapshot=str(rp),raw_snapshot_sha256=sha(rp),original_provider_postRET_actual=bool(kind),original_before_first_game_instruction=True)
    if not kind:record.update(actual_return_PC=words(frame)[0],actual_F64_arguments_hex=frame[4:20].hex(),actual_F64_arguments=list(struct.unpack('<2d',frame[4:20])))
    else:
     entry=calls[-1];eframe=bytes.fromhex(entry['frame32_hex']);need(cpu[4]==entry['CPU'][4]+4 and entry['actual_return_PC']==pc,'Genuine provider cdecl RET consumes only4B');need(all(cpu[i]==entry['CPU'][i]for i in (3,5,6,7)),'Actual cdecl callee saved registers');need(h[5]==entry['header'][5],'Actual complete cdecl FS head balanced');ret_top=hw(fx,2)>>11&7;need(fx[4]&(1<<ret_top),'Actual returned x87 ST0 tag is nonempty');record.update(actual_return_raw80_hex=fx[32:42].hex(),actual_return_TOP=ret_top,argument_bytes_after_hex=frame[:16].hex(),argument_byte_differences=difference(eframe[4:20],frame[:16]),returned_raw80_is_observation_only=True)
     counts['actual_hypot_calls']+=1;counts['actual_cdecl_RET4_joins']+=1
    calls.append(record);counts['whole_cdecl_CPU_FX_ENV_frame_stack_source_CRT_observations']+=1;counts['whole_cdecl_CRT_pages']+=64
   def image(side,address,n):
    mo=2276 if side=='before'else 178404;offset=mo+pages.index(address&~4095)*4096+(address&4095);return data[offset:offset+n]
   output=[]
   for i,v in enumerate(stores):
    address=0x60b2c8+i*4;value=image('after',address,4);output.append(dict(address=address,source_PC=v['pc'],bytes_hex=value.hex(),F32=struct.unpack('<f',value)[0],observed_only=True));counts['actual_source_F32_publications']+=1
   for p in pages:
    a=image('before',p,4096);b=image('after',p,4096)
    if p==0x20001000:pass # Whole actual stack retained; literal source proof remains separate.
    elif p==0x60b000:
     changes=difference(a,b);allowed=set(range(0x2c8,0x2ec));need(all(v['offset']in allowed for v in changes),'Only nine observed F32 publication cells changed in full game object page')
    else:need(a==b,'Whole unrelated game/provider observation page conserved '+hex(p))
    counts['whole_phase_page_endpoints_retained']+=2
   for i in range(64):
    p=0x78000000+i*4096;a=capture.data(stem+f'hypot-CRT-before/{p}.bin');b=capture.data(stem+f'hypot-CRT-after/{p}.bin');need(len(a)==len(b)==4096,'Both complete actual CRT root endpoint pages');page_rows.append(dict(sequence=seq,page=p,before_sha256=hashlib.sha256(a).hexdigest(),after_sha256=hashlib.sha256(b).hexdigest(),differences=difference(a,b)));counts['whole_CRT_phase_page_endpoints_retained']+=2
   for prefix in('fs-event','lockit','nullfree','vtable'):need(words(capture.data(stem+prefix+'-count.bin'))==(0,),'No unrelated original observer entered')
   need(capture.data(f'cleanup/{seq}/registry.bin')==b'','Actual root registers no callback');rp=rawdir/f'case-{seq}-record.bin';rp.write_bytes(data);pin(rp);rows.append(dict(sequence=seq,repeat=repeat,CW=cw,TOP=top,BEFORE_CPU=list(before),AFTER_CPU=list(after),BEFORE_FX512_hex=fx0.hex(),AFTER_FX512_hex=fx1.hex(),BEFORE_ENV28_hex=env0.hex(),AFTER_ENV28_hex=env1.hex(),BEFORE_stack_hex=image('before',0x20001000,4096).hex(),AFTER_stack_hex=image('after',0x20001000,4096).hex(),BEFORE_object_hex=image('before',0x60b2c8,36).hex(),AFTER_object_hex=image('after',0x60b2c8,36).hex(),outputs=output,calls=calls,raw_record=str(rp),raw_record_sha256=sha(rp),provider_outputs_observed_only=True));counts['actual_root_phases']+=1;counts['whole_root_CPU_FX_ENV_endpoints']+=2;counts['full_host_restoration_relations']+=1
  need(counts['actual_root_phases']==6 and counts['actual_hypot_calls']==12 and counts['whole_cdecl_CPU_FX_ENV_frame_stack_source_CRT_observations']==24 and counts['actual_source_F32_publications']==54,'Complete genuine finite six-case extent');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if capture is not None:capture.close();capture.entries.clear();capture.bundles.clear();capture=None
  for fn,value in(('actual-hypot-endpoints.json',rows),('actual-CRT-page-endpoints.json',page_rows)):
   p=out/fn;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  report=dict(passed=passed,scope='Authentic hardware root and true cdecl finite observations only; literal numerical/source/provider model equivalence remains separate',execution_path=str(path),execution_sha256=digest,counts=dict(counts),source_after_seed=False,numerical_prediction_used=False,provider_preinvoked=False,provider_results_observed_only=True,whole_game_stack_source_proven=False,whole_original_provider_CPU_modeled=False,individual_original_CRT_FS_events_observed=False,source_native_equivalence=False,initializer_credit=0,reader_closed=True,files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
