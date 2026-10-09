"""Compare all actual hardware outputs with raw native outputs and preservation."""
import argparse,hashlib,json,mmap,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[2];N=65536;HS=2176;NS=8120;CW=2768
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,why):
 if not v:raise ValueError(why)
def w(b,o=0):return struct.unpack_from('<H',b,o)[0]
def initial_state(fx,env):
 s=bytearray((i*13+7)&255 for i in range(3504));s[2736:2760]=bytes(24);s[CW:CW+512]=fx
 s[CW+6:CW+24]=bytes(18)
 struct.pack_into('<H',s,CW+6,w(env,18));s[CW+8:CW+12]=env[12:16];s[CW+12:CW+14]=env[16:18];s[CW+16:CW+20]=env[20:24];s[CW+20:CW+22]=env[24:26]
 # Public State AddressSpace: six volatile uint64/Reg pairs. Only low DWORD
 # of SS/FS/DS changed by replay; hidden high DWORD/padding stays dense.
 for offset,value in ((2112+8,0),(2112+56,0x7ffde000),(2112+72,0)):struct.pack_into('<I',s,offset,value)
 return bytes(s)
def hardware(row,index,repeat):
 need(len(row)==HS,'Hardware record extent');tag=struct.unpack_from('<4I',row);need(tag[0]==repeat and tag[1]==index and tag[3]==0 and tag[2]<65536,'Hardware actual ordered input/status')
 fx0=row[16:528];fx1=row[528:1040];env0=row[2064:2092];env1=row[2092:2120]
 need(w(fx0)==0x37f and w(fx0,2)==0 and fx0[4]==0 and struct.unpack_from('<I',fx0,24)[0]==0x1f80,'Measured hardware entry domain')
 need(tag[2]==w(fx1)==w(env1),'Hardware independent FNSTCW/FX/ENV agreement');need(fx0[2:]==fx1[2:] and env0[2:]==env1[2:],'Hardware non-CW preservation');need(row[1040:1552]==row[1552:2064] and row[2120:2148]==row[2148:2176],'Hardware host restoration')
 return tag[2],fx0,fx1,env0,env1
def native(row,index,observations,seed):
 need(len(row)==NS,'Native record extent');observed,fx0,fx1,env0,env1=observations
 need(struct.unpack_from('<4I',row)==(0,index,observed,0),'Actual native tag/output differs from hardware')
 s0=row[16:3520];s1=row[3520:7024]
 need(s0==seed,'Complete actual native persistent prestate identity')
 expected=bytearray(seed);struct.pack_into('<H',expected,CW,observed);need(s1==expected,'Complete 3504-byte State except CW preserved')
 need(row[7024:7536]==fx0 and row[7536:8048]==fx1,'Separate 512-byte FX differential')
 need(row[8048:8076]==env0 and row[8076:8104]==env1,'Separate 28-byte legacy metadata differential')
 need(row[8104:8112]==struct.pack('<Q',0xffeeddcc0000bbaa|(index<<16)),'Exact8-byte guest memory input')
 need(row[8112:8120]==struct.pack('<Q',0xffee00000000bbaa|(index<<16)|(observed<<32)),'Exact2-byte store plus all other guest bytes preservation')
def corruptions(row,observations,seed):
 controls=[]
 for name,offset in [('tag',0),('input',4),('observed',8),('required-fault',12),('prestate-CPU',16+2208),('after-CPU',3520+2208),('prestate-CW',16+CW),('after-CW',3520+CW),('after-State-FOP',3520+CW+6),('after-State-FS',3520+2112+56),('FX-before',7024),('FX-after-CW',7536),('FX-after-SW',7538),('FX-after-tags',7540),('FX-after-MXCSR',7536+24),('FX-after-metadata',7542),('legacy-before',8048),('legacy-CW',8076),('legacy-FIP',8088),('legacy-FOP',8094),('legacy-FDP',8096),('memory-before',8104),('memory-after-owned',8116),('memory-after-unowned',8119),('hidden-State',3520+3400)]:
  b=bytearray(row);b[offset]^=1
  try:native(b,0,observations,seed)
  except ValueError as e:controls.append({'name':name,'rejected':True,'diagnostic':str(e)});continue
  raise ValueError('Observer accepted '+name)
 for start,name in ((3520+CW+32,'State-raw80'),(7536+32,'FX-raw80'),(3520+CW+160,'State-XMM'),(7536+160,'FX-XMM')):
  for i in range(8):
   b=bytearray(row);b[start+16*i]^=1
   try:native(b,0,observations,seed)
   except ValueError as e:controls.append({'name':name+'-'+str(i),'rejected':True,'diagnostic':str(e)});continue
   raise ValueError('Observer accepted '+name)
 return controls
def main(run,out):
 m=json.loads(run.read_text());need(m['passed'] and len(m['actual_controls'])==14,'Actual complete native control report');need(not out.exists() and out.is_relative_to(ROOT/'reports/m4-guest-cw'),'Fresh private comparison')
 hp=pathlib.Path(m['hardware_path']);need(sha(hp)==m['hardware_sha256']=='a31f18e7960db0caba66c63cfd949ba776e08b33564f17d7a0bd2918574801b4','Actual hardware source identity');controls=[]
 with hp.open('rb') as hf,mmap.mmap(hf.fileno(),0,access=mmap.ACCESS_READ) as h:
  need(len(h)==24+2*N*HS and h[:8]==b'MW4CW001' and struct.unpack_from('<4I',h,8)==(1,2*N,HS,N),'Hardware raw header')
  for repeat,level in enumerate(('O0','O2')):
   p=pathlib.Path(m['raws'][level]['path']);need(sha(p)==m['raws'][level]['sha256'],'Actual native raw identity')
   with p.open('rb') as nf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as n:
    need(len(n)==24+N*NS and n[:8]==b'MW4GCW01' and struct.unpack_from('<4I',n,8)==(1,N,NS,CW),'Native raw header/layout')
    seed=None
    for i in range(N):
     hr=h[24+(repeat*N+i)*HS:24+(repeat*N+i+1)*HS];nr=n[24+i*NS:24+(i+1)*NS];obs=hardware(hr,i,repeat)
     if seed is None:seed=initial_state(obs[1],obs[3])
     native(nr,i,obs,seed)
     other=h[24+((1-repeat)*N+i)*HS:24+((1-repeat)*N+i+1)*HS];need(hr[4:1040]==other[4:1040] and hr[2064:2120]==other[2064:2120],'Hardware exact guest repeat')
    controls+=corruptions(n[24:24+NS],hardware(h[24+repeat*N*HS:24+(repeat*N+1)*HS],0,repeat),seed)
 out.mkdir(parents=True);report={'passed':True,'scope':'Actual hardware versus native empty-state CW transfer only; numerical/provider integration pending','run_path':str(run),'run_sha256':sha(run),'actual_hardware_records':2*N,'native_records':2*N,'all_input_words_per_optimization':N,'optimizations':['O0','O2'],'differences':0,'complete_State_bytes':3504,'separate_FX_bytes':512,'separate_legacy_ENV_bytes':28,'guest_memory_bytes':8,'observer_controls':controls,'actual_worker_controls':14,'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):sha(p) for p in [run,hp,pathlib.Path(__file__),out/'report.json']+[pathlib.Path(m['raws'][k]['path']) for k in ('O0','O2')]}},indent=2)+'\n');print('131072 actual differential records passed;',len(controls),'observer corruptions rejected')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('run',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);v=a.parse_args();main(v.run.resolve(),v.output.resolve())
