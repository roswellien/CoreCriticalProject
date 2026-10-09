"""Literal original integer string bodies; static COFF preparation only."""
from concurrent.futures import ThreadPoolExecutor
import ctypes as c,hashlib,importlib.util,json,re,subprocess,sys,time,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from paths import publish_bytes
from manifests import normalized,verify_manifest
BRIDGES={'__remill_read_memory_8','__remill_read_memory_16','__remill_read_memory_32','__remill_read_memory_64','__remill_write_memory_8','__remill_write_memory_16','__remill_write_memory_32','__remill_write_memory_64','__remill_function_call','__remill_function_return','__remill_jump','__remill_missing_block'}
def need(x,w):
 if not x:raise ValueError(w)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main(name):
 started=time.perf_counter();out=ROOT/'reports/m4-strings-native'/name
 need(re.fullmatch('lifts-r[1-9][0-9]*',name) and not out.exists(),'Fresh string lift directory');files={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or v==h,'Pinned literal dependency '+str(p));files[normalized(str(p))]=v;return p
 graphpath=pin(ROOT/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.provider.json','2e7e0fdbf9b673aacc7da13ab1802e44db816db5b1a3d1ec50e2b59bcc12d4f5')
 provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 pe_module=module('strings_physical_pe',pin(ROOT/'tools/m4-crt/recover_provider.py'));pe=pe_module.PE(provider,sha(provider))
 parser=module('strings_operand_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 lifter=pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')
 sem=pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc','618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
 dll=pin(llvm/'LLVM-C.dll','34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
 lower_path=pin(ROOT/'tools/m4-crt-mainargs-recovery/recover.py');text=lower_path.read_text();lower=text[text.index('def lower('):text.index("if __name__ == '__main__':",text.index('def lower('))]
 lower=lower.replace('mw34_mainargs_','mw34_strings_provider_').replace("and '__remill_missing_block' not in text",'')
 sys.path.insert(0,str(ROOT/'tools/lifting'))
 from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
 ns=dict(c=c,re=re,sha=sha,LLVM=LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES);exec(compile(lower,str(lower_path),'exec'),ns)
 upstream_path=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp');upstream=upstream_path.read_text()
 for p in (llvm/'clang.exe',llvm/'llvm-nm.exe',Path(__file__),Path(sys.executable),ROOT/'tools/lifting/host_adapter.py'):pin(p)
 graphs=js(graphpath)['graphs'];inputs=[];contracts={};spans=[]
 for name,entry in [('strdup',0x78010a6d),('strlen',0x78002f32),('strcpy',0x78002fab)]:
  g=graphs[str(entry)];rows=sorted(g['instructions'],key=lambda r:r['pc']);need(len(rows)=={'strdup':23,'strlen':43,'strcpy':51}[name],'Exact local source rows')
  end=max(r['pc']+r['size'] for r in rows);code=bytearray(b'\xcc'*(end-entry));need(len(code)<4096,'Finite sparse local input')
  previous_end=None;span_start=None;span_code=bytearray()
  for r in rows:
   raw=bytes.fromhex(r['bytes']);need(pe.read(r['pc']-pe.base,len(raw))==raw,'Original provider instruction bytes');code[r['pc']-entry:r['pc']-entry+len(raw)]=raw
   value=dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0].strip());contracts[r['pc']]=parser.instruction_contract(value)
   if previous_end is not None and previous_end!=r['pc']:
    spans.append(dict(address=span_start,bytes=len(span_code),sha256=hashlib.sha256(span_code).hexdigest(),permissions=5));span_code=bytearray();span_start=None
   if span_start is None:span_start=r['pc']
   span_code.extend(raw);previous_end=r['pc']+len(raw)
  spans.append(dict(address=span_start,bytes=len(span_code),sha256=hashlib.sha256(span_code).hexdigest(),permissions=5))
  inputs.append((name,entry,bytes(code),len(rows),sum(r['size'] for r in rows)))
 out.mkdir(parents=True);commands=[]
 try:
  def lift(item):
   name,entry,code,row_count,literal_bytes=item;cmds=[];publish_bytes(out/(name+'-source.bin'),code)
   def run(program,args,label):
    argv=[str(program),*map(str,args)];t=time.perf_counter();cp=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000)
    publish_bytes(out/(label+'.stdout'),cp.stdout);publish_bytes(out/(label+'.stderr'),cp.stderr);cmds.append(dict(label=label,argv=argv,exit_code=cp.returncode,seconds=time.perf_counter()-t));need(cp.returncode==0,'Source tool '+label);return cp.stdout
   run(lifter,['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),'--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_pre_out='+str(out/(name+'-pre.ll')),'--ir_out='+str(out/(name+'-guest.ll'))],name+'-lift')
   guest=(out/(name+'-guest.ll')).read_text();calls=[dict(kind='direct',target=int(a,16)) for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',guest,re.M)]
   v=ns['lower'](out,name,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm);v.update(entry=entry,symbol='mw34_strings_provider_'+name+'_body',source_bytes=len(code),literal_source_bytes=literal_bytes,original_rows=row_count,input_sha256=sha(out/(name+'-source.bin')),direct_targets=calls)
   for level,o in v['objects'].items():
    need(Path(o['path']).read_bytes()[:2]==b'\x64\x86','AMD64 literal COFF');o['machine']=0x8664;o['symbol']=v['symbol']
    symbols=re.findall(r'^\s*U\s+(\S+)\s*$',(out/(name+'-undefined-'+level+'.stdout')).read_text(),re.M);need(all(s in v['bridges'] for s in symbols),'Only admitted physical undefined bridges')
   return name,v,cmds
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lift,inputs))
  bodies={n:v for n,v,_ in results}
  for _,_,cmds in results:commands.extend(cmds)
  cb=module('string_callback_recovery',pin(ROOT/'tools/m4-crt-locale-batch-recovery/callbacks.py'));sites={};details={}
  for n,v in bodies.items():
   found,mapping=cb.recover(cb.function((out/(n+'-pre.ll')).read_text(),v['entry']),cb.function((out/(n+'-guest.ll')).read_text(),v['entry']),v['entry'],contracts)
   details[n]=dict(callback_sites=found,source_marker_map=mapping)
   for row in found:
    pc=row['pc'];offsets=row['State_offsets'];need(pc not in sites or sites[pc]==offsets,'Exact callback multiplicity');sites[pc]=offsets
  publish_bytes(out/'instruction-contracts.json',(json.dumps(dict(instructions=[contracts[p] for p in sorted(contracts)],new_spans=spans),indent=2)+'\n').encode())
  publish_bytes(out/'callbacks.json',(json.dumps(dict(bodies=details,State_offsets_by_original_PC={str(pc):v for pc,v in sorted(sites.items())}),indent=2)+'\n').encode())
  for p in out.iterdir():
   if p.is_file():pin(p)
  objects={o['path']:o['sha256'] for v in bodies.values() for o in v['objects'].values()}
  report=dict(schema='mw34-strings-provider-lifts-v1',passed=True,scope='Source-only original bytes, exact sparse lift, and physical AMD64 COFFs; no native/provider API execution or acceptance',source_bodies=bodies,entry_objects=objects,instruction_contracts_sha256=sha(out/'instruction-contracts.json'),callbacks_sha256=sha(out/'callbacks.json'),original_rows=117,literal_source_bytes=312,sparse_holes_excluded_from_identity=True,native_executed=False,native_component_executed=False,roots_admitted=0,commands=commands,files=files,physical_closure=verify_manifest(files),seconds=time.perf_counter()-started)
  publish_bytes(out/'report.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode());print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),physical_objects=len(objects))))
 except Exception:publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
if __name__=='__main__':main(sys.argv[1])
