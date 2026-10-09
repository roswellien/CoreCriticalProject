"""Fresh exact-worker captures; stdout/stderr and all partial failures retained."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def main():
 build,out=map(lambda p:Path(p).resolve(),sys.argv[1:3]);assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists()
 doc=json.loads((build/'build.json').read_text());assert doc['passed']
 for path,digest in doc['bindings'].items():assert sha(path)==digest,path
 worker=Path(doc['original_worker']);out.mkdir(parents=True);commands=[]
 def run(name,args):
  r=subprocess.run(list(map(str,args)),capture_output=True,timeout=190);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);commands.append({'name':name,'command':list(map(str,args)),'exit_code':r.returncode});return r.returncode
 try:
  assert run('protocol',[worker,'--check-protocol'])==0
  assert run('publisher',[worker,'--check-publication',out/'publication-controls'])==0
  common=[worker,ROOT/'reports/m4-fp-numeric-max/recovery-r1/pages.bin',ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL']
  assert run('default',common+[out/'default.bin'])==0
  assert run('directed',common+[out/'directed.bin','--directed'])==0
  passed=True
 except Exception as error:passed=False;(out/'failure.txt').write_text(repr(error))
 report={'passed':passed,'scope':'Actual isolated provider/game capture; no full DLL initialization or shared Runtime admission','commands':commands,'build':bind(build/'build.json'),'source':bind(__file__),'worker':bind(worker),'artifacts':[bind(p) for p in out.rglob('*') if p.is_file()]}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':passed,'out':str(out)}));assert passed
if __name__=='__main__':main()
