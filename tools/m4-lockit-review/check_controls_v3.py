"""Reuse generic FS byte checks; assert this suite's exact four normal frames."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'check_controls_v2.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(p),'exec'),globals())";assert s.count(needle)==1;s=s.replace(needle,'compiled_source=s')
ctx={'__file__':__file__,'__name__':'control_review_deriver'};exec(compile(s,str(p),'exec'),ctx);source=ctx['compiled_source']
source=source.replace('H.chain_checks(a,live,source,not case,counts)','H.chain_checks(a,live,source,False,counts)')
needle="      need(len(calls)==len(imports)==8 and all(w[11]==1 for w in calls),'Eight genuine source CALL/RET records completed')"
extra="      frames=records(a,live+'fs-frame-witnesses.bin',32);need(len(frames)==4 and all(w[15]==w[19]==w[21]==1 for w in frames) and not a.data(live+'fs-active-records.bin') and a.words(live+'fs-current-tib.bin',5)[1]==0xffffffff,'Exactly four genuine complete installed/restored/returned sourceFS records')\n"
assert source.count(needle)==1;source=source.replace(needle,extra+needle)
exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())
