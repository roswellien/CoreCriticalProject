"""Add exact mixed game instructions to the independently executed persistent model."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 parent=R/'reports/m4-formatting-source/persistent-model-r3/report.json';assert sha(parent)=='8a6f4968d524105ea04aeaa4c08a78ec2a259cf6b279ff719ddc0cabf05ad9cf';prior=json.loads(parent.read_bytes());source=Path(prior['model']);assert sha(source)==prior['model_sha256']
 native=R/'reports/m4-formatting-native/preparation-r18/report.json';assert sha(native)=='68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06';prep=json.loads(native.read_bytes());assert prep['passed']
 contracts=R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json';callbacks=Path(prep['mixed_callbacks']);assert sha(callbacks)==prep['mixed_callbacks_sha256']
 text=source.read_text()+f'''

accepted128_source_program=source_program
def source_program():
 program,callbacks=accepted128_source_program()
 data=checked(R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json','{sha(contracts)}')
 for row in data['instructions']:
  pc=row['pc']
  if pc in program:I.need(program[pc]['bytes_hex']==row['bytes_hex'] and program[pc]['width']==row['width'],'Identical physical shared mixed instruction bytes')
  else:program[pc]=row
 data=checked(R/'reports/m4-formatting-native/preparation-r18/mixed-callbacks.json','{sha(callbacks)}')
 for pc,offsets in data['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical literal mixed undefined callback order');callbacks[pc]=offsets
 return program,callbacks

Accepted128Machine=Machine
class Machine(Accepted128Machine):
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
  if domain=='source'and size==4 and(original_pc,address)in((0x4e530f,0x5bb4f8),(0x4e5389,0x5bb4f4)):
   raw,target=(0x1df582,0x7810a290)if original_pc==0x4e530f else(0x1df568,0x7810a350)
   I.need(value==raw and self.reg('ecx')==(self.reg('esp')+44)&0xffffffff,'Literal mixed raw owning import and LEA-retained ECX')
   self.import_projections.append((11,original_pc,address,value,target,0,0,0));return target
  return value
'''
 model=out/'persistent_model.py';model.write_text(text)
 files={str(p.resolve()):sha(p)for p in(Path(__file__),parent,source,native,contracts,callbacks,model)}
 report=dict(passed=True,scope='Unexecuted literal formatting4 persistent model; inherited accepted125 arithmetic and provider semantics retained',model=str(model),model_sha256=sha(model),files=files,executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
