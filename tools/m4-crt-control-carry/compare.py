"""Author observer for the actual control-to-selected26 persistent sequence."""
import hashlib, importlib.util, json, pathlib, struct, sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-control-carry'
sys.path.insert(0,str(ROOT/'tools/m4-mixed-startup/original'))
import compare_native as mixed
import observe

OS=92388;NS=104808;SEQUENCES=24;PHASES=27;FRAME=0x20001800
RFX0=103468;RFX1=103980;CONTROL_COUNT=104492;CONTROL_EVENTS=104496;RC=104752;RR=104756;INITIAL_CW=104804

def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,w):
 if not v:raise ValueError(w)
def u(b,o,n=1):return struct.unpack_from('<'+str(n)+'I',b,o)
def h(b,o=0):return struct.unpack_from('<H',b,o)[0]
def overlay(s,c,flat=True):return mixed.overlay(s,c,flat)
def initial_state(o,sequence):
 s=bytearray((i*13+sequence+7)&255 for i in range(3504));c=o['before']
 struct.pack_into('<I',s,2120,0);struct.pack_into('<I',s,2168,0x7ffde000);struct.pack_into('<I',s,2184,0)
 s=overlay(s,c);s[2736:2760]=bytes(24);s[2768:3280]=o['fx0'];env=o['env0']
 s[2774:2776]=env[18:20];s[2776:2780]=env[12:16];s[2780:2782]=env[16:18];s[2784:2788]=env[20:24];s[2788:2790]=env[24:26]
 for off,v in [(2090,0x2b),(2106,0x2b),(2110,0x23)]:struct.pack_into('<H',s,off,v)
 for i in range(8):s[2486+16*i:2496+16*i]=o['fx0'][32+16*i:42+16*i];s[16+64*i:32+64*i]=o['fx0'][160+16*i:176+16*i]
 return bytes(s)
def ci_events():
 s=FRAME;p=s-12;q=p-12
 return [(1,0x5ac5a0,s,0x5ac436),(3,0x5ac5d6,p,0x5ac5af),(4,0x1ded8a,p,0x5ac5af),(1,0x780042e1,p,0x5ac5af),(1,0x780042f7,q,0x780042f4),(1,0x7800432c,q-20,0x78004308),(2,0x78004308,q-16,0x78004308),(1,0x7800439f,q-24,0x7800431f),(2,0x7800431f,q-20,0x7800431f),(2,0x780042f4,q+4,0x780042f4),(2,0x5ac5af,p+4,0x5ac5af),(5,0x5ac5af,p+4,0x5ac5af),(2,0x5ac436,s+4,0x5ac436)]
def snapshot_cpu(s):
 c=[mixed.word(s,o) for o in mixed.GPR[:8]];flags=mixed.word(s,2080)&~0xcd5
 for off,bit in mixed.AF:need(s[off] in (0,1),'Boolean native flags');flags|=s[off]<<bit
 return tuple(c+[flags,mixed.word(s,2472)])
def equal_pair(o,n,phase):
 need(o['tag']==n['tag'],'Exact actual carry tags/order')
 before_mask=0xcd5 if phase<=4 else 0xcc5;after_mask=0xcd5 if phase<4 else 0xcc5
 for label,mask in [('before',before_mask),('after',after_mask)]:
  oc=o[label];nc=n[label];need(oc[:8]==nc[:8] and oc[8]&mask==nc[8]&mask,'All actual CPU and defined arithmetic flags '+label)
  need(oc[9]==0x410a80 and nc[9]==0x5ac436 if phase==0 and label=='after' else oc[9]==nc[9],'Literal control-only instrumentation PC projection '+label)
 for key in ('memory0','memory1'):need(o[key]==n[key],'Complete eleven owned pages '+key)
 for ph in ('0','1'):
  a,b=o['fx'+ph],n['fx'+ph]
  need(a[:6]==b[:6] and a[24:]==b[24:],'Complete observed FX architectural/status/raw storage and reserved capability data '+ph)
  need(a[6:24]==bytes(18),'Original hardware FX metadata representation '+ph)
  need(o['env'+ph]==n['env'+ph],'Separate complete original/native legacy ENV '+ph)
 need(observe.host_equal(o['host0'],o['host1'],o['hostenv0'],o['hostenv1']),'Actual original host restoration')
 need(observe.host_equal(n['host0'],n['host1'],n['hostenv0'],n['hostenv1']) and n['host0'][160:416]==n['host1'][160:416],'Actual native full SIMD/legacy host restoration')
