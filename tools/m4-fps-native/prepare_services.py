"""Permit only the additional literal FPS callback in the existing service."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-fps-native'/name;assert not out.exists();out.mkdir();pins={};prior=R/'reports/m4-widget-native/service-preparation-r3';report=prior/'report.json';assert sha(report)=='3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd';old=json.loads(report.read_bytes());pins[str(report)]=sha(report);relations=[]
 for p in prior.iterdir():
  if not p.is_file()or p.name=='report.json':continue
  q=out/p.name;shutil.copyfile(p,q);pins[str(p)]=sha(p);relations.append(dict(name=p.name,prior_path=str(p),prior_sha256=sha(p),current_path=str(q)))
 p=out/'session_impl.inc';s=p.read_text();a='case 0x479590:callback=0x4795d0;break;default:';b='case 0x479590:callback=0x4795d0;break;case 0x40f000:callback=0x40f030;break;default:';assert s.count(a)==1;s=s.replace(a,b).replace('six normal widget roots','seven normal widget/FPS roots');p.write_text(s)
 for row in relations:row['current_sha256']=sha(row['current_path']);row['byte_identical']=row['current_sha256']==row['prior_sha256'];pins[row['current_path']]=row['current_sha256']
 assert [x['name']for x in relations if not x['byte_identical']]==['session_impl.inc'];pins[str(Path(__file__).resolve())]=sha(__file__)
 result=dict(old);result.update(scope='Finite7-route extension of current accepted borrowed source onexit service; only exact FPS callback added, no host onexit or output seed',native_library=str(out/'registry_library.cpp'),native_include=str(out),root_extension=0x40f000,source_callback=0x40f030,prior_service_preparation_sha256=sha(report),source_changes=[[a,b],['six normal widget roots','seven normal widget/FPS roots']],copied_source_relations=relations,changed_files=['session_impl.inc'],files=pins,native_executed=False,initializer_credit=0)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),source_files=len(relations))))
if __name__=='__main__':main(sys.argv[1])
