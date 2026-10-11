"""Bound the debugger metadata claim while retaining all actual raw bytes."""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
files = {}
def pin(path, digest=None):
 path = Path(path).resolve()
 with path.open('rb') as stream: value = hashlib.file_digest(stream,'sha256').hexdigest()
 assert digest is None or digest == value
 files[str(path)] = value
 return path
base = pin(R/'tools/m4-hypot-original/validate_trace.py')
pin(R/'reports/m4-hypot-original/trace-validation-r1/report.json','0b19a8ee2e7a4d609da668cb6ae46f35a27115dde89213ba9987c5f63929b53f')
pin(R/'reports/m4-hypot-original/trace-execution-r2/report.json','ea13e2ec03f460df46d49d3a6a67f4b27896e7989437d54d9d2684dfbd360416')
metadata = pin(R/'reports/m4-hypot-original/trace-metadata-r1/report.json')
pin(R/'reports/m4-hypot-original/trace-metadata-r1/actual-metadata.json')
text=base.read_text()
hunks=[
 ("   need(u(record,2204)[0]==0x4b5905 and u(record,2212)[0]==0x60b2e8,'Final canonical source ENV metadata preserved under CONTROL-only tracing')",
  "   # Raw debugger ENV metadata is retained below; canonical FIP/FDP is proven only by the separately bound normal observer, not this trace."),
 ("counts['actual_final_canonical_FIP_FDP_relations']+=1", "counts['actual_raw_final_ENV28_observations']+=1"),
 ("normal_numerical_results_are_observation_comparison_only=True,files=PINS)",
  "normal_numerical_results_are_observation_comparison_only=True,canonical_debugger_FIP_FDP_claimed=False,debugger_metadata_replaced=False,normal_canonical_ENV_gate_sha256='80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313',files=PINS)")]
for old,new in hunks:
 assert text.count(old)==1
 text=text.replace(old,new)
target=R/'tools/m4-hypot-original/validate_trace_v2.py'
assert not target.exists()
target.write_text(text)
pin(target);pin(__file__);pin(sys.executable)
out=R/'reports/m4-hypot-original/trace-validation-preparation-r2'
assert not out.exists();out.mkdir()
report=dict(passed=True,scope='Exact three-hunk validator scope correction; traced raw ENV/FX/CONTEXT metadata is retained without canonical identity credit or substitution, independent normal canonical proof remains bound',
 hunks=3,writer_unchanged=True,source_after_seed=False,numerical_expected_seed=False,metadata_replaced=False,
 metadata_observation_path=str(metadata),normal_canonical_gate_sha256='80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313',files=files)
p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p)
print(json.dumps(dict(passed=True,sha256=files[str(p.resolve())],validator_sha256=files[str(target.resolve())])))
