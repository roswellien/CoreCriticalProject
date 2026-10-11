"""Proof serialization only: hex-encode the model's computed snapshot State."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,label):
 if not v:raise ValueError(label)
def main(name):
 out=R/'reports/m4-widget-source-review'/name;need(not out.exists(),'Fresh serialization-only repair');out.mkdir(parents=True)
 base=R/'tools/m4-widget-source-review/compare_registry_v6.py';need(sha(base)=='b7c31324eba4ed45f99d1d801a35a02917b0d53eceed58ea7f1bf7dc87ca3b82','Exact immutable provider merge6')
 a='self.phases[name]=dict(state=bytes(self.state),CPU=list(self.projected_cpu()),fx=self.fx.hex(),source_access_index=len(self.accesses))'
 b='self.phases[name]=dict(state=bytes(self.state).hex(),CPU=list(self.projected_cpu()),fx=self.fx.hex(),source_access_index=len(self.accesses))'
 text=base.read_text();need(text.count(a)==1,'One model-only observation serializer');text=text.replace(a,b,1)
 tool=R/'tools/m4-widget-source-review/compare_registry_v7.py';need(not tool.exists(),'Fresh serializer7');tool.write_text(text)
 need(tool.read_text().replace(b,a,1)==base.read_text(),'Exact inverse restores source6, all computations/equality controls untouched')
 # Complete reversible representation witness, independent of a candidate run.
 from os import urandom
 sample=bytes(range(256))*13+bytes(range(176));need(len(sample)==3504 and bytes.fromhex(sample.hex())==sample,'Exact State3504 hex inverse')
 delta=out/'changes.json';delta.write_text(json.dumps(dict(before=a,after=b,computed_State_observation_encoding='hex',no_source_prediction_change=True),indent=2)+'\n')
 files={str(p.resolve()):sha(p) for p in(base,tool,delta,Path(__file__),Path(sys.executable),R/'reports/m4-widget-source-review/registry-source-preparation-r1/report.json')}
 report=dict(passed=True,scope='Proof-only computed State3504 snapshot hex serialization; does not change source prediction, response seams, equality or counts',base_sha256=sha(base),comparison=str(tool),comparison_sha256=sha(tool),changed_sites=1,exact_inverse_restores_base_source=True,source_API_phase_state_encoding='hex',native_worker_rerun=False,archive_reader_opened=False,execution_claimed=False,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),comparison=str(tool),comparison_sha256=sha(tool),passed=True)))
if __name__=='__main__':main(sys.argv[1])
