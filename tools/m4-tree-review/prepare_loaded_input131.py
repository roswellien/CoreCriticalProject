"""Fresh physical 131-page declaration; retain inherited 130 tool immutable."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-tree-review/prepare_loaded_input130.py';s=prior.read_text()
replacements=[('reports/m4-startup130-original/validation-r2/report.json','reports/m4-startup131-original/validation-r2/report.json'),('91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca','9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'),('reports/m4-joint-startup130/preparation-r2/report.json','reports/m4-joint-startup131/preparation-r1/report.json'),('060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')]
for a,b in replacements:
 assert s.count(a)==1,a;s=s.replace(a,b)
a="need(joint['native_preparation_sha256']==sha(np),'Current broad preparation binds corrected19')"
b="need(Path(joint['native_library']).resolve()==(np.parent/'registry_library.cpp').resolve() and joint['files'][str((np.parent/'registry_library.cpp').resolve())]==native['files'][str((np.parent/'registry_library.cpp').resolve())],'Current131 broad preparation binds exact corrected19 library')"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('pin(artifact);pin(__file__)','pin(artifact);pin(prior);pin(__file__)')
s=s.replace('current130','current131').replace('complete130','complete131')
exec(compile(s,str(prior),'exec'),globals())
