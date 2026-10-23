"""ROOT compile-only admission of reviewed literal bridge; no link or load."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-loader-message-review/root-literal-compile-admission-r2';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 base=R/'reports/m4-loader-message-review/persistent-code-preparation-r2';prep_sha='3f132e4b76ec369a7b1a88157882d6d1025de81003a7c3c62d43c1035df6a5f0';prep=read(base/'report.json',prep_sha)
 assert prep['passed']and prep['source_delta_hunks']==4 and not prep['complete_DLL_link_admitted']
 for p,h in prep['files'].items():pin(p,h)
 text=pin(base/'native_provider_literal_v1.cpp').read_text();deltas=read(base/'exact-native-source-inverse.json');assert len(deltas)==4
 for d in reversed(deltas):assert text.count(d['after'])==1;text=text.replace(d['after'],d['before'])
 assert text==pin(R/'tools/m4-loader-message-review/native_provider.cpp').read_text()
 recipe=read(base/'ROOT-compile-and-admission-recipe.json','140001697ccf04aed0b8a043de6155ab514ff9ef47954367a19e95d2804e86f4')
 for level in ('O0','O2'):
  commands=recipe['compile_commands'][level];assert len(commands)==2
  for c in commands:assert c[0]==recipe['compiler']and '/c'in c and '/LD'not in c and '/link'not in c;pin(c[-1])
 pin(recipe['compiler']);table=R/'reports/m4-loader-message-review/native-preparation-r1/source_table.hpp';parent=read(table.parent/'report.json','de099653af14f330b58d4e4a9753b9e4ab4712f4c18fbd147a7393a396406f16');pin(table,parent['files'][str(table)])
 for p in ('root_compile_literal_v1.py','root_compile_literal_v1.ps1','root_compile_literal_v2.py','root_compile_literal_v2.ps1'):pin(R/'tools/m4-loader-message-review'/p)
 vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
 for p in ('Common7/Tools/Microsoft.VisualStudio.DevShell.dll','Common7/Tools/VsDevCmd.bat'):pin(vs/p)
 a=pin(R/'tools/m4-loader-message-review/root_compile_literal_v1.py').read_text();b=pin(R/'tools/m4-loader-message-review/root_compile_literal_v2.py').read_text()
 old="headers=data['Includes'];assert headers and len({str(Path(p).resolve()).casefold()for p in headers})==len(headers)";new="headers=data['Includes'];assert headers and all(type(p)is str and Path(p).is_absolute()for p in headers);assert not data['ImportedModules']and not data['ImportedHeaderUnits']"
 assert b.count(new)==1 and b.replace(new,old)==a
 for p in (R/'reports/m4-loader-message-review/literal-code-build-r1/report.json',R/'reports/m4-loader-message-review/literal-code-build-r1/O0/native_provider_literal_v1.dependencies.json'):pin(p)
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='message_literal_compile_only',preparation_sha256=prep_sha,whole_native_inverse_hunks=4,exact_compile_commands=4,compiler_executed=False,linker_invoked=False,DLL_loaded=False,source_evaluator_invoked=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))
if __name__=='__main__':main()
