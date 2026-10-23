"""Additive graph binding and literal current ASM/root identities, no relaxed predicates."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('check_schema138_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f549f36a03a2a6c5123b2f29dc86f76eec14f2c445f1307972afbadc0d895ea8'
s=p.read_text()
changes=[
 ("('native-inputs.py','native-TLS.py','native-boundary.py','native-linked.py')","('native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py')"),
 ("env.update(level=level,w=w,bf=bf,image=image)","graph=pin(bf/'build.ninja').read_text()\n   env.update(level=level,w=w,bf=bf,image=image,graph=graph)\n   exec(compile(blocks['native-graph.py'],str(prepdir/'native-graph.py'),'exec'),env)"),
 ("('mov ecx,800h','rep movsd','mov esi,fs:[18h]')","('mov ecx,2048','rep movsd','mov esi,DWORD PTR fs:[18h]')"),
 ("{0x4103f0,0x410620,0x4b67f0}","{0x4103f0,0x410440,0x459b40}"),
 ("pin(__file__);pin(sys.executable)","pin(Path(__file__).with_name('check_schema138_v1.py'),'f549f36a03a2a6c5123b2f29dc86f76eec14f2c445f1307972afbadc0d895ea8');pin(__file__);pin(sys.executable)")]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
