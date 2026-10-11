"""Direct-bound seven-root build/run controllers; no target execution."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 pins={}
 for name in('build.ps1','run.py'):
  p=R/'tools/m4-font479590-original'/name;pins[str(p)]=sha(p);s=p.read_text(encoding='utf-8-sig').replace('reports/m4-font479590-original','reports/m4-fps-original')
  if name=='build.ps1':
   if s.count('phases=6;roots=6')!=1:raise ValueError('Exact build geometry')
   s=s.replace('phases=6;roots=6','phases=7;roots=7').replace('snapshot_bytes=266964;direct_primary','snapshot_bytes=266964;fps_snapshot_bytes=529700;direct_primary')
  else:s=s.replace('Genuine carried five-widget plus479590 original normal execution only','Genuine carried five-widget plus479590 plus40F000 fps original normal execution only')
  q=D/name
  if q.exists():raise ValueError('Fresh derivative controller')
  q.write_text(s)
 p=Path(__file__).resolve();pins[str(p)]=sha(p);q=D/'controllers-lineage.json';q.write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main()
