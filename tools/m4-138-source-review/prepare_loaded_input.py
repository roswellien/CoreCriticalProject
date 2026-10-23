"""Current138 whole bootstrap page declaration; operand and carry proofs separate."""
from pathlib import Path
import ast, hashlib, sys
R=Path(__file__).resolve().parents[2]
BASE=R/'tools/m4-tree-review/prepare_loaded_input130.py'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
s=BASE.read_text()
changes=[
('reports/m4-startup130-original/validation-r2/report.json','reports/m4-startup138-original/original-validation-r3/report.json'),
('91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f'),
('reports/m4-joint-startup130/preparation-r2/report.json','reports/m4-joint-startup138/preparation-r4/report.json'),
('060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c',None),
]
jp=R/'reports/m4-joint-startup138/preparation-r4/report.json'
changes[-1]=(changes[-1][0],sha(jp))
for old,new in changes:
    assert s.count(old)==1,old
    s=s.replace(old,new)
old="need(joint['native_preparation_sha256']==sha(np),'Current broad preparation binds corrected19')"
new="""build=read(R/'reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47')
 service=read(joint['borrowed_service_preparation'],joint['borrowed_service_preparation_sha256'])
 library=pin(joint['native_library'],service['files'][str(Path(joint['native_library']).resolve())])
 need(build['passed'] and build['preparation_sha256']==sha(jp) and service['passed'] and service['native_library']==str(library) and build['files'][str(library)]==sha(library),'Actual current138 compiler consumes exact current FPS/growth service library; bootstrap endpoint equality remains separate')"""
assert s.count(old)==1
s=s.replace(old,new)
s=s.replace('pin(artifact);pin(__file__)', 'pin(artifact);pin(BASE);pin(__file__)')
s=s.replace('current130','current138').replace('complete130','complete138')
ast.parse(s)
exec(compile(s,str(BASE),'exec'),globals())
