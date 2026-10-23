"""ROOT exact current source7 post-source admission; ordinary dependencies only."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 P=R/'reports/m4-original141-source/inherited-review-preparation-r5';out=P.parent/'root-inherited-admission-r1';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if not p.is_relative_to(R):
   assert any(p.is_relative_to(q)for q in (Path(sys.prefix).resolve(),Path('C:/Program Files/Microsoft Visual Studio/18/Community'),Path('C:/Program Files (x86)/Windows Kits/10')))or p in {Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'),*(Path('C:/Windows/SysWOW64')/n for n in ('kernel32.dll','ntdll.dll','apphelp.dll','gdi32.dll','user32.dll'))}or(p.parent==Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original')and p.name in('index.json','payload.bin'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 q=read(P/'report.json','441843113f47e0ac2fdde7031481eec50b5b070c25cd8a94e3557820b0667587')
 assert q['prepared_only']and q['exact_whole_parent_inverse']and not q['reviewer_executed']and not q['source_execution']and not q['canonical_reader_opened']
 for p,h in q['files'].items():pin(p,h)
 declared=read(P/'ordinary-closure-declarations.json','5b100df8079a5081b41ae801b056202d8eaf1e2432e7996a45463b6a4b93f034')
 assert declared['original_source_sha256']==q['original_source_sha256']=='44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334'
 assert declared['configuration_sha256']==q['configuration_sha256']=='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0'
 assert len(declared['declarations'])==q['ordinary_declared_dependencies']==9625
 for p,h in declared['declarations'].items():pin(p,h)
 parent=pin(R/'tools/m4-original141-source/review_inherited141_v3.py','b7b3397cc561831f6ce72a35d5cfce65ed82ab24d3fa9316f68bdcb148b20872').read_text()
 candidate=pin(R/'tools/m4-original141-source/review_inherited141_v4.py','c359853e4ea0993f46a267aedab513832a492bde64cb1915f6967902234db4a1').read_text();lines=candidate.splitlines(keepends=True);deltas=read(P/'inverse.json','c02791b136d4668180b5679f51e2e6296f177b58689bf736163ce65f550d4f95');assert len(deltas)==2
 for d in deltas:assert ''.join(lines[d['child_start']:d['child_stop']])==d['child']
 for d in reversed(deltas):lines[d['child_start']:d['child_stop']]=d['parent'].splitlines(keepends=True)
 assert ''.join(lines)==parent;ast.parse(candidate)
 source=read(q['original_source_path'],q['original_source_sha256']);assert source['passed']and source['reader_closed']and source['ordinary_reader_closed']and not source['canonical_reader_opened']and not source['source_AFTER_seed']and source['configuration_sha256']==q['configuration_sha256']and source['counts']['phases']==846 and source['counts']['callbacks']==111
 assert {c['domain']for c in source['children']}=={'constructor18','formatter4','old4','new_MFC','widget','tree'}
 for child in source['children']:
  g=read(child['path'],child['sha256']);assert g['passed']and not g['canonical_reader_opened']and not g['source_AFTER_seed']
  for p,h in g['files'].items():pin(p,h)
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();report=out/'report.json';report.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='original141_post_source_inherited_review',configuration_sha256=q['configuration_sha256'],original_source_sha256=q['original_source_sha256'],whole_reviewer_inverse_hunks=2,ordinary_dependencies_physically_authenticated=len(files),reviewer_executed=False,source_execution=False,canonical_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 with report.open('rb')as f:print(json.dumps(dict(path=str(report),sha256=hashlib.file_digest(f,'sha256').hexdigest(),files=len(files))))
if __name__=='__main__':main()
