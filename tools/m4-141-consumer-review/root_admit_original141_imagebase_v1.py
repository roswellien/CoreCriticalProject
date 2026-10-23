"""Independent finite linker-base review; admit compilation only."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,v,h);files[str(p)]=v;return p
for rel,h in [('imagebase-preparation-r3','1f58e197f0622c09bff2ac3241f7004b12f0f110a48fddea725581b83a146e16'),('source-preparation-r6','a54ece9c861485fb2e121bc1733550e0d0ab462199d85de83a2894fc72702b6c'),('imagebase-controls-r1','0fd990402679ecfa640435933da86fffda8a23d32c583f8102d5ce154b0a62f4')]:
 d=json.loads(pin(R/'reports/m4-original141'/rel/'report.json',h).read_bytes());assert d['passed']
 for p,v in d['files'].items():pin(p,v)
before=R/'reports/m4-original141/source-preparation-r3';after=R/'reports/m4-original141/source-preparation-r6'
names=[]
for p in sorted(before.iterdir()):
 if not p.is_file() or p.name in ('report.json','pins.json'):continue
 a=pin(p).read_bytes();b=pin(after/p.name).read_bytes()
 if p.name=='CMakeLists.txt':
  assert a.count(b'/BASE:0x18000000')==b.count(b'/BASE:0x28000000')==1
  assert b.replace(b'/BASE:0x28000000',b'/BASE:0x18000000')==a
 else:assert a==b
 names.append(p.name)
broker=(after/'original_broker.hpp').read_text();match=re.search(r'array<std::uint32_t,36> bases\{([^}]+)\}',broker);assert match
bases=[int(x,16) for x in match[1].split(',')];assert len(set(bases))==len(bases)==36
build=json.loads(pin(R/'reports/m4-original141/build-r1/build.json').read_bytes())
im=PEImage(pin(build['worker'],build['worker_sha256']).read_bytes());assert im.machine==0x14c and im.image_base==0x18000000
assert im.image_base<0x20010000 and 0x20000000<im.image_base+im.size_of_image
assert all(not (0x28000000<a+65536 and a<0x28000000+im.size_of_image) for a in bases)
for p,v in json.loads(pin(after/'pins.json').read_bytes())['files'].items():pin(p,v)
pin(R/'tools/m4-141-consumer-review/build_original141.ps1');pin(__file__);pin(R/'tools/analysis/pe.py')
assert all(sha(p)==h for p,h in files.items())
out=R/'reports/m4-original141/root-build-admission-r4';out.mkdir()
report=dict(passed=True,independent_review=True,compile_admitted=True,worker_launch_admitted=False,initializer_credit=0,exact_one_CMake_token_inverse=True,whole_payloads_reviewed=names,broker_regions=36,projected_image_end=0x28000000+im.size_of_image,actual_new_image_layout_pending=True,complete_linked_relocation_review_pending=True,files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(sha(out/'report.json'),len(files))
