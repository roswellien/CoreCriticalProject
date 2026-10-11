"""Correct the copied Session declaration; no body or literal changes."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 pp=R/'reports/m4-joint-startup138/preparation-r1/report.json';assert sha(pp)=='a3cd89ab7f0a9697de31594313892979bdeaa1ae2a7070958be40312254024b2';d=json.loads(pp.read_bytes());out=pp.parent.parent/name;assert not out.exists();out.mkdir();pins=dict(d['files']);pins[str(pp.resolve())]=sha(pp);copies=[];generated={}
 for p,h in pins.items():assert Path(p).suffix.lower()not in('.mwb','.zip')and sha(p)==h
 for p in pp.parent.rglob('*'):
  if p.is_file()and p.name!='report.json':
   q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes();b=raw.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(b);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),initial_sha256=sha(q),path_rebase=raw!=b))
 p=out/'onexit_session.hpp';old=p.read_text();a=' void finish();void dump(Sink,void*)const;';assert old.count(a)==1;new=old.replace(a,' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);\n'+a);p.write_text(new)
 service=R/'reports/m4-fps-native/service-preparation-r2/session.hpp';assert p.read_bytes()==service.read_bytes(),'Complete current service declaration identity';pins[str(service.resolve())]=sha(service)
 for row in copies:row['current_sha256']=sha(row['target']);row['byte_identical']=row['source_sha256']==row['current_sha256']
 for p in out.rglob('*'):
  if p.is_file():pins[str(p.resolve())]=sha(p);generated[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable)
 d.update(passed=True,parent_preparation_sha256=sha(pp),prior_copy_relations=copies,generated_sources=generated,files=pins,additive_declaration_change=dict(file='onexit_session.hpp',relation='One missing borrowed service method declaration; complete file identical to actually compiled service header',service_sha256=sha(service)),worker_executed=False,execution_admitted=False,initializer_credit=0)
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
