"""Metadata-only sole reader lease after exact common pair workers terminate."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];RECIPE='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(original_path,original_hash,native_path,native_hash,name,root_slot):
 assert root_slot=='root-reader-slot-available','Root must serialize sole original reader after every prior canonical reader closes';P={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v;P[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 op=read(R/'reports/m4-tree-review/version-original-common-prelaunch-r2/report.json','caa8b189a0da510dee164f3b54b51decd0d0662a110e77d5204f09adf1bf5f5d');np=read(R/'reports/m4-tree-review/version-native-common-prelaunch-r1/report.json','c1d894005c1a3e6f3273d12e34e3716a0dcffc0b2176a014e25013c95b6f6938');dp=read(R/'reports/m4-version-source/common-pair-data-admission-r1/report.json','7bfe8c5fa1c0d2a186fd22977935dc5c4ac92b5d6994bba99b459037175a57db');assert op['passed']and np['passed']and dp['passed']
 o=read(original_path,original_hash);n=read(native_path,native_hash);assert o['passed']and n['passed']and o['all_workers_terminal']and n['all_workers_terminal']and o['original_worker_invocations']==1 and n['actual_workers_launched']==2
 assert o['build_sha256']==op['build_sha256']and n['build_sha256']==np['build_sha256']and o['preparation_sha256']==op['preparation_sha256']and n['preparation_sha256']==np['preparation_sha256']and o['common_caller_recipe_sha256']==n['common_caller_recipe_sha256']==op['common_caller_recipe_sha256']==np['common_caller_recipe_sha256']==RECIPE
 assert o['admission_review_sha256']=='caa8b189a0da510dee164f3b54b51decd0d0662a110e77d5204f09adf1bf5f5d'and n['admission_review_sha256']=='c1d894005c1a3e6f3273d12e34e3716a0dcffc0b2176a014e25013c95b6f6938'
 assert o['role']=='single_original8_common_transport'and n['role']=='direct_ordinary_closed_native3_common'and not o['archive_payload_reader_opened']and not n['archive_reader_opened']
 tool=pin(R/'tools/m4-version-source/compare_common_v1.py','b46de35b4c118a17b5ef8c0f0722b1c910813ef0f48489c33d0c64660fd82c55');pin(R/'tools/m4-crt-allocation-root/run_v2.py');pin(__file__)
 out=R/'reports/m4-version-source'/name;assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Metadata-only exact terminal original8/native3 workers and admitted source/object/observer pair; root owns sole reader scheduling',original_execution_sha256=original_hash,native_execution_sha256=native_hash,comparison_tool_sha256=sha(tool),sole_original_reader_lease=True,original_input_role=o['role'],native_input_role=n['role'],common_caller_recipe_sha256=RECIPE,archive_reader_opened=False,source_original_equivalence=False,initializer_credit=0,files=P),indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(*sys.argv[1:])
