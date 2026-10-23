"""Version adapter on current141 service, with exact reversible source deltas."""
from pathlib import Path
import difflib,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def method(s):
 start=s.index(' void borrow_widget_onexit(State&source,');body=s.index('{',start);depth=0
 for i in range(body,len(s)):
  if s[i]=='{':depth+=1
  if s[i]=='}':
   depth-=1
   if not depth:return s[start:i+1]
 raise ValueError('Unclosed method')
def merge(old,new,current):
 a,b=old.splitlines(True),new.splitlines(True);changes=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if tag=='equal':continue
  before,after=''.join(a[i:j]),''.join(b[k:l])
  if not before:
   candidates=[]
   if i:candidates.append((''.join(a[i-1:i]),''.join(a[i-1:i])+after))
   if i<len(a):candidates.append((''.join(a[i:i+1]),after+''.join(a[i:i+1])))
  else:candidates=[(before,after)]
  candidates=[(x,y)for x,y in candidates if current.count(x)==1 and y and current.count(y)==0]
  assert candidates,('Exact unique nonoverlapping source anchor',tag,i,j)
  before,after=candidates[0];current=current.replace(before,after,1);changes.append(dict(before=before,after=after))
 return current,changes
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,str(p);pins[str(p)]=v;return p
 current=R/'reports/m4-startup141-runway/service-preparation-r1';version=R/'reports/m4-version-source/service-preparation-r4';ancestor=R/'reports/m4-widget-native/service-preparation-r3'
 c=json.loads(pin(current/'report.json','6edf61e7b56bb178a6b1dbbb5a0b647af4099272cb59a80f3e277267c435aade').read_bytes())
 v=json.loads(pin(version/'report.json').read_bytes());assert c['passed']and v['passed']
 for p,h in v['files'].items():
  q=Path(p)
  if q.parent in(version,ancestor):pin(q,h)
 for p,h in c['files'].items():
  if Path(p).parent==current:pin(p,h)
 old=(ancestor/'session_impl.inc').read_text();new=(version/'session_impl.inc').read_text();base=(current/'session_impl.inc').read_text()
 oldmethod,newmethod,basemethod=method(old),method(new),method(base)
 addition='case 0x4af240:callback=0x4af270;break;'
 assert newmethod.replace(addition,'',1)==oldmethod
 normalized=new.replace(newmethod,oldmethod,1)
 merged,changes=merge(old,normalized,base)
 assert method(merged)==basemethod
 anchor='case 0x459b40:callback=0x459b70;break;default:';assert basemethod.count(anchor)==1
 finalmethod=basemethod.replace(anchor,anchor.replace('default:',addition+'default:'),1)
 merged=merged.replace(basemethod,finalmethod,1);changes.append(dict(before=basemethod,after=finalmethod))
 header,hchanges=merge((ancestor/'session.hpp').read_text(),(version/'session.hpp').read_text(),(current/'session.hpp').read_text())
 for final,original,rows in[(merged,base,changes),(header,(current/'session.hpp').read_text(),hchanges)]:
  restored=final
  for row in reversed(rows):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'],1)
  assert restored==original
 assert finalmethod.replace(addition,'',1)==basemethod
 out.mkdir(parents=True)
 for p in current.iterdir():
  if p.is_file()and p.name!='report.json':shutil.copyfile(pin(p),out/p.name)
 (out/'session_impl.inc').write_text(merged);(out/'session.hpp').write_text(header)
 extras=[]
 for p in version.iterdir():
  if p.is_file()and p.name!='report.json'and not(current/p.name).exists():shutil.copyfile(pin(p),out/p.name);extras.append(p.name)
 deltas=dict(session_impl=changes,session_header=hchanges,version_callback=addition,extra_files=extras)
 (out/'current-union-delta.json').write_text(json.dumps(deltas,indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 pin(__file__);pin(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Unexecuted version service adapter union with current141 constructor/FPS/growth service; no carried input admission',native_include=str(out),native_library=str(out/'registry_library.cpp'),current141_service_sha256=sha(current/'report.json'),version_service_sha256=sha(version/'report.json'),exact_inverse_restores_current141=True,entire_current141_borrow_method_retained_except_version_case=True,version_adapter_source_changes_identical=True,changed_current_files=['session.hpp','session_impl.inc'],extra_files=extras,worker_executed=False,execution_admitted=False,initializer_credit=0,independent_review_pending=True,carried_original_source_pair_controls_pending=True,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])
