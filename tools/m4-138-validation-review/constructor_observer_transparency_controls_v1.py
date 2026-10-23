"""Finite source-shadow controls: actual own input, no equality target opened."""
from pathlib import Path
import importlib.util,json,hashlib,sys,copy
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};tests=[]
 def pin(p):
  p=Path(p).resolve();pins[str(p)]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();return p
 p=pin(R/'tools/m4-constructor-native/derive_source_v9.py');s=importlib.util.spec_from_file_location('d',p);d=importlib.util.module_from_spec(s);s.loader.exec_module(d);i=json.loads(pin(R/'reports/m4-138-validation-review/constructor-original18-source-r4/original-0-4260848/input.json').read_bytes());program,callbacks=d.M.source_program(pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json'))
 def machine():return d.M.Machine(d.M.from_original_before(i),bytes.fromhex(i['BEFORE_FX_hex']),bytes.fromhex(i['BEFORE_CPU_hex']),{int(k):bytes.fromhex(v)for k,v in i['BEFORE_memory'].items()},program=program,callbacks=callbacks,owner_roles=copy.deepcopy(i['owners']),source_imports={},original_observer_stack=True)
 def reject(n,f):
  try:f()
  except ValueError:tests.append(dict(name=n,rejected=True));return
  raise ValueError('Control did not reject '+n)
 m=machine();address=0x200017fc;old=m.bytes(address,4);m.observer_shadow[address-0x20001000:address-0x20001000+4]=(0x202).to_bytes(4,'little');assert old!=(0x202).to_bytes(4,'little');reject('source operand cannot consume earlier observer PUSHFD',lambda:m.read(address,4));reject('typed API return frame cannot consume observer clobber',lambda:m.observer_live_bytes(address,4));reject('partially overlapping API buffer cannot hide one clobbered byte',lambda:m.observer_live_bytes(address-3,4));m.write(address,int.from_bytes(old,'little'));m.observer_live_bytes(address,4);m.read(address,4);tests.append(dict(name='exact later literal source write restores transparency',passed=True));m.observer_live_bytes(0x20000000,16);tests.append(dict(name='outside upper stack no invented shadow ownership',passed=True))
 # Test actual API wrapper before any external-provider mutation or outputs.
 m=machine();frame=m.reg('esp');m.observer_shadow[frame-0x20001000:frame-0x20001000+1]=bytes([m.bytes(frame,1)[0]^1]);response=d.M.ActualAPIs([dict(argc=3,args=[0,0,16],initial_allocations=[],input_buffers=[])]);reject('ActualAPIs rejects mismatched return before parent provider',lambda:response(m,0));m=machine();frame=m.reg('esp');m.observer_shadow[frame+7-0x20001000:frame+8-0x20001000]=bytes([m.bytes(frame+7,1)[0]^1]);response=d.M.ActualAPIs([dict(argc=3,args=[0,0,16],initial_allocations=[],input_buffers=[])]);reject('ActualAPIs rejects mismatched argument before parent provider',lambda:response(m,0))
 for p in(R/'tools/m4-constructor-native/game_model_v9.py',R/'tools/m4-constructor-native/game_model_v8.py',__file__):pin(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Finite rejection controls on actual own original BEFORE source Machine; no endpoint buffers opened. Compiled observer identity is pinned spec and independent whole-link review, not simulated here.',controls=tests,source_AFTER_seed=False,canonical_reader_opened=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
