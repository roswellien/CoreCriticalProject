"""Verify admission and documents, resolving this report's own link at publication."""
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
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage


def main(acceptance_sha, stage_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-return-root':
        raise ValueError('Fresh final verification output')
    accepted = out.parent/'root-acceptance-r1/report.json'
    stage = out.parent/'root-acceptance-stage-r1'
    if sha_file(accepted) != acceptance_sha: raise ValueError('Fixed admitted receipt')
    value = json.loads(accepted.read_bytes(), object_pairs_hook=unique_object)
    if value['passed'] is not True: raise ValueError('Successful admission')
    verified = verify_stage(stage, stage_sha)
    if not verified['recorded_stage_passed']: raise ValueError('Successful admission stage')
    command = json.loads((stage/'stage.json').read_bytes(), object_pairs_hook=unique_object)
    outputs = {normalized(p): h for p, h in command['artifact_sha256'].items()}
    if outputs.get(normalized(str(accepted))) != acceptance_sha:
        raise ValueError('Completed admission stage output association')
    closure = verify_manifest(value['files'])
    folders = [ROOT/'tools'/name for name in ('m4-crt-heap-return', 'm4-crt-heap-return-review',
        'm4-crt-heap-return-recovery', 'm4-crt-heap-return-root', 'm4-crt-heap-return-root-audit',
        'm4-crt-heap-return-acceptance-review')]
    sources = sorted(p for folder in folders for p in folder.glob('*.py'))
    for p in sources: ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    scripts = sorted(p for folder in folders for p in folder.glob('*.ps1'))
    for p in scripts:
        quoted = str(p).replace("'", "''")
        command = "$tokens=$null; $parseErrors=$null; [System.Management.Automation.Language.Parser]::ParseFile('"+quoted+"',[ref]$tokens,[ref]$parseErrors) | Out-Null; if($parseErrors.Count) { $parseErrors | Out-String | Write-Output; exit 1 }"
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
            capture_output=True, timeout=30, creationflags=0x08000000)
        if result.returncode: raise ValueError('PowerShell syntax: '+str(p))
    documents = [Path(item['path']) for item in value['documents']]; links = 0; self_links = []
    for p in documents:
        content = p.read_text(encoding='utf-8')
        if any(line != line.rstrip() for line in content.splitlines()):
            raise ValueError('Trailing whitespace: '+str(p))
        for ref in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in ref: continue
            target = (p.parent/ref.split('#')[0]).resolve()
            if not target.exists():
                if target != (out/'report.json').resolve():
                    raise ValueError('Missing local link: '+str(p)+' '+ref)
                self_links.append(dict(document=str(p), reference=ref, target=str(target)))
            links += 1
    pins = {str(p): sha_file(p) for p in [accepted, stage/'stage.json', Path(__file__), *sources, *scripts, *documents]}
    report = dict(passed=True, acceptance_sha256=acceptance_sha, acceptance_stage_sha256=stage_sha,
        completed_stage=verified, current_admitted_physical_closure=closure, Python_AST_files=len(sources),
        PowerShell_AST_files=len(scripts), documents=len(documents), local_document_links=links,
        self_document_links_resolved_at_publication=self_links,
        trailing_whitespace=0, files=pins, original_or_native_or_game_executed=False, whole_M4_complete=False)
    out.mkdir(); publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    if any(not Path(item['target']).is_file() for item in self_links):
        raise ValueError('Current report self-link publication did not resolve')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}))


if __name__ == '__main__': main(*sys.argv[1:])
