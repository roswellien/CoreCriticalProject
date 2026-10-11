"""Pin current mapped-source fixture without launching a worker."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-fps-native'/name;assert not out.exists();out.mkdir();parent=R/'tools/m4-fps-native/run_fixture.py';target=R/'tools/m4-fps-native/run_fixture_v2.py';assert not target.exists();t=parent.read_text();changes=[]
 for a,b,n in [('fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7','636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a',2),('e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc','bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0',2),('reports/m4-fps-native/fixture-build-r1','reports/m4-fps-native/fixture-build-r2',1),('reports/m4-fps-native/fixture-preparation-r1','reports/m4-fps-native/fixture-preparation-r2',1)]:
  assert t.count(a)==n,(a,t.count(a));t=t.replace(a,b);changes.append(dict(before=a,after=b,count=n))
 marker="   # Ordinary file witnesses only. No canonical payload/index reader is opened."
 assert t.count(marker)==1
 t=t.replace(marker,"""   page_contract=json.loads(pin(R/'reports/m4-fps-native/fixture-preparation-r2/provider-page-contracts.json').read_bytes())
   for page in page_contract['pages']:
    address=page['address'];stem=capture/'provider-mapping'/('page-'+str(address));row=words(Path(str(stem)+'-row.bin'),6);need(row[:4]==(1,address,page['file_offset'],page['permissions'])and row[4:6]in((0,1),(1,0)),'Exact current physical mapping disposition')
    physical=pin(Path(str(stem)+'-physical.bin'),page['sha256']).read_bytes();after=pin(Path(str(stem)+'-after.bin').read_bytes() if False else Path(str(stem)+'-after.bin')).read_bytes();need(len(physical)==len(after)==4096,'Complete mapped/provider admission payloads')
    if row[4]:need(after==physical,'Absent page receives whole own physical payload')
    else:need(pin(Path(str(stem)+'-before.bin')).read_bytes()==after,'Every prior provider payload preserved exactly')
    for phase in range(7):
     for side in('before','after'):need(len(pin(capture/f'phase-{phase}'/side/f'provider-source-page-{address}.bin').read_bytes())==4096,'Whole current provider phase endpoint')
   # Ordinary file witnesses only. No canonical payload/index reader is opened.""")
 ast.parse(t);target.write_text(t);q=out/'source-relations.json';q.write_text(json.dumps(changes,indent=2)+'\n');pins={str(p.resolve()):sha(p)for p in(parent,target,q,Path(__file__),R/'reports/m4-fps-native/fixture-preparation-r2/report.json',R/'reports/m4-fps-native/fixture-build-r2/build.json',R/'reports/m4-fps-native/fixture-preparation-r2/provider-page-contracts.json')};q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Current exact seven-route controller and finite physical mapping structure checks prepared only',controller=str(target),controller_sha256=sha(target),build_sha256='636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a',preparation_sha256='bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0',actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1])
