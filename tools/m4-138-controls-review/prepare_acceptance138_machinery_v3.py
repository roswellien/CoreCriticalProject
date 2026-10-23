"""Finite corrected root-list parsing; source-only additive preparation."""
from pathlib import Path
p=Path(__file__).with_name('prepare_acceptance138_machinery.py')
s=p.read_text().replace('acceptance138-machinery-preparation-r1','acceptance138-machinery-preparation-r3').replace('acceptance138_semantics.py','acceptance138_semantics_v3.py')
for before,after in [
 ("old_text.split('registration_roots = {',1)[1].split('};',1)[0].strip()","re.search(r'registration_roots *[{]([^}]+)[}]',old_text).group(1)"),
 ("new_text.split('registration_roots = {',1)[1].split('};',1)[0].strip()","re.search(r'registration_roots *[{]([^}]+)[}]',new_text).group(1)"),
 ('[0x40e420,0x40ef90,0x40f030,0x4795d0,0x5a3c60,0x5a4020,0x5a6720]','[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0]')]:
 assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'))
