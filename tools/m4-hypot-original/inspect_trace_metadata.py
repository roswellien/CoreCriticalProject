"""Retain debugger metadata observations without inferring their cause."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
out = R/'reports/m4-hypot-original/trace-metadata-r1'
assert not out.exists()
out.mkdir()
files = {}
def pin(path, digest=None):
 path = Path(path).resolve()
 with path.open('rb') as stream:
  value = hashlib.file_digest(stream, 'sha256').hexdigest()
 assert digest is None or digest == value
 files[str(path)] = value
 return path
def words(blob, offset, count=1):
 return list(struct.unpack_from('<' + 'I'*count, blob, offset))
execution_path = pin(R/'reports/m4-hypot-original/trace-execution-r2/report.json', 'ea13e2ec03f460df46d49d3a6a67f4b27896e7989437d54d9d2684dfbd360416')
execution = json.loads(execution_path.read_bytes())
assert execution['passed']
normal_path = pin(R/'reports/m4-hypot-original/prefix-validation-r2/actual-hypot-endpoints.json')
normal = json.loads(normal_path.read_bytes())
spec = importlib.util.spec_from_file_location('hypot_metadata_direct', pin(R/'tools/m4-crt-allocation-root/run_v2.py'))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
reader = None
rows = []
try:
 reader = D.DirectSet(Path(execution['original_capture']), pin)
 for sequence in range(6):
  record = reader.data(f'phase/{sequence}/0.bin')
  raw = reader.data(f'phase/{sequence}/0/hypot-trace/events.bin')
  schema = words(reader.data(f'phase/{sequence}/0/hypot-trace/schema.bin'), 0, 8)
  assert len(raw) == schema[4]*1840
  events = []
  for index in range(schema[4]):
   event = raw[index*1840:(index+1)*1840]
   pc = words(event, 4)[0]
   if 0x4b5900 <= pc <= 0x4b593e:
    before, after = event[32:748], event[748:1464]
    events.append(dict(index=index, PC=pc, next_PC=words(event, 8)[0],
      legacy_before_FIP_FDP=[words(before,40)[0],words(before,48)[0]],
      legacy_after_FIP_FDP=[words(after,40)[0],words(after,48)[0]],
      extended_before_FIP_FDP=[words(before,212)[0],words(before,220)[0]],
      extended_after_FIP_FDP=[words(after,212)[0],words(after,220)[0]]))
  rows.append(dict(sequence=sequence, trace_event_count=schema[4],
    trace_AFTER_ENV28_hex=record[2192:2220].hex(),
    trace_AFTER_ENV_FIP_FDP=[words(record,2204)[0],words(record,2212)[0]],
    trace_AFTER_FX512_FIP_FDP=[words(record,636)[0],words(record,644)[0]],
    normal_AFTER_ENV28_hex=normal[sequence]['AFTER_ENV28_hex'],
    actual_late_game_events=events))
finally:
 if reader is not None:
  reader.close()
  reader.entries.clear()
  reader.bundles.clear()
  reader = None
 p=out/'actual-metadata.json'
 p.write_text(json.dumps(rows,indent=2)+'\n')
 pin(p);pin(__file__);pin(sys.executable)
 report=dict(passed=len(rows)==6, scope='Measured raw debugger metadata only; cause is not established and fields are never replaced',
   reader_closed=True, numerical_model_used=False, native_credit=False,
   canonical_trace_FIP_FDP_claim=False, files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(report_sha256=pin(p),rows=rows),default=str))
