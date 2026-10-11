"""Use the source instruction state PC for owning-IAT operand provenance.

The interpreter cursor advances to fall-through before evaluating operands;
the retained State RIP still identifies the currently executing instruction.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_connected_fixture_v3.py';wrapper=parent.read_text()
needle="exec(compile(wrapper,str(parent),'exec'),globals())"
addition="""marker=\"source_pc=self.cursor if pc is None else pc;value=super().read(address,size,domain,pc)\"
replacement=\"source_pc=self.word(2472) if pc is None else pc;value=super().read(address,size,domain,pc)\"
wrapper=wrapper.replace(\"exec(compile(text,str(parent),'exec'),globals())\",\"assert text.count(\"+repr(marker)+\")==1;text=text.replace(\"+repr(marker)+\",\"+repr(replacement)+\");text=text.replace(\\\"pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v3.py');pin(sys.executable)\\\",\\\"pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v3.py');pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v4.py');pin(sys.executable)\\\");exec(compile(text,str(parent),'exec'),globals())\")
exec(compile(wrapper,str(parent),'exec'),globals())"""
assert wrapper.count(needle)==1;wrapper=wrapper.replace(needle,addition)
exec(compile(wrapper,str(parent),'exec'),globals())
