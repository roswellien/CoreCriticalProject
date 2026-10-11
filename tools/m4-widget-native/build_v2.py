"""Add the actual startup loader include directory to the frozen compiler."""
from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent;base=p/'build.py'
expected='b6ccad98671bb7c6d91f3a3b3ce5df7a13c2149e5238a1c22c45dbf5bb0e01f4'
# The checked base digest is supplied from the preserved preparation file map.
import json,sys
R=p.parents[1]
report=json.loads((R/sys.argv[1]).read_text())
actual=hashlib.sha256(base.read_bytes()).hexdigest()
assert report['files'][str(base)]==actual
s=base.read_text()
s=s.replace("'-I',R/'tools/m4-runtime','-I',R/'runtime'","'-I',R/'tools/m4-runtime','-I',R/'tools/m4-startup','-I',R/'runtime'")
s=s.replace("for p in (clang,lib,nm,Path(__file__).resolve(),R/'tools/m4-widget-native/build.ps1')", "for p in (clang,lib,nm,base,Path(__file__).resolve(),R/'tools/m4-widget-native/build_v2.ps1',R/'tools/m4-widget-native/build.ps1')")
exec(compile(s,str(base),'exec'),globals())
