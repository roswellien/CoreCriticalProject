"""Create additive startup120 integration from immutable accepted116 files."""
from pathlib import Path
import json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).parent
OLD=ROOT/'tools/m4-joint-startup116'
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def write(name,s):
 p=HERE/name;assert not p.exists(),p
 if p.suffix=='.py':compile(s,str(p),'exec')
 p.write_text(s,encoding='utf-8')
for name in ('CMakeLists.txt','build.py','build.ps1','run.py','audit.py','link.py','loader_page_audit.py','stage_receipt.py','configuration.py','next_frontier.py'):
 s=(OLD/name).read_text().replace('116','120')
 if name=='run.py':
  s=one(s,'(1,6,120,696,17,159716)','(1,6,120,720,17,159716)')
  s=one(s,"words('registration-roots.bin',88)","words('registration-roots.bin',92)")
 if name=='audit.py':s=one(s,"words('registration-roots.bin',88)","words('registration-roots.bin',92)")
 write(name,s)
print(json.dumps(dict(passed=True,generated_tools=10)))
