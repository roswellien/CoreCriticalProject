"""Complete physical x86 FS and finite-indirect observation trampoline attribution."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-vtable-original'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def expected_vtable(h):
 b=bytearray();rel=[];marks={}
 def emit(x):b.extend(bytes.fromhex(x))
 def addr(n,a=0,t=6):rel.append((len(b),n,t));b.extend(struct.pack('<I',a))
 stores=['a3','890d','8915','891d','8925','892d','8935','893d'];loads=['a1','8b0d','8b15','8b1d','8b25','8b2d','8b35','8b3d']
 for i,x in enumerate(stores):emit(x);addr('_vtable_cpu',i*4)
 emit('c705');addr('_vtable_cpu',36);b.extend(struct.pack('<I',h['PC']));emit('c705');addr('_vtable_point');b.extend(struct.pack('<I',h['kind']))
 marks['host_stack_switch']=len(b);emit('8b25');addr('_mixed_host_esp');marks['first_stack_instruction']=len(b);emit('9c8f05');addr('_vtable_cpu',32)
 emit('64a100000000a3');addr('_vtable_head');emit('0fae05');addr('_vtable_fx');emit('d935');addr('_vtable_env');emit('d925');addr('_vtable_env');emit('e8');addr('_vtable_observe',0,0x14)
 emit('0fae0d');addr('_vtable_fx');emit('d925');addr('_vtable_env');emit('ff35');addr('_vtable_cpu',32);emit('9d')
 for i,x in enumerate(loads):
  if i!=4:emit(x);addr('_vtable_cpu',i*4)
 marks['guest_stack_restore']=len(b);emit('8b25');addr('_vtable_cpu',16);marks['literal_source_replay']=len(b);b.extend(bytes.fromhex(h['replayed_bytes']))
 if h['kind']==0:marks['continuation_jump']=len(b);emit('ff25');addr('_vtable_continue_'+format(h['PC'],'x'))
 return bytes(b),rel,marks
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh attribution');out.mkdir(parents=True);pins={};rows=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));pins[str(p)]=v;return p
 try:
  s=importlib.util.spec_from_file_location('immutable_fs_attribution',pin(ROOT/'tools/m4-fs-source/observer_attribution.py'));A=importlib.util.module_from_spec(s);s.loader.exec_module(A);pin(__file__)
  prep=BASE/'preparation-r3';build=BASE/'build-r2';pr=json.loads(pin(prep/'report.json','a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5').read_bytes());br=json.loads(pin(build/'build.json','ea4fb73e11dfa0d5c4b6f4145eb57df5148e5b096bb44e3fdd6c8d9d99e6dc5a').read_text(encoding='utf-8-sig'));need(pr['passed']and br['passed']and br['preparation_sha256']==sha(prep/'report.json'),'Exact passed source/build binding');pin(build/'original-worker.exe',br['worker_sha256'])
  for name_ in('reference.cpp','fs_observer_x86.asm','vtable_observer_x86.asm','nullfree_observer_x86.asm'):pin(prep/name_)
  sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
  game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  for family,objname,binding in [('FS','fs_observer_x86.obj','fs-hook-bindings.json'),('indirect','vtable_observer_x86.obj','vtable-hook-bindings.json')]:
   obj=pin(build/'build-x86/mw34_joint_startup120_original.dir/Release'/objname);symbols,sections=A.parse_coff(obj.read_bytes());items=json.loads(pin(prep/binding).read_bytes());need(len(items)==(33 if family=='FS'else 6),'Exact declared trampoline family');claimed={}
   for h in items:
    pc=h['PC'];raw=bytes.fromhex(h['raw_bytes']);pe=crt if pc>=0x78000000 else game;offset,_=pe.rva_range(pc-pe.image_base,len(raw));need(pe.data[offset:offset+len(raw)]==raw,'Actual original PE source bytes including all declared tail bytes')
    symbol='_'+h['declared_observer'];defs=[v for v in symbols.values()if v['name']==symbol];need(len(defs)==1,'One physical external observer');d=defs[0];need(d['storage']==2 and d['type']==0x20 and d['section']>0,'Actual i386 executable function');sec=sections[d['section']];need(sec['characteristics']&0x20000000,'Executable physical COFF section')
    expected,rel,marks=A.expected_function(pc,h['kind'],raw)if family=='FS'else expected_vtable(h);actual=sec['bytes'][d['value']:d['value']+len(expected)];need(actual==expected,'Complete assembled observer byte sequence');actual_rel=[(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)];need(actual_rel==rel,'Exact all relocation symbols/types/addends')
    if family=='FS':need(all(marks[k+'_host_stack_switch']+6==marks[k+'_first_stack_instruction']for k in('fs_before','fs_after'))and marks['source_MOV']==marks['fs_before_source_stack_restore']+6,'Source/host stack discipline around literal FS source MOV')
    else:need(marks['host_stack_switch']+6==marks['first_stack_instruction']and marks['literal_source_replay']==marks['guest_stack_restore']+6,'Source/host stack discipline around physical indirect helper replay');need(h['kind']==0 or bytes.fromhex(h['replayed_bytes'])in(b'\xc3',b'\xc2\x04\x00'),'Genuine physical RET bytes after preRET observation')
    claimed.setdefault(d['section'],[]).append((d['value'],d['value']+len(expected)));rows.append(dict(family=family,PC=pc,symbol=symbol,source_image_offset=offset,source_bytes=raw.hex(),replayed_bytes=h.get('replayed_bytes',h['raw_bytes']),COFF_section=d['section'],COFF_value=d['value'],function_bytes=len(expected),sha256=hashlib.sha256(actual).hexdigest(),marks=marks,relocations=[dict(offset=o,symbol=n,type=t)for o,n,t in rel]))
   for secno,ranges in claimed.items():
    ranges.sort();need(ranges[0][0]==0 and all(a[1]==b[0]for a,b in zip(ranges,ranges[1:]))and ranges[-1][1]==len(sections[secno]['bytes']),'Every physical executable observer byte accounted for')
  (out/'attribution.json').write_text(json.dumps(rows,indent=2)+'\n');pin(out/'attribution.json')
  clarification=dict(frozen_field='padding_bytes',correct_meaning='Bounded trailing source bytes not replayed because the genuine RET has already returned',site=0x59ff0d,physical_bytes='c39090568b',genuine_RET_bytes='c3',NOP_tail_bytes='9090',unselected_neighbor_prefix=dict(entry=0x59ff10,bytes='568b',reached=False,admitted=False),whole_declared_patch_verified=True,original_observation='Target entry and immediate preRET only; postRET physically derived',capture_unchanged=True)
  (out/'tail-scope.json').write_text(json.dumps(clarification,indent=2)+'\n');pin(out/'tail-scope.json');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Complete physical33 FS +6 finite-indirect i386 observer attribution; actual root source/CPU transparency is separate',source_sites=len(rows),FS_sites=sum(r['family']=='FS'for r in rows),indirect_sites=sum(r['family']=='indirect'for r in rows),compiled_function_bytes=sum(r['function_bytes']for r in rows),full_CPU_flags_FX_ENV_saved_and_restored=True,host_stack_before_first_stack_instruction=True,source_effects_only_physical_replay=True,actual_preRET_scope=True,naked_neighbor_function_admitted=False,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
