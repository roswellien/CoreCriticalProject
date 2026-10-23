"""Pre-capture source/compiled stack ownership; no dynamic source equivalence claim."""
from pathlib import Path
import ast,hashlib,importlib.util,json,re,struct,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/source-stack-preparation-r3';out.mkdir();files={};rows=[];controls=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;files[str(p)]=v;return p
 def read(p):return json.loads(pin(p).read_bytes())
 def control(name,fn,reject=False):
  try:fn()
  except (AssertionError,ValueError):assert reject,name
  else:assert not reject,name
  controls.append(dict(name=name,rejected=reject))
 prep=R/'reports/m4-original141/source-preparation-r6'
 proof=read(R/'reports/m4-original141/root-compiled-review-r2/report.json');assert proof['passed']
 for p,h in proof['files'].items():pin(p,h)
 links=read(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json')
 fs=pin(prep/'fs_observer_x86.asm').read_text();ctor=pin(prep/'constructor_observer_x86.asm').read_text()
 bindings=read(prep/'fs-hook-bindings.json');assert len(bindings)==108
 fslink=next(x for x in links if x['symbol']=='fs_observer_x86 whole source')
 cpath=pin(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py');sp=importlib.util.spec_from_file_location('stack_coff',cpath);C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)
 obj=R/'reports/m4-original141/build-r2/build-x86/mw34_joint_startup124_original.dir/Release/fs_observer_x86.obj'
 sy,sections=C.coff(pin(obj).read_bytes());sec=[i for i,s in sections.items()if s['flags']&0x20000000 and s['bytes']];assert len(sec)==1
 assert sections[sec[0]]['bytes'].hex()==fslink['object_raw_hex']
 symbols={v['name']:v for v in sy.values()if v['section']==sec[0]}
 def fs_body(body,raw):
  lines=[x.strip()for x in body.splitlines()if x.strip()]
  assert lines.count('pushfd')==2 and lines.count('popfd')==2
  assert lines.count('mov esp,mixed_host_esp')==2
  assert lines.count('call fs_observe_before')==lines.count('call fs_observe_after')==1
  db=[i for i,x in enumerate(lines)if x.startswith('db ')];assert len(db)==1
  actual=bytes(int(x.strip()[:-1],16)for x in lines[db[0]][3:].split(','));assert actual==bytes.fromhex(raw)
  # Every instruction before each host-stack switch is a MOV or the original FS MOV.
  for i,x in enumerate(lines):
   if x=='mov esp,mixed_host_esp':
    prev=max([-1]+[j for j in range(i)if lines[j].startswith('db ')])+1
    assert all(y.startswith('mov ')for y in lines[prev:i])
  # All observer pushes, pops and callbacks execute on host ESP; only displaced FS instruction runs on guest ESP.
  host=False
  for x in lines:
   if x=='mov esp,mixed_host_esp':host=True
   elif x in('mov esp,DWORD PTR fs_before_cpu[16]','mov esp,DWORD PTR fs_after_cpu[16]'):host=False
   elif x.startswith(('push','pop','call ')):assert host
  assert not host and lines[-1].startswith('jmp DWORD PTR fs_continue_')
  return True
 for b in bindings:
  name=b['declared_observer'];body=fs.split(name+' PROC\n',1)[1].split(name+' ENDP',1)[0];fs_body(body,b['raw_bytes']);v=symbols['_'+name]
  rows.append(dict(source_PC=b['PC'],kind=b['kind'],raw_FS_hex=b['raw_bytes'],continuation=b['continuation'],observer=name,linked_entry=fslink['address']+v['value'],whole_PROC_SHA256=hashlib.sha256(body.encode()).hexdigest(),observer_guest_stack_stores=0,source_instruction_executed_once=True,source_flags_changed=False))
 body=fs.split(bindings[0]['declared_observer']+' PROC\n',1)[1].split(bindings[0]['declared_observer']+' ENDP',1)[0]
 control('all108 complete FS PROC host ownership',lambda:fs_body(body,bindings[0]['raw_bytes']))
 control('reject guest PUSHFD before host switch',lambda:fs_body(body.replace('mov esp,mixed_host_esp\n pushfd','pushfd\n mov esp,mixed_host_esp',1),bindings[0]['raw_bytes']),True)
 control('reject changed displaced source instruction',lambda:fs_body(body, '00'*6),True)
 push=read(R/'reports/m4-original141/PUSHFD-preparation-r2/spec.json');assert len(push['points'])==11
 for p,h in push['files'].items():pin(p,h)
 for point in push['points']:
  body=ctor.split(point['observer']+' PROC\n',1)[1].split(point['observer']+' ENDP',1)[0]
  marker='mov ctor_kind,'+str(point['kind']);assert body.count(marker+'\n')==1;body=body.split(marker+'\n',1)[1];body=re.split(r'\n mov ctor_kind,\d+\n',body,maxsplit=1)[0]
  first=body.split('mov esp,mixed_host_esp',1)[0];assert first.count('pushfd')==1 and first.count('pop DWORD PTR ctor_cpu[32]')==1
  assert all(x.strip().startswith(('mov ','pushfd','pop DWORD PTR ctor_cpu[32]'))for x in first.splitlines()if x.strip())
  last=body.split('mov esp,mixed_host_esp',1)[1];restore=last.index('mov esp,DWORD PTR ctor_cpu[16]')
  assert 'push DWORD PTR ctor_cpu[32]\n popfd'in last[:restore] and 'pushfd'not in last
  assert point['source_ESP_write_displacement']==-4 and point['write_bytes']==4
  rows.append(dict(observer=point['observer'],source_PC=point['source_PC'],guest_stack_store='DWORD[source-computed ESP-4] = source-computed EFLAGS',observer_PUSHFD_PC=point['observer_PUSHFD_PC'],guest_store_bytes=4,source_after_seed=False,undefined_flags_must_remain_carried=True))
 # Production shadow computation: reject unbounded guest addresses, retain undefined metadata.
 tree=ast.parse(pin(R/'tools/m4-constructor-native/game_model_v8.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));step=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='step');block=ast.unparse(step.body[0])
 def shadow(esp):
  p=push['points'][0];m=types.SimpleNamespace(original_observer_stack=True,constructor_active=True,cursor=p['source_PC'],observer_points={p['source_PC']:p},observer_shadow=bytearray(4096),observer_stores=[],constructor_root=0x4103f0,PCs=[],fx=bytes(512),arch_undefined={'AF':123},projected_cpu=lambda:[0,1,2,3,esp,5,6,7,0x8d5,p['source_PC']])
  def need(v,s):
   if not v:raise ValueError(s)
  exec(compile(block,'actual source-shadow production block','exec'),dict(self=m,I=types.SimpleNamespace(need=need),struct=struct));assert m.observer_stores[0]['write_hex']=='d5080000'and m.observer_stores[0]['source_undefined_flags']=={'AF':123}
 control('source-computed EFLAGS, no AFTER input',lambda:shadow(0x20001f00))
 control('reject lower guest crossing store',lambda:shadow(0x20001002),True)
 control('reject upper guest crossing store',lambda:shadow(0x20002002),True)
 pin(__file__);p=out/'stack-ownership.json';p.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');pin(p)
 report=dict(passed=True,prepared_only=True,compiled_FS_source_hooks=108,FS_guest_observer_stack_stores=0,compiled_constructor_guest_PUSHFD_points=11,controls=controls,files=files,worker_launched=False,reader_opened=False,initializer_credit=0,static_proof='Whole compiled/source hook identity and exact guest/host stack ownership. Constructor PUSHFD makes one4B source-ESP-4 store; FS hook observer makes zero guest stack stores. Flags/FX/register restoration physically retained.',dynamic_pending='Actual connected original141 source execution must derive each boundary CPU/EFLAGS including carried undefined metadata, exact store chronology and subsequent live operand overwrite/read transparency, and compare whole observed stack. Static and isolated54 evidence cannot establish those actual141 equalities.')
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
