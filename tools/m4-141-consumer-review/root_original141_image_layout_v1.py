"""Actual rebuilt PE geometry and whole compiler closure; no execution."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,v,h);assert files.setdefault(str(p),v)==v;return p
folder=R/'reports/m4-original141/build-r2';b=json.loads(pin(folder/'build.json').read_bytes());assert b['passed'] and not b['original_executed'] and not b['native_executed']
assert Path(b['preparation'])==R/'reports/m4-original141/source-preparation-r6' and b['preparation_sha256']=='a54ece9c861485fb2e121bc1733550e0d0ab462199d85de83a2894fc72702b6c'
for p,h in json.loads(pin(folder/'pins.json').read_bytes())['files'].items():pin(p,h)
im=PEImage(pin(b['worker'],b['worker_sha256']).read_bytes());assert im.machine==0x14c and im.image_base==0x28000000 and im.size_of_image==0xA113000
broker=pin(Path(b['preparation'])/'original_broker.hpp').read_text();m=re.search(r'array<std::uint32_t,36> bases\{([^}]+)\}',broker);assert m
bases=[int(x,16) for x in m[1].split(',')];assert len(bases)==len(set(bases))==36
assert all(not(im.image_base<a+65536 and a<im.image_base+im.size_of_image) for a in bases)
old=json.loads(pin(R/'reports/m4-original141/build-r1/build.json').read_bytes());prior=PEImage(pin(old['worker'],old['worker_sha256']).read_bytes());assert im.sections==prior.sections
pin(__file__);pin(R/'tools/analysis/pe.py');assert all(sha(p)==h for p,h in files.items())
out=R/'reports/m4-original141/root-image-layout-r1';out.mkdir();p=out/'report.json'
p.write_text(json.dumps(dict(passed=True,actual_PE32_image_base=im.image_base,actual_size_of_image=im.size_of_image,actual_image_end=im.image_base+im.size_of_image,all36_guest_reservations_disjoint=True,whole_section_geometry_unchanged=True,worker_executed=False,worker_launch_admitted=False,whole_linked_relocations_pending=True,initializer_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(sha(p),len(files))
