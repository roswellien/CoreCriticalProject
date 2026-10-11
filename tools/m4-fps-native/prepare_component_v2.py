"""Pin the entire actually opened static Python/JSON chain for FPS preparation."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];generator=R/'tools/m4-fps-native/prepare_component.py';s=generator.read_text()
a="R=Path(__file__).resolve().parents[2]"
b="""R=Path(__file__).resolve().parents[2]
READS=set();OPTIONAL=set()
def audit(event,args):
 if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 if not p.is_relative_to(R):return
 if isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3):
  if p.suffix.lower()in('.mwb','.zip'):raise ValueError('No capture/archive reader during preparation')
  (READS if p.is_file()else OPTIONAL).add(str(p))
sys.addaudithook(audit)"""
assert s.count(a)==1;s=s.replace(a,b)
a=" report=dict(passed=True,scope='Seven-route"
b=""" pin(R/'tools/m4-widget-native/build.py',prior['files'][str((R/'tools/m4-widget-native/build.py').resolve())]);pin(R/'tools/m4-fps-native/prepare_component.py')
 for q in list(READS):pin(q,actual['files'].get(q,prior['files'].get(q)))
 need(READS<=set(pins),'Every actual successful static read pinned')
 report=dict(all_successful_static_reads_pinned=True,actual_successful_static_reads=len(READS),optional_missing_reads=sorted(OPTIONAL),passed=True,scope='Seven-route"""
assert s.count(a)==1
exec(compile(s.replace(a,b),str(generator),'exec'),globals())
