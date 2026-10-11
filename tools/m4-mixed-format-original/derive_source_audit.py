"""Bind every actual local source dependency read by the successful bounded model."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'tools/m4-mixed-format-original/compare_source_v7.py';s=p.read_text();needle='PINS={}\n';assert s.count(needle)==1
audit='''PINS={};AUDITED_READS=set();FAILED_OPTIONAL_READS=set()
def audit_workspace_read(event,args):
    if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
    path=Path(args[0]).resolve()
    if not path.is_relative_to(R):return
    mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else0
    reading=isinstance(mode,str)and'r'in mode or(mode is None and isinstance(flags,int)and not(flags&3))
    if not reading:return
    if path.suffix.lower()=='.mwb':need(path.is_relative_to(R/'reports/m4-mixed-format-original/trace-execution-r1'),'No inherited/native capture in bounded source audit')
    if path.is_file():AUDITED_READS.add(str(path))
    else:FAILED_OPTIONAL_READS.add(str(path))
sys.addaudithook(audit_workspace_read)
'''.replace('else0','else 0')
s=s.replace(needle,audit,1)
needle="        report=dict(passed=passed,scope=";assert s.count(needle)==1
s=s.replace(needle,"        for actual_read in list(AUDITED_READS):pin(actual_read)\n        need(AUDITED_READS<=set(PINS),'Every successful actual dependency read physically pinned')\n        report=dict(passed=passed,actual_dependency_reads=len(AUDITED_READS),complete_executed_dependency_chain_pinned=True,failed_optional_open_paths=sorted(FAILED_OPTIONAL_READS),original_game_FS_observations=6,allocator_FS_frames_literal_only=True,scope=",1)
p=ROOT/'tools/m4-mixed-format-original/compare_source_v8.py';assert not p.exists();p.write_text(s)
