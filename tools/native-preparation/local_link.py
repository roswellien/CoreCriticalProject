"""Private integration link using regenerated game objects and existing host objects.

This is a development trial, not a distributable preparer: it still needs the
developer's authored host compilation and Windows SDK. Never packages outputs.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from translate import need, sha


def export(build, candidates, output):
    need(not output.exists(), 'Use a fresh local link plan')
    ninja = build / 'build.ninja'
    text = ninja.read_text()
    match = re.search(r'^build entry_commandline\.exe: CXX_EXECUTABLE_LINKER__entry_commandline_Release (.+)$', text, re.M)
    need(match is not None, 'Expected native host link rule')
    # Ninja escapes drive colons, spaces and dollar signs. Consume tokens
    # explicitly so an escaped space cannot split a filename.
    tokens = re.findall(r'(?:\$[^\r\n]|[^\s$])+', match[1])
    paths = [re.sub(r'\$([ :$])', r'\1', t) for t in tokens]
    need(all(p.endswith('.obj') for p in paths), 'Unexpected native link input')
    by_hash = {}
    for item in candidates:
        digest = item['sha256']
        need(digest not in by_hash, 'Ambiguous generated component identity')
        by_hash[digest] = item
    selected, used, authored = [], set(), 0
    for name in paths:
        source = Path(name)
        if not source.is_absolute():
            need(name.startswith('CMakeFiles\\entry_commandline.dir\\') and '..' not in source.parts,
                 'Unexpected authored host object path')
            source = build / source
            digest = sha(source)
            selected.append(dict(path=str(source), sha256=digest, kind='existing-authored-host'))
            authored += 1
        else:
            digest = sha(source)
            need(digest in by_hash, 'Native input lacks an original-source generator: '+str(source))
            need(digest not in used, 'Native component selected twice')
            used.add(digest)
            item = by_hash[digest]
            selected.append(dict(path=str(Path(item['path']).resolve()), sha256=digest, kind='generated-from-original'))
    need(used == set(by_hash), 'Generated component does not belong to selected host')
    need(authored == 7 and len(used) == 37348, 'Unexpected selected host component counts')
    libraries = re.search(r'^  LINK_LIBRARIES = (.+)$', text[match.end():], re.M)[1].split()
    need(all(re.fullmatch('[A-Za-z0-9_]+\\.lib', p) for p in libraries), 'Unexpected system library')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(contract='mw3-private-generated-link-v1', inputs=selected,
        libraries=libraries, build_ninja_sha256=sha(ninja), distributable=False), indent=2)+'\n')
    return dict(generated=len(used), existing_authored=authored)


def link(plan_path, linker, output):
    need(not output.exists(), 'Use a fresh private linked-runtime directory')
    plan = json.loads(plan_path.read_text())
    need(plan['contract'] == 'mw3-private-generated-link-v1' and plan['distributable'] is False, 'Private link contract required')
    kinds = [item['kind'] for item in plan['inputs']]
    need(kinds.count('generated-from-original') == 37348 and kinds.count('existing-authored-host') == 7 and
         len(kinds) == 37355, 'Unexpected private link component counts')
    need(all(re.fullmatch('[A-Za-z0-9_]+\\.lib', p) for p in plan['libraries']), 'Unexpected private link library')
    for item in plan['inputs']:
        path = Path(item['path'])
        need(path.is_file() and sha(path) == item['sha256'], 'Generated/host input missing or changed: '+str(path))
    output.mkdir(parents=True)
    response = output / 'objects.rsp'
    names = [item['path'] for item in plan['inputs']]
    need(all('"' not in p and '\n' not in p and '\r' not in p for p in names), 'Invalid link input name')
    response.write_text('\n'.join('"'+p+'"' for p in names)+'\n'+' '.join(plan['libraries'])+'\n')
    target = output / 'entry_commandline.exe'
    # SDK libraries must already be supplied by the developer environment.
    result = subprocess.run([str(linker), '@'+str(response), '/nologo', '/machine:x64', '/INCREMENTAL:NO',
        '/subsystem:console', '/DEBUG', '/OPT:REF', '/OPT:ICF', '/version:0.0', '/out:'+str(target),
        '/implib:'+str(output / 'entry_commandline.lib'), '/pdb:'+str(output / 'entry_commandline.pdb')], capture_output=True)
    (output / 'link.log').write_bytes(result.stdout+result.stderr)
    need(result.returncode == 0, 'Private native link failed; see link.log')
    for item in plan['inputs']:
        need(sha(Path(item['path'])) == item['sha256'], 'Input changed during private native link')
    receipt = dict(native_sha256=sha(target), generated_objects=37348, existing_authored_objects=7,
        private_trial=True, distributable=False, original_code_executed=False, plan_sha256=sha(plan_path))
    (output / 'generation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('export')
    for name in ('build', 'candidates', 'output'):
        create.add_argument('--'+name, type=Path, required=True)
    run = commands.add_parser('link')
    for name in ('plan', 'linker', 'output'):
        run.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        print(export(args.build.resolve(), json.loads(args.candidates.read_text()), args.output.resolve()))
    else:
        print(link(args.plan.resolve(), args.linker.resolve(), args.output.resolve()))
