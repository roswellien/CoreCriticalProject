"""Verify the completed admission stage, frozen closure and authored files."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage


def main(acceptance_sha, stage_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-init-root':
        raise ValueError('Fresh final verification directory')
    accepted = ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json'
    stage = ROOT/'reports/m4-crt-heap-init-root/root-acceptance-stage-r1'
    if sha_file(accepted) != acceptance_sha:
        raise ValueError('Fixed admitted receipt')
    value = json.loads(accepted.read_bytes(), object_pairs_hook=unique_object)
    if value['passed'] is not True:
        raise ValueError('Successful admission')
    verified = verify_stage(stage, stage_sha)
    if verified['recorded_stage_passed'] is not True:
        raise ValueError('Actual completed admission stage')
    closure = verify_manifest(value['files'])
    tool_dirs = [ROOT/'tools'/name for name in (
        'm4-crt-heap-init', 'm4-crt-heap-init-review', 'm4-crt-heap-init-recovery',
        'm4-crt-heap-init-root', 'm4-crt-heap-init-root-audit')]
    sources = sorted(p for folder in tool_dirs for p in folder.glob('*.py'))
    for path in sources:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    scripts = sorted(p for folder in tool_dirs for p in folder.glob('*.ps1'))
    for path in scripts:
        quoted = str(path).replace("'", "''")
        command = "$tokens=$null; $parseErrors=$null; [System.Management.Automation.Language.Parser]::ParseFile('"+quoted+"',[ref]$tokens,[ref]$parseErrors) | Out-Null; if($parseErrors.Count) { $parseErrors | Out-String | Write-Output; exit 1 }"
        result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
            capture_output=True, timeout=30, creationflags=0x08000000)
        if result.returncode:
            raise ValueError('PowerShell syntax: '+str(path)+' '+result.stdout.decode(errors='replace'))
    documents = [ROOT/'docs/m4-crt-heap-init-review.md', ROOT/'docs/m4-progress-heap-init.md']
    documents += [folder/'README.md' for folder in tool_dirs]
    links = 0
    for path in documents:
        text = path.read_text(encoding='utf-8')
        if any(line != line.rstrip() for line in text.splitlines()):
            raise ValueError('Document trailing whitespace: '+str(path))
        for ref in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in ref:
                continue
            target = path.parent/ref.split('#')[0]
            if not target.exists():
                raise ValueError('Missing local link: '+str(path)+' '+ref)
            links += 1
    pins = {str(path):sha_file(path) for path in [accepted,stage/'stage.json',Path(__file__),*sources,*scripts,*documents]}
    report = dict(passed=True, acceptance_sha256=acceptance_sha, acceptance_stage_sha256=stage_sha,
        completed_stage=verified, current_admitted_physical_closure=closure,
        Python_AST_files=len(sources), PowerShell_AST_files=len(scripts), documents=len(documents),
        local_document_links=links, trailing_whitespace=0, files=pins,
        original_or_native_or_game_executed=False, whole_M4_complete=False)
    out.mkdir()
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='files'}))


if __name__ == '__main__':
    main(*sys.argv[1:])
