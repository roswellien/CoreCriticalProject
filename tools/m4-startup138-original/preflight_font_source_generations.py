"""Synthetic source resource joins and physical literal-store readiness only."""
from pathlib import Path
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[2];helper=Path(__file__).with_name('font_source_generations.py');s=importlib.util.spec_from_file_location('fontjoin',helper);F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
contract=R/'reports/m4-fps-original/source-preparation-r4/source-contracts.json';d=json.loads(contract.read_bytes());row=next(r for r in d['instructions']if r['pc']==0x5a0753);assert row['mnemonic']=='mov'and row['operands']=='dword ptr [esi + 0x258], eax'
class Machine:
 def __init__(self):self.registers={'esi':0x730000,'eax':0x99};self.memory={};self.accesses=[(0x5a0753,0x730258,0x99,4,True)]
 def reg(self,k):return self.registers[k]
 def bytes(self,a,n):return self.memory.get(a,b'\0'*n)
def exercise(case):
 m=Machine();g=F.Generations(0);before=dict(API='CreateFontA',CPU=[0]*6+[m.reg('esi')],header=[0]*11+[m.reg('esi')]);after=dict(CPU=[0x99]+[0]*5+[m.reg('esi')],header=before['header'],index=3)
 if case=='wrong-instance':after['CPU'][6]+=4
 g.gdi(m,before,after,134,0x5a3c30)
 m.memory[0x730258]=struct.pack('<I',0x99);g.store(m,0x5a0753,0x730258,0x99 if case!='wrong-store' else 0x98,4,'source')
 resources=struct.pack('<8I',1,0,0x5a3c30,0x730000,0x99,3,1,0xffffffff);g.phase(resources)
 cleanup=bytearray(1112);struct.pack_into('<8I',cleanup,0,1,0,0x730000,0x99,1,0,0,1)
 if case=='wrong-cleanup':struct.pack_into('<I',cleanup,12,0x98)
 lifetime=dict(sequence=0,occurrence=0,phase=134,root=0x5a3c30,instance=0x730000,handle=0x99,created_event=3,live=True,deleted_event=None,manual_cleanup_BOOL=1,FX_BEFORE_hex=bytes(512).hex(),FX_AFTER_hex=bytes(512).hex(),ENV_BEFORE_hex=bytes(28).hex(),ENV_AFTER_hex=bytes(28).hex())
 g.cleanup(struct.pack('<8I',1,0,0x5a3c30,0x730000,0x99,3,0,0xfffffffe),lambda i:bytes(cleanup),[lifetime]);return True
results={}
for case in('valid','wrong-instance','wrong-store','wrong-cleanup'):
 try:results[case]=exercise(case)
 except ValueError:results[case]=False
assert results=={'valid':True,'wrong-instance':False,'wrong-store':False,'wrong-cleanup':False}
out=R/'reports/m4-startup138-original/font-source-generation-preparation-r1';assert not out.exists();out.mkdir();files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(helper,contract,Path(__file__))};q=out/'report.json';q.write_text(json.dumps(dict(passed=True,readiness_only=True,controls=results,source_literal_store_PC=0x5a0753,source_owning_field_offset=0x258,complete_widget_gate=False,original_or_native_source_machine_executed=False,new_capture_inputs_opened=False,archive_reader_opened=False,manual_cleanup_is_source_callback=False,source_shutdown_executed=False,pending=['Integrate source GDI hook and exact owning-source store hook into immutable current original replay','Join everyphase full widget-resources inventory and all90 current font lifetime/manualcleanup observations','Complete current42 widget full69/CRT/backing endpoints including new kind3 API initial observations'],files=files),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
