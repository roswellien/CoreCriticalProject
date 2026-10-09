"""Literal entry supplementation; frozen first preparation remains unchanged."""
from pathlib import Path
import hashlib
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
base=ROOT/'tools/m4-crt-locale-batch/lift.py'
source=base.read_text()
first=source.index('    for label,info in recovery')
last=source.index('    initial=verify_manifest',first)
source=source[:first]+'''    append('string_type_entry_78002e55','string-type',0x78002e55,True)
    append('setmbcp_cold_entry_7800e4f1','setmbcp-cold',0x7800e4f1,True)
    unique_new_bytes=0
    compiled_bytes=sum(len(code) for _,_,_,code,_ in inputs)
    need(len(inputs)==2 and compiled_bytes==513,'Two literal backward-entry bodies, no new guard identity')
'''+source[last:]
source=source.replace("ROOT/'reports/m4-crt-locale-batch'/name","ROOT/'reports/m4-crt-locale-batch-recovery'/name")
source=source.replace("re.fullmatch('lifts-r[1-9][0-9]*',name)","name=='lifts-supplement-r1'")
source=source.replace("    for path in (llvm/'clang.exe'","    add(ROOT/'tools/m4-crt-locale-batch/lift.py','"+hashlib.sha256(base.read_bytes()).hexdigest()+"')\n    for path in (llvm/'clang.exe'")
exec(compile(source,str(base),'exec'),dict(__file__=__file__,__name__='__main__'))
