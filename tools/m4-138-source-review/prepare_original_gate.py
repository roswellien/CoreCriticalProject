"""Add strict original138 input admission before opening a source reader."""
from pathlib import Path
import ast
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'reports/m4-joint-startup138-source/preparation-r2/report.json'
PARENT_SHA = '0f4ddf4df9576aa132388e22c26dff01f1abbed59e4975dd8818a42800bec26d'


def main(name):
    out = ROOT / 'reports/m4-joint-startup138-source' / name
    if out.exists():
        raise ValueError('Fresh immutable preparation required')
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        if path.suffix.lower() in ('.mwb', '.mwi', '.zip'):
            raise ValueError('No capture input admitted')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if expected is not None and digest != expected:
            raise ValueError('Physical input changed: ' + str(path))
        if str(path) in pins and pins[str(path)] != digest:
            raise ValueError('Conflicting physical input')
        pins[str(path)] = digest
        return path

    parent = json.loads(pin(PARENT, PARENT_SHA).read_bytes())
    if not parent['passed'] or parent['writer_executed'] or parent['capture_archive_reader_opened']:
        raise ValueError('Unexecuted parent source preparation required')
    for path, digest in parent['files'].items():
        pin(path, digest)
    entry = pin(parent['entrypoint'])
    original = entry.read_text()
    old = "  op=pin(original_report,original_digest);need(json.loads(op.read_bytes())['passed'],'Current complete genuine original131 validation');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)"
    new = """  op=pin(original_report,original_digest);original_validation=json.loads(op.read_bytes())
  required_original=dict(passed=True,original_executed=True,native_executed=False,record_bytes=356992,combined_pages=69,callbacks=108,initialized_state=2,reader_closed=True,paired_export_readers_closed=True,state_seeded=False,per_phase_reseed=False,AFTER_machine_seed=False,initializer_credit=0,build_sha256='748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69',preparation_sha256='e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2')
  for field,expected in required_original.items():need(field in original_validation and original_validation[field]==expected,'Complete current original138 admission '+field)
  original_counts=original_validation['counts'];need(original_counts['phases']==828 and original_counts['widget_actual_root_phases']==42 and original_counts['widget_whole_source_page_endpoints']==114264 and original_counts['widget_whole_CRT_phase_page_endpoints']==105984 and original_counts['widget_whole_nonstack_carried_page_relations']==55896 and original_counts['widget_exact_MFC_CRT_transition_page_relations']==768,'Complete original138 observation and exact observer chronology domain')
  need(original_counts['widget_complete_GDI_boundary_sides']>0 and original_counts['widget_actual_stdcall_RETURN_relations']*2==original_counts['widget_complete_GDI_boundary_sides'],'Complete original GDI entry/return pairing')
  ori=D.DirectSet(original_validation['original_capture'],pin)"""
    if original.count(old) != 1:
        raise ValueError('Exact single original input gate required')
    source = original.replace(old, new)
    if source.replace(new, old) != original:
        raise ValueError('All inherited source checks retained')
    ast.parse(source)
    out.mkdir(parents=True)
    current = out / entry.name
    current.write_text(source)
    pin(current)
    for filename in ('continuity138.py', 'final_observer138.py', 'final_observer138_v2.py', 'paired_exports.py'):
        data = pin(entry.parent / filename).read_bytes()
        target = out / filename
        target.write_bytes(data)
        pin(target)
    delta = out / 'original-admission-delta.json'
    delta.write_text(json.dumps(dict(old=old, new=new, exact_inverse_restores_parent=True), indent=2) + '\n')
    pin(delta)
    pin(__file__)
    pin(sys.executable)
    report = dict(parent)
    report.update(parent_preparation_sha256=PARENT_SHA, entrypoint=str(current.resolve()),
                  scope='Unexecuted source preparation with explicit generated pair helper and strict current original138 admission before canonical reader',
                  original138_input_gate_strengthened=True, exact_inverse_restores_parent=True,
                  writer_executed=False, capture_archive_reader_opened=False, initializer_credit=0, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, report=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), physical_inputs=len(pins))))


if __name__ == '__main__':
    main(sys.argv[1])
