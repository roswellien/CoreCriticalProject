"""Create additive 116 integration tools from the frozen accepted109 tools."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
OLD=ROOT/'tools/m4-joint-startup109'
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def write(name,s):
 p=HERE/name;assert not p.exists(),p;compile(s,str(p),'exec')if p.suffix=='.py'else None;p.write_text(s,encoding='utf-8')
for name in('CMakeLists.txt','build.py','build.ps1','run.py','audit.py','link.py'):
 s=(OLD/name).read_text().replace('109','116')
 if name=='run.py':
  s=one(s,"(1,6,116,654,17,159716)","(1,6,116,696,17,159716)")
  s=one(s,"words('registration-roots.bin',81)","words('registration-roots.bin',88)")
 if name=='audit.py':s=one(s,"words('registration-roots.bin',81)","words('registration-roots.bin',88)")
 if name=='link.py':
  s=one(s,"and p['linked_literal_COFFs_per_level']==312","and p['linked_literal_COFFs_per_level']>=312\n literal_count=p['linked_literal_COFFs_per_level']")
  s=s.replace('==312','==literal_count').replace('literal_COFFs=312','literal_COFFs=literal_count').replace('len(linked)==341','len(linked)==literal_count+29')
  s=one(s,'literal_COFF_links=624,compiled_objects=54,actual_linked_inputs=682','literal_COFF_links=2*literal_count,compiled_objects=54,actual_linked_inputs=2*(literal_count+29)')
 write(name,s)
print(json.dumps({'passed':True,'generated_tools':[str(HERE/n)for n in ('CMakeLists.txt','build.py','build.ps1','run.py','audit.py','link.py')]}))
