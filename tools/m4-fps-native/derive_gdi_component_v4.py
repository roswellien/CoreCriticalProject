"""Suppress only Windows min/max macros before the direct SHA declaration."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 pp=R/'reports/m4-fps-native/connected-component-preparation-r3/report.json';assert sha(pp)=='da3ee4f6e3fc5aafefe4a73731679e659bc2e90455b1bd7c36cf6f243d9682d7';d=json.loads(pp.read_bytes());out=pp.parent.parent/name;assert not out.exists();out.mkdir();pins=dict(d['files']);pins[str(pp.resolve())]=sha(pp);rows=[]
 for p,h in pins.items():assert Path(p).suffix.lower()not in('.mwb','.zip')and sha(p)==h
 for p in pp.parent.iterdir():
  if p.is_file()and p.name!='report.json':q=out/p.name;shutil.copyfile(p,q);rows.append(dict(name=p.name,source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p)))
 p=out/'component.cpp';s=p.read_text();assert s.count('#include <Windows.h>')==1;s=s.replace('#include <Windows.h>','#define NOMINMAX\n#include <Windows.h>');p.write_text(s)
 for row in rows:row.update(current_sha256=sha(row['target']),byte_identical=sha(row['target'])==row['source_sha256']);assert row['byte_identical']or row['name']=='component.cpp'
 d['IRs']=[str((out/Path(p).name).resolve())for p in d['IRs']];d['namespace_relations']=[dict(x,component_IR=str((out/Path(x['component_IR']).name).resolve()),component_sha256=sha(out/Path(x['component_IR']).name))for x in d['namespace_relations']]
 for p in out.iterdir():
  if p.is_file():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable);d.update(parent_component_preparation=str(pp.resolve()),parent_component_preparation_sha256=sha(pp),prior_copy_relations=rows,changed_generated_files=[dict(name='component.cpp',relation='Only define NOMINMAX before Windows.h; SHA header and all literal/provider behavior unchanged',before_sha256=sha(pp.parent/'component.cpp'),after_sha256=sha(out/'component.cpp'))],files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
