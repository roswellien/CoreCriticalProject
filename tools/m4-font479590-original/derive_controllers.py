"""Bind shared worker build/run/validator controllers to six measured roots."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def replace(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact controller derivation '+a[:70])
 return s.replace(a,b,1)
def main():
 pins={}
 for name in('build.ps1','run.py','validate_v2.py'):
  p=R/'tools/m4-widget-original'/name;pins[str(p)]=sha(p);s=p.read_text(encoding='utf-8-sig')
  s=s.replace('reports/m4-widget-original','reports/m4-font479590-original')
  if name=='build.ps1':
   s=replace(s,'phases=5;roots=5','phases=6;roots=6');target=out/name
  elif name=='run.py':
   s=replace(s,'Genuine bounded shared five-widget original normal execution only','Genuine carried five-widget plus479590 original normal execution only');target=out/name
  else:
   s=replace(s,'==(1,5,5,356992)','==(1,6,6,356992)');s=replace(s,'==(1,1,5,5,43,356992)','==(1,1,6,6,43,356992)');s=replace(s,"counts['actual_root_phases']==5","counts['actual_root_phases']==6");s=replace(s,'Complete actual five-root extent','Complete actual six-root extent')
   s=replace(s,"pin(R/'tools/m4-widget-original/derive_validate_v2.py');", "pin(R/'tools/m4-font479590-original/derive_controllers.py');")
   target=out/'validate.py'
  if target.exists():raise ValueError('Fresh controller '+str(target))
  target.write_text(s,encoding='utf-8')
 pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
 (out/'controllers-lineage.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
 print(json.dumps(dict(generated=['build.ps1','run.py','validate.py'],lineage_sha256=sha(out/'controllers-lineage.json'))))
if __name__=='__main__':main()
