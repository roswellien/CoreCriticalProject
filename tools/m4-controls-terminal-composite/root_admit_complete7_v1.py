"""ROOT complete7 bounded physical admission; terminal header projection only."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 P=R/'reports/m4-controls-terminal-composite/complete7-preparation-r1';out=P.parent/'root-complete7-admission-r1';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.mwc')and p.name!='transport.json'
  assert p.is_relative_to(R)or p.is_relative_to(Path(sys.prefix).resolve())or p.is_relative_to(Path('C:/Program Files/Microsoft Visual Studio/18/Community'))or p.is_relative_to(Path('C:/Program Files (x86)/Windows Kits/10'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 required=read(P/'adapter-required-inputs.json','fb89e07227617c267ff08ecb418aceafdec82a01214e5268cc6bd18f7d22e741');assert required['prepared']and not required['adapter_executed']and not required['underlying_physical_files_rehashed_now']and len(required['files'])==required['declared_input_count']==1445
 for p,h in required['files'].items():pin(p,h)
 script=pin(R/'tools/m4-controls-terminal-composite/legacy_complete7_v1.py','9b5633af66a477445eb25373d63f4fa93fafe59731441f684aa9a05148e6bb2a');ast.parse(script.read_text())
 controls=read(P.parent/'root-complete7-controls-r1/report.json');assert controls['pure_controls_completed']and controls['control_count']==18 and len(set(controls['controls']))==18 and not controls['adapter_main_executed']and not controls['composer_main_executed']and controls['accepted_function_credit']==0
 for p,h in controls['files'].items():pin(p,h)
 pin(R/'tools/m4-controls-terminal-composite/complete7_controls_v1.py','f04025b5720c7c539fd2ed54c604e3ca743bccded51ef92f007e546025177c16')
 terminalpath=pin(R/'reports/m4-138-preresource-strict-review/root-aggregate-r1/report.json','d3f4c2352cbf957088d885f2a8f5d21268cf86efc002556994b6a71c4d42e8c9')
 # Parse only the actual small header preceding the physical edge map. The
 # entire report SHA is freshly authenticated above; no giant JSON load.
 header=[]
 with terminalpath.open('r',encoding='utf-8')as f:
  for _ in range(60):
   line=f.readline()
   if line.strip()=='"files": {':break
   header.append(line)
  else:raise AssertionError('Exact actual terminal header boundary')
 text=''.join(header).rstrip();assert text.endswith(',');terminal=json.loads(text[:-1]+'\n}')
 assert terminal['passed']and terminal['case_count']==24 and not terminal['worker_executed']and not terminal['capture_reader_opened']and terminal['accepted_function_credit']==0
 counts=terminal['counts'];assert counts['actual_precise_denials']==counts['actual_unchanged_poisoned_retries']==counts['entryframe64_checked']==24
 manifest=read(R/'reports/m4-138-preresource-strict-review/root-aggregate-admission-r1/aggregate-manifest.json','6e7bf035598fad79a4b6b67eb030ffc9825158c85856255975d5dd47a083da16');assert len(manifest['strict_cases'])==24 and {(c['level'],c['mode'])for c in manifest['strict_cases']}=={(l,m)for l in('O0','O2')for m in range(1,13)}
 projection=dict(report_path=str(terminalpath),report_sha256=files[str(terminalpath)],passed=True,case_count=24,strict_case_manifest_sha256='6e7bf035598fad79a4b6b67eb030ffc9825158c85856255975d5dd47a083da16',whole_physical_report_rehashed_by_ROOT=True,counts=counts,terminal_case_edge_membership_revalidation_by_composer_required=True)
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();report=out/'report.json';report.write_text(json.dumps(dict(passed=True,independent_review=True,legacy_complete7_adapter_admitted=True,actual_legacy24_terminal=projection,complete7_adapter_executed=False,composite_admitted=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 with report.open('rb')as f:print(json.dumps(dict(path=str(report),sha256=hashlib.file_digest(f,'sha256').hexdigest(),files=len(files))))
if __name__=='__main__':main()
