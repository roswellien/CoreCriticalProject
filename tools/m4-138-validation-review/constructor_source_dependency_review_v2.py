from pathlib import Path
import hashlib,json,sys,importlib.util,ast
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};reads={};oldb=Path.read_bytes;oldt=Path.read_text
 def pin(p):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();pins[str(p)]=v;return p
 def rb(p):
  b=oldb(p);reads[str(Path(p).resolve())]=hashlib.sha256(b).hexdigest();return b
 def rt(p,*a,**k):
  v=oldt(p,*a,**k);pin(p);reads[str(Path(p).resolve())]=pins[str(Path(p).resolve())];return v
 Path.read_bytes=rb;Path.read_text=rt
 def load(p,n):
  p=pin(R/p);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 m=load('tools/m4-constructor-native/game_model_v5.py','dependency_model');program,cb=m.source_program(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json')
 objects=[m,m.P,m.P.P,m.P.P.P,m.G,m.I];modules=[]
 for ob in objects:
  if hasattr(ob,'__file__'):
   path=pin(ob.__file__);ast.parse(oldt(path));modules.append(str(path))
 # Exact preserved v4 body plus one precise msize family; source_program appends accepted registry rows.
 a=oldt(R/'tools/m4-constructor-native/game_model_v4.py');b=oldt(R/'tools/m4-constructor-native/game_model_v5.py');marker="          'free':(0x7800139f,0x780013a5,0x780013a6,0x78001416,0x78001419)}";replacement="          'free':(0x7800139f,0x780013a5,0x780013a6,0x78001416,0x78001419),\n          'msize':(0x7800152c,0x78001532,0x78001533,0x78001596,0x78001599)}";assert a.count(marker)==1;expected=a.replace(marker,replacement);assert b.startswith(expected);append=b[len(expected):];assert 'def source_program(preparation):'in append
 for path,h in reads.items():assert pin(path)and pins[path]==h
 pin(R/'tools/m4-constructor-native/game_model_v4.py');pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact inherited literal module dependency/source_program reads and preserved v4 prefix inverse; msize family and accepted registry descriptors additive. Source execution/acceptance separate.',program_rows=len(program),callback_sites=len(cb),model_modules=modules,source_descriptor_reads=reads,v4_full_prefix_inverse=True,v5_addition=append,canonical_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