def row_check(ob,nb,index,previous,static):
 need(len(ob)==OS and len(nb)==NS,'Exact carry row extent')
 o=observe.fields(ob);n=mixed.native_fields(nb[:103468]);sequence=index//27;phase=index%27;cw=observe.CW[sequence%12]
 need(o['tag'][0:3]==(sequence,sequence//12,phase) and o['tag'][5:]==(cw,0,0,1),'Exact actual24-sequence directed domain')
 equal_pair(o,n,phase)
 need(u(nb,INITIAL_CW)==(cw,),'Exact carried initial CW tag')
 need(u(n['state0'],2796)==u(n['state1'],2796)==(0x2ffff,),'Resident full State capability mask retained')
 for ph,offset in [('0',RFX0),('1',RFX1)]:
  fx,env=mixed.project(n['state'+ph]);expected=bytearray(fx);expected[6:24]=bytes(18)
  need(nb[offset:offset+512]==expected,'Whole separate Runtime FX projection/capability storage '+ph)
  need((fx,env)==(n['fx'+ph],n['env'+ph]),'Exact State software FX/legacy projection '+ph)
  need(snapshot_cpu(n['state'+ph])==n['before' if ph=='0' else 'after'],'Complete State CPU projection '+ph)
 need(n['state0']==(initial_state(o,sequence) if phase==0 else mixed.boundary_state(previous,n)),'Entire3504 persistent State entry seed/carry')
 if not phase:
  need(o['before']==observe.INITIAL+(0x5ac5a0,) and h(o['fx0'])==cw and h(o['fx0'],2)==0 and o['fx0'][4]==0 and u(o['fx0'],24,2)==(0x1f80,0x2ffff),'Actual original initial empty control domain')
  wanted_cw=(cw&~0x300)|0x200;need(h(o['fx1'])==h(o['env1'])==wanted_cw,'Actual original wrapper precision result')
  x=FRAME-8;arith=(1 if FRAME<x else 0)|((FRAME&255).bit_count()%2==0)*4|((x^8^FRAME)&16)|((FRAME==0)<<6)|(((FRAME>>31)&1)<<7)|(bool(~(x^8)&(x^FRAME)&0x80000000)<<11)
  need(o['after'][8]==(o['before'][8]&~0x8d5)|arith,'Actual final wrapper ADD ESP8 defines AF and all arithmetic flags')
  expected=bytearray(overlay(n['state0'],n['after'],False));expected[2768:2770]=o['fx1'][:2]
  need(n['state1']==expected,'Entire3504 control-defined writes and hidden/FS/legacy preservation')
  need(u(nb,CONTROL_COUNT)==(13,) and nb[CONTROL_EVENTS:RC]==b''.join(struct.pack('<4I',*e)for e in ci_events())+bytes(48),'Actual thirteen control CALL/RET/tail phases')
  need(n['counts']==(0,0,0,0,0,0,0,0,1,0) and not any(any(e)for e in n['events']) and n['routes']==[bytes(96),bytes(96)],'No fabricated selected-root observations for control callback')
  need(u(nb,RC)==(2,) and u(nb,RR,12)==(0x5ac431,0x5ac5a0,0x5ac436,0,1,0,0x5ac5aa,0x5bb578,0x5ac5af,1,1,1),'Actual r9 control outer/import routes')
 else:
  need(n['state1']==mixed.expected_state_after(o,n),'Entire3504 actual selected-root writes/protection')
  need(u(nb,CONTROL_COUNT)==(0,) and not any(nb[CONTROL_EVENTS:RC]),'No fabricated control events in later callback')
  need(not mixed.check_events(o,n,static) and not mixed.check_routes(o,n),'Actual complete checked selected-root accesses and compiled call/RET routes')
  before=list(previous['after']);before[4]=FRAME;before[9]=n['tag'][4]
  need(n['before']==tuple(before),'Native genuine preceding CPU carry')
  memory=bytearray(previous['memory1']);struct.pack_into('<I',memory,10*4096+0x800,0x410a80)
  need(n['memory0']==memory,'Whole native page carry except declared single caller return-word framing')
  need(n['fx0']==previous['fx1'] and n['env0']==previous['env1'],'Genuine native software FP/legacy carry')
  need(nb[RFX0:RFX0+512]==previous['runtime_fx_after'],'Genuine whole Runtime FX carry')
  need(h(n['fx0'])==h(previous['fx1'])==((cw&~0x300)|0x200),'Measured control-result CW reaches each numerical/integer entry without injected expectation')
  site=0x5ac436 if phase==1 else 0x410a80
  need(u(nb,RC)==(1,) and u(nb,RR,6)==(site,n['tag'][4],0x410a80,0,1,phase+1) and not any(nb[RR+24:INITIAL_CW]),'Actual selected-root r9 route and sparse ledger')
 n['runtime_fx_after']=nb[RFX1:RFX1+512]
 return n
def main(build_path,out):
 need(not out.exists() and out.is_relative_to(BASE),'Fresh private comparison required');build=read(build_path);need(build['passed'],'Actual both-level carry build required')
 original_report=read(build['original_report_path']);op=pathlib.Path(original_report['raw']['path']);need(sha(op)==original_report['raw']['sha256'],'Exact original observations')
 ob=op.read_bytes();need(ob[:8]==b'MW4CCO01' and u(ob,8,6)==(1,24,27,648,11,OS),'Actual original header')
 extraction=read(ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2/extraction.json');mixed.configure(extraction)
 static=read(ROOT/'reports/m4-startup/next-initializer-410940-events/report.json')['memory_events'];levels=[];all_controls=[];raws=[]
 for level in ('O0','O2'):
  path=build_path.parent/('native-'+level+'.bin');nb=path.read_bytes();need(nb[:8]==b'MW4CCN01' and u(nb,8,6)==(1,24,27,648,11,NS) and len(nb)==32+648*NS,'Complete actual native header/extent');previous=None
  for i in range(648):previous=row_check(ob[32+i*OS:32+(i+1)*OS],nb[32+i*NS:32+(i+1)*NS],i,previous,static)
  locations=[('initial-CW',INITIAL_CW),('State-capability',95892+2796),('RuntimeFX-before-capability',RFX0+28),('RuntimeFX-after-capability',RFX1+28),('State-hidden',95892+3400),('State-FS',95892+2168),('defined-AF',108),('control-thunk-entry',CONTROL_EVENTS+16+4),('control-tail-ESP',CONTROL_EVENTS+32+8),('r9-import-owner',RR+24+4),('r9-import-completed',RR+24+16)]
  for off in range(8):locations.extend([('State-raw80-'+str(off),95892+2486+off*16),('FX-raw80-'+str(off),628+32+off*16),('State-vector-'+str(off),95892+16+off*64)])
  first=ob[32:32+OS];native=nb[32:32+NS]
  for name,offset in locations:
   changed=bytearray(native);changed[offset]^=0x10 if name=='defined-AF' else 1
   try:row_check(first,changed,0,None,static)
   except(ValueError,struct.error)as error:all_controls.append({'level':level,'name':name,'rejected':True,'diagnostic':str(error)});continue
   raise ValueError('Accepted observer corruption '+name)
  levels.append({'level':level,'records':648,'persistent_boundaries':624,'actual_control_callbacks':24,'actual_selected_callbacks':624,'passed':True});raws.append(path)
 out.mkdir();report={'passed':True,'scope':'Author actual control-result CW and complete27-phase selected carry comparison; compiled causal and independent review still required','original_phases':648,'native_phases':1296,'levels':levels,'differences':0,'observer_controls':all_controls,'control_only_original_capture_PC':0x410a80,'control_native_return_PC':0x5ac436,'authored_boundary_return_word':'Only control→firstroot caller frame word changes from5AC436 to410A80; all other full pages persist','temporary_Request_capability_mapping':{'offset':28,'bytes':4,'resident_value':0x2ffff,'validator_copy_value':0,'resident_State_or_Runtime_FX_changed':False},'CW_expected_value_is_not_execution_input':True,'full_ledger_completed':False,'whole_M4_complete':False};rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');paths=[rp,op,build_path,pathlib.Path(__file__),ROOT/'tools/m4-mixed-startup/original/compare_native.py',ROOT/'tools/m4-mixed-startup/original/observe.py']+raws;(out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):sha(p)for p in paths}},indent=2)+'\n');print('648original/1296native full carry phases pass;',len(all_controls),'observer corruptions;',sha(rp))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
