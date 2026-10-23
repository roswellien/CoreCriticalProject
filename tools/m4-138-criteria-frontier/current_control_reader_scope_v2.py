"""Ordinary-controller reader scope, separate from full raw/private review."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 q=pin(R/'reports/m4-joint-startup138/context-controls-execution-r1/report.json','43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863');execution=json.loads(q.read_bytes());assert execution['passed']is True and execution['ordinary_outputs_only']is True
 paths=['tools/m4-joint-startup138/run_context_controls_v3.py','tools/m4-pipeline/stages_capture_storage.py','tools/m4-pipeline/paths_capture_storage.py','tools/m4-pipeline/paths.py','tools/m4-pipeline/manifests.py'];sources={}
 for rel in paths:
  p=R/rel;h=execution['files'].get(str(p));p=pin(p,h);s=p.read_text();ast.parse(s);sources[rel]=s
  assert not any(x in s for x in ('ExportReader','BoundedReader','NativeCapture','DirectSet(','zipfile','import mmap'))
 controller=sources[paths[0]];assert 'from stages_capture_storage import run_stage,verify_stage'in controller and 'from paths_capture_storage import STORAGE_ROOT'in controller
 assert 'capture.rglob' in controller and 'manifest='in controller and "for q,h in list(pins.items())"in controller
 stage=sources[paths[1]];assert "with Path(path).open('rb') as stream:"in stage and 'child.stdout.close()'in stage and 'child.stderr.close()'in stage and 'child.communicate(timeout=timeout_seconds)'in stage
 assert "status = 'success' if exit_code == 0 else 'nonzero_exit'"in stage and 'process_file_open_attestation=False'in stage
 assert {(r['level'],r['mode'])for r in execution['runs']}=={(level,mode)for level in ('O0','O2')for mode in range(1,9)}
 terminals=[]
 for r in execution['runs']:
  p=pin(r['stage'],r['stage_sha256']);st=json.loads(p.read_bytes());assert r['passed']is True and st['passed']is True and st['status']=='success'and st['exit_code']==0 and st['launch_error']is None and st['inputs_stable']is True
  assert st['stage_source_sha256']==pins[str(R/paths[1])] and st['process_file_open_attestation']is False
  assert st['input_sha256']==st['final_input_sha256']and not st['missing_outputs']and not st['invalid_outputs']
  terminals.append(dict(level=r['level'],mode=r['mode'],stage=str(p),sha256=pins[str(p)]))
 pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Exact current ordinary worker-controller and16 terminal stages; zero bounded/canonical reader constructors in inspected controller dependency source; not full raw/private reviewer closure or process handle attestation',candidate=dict(gate='controls_execution',field='all_bounded_readers_closed',value=True,named_domain='ordinary controller only:0 bounded readers; context-managed hash streams and terminal process pipes'),bounded_reader_instances=0,worker_terminal_stages=terminals,full_raw_review_closed_claim=False,full_payload_inventory_rehashed=False,worker_executed=False,archive_reader_opened=False,configuration_created=False,allowance_created=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
