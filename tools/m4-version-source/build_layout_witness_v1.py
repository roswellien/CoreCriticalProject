"""Actual x86 compiler layout/common-header assertions; no link or execution."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(preparation,expected,output):
 prep=(R/preparation).resolve();assert sha(prep)==expected;d=json.loads(prep.read_bytes());assert d['passed'];out=(R/output).resolve();assert not out.exists();out.mkdir(parents=True);pins={};error=None;headers=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 pin(__file__);pin(R/'tools/m4-version-source/build_layout_witness_v1.ps1');cl=pin(shutil.which('cl.exe'));src=pin(prep.parent/'layout_witness.cpp');obj=out/'layout_witness.obj';argv=[str(cl),'/nologo','/std:c++20','/O2','/EHsc','/W4','/WX','/MD','/showIncludes','/c','/I'+str(R/'reports/m4-version-source/original-preparation-r4'),'/I'+str(R/'tools/m4-capture-direct'),'/Fo'+str(obj),str(src)]
 try:
  c=subprocess.run(argv,cwd=out,capture_output=True,timeout=120,creationflags=0x08000000);a=out/'compile.stdout';b=out/'compile.stderr';a.write_bytes(c.stdout);b.write_bytes(c.stderr);pin(a);pin(b)
  for row in(c.stdout+c.stderr).decode(errors='replace').splitlines():
   if 'Note: including file:'in row:
    p=pin(row.split('Note: including file:',1)[1].strip())
    if p not in headers:headers.append(p)
  assert c.returncode==0,'Actual MSVC32 layout/common-caller compile';pin(obj);assert R/'tools/m4-version-source/common_caller_v1.hpp'in headers and R/'reports/m4-version-source/original-preparation-r4/reference.cpp'in headers
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in pins.items():assert sha(p)==h
 d=dict(passed=error is None,scope='Actual x86 compiler proves original Snapshot/Record offsets and complete common-caller header syntax; compile-only',preparation_sha256=expected,object=str(obj),object_sha256=sha(obj)if obj.is_file()else None,argv=argv,actual_compiler_headers=[str(p)for p in headers],worker_linked=False,native_or_original_executed=False,archive_reader_opened=False,files=pins,error=error);p=out/'build.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(p),sha256=sha(p),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
