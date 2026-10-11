"""Exact additive first-writer controller; does not run a worker."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh FPS controller preparation');out.mkdir()
 old=R/'tools/m4-widget-native/run_fixture_v5.py';target=R/'tools/m4-fps-native/run_fixture.py';need(not target.exists(),'Fresh seven-root controller');source=old.read_text();changes=[]
 def replace(a,b,n=1):
  nonlocal source
  need(source.count(a)==n,'Exact inherited controller text '+a);source=source.replace(a,b);changes.append(dict(before=a,after=b,count=n))
 replace('reports/m4-widget-native','reports/m4-fps-native',3)
 replace("036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98","fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7",2)
 replace("58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401","e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc",2)
 replace('fixture-build-r13','fixture-build-r1');replace('fixture-preparation-r16','fixture-preparation-r1')
 replace('(1,1,6,52,0,0,0,0)','(1,1,7,58,0,0,0,0)');replace('Six measured registered root routes complete','Seven measured registered root routes complete')
 replace("final=capture/'phase-5'","final=capture/'phase-6'")
 replace('24643*24','25003*24');replace('147*1488','149*1488');replace('505*32','511*32');replace('579*32','588*32')
 replace("# Ordinary file witnesses only. No canonical payload/index reader is opened.","need((final/'formats.bin').stat().st_size==2528,'One whole actual literal vsprintf entry/return record');need((final/'format-dispatches.bin').stat().st_size==3*32,'Three actual literal readonly character dispatches')\n   # Ordinary file witnesses only. No canonical payload/index reader is opened.")
 replace('Six registered widget Runtime roots through current accepted source registry service and real native GDI; measured worker structure only, no source/native equivalence or connected136 acceptance','Seven registered widget/FPS Runtime roots through literal vsprintf and current accepted source registry service with actual native GDI; measured worker structure only, no source/native equivalence or connected138 acceptance')
 replace('Run only the exact independently admitted widget fixture, never game UI.','Run only the exact independently admitted seven-root widget/FPS fixture, never game UI.')
 ast.parse(source);target.write_text(source)
 q=out/'controller-source-relations.json';q.write_text(json.dumps(changes,indent=2)+'\n')
 files={str(p.resolve()):sha(p)for p in(old,target,q,Path(__file__),R/'tools/m4-pipeline/stages.py',R/'reports/m4-fps-native/fixture-preparation-r1/report.json',R/'reports/m4-fps-native/fixture-build-r1/build.json')}
 report=dict(passed=True,scope='Seven-root controller prepared and parsed only; writer unlaunched',changes=len(changes),preparation_sha256='e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc',build_sha256='fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7',source_roots=7,literal_bodies=58,actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])
