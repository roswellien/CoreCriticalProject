"""Fresh authentic-loader one-root worker; no archive reader or expected outputs."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-mfc1168-probe'
REC=R/'reports/m4-mfc1168-original/recovery-r2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or v==h,'Physical identity '+str(p));pins[str(p)]=v;return p
 def load(p,tag):
  s=importlib.util.spec_from_file_location(tag,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 rec=json.loads(pin(REC/'report.json').read_bytes());need(rec['passed'],'Pinned recovery2')
 for p,h in rec['files'].items():pin(p,h)
 A=load(R/'tools/m4-service-initializers/recover.py','probe_PE');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','probe_operands')
 modules={k:A.Module(pin(R/p,A.IDENTITIES[p]))for k,p in [('game','MW3/Mech3.exe'),('MFC','local/mw3-staged/Shared_DLLs/MFC42.DLL'),('CRT','local/mw3-staged/Shared_DLLs/MSVCRT.DLL')]}
 g=json.loads(pin(REC/'game-graphs.json').read_bytes());p=json.loads(pin(REC/'provider-graphs.json').read_bytes());rows={}
 for label,graphs in [('game',g),*p.items()]:
  for graph in graphs.values():
   for row in graph['instructions']:
    raw=bytes.fromhex(row['bytes']);m=modules[label];off,_=m.image.rva_range(row['pc']-m.base,len(raw));need(m.image.data[off:off+len(raw)]==raw,'Physical source instruction')
    need(row['pc']not in rows or rows[row['pc']]==dict(row,module=label),'Unique source boundary');rows[row['pc']]=dict(row,module=label)
 regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi'];descriptors=[];gaps=[]
 for pc,row in sorted(rows.items()):
  op=row['mnemonic'];args=row['operands'].split(' <')[0];repeat=None
  if op in ('rep','repe','repz','repne','repnz'):repeat=op;op,args=args.split(None,1)
  n=dict(pc=pc,width=row['size'],bytes_hex=row['bytes'],mnemonic=op,operands=args)
  if repeat:n['repeat']=repeat
  cells=[]
  try:
   c=D.instruction_contract(n)
   for i,v in enumerate(c['decoded_operands']):
    if v['kind']!='memory':continue
    rd=i in c['explicit_memory_reads'];wr=i in c['explicit_memory_writes']
    if not(rd or wr):continue
    bits=v['bits'] or next((x['bits']for x in c['decoded_operands']if x['kind']=='register'),32)
    coef=[0]*8
    for term in v['terms']:coef[regs.index(term['register'])]+=term['scale']
    cells.append(dict(displacement=v['displacement'],coefficients=coef,width=bits//8,read=int(rd),write=int(wr),segment=1 if v['segment']=='fs'else 0))
   for v in c['implicit_memory']:
    coef=[0]*8;kind=v['kind'];write=kind in('stack-write','string-write')
    if kind.startswith('stack'):coef[5 if v['address']=='SSBASE+EBP'else 4]=1;disp=0xfffffffc if write else 0
    else:coef[6 if v['address'].endswith('ESI')else 7]=1;disp=0
    cells.append(dict(displacement=disp,coefficients=coef,width=v['bits']//8,read=int(not write),write=int(write),segment=0))
   if op in('scasb','scasw','scasd','lodsb','lodsw','lodsd','movsb','movsw'):
    width={'b':1,'w':2,'d':4}[op[-1]];coef=[0]*8;coef[7 if op.startswith('scas')else 6]=1
    cells.append(dict(displacement=0,coefficients=coef,width=width,read=1,write=0,segment=0))
    if op.startswith('movs'):coef=[0]*8;coef[7]=1;cells.append(dict(displacement=0,coefficients=coef,width=width,read=0,write=1,segment=0))
   need(len(cells)<=4 and all(0<v['width']<=8 for v in cells),'Bounded trace memory cells')
  except Exception as e:cells=[];gaps.append(dict(pc=pc,mnemonic=op,operands=args,reason=str(e)))
  descriptors.append(dict(**n,module=row['module'],cells=cells,opcode=int(row['bytes'][:2],16)))
 out.mkdir(parents=True)
 # Only exact three physical game pages plus genuine virtual-zero game object.
 pages=[]
 for base in (0x5ae000,0x5ab000,0x5bb000,0x736000):
  image=modules['game'].image;raw=bytearray(4096);sec=modules['game'].section(base)
  for i in range(4096):
   try:off,_=image.rva_range(base+i-modules['game'].base,1);raw[i]=image.data[off]
   except ValueError:pass
  pages.append((base,0x20 if sec['executable']else 4 if sec['writable']else 2,bytes(raw)))
 pack=struct.pack('<8sI',b'MW41168P',len(pages))+b''.join(struct.pack('<II',b,f)+v for b,f,v in pages);(out/'pages.bin').write_bytes(pack)
 (out/'instruction-contracts.json').write_text(json.dumps(dict(instructions=descriptors,descriptor_gaps=gaps),indent=2)+'\n')
 cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
 h='#pragma once\nstruct TraceMemory{unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct TracePoint{unsigned pc,width,opcode,count;TraceMemory cells[4];};\ninline constexpr std::array<TracePoint,'+str(len(descriptors))+'> trace_points{{\n'
 for d in descriptors:h+='{'+','.join(map(str,[d['pc'],d['width'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c)for c in d['cells'])+'}},\n'
 (out/'trace_points.hpp').write_text(h+'}};\n')
 deps=json.loads(pin(REC/'dependencies.json').read_bytes());imports={}
 counts={**D.API_ARGUMENTS,'TlsGetValue':1,'TlsSetValue':2,'TlsAlloc':0,'TlsFree':1,'GlobalAlloc':2,'GlobalReAlloc':3,'GlobalLock':1,'GlobalUnlock':1,'GlobalFree':1,'GlobalSize':1,'LocalAlloc':2,'LocalReAlloc':3,'LocalFree':1,'LocalSize':1,'GetLastError':0,'GetCurrentThreadId':0,'GetVersion':0,'GetVersionExA':1,'GetModuleHandleA':1,'GetProcAddress':2,'InterlockedIncrement':1,'InterlockedDecrement':1,'DeleteCriticalSection':1}
 for mod in modules.values():
  for i,v in mod.imports.items():
   if v.get('name')in counts:imports[i]=dict(iat=i,name=v['name'],argc=counts[v['name']],library=v['library'])
 api='#pragma once\nstruct ApiImport{unsigned iat,argc;const char*name;};\ninline constexpr std::array<ApiImport,'+str(len(imports))+'> api_imports{{\n'+''.join('{'+str(v['iat'])+','+str(v['argc'])+',"'+v['name']+'"},\n'for v in imports.values())+'}};\n'
 (out/'api_imports.hpp').write_text(api);(out/'api-imports.json').write_text(json.dumps(list(imports.values()),indent=2)+'\n')
 template=R/'reports/m4-cosine-original/prefix-preparation-r2'
 protocol=pin(template/'protocol.hpp').read_text();protocol=protocol.replace('sequences=6, roots=1','sequences=1, roots=1');(out/'protocol.hpp').write_text(protocol)
 broker=pin(template/'original_broker.hpp').read_text();a=broker.index('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<');b=broker.index('\n            if(handle_debug_checkpoint',a);broker=broker[:a]+'const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;'+broker[b:];(out/'original_broker.hpp').write_text(broker)
 asm=pin(template/'reference_x86.asm').read_text();a=asm.index('EXTERN spi_service_before:');b=asm.index('.code',a);asm=asm[:a]+asm[b:];a=asm.index('spi_service_entry PROC');asm=asm[:a]+'END\n';(out/'reference_x86.asm').write_text(asm)
 for n in('worker.cpp','trace.hpp','boundaries.asm','CMakeLists.txt'):(out/n).write_bytes(pin(Path(__file__).parent/n).read_bytes())
 for p in out.iterdir():pin(p)
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Authentic single root1168 original probe and separate debugger trace; no expected source outputs or initializer credit',root=0x5ae3e4,root_slot=0x5e0040,game_rows=25,physical_rows=len(rows),trace_descriptors=len(descriptors),descriptor_gaps=gaps,recovery=str(REC/'report.json'),recovery_sha256=sha(REC/'report.json'),pack_sha256=sha(out/'pages.bin'),normal_and_trace_same_worker=True,preinvocation_1168=False,seeded_TLS_or_locale=False,capture_reader_opened=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),rows=len(rows),descriptor_gaps=len(gaps))))
if __name__=='__main__':main(sys.argv[1])
