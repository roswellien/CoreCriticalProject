"""ROOT current53-edit formatter partition policy admission."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('root_seal_current_policy_v9.py')
with p.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='48e34ce31ff288eb57614ffb2a6e693abfcc7f53c8132a23b8266e929edfaea5'
s=p.read_text()
changes=[('root-policy-admission-r6','root-policy-admission-r7'),('comparer-preparation-r11','comparer-preparation-r13'),('69888fc3aecb975215744406b7147da737f1593a6be19678dba606257351f6eb','84f047b2d83c54ef678e60ba645cd9cf46d3f95737baaa3c70f4d7a7948e3d9c'),('preflight_comparer_v11.py','preflight_comparer_v13.py'),('root-definition-preflight-r6','root-definition-preflight-r7'),('all51_hunks_exactly_invert','all53_hunks_exactly_invert')]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
anchor="assert s.count(a)==1;s=s.replace(a,b)"
addition="\na=\" assert caller['complete_selected138_original_provider_input_footprint_reviewed'] is True\"\nb=a+\"\\n formatter=read(R/'reports/m4-startup138-paired/format-module-root-review-r1/report.json','39a98c818eed260d830f1cc646553b66407c9477b0554e5d41d4a2ad959f8f00');assert formatter['independent_review']and formatter['separate_CRT_publications']==72 and formatter['refused_adverses']==504\"\nassert s.count(a)==1;s=s.replace(a,b)\n"
assert s.count(anchor)==2
position=s.index(anchor)+len(anchor);s=s[:position]+addition+s[position:]
a="pin(Path(__file__).with_name('root_seal_current_policy_v7.py'));"
b="pin(Path(__file__).with_name('root_seal_current_policy_v9.py'));"+a
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))
