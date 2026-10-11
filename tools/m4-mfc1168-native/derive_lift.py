"""Derive additive thirteen-body finite normal Remill/COFF preparation."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-tree-source/lift.py';s=p.read_text()
s=s.replace("ROOT/'reports/m4-tree-source/recovery-r1'","ROOT/'reports/m4-mfc1168-probe/native-contracts-r1'").replace("REC_SHA='81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4'","REC_SHA='ec43e53280a0b15d6f29da7ac51e9f04d20d6b25514275cfb618448348eadade'")
s=s.replace('mw34_onexit_game_','mw34_mfc1168_').replace("ROOT/'reports/m4-tree-source'/name","ROOT/'reports/m4-mfc1168-native'/name").replace("pin(REC/'game-new-graphs.json')","pin(REC/'game-normal-graphs.json')").replace("pin(REC/'FS-frame-contracts.json')","pin(REC/'contracts.json')")
a="  # All accepted124 bodies remain unchanged; lift eight physical tree entries."
assert s.count(a)==1;s=s.replace(a,"  crt=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());mfc=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73df73bdf05b518120632099e2fc8'.replace('3df73bdf','3d73bdf')).read_bytes())\n  # Thirteen normal-only entry graphs; other branch targets retain missing-block denial.")
# Use the exact pinned MFC digest rather than a constructed literal.
s=s.replace("'5f66a4d221e24c767aadd3f43a981df53d42f3d73df73bdf05b518120632099e2fc8'.replace('3df73bdf','3d73bdf')","'5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'")
a="   entry=g['entry'];component=f'f_{entry:x}';commands=[]"
assert s.count(a)==1;s=s.replace(a,a+";source_pe=crt if entry>=0x78000000 else mfc if entry>=0x5f400000 else pe")
a="off,_=pe.rva_range(a-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw"
assert s.count(a)==1;s=s.replace(a,"off,_=source_pe.rva_range(a-source_pe.image_base,len(raw));need(source_pe.data[off:off+len(raw)]==raw")
s=s.replace("scope='Exact game source/COFF preparation only, no initializer execution credit'","scope='Thirteen finite normal cached MFC1168 source/COFF bodies; unobserved branches denied, no initializer execution credit'")
a="  for p in (Path(__file__),Path(sys.executable),ROOT/'tools/lifting/host_adapter.py'"
assert s.count(a)==1;s=s.replace(a,"  for p in (Path(__file__),Path(sys.executable),ROOT/'tools/m4-mfc1168-native/derive_lift.py',ROOT/'tools/m4-tree-source/lift.py',ROOT/'tools/lifting/host_adapter.py'")
out=R/'tools/m4-mfc1168-native/lift.py';assert not out.exists();out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
