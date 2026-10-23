"""Root admits exact source6 review derivatives; source evaluation is separate."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/source6-root-review-preflight-r1';assert not out.exists();out.mkdir();pins={}
 p=R/'reports/m4-138-controls-review/source6-review-preparation-r1/report.json';assert sha(p)=='872e86b438d53b6b641a14191f1bedb1404e3339bcd80ef8d04494f871abf0d7';d=json.loads(p.read_bytes());assert d['passed']
 for path,h in d['files'].items():assert Path(path).suffix.lower()not in{'.mwb','.zip'}and sha(path)==h;pins[path]=h
 inverse=[]
 for row in d['derivatives']:
  current=Path(row['derivative']).read_text();old=Path(row['parent']).read_text()
  restored=current
  for delta in reversed(row['changes']):assert restored.count(delta['after'])==1;restored=restored.replace(delta['after'],delta['before'],1)
  assert restored==old;compile(current,row['derivative'],'exec');inverse.append(dict(path=row['derivative'],changes=len(row['changes']),whole_inverse_restored_parent=True))
 # Every new extent must be tied to measured source6, while all inherited guards survive inversion.
 source=Path(d['source_provider_path']);assert sha(source)==d['source_provider_sha256'];s=json.loads(source.read_bytes());assert s['passed']and s['reader_closed']and s['counts']['persistent_phases']==1656 and s['counts']['whole_page_BEFORE']==s['counts']['whole_page_AFTER']==114264
 assert s['counts']['literal_widget_roots']==84 and s['counts']['actual_GDI_source_calls']==1788 and s['counts']['actual_manual_owned_font_frees']==180
 assert all(s[k]is False for k in['per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','native_CS40_opaque_copy','native_DllMain_credit'])
 pins[str(source.resolve())]=sha(source);pins[str(p.resolve())]=sha(p);pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Root exact inverse/source extent admission for current source6 independent provider/closure/MFC reviewer derivatives; executed review gates remain separate',derivatives=inverse,source_provider_sha256=sha(source),inherited_predicates_unchanged_except_exact_current_lineage_and_coverage=True,independent_widget_review_separate=True,archive_reader_opened=False,source_machine_executed=False,worker_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
