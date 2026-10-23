"""Production raw owning-cell assertion controls, no capture reader."""
from pathlib import Path
import ast,hashlib,json,struct
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/constructor-input141-cell-controls-r2';out.mkdir();p=R/'tools/m4-141-consumer-review/constructor_input141_v1.py';s=p.read_text(encoding='utf-8');tree=ast.parse(s)
 assertion=next(n for n in ast.walk(tree)if isinstance(n,ast.Assert)and 'before['in ast.unparse(n.test));expr=compile(ast.Expression(assertion.test),str(p),'eval');f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='words');env=dict(struct=struct);exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),'exec'),env)
 cells=(0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040);results=[]
 for i,cell in enumerate(cells):
  for mutation in (False,True):
   page=bytearray(4096);raw=0x2802c8fc+i*16;struct.pack_into('<I',page,cell%4096,raw+int(mutation));env.update(before={0x7802e000:page},cell=cell,raw=raw);got=bool(eval(expr,env));assert got==(not mutation);results.append(dict(kind=i,altered_own_BEFORE_cell=mutation,passed=True))
 files={str(p):hashlib.sha256(p.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};q=out/'report.json';q.write_text(json.dumps(dict(passed=True,production_assertion=ast.unparse(assertion.test),controls=results,canonical_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main()
