"""Bind every referenced named common CPU/ENV/stack constant to final workers."""
from pathlib import Path
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[2];P={};rows=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;P[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
recipe=read(R/'reports/m4-version-source/common-caller-preparation-r1/common-caller.json');expected={'cpu':struct.pack('<10I',*recipe['CPU']),'env':bytes.fromhex(recipe['ENV28_hex']),'stack':bytes(recipe['stack_bytes'])}
original=read(R/'reports/m4-tree-review/version-original-common-prelaunch-r2/report.json','caa8b189a0da510dee164f3b54b51decd0d0662a110e77d5204f09adf1bf5f5d');native=read(R/'reports/m4-tree-review/version-native-common-prelaunch-r1/report.json','c1d894005c1a3e6f3273d12e34e3716a0dcffc0b2176a014e25013c95b6f6938');assert original['passed']and native['passed']
C32=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','data32');PE32=load(R/'tools/analysis/pe.py','dataPE32');C64=load(R/'tools/m4-tree-review/amd64_coff.py','data64');PE64=load(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','dataPE64');N=load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','bytes64')
def kind(name):return next((k for k in expected if name.startswith('?'+k+'@m4_version_common@mw34@@')),None)
obj=R/'reports/m4-version-source/original-build-r8/reference.obj';sy,se=C32.coff(pin(obj).read_bytes());image=PE32.PEImage(pin(R/'reports/m4-version-source/original-build-r8/original-worker.exe','6c26c4cf0f18a66e28278667ca926cfc6fea15dfbda79a90a4854acc9cb7e027').read_bytes());symbols={s['name']:s for s in sy.values()};links=read(R/'reports/m4-tree-review/version-original-common-prelaunch-r2/physical-links.json')
for proof in links:
 for rel in proof['relocations']:
  k=kind(rel['symbol'])
  if k is None:continue
  s=symbols[rel['symbol']];raw=expected[k];assert se[s['section']]['bytes'][s['value']:s['value']+len(raw)]==raw;va=rel['actual_symbol_address'];off,_=image.rva_range(va-image.image_base,len(raw));assert image.data[off:off+len(raw)]==raw;rows.append(dict(branch='original',symbol=rel['symbol'],caller=proof['symbol'],address=va,whole_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
native_links=read(R/'reports/m4-tree-review/version-native-common-prelaunch-r1/physical-links.json')
for level,workerhash in(('O0','43967fd9a66e28e3b4c3932acd88d2b036f226638a00a3c61e17237ed3d4c380'),('O2','fb2b0df7b674ef5e2d06caf9e00e1a381f8e46e07a78408748315ce9ece16d1a')):
 folder=R/'reports/m4-version-source/fixture-build-r3'/level;image=PE64.AMD64Image(pin(folder/'mw34_version.exe',workerhash).read_bytes());sy,se=C64.parse(pin(folder/'fixture.obj').read_bytes())
 for proof in native_links:
  if proof['level']!=level or Path(proof['object']).name!='fixture.obj':continue
  raw,rels=C64.function(sy,se,proof['symbol'])
  for rel in rels:
   s=rel['symbol'];k=kind(s['name'])
   if k is None:continue
   data=expected[k];assert se[s['section']]['bytes'][s['value']:s['value']+len(data)]==data;assert 4<=rel['type']<=9
   for address in proof['addresses']:
    actual=N.image_bytes(image,address,len(raw));o=rel['offset'];va=address+o+4+rel['type']-4+struct.unpack_from('<i',actual,o)[0]-struct.unpack_from('<i',raw,o)[0];assert N.image_bytes(image,va,len(data))==data;rows.append(dict(branch=level,symbol=s['name'],caller=proof['symbol'],address=va,whole_bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
assert rows and all(any(r['branch']==branch for r in rows)for branch in('original','O0','O2'));pin(__file__);out=R/'reports/m4-version-source/common-pair-data-admission-r1';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Every named common CPU/ENV/stack constant reference in currently attributed original/native caller functions has exact authored whole object and linked bytes',relations=rows,live_code_link_admission_uses_original_and_native_reports=True,unreferenced_or_inlined_named_constants_do_not_claim_separate_live_data=True,worker_launched=False,archive_reader_opened=False,initializer_credit=0,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest(),len(rows))
