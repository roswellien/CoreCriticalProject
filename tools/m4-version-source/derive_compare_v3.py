"""Bind the sole-reader comparison to original5 and its actual provider proof."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
p=P/'compare_v2.py';assert sha(p)=='385329543daff1416cf45ac9311f98057e8ad2dd9dd8a83f6d3758908b8085eb';s=p.read_text()
for a,b in [('7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529','149a328436631f8d7f7f579629deb2a8367bd3d1e76296cbaaaed14385c6fc30'),('fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292','85872a4a2a3932d1c2ab05c28aaad4e8b14a59d2137c9ff8b24e1dc45b75ed87')]:s=once(s,a,b)
s=s.replace('single_original4_transport','single_original5_transport').replace('original4/native2','original5/native2')
helper='''def original_provider_validation(data):
 setup=words(data('version-provider/setup.bin'),10,'Q');need(setup[0]==1 and setup[3]==0x78000000 and setup[1]!=setup[2]and setup[2]!=setup[3]and setup[7:]==(8,2,1),'Actual isolated system VERSION CRT/legacy owners and closed context before source')
 raw=data('version-provider/CRT-IAT.bin');bindings=list(struct.iter_unpack('<5Q',raw));need(len(bindings)==8,'Whole eight actual VERSION system CRT import cells')
 RVAs=(20796,20800,20804,20808,20812,20816,20820,20824)
 for i,b in enumerate(bindings):need(b[0]==RVAs[i]and b[1]==b[2]and b[1]and b[3]==setup[2]and b[4]==setup[3],'Every physical VERSION CRT import maps to its actual independently named system export')
 contexts=[]
 for i in range(2):
  b=data('version-provider/context-'+str(i)+'.bin');need(0<len(b)<=4096,'Whole actual private two-file DLL redirection record');contexts.append(dict(bytes=len(b),sha256=digest(b),whole_raw_hex=b.hex()))
 path=data('version-provider/VERSION-path.bin');CRT_path=data('version-provider/CRT-path.bin');need(path.decode('utf-16-le').replace(chr(92),'/').lower().endswith('/original-preparation-r5/system-version32/version.dll')and CRT_path.decode('utf-16-le').replace(chr(92),'/').lower().endswith('/original-preparation-r5/system-version32/msvcrt.dll'),'Actual frozen isolated system32 copied provider paths')
 return dict(setup=list(setup),whole_CRT_IAT_bindings=[list(b)for b in bindings],context_records=contexts,VERSION_path_hex=path.hex(),CRT_path_hex=CRT_path.hex(),VERSION_physical_sha256='4f66b88731e84be8e1545eefc589a79e701cca426ce916e4ac9322e60ea9680b',CRT_physical_sha256='23a918921c545140d189ce6dc68590bacdeb0ab2f3e3a9a2d722c5aff45ce64f',legacy_CRT_retained=True,context_inactive_before_source=True)

'''
s=once(s,'def original_validation(data):',''+helper+'def original_validation(data):\n provider=original_provider_validation(data)')
s=once(s,"need(data(p+'/file-sha.bin').decode()==IMAGE_SHA", "need(identity[1]==provider['setup'][1]and data(p+'/primary-path.bin').hex()==provider['VERSION_path_hex']and data(p+'/primary-sha.bin').decode()==provider['VERSION_physical_sha256'],'Actual source API uses the frozen byte-identical Windows VERSION primary module');need(data(p+'/file-sha.bin').decode()==IMAGE_SHA")
s=once(s,"return dict(record=rec,before=before,after=after,rows=rows,allocations=allocations,API_count=count//3)","return dict(record=rec,before=before,after=after,rows=rows,allocations=allocations,API_count=count//3,provider=provider)")
s=once(s,"entry=dict(level=level,caller_before=", "entry=dict(level=level,original_isolated_provider=o['provider'],caller_before=")
s=once(s,"pin(R/'tools/m4-version-source/derive_compare_v2.py');pin(__file__)","pin(R/'tools/m4-version-source/derive_compare_v2.py');pin(R/'tools/m4-version-source/compare_v2.py','385329543daff1416cf45ac9311f98057e8ad2dd9dd8a83f6d3758908b8085eb');pin(R/'tools/m4-version-source/derive_compare_v3.py');pin(__file__)")
q=P/'compare_v3.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');print(json.dumps(dict(path=str(q),sha256=sha(q),archive_reader_opened=False)))
