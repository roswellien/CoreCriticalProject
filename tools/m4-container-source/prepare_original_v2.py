"""Compile-only local-name correction; preserve the original prepared attempt."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];p=root/'tools/m4-container-source/prepare_original.py';q=p.with_name('prepare_original_corrected.py');assert not q.exists()
s=p.read_text();start=s.index('CONTAINER_CPP=r');end=s.index('def null_asm()',start);s=s[:start]+s[start:end].replace('const auto frame=nullfree_cpu.esp','const auto source_frame=nullfree_cpu.esp').replace('if(frame<','if(source_frame<').replace('||frame+16','||source_frame+16').replace('reinterpret_cast<unsigned*>(frame)','reinterpret_cast<unsigned*>(source_frame)').replace('e.frame=frame','e.frame=source_frame')+s[end:];q.write_text(s)
