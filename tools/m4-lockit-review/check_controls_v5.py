"""Use the actual source State/API frame, separate from intentionally carried RuntimeCPU."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'check_controls_v4.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())";assert s.count(needle)==1;s=s.replace(needle,'compiled_source=source')
ctx={'__file__':__file__,'__name__':'control_review_deriver'};exec(compile(s,str(p),'exec'),ctx);source=ctx['compiled_source']
needle="struct.unpack_from('<I',a.data(trigger+'CPU.bin'),16)[0]+4";assert source.count(needle)==1;source=source.replace(needle,'api[5]+4')
exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())
