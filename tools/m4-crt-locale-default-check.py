"""Final syntax, documentation and completed admission-stage checks."""
import ast
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes
from stages import verify_stage

files = list((ROOT/'tools/m4-crt-locale-default-root').glob('*.py'))
for path in files:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
docs = [ROOT/'docs/m4-crt-locale-default-review-r2.md', ROOT/'docs/m4-progress-locale-default-r2.md',
        ROOT/'tools/m4-crt-locale-default-root/README.md']
errors, links = [], 0
for path in files+docs:
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.rstrip() != line:
            errors.append(str(path)+':'+str(number))
for path in docs:
    for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if not target.startswith(('http:', 'https:', 'codex:')):
            links += 1
            if not (path.parent/target.split('#')[0]).resolve().exists():
                errors.append(str(path)+': '+target)
if errors:
    raise ValueError(errors)
stage = ROOT/'reports/m4-crt-locale-default-root/root-acceptance-stage-r4'
stage_sha = sha_file(stage/'stage.json')
checked = verify_stage(stage, stage_sha)
if not checked['recorded_stage_passed']:
    raise ValueError('Completed zero-exit admission stage')
path = ROOT/'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json'
digest = '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'
if sha_file(path) != digest:
    raise ValueError('Externally fixed final receipt')
admission = json.loads(path.read_bytes())
if not admission['passed']:
    raise ValueError('Successful final admission')
report = dict(passed=True, python_AST_files=len(files), local_document_links=links,
    trailing_whitespace_errors=len(errors), final_stage=checked, final_stage_sha256=stage_sha,
    current_physical_closure=admission['physical_closure'], final_report_sha256=digest,
    capture_logical_files=sum(a['logical_files'] for a in admission['archives']),
    checker_sha256=sha_file(__file__), native_execution=False, ordinary_game_launched=False)
output = ROOT/'reports/m4-crt-locale-default-root/final-check-r1'
if output.exists():
    raise ValueError('Fresh final check output')
output.mkdir()
publish_bytes(output/'report.json', (json.dumps(report, indent=2)+'\n').encode())
print(json.dumps(report))
