"""Input-derived observer of authored local x64 FLD/FSTP carry unit captures."""
from pathlib import Path
from collections import Counter
import hashlib,itertools,json,mmap,re,struct,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
WORDS=(0x7f7fffff,0,0x80000000,1,0x80000001,0x7fffff,0x800000,0x3f800000,0xbf800000,0x3eaaaaab,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345)
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def raw(i):return struct.pack('<QH',0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0))
def promote(word):
 sign=word>>31;exp=(word>>23)&255;frac=word&0x7fffff;ie=int(exp==255 and frac!=0 and not frac&0x400000);de=int(exp==0 and frac!=0)
 if exp==255:m=(0x800000|frac)<<40;e=0x7fff;m|=0x4000000000000000 if frac else 0
 elif exp:m=(0x800000|frac)<<40;e=exp-127+16383
 elif frac:n=frac.bit_length();m=frac<<(64-n);e=n-1-149+16383
 else:m=e=0
 return struct.pack('<QH',m,e|(sign<<15)),word|(0x400000 if ie else 0),ie,de
def kind(b):
 m,e=struct.unpack('<QH',b);e&=0x7fff
 return 1 if m==0 and e==0 else 2 if e==0x7fff or e==0 or not m>>63 else 0
def tags(top,depth):
 ftw=0;full=0xffff
 for i in range(depth):p=(top+i)&7;ftw|=1<<p;full&=~(3<<(2*p))
 return ftw,full
def check(r,expected_tag,metadata):
 errors=[]
 def eq(label,a,b):
  if a!=b:errors.append(label)
 rep,inp,cw,top,depth,sticky,c1,result,restored=struct.unpack_from('<9I',r)
 eq('exact_authored_case_order',(rep,inp,depth,sticky,cw,top,c1),expected_tag)
 word=WORDS[inp];value,out,ie,de=promote(word);ftw,ft=tags(top,depth);newtop=(top-1)&7;newftw=ftw|(1<<newtop);newft=(ft&~(3<<(newtop*2)))|(kind(value)<<(newtop*2))
 fx=[r[o:o+512] for o in (36,548,1060,1572,2084)];env=[r[o:o+28] for o in (2596,2624,2652,2680,2708)]
 cases=(('before',fx[0],env[0],top<<11|sticky|c1<<9,ftw,ft,[raw(i) for i in range(8)]),('loaded',fx[1],env[1],newtop<<11|sticky|ie|de<<1,newftw,newft,[value]+[raw(i) for i in range(7)]),('stored',fx[2],env[2],top<<11|sticky|ie|de<<1,ftw,ft,[raw(i) for i in range(7)]+[value]))
 for name,x,e,sw,ftw_,ft_,bank in cases:
  eq(name+'_CW_status_tags_MXCSR',(u16(x),u16(x,2),x[4],u32(x,24)),(cw,sw,ftw_,0x1f80))
  eq(name+'_input_derived_all_raw80_observed',[x[32+i*16:42+i*16] for i in range(8)],bank)
  eq(name+'_FX_zero_metadata_observation',x[6:24],bytes(18));eq(name+'_SIMD_seed_projection',x[160:416],bytes(256))
  eq(name+'_ENV_CW_status_fulltags',struct.unpack_from('<3I',e),(0xffff0000|cw,0xffff0000|sw,0xffff0000|ft_))
 eq('original_seed_ENV_metadata',env[0][12:],struct.pack('<4I',0x11223344,0x011d0023,0x55667788,0xffff002b))
 eq('actual_compiled_FLD_FSTP_PC_delta',(u32(env[2],12)-u32(env[1],12))&0xffffffff,metadata['pc_delta'])
 eq('actual_FLD_opcode',u16(env[1],18)&0x7ff,metadata['fld_fop']);eq('actual_FSTP_opcode',u16(env[2],18)&0x7ff,metadata['fstp_fop'])
 eq('actual_host_CS_DS',[(u16(e,16),u16(e,24)) for e in env[1:3]],[(0x33,0x2b)]*2)
 eq('authored_output_from_input',result,out);eq('probe_owned_full_host_FX_restoration',fx[3],fx[4]);eq('probe_owned_full_host_ENV_restoration',env[3],env[4]);eq('actual_restoration_result',restored,1)
 return errors
