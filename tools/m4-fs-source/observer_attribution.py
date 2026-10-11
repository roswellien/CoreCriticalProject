"""Independently bind every compiled x86 FS observer to its exact source MOV."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def parse_coff(data):
 machine,count,_,symoff,n,optional,_=struct.unpack_from('<HHIIIHH',data)
 need(machine==0x14c and optional==0,'Physical i386 COFF')
 strings=symoff+n*18;end=strings+struct.unpack_from('<I',data,strings)[0];need(end<=len(data),'Bounded COFF strings');symbols={};i=0
 while i<n:
  a,value,sec,typ,storage,aux=struct.unpack_from('<8sIhHBB',data,symoff+i*18)
  if a[:4]==b'\0'*4:
   pos=strings+struct.unpack_from('<I',a,4)[0];need(strings+4<=pos<end,'COFF long name');name=data[pos:data.index(b'\0',pos,end)].decode('ascii')
  else:name=a.rstrip(b'\0').decode('ascii')
  symbols[i]=dict(name=name,value=value,section=sec,type=typ,storage=storage);i+=1+aux
 sections={}
 for k in range(count):
  o=20+k*40;name=data[o:o+8].rstrip(b'\0').decode('ascii');size,raw,rel,_,nr=struct.unpack_from('<IIIIH',data,o+16);chars=struct.unpack_from('<I',data,o+36)[0]
  need(raw+size<=len(data)and rel+nr*10<=len(data),'Bounded raw COFF section and relocations')
  rows=[]
  for j in range(nr):
   offset,index,typ=struct.unpack_from('<IIH',data,rel+j*10);need(index in symbols,'Relocation symbol exists');rows.append((offset,symbols[index]['name'],typ))
  sections[k+1]=dict(name=name,bytes=data[raw:raw+size],relocations=rows,characteristics=chars)
 return symbols,sections
def expected_function(pc,kind,raw):
 b=bytearray();rel=[]
 def emit(h):b.extend(bytes.fromhex(h))
 def address(name,addend=0,typ=6):rel.append((len(b),name,typ));b.extend(struct.pack('<I',addend))
 emit('c705');address('_fs_event_kind');b.extend(struct.pack('<I',kind))
 stores=['a3','890d','8915','891d','8925','892d','8935','893d'];loads=['a1','8b0d','8b15','8b1d','8b25','8b2d','8b35','8b3d'];marks={}
 def capture(prefix):
  for i,op in enumerate(stores):emit(op);address('_'+prefix+'_cpu',i*4)
  emit('c705');address('_'+prefix+'_cpu',36);b.extend(struct.pack('<I',pc))
  marks[prefix+'_host_stack_switch']=len(b);emit('8b25');address('_mixed_host_esp')
  marks[prefix+'_first_stack_instruction']=len(b);emit('9c8f05');address('_'+prefix+'_cpu',32)
  emit('64a100000000a3');address('_'+prefix+'_head');emit('0fae05');address('_'+prefix+'_fx');emit('d935');address('_'+prefix+'_env');emit('d925');address('_'+prefix+'_env')
  emit('e8');address('_fs_observe_'+prefix.removeprefix('fs_'),0,0x14)
  emit('0fae0d');address('_'+prefix+'_fx');emit('d925');address('_'+prefix+'_env');emit('ff35');address('_'+prefix+'_cpu',32);emit('9d')
  for i,op in enumerate(loads):
   if i==4:continue
   emit(op);address('_'+prefix+'_cpu',i*4)
  marks[prefix+'_source_stack_restore']=len(b);emit('8b25');address('_'+prefix+'_cpu',16)
 capture('fs_before');marks['source_MOV']=len(b);b.extend(raw);capture('fs_after');marks['continuation_jump']=len(b);emit('ff25');address('_fs_continue_'+format(pc,'x'))
 return bytes(b),rel,marks
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive output');out.mkdir(parents=True);pins={};rows=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Immutable physical input '+str(p));pins[str(p)]=v;return p
 try:
  pin(__file__);build=pin(BASE/'original-build-r4/build.json','d8a28a96d6e2f00403a1dca92ba92d720cd12a63dc4b058bd9d2fea3bdc62d61');need(json.loads(build.read_bytes())['passed'],'Compiled original worker')
  prep=pin(BASE/'original-preparation-r5/report.json','57ffbf9a5d1a6375dafcacf1a2cdc9b878b8fa5dbe9af4b49180098b9da1e0d6');need(json.loads(prep.read_bytes())['passed'],'Frozen observer preparation')
  pin(BASE/'original-preparation-r5/fs_observer_x86.asm');pin(BASE/'original-preparation-r5/reference.cpp');pin(BASE/'original-build-r4/original-worker.exe');obj=pin(BASE/'original-build-r4/build-x86/mw34_joint_startup109_original.dir/Release/fs_observer_x86.obj');symbols,sections=parse_coff(obj.read_bytes())
  bindings=json.loads(pin(BASE/'original-preparation-r5/fs-hook-bindings.json').read_bytes());need(len(bindings)==9,'All nine physical FS source sites')
  sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PEImage(game)
  for item in bindings:
   pc=item['PC'];raw=bytes.fromhex(item['raw_bytes']);offset,_=pe.rva_range(pc-0x400000,len(raw));need(game[offset:offset+len(raw)]==raw,'Exact physical original FS MOV')
   symbol='_fs_hook_'+format(pc,'x');defs=[v for v in symbols.values()if v['name']==symbol];need(len(defs)==1,'One physical observer symbol');d=defs[0];need(d['storage']==2 and d['type']==0x20 and d['section']>0,'External i386 function');section=sections[d['section']];need(section['characteristics']&0x20000000,'Executable observer section')
   expected,rel,marks=expected_function(pc,item['kind'],raw);actual=section['bytes'][d['value']:d['value']+len(expected)];need(actual==expected,'Whole assembled observer bytes including every saved register, FX, ENV and host stack switch')
   observed=[(o-d['value'],n,t)for o,n,t in section['relocations']if d['value']<=o<d['value']+len(expected)];need(observed==rel,'All exact assembled relocation names/types/addends')
   need(marks['source_MOV']==0xb6 and marks['source_MOV']==marks['fs_before_source_stack_restore']+6,'Literal source MOV immediately after authentic source ESP restoration');need(marks['fs_after_host_stack_switch']>marks['source_MOV']+len(raw),'All source GPRs saved after literal MOV before switching host stack');need(all(marks[p+'_host_stack_switch']+6==marks[p+'_first_stack_instruction']for p in('fs_before','fs_after')),'First stack instruction uses saved host stack')
   rows.append(dict(PC=pc,kind=item['kind'],source_bytes=raw.hex(),source_image_offset=offset,symbol=symbol,section=d['section'],section_name=section['name'],COFF_value=d['value'],function_bytes=len(expected),function_sha256=hashlib.sha256(actual).hexdigest(),source_MOV_offset=marks['source_MOV'],relative_marks=marks,relocations=[dict(offset=o,symbol=n,type=t)for o,n,t in rel],declared_source_broker=dict(width=len(raw),bytes='e9 + actual linked observer relative DWORD + '+str(len(raw)-5)+' exact90 padding bytes',continuation=item['continuation'],scope='Only these exact source bytes; runtime checks require actual linked hook pointer displacement and every padding byte')))
  need(sum(r['function_bytes']for r in rows)==3300 and sum(len(r['relocations'])for r in rows)==504,'Complete physical observer executable section and all504 relocations');need(len(sections[rows[0]['section']]['bytes'])==3300,'No unexamined executable observer bytes');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'attribution.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'attribution.json');report=dict(passed=passed,scope='Static complete compiled i386 observer attribution plus exact nine declared broker spans; actual observed transparency is a separate functional gate',source_sites=len(rows),compiled_function_bytes=sum(r['function_bytes']for r in rows),host_stack_before_any_push_or_call=True,source_MOV_reexecuted_in_compiled_trampoline=True,full_CPU_flags_FX_ENV_saved_and_restored=True,physical_relocation_validation=True,game_handler_execution=False,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
