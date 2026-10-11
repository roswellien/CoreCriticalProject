"""Add proof-only literal BEFORE/boundary exports to admitted reader4."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True)
 parent=ROOT/'tools/m4-joint-startup131/compare_provider_v4.py';target=parent.with_name('compare_provider_v5.py');assert not target.exists()
 text=parent.read_text();before='import mfc_source_v2 as MF';after='import mfc_source_v3 as MF';assert text.count(before)==1;text=text.replace(before,after);ast.parse(text);target.write_text(text)
 inputs=(Path(__file__),parent,target,parent.with_name('mfc_source_v3.py'),parent.with_name('mfc_source_v2.py'))
 report=dict(passed=True,scope='Unexecuted proof-only seven literal boundary and computed BEFORE exports; frozen evaluator/capture coverage and all comparison predicates unchanged',parent_preparation=str(ROOT/'reports/m4-joint-startup131-source/preparation-r4/report.json'),parent_preparation_sha256=sha(ROOT/'reports/m4-joint-startup131-source/preparation-r4/report.json'),tool=str(target),changes=[dict(before=before,after=after)],files={str(p.resolve()):sha(p)for p in inputs},source_computed_BEFORE=True,literal_normal_boundary_PCs=[0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca],snapshot_native_observation_claim=False,candidate_AFTER_machine_seed=False,per_phase_BEFORE_machine_seed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
