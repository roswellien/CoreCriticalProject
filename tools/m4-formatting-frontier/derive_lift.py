"""Literal formatting game/strrchr lifts from the reviewed tree lift recipe."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-tree-source/lift.py';s=p.read_text();changes=[]
def one(a,b):
    global s
    assert s.count(a)==1,a;s=s.replace(a,b);changes.append(dict(before=a,after=b))
one("REC=ROOT/'reports/m4-tree-source/recovery-r1'", "REC=ROOT/'reports/m4-formatting-frontier/recovery-r1'")
one("REC_SHA='81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4'", "REC_SHA='8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15'")
one("out=ROOT/'reports/m4-tree-source'/name", "out=ROOT/'reports/m4-formatting-frontier'/name")
one("pin(REC/'report.json',REC_SHA);graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());roots=json.loads(pin(REC/'FS-frame-contracts.json').read_bytes());inputs={}", """pin(REC/'report.json',REC_SHA);graphs=json.loads(pin(REC/'game-new-graphs.json').read_bytes());strrchr=json.loads(pin(REC/'strrchr-graph.json').read_bytes());graphs[str(strrchr['entry'])]=strrchr;need(len(graphs)==11,'Ten game plus one closed strrchr source graph');roots=json.loads(pin(REC/'roots.json').read_bytes());inputs={} """)
one("# All accepted124 bodies remain unchanged; lift eight physical tree entries.", "# Prepare ten exact formatting game bodies and one complete strrchr body.")
one("pe=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())", "pe=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())")
one("entry=g['entry'];component=f'f_{entry:x}';commands=[]", "entry=g['entry'];component=f'f_{entry:x}';commands=[];source_pe=crt if entry>=0x78000000 else pe")
one("off,_=pe.rva_range(a-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw", "off,_=source_pe.rva_range(a-source_pe.image_base,len(raw));need(source_pe.data[off:off+len(raw)]==raw")
one("new_guest_objects=2*len(bodies)", "new_guest_objects=2*len(bodies)") if False else None
one("root_count=1", "root_count=3")
one("ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/analysis/pe.py'", "ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/analysis/pe.py',ROOT/'tools/m4-tree-source/lift.py',ROOT/'tools/m4-formatting-frontier/derive_lift.py'")
one("Exact game source/COFF preparation only, no initializer execution credit", "Exact formatting game and strrchr source/COFF preparation only; sprintf and runtime remain open")
out=Path(__file__).with_name('lift.py');assert not out.exists();out.write_text(s);print(json.dumps(dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(),changes=len(changes))))
