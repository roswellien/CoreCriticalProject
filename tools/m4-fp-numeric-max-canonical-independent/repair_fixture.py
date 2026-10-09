"""Preserve failed independent build and make a separate fixture-only comment repair."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).resolve().parent
OUT=SRC/'r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 failed=ROOT/'reports/m4-fp-numeric-max-carry/independent-compiled-canonical-r1'
 assert 'use of undeclared identifier' in (failed/'O0-build.log').read_text()
 s=(SRC/'controls.cpp').read_text();a='t.sw.c1=0; // Independently specified bounded nonoverflow FLD effect.'
 assert s.count(a)==1;s=s.replace(a,'t.sw.c1=0; /* Independently specified bounded nonoverflow FLD effect. */')
 (OUT/'controls.cpp').write_text(s)
 (OUT/'boundary.s').write_bytes((SRC/'boundary.s').read_bytes())
 c=(SRC/'CMakeLists.txt').read_text().replace('${CMAKE_CURRENT_SOURCE_DIR}/../..','${CMAKE_CURRENT_SOURCE_DIR}/../../..');(OUT/'CMakeLists.txt').write_text(c)
 b=(SRC/'build.py').read_text().replace('parents[2]','parents[3]').replace("OUT=BASE/'independent-compiled-canonical-r1'","OUT=BASE/'independent-compiled-canonical-r2'")
 (OUT/'build.py').write_text(b)
 files={str(p):sha(p) for p in failed.rglob('*') if p.is_file()}
 files.update({str(p):sha(p) for p in SRC.iterdir() if p.is_file()})
 (OUT/'derivation.json').write_text(json.dumps(dict(scope='Only own C++ inline comment delimiter repaired; old literal fixture/build/logs retained. The // had accidentally hidden subsequent same-line bank/value declarations.',prior_failure_files=files,current_sources={str(OUT/n):sha(OUT/n) for n in ('controls.cpp','boundary.s','CMakeLists.txt','build.py')},production_changes=False),indent=2)+'\n')
 print(json.dumps(dict(preserved_files=len(files),repair='Own same-line comment delimiter only')))
if __name__=='__main__':main()
