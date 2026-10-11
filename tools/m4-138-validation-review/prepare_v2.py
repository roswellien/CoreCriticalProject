"""Fresh additive GDI pairing repair; ordinary inputs and synthetic controls only."""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'reports/m4-138-validation-review/pairing-preparation-r1'
files = {}; changes = []
def pin(path, expected=None):
    path = Path(path).resolve()
    assert path.name not in ('index.json', 'payload.bin', 'transport.json')
    assert path.suffix.lower() not in ('.mwb', '.zip') and path.stat().st_size <= 32*1024*1024
    with path.open('rb') as stream: value = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert expected is None or value == expected
    files[str(path)] = value
    return path
def replace(text, before, after, label):
    assert text.count(before) == 1, label
    changes.append(dict(file=label, before=before, after=after, occurrences=1))
    return text.replace(before, after)
audit = json.loads(pin(ROOT/'reports/m4-138-validation-review/ordinary-audit-r1/report.json').read_text())
assert audit['passed'] and audit['exact_additive_delta_reconstruction']
for path, value in audit['files'].items(): pin(path, value)
helper_path = ROOT/'tools/m4-startup138-original/widget_phase.py'
validator_path = ROOT/'tools/m4-startup138-original/validate.py'
helper = pin(helper_path).read_text(); validator = pin(validator_path).read_text()
helper = replace(helper, 'class Observer:',
    "def pair_position(index,side):\n need(side==index%2,'Every actual GDI boundary alternates entry then return; no missing or trailing entry')\ndef pair_extent(sides,returns):\n need(sides==2*returns,'Every actual GDI entry has exactly one return')\nclass Observer:", 'widget_phase_v2.py')
helper = replace(helper, '  paired=[]\n', "  paired=[];returns_before=self.counts['widget_actual_stdcall_RETURN_relations']\n", 'widget_phase_v2.py')
helper = replace(helper, "side=h[3]%2;need(api<3", "side=h[3]%2;pair_position(i,side);need(api<3", 'widget_phase_v2.py')
helper = replace(helper, "  fc=w(self.records.data(stem+'fps-count.bin'))[0]", "  pair_extent(count,self.counts['widget_actual_stdcall_RETURN_relations']-returns_before)\n  fc=w(self.records.data(stem+'fps-count.bin'))[0]", 'widget_phase_v2.py')
validator = replace(validator, 'from widget_phase import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES', 'from widget_phase_v2 import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES', 'validate_v2.py')
validator = replace(validator, "counts['widget_complete_GDI_boundary_sides']>0 and", "counts['widget_complete_GDI_boundary_sides']>0 and counts['widget_actual_stdcall_RETURN_relations']*2==counts['widget_complete_GDI_boundary_sides'] and", 'validate_v2.py')
validator = replace(validator, "pin(Path(__file__).resolve().parent/'widget_phase.py')", "pin(Path(__file__).resolve().parent/'widget_phase_v2.py')", 'validate_v2.py')
ast.parse(helper); ast.parse(validator)
helper_v2 = helper_path.with_name('widget_phase_v2.py'); validator_v2 = validator_path.with_name('validate_v2.py')
assert not OUT.exists() and not helper_v2.exists() and not validator_v2.exists()
helper_v2.write_text(helper); validator_v2.write_text(validator)
pin(helper_v2); pin(validator_v2)
spec=importlib.util.spec_from_file_location('review_widget_v2',helper_v2); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
controls=[]
for sides, expected in [([],True),([0,1],True),([0,1,0,1],True),([0,0],False),([1,0],False),([0,1,0,0],False),([0],False)]:
    passed=True
    try:
        for index, side in enumerate(sides): module.pair_position(index,side)
        module.pair_extent(len(sides),sides.count(1))
    except ValueError: passed=False
    assert passed==expected
    controls.append(dict(sides=sides, expected_valid=expected, actual_valid=passed))
pin(__file__); pin(sys.executable)
OUT.mkdir(parents=True)
delta_path=OUT/'deltas.json'; delta_path.write_text(json.dumps(changes,indent=2)+'\n'); pin(delta_path)
controls_path=OUT/'pairing-controls.json'; controls_path.write_text(json.dumps(controls,indent=2)+'\n'); pin(controls_path)
arguments=[str(ROOT/'reports/m4-startup138-original/build-r4/build.json'),'748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69',str(ROOT/'reports/m4-startup138-original/original-execution-r1'),str(ROOT/'reports/m4-tree-review/original138-prelaunch-r5/report.json'),'efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a','original-validation-r1']
report=dict(passed=True,scope='Independent ordinary pin/schema review plus additive GDI pairing repair and synthetic controls only',
    recommend_running_validator=True,validator=str(validator_v2),validator_sha256=files[str(validator_v2)],helper=str(helper_v2),helper_sha256=files[str(helper_v2)],
    parent_validator=str(validator_path),parent_validator_sha256=files[str(validator_path)],parent_helper=str(helper_path),parent_helper_sha256=files[str(helper_path)],
    retained_inherited_gates=True,exact_changes=len(changes),synthetic_controls_passed=len(controls),planned_arguments=arguments,
    root_admission_required=True,capture_opened=False,archive_index_opened=False,validation_executed=False,native_executed=False,initializer_credit=0,
    limitations='Observation-only validator; independent literal source/native semantic gates remain separate. This review admits no functions.',files=files)
target=OUT/'report.json'; target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),validator_sha256=report['validator_sha256'],helper_sha256=report['helper_sha256'],pins=len(files),controls=len(controls))))
