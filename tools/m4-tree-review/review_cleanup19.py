"""Independent source-only cleanup transition review. No capture payload reads."""
from pathlib import Path
import json,sys,hashlib
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or a==h,(p,h,a);pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=read(R/'reports/m4-formatting-native/preparation-r18/report.json','68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06')
 new=read(R/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 a,b=Path(old['native_include']),Path(new['native_include']);rows=[]
 names={Path(p).name for p in new['files']if Path(p).parent==b}
 assert len(names)==71
 for n in sorted(names):
  x=pin(a/n,old['files'][str(a/n)]).read_bytes();y=pin(b/n,new['files'][str(b/n)]).read_bytes()
  if n=='session_impl.inc':
   s=x.decode();before='  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();\n  try{\n   if(r.poisoned())poison();'
   after='  if(r.poisoned()&&!failed)poison();\n  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();\n  try{'
   assert s.count(before)==1 and s.replace(before,after).encode()==y
  else:assert x==y,n
  rows.append(dict(name=n,old_sha256=sha(a/n),new_sha256=sha(b/n),whole_byte_identical=x==y))
 assert sum(r['whole_byte_identical']for r in rows)==70
 assert old['entry_objects']==new['entry_objects'] and new['live_owner_bound']==old['live_owner_bound']==92
 for p,h in new['entry_objects'].items():pin(p,h)
 current=(b/'session_impl.inc').read_text();assert current.index('if(r.poisoned()&&!failed)poison();',current.index(' void finish(){'))<current.index('InvocationHostBoundary host;',current.index(' void finish(){'))
 assert 'void pause()'in current and 'lb::binding=nullptr' in current
 pin(__file__)
 target=out/'report.json';target.write_text(json.dumps(dict(passed=True,scope='Independent physical 71-source native18/native19 relation and precise first-fault cleanup binding order; executable controls remain required',native18_sha256=sha(a/'report.json'),native19_sha256=sha(b/'report.json'),copied_source_files=71,whole_byte_identical_source_files=70,exact_source_transitions=1,literal_object_identities=len(new['entry_objects']),live_owner_bound=92,normal_source_bodies_changed=False,capture_archives_opened=0,initializer_credit=0,relations=rows,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
