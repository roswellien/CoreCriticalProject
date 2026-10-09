"""Raw exhaustive CW observations, bit mapping, restoration and corruption checks."""
from pathlib import Path
import argparse,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[2];COUNT=131072;STRIDE=2176
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def need(ok,why):
 if not ok:raise ValueError(why)
def word(b,o):return struct.unpack_from('<H',b,o)[0]
def record(b,i):
 repeat,input,observed,status=struct.unpack_from('<4I',b);need((repeat,input)==(i//65536,i%65536),'Exact exhaustive input/repeat order');need(status==0,'Hardware rejected exact requested word; no reset/success admission');need(observed<=65535,'Actual FNSTCW word width')
 before=b[16:528];after=b[528:1040];env_before=b[2064:2092];env_after=b[2092:2120]
 need(word(before,0)==0x37f and word(before,2)==0 and before[4]==0 and struct.unpack_from('<I',before,24)[0]==0x1f80,'Actual CW transfer input CW/SW/FTW/MXCSR')
 need(before[6:24]==bytes(18),'Observed hardware FX metadata representation');need(word(env_before,0)==0x37f and word(env_before,4)==0 and word(env_before,8)==0xffff and struct.unpack_from('<I',env_before,12)[0]==0x11223344 and word(env_before,18)==0x11d and struct.unpack_from('<I',env_before,20)[0]==0x55667788,'Actual nonzero legacy input metadata')
 for r in range(8):need(before[32+16*r:42+16*r]==bytes((17+r*13+j*7)&255 for j in range(10)),'Actual raw80 input slot '+str(r))
 need(before[160:288]==bytes((j*19+3)&255 for j in range(128)),'Actual nonzero XMM input')
 need(observed==word(after,0)==word(env_after,0),'Independent actual FNSTCW/FXSAVE/FNSTENV CW agreement');need(before[2:]==after[2:],'All captured non-CW guest FX bytes preserved');need(env_before[2:]==env_after[2:],'All captured non-CW legacy bytes preserved');need(b[1040:1552]==b[1552:2064] and b[2120:2148]==b[2148:2176],'Full actual host FX/ENV restoration');return observed
def corruptions(sample):
 results=[]
 def deny(name,b):
  try:record(b,0)
  except (ValueError,struct.error) as e:results.append({'name':name,'rejected':True,'diagnostic':str(e)});return
  raise ValueError('Observer accepted corruption '+name)
 for name,offset in [('repeat',0),('input',4),('FNSTCW',8),('hardware-status',12),('guest-before-CW',16),('guest-before-SW',18),('guest-before-FTW',20),('guest-after-CW',528),('guest-after-SW',530),('guest-after-FTW',532),('guest-after-mxcsr',552),('guest-after-FOP',534),('guest-after-FIP',536),('guest-after-FDP',544),('guest-env-CW',2092),('guest-env-SW',2096),('guest-env-tags',2100),('guest-env-FIP',2104),('guest-env-FCS',2108),('guest-env-FOP',2110),('guest-env-FDP',2112),('guest-env-FDS',2116),('host-CW',1552),('host-SW',1554),('host-FTW',1556),('host-mxcsr',1576),('host-ENV-CW',2148),('host-ENV-FIP',2160),('host-ENV-FOP',2166),('host-ENV-FDP',2168)]:
  b=bytearray(sample);b[offset]^=1;deny(name,b)
 for kind,start in [('guest-raw80',560),('guest-XMM',688),('host-raw80',1584),('host-XMM',1712)]:
  for r in range(8):b=bytearray(sample);b[start+16*r]^=1;deny(kind+'-'+str(r),b)
 return results
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);a=p.parse_args();run=Path(a.run).resolve();out=Path(a.out).resolve();need(out.is_relative_to(ROOT/'reports/m4-crt-cw') and not out.exists(),'Fresh private CW analysis');m=json.loads(run.read_text());need(m['passed'] and m['records']==COUNT and m['actual_causal_controls']==5,'Actual complete CW worker/control report');raw=Path(m['raw']['path']);need(sha(raw)==m['raw']['sha256'],'Exact original raw identity');b=raw.read_bytes();need(len(b)==24+COUNT*STRIDE and b[:8]==b'MW4CW001' and struct.unpack_from('<4I',b,8)==(1,COUNT,STRIDE,65536),'Exact CW raw header/extent');values=[];view=memoryview(b)
 for i in range(COUNT):values.append(record(view[24+i*STRIDE:24+(i+1)*STRIDE],i))
 for i in range(65536):
  x=view[24+i*STRIDE:24+(i+1)*STRIDE];y=view[24+(i+65536)*STRIDE:24+(i+65537)*STRIDE];need(values[i]==values[i+65536] and x[16:1040]==y[16:1040] and x[2064:2120]==y[2064:2120],'Exact repeated guest CW/physical/legacy observation')
 keep=ones=zeros=0;nonlinear=[]
 for bit in range(16):
  mask=1<<bit;outputs=[bool(x&mask) for x in values[:65536]]
  if all(y==bool(x&mask) for x,y in enumerate(outputs)):keep|=mask
  elif all(outputs):ones|=mask
  elif not any(outputs):zeros|=mask
  else:nonlinear.append(bit)
 need(not nonlinear and all(y==(x&keep)|ones for x,y in enumerate(values[:65536])),'Complete observed Boolean CW normalization policy');controls=corruptions(view[24:24+STRIDE]);out.mkdir(parents=True);table=out/'measured-cw-map.bin';table.write_bytes(struct.pack('<65536H',*values[:65536]));report={'passed':True,'scope':'Authored original hardware CW transfer research only; no vendor/game body or native bridge/provider equivalence','run':bind(run),'raw':bind(raw),'source':bind(__file__),'measured_map':bind(table),'records':COUNT,'all_16bit_inputs':65536,'exact_guest_repeats':65536,'hardware_faults':0,'normalization':{'keep_mask':keep,'forced_one_mask':ones,'forced_zero_mask':zeros,'nonlinear_bits':nonlinear,'formula':'(requested_word & 0x%04X) | 0x%04X'%(keep,ones),'all_actual_input_rows_verified':True,'claim':'Measured on this host in empty-tag, zero-exception x87 state; no universal CPU or arithmetic behavior claim'},'actual_host_restoration_records':COUNT,'guest_non_CW_FX_and_legacy_preservation_records':COUNT,'actual_worker_controls':5,'observer_controls':controls,'limits':['TOP0 only; empty physical tags, nonzero raw80/XMM storage, SW0, guestMXCSR1F80','Every exact16-bit input was loaded once per repeat; no unsupported bit reset or retry before hardware capture','Reserved PC transfers observed; arithmetic with reserved precision and unmasked pending exceptions remains unresolved','No host-loaded provider identity, original CRT execution, native bridge, initializer/menu or fullM4 acceptance'],'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');paths=[run,raw,Path(__file__),table,out/'report.json'];(out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):sha(x) for x in paths}},indent=2)+'\n');print(COUNT,'records passed; normalization',report['normalization']['formula'],';',len(controls),'observer corruptions rejected')
if __name__=='__main__':main()
