"""Source-only pre-IR regeneration authenticates callbacks in frozen old guest IR."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode=True
import callbacks as C
ROOT=C.ROOT
def main():
 out=ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-union-r1';C.need(not out.exists(),'Fresh callback union')
 files={}
 def add(p,h=None):
  p=Path(p).absolute();v=C.sha(p);C.need(h is None or v==h,'Pinned union dependency');files[C.normalized(str(p))]=v;return p
 current=C.read(add(ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-r1/callbacks.json','802647aa9bca1f09b58ffd7b7baa4962a3c734492f74b057a04cabeb5f65d21f'))
 rows={x['pc']:x for x in C.read(add(ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json','194e2ca814869c500fd2948d9cc801d3ad7a8aef2367166379a5d0ad87e5a624'))['instructions']}
 build=C.read(add(ROOT/'reports/m4-crt-allocation/build-r9/build.json'));dirs=sorted({Path(p).parent for p in build['entry_objects']})
 lifter=add(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')
 semantics=add(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc','618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
 add(Path(__file__));add(Path(C.__file__));out.mkdir(parents=True);old={};commands=[]
 for directory in dirs:
  for guest in sorted(directory.glob('*guest.ll')):
   text=guest.read_text();found=re.search(r'^define ptr @sub_([a-f0-9]+)\(',text,re.M)
   if not found or int(found[1],16) not in rows:continue
   entry=int(found[1],16);prefix=guest.name[:-len('guest.ll')];source=directory/(prefix+'source.bin')
   if not source.is_file():continue
   add(guest);add(source);raw=source.read_bytes();cursor=entry;code=bytearray()
   while len(code)<len(raw):C.need(cursor in rows,'Frozen old literal instruction closure');row=rows[cursor];code.extend(bytes.fromhex(row['bytes_hex']));cursor+=row['width']
   C.need(bytes(code)==raw,'Every old actual lifted byte matches current original source interface')
   key=directory.parent.name+'-'+prefix.rstrip('-')+'-'+format(entry,'x');pre=out/(key+'-pre.ll');new=out/(key+'-guest.ll')
   argv=[str(lifter),'--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),'--bytes='+raw.hex(),'--semantics_dir='+str(semantics.parent),'--ir_pre_out='+str(pre),'--ir_out='+str(new)]
   cp=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000)
   for name,payload in (('stdout',cp.stdout),('stderr',cp.stderr)):p=out/(key+'.'+name);C.publish_bytes(p,payload);add(p)
   commands.append(dict(argv=argv,exit_code=cp.returncode));C.need(cp.returncode==0,'Actual source-only pre-IR regeneration')
   add(pre);add(new)
   def canonical(value):return re.sub(r' #[0-9]+','',re.sub(r', ![a-zA-Z_.]+ ![0-9]+','',value))
   C.need(canonical(C.function(new.read_text(),entry))==canonical(C.function(text,entry)),'Fresh literal trace equals frozen actual compiled guest trace')
   sites,mapping=C.recover(C.function(pre.read_text(),entry),C.function(text,entry),entry,rows)
   old[key]=dict(entry=entry,actual_guest_IR_path=str(guest),actual_guest_IR_sha256=C.sha(guest),callback_sites=sites,actual_static_callback_calls=sum(x['callback_count'] for x in sites),source_marker_map=mapping)
 sites={x['pc'] for body in current['bodies'].values() for x in body['callback_sites']}
 for body in old.values():sites.update(x['pc'] for x in body['callback_sites'])
 C.need(len(old)>=20,'Complete ordinary current reused heap/allocator/default/mainargs bodies')
 def put(name,value):
  p=out/name;C.publish_bytes(p,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode());add(p);return p
 p=put('callbacks.json',dict(schema='mw34-locale-batch-generated-callback-union-v1',generated_undefined_sites=sorted(sites),new_bodies=current['bodies'],baseline_bodies=old,architectural_undefined_flags_not_assumed_intrinsic_callbacks=True))
 r=put('report.json',dict(schema='mw34-m4-locale-batch-callback-union-recovery-v1',passed=True,baseline_bodies=len(old),new_bodies=len(current['bodies']),callback_PC_sites=len(sites),callbacks_path=str(p),callbacks_sha256=C.sha(p),commands=commands,source_only=True,native_executed=False,API_executed=False,files=files,physical_closure=C.verify_manifest(files)))
 q=put('pins.json',dict(schema='mw34-m4-locale-batch-callback-union-pins-v1',files=files))
 print(json.dumps(dict(passed=True,report_sha256=C.sha(r),callbacks_sha256=C.sha(p),pins_sha256=C.sha(q),baseline_bodies=len(old),sites=len(sites))))
if __name__=='__main__':main()
