"""Same literal interpreter, now consume actual complete prep5 memory inputs.

Only genuine/current invocation BEFORE is supplied to the model. Actual extra
AFTER endpoints and raw hardware sides remain strict comparison targets.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_connected_fixture.py';text=parent.read_text()
old="initial_memory={a:bytes(v)for a,v in memory.items()};m=Literal"
new="""index=records.data(stem+'before/memory/index.bin');regions=list(struct.iter_unpack('<3I',index));eq(len(regions),12,'All eight new loader inputs plus CRT and three minimalFS regions');eq(regions[:5],[(o['new'],o['extent'],3)for o in inputs['role_owners']],'Whole five current carried typed owner extents');eq(regions[5:],[(0x5f4cb000,4096,3),(cs,24,3),(0x7ffdee1c,4,3),(0x78037000,4096,3),(0x7ffde000,4,3),(0x7ffde004,8,1),(0x7ffde018,4,1)],'Exact manager/CS/TLS/CRT/minimalFS endpoint inventory')
    for address,size,permission in regions:
     value=records.data(stem+f'before/memory/{address}.bin');eq(len(value),size,'Complete actual current source BEFORE extent')
     if address==0x78037000:
      for cell in inputs['CRT_cells']:eq(words(value,o=cell['address']-address)[0],cell['projected'],'Actual carried cached1252/lock25/transient input cells')
      # All other CRT bytes are carried from this root invocation BEFORE.
      # Their earlier bootstrap effects require the separate persistent gate.
     elif address==0x7ffde004:eq(value,struct.pack('<2I',0x20002000,0x20001000),'Existing exact Runtime stack bounds retained')
     elif address==0x7ffde018:eq(value,struct.pack('<I',0x7ffde000),'Existing exact Runtime minimal TIB self retained')
     else:eq(value,bytes(memory[address]),'Whole genuine typed-loader/declared minimalFS current BEFORE')
     memory[address]=bytearray(value);counts['whole_declared_current_BEFORE_regions']+=1
    initial_memory={a:bytes(v)for a,v in memory.items()};m=Literal"""
assert text.count(old)==1;text=text.replace(old,new)
old="eq(m.bytes(0x78037000,4096),initial_memory[0x78037000],'Literal full modeled CRT25 page returns to declared input; actual full endpoint separately pending')"
new="""eq(m.bytes(0x78037000,4096),initial_memory[0x78037000],'Literal whole current CRT25 page returns to its carried BEFORE')
    eq(records.data(stem+'after/memory/index.bin'),index,'Same entire declared memory endpoint inventory')
    for address,size,permission in regions:eq(m.bytes(address,size),records.data(stem+f'after/memory/{address}.bin'),'Every complete literal extra manager/CRT/minimalFS/role endpoint');counts['whole_extra_memory_endpoints']+=1
    hardware=records.data('sequence-0/MFC-caller-hardware.bin');eq(len(hardware),1632,'Three complete actual assembly hardwareFX512/ENV28 sides');eq(hardware[:512],hardware[1088:1600],'Entire actual caller hardwareFX512 restored by current connected boundary');eq(hardware[512:540],hardware[1600:1628],'Entire actual caller hardwareENV28 restored by current connected boundary');counts['whole_actual_caller_hardwareFX512_ENV28']+=1"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("unobserved_extra_whole_endpoints=['MFC manager5F4CB000','CRT78037000','guest FS fields']", "unobserved_extra_whole_endpoints=[],whole_extra_regions=regions,whole_caller_hardware_restored=True,caller_boundary='Current14 selected Context invocation includes MFC owned resources; old registry construction/cleanup outside'")
text=text.replace('extra manager/CRT/TIB whole endpoints pending','complete manager/CRT/minimalFS extra endpoints and actual full assembly hardware caller restoration')
text=text.replace("pin(__file__);pin(sys.executable)", "pin(__file__);pin(R/'tools/m4-mfc1168-native/compare_connected_fixture.py');pin(R/'tools/m4-mfc1168-native/compare_connected_fixture_v2.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
