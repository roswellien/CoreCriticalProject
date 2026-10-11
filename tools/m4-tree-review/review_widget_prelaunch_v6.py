"""Compare assembly grammar with explicit CRLF normalization only."""
from pathlib import Path
import hashlib
V5=Path(__file__).with_name('review_widget_prelaunch_v5.py')
V5_SHA='be3458ecd0ba96c871927c365b4d2c186d4b0ea3f32a3ed5a760a6024a49b5f4'
if hashlib.sha256(V5.read_bytes()).hexdigest()!=V5_SHA:raise ValueError('Immutable physical page reviewer')
program=V5.read_text()
anchor="exec(compile(source,str(BASE),'exec'),globals())"
if program.count(anchor)!=1:raise ValueError('One independent checker invocation')
transform=r'''
old="asm = raw(directory / 'reference_x86.asm').decode()"
new="asm = raw(directory / 'reference_x86.asm').decode().replace('\\r\\n','\\n')"
if source.count(old)!=1:raise ValueError('One source grammar line-ending normalization')
source=source.replace(old,new,1)
anchor_pin='        pin(__file__); pin(sys.executable)'
if source.count(anchor_pin)!=1:raise ValueError('One current independent code pin')
source=source.replace(anchor_pin,'        pin(V5,V5_SHA);\n'+anchor_pin,1)
exec(compile(source,str(BASE),'exec'),globals())
'''
program=program.replace(anchor,transform,1)
exec(compile(program,str(V5),'exec'),globals())
