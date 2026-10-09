"""Author offline observer; does not execute a worker or import fixture/executor helpers."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
COUNT=1536;OS=26836;NS=33964;FRAME=0x200017fc;RET=0x5ac42e;ENTRY=0x7800b38f
CWS=[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f]
ARGS=[0,0x51e7b0,0xffffffff,0x10000001,0x30000000,0x7800b38f,0x80000000,0x12345678]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v):struct.pack_into('<I',b,o,v)
def need(ok,msg):
 if not ok:raise AssertionError(msg)
def common(r):
 return {'tag':words(r,0,5),'before':list(words(r,20,10)),'after':list(words(r,60,10)),
 'fx':[bytes(r[100+i*512:612+i*512]) for i in range(4)],
 'env':[bytes(r[2148+i*28:2176+i*28]) for i in range(4)],
 'memory':[bytes(r[2260+i*12288:14548+i*12288]) for i in range(2)]}
def modeled_state(o):
 i=o['tag'][1];s=bytearray((j*13+i+7)&255 for j in range(3504));fx=o['fx'][0];env=o['env'][0]
 s[2768:3280]=fx
 for dst,src,n in [(2774,18,2),(2776,12,4),(2780,16,2),(2784,20,4),(2788,24,2)]:s[dst:dst+n]=env[src:src+n]
 sw=struct.unpack_from('<H',fx,2)[0]
 for off,bit in [(2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)]:s[off]=(sw>>bit)&1
 for j in range(8):s[2486+16*j:2496+16*j]=fx[32+16*j:42+16*j];s[16+64*j:32+64*j]=fx[160+16*j:176+16*j]
 for off in [2120,2184]:put(s,off,0)
 put(s,2168,0x7ffde000)
 for off,v in zip([2216,2248,2264,2232,2312,2328,2280,2296,2472],o['before'][:8]+[o['before'][9]]):put(s,off,v)
 f=o['before'][8];struct.pack_into('<Q',s,2080,f)
 for off,bit in [(2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)]:s[off]=(f>>bit)&1
 return s
def verify_pair(original,native,index):
 o=common(original);n=common(native);tag=(index//768,index,ARGS[index%8],CWS[(index//64)%12],(index//8)%8)
 need(o['tag']==n['tag']==tag,'Exact schedule')
 need(n['before']==o['before'],'All CPU BEFORE fields')
 oc=o['after'].copy();oc[9]=RET;nc=n['after'].copy();oc[8]&=~0x10;nc[8]&=~0x10
 need(oc==nc,'Paired CPU AFTER with only undefined AF and final capture-PC projection')
 for f in range(2):need(n['fx'][f]==o['fx'][f],'All software/hardware FX512 relational preservation');need(n['env'][f]==o['env'][f],'Separate legacy ENV28 relational preservation');need(n['memory'][f]==o['memory'][f],'All three owned pages')
 need(n['fx'][2]==n['fx'][3] and n['env'][2]==n['env'][3],'Full native host restoration')
 expected=modeled_state(o);need(native[26836:30340]==expected,'Whole State BEFORE independently reconstructed from only original BEFORE inputs')
 put(expected,2216,tag[2]);put(expected,2312,FRAME+4);put(expected,2472,RET)
 for off,v in [(2065,0),(2067,1),(2069,0),(2071,1),(2073,0),(2077,0)]:expected[off]=v
 need(native[30340:33844]==expected,'Whole State AFTER defined mutation and protected bytes')
 cpuafter=o['before'].copy();cpuafter[0]=tag[2];cpuafter[4]=FRAME+4;cpuafter[8]=(cpuafter[8]&~0x8d5)|0x44;cpuafter[9]=RET
 need(n['after']==cpuafter,'Exact native chosen AF-zero policy and full CPU')
 events=[(FRAME+4,tag[2],4,0),(0x780392b8,words(o['memory'][0],4096+0x2b8)[0],4,0),(0x780392b8,0,4,1),(0x7803b0c4,tag[2],4,1),(FRAME,RET,4,0)]
 need([words(native,33844+j*16,4) for j in range(5)]==events,'Actual ordered checked body events')
 need(words(native,33924,6)==(0x5ac428,0x5bb50c,RET,1,1,0),'Same-word typed import orchestration')
 need(words(native,33948,4)==(5,1,1,0),'Actual complete non-faulted owner counters')
def load(p,magic,stride):
 b=p.read_bytes();need(len(b)==24+COUNT*stride and b[:8]==magic and words(b,8,4)==(1,COUNT,stride,12288 if stride==OS else 3504),'Exact stream framing');return b
def main():
 out=Path(sys.argv[1]).resolve();need(not out.exists(),'Fresh comparison directory');out.mkdir(parents=True)
 (out/'observer-source.py').write_bytes(Path(__file__).read_bytes())
 original=ROOT/'reports/m4-crt-matherr/paired-original-r1-normal-windows/original.bin'
 build=ROOT/'reports/m4-crt-matherr/paired-native-build-r7'
 paths=[build/'native-O0.bin',build/'native-O2.bin'];ob=load(original,b'MW4MOR01',OS)
 controls=[];passed=False;failure=None
 try:
  for p in paths:
   nb=load(p,b'MW4MPN01',NS)
   for j in range(COUNT):verify_pair(ob[24+j*OS:24+(j+1)*OS],nb[24+j*NS:24+(j+1)*NS],j)
   first=nb[24:24+NS];oref=ob[24:24+OS]
   # Distinct field mutations, including protected State and software/hardware metadata.
   offsets=[0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76,80,84,88,92,96,
    100,102,104,106,108,110,112,116,120,124,132,260,612,614,616,618,620,622,624,628,632,636,644,772,
    1124,1636,2148,2152,2156,2160,2164,2166,2168,2172,2176,2180,2184,2188,2192,2194,2196,2200,
    2204,2232,2260,4303,4308,6356,7068,10456,10552,14548,16591,16596,18644,19356,22744,22840,
    26836,26836+2065,26836+2067,26836+2069,26836+2075,26836+2080,26836+2216,26836+2312,26836+2486,26836+2768,26836+2774,26836+2776,26836+2784,26836+3280,
    30340,30340+2069,30340+2075,30340+2080,30340+2216,30340+2312,30340+2472,30340+2486,30340+2768,30340+2774,30340+2776,30340+2784,30340+3280]
   offsets+=list(range(33844,33964,4))
   for offset in offsets:
    bad=bytearray(first);bad[offset]^=1;rejected=False
    try:verify_pair(oref,bad,0)
    except AssertionError:rejected=True
    need(rejected,f'Actual observer mutation was not causal offset{offset}');controls.append({'level':p.stem,'offset':offset,'rejected':True})
   # Undefined ORIGINAL AF changes remain allowed; native's chosen State AF must not.
   alternate=bytearray(oref);alternate[92]^=0x10;verify_pair(alternate,first,0);controls.append({'level':p.stem,'original_AF_flip_allowed':True})
  passed=True
 except Exception as e:failure=str(e);(out/'failure.txt').write_text(failure+'\n');raise
 finally:
  report={'passed':passed,'failure':failure,'original_records':1536,'native_records':3072,'events':15360,'routes':3072,'observer_controls':len(controls),'controls':controls,
   'scope':'Offline relational author comparison, native-only execution; original AFTER never an execution input. Only original AND AF undefined and instrumentation capture PC projected; all native State bytes checked. Native software FX/legacy views are distinct from original hardware captures; their exact preservation is proved through complete State and owned FX bytes. No original process/ordinary game/callback execution, independent review pending.'}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files={str(p):sha(p) for p in [Path(__file__),original,*paths,build/'build.json']};files.update({str(p):sha(p) for p in out.iterdir() if p.is_file()});(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n')
 print(json.dumps({'passed':True,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'controls':len(controls)}))
if __name__=='__main__':main()