def main():
 build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.parent==BASE and not out.exists();out.mkdir();bindings={};results=[];controls=[];decodes=[]
 def bind(p,expected=None):
  p=Path(p).resolve();h=sha(p);assert expected is None or h==expected,(str(p),h,expected);bindings[str(p)]=h;return h
 try:
  d=json.loads((build/'build.json').read_text(encoding='utf-8-sig'));assert d['passed'];bind(build/'build.json')
  for key in ('source_files','artifacts','tools'):
   for p,h in d[key].items():bind(p,h)
  llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';bind(llvm/'llvm-objdump.exe');bind(llvm/'llvm-readobj.exe');bind(sys.executable)
  for level in ('O0','O2'):
   obj=Path(d['build_directories'][level])/'CMakeFiles/mw34_nmx_carry_probe.dir/probe.cpp.obj';bind(obj);dis=out/f'probe-{level}-disassembly.txt';args=[str(llvm/'llvm-objdump.exe'),'-d',str(obj)];p=subprocess.run(args,capture_output=True,timeout=60);assert p.returncode==0;dis.write_bytes(p.stdout);bind(dis)
   ins=[]
   for line in p.stdout.decode().splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)(.*)$',line)
    if m and m[3].split() and m[3].split()[0] in ('flds','fstps'):ins.append((int(m[1],16),bytes.fromhex(m[2]),m[3].split()[0]))
   assert len(ins)==2 and [x[2] for x in ins]==['flds','fstps'],ins
   def fop(b):
    if 0x40<=b[0]<=0x4f:b=b[1:]
    assert b[0]==0xd9;return ((b[0]&7)<<8)|b[1]
   metadata={'pc_delta':ins[1][0]-ins[0][0],'fld_fop':fop(ins[0][1]),'fstp_fop':fop(ins[1][1])};decodes.append({'level':level,'object':str(obj),'metadata':metadata,'exact_instructions':[(hex(a),b.hex(),op) for a,b,op in ins]})
   path=build/f'hardware-{level}.bin';bind(path)
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
    assert m[:8]==b'MW4NMC01' and struct.unpack_from('<4I',m,8)==(1,18432,2736,0) and len(m)==24+18432*2736
    schedule=itertools.product(range(2),range(16),(0,1,7),(0,2,32,34),CWS,(0,7),(0,1));fails=Counter();incoming_one=0;PE=0;defined=0
    for i,t in enumerate(schedule):
     r=m[24+i*2736:24+(i+1)*2736];fails.update(check(r,t,metadata));incoming_one+=t[-1];PE+=int(bool(t[3]&32));defined+=int(((WORDS[t[1]]>>23)&255)!=255)
    assert i==18431
    results.append(dict(level=level,records=18432,failures=dict(fails),incoming_C1_one_records=incoming_one,incoming_PE_records=PE,finite_FLDC1_source_defined_records=defined,all_FLD_nooverflow_C1_architectural=18432,final_FSTP_C1_defined_credit=0))
    r=m[24:24+2736];t=(0,0,0,0,0x7f,0,0)
    for off in (0,4,28,32,36,38,40,36+24,36+32,548+2,548+4,548+32,1060+2,1060+32,2596+8,2624+8,2624+18,2652+12,2680+12,2084+33):
     q=bytearray(r);q[off]^=1;e=check(q,t,metadata);assert e,(level,off);controls.append(dict(level=level,offset=off,rejected_by=e))
  remill=ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/lib/Arch/X86/Semantics/X87.cpp';bind(remill)
  text=remill.read_text();start=text.index('DEF_FPU_SEM(FLD,');end=text.index('DEF_FPU_SEM(FLDfromstack',start);assert 'state.sw.c1' not in text[start:end]
  bind(__file__);(out/'observer-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'observer-source.py')
  report=dict(passed=not any(x['failures'] for x in results),scope='Authored local x64 hardware unit only; no original process/code or shared Runtime gate acceptance',results=results,negative_controls=controls,compiled_instruction_evidence=decodes,manual=dict(url='https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf',checked_date='2026-10-07',FLD='PDF454 / vol2A3-353: both modes; C1 zero without overflow; C0/C2/C3 undefined',FSTP='PDF488 / vol2A3-387: rounding-direction C1 applies to a newly generated precision exception; incoming sticky PE is not proof of new inexact rounding'),source_defect='Frozen Remill FLD source does not update shadow C1; standalone gated domain admitted incomingC1zero only',provenance='FX/ENV actual host64 numeric captures; ENV instruction delta/FOP matched compiled object, absolute ASLR module base not emitted; not guest-PC metadata',raw80='All values independently derived from source bits; empty/dead storage is observed only',host_scope='Single authored asm probe restores its own caller context and captures afterward. Does not prove Session/Runtime restoration',original_executed=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],results=results,controls=len(controls),bindings=len(bindings))));assert report['passed']
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-observer-source.py').write_bytes(Path(__file__).read_bytes());raise
if __name__=='__main__':main()
