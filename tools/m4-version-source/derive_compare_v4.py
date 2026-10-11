"""Retain comparison3 and add whole loaded/copy provider physical IDs."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
p=P/'compare_v3.py';assert sha(p)=='2b4f22cf66d0fe3e0f757de56be58b6f272c4240bc0c8f5dc4d39704d2e396c3';s=p.read_text()
for a,b in [('149a328436631f8d7f7f579629deb2a8367bd3d1e76296cbaaaed14385c6fc30','37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6'),('85872a4a2a3932d1c2ab05c28aaad4e8b14a59d2137c9ff8b24e1dc45b75ed87','cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7')]:s=once(s,a,b)
s=s.replace('single_original5_transport','single_original6_transport').replace('original5/native2','original6/native2')
s=once(s," raw=data('version-provider/CRT-IAT.bin');", " IDs=words(data('version-provider/file-IDs.bin'),28,'Q');need(IDs[:7]==IDs[7:14]and IDs[14:21]==IDs[21:]and IDs[4]==28976,'Whole actual loaded VERSION and CRT file identities equal their exact physical copies');\n raw=data('version-provider/CRT-IAT.bin');")
s=once(s,'return dict(setup=list(setup),whole_CRT_IAT_bindings=', 'return dict(setup=list(setup),whole_loaded_and_expected_provider_file_IDs=list(IDs),whole_CRT_IAT_bindings=')
s=once(s,"pin(R/'tools/m4-version-source/derive_compare_v3.py');pin(__file__)","pin(R/'tools/m4-version-source/derive_compare_v3.py');pin(R/'tools/m4-version-source/compare_v3.py','2b4f22cf66d0fe3e0f757de56be58b6f272c4240bc0c8f5dc4d39704d2e396c3');pin(R/'tools/m4-version-source/derive_compare_v4.py');pin(__file__)")
q=P/'compare_v4.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');print(json.dumps(dict(path=str(q),sha256=sha(q),archive_reader_opened=False)))
