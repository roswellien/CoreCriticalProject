"""Admit the exact two protected-IAT mutation repairs with unchanged refusals."""
from pathlib import Path
import runpy

previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v7.py')
scope=runpy.run_path(str(previous),run_name='generate_review_only')
text=scope['text'];globals().update({key:scope[key]for key in('BASE','V2','V3','V4')})
for before,after in(
    ('3f58e9ef746d10f77ccb34c7081dcc16aa007247d6c86fc3da6634b71036cd3c','7e7ea6be02ed299ff6fc3171e9fa119da6fd7e8aa866d7626c912bf8aefaac1d'),
    ('ecfadc502d353d00afee039ff292733ee9c43601bb629969cd752c9a62debf48','0a45415c36b76ae10669f9ecbb8289fac4878b9e564f33212128a5c22ac12136'),
    ('connected-controls-build-r4/build.json','connected-controls-build-r5/build.json'),
    ('connected_controls_v4.inc','connected_controls_v5.inc'),
    ('3EF3D8F5','96291D99'),('832FC712','96291D99'),
):
    assert before in text,before;text=text.replace(before,after)
anchor='  assert controls==previous_controls.replace(old_line,replacement)'
assert text.count(anchor)==1
checks=r'''
  expected_diagnostic=previous_controls.replace(old_line,replacement)
  assert pin(R/'tools/m4-mfc1168-native/connected_controls_v4.inc').read_text()==expected_diagnostic
  repairs={
   ' case 3:scalar(0x5f498330,0);break;':' case 3:r.memory().protect({0x5f498000},mw34::Permissions::read|mw34::Permissions::write);scalar(0x5f498330,0);r.memory().protect({0x5f498000},mw34::Permissions::read);break;',
   ' case 9:scalar(0x7802e0c8,0);break;':' case 9:r.memory().protect({0x7802e000},mw34::Permissions::read|mw34::Permissions::write);scalar(0x7802e0c8,0);r.memory().protect({0x7802e000},mw34::Permissions::read);break;',
  }
  for before,after in repairs.items():
   assert expected_diagnostic.count(before)==1
   expected_diagnostic=expected_diagnostic.replace(before,after)
  assert controls==expected_diagnostic
  counts['whole_intended_protected_IAT_mutation_repairs']=2
'''
text=text.replace(anchor,checks)
anchor="pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v7.py');"
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v8.py');")
exec(compile(text,str(__file__),'exec'),globals())
