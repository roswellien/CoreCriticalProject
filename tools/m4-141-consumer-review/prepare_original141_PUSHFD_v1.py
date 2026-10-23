"""Current compiled constructor PUSHFD provenance plus finite source shadow controls."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct,sys,types
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141/PUSHFD-preparation-r1';out.mkdir();files={};points=[];checks=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 current=R/'reports/m4-original141/source-preparation-r2';build=R/'reports/m4-original141/build-r1';release=build/'build-x86/mw34_joint_startup124_original.dir/Release'
 review=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r1/report.json','eb75e0b93508887402c328d3a4b8f5dfadc5baa391add6b71568797d2a90d9c3').read_bytes());assert review['passed']
 links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r1/physical-links.json').read_bytes());proof=next(r for r in links if r['symbol']=='constructor_observer_x86 whole source')
 legacy=json.loads(pin(R/'reports/m4-138-validation-review/constructor-observer-stack-spec-r2/spec.json','8b45b01c56bc2e06e5702233bdefc589f1363bc3be79ec092ebed0cac37de0ce').read_bytes());assert legacy['passed']and len(legacy['points'])==11
 C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','PUSHFD_CO F'.replace(' ',''));symbols,sections=C.coff(pin(release/'constructor_observer_x86.obj').read_bytes());ids=[n for n,s in sections.items()if s['flags']&0x20000000 and s['bytes']];assert len(ids)==1;sec=ids[0];raw=sections[sec]['bytes'];assert raw.hex()==proof['object_raw_hex'];linked=bytes.fromhex(proof['linked_hex']);assert len(linked)==len(raw)==2116
 parent=R/'reports/m4-138-validation-review/constructor-input-capture-build-r2/build-x86/mw34_joint_startup124_original.dir/Release/constructor_observer_x86.obj';_,old_sections=C.coff(pin(parent).read_bytes());olds=[s['bytes']for s in old_sections.values()if s['flags']&0x20000000 and s['bytes']];assert olds==[raw]
 asm=pin(current/'constructor_observer_x86.asm');assert asm.read_bytes()==pin(R/'reports/m4-138-validation-review/constructor-input-capture-preparation-r5/constructor_observer_x86.asm').read_bytes()
 sym={v['name']:v for v in symbols.values()if v['section']==sec};res={v['symbol']:v['actual_symbol_address']for v in proof['relocations']if v['resolution_kind']=='virtual address'}
 for v in legacy['points']:
  sy=sym['_'+v['observer']];offset=v['observer_PUSHFD_PC']-v['observer_entry'];at=sy['value']+offset;assert raw[at:at+3]==b'\x9c\x8f\x05';assert linked[at:at+7]==b'\x9c\x8f\x05'+struct.pack('<I',res['_ctor_cpu']+32)
  rel=next(x for x in proof['relocations']if x['offset']==at+3);assert rel['type']==6 and rel['symbol']=='_ctor_cpu'
  # Source ASM whole PROC is bound, including host stack switch and restoration.
  body=asm.read_text().split(v['observer']+' PROC\n',1)[1].split(v['observer']+' ENDP',1)[0];assert 'mov esp,mixed_host_esp'in body and 'mov esp,DWORD PTR ctor_cpu[16]'in body and 'pushfd'in body and 'pop DWORD PTR ctor_cpu[32]'in body
  point={**v,'observer_entry':proof['address']+sy['value'],'observer_PUSHFD_PC':proof['address']+at,'raw_first_pushfd_pop_hex':linked[at:at+7].hex(),'whole_current_ASM_bytes':len(raw)};points.append(point)
 # CS24 producer PUSHFD copies are on host ESP, never an extra guest shadow.
 ref=pin(current/'reference_x86.asm').read_text();body=ref.split('registry_API_common PROC',1)[1].split('registry_API_common ENDP',1)[0];host=body.index('mov esp,mixed_host_esp');guest=body.index('mov esp,DWORD PTR registry_API_after[16]');assert host<guest and body[host:guest].count('pushfd')==3 and 'mov esp,'not in body[host+len('mov esp,mixed_host_esp'):guest];checks.append(dict(passed=True,name='all3 API CS-before/after PUSHFD copies on actual host ESP'))
 # Exercise exact source-computed shadow-store production block for every point.
 model=pin(R/'tools/m4-constructor-native/game_model_v8.py');tree=ast.parse(model.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));step=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='step');block=ast.unparse(step.body[0])
 class Fake:
  def __init__(self,p,flags):
   self.original_observer_stack=True;self.constructor_active=True;self.cursor=p['source_PC'];self.observer_points={self.cursor:p};self.observer_shadow=bytearray(4096);self.observer_stores=[];self.constructor_root=0x4103f0;self.PCs=[1]*19;self.fx=bytearray(512);self.arch_undefined={'AF':0x1234};self.flags=flags
  def projected_cpu(self):return [0,1,2,3,0x20001f00,5,6,7,self.flags,self.cursor]
 need=lambda v,s: (_ for _ in ()).throw(ValueError(s))if not v else None
 for p in points:
  for flags in(0x202,0x8d5):
   m=Fake(p,flags);exec(compile(block,'source-computed observer PUSHFD block','exec'),dict(self=m,I=types.SimpleNamespace(need=need),struct=struct));e=m.observer_stores[0];assert e['address']==0x20001efc and e['write_hex']==struct.pack('<I',flags).hex()and e['source_undefined_flags']=={'AF':0x1234}and not e['observed_endpoint_seed']and e['observer_PUSHFD_PC']==p['observer_PUSHFD_PC'];assert m.observer_shadow[0xefc:0xf00]==struct.pack('<I',flags);checks.append(dict(passed=True,name=p['observer']+' kind'+str(p['kind'])+' EFLAGS '+hex(flags)))
 for n in('constructor-shadow-root-review-r2','constructor-observer-geometry-review-r1','constructor-observer-transparency-controls-r1'):
  receipt=json.loads(pin(R/'reports/m4-138-validation-review'/n/'report.json').read_bytes());assert receipt['passed']
  for path,h in receipt['files'].items():
   p=Path(path)
   if p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json':pin(p,h)
 pin(__file__);spec=dict(passed=True,points=points,scope='Current compiled original141 complete11 constructor observer PUSHFD physical identity; finite source-shadow controls; same whole ASM as isolated54. Full connected141 source occurrences remain pending.',source_AFTER_seed=False,files=files);q=out/'spec.json';q.write_text(json.dumps(spec,indent=2)+'\n');pin(q)
 report=dict(passed=True,prepared_only=True,whole_ASM_byteidentity=True,compiled_constructor_points=11,controls=len(checks),checks=checks,source_partial_flag_metadata_preserved=True,CS24_guest_stack_stores=0,legacy54_causal_controls_retained=True,current141_source_shadow_not_installed=True,connected141_source_causal_equivalence_pending=True,whole_CRT_IAT_validator_pending=True,worker_admitted=False,worker_launched=False,canonical_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),spec_sha256=sha(out/'spec.json'),controls=len(checks))))
if __name__=='__main__':main()
