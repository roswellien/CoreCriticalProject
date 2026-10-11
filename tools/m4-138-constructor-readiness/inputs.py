"""Fresh hash closure of inputs explicitly consumed by admitted r8 controller."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists()
 pins={};expected={}
 def read(relative,h=None):
  p=(R/relative).resolve();v=sha(p);assert h is None or v==h; pins[str(p)]=v;return json.loads(p.read_bytes())
 def merge(d):
  for p,h in d.items():
   assert Path(p).suffix.lower()not in('.zip','.mwb'),'Ordinary inputs only'
   assert p not in expected or expected[p]==h,'No conflicting physical input'
   expected[p]=h
 admitted=read('reports/m4-constructor-native/admitted-controller-r1/report.json','f9a45fe0f08c3cbccdde1b5d8f01b406ffadc5d7a2ea7077bbb47a9e546c472b')
 a=read('reports/m4-tree-review/constructor-native37-prelaunch-r4/report.json',admitted['preflight_sha256'])
 b=read('reports/m4-constructor-native/fixture-build-r8/build.json',admitted['build_sha256'])
 p=read('reports/m4-constructor-native/fixture-preparation-r4/report.json',admitted['preparation_sha256'])
 assert all(x['passed']for x in(a,b,p))and b['preparation_sha256']==admitted['preparation_sha256']
 for x in(a,b,p):merge(x['files'])
 for level in('O0','O2'):
  worker=b['workers'][level];assert a['files'][str(Path(worker['path']).resolve())]==worker['sha256'];merge({worker['path']:worker['sha256']})
 merge({str((R/'MW3/Mech3.exe').resolve()):'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
        str((R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').resolve()):'91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a',
        str((R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve()):'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
        str((R/'local/mw3-staged/Shared_DLLs/MFC42.DLL').resolve()):'5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8',
        admitted['controller_path']:admitted['controller_sha256']})
 paths=sorted(expected)
 with ThreadPoolExecutor(max_workers=4)as pool:
  for path,digest in zip(paths,pool.map(sha,paths)):
   assert digest==expected[path],path;pins[path]=digest
 for path in (Path(sys.executable).resolve(),R/'tools/m4-pipeline/stages.py',Path(__file__).resolve()):pins[str(path)]=sha(path)
 service=read('reports/m4-constructor-native/service-preparation-r5/report.json','61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761')
 assert service['passed']and service['initializer_credit']==0
 executions=sorted(q.name for q in(R/'reports/m4-constructor-native').iterdir()if q.is_dir()and 'execution' in q.name)
 assert executions==['fixture-execution-r1'],'Unexpected newer execution needs inspection'
 report=dict(passed=True,scope='Fresh ordinary physical closure of all explicitly pinned a/b/p/worker/PE inputs consumed by admitted r8 controller; no writer or capture reader',
  native_execution_performed=False,archive_reader_opened=False,initializer_credit=0,
  ordinary_expected_inputs_verified=len(expected),existing_execution_names=executions,
  controller=admitted['controller_path'],controller_sha256=admitted['controller_sha256'],
  planned_argv=['C:\\Python314\\python.exe','-B',admitted['controller_path'],*admitted['planned_arguments']],
  remaining='Root must choose a fresh execution name and scheduling slot. Writer success then requires strict whole source/provider/state/owned-resource validation, controls, independent review and full carried integration; no full144 credit from isolated37 fixture.',files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),verified=len(expected))))
if __name__=='__main__':main(sys.argv[1])
