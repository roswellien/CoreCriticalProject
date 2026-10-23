"""ROOT whole source derivative inverses; no imports, reader or source run."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]

def main(name):
 out=R/'reports/m4-original141-source'/name
 assert not out.exists()
 files={};rows=[]
 def pin(p,h=None):
  p=(R/Path(p)).resolve()
  assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v)
  assert str(p)not in files or files[str(p)]==v
  files[str(p)]=v
  return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def text(p):return pin(p).read_text(encoding='utf-8')
 def receipt(p,h):
  v=read(p,h)
  for q,d in v['files'].items():pin(q,d)
  return v
 def replacements(parent,child,deltas):
  before=text(parent);after=text(child);s=before
  for d in deltas:
   assert s.count(d['old'])==d.get('occurrences',1)
   s=s.replace(d['old'],d['new'])
  assert s==after,'Whole forward equality'
  for d in reversed(deltas):
   assert s.count(d['new'])==d.get('occurrences',1)
   s=s.replace(d['new'],d['old'])
  assert s==before,'Whole inverse equality'
  ast.parse(after)
  rows.append(dict(parent=str(pin(parent)),child=str(pin(child)),hunks=len(deltas),whole_inverse=True))
 def linedeltas(row):
  before=text(row['parent']);after=text(row['child']);a=before.splitlines(keepends=True);b=after.splitlines(keepends=True)
  for d in row['deltas']:
   assert ''.join(a[d['parent_start']:d['parent_stop']])==d['parent']
   assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(row['deltas']):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(keepends=True)
  assert ''.join(b)==before,'Whole unchanged-line inverse'
  ast.parse(after)
  rows.append(dict(parent=row['parent'],child=row['child'],hunks=len(row['deltas']),whole_inverse=True))
 base=R/'reports/m4-original141-source'
 v=receipt(base/'readiness-r1/report.json','1028fb7d2e2d093dae2e1e00243ef24b5d271c7a8841754d2f971cce0d0833cd')
 for row in v['derivatives']:replacements(row['parent'],row['child'],row['replacements'])
 receipt(base/'source-preparation-r1/report.json','b2a1251c8a36dec92eaa794f46a1d18096124c44030592f07293fc1a4467d59b')
 for row in read(base/'source-preparation-r1/inverse.json'):replacements(row['parent'],row['child'],row['replacements'])
 receipt(base/'family-preparation-r2/report.json','15b8a867f8a8b049947c69f0546cf6a7b51666e154c48a3b4e4a81980f40e272')
 for row in read(base/'family-preparation-r2/inverse.json'):linedeltas(row)
 receipt(base/'old4-preparation-r1/report.json','755dca1156098f648c5a9ba8f719741ee52547cf7721822dbb9756a6c882defb')
 replacements('tools/m4-startup138-original/old4_source_r6.py','tools/m4-original141-source/old4_source141_v1.py',read(base/'old4-preparation-r1/inverse.json'))
 receipt(base/'controller-preparation-r2/report.json','216291d75a1504d0a27a13da4dd392855efe21b4321a5e204e6f20230ef57bba')
 for row in read(base/'controller-preparation-r2/inverse.json'):linedeltas(row)
 receipt(base/'controls-preparation-r1/report.json','d76f9ea5c69993f5407c56f356c36a123408a2f885711e8f5bc74ce1d8aec024')
 receipt(base/'root-input-metadata-r1/report.json','eb73abbf388a8407a5f412755675e5f611ef70cfdb8698b9b450f3476c0cbe67')
 pin(__file__);pin(sys.executable)
 for p,h in files.items():pin(p,h)
 out.mkdir()
 result=dict(passed=True,scope='Whole original141 source derivative inverses and current metadata physical conservation; no import/source endpoint validation or execution admission',rows=rows,known_pending_widget_cleanup_phase=True,source_execution_admitted=False,source_evaluated=False,reader_opened=False,worker_launched=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n')
 print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
