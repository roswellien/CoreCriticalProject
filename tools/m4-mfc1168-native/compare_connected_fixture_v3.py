"""Add the fixed Native17 whole BEFORE pages, including its lower stack.

The prior comparer supplied the46 external ordinary page inventory but omitted
the separate fixed lower-stack input. No observed AFTER byte enters this model.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_connected_fixture_v2.py';wrapper=parent.read_text()
needle="exec(compile(text,str(parent),'exec'),globals())"
addition="""old='# Every ordinary carried page comes from this native invocation BEFORE.'
new='''# The fixed Native17 page block is an independently retained BEFORE input.
    eq(len(phase),159716,'Complete current Native fixed ABI')
    for i,address in enumerate(PAGES):
     value=phase[2276+i*4096:2276+(i+1)*4096];eq(len(value),4096,'Entire fixed BEFORE source page');memory[address]=bytearray(value);counts['whole_fixed_Native17_BEFORE_pages']+=1
    # Every ordinary carried page comes from this native invocation BEFORE.'''
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v2.py');pin(sys.executable)","pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v2.py');pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v3.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())"""
assert wrapper.count(needle)==1;wrapper=wrapper.replace(needle,addition)
exec(compile(wrapper,str(parent),'exec'),globals())
