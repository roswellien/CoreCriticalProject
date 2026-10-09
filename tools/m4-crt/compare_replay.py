"""Compare actual original/native raw CRT results and corrupt each observer layer."""
from pathlib import Path
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[2]
COUNT=1728;OS=18668;NS=17588;MEM=8204;BEGIN=0x20002100;SP=0x20001800;RETURN=0x10000100
CW=(0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f)
CB=(0x10001000,0x10001040,0x10001080,0x100010c0,0x10001100)
ENTRY=(0x780014f8,)*6+(0x78004625,0x7800462f,0x78004635)
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def cpu(b,o):return struct.unpack_from('<10I',b,o)
def tags(i):return (i//864,(i%864)//96,CW[(i%96)//8],i%8,0)
def read_stream(path,magic,stride):
 b=Path(path).read_bytes();need(len(b)==24+COUNT*stride,'Raw exact complete extent');need(b[:8]==magic and struct.unpack_from('<4I',b,8)==(1,COUNT,stride,MEM),'Raw header version/count/stride/memory');return [b[24+i*stride:24+(i+1)*stride] for i in range(COUNT)]
def original_record(o,i):
 repeat,c,cw,top,status=tags(i);need(struct.unpack_from('<5I',o)==tags(i),'Original tag/order/status');need(cpu(o,20)==(0x13579bdf,0x2468ace0,0x81726354,0x10293847,SP,0x92837465,0x56473829,0xaabbccdd,0x202,ENTRY[c]),'Actual original pre-body CPU')
 need(cpu(o,60)[4]==SP+4 and cpu(o,60)[9]==RETURN,'Original actual return PC/ESP');need(all(cpu(o,60)[n]==cpu(o,20)[n] for n in (3,5,6,7)),'Original nonvolatile return')
 f=o[100:612];env=o[2148:2176];need(u16(f,0)==cw and u16(f,2)==top<<11 and f[4]==0 and u32(f,24)==0x1f80,'Original initial CW/TOP/FTW/MXCSR')
 need(f[6:24]==bytes(18),'Measured hardware FX zero metadata');need(u16(env,0)==cw and u16(env,4)==top<<11 and u16(env,8)==0xffff and u32(env,12)==0x11223344 and u16(env,16)==0x23 and u16(env,18)==0x11d and u32(env,20)==0x55667788 and u16(env,24)==0x2b,'Original actual legacy environment metadata')
 for r in range(8):need(f[32+16*r:42+16*r]==bytes((17+r*13+j*7)&255 for j in range(10)),'Actual original nonzero raw80 logical slot '+str(r))
 need(f[160:288]==bytes((j*19+3)&255 for j in range(128)),'Actual original nonzero XMM input');need(o[100:612]==o[612:1124] and o[2148:2176]==o[2176:2204],'Original MOV-only guest FP/ENV preserved')
 need(o[1124:1636]==o[1636:2148] and o[2204:2232]==o[2232:2260],'Actual complete host FX/ENV restoration')
 need(u32(o,2260+0x800)==RETURN and o[2260+8192:2260+8204]==bytes(12),'Original return/global input bytes')
 expected_counter=(12,12,0,0,13,1,0,0,0)[c];after=o[10464:18668];need(u32(after,4096+0x800)==expected_counter,'Actual original authored callback order counter')
 need(u32(after,8192)==(2 if c==6 else 0) and after[8196:8204]==bytes(8),'Original exact provider globals')
 if c==4:need(u32(after,4096+0x104)==CB[2],'Original future slot mutation observed')
 if c==5:need(u32(after,0x808)==BEGIN+4,'Original caller end mutation observed')
 if c==7:need(cpu(o,60)[0]==0x78038eec,'Original stable guest fmode pointer')
 if c==8:need(cpu(o,60)[0]==0x78038ef0,'Original stable guest commode pointer')
 if c>=6:need(cpu(o,60)[8]==0x202,'Original MOV flags unchanged')
def compare_record(o,n,i):
 need(struct.unpack_from('<5I',n)==tags(i),'Native tag/order/status');need(n[20:100]==o[20:100],'Native full CPU before/after');need(n[100:1124]==o[100:1124],'Native complete captured FX before/after');need(n[1124:1180]==o[2148:2204],'Native legacy environment before/after');need(n[1180:17588]==o[2260:18668],'Native exact stack/table/provider globals before/after')
def ledger_record(v,i):
 c=tags(i)[1];need(v['ordinal']==i and v['case']==c and v['opaque_bytes_unchanged']==3504,'Native record/complete State check')
 targets=((0,CB[0],CB[1],0),(CB[0],CB[1]),(),(),(CB[3],CB[2]),(CB[4],),(),(),())[c]
 need(v['visits']==[{'slot':BEGIN+4*n,'target':target,'status':2 if target else 0} for n,target in enumerate(targets)],'Native ordered reached-slot ledger')
 slot=(0x5bb510,)*6+(0x5bb5a4,0x5bb57c,0x5bb504)
 expected=[{'site':0x10000080,'target':slot[c],'return':RETURN,'completed':True}]+[{'site':0x7800150e,'target':t,'return':0x78001510,'completed':True} for t in targets if t]
 need(v['calls']==expected,'Native actual service/callback site/return/completion ledger')
def controls(original,native,ledger):
 result=[]
 def denial(name,fn):
  try:fn()
  except (ValueError,KeyError,struct.error) as e:result.append({'name':name,'rejected':True,'diagnostic':str(e)});return
  raise ValueError('Observer accepted corruption '+name)
 for name,offset in [('original-tag',4),('original-cw',100),('original-top',103),('original-ftw',104),('original-cpu',20),('original-return-sp',76),('original-return-pc',96),('original-env-fip',2160),('original-env-fop',2166),('original-env-fdp',2168),('original-host-cw',1636),('original-host-env',2232),('original-host-raw80',1668),('original-host-xmm',1796),('original-order-counter',10464+4096+0x800)]:
  b=bytearray(original[0]);b[offset]^=1;denial(name,lambda b=b:original_record(b,0))
 for r in range(8):
  b=bytearray(original[0]);b[132+16*r]^=1;denial('original-raw80-'+str(r),lambda b=b:original_record(b,0))
 for name,offset in [('native-tag',4),('native-before-eax',20),('native-after-eax',60),('native-after-esp',76),('native-after-esi',84),('native-after-flags',92),('native-after-pc',96),('native-cw',612),('native-top',615),('native-ftw',616),('native-mxcsr',636),('native-env-cw',1152),('native-env-top',1156),('native-env-tags',1160),('native-env-fip',1164),('native-env-fop',1170),('native-env-fdp',1172),('native-env-fcs',1168),('native-env-fds',1176),('native-stack-ret',9384+0x800),('native-table-before',1180+4096+0x100),('native-counter-after',9384+4096+0x800),('native-globals-after',9384+8192)]:
  b=bytearray(native[0]);b[offset]^=1;denial(name,lambda b=b:compare_record(original[0],b,0))
 for r in range(8):
  b=bytearray(native[0]);b[644+16*r]^=1;denial('native-raw80-'+str(r),lambda b=b:compare_record(original[0],b,0))
 for name,field in [('ledger-target','target'),('ledger-callsite','site'),('ledger-return','return'),('ledger-incomplete','completed')]:
  v=json.loads(json.dumps(ledger[0]));v['calls'][1][field]=False if field=='completed' else v['calls'][1][field]^4;denial(name,lambda v=v:ledger_record(v,0))
 v=json.loads(json.dumps(ledger[0]));v['visits'][1]['slot']^=4;denial('ledger-reordered-slot',lambda:ledger_record(v,0))
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--original-report',required=True);p.add_argument('--native-report',required=True);p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve();need(out.is_relative_to(ROOT/'reports/m4-crt') and not out.exists(),'Fresh comparison report required');op=Path(a.original_report).resolve();np=Path(a.native_report).resolve();om=json.loads(op.read_text());nm=json.loads(np.read_text());need(om['passed'] and nm['passed'],'Actual worker/control reports passed');original=read_stream(om['original']['path'],b'MW4CRO01',OS);out.mkdir(parents=True);passed=False;failure=None;observers=[];streams=[]
 try:
  for i,o in enumerate(original):original_record(o,i)
  for i in range(864):need(original[i][20:1124]+original[i][2148:2204]+original[i][2260:]==original[i+864][20:1124]+original[i+864][2148:2204]+original[i+864][2260:],'Exact repeated guest observations')
  for s in nm['streams']:
   native=read_stream(s['raw']['path'],b'MW4CRN01',NS);ledger=json.loads(Path(s['ledger']['path']).read_text())['records'];need(len(ledger)==COUNT,'Complete native ledger')
   for i,(o,n,v) in enumerate(zip(original,native,ledger)):compare_record(o,n,i);ledger_record(v,i)
   controls_result=controls(original,native,ledger);observers.extend({'level':s['level'],**x} for x in controls_result);streams.append({'level':s['level'],'raw':s['raw'],'ledger':s['ledger'],'matched_records':COUNT,'differences':0,'observer_controls':len(controls_result)})
  need(streams[0]['raw']['sha256']==streams[1]['raw']['sha256'],'Bitwise O0/O2 native output agreement');passed=True
 except Exception as e:failure=str(e);raise
 finally:
  report={'passed':passed,'failure':failure,'scope':'Four recovered CRT provider bodies on authored callbacks only; actual game initializer integration and full CRT/startup/menu remain open','original_report':bind(op),'native_report':bind(np),'source':bind(__file__),'original':om['original'],'original_records':COUNT,'exact_guest_repeats':864,'native_records':2*COUNT,'streams':streams,'observer_controls':observers,'actual_worker_controls':18,'comparison_fields':'All 10 CPU DWORDs, full captured FX512, separate legacy ENV28, every owned stack/table/global byte, actual native ordered visit/call ledger','input_policy':'Native reads original pre-body CPU/FX/ENV/memory only; never original after fields as expected outputs','legacy_policy':'Measured Windows FX metadata is zero; native legacy fields are seeded and captured separately in persistent Remill State; all physical tags empty, all TOPs, nonzero raw80/XMM storage','original_event_trace':False,'limits':['Four measured staged-provider functions; actual host provider selection unobserved','No game code executed; callback code is authored fixture, not game slots','No DLL loading/import resolution/DllMain/SEH dispatch or full 144-initializer ordering','Native opaque State preservation is a separately checked invariant; no original Remill State exists','Mask/unmasked/occupied x87 arithmetic domains and callback exceptions unresolved','Single-thread fresh private ordinary-directory worker scope; no concurrent publisher promise'],'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[op,np,Path(__file__),Path(om['original']['path']),*(Path(x['raw']['path']) for x in nm['streams']),*(Path(x['ledger']['path']) for x in nm['streams']),out/'report.json'];(out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):sha(x) for x in files}},indent=2)+'\n')
 print('1728 original / 3456 native CRT records matched; '+str(len(observers))+' observer corruptions rejected')
if __name__=='__main__':main()
