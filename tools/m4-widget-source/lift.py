"""Widget exact literal source compilation; no execution or admission."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ctypes as c, hashlib, json, re, subprocess, sys, time, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, checked_state_offsets
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
REC=ROOT/'reports/m4-widget-source/lift-preparation-r1'
REC_SHA='b1778f7359075bae0c6c2afa0f5745b864b481f2e762dce64b385bb16c9a01dd'
BRIDGES={'__remill_read_memory_'+x for x in ('8','16','32','64','f32','f64')}|{'__remill_write_memory_'+x for x in ('8','16','32','64','f32','f64')}|{'__remill_'+x for x in ('function_call','function_return','jump','missing_block','fpu_exception_clear','fpu_exception_test')}|{'mw34_onexit_game_fsqrt_raw80'}
RENAME={x:'mw34_onexit_game_'+x.removeprefix('__remill_').replace('read_memory_','read').replace('write_memory_','write').replace('function_call','call').replace('function_return','return').replace('missing_block','missing').replace('fpu_exception_','fpu_') for x in BRIDGES if x.startswith('__remill_')}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class FPTypes(LLVM):
 def text(self,v):
  p=self.PrintValueToString(v);s=c.string_at(p).decode();self.DisposeMessage(p);return s
 def type_name(self,t):
  kind=self.GetTypeKind(t)
  if kind in (0,2,3,4,14):return {0:'void',2:'float',3:'double',4:'x86_fp80',14:'metadata'}[kind]
  if kind==8:return 'i'+str(self.GetIntTypeWidth(t))
  if kind==12:return 'ptr'
  raise ValueError('Unreviewed boundary type '+str(kind))
def strict_fp(text):
 counts={};declarations=[]
 for op in ('fadd','fsub','fmul','fdiv'):
  pat=rf'^(  %\w+) = {op} x86_fp80 (%\w+), (%\w+)$'
  text,n=re.subn(pat,rf'\1 = call x86_fp80 @llvm.experimental.constrained.{op}.f80(x86_fp80 \2, x86_fp80 \3, metadata !"round.dynamic", metadata !"fpexcept.strict")',text,flags=re.M)
  counts[op]=n
  if n:declarations.append(f'declare x86_fp80 @llvm.experimental.constrained.{op}.f80(x86_fp80, x86_fp80, metadata, metadata)')
 for src,ty in (('f32','float'),('f64','double')):
  pat=rf'^(  %\w+) = fpext {ty} (%\w+) to x86_fp80$'
  text,n=re.subn(pat,rf'\1 = call x86_fp80 @llvm.experimental.constrained.fpext.f80.{src}({ty} \2, metadata !"fpexcept.strict")',text,flags=re.M);counts['extend_'+src]=n
  if n:declarations.append(f'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.{src}({ty}, metadata)')
  pat=rf'^(  %\w+) = fptrunc x86_fp80 (%\w+) to {ty}$'
  text,n=re.subn(pat,rf'\1 = call {ty} @llvm.experimental.constrained.fptrunc.{src}.f80(x86_fp80 \2, metadata !"round.dynamic", metadata !"fpexcept.strict")',text,flags=re.M);counts['truncate_'+src]=n
  if n:declarations.append(f'declare {ty} @llvm.experimental.constrained.fptrunc.{src}.f80(x86_fp80, metadata, metadata)')
 pat=r'^(  %\w+) = fcmp (ueq|oeq|olt|ult|ogt|ugt|uno|ord|une|one|ole|ule|oge|uge) x86_fp80 (%\w+), ([^\n]+)$'
 text,n=re.subn(pat,r'\1 = call i1 @llvm.experimental.constrained.fcmp.f80(x86_fp80 \3, x86_fp80 \4, metadata !"\2", metadata !"fpexcept.strict")',text,flags=re.M);counts['compare']=n
 if n:declarations.append('declare i1 @llvm.experimental.constrained.fcmp.f80(x86_fp80, x86_fp80, metadata, metadata)')
 sqrt_n=0
 def sqrt(m):
  nonlocal sqrt_n
  result,value=m.groups();k=sqrt_n;sqrt_n+=1
  return f'  %onexit.sqrt.in.{k} = alloca x86_fp80, align 16\n  %onexit.sqrt.out.{k} = alloca x86_fp80, align 16\n  store x86_fp80 {value}, ptr %onexit.sqrt.in.{k}, align 16\n  call void @mw34_onexit_game_fsqrt_raw80(ptr %onexit.sqrt.in.{k}, ptr %onexit.sqrt.out.{k})\n  {result} = load x86_fp80, ptr %onexit.sqrt.out.{k}, align 16'
 text,n=re.subn(r'^  (%\w+) = call x86_fp80 @sqrtl\(x86_fp80 noundef (%\w+)\)(?: #\d+)?$',sqrt,text,flags=re.M);counts['sqrt_raw80']=n
 if n:
  text,removed=re.subn(r'^declare (?:dso_local )?x86_fp80 @sqrtl\([^\n]+\n','',text,flags=re.M);need(removed==1,'One original sqrt math declaration');declarations.append('declare void @mw34_onexit_game_fsqrt_raw80(ptr, ptr)')
 text=text.replace('ptr noalias %memory) {','ptr noalias %memory) strictfp {',1)
 return text+'\n'+'\n'.join(declarations)+'\n',counts
def main(name,only='all'):
 out=ROOT/'reports/m4-widget-source'/name;need(re.fullmatch('lifts-r[1-9][0-9]*',name) and not out.exists(),'Fresh source lift output');out.mkdir(parents=True)
 files={};started=time.perf_counter();
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or v==h,'Pinned input '+str(p));files[str(p)]=v;return p
 try:
  pin(REC/'report.json',REC_SHA);graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());roots=json.loads(pin(REC/'fs-roots.json').read_bytes());inputs={}
  pe=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  # All accepted103 bodies remain unchanged; lift17 new literal entries only.
  llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';lifter=pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe');sem=pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc','618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca');dll=pin(llvm/'LLVM-C.dll')
  lowerp=pin(ROOT/'tools/m4-crt-mainargs-recovery/recover.py');s=lowerp.read_text();body=s[s.index('def lower('):s.index("if __name__ == '__main__':")].replace('mw34_mainargs_','mw34_onexit_game_').replace("and '__remill_missing_block' not in text",'')
  body=body.replace("need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32')", "need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32','llvm.fabs.f80','llvm.fabs.f32','llvm.fabs.f64','llvm.memcpy.p0.p0.i32','llvm.memmove.p0.p0.i32','llvm.lifetime.start.p0','llvm.lifetime.end.p0') or n.startswith('llvm.experimental.constrained.')")
  body=body.replace("need(api.IsAFunction(api.GetCalledValue(inst)),'Only named LLVM calls')", "\n                    if not api.IsAFunction(api.GetCalledValue(inst)):\n                        need('call void asm sideeffect \\\"\\\", \\\"~{memory},~{dirflag},~{fpsr},~{flags}\\\"()' in api.text(inst),'Only exact original empty FP ordering barrier');continue")
  injection="bridges.add(n)\n            renamed=(RENAME.get(n) or ('mw34_onexit_game_direct_'+direct[1] if direct else n)).encode()\n            if renamed.decode()!=n:\n                api.dll.LLVMSetValueName2(fn,renamed,len(renamed));bridges.remove(n);bridges.add(renamed.decode())\n        api.SetFunctionCallConv"
  body=body.replace('bridges.add(n)\n        api.SetFunctionCallConv',injection)
  ns=dict(RENAME=RENAME,c=c,re=re,sha=sha,LLVM=FPTypes,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES);exec(compile(body,str(lowerp),'exec'),ns)
  upstream=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
  selected=[g for g in graphs.values() if only=='all' or bool(g.get('FP_sites'))==(only=='fp')]
  def work(g):
   entry=g['entry'];component=f'f_{entry:x}';commands=[]
   need(not g['unresolved_controls'] or (entry==0x5ac210 and {u['pc']for u in g['unresolved_controls']}=={0x5ac24b}), 'Only retained reverse-destructor callback frontier; no admission');need(all('fs:[0x0]' in row['operands'] for row in g['FS_sites']),'Only exact normal FS0 instructions')
   end=max(x['pc']+x['size']for x in g['instructions']);code=bytearray(b'\xcc'*(end-entry))
   for row in g['instructions']:
    if row['pc']<entry:continue # Separately literal lower tail body.
    a=row['pc'];raw=bytes.fromhex(row['bytes']);off,_=pe.rva_range(a-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Every exact original row');code[a-entry:a-entry+len(raw)]=raw
   (out/(component+'-source.bin')).write_bytes(code)
   def run(program,args,label):
    argv=[str(program),*map(str,args)];t=time.perf_counter();p=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr);commands.append(dict(argv=argv,exit_code=p.returncode,seconds=time.perf_counter()-t));need(p.returncode==0,'Source tool '+label);return p.stdout
   flags=out/(component+'-lift.flags');flags.write_text('\n'.join(['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),'--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_pre_out='+str(out/(component+'-pre.ll')),'--ir_out='+str(out/(component+'-guest.ll'))])+'\n')
   run(lifter,['--flagfile='+str(flags)],component+'-lift');guest=out/(component+'-guest.ll');txt=guest.read_text();calls=[dict(kind='direct',target=int(a,16))for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',txt,re.M)]
   baseline=out/(component+'-baseline.ll');baseline.write_text(txt);strict={}
   if g.get('FP_sites'):txt,strict=strict_fp(txt);guest.write_text(txt)
   b=ns['lower'](out,component,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm)
   b.update(entry=entry,symbol='mw34_onexit_game_'+component,source_bytes=len(code),unique_decoded_bytes=sum(x['size']for x in g['instructions']),source_sha256=sha(out/(component+'-source.bin')),instructions=g['instructions'],direct_source_targets=calls,strict_FP= strict,FP_semantic_repairs=False,undefined_calls=len(re.findall(r'call (?:zeroext )?i8 @__remill_undefined_8\(',baseline.read_text())),research_terminal=g.get('research_terminal'))
   print(json.dumps(dict(entry=hex(entry),objects=2,FP=bool(strict))),flush=True);return component,b,commands
  with ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(work,selected))
  bodies={n:b for n,b,_ in results};commands=[row for _,_,rows in results for row in rows]
  manifest=[]
  for b in bodies.values():manifest.append(dict(entry=b['entry'],symbol=b['symbol'],objects=b['objects'],bridges=b['bridges'],undefined_calls=b['undefined_calls'],FP=bool(b['strict_FP']),research_terminal=b['research_terminal']))
  for p in (Path(__file__),Path(sys.executable),ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/analysis/pe.py',llvm/'clang.exe',llvm/'llvm-nm.exe'):pin(p)
  for p in out.iterdir():
   if p.is_file():pin(p)
  report=dict(passed=True,scope='Exact game source/COFF preparation only, no initializer execution credit',recovery_sha256=REC_SHA,source_bodies=bodies,dispatch_manifest=manifest,roots=roots,root_count=5,new_guest_objects=2*len(bodies),entry_objects={o['path']:o['sha256']for b in bodies.values()for o in b['objects'].values()},State_bytes=3504,FX_bytes=512,CPU_bytes=40,callback_rename=RENAME,commands=commands,files=files,native_executed=False,original_executed=False,seconds=time.perf_counter()-started)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),bodies=len(bodies),objects=2*len(bodies))))
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1],sys.argv[2]if len(sys.argv)>2 else'all')
