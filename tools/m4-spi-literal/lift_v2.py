"""Fresh literal SPI root closure, AMD64 Remill objects; no runtime credit."""
from pathlib import Path
import ctypes as c,hashlib,json,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lifting'))
from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
BRIDGES={'__remill_read_memory_32','__remill_write_memory_32','__remill_function_call','__remill_function_return','__remill_jump','__remill_missing_block'}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-spi-literal'/name;need(re.fullmatch('lifts-r[1-9][0-9]*',name) and not out.exists(),'Fresh owned report');out.mkdir(parents=True)
 pins={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Pinned dependency '+str(p));pins[str(p)]=a;return p
 def run(prog,args,label):
  cp=subprocess.run([str(prog),*map(str,args)],capture_output=True,timeout=120,creationflags=0x08000000)
  (out/(label+'.stdout')).write_bytes(cp.stdout);(out/(label+'.stderr')).write_bytes(cp.stderr)
  commands.append(dict(argv=[str(prog),*map(str,args)],exit_code=cp.returncode));need(cp.returncode==0,'Tool failed '+label);return cp.stdout
 try:
  pe=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  graph=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json').read_bytes())[str(0x482cf0)]
  need(len(graph['instructions'])==22 and graph['local_decode_closed'] and not graph['FP_sites'] and not graph['FS_sites'],'Closed exact22sourceinstructions')
  spans=[]
  for start,n in ((0x482cc0,41),(0x482cf0,5),(0x482d00,10)):
   off,_=pe.rva_range(start-pe.image_base,n);b=pe.data[off:off+n];spans.append(dict(start=start,size=n,file_offset=off,sha256=hashlib.sha256(b).hexdigest()))
  lo,hi=0x482cc0,0x482d0a;off,_=pe.rva_range(lo-pe.image_base,hi-lo);code=bytearray(pe.data[off:off+hi-lo])
  covered=set()
  for i in graph['instructions']:
   b=bytes.fromhex(i['bytes']);need(code[i['pc']-lo:i['pc']-lo+len(b)]==b,'Exact original instruction bytes');covered.update(range(i['pc']-lo,i['pc']-lo+len(b)))
  for i in range(len(code)):
   if i not in covered:code[i]=0xcc
  llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
  lifter=pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe');sem=pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc','618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca');dll=pin(llvm/'LLVM-C.dll')
  lowerp=pin(ROOT/'tools/m4-crt-mainargs-recovery/recover.py');source=lowerp.read_text();body=source[source.index('def lower('):source.index("if __name__ == '__main__':")].replace('mw34_mainargs_','mw34_spi_').replace("and '__remill_missing_block' not in text",'')
  rename={'__remill_read_memory_32':'mw34_spi_read32','__remill_write_memory_32':'mw34_spi_write32','__remill_function_call':'mw34_spi_call','__remill_function_return':'mw34_spi_return','__remill_jump':'mw34_spi_jump','__remill_missing_block':'mw34_spi_missing'}
  injection="bridges.add(n)\n            if n in RENAME:\n                renamed=RENAME[n].encode();api.dll.LLVMSetValueName2(fn,renamed,len(renamed));bridges.remove(n);bridges.add(renamed.decode())\n        api.SetFunctionCallConv"
  body=body.replace('bridges.add(n)\n        api.SetFunctionCallConv',injection)
  ns=dict(RENAME=rename,c=c,re=re,sha=sha,LLVM=LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES);exec(compile(body,str(lowerp),'exec'),ns)
  upstream=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text();bodies={}
  # Each external local jump is still dispatched through the source PC ledger.
  for name,entry,n in (('initializer',0x482cf0,5),('thunk',0x482d00,10),('helper',0x482cc0,41)):
   p=out/(name+'-source.bin');p.write_bytes(bytes(code[entry-lo:entry-lo+n]))
   run(lifter,['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),'--bytes='+p.read_bytes().hex(),'--semantics_dir='+str(sem.parent),'--ir_pre_out='+str(out/(name+'-pre.ll')),'--ir_out='+str(out/(name+'-guest.ll'))],name+'-lift')
   txt=(out/(name+'-guest.ll')).read_text();calls=[dict(kind='direct',target=int(a,16))for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',txt,re.M)]
   b=ns['lower'](out,name,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm);b.update(entry=entry,source_bytes=n,source_sha256=sha(p));bodies[name]=b
  for p in (Path(__file__),Path(sys.executable),ROOT/'tools/analysis/pe.py',ROOT/'tools/lifting/host_adapter.py',llvm/'clang.exe',llvm/'llvm-nm.exe'):pin(p)
  for p in out.iterdir():
   if p.is_file():pin(p)
  report=dict(passed=True,scope='Source-only exact SPI closed22instruction graph / 56unique originalbytes, 3literal entries /6AMD64 COFFs',source_spans=spans,graph=graph,source_bodies=bodies,entry_objects={o['path']:o['sha256']for b in bodies.values()for o in b['objects'].values()},callback_rename=rename,State_bytes=3504,FX_bytes=512,CPU_bytes=40,native_executed=False,original_executed=False,whole_M4_complete=False,commands=commands,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
