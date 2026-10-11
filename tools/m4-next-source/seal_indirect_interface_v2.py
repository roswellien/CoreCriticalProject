"""Use the frozen disassembler's hexadecimal memory-offset spelling."""
from pathlib import Path
T=Path(__file__).resolve().parent
p=T/'seal_indirect_interface.py';q=T/'seal_indirect_interface_corrected.py';assert not q.exists()
s=p.read_text().replace("'eax, dword ptr [esp + 4]'","'eax, dword ptr [esp + 0x4]'")
q.write_text(s)
out=T.parents[1]/'reports/m4-next-source/indirect-interface-r1'
(out/'failure.txt').write_text('Static input spelling assertion used decimal displacement4; frozen exact LLVM text uses0x4. No physical-source mismatch; this unpassed attempt is superseded by fresh r2.\n')
