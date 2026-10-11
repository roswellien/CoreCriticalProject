"""Whole standalone ASM attribution uses its actual sole executable entry contract."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('review_mfc1168_resource_prelaunch.py')
SHA='ec43465a7913e4729d39fe7acb0ad6ef7a4c1ed5180a5151b26269b962d7331b'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
text=BASE.read_text()
before="asm.count('fnstenv')==asm.count('fldenv')==3"
assert text.count(before)==1
text=text.replace(before,"asm.count('fnstenv')==3 and asm.count('fldenv')==4")
before="symbols,sections=C.parse(pin(build/'hardware_boundary.obj').read_bytes());raw,relocs=C.function(symbols,sections,'mfc_hardware_call');matches=C.linked_candidates(image,raw,relocs)"
after="""symbols,sections=C.parse(pin(build/'hardware_boundary.obj').read_bytes())
        asm_entries=[x for x in symbols.values()if x['name']=='mfc_hardware_call']
        need(len(asm_entries)==1 and asm_entries[0]['section']>0 and asm_entries[0]['value']==0 and asm_entries[0]['type']==0 and asm_entries[0]['storage']==2,'Exact sole named standalone ASM entry')
        section=sections[asm_entries[0]['section']]
        need(section['flags']&0x20000000 and [x['name']for x in symbols.values()if x['section']==asm_entries[0]['section']and x['storage']==2]==['mfc_hardware_call'],'Complete standalone executable ASM section extent')
        raw,relocs=section['bytes'],section['relocations']
        expected=bytes.fromhex('534883ec204889d3480fae03d9b300020000d9a300020000e800000000480fae8320020000d9b320040000d9a320040000480fae0bd9a300020000480fae8340040000d9b340060000d9a3400600004883c4205bc3')
        need(raw==expected and len(raw)==85 and len(relocs)==1 and relocs[0]['offset']==25,'Independently derived full PUSH/shadow-space/FXSAVE/FNSTENV/FLDENV/CALL/restore/RET bytes')
        matches=C.linked_candidates(image,raw,relocs)"""
assert text.count(before)==1
text=text.replace(before,after)
before='    pin(__file__);pin(sys.executable);out.mkdir()'
assert text.count(before)==1
text=text.replace(before,"    pin(BASE,SHA);pin(Path(__file__).with_name('review_mfc1168_resource_prelaunch_v2.py'),'eeabd020f033a2c54ee3896d5939a330291ef78a27a160eb260645896201b565');pin(__file__);pin(sys.executable);out.mkdir()")
exec(compile(text,str(BASE),'exec'),globals())
