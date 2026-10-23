"""Exact current Mech3Msg sorter/helper Remill lifts, O0/O2 COFF only.

No target DLL, generated object or worker is loaded/executed. Existing reviewed
host-layout lowering is reused without relaxing missing-block closure.
"""
from pathlib import Path
import ctypes as c,hashlib,json,re,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/lifting'));sys.path.insert(0,str(R/'tools/analysis'))
from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
from pe import PEImage
BRIDGES={'__remill_read_memory_'+x for x in('8','16','32','64')}|{'__remill_write_memory_'+x for x in('8','16','32','64')}|{'__remill_'+x for x in('function_call','function_return','jump','missing_block')}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/literal-sorter-lifts-r1';need(not out.exists(),'Fresh additive literal lift');out.mkdir(parents=True);pins={};commands=[];passed=False;results={};started=time.monotonic()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact pinned literal lift '+str(p));pins[str(p)]=v;return p
 def run(program,args,label):
  argv=[str(program),*map(str,args)];t=time.monotonic();p=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr);commands.append(dict(argv=argv,exit_code=p.returncode,seconds=time.monotonic()-t));need(p.returncode==0,'Literal source tool '+label);return p.stdout
 try:
  physical=R/'reports/m4-loader-message-review/physical-r4';pin(physical/'report.json','138452ce77ef212ca239499794e0aa9e4a6034a64361a70fc71b0896205959e4');g=json.loads(pin(physical/'current-physical-CFG.json').read_bytes());need(g['closures']['sort']['physical_instruction_count']==952 and g['closures']['sort']['dynamic_CFG_closed'],'Exact finite whole sort physical closure');rows={x['pc']:x for x in g['rows']};allpcs=set(g['closures']['sort']['physical_PCs'])
  image=PEImage(pin(R/'MW3/Mech3Msg.dll','8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c').read_bytes())
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';lifter=pin(R/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe');sem=pin(R/'local/tools/remill-x87-control-repair/semantics/x86.bc','618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca');dll=pin(llvm/'LLVM-C.dll');lowerp=pin(R/'tools/m4-crt-mainargs-recovery/recover.py');source=lowerp.read_text();body=source[source.index('def lower('):source.index("if __name__ == '__main__':")].replace('mw34_mainargs_','mw34_message_literal_')
  ns=dict(c=c,re=re,sha=sha,LLVM=LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES);exec(compile(body,str(lowerp),'exec'),ns);upstream=pin(R/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text();covered=set()
  for entry,limit in((0x10001000,0x10001650),(0x10001740,0x10001a60)):
   name='f_'+hex(entry)[2:];pcs=sorted(pc for pc in allpcs if entry<=pc<limit);need(pcs and pcs[0]==entry,'Literal sorter function entry');covered.update(pcs);end=max(pc+rows[pc]['size']for pc in pcs);code=bytearray(b'\xcc'*(end-entry))
   for pc in pcs:
    raw=bytes.fromhex(rows[pc]['bytes']);off=image.rva_range(pc-image.image_base,len(raw))[0];need(image.read(off,len(raw))==raw,'Every authoritative physical sorter instruction');code[pc-entry:pc-entry+len(raw)]=raw
   p=out/(name+'-source.bin');p.write_bytes(code);flags=out/(name+'-lift.flags');flags.write_text('\n'.join(['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),'--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_pre_out='+str(out/(name+'-pre.ll')),'--ir_out='+str(out/(name+'-guest.ll'))])+'\n');run(lifter,['--flagfile='+str(flags)],name+'-lift');guest=(out/(name+'-guest.ll')).read_text();calls=[dict(kind='direct',target=int(a,16))for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',guest,re.M)];need(all(x['target']==0x10001740 for x in calls),'Only literal recursive sorter helper call boundary')
   result=ns['lower'](out,name,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm);result.update(entry=entry,physical_instruction_count=len(pcs),physical_PCs=pcs,source_bytes=len(code),source_sha256=sha(p),direct_calls=calls);results[name]=result
  need(covered==allpcs,'All952 sorter physical instructions assigned exactly two literal functions');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p in [Path(__file__),Path(sys.executable),R/'tools/lifting/host_adapter.py',R/'tools/analysis/pe.py',llvm/'clang.exe',llvm/'llvm-nm.exe']if 'llvm'in locals()else[Path(__file__),Path(sys.executable)]:pin(p)
  for p in out.iterdir():
   if p.is_file():pin(p)
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Exact current Mech3Msg952-instruction sorter/helper literal Remill source lowering and O0/O2 object preparation only',bodies=results,commands=commands,seconds=time.monotonic()-started,REA_status='target_unavailable: no active app; existing local Remill setup reused',source_machine_evaluated=False,native_executed=False,DLL_loaded=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),bodies=len(results))))
if __name__=='__main__':main()
