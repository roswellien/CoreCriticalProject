"""Bind all derivative validator source files and actual source API frame identity."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;p=HERE/'check_controls_v5.py';s=p.read_text(encoding='utf-8')
old="assert s.count(needle)==1;s=s.replace(needle,'compiled_source=source')"
new="assert s.count(needle)>=1;s=s.rsplit(needle,1)[0]+'compiled_source=source\\n'"
assert s.count(old)==1;s=s.replace(old,new)
needle="exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())"
assert s.endswith(needle+'\n');s=s[:s.rfind(needle)]+'compiled_source=source\n'
ctx={'__file__':__file__,'__name__':'control_review_deriver'};exec(compile(s,str(p),'exec'),ctx);source=ctx['compiled_source']
anchor="  pin(__file__);H=module"
replacement="  pin(__file__)\n  for validator in Path(__file__).parent.glob('check_controls*.py'):pin(validator)\n  H=module"
assert source.count(anchor)==1;source=source.replace(anchor,replacement)
exec(compile(source,str(HERE/'check_controls.py'),'exec'),globals())
