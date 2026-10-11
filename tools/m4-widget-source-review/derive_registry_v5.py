"""Additive exact lifecycle classification for widget52 registry raw inputs.

The five DeleteCriticalSection lifecycle records occur after the modeled six
provider intervals. They are retained as unmodeled cleanup observations, never
transported as source effects. The literal model/equality predicates are intact.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,label):
 if not v:raise ValueError(label)
def main(name):
 out=R/'reports/m4-widget-source-review'/name;need(not out.exists(),'Fresh additive parser repair receipt');out.mkdir(parents=True)
 base=R/'tools/m4-widget-native/compare_registry_v4.py';need(sha(base)=='6b64b0212595e7ca812a6b1bec600480afcb4656e819e237e0dc717664b24744','Immutable exact registry4')
 text=base.read_text()
 replacements=[
 ("  if w[31]==1:\n   need(w[2]==0 and w[3]==0x78146190,'Exact named bootstrap association');name_='MSVCP-resource-association'",
  "  if w[31]==1:\n   need(w[2]==0 and w[8]==1 and w[14:16]==(1,1),'Exact lifecycle observation marker/status')\n   if (w[3],w[4])==(0x78146190,0x866ce):name_='MSVCP-resource-association'\n   else:\n    need((w[3],w[4])==(0x7802e040,0x3446a),'Only exact physical native DeleteCriticalSection cleanup identity');name_='unmodeled-native-cleanup-DeleteCriticalSection'"),
 ("  for level in('O0','O2'):\n   folder=",
  "  pin(R/'reports/m4-widget-native/service-preparation-r3/locale_batch_operations.inc');pin(R/'reports/m4-widget-native/service-preparation-r3/lockit_operations.inc');pin(R/'reports/m4-widget-source-review/registry-parser-preparation-r1/report.json','PREPARATION_SHA')\n  for level in('O0','O2'):\n   folder="),
 ("    response=responses_module.ActualResponses(all_facts);response.index=start",
  "    cleanup=[v for v in all_facts if v['name']=='unmodeled-native-cleanup-DeleteCriticalSection'];need(len(cleanup)==5 and all(v['words'][1]>=end for v in cleanup),'All five native cleanup observations are beyond this modeled provider interval');counts['unmodeled_cleanup_after_interval_joins']+=len(cleanup)\n    response=responses_module.ActualResponses(all_facts);response.index=start"),
 ]
 changes=[]
 for a,b in replacements:
  need(text.count(a)==1,'Unique exact additive parser delta');text=text.replace(a,b,1);changes.append(dict(before=a,after=b))
 # This proof-only marker is replaced after the immutable preparation is sealed
 # through a separate hardcoded input receipt, avoiding self-hash recursion.
 text=text.replace(";pin(R/'reports/m4-widget-source-review/registry-parser-preparation-r1/report.json','PREPARATION_SHA')",'')
 tool=R/'tools/m4-widget-source-review/compare_registry_v5.py';need(not tool.exists(),'Fresh registry5 source file');tool.write_text(text)
 operations=R/'reports/m4-widget-native/service-preparation-r3/locale_batch_operations.inc'
 lockit=R/'reports/m4-widget-native/service-preparation-r3/lockit_operations.inc'
 need('lifecycle_api("DeleteCriticalSection",0x7802e040,0x3446a' in operations.read_text(),'Physical caller-declared cleanup classification')
 need('lifecycle_api("InitializeCriticalSection",0x78146190,0x866ce' in lockit.read_text(),'Physical bootstrap association classification')
 # Reversing each exact transformation gives byte-identical old semantics.
 old=tool.read_text()
 for a,b in reversed(replacements):
  b=b.replace(";pin(R/'reports/m4-widget-source-review/registry-parser-preparation-r1/report.json','PREPARATION_SHA')",'')
  need(old.count(b)==1,'Unique invertible parser change');old=old.replace(b,a,1)
 need(old==base.read_text(),'Exact unchanged full source/equality/control algorithm after inverse')
 delta=out/'changes.json';delta.write_text(json.dumps(changes,indent=2)+'\n')
 files={str(p.resolve()):sha(p) for p in (base,tool,operations,lockit,delta,Path(__file__),Path(sys.executable),R/'reports/m4-widget-native/source-registry-r1/report.json',R/'reports/m4-widget-native/source-prefix-r1/report.json')}
 report=dict(passed=True,scope='Additive exact raw lifecycle parser repair only; six provider literal source/equality predicates unchanged, five actual cleanup observations kept outside every source interval',
  base_sha256=sha(base),comparison=str(tool),comparison_sha256=sha(tool),changed_sites=3,
  exact_inverse_restores_base_source=True,new_source_or_API_effects=False,AFTER_seed=False,
  native_worker_rerun=False,archive_reader_opened=False,execution_claimed=False,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),comparison=str(tool),comparison_sha256=sha(tool),passed=True)))
if __name__=='__main__':main(sys.argv[1])
