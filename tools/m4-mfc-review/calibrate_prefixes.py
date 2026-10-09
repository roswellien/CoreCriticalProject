"""Pure BEFORE-source ABI calibration, stopping before either CRT function.

No API response or allocator result is supplied. This tests the exact prefix,
raw-IAT projection, stack footprint, and caller frame for varied input values.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def need(value,message):
 if not value:raise ValueError(message)
def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main(version):
 out=ROOT/'reports/m4-mfc-review'/version;need(not out.exists(),'Fresh source-prefix calibration');pins={}
 def pin(path,expected=None):
  path=Path(path).resolve();digest=sha(path);need(expected is None or digest==expected,'Exact physical model input');pins[str(path)]=digest;return path
 interface=pin(ROOT/'reports/m4-mfc-review/interface-r1/instruction-contracts.json','94fddd9fc34c0d1dff5100ae8a9f5c66b39e66854a1e5a2d07ac81966656dfeb')
 P=load('mfc_prefix_model',pin(ROOT/'tools/m4-mfc-review/provider_model.py'));program,callbacks=P.source_program(interface)
 for path in ('tools/m4-strings-review/provider_model.py','tools/m4-onexit-review/provider_model.py','tools/m4-crt-locale-batch-model-review/interpreter_v2.py','tools/m4-crt-locale-batch-model-review/batch.py'):pin(ROOT/path)
 observations=[]
 for kind,entry,target,ret,args in (('allocate',0x5f401ea0,0x780012b3,0x5f401eb7,(0,1,12,16,17,31,1024,1048576)),('free',0x5f401782,0x78001390,0x5f40178c,(0,0x31000000,0x31001000,0xfffffffc))):
  for alignment in (0,4,8,12):
   for argument in args:
    frame=0x20001880+alignment;state=bytearray(3504);before={}
    for index,name in enumerate(('eax','ecx','edx','ebx','ebp','esi','edi')):
     before[name]=(0x11220000+index*0x01010203+argument)&0xffffffff;struct.pack_into('<I',state,P.I.REG[name],before[name])
    struct.pack_into('<I',state,P.I.REG['esp'],frame);struct.pack_into('<I',state,2472,entry)
    for index,offset in enumerate(P.I.FLAGS.values()):state[offset]=index%2
    stack=bytearray(b'\xa5'*4096);struct.pack_into('<II',stack,frame-0x20001000,0x410a80,argument)
    data=bytearray(4096);struct.pack_into('<I',data,0x14c,0x78001498);struct.pack_into('<I',data,0x148,0x7800138a);struct.pack_into('<I',data,0x970,0xffffffff)
    machine=P.Machine(state,bytes(512),bytes(40),{0x20001000:stack,0x5f498000:data},program=program,callbacks=callbacks)
    while machine.cursor!=target:need(machine.steps<16,'Exact bounded source prefix');machine.step()
    if kind=='allocate':
     expected_frame=frame-24;expected=[ret,argument,before['edi'],before['esi'],before['ebp'],before['ebx']]
     need(machine.reg('ebp')==argument and machine.reg('ebx')==target and machine.reg('esi')==0xffffffff,'Literal allocator request/target/handler prefix')
     need(machine.mfc_import_reads==[(0x5f401ea1,0x5f49814c,0x78001498,target,4)],'Raw malloc input precedes exact named projection')
    else:
     expected_frame=frame-8;expected=[ret,argument]
     need(machine.mfc_import_reads==[(0x5f401786,0x5f498148,0x7800138a,target,4)],'Raw free input precedes exact named projection')
    need(machine.reg('esp')==expected_frame and machine.bytes(expected_frame,4*len(expected))==struct.pack('<'+'I'*len(expected),*expected),'Complete original source CALL stack bytes')
    need(machine.bytes(frame,8)==struct.pack('<II',0x410a80,argument),'Original incoming return/argument unchanged')
    need(machine.state[2064:2080]==state[2064:2080],'No prefix arithmetic flag modification')
    need(machine.calls[-1]==((0x5f401eb5 if kind=='allocate' else 0x5f401786),target,ret),'Exact register-indirect or memory-indirect CALL')
    writes=[r for r in machine.accesses if r[4]];need(len(writes)==(6 if kind=='allocate' else 2)and all(expected_frame<=r[1]<frame for r in writes),'Only literal stack prefix writes')
    observations.append(dict(kind=kind,entry_frame=frame,argument=argument,CRT_entry_frame=machine.reg('esp'),return_PC=ret,computed_stack_hex=machine.bytes(expected_frame,frame-expected_frame).hex(),original_PCs=machine.PCs,raw_projected_reads=machine.mfc_import_reads,source_accesses=machine.accesses))
 out.mkdir(parents=True);path=out/'computed-prefixes.json';path.write_text(json.dumps(observations,indent=2)+'\n');pin(path);pin(__file__)
 report=dict(passed=True,schema='mw34-mfc-original-prefix-calibration-v1',scope='Pure BEFORE literal source prefixes stop at CRT entry before any API or allocator result',computed_allocator_prefixes=32,computed_free_prefixes=16,complete_source_callframe_checks=48,raw_import_projection_checks=48,API_response_supplied=False,allocator_result_supplied=False,actual_API_executed=False,native_executed=False,AFTER_machine_seed=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
