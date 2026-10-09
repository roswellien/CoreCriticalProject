"""Focused read-only review of the exact future self-link publication check."""
import ast
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-version-root-audit'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path


def need(value, why):
    if not value:
        raise ValueError(why)


def main(directory):
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh final-check derivative review')
    files = {}

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Exact input identity')
        files[normalized(str(path))] = actual
        return path

    base = pin(ROOT/'tools/m4-crt-heap-version-root/final_check.py',
               'a1e33721f35f95f2ccc22c3c2a90f817780e9d7192db12dad6ec8f5a759e9191')
    current = pin(base.with_name('final_check_v2.py'),
                  'b227618ad3dccde1026fa183ddaee5e13d2d0a4ff82df4fe5e648d85dbf045ea')
    code = current.read_text()
    def prefix(path):
        tree = ast.parse(path.read_text())
        body = next(n.body for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        stop = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'documents' for t in n.targets))
        return [ast.dump(n, include_attributes=False) for n in body[:stop]]
    need(prefix(base) == prefix(current), 'All acceptance/stage/closure/source syntax checks unchanged')
    need("if target != (out/'report.json').resolve():" in code
         and "raise ValueError('Missing local link: '+str(p)+' '+ref)" in code,
         'Only exact resolved future report is admitted as a missing link')
    publication = code.index("publish_bytes(out/'report.json'")
    check = code.index("if any(not Path(item['target']).is_file() for item in self_links):")
    need(publication < check and "raise ValueError('Current report self-link publication did not resolve')" in code,
         'Published report must resolve before successful completion')
    accepted = pin(ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json',
                   'cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1')
    value = json.loads(accepted.read_bytes(), object_pairs_hook=unique_object)
    need(value['passed'] is True, 'Completed root admission')
    stage = pin(accepted.parent.parent/'root-acceptance-stage-r1/stage.json')
    staged = json.loads(stage.read_bytes(), object_pairs_hook=unique_object)
    need(staged['passed'] is True and staged['status'] == 'success', 'Recorded successful root admission stage')
    outputs = {normalized(p): h for p, h in staged['artifact_sha256'].items()}
    need(outputs[normalized(str(accepted))] == sha_file(accepted), 'Exact admission stage-output association')
    future = (accepted.parent.parent/'final-check-r1/report.json').resolve()
    links = 0
    self_links = []
    for item in value['documents']:
        document = pin(item['path'], item['sha256'])
        content = document.read_text(encoding='utf-8')
        need(all(line == line.rstrip() for line in content.splitlines()), 'Current document whitespace')
        for reference in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in reference:
                continue
            target = (document.parent/reference.split('#')[0]).resolve()
            if target == future:
                self_links.append(dict(document=str(document), reference=reference, target=str(target), exists_at_review=target.is_file()))
            else:
                need(target.exists(), 'All other current local links exist')
            links += 1
    need(len(self_links) == 1, 'Exactly one document reference to current final-check output')
    for path in (Path(__file__), Path(sys.executable), ROOT/'tools/m4-pipeline/capture_bundle.py',
                 ROOT/'tools/m4-pipeline/manifests.py', ROOT/'tools/m4-pipeline/paths.py'):
        pin(path)
    closure = verify_manifest(files)
    out.mkdir()
    publish_bytes(out/'pins.json', (json.dumps(dict(files=files), indent=2)+'\n').encode())
    report = dict(passed=True, schema='mw34-m4-heap-version-root-final-check-derivative-review-v1',
        scope='Focused read-only future self-link derivative and current document link corroboration',
        base_final_check_sha256=sha_file(base), derivative_final_check_sha256=sha_file(current),
        acceptance_sha256=sha_file(accepted), acceptance_stage_sha256=sha_file(stage),
        original_acceptance_stage_closure_AST_checks_unchanged=True,
        exception_only_exact_resolved_own_output=True, all_other_missing_links_rejected=True,
        atomic_publication_followed_by_is_file_assertion=True, self_document_links=self_links,
        documents=len(value['documents']), current_local_links=links, no_actionable_findings=True,
        unchanged_archives_or_full_models_reread=False, full_acceptance_closure_reverified_by_this_review=False,
        root_final_checker_or_native_API_game_executed_by_this_review=False,
        whole_M4_complete=False, files=files, physical_closure=closure,
        pins_sha256=sha_file(out/'pins.json'))
    publish_bytes(out/'report.json', (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}))


if __name__ == '__main__':
    main(*sys.argv[1:])
