"""Declare the genuine post-bootstrap sentinel shape for a model-only prefix."""
from pathlib import Path
T=Path(__file__).resolve().parent
p=T/'model_preflight.py';q=T/'model_preflight_corrected.py';assert not q.exists()
s=p.read_text().replace(" state=bytearray(3504)"," struct.pack_into('<I',memory[0x9a1000],0x7ec,0xffffffff)\n struct.pack_into('<I',memory[0x9a1000],0x7f0,0xffffffff)\n state=bytearray(3504)")
s=s.replace('model-preflight-r1','model-preflight-r2').replace("'tools/m4-next-source/model_preflight.py'","'tools/m4-next-source/model_preflight_corrected.py'")
q.write_text(s)
