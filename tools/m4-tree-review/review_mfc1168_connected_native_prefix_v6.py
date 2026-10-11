"""Assembler entry uses the whole physical .text section and its defined label."""
from pathlib import Path
PARENT6=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v5.py')
program=PARENT6.read_text()
needle="program=program.replace('  pin(PREVIOUS);pin(BASE);'"
addition="program=program.replace(\"br,brels=C.function(bs,bsec,'mfc_connected_hardware_call')\",\"labels=[s for s in bs.values()if s['name']=='mfc_connected_hardware_call'];assert len(labels)==1 and labels[0]['section']==1 and labels[0]['value']==0 and bsec[1]['flags']&0x20000000;br,brels=bsec[1]['bytes'],bsec[1]['relocations']\")\n"
assert needle in program
program=program.replace(needle,addition+needle)
program=program.replace('  pin(PARENT);pin(PREVIOUS);pin(BASE);','  pin(PARENT6);pin(PARENT);pin(PREVIOUS);pin(BASE);')
exec(compile(program,str(PARENT6),'exec'),globals())
