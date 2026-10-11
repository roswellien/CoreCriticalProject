"""Attribute only typed bridges actually referenced by the thirteen literal bodies."""
from pathlib import Path
BASE9=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v8.py')
program=BASE9.read_text()
anchor="exec(compile(program,str(BASE8),'exec'),globals())"
assert program.count(anchor)==1
addition=r"""
unused=('mw34_mfc1168_read8','mw34_mfc1168_read16','mw34_mfc1168_read64','mw34_mfc1168_write16','mw34_mfc1168_write64')
insertion="\n".join("generator=generator.replace("+repr(repr(n)+',')+",'')"for n in unused)+"\n"
program=program.replace("helper=r'''",insertion+"helper=r'''")
program=program.replace('  pin(BASE8);pin(PREVIOUS);pin(BASE);','  pin(BASE9);pin(BASE8);pin(PREVIOUS);pin(BASE);')
"""
program=program.replace(anchor,addition+anchor)
exec(compile(program,str(BASE9),'exec'),globals())
