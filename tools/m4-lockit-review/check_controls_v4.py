"""Bound the import mutation's already-read first call and next genuine import refusal."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'check_controls_v3.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())";assert s.count(needle)==1;s=s.replace(needle,'compiled_source=source')
ctx={'__file__':__file__,'__name__':'control_review_deriver'};exec(compile(s,str(p),'exec'),ctx);source=ctx['compiled_source']
source=source.replace("and not tags[4],'Exactly one reached first-root targeted refusal with no initializer credit'","and tags[4]==int(case==5),'Exactly one reached targeted refusal with exact already-validated first-root prefix for delayed import mutation'")
source=source.replace("fault[1] in (api[4],api[2])","fault[1] in ((0x4dc193,) if case==5 else (api[4],api[2]))")
anchor="       need(struct.unpack_from('<I',a.data(live+f'current-page-{address&~4095}.bin'),address&4095)[0]==effect[3],'Actual retained whole page contains intervention')"
extra="\n       if case==5:need(len(calls)==2 and all(w[2]==0x411010 and w[11]==1 for w in calls) and calls[-1][13]==0 and source[-1]==(0x4dc193,0x5bb4f8,effect[3],4,0) and fault[2]==0x5bb4f8,'Already-read first source pair completes; next genuine changed-IAT source read causes refusal')"
assert source.count(anchor)==1;source=source.replace(anchor,anchor+extra)
exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())
