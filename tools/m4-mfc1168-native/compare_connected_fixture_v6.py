"""All46 fixed/external whole pages, correct current operandPC, BEFORE only.

Reuse the frozen v2 transformation, then apply the two input-adapter fixes and
the full fixed-page output comparison explicitly rather than nested wrappers.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;adapter=p/'compare_connected_fixture_v2.py'
script=adapter.read_text();tail="exec(compile(text,str(parent),'exec'),globals())"
assert script.endswith(tail+'\n')
scope={'__file__':str(adapter),'__name__':'source_adapter_only'}
exec(compile(script[:-len(tail+'\n')],str(adapter),'exec'),scope)
text=scope['text'];parent=scope['parent']
old='# Every ordinary carried page comes from this native invocation BEFORE.'
new='''# Fixed Native17 whole BEFORE pages include the true lower stack.
    eq(len(phase),159716,'Complete current Native fixed ABI')
    for i,address in enumerate(PAGES):
     value=phase[2276+i*4096:2276+(i+1)*4096];eq(len(value),4096,'Entire fixed BEFORE source page');memory[address]=bytearray(value);counts['whole_fixed_Native17_BEFORE_pages']+=1
    # Every ordinary carried page comes from this native invocation BEFORE.'''
assert text.count(old)==1;text=text.replace(old,new)
old="source_pc=self.cursor if pc is None else pc;value=super().read(address,size,domain,pc)"
new="source_pc=self.word(2472) if pc is None else pc;value=super().read(address,size,domain,pc)"
assert text.count(old)==1;text=text.replace(old,new)
old="for page in pages:eq(m.bytes(page,4096),records.data(f'sequence-0/phase-13-after-page-{page}.bin'),'Every entire ordinary carried source page endpoint');counts['whole_ordinary_source_page_endpoints']+=1"
new="""for i,address in enumerate(PAGES):eq(m.bytes(address,4096),phase[71908+i*4096:71908+(i+1)*4096],'Every entire fixed source-derived Native17 endpoint including lower stack');counts['whole_fixed_Native17_source_endpoints']+=1
    eq(len(set(PAGES)|set(pages)),46,'Complete current46 source page union')
    for page in pages:eq(m.bytes(page,4096),records.data(f'sequence-0/phase-13-after-page-{page}.bin'),'Every entire ordinary carried source page endpoint');counts['whole_ordinary_source_page_endpoints']+=1"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v2.py');pin(sys.executable)","pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v2.py');pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v6.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
