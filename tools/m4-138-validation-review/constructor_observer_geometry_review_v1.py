"""Exact finite54 source stack geometry and direct-byte read inventory."""
from pathlib import Path
import json,hashlib,ast,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};cases=[];direct=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 def get(p):return json.loads(pin(p).read_bytes())
 for rel,h,branches in [('constructor-original18-source-r4','48cad330f7fe559721fe10748efdf4261e92d22653ba141883065c4c9342fff6',('original',)),('constructor-native36-source-r6','e7bc628fe59f20e69a5823e2f54ad88af94d9f0dbbfea1c51d8e45807d5c4392',('O0','O2'))]:
  rec=json.loads(pin(R/'reports/m4-138-validation-review'/rel/'report.json',h).read_bytes());assert rec['passed']
  for branch in branches:
   for seq in range(6):
    for root in(0x4103f0,0x410440,0x459b40):
     base=R/'reports/m4-138-validation-review'/rel/f'{branch}-{seq}-{root}';result=get(base/'source-derivation.json');inp=get(base/'input.json');cross=[];stack_accesses=[]
     for pc,address,value,width,write in result['accesses']:
      if address<0x20002000 and address+width>0x20001000:
       stack_accesses.append([pc,address,width,write]);
       if not(0x20001000<=address and address+width<=0x20002000):cross.append([pc,address,width,write])
     assert not cross
     for event in result['constructor_FS']:
      if 'frame'in event:assert 0x20001000<=event['frame']and event['frame']+12<=0x20002000
     provider=[]
     for fact in inp['APIs']:
      frame=fact['before_cpu'][4];assert 0x20001000<=frame and frame+4+4*fact['argc']<=0x20002000;provider.append(dict(site=fact['site'],frame=frame,frame_bytes=4+4*fact['argc'],input_buffers=[dict(address=b['address'],bytes=b['bytes'])for b in fact.get('input_buffers',[])]))
     # Source-computed Machine observer stores include complete physical11 spec roles.
     for event in result['original_observer_stores']:assert 0x20001000<=event['address']and event['address']+4<=0x20002000
     cases.append(dict(branch=branch,sequence=seq,root=root,source_accesses=len(result['accesses']),bounded_upper_stack_operands=len(stack_accesses),crossing_upper_stack_operands=cross,all_FS_raw12_frames_bounded=True,typed_provider_byte_reads=provider))
 audit=get(R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json');assert audit['passed']
 for file,h in audit['files'].items():
  p=Path(file)
  if p.suffix=='.py'and p.name.startswith('game_model'):
   pin(p,h);tree=ast.parse(p.read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='bytes':direct.append(dict(path=str(p),line=n.lineno,expression=ast.get_source_segment(p.read_text(),n)))
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All54 current literal source operand geometry and typed-provider return/argument/input buffers. Source accesses crossing upper-stack boundaries absent; all source FS raw12 direct frames bounded. Static direct-byte inventory retained for independent role review, not treated as generic observed-byte seeding.',cases=cases,direct_byte_call_inventory=direct,source_API_v9_coverage='Before parent provider mutation: complete return+argc frame, every declared input_buffer, each genuine malloc-frame caller request',whole_byte_call_semantics_review_pending=True,initializer_credit=0,canonical_reader_opened=False,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
