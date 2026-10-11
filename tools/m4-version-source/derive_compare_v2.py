"""Explicit sole original reader/native2 ordinary roles and capture manifests."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
p=P/'compare_v1.py';s=p.read_text()
s=once(s,"pins[str(p)]=v;return p","need(str(p)not in pins or pins[str(p)]==v,'Stable reopened comparison physical input');pins[str(p)]=v;return p")
a="  pin(__file__);helper=pin(R/'tools/m4-crt-allocation-root/run_v2.py')"
b="""  need(gate['sole_original_reader_lease']is True and gate['original_input_role']=='single_original4_transport'and gate['native_input_role']=='direct_ordinary_closed_native2','Explicit independent sole original reader and direct closed-native2 input roles')
  need(oe['preparation_sha256']=='7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529'and oe['build_sha256']=='fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292'and ne['preparation_sha256']=='ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee'and ne['build_sha256']=='d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42','Exact isolated original4/native2 frozen source/candidate roles')
  transport=pin(Path(oe['run']['capture'])/'transport.json',oe['run']['transport_sha256']);metadata=json.loads(transport.read_bytes());need(metadata['logical_files']<=2048 and metadata['payload_bytes']<=256*1024*1024 and len(metadata['parts'])<=8,'Bounded single-root original payload before sole strict reader opens')
  pin(R/'tools/m4-version-source/compare_v1.py','"""+sha(p)+"""');pin(R/'tools/m4-version-source/derive_compare_v2.py');pin(__file__);helper=pin(R/'tools/m4-crt-allocation-root/run_v2.py')"""
s=once(s,a,b)
a="   root=Path(ne['runs'][level]['capture'])\n   def native(n):return pin(root/n).read_bytes()"
b="""   root=Path(ne['runs'][level]['capture']);need(ne['runs'][level]['passed']and root.parent==Path(native_report).resolve().parent and root.name==level,'Exact closed ordinary native2 optimization-level capture role');manifest_path=pin(ne['runs'][level]['output_manifest'],ne['runs'][level]['output_manifest_sha256']);manifest=json.loads(manifest_path.read_bytes())
   def native(n):
    need(n in manifest and Path(n).suffix.lower()not in('.mwb','.zip'),'Required direct ordinary native witness from exact controller output manifest');p=pin(root/n,manifest[n]['sha256']);b=p.read_bytes();need(len(b)==manifest[n]['bytes'],'Whole native manifest-bound witness extent');return b"""
s=once(s,a,b)
s=once(s,"region=pin(p).read_bytes();native_object=region[","region=native(str(p.relative_to(root)).replace('\\\\','/'));native_object=region[")
s=once(s,"base=int(f.stem.removeprefix('game-region-'));a=pin(f).read_bytes();b=pin(root/'phase-0'/'after'/f.name).read_bytes();","base=int(f.stem.removeprefix('game-region-'));a=native('phase-0/before/'+f.name);b=native('phase-0/after/'+f.name);")
s=once(s,"archive_reader_opened=opened,all_archive_readers_closed=closed or not opened,","archive_reader_opened=opened,all_archive_readers_closed=closed or not opened,sole_original_reader=True,original_payload_bound_bytes=256*1024*1024,native_payload_role='direct ordinary manifest-bound native2',")
q=P/'compare_v2.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');print(json.dumps(dict(path=str(q),sha256=sha(q),archive_reader_opened=False)))
