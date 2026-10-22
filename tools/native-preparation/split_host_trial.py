"""Private trial separating authored host code from user-generated native code.

The development host link uses the installed SDK. The translated DLL link must
use only the generated objects and the authored host's import library, without
SDK/CRT libraries. Outputs are private pending payload/provenance review.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from translate import need, sha


def build(plan_path, llvm, output):
    need(not output.exists(), 'Use a fresh split-host trial directory')
    plan = json.loads(plan_path.read_text())
    need(plan['contract'] == 'mw3-private-generated-link-v1', 'Selected private link plan required')
    host, guest = [], []
    for item in plan['inputs']:
        path = Path(item['path'])
        need(sha(path) == item['sha256'], 'Selected split input changed: '+str(path))
        (host if item['kind'] == 'existing-authored-host' else guest).append(path)
    need(len(host) == 7 and len(guest) == 37348, 'Complete selected host inputs required')
    output.mkdir(parents=True)

    def response(name, arguments):
        need(all(not any(c in str(a) for c in '\r\n"') for a in arguments), 'Invalid response argument')
        target = output / (name+'.rsp')
        target.write_text('\n'.join('"'+str(a)+'"' for a in arguments)+'\n')
        return '@'+str(target)

    def run(tool, arguments, name):
        result = subprocess.run([str(llvm / tool), *map(str, arguments)], capture_output=True)
        (output / (name+'.stdout')).write_bytes(result.stdout)
        (output / (name+'.stderr')).write_bytes(result.stderr)
        need(result.returncode == 0, 'Split host step failed: '+name)
        return result.stdout.decode(errors='replace')

    def symbols(objects, name):
        result = run('llvm-nm.exe', ['--extern-only','--format=posix',response(name, objects)], name)
        defined, undefined = {}, set()
        for line in result.splitlines():
            match = re.match(r'^(\S+) ([A-Za-z?])(?: |$)', line)
            if not match:
                continue
            symbol, kind = match.groups()
            if kind == 'U':
                undefined.add(symbol)
            else:
                defined[symbol] = kind
        return defined, undefined

    host_defs, host_undef = symbols(host, 'host-symbols')
    guest_defs, guest_undef = symbols(guest, 'guest-symbols')
    guest_exports = sorted(set(guest_defs) & host_undef)
    # Import-address references use the library's public symbol; its import
    # library provides the corresponding __imp_ slot on the DLL side.
    host_exports = sorted({n.removeprefix('__imp_') for n in guest_undef-set(guest_defs)})
    need(0 < len(guest_exports) < 65535 and 0 < len(host_exports) < 65535, 'Bounded split native export tables')
    need(all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.$]*', n) for n in guest_exports+host_exports), 'Unexpected native seam symbol')

    def definition(name, library, names, kinds):
        path = output / (name+'.def')
        lines = [n+(' DATA' if kinds.get(n) in ('B','C','D','R','S') else '') for n in names]
        path.write_text('LIBRARY '+library+'\nEXPORTS\n'+'\n'.join(lines)+'\n')
        return path

    guest_def = definition('translated', 'MW3Translated.dll', guest_exports, guest_defs)
    host_def = definition('host', 'entry_commandline.exe', host_exports, host_defs)
    run('llvm-lib.exe', ['/machine:x64','/def:'+str(guest_def),'/out:'+str(output / 'translated.lib')], 'guest-import-library')
    host_args = [*host, output / 'translated.lib', *plan['libraries'], '/nologo','/machine:x64','/INCREMENTAL:NO',
        '/subsystem:console','/OPT:REF','/OPT:ICF','/def:'+str(host_def),'/out:'+str(output / 'entry_commandline.exe'),
        '/implib:'+str(output / 'authored-host.lib')]
    run('lld-link.exe', [response('host-link', host_args)], 'host-link')
    # No Windows SDK or proprietary startup/import libraries are passed here.
    guest_args = [*guest, output / 'authored-host.lib','/nologo','/machine:x64','/DLL','/NOENTRY','/OPT:REF','/OPT:ICF',
        '/def:'+str(guest_def),'/out:'+str(output / 'MW3Translated.dll'),'/implib:'+str(output / 'translated-final.lib')]
    run('lld-link.exe', [response('guest-link', guest_args)], 'guest-link')
    for item in plan['inputs']:
        need(sha(Path(item['path'])) == item['sha256'], 'Split input changed during link')
    result = dict(contract='mw3-private-split-native-trial-v1', host_objects=len(host), generated_objects=len(guest),
        host_exports=len(host_exports), generated_exports=len(guest_exports),
        host_sha256=sha(output / 'entry_commandline.exe'), translated_sha256=sha(output / 'MW3Translated.dll'),
        plan_sha256=sha(plan_path), translated_link_sdk_libraries=[], distributable=False)
    (output / 'generation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'llvm', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(build(args.plan.resolve(), args.llvm.resolve(), args.output.resolve()))
