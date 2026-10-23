"""Current literal54 dependency closure, ordinary immutable files only."""
from pathlib import Path
import hashlib,json,sys,importlib.util,types,ast
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};reads={};rb0=Path.read_bytes;rt0=Path.read_text
 def pin(p,h=None):
  p=Path(p).resolve();assert p.is_relative_to(R);v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def rb(p):
  b=rb0(p);reads[str(Path(p).resolve())]=hashlib.sha256(b).hexdigest();return b
 def rt(p,*a,**k):
  v=rt0(p,*a,**k);reads[str(Path(p).resolve())]=hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest();return v
 Path.read_bytes=rb;Path.read_text=rt
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 d=load('tools/m4-constructor-native/derive_source_v8.py','current_derivation');a=load('tools/m4-138-validation-review/constructor_original_input_v5.py','original_adapter');b=load('tools/m4-138-validation-review/constructor_native_input_v7.py','native_adapter')
 program,callbacks=d.M.source_program(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json');seen=set();modules=[]
 def visit(m):
  if id(m)in seen:return
  seen.add(id(m));p=getattr(m,'__file__',None)
  if p and Path(p).resolve().is_relative_to(R):pin(p);ast.parse(rt0(Path(p)));modules.append(str(Path(p).resolve()))
  for v in vars(m).values():
   if isinstance(v,types.ModuleType)and getattr(v,'__file__',None)and Path(v.__file__).resolve().is_relative_to(R):visit(v)
 for m in(d,a,b):visit(m)
 lineage={}
 for rel,digest in [('constructor-provider-named-proof-r1/report.json','0bfde9d0b381efd15ed762cb8ecb81a79a61a26f7a9439f3c3897f6a21aef6ec'),('constructor-observer-stack-spec-r2/spec.json','8b45b01c56bc2e06e5702233bdefc589f1363bc3be79ec092ebed0cac37de0ce'),('constructor-original18-source-r3/report.json','e4457313868e295c31a264bce53340249de0fab071d79c4d049d60f9c85d04ca'),('constructor-native36-source-r5/report.json','ea3b9eb6df741a1c60e88168cd870d95619500201ddef8a2fb2bf54e01c66c74')]:
  p=pin(R/'reports/m4-138-validation-review'/rel,digest);rec=json.loads(rb0(p));assert rec['passed'];lineage[rel]=digest
  for f,h in rec['files'].items():
   # Existing sealed payloads are already hashed by their owning closed Facade; do not open another reader here.
   if Path(f).name in('payload.bin','index.json','transport.json'):continue
   pin(f,h)
 p7=pin(R/'tools/m4-constructor-native/game_model_v7.py');p8=pin(R/'tools/m4-constructor-native/game_model_v8.py');t7=rt0(p7);t8=rt0(p8);assert t7.replace('constructor-observer-stack-spec-r1/spec.json','constructor-observer-stack-spec-r2/spec.json').replace('af2e8d54916aa6839b3442ab823476703ae7200bed44e98fb3fd716c38be3ef4','8b45b01c56bc2e06e5702233bdefc589f1363bc3be79ec092ebed0cac37de0ce')==t8
 for p,h in reads.items():pin(p,h)
 pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current literal54 exact recursive Python dependency/source descriptor read closure plus physical named-provider and complete compiled PUSHFD specifications. No acceptance credit; native input carry policy separate.',program_rows=len(program),callback_sites=len(callbacks),modules=sorted(set(modules)),source_descriptor_reads=reads,lineage=lineage,model_v8_exact_spec_binding_inverse=True,original_own_input_adapter_v2_pinned=str(R/'tools/m4-138-validation-review/constructor_original_input_v2.py')in pins,canonical_reader_opened=False,ordinary_raw_reader_opened=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
