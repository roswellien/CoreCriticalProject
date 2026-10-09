"""Publish a documentation-only clarification without changing sealed proof."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import unique_object
from paths import publish_bytes


def main():
    path = ROOT/'reports/m4-crt-locale-default-root/config-r2/config.json'
    if sha_file(path) != 'd9141bd7020ce3508f1696cedc832afef26781ff98777a6db476584d6ff45dd0':
        raise ValueError('Frozen prior admission request changed')
    config = json.loads(path.read_bytes(), object_pairs_hook=unique_object)
    old = 'Root makes no full causal\nsource-model claim for fault controls; the independently authored compiled\ncorpus supplies that evidence.'
    new = 'Root makes no full causal\nsource-model claim for fault controls. The independent compiled corpus\nseparately validates those fault and cleanup paths; it does not supply a full\ncausal source-model oracle.'
    replacements = {
        'm4-crt-locale-default-review.md': 'm4-crt-locale-default-review-r2.md',
        'm4-progress-locale-default.md': 'm4-progress-locale-default-r2.md',
    }
    documents = []
    for item in config['documents']:
        source = Path(item['path'])
        if sha_file(source) != item['sha256']:
            raise ValueError('Frozen documentation changed')
        if source.name not in replacements:
            documents.append(item)
            continue
        target = source.with_name(replacements[source.name])
        if target.exists():
            raise ValueError('Fresh documentation revision required')
        text = source.read_text(encoding='utf-8')
        if source.name.startswith('m4-crt-'):
            if text.count(old) != 1:
                raise ValueError('Exactly one scope clarification')
            text = text.replace(old, new)
            text = text.replace('root-acceptance-r1/report.json', 'root-acceptance-r2/report.json')
            text += '\nThis revision clarifies compiled fault-test scope. Earlier native/source\nreceipts and the first sealed review remain unchanged.\n'
        else:
            text = text.replace('(m4-crt-locale-default-review.md)', '(m4-crt-locale-default-review-r2.md)')
        with target.open('xb') as stream:
            stream.write(text.encode('utf-8'))
        documents.append(dict(path=str(target), sha256=sha_file(target)))
        config['history'].append(item)
    config['documents'] = documents + [dict(path=str(Path(__file__).absolute()), sha256=sha_file(__file__))]
    accepted = ROOT/'reports/m4-crt-locale-default-root/root-acceptance-r1/report.json'
    accepted_sha = '2e17792b6d27a8297641773a780e5b366b4d28ed92de1e43a41873cd9e54592c'
    if sha_file(accepted) != accepted_sha:
        raise ValueError('Prior sealed proof changed')
    config['history'].append(dict(path=str(accepted), sha256=accepted_sha))
    output = ROOT/'reports/m4-crt-locale-default-root/config-r3'
    if output.exists():
        raise ValueError('Fresh clarification admission output')
    output.mkdir()
    destination = output/'config.json'
    publish_bytes(destination, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(destination), sha256=sha_file(destination),
                         native_source_proofs_unchanged=True, old_docs_preserved=True)))


if __name__ == '__main__':
    main()
