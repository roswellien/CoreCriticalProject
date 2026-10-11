"""Freeze original5/system-provider comparison without opening captures."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 for rel,h in [('comparison-execution-preparation-r1/report.json','deb3caa52d1fe57405425e5577a309b5f17b3daf5de9de2c5288b5f26b2c9433'),('original-controller-preparation-r2/report.json','b5262ea347b202137ac0b0192fa98a507da67876a3e70e800425e1ecab81b652')]:
  d=json.loads(pin(R/'reports/m4-version-source'/rel,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
 tool=pin(R/'tools/m4-version-source/compare_v3.py');compile(tool.read_text(),str(tool),'exec');pin(__file__);pin(R/'tools/m4-version-source/derive_compare_v3.py');out.mkdir(parents=True)
 d=dict(passed=True,scope='One independently admitted original5 strict payload reader, actual isolated system provider proof, manifest-bound direct ordinary native2 witnesses; preparation only',comparison_tool=str(tool),comparison_tool_sha256=sha(tool),reader_admission_keys=['passed','original_execution_sha256','native_execution_sha256','comparison_tool_sha256','sole_original_reader_lease','original_input_role','native_input_role'],required_original_role='single_original5_transport',required_native_role='direct_ordinary_closed_native2',original_payload_maximum_bytes=256*1024*1024,original_logical_files_maximum=2048,original_parts_maximum=8,original_reader_count=1,original_reader_closed_in_finally=True,native_archive_readers=0,current_frozen_workers_changed=False,archive_reader_opened=False,source_original_equivalence=False,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),tool_sha256=sha(tool),passed=True,archive_reader_opened=False)))
if __name__=='__main__':main(sys.argv[1])
