"""Compare the complete fixed Native17 AFTER block as source-derived output."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_connected_fixture_v4.py';wrapper=parent.read_text()
needle="exec(compile(wrapper,str(parent),'exec'),globals())"
addition="""marker=\"for page in pages:eq(m.bytes(page,4096),records.data(f'sequence-0/phase-13-after-page-{page}.bin'),'Every entire ordinary carried source page endpoint');counts['whole_ordinary_source_page_endpoints']+=1\"
replacement=\"\"\"for i,address in enumerate(PAGES):eq(m.bytes(address,4096),phase[71908+i*4096:71908+(i+1)*4096],'Every whole fixed source-derived Native17 page endpoint including lower stack');counts['whole_fixed_Native17_source_endpoints']+=1
    eq(len(set(PAGES)|set(pages)),46,'Complete current46 source page union')
    for page in pages:eq(m.bytes(page,4096),records.data(f'sequence-0/phase-13-after-page-{page}.bin'),'Every entire ordinary carried source page endpoint');counts['whole_ordinary_source_page_endpoints']+=1\"\"\"
wrapper=wrapper.replace(\"exec(compile(text,str(parent),'exec'),globals())\",\"assert text.count(\"+repr(marker)+\")==1;text=text.replace(\"+repr(marker)+\",\"+repr(replacement)+\");text=text.replace(\\\"pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v4.py');pin(sys.executable)\\\",\\\"pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v4.py');pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v5.py');pin(sys.executable)\\\");exec(compile(text,str(parent),'exec'),globals())\")
exec(compile(wrapper,str(parent),'exec'),globals())"""
assert wrapper.count(needle)==1;wrapper=wrapper.replace(needle,addition)
exec(compile(wrapper,str(parent),'exec'),globals())
